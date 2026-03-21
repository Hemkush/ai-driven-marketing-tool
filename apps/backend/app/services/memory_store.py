import hashlib
import json
import re

from openai import OpenAI
from sqlalchemy import and_
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models import MemoryChunk


def _topic_from_question(question_text: str) -> str:
    q = (question_text or "").lower()
    if any(k in q for k in ["competitor", "competition", "rival", "alternative"]):
        return "competitors"
    if any(k in q for k in ["budget", "spend", "investment"]):
        return "budget"
    if any(k in q for k in ["cost", "cac", "expense"]):
        return "cost"
    if any(k in q for k in ["goal", "plan", "objective", "target"]):
        return "goal"
    if any(k in q for k in ["customer", "audience", "buyer", "segment"]):
        return "customer"
    return "business"


def _chunk_text(text: str, max_chars: int = 550) -> list[str]:
    raw = " ".join((text or "").split())
    if not raw:
        return []
    if len(raw) <= max_chars:
        return [raw]
    parts = re.split(r"(?<=[.!?])\s+", raw)
    chunks: list[str] = []
    current = ""
    for part in parts:
        candidate = (current + " " + part).strip()
        if len(candidate) <= max_chars:
            current = candidate
            continue
        if current:
            chunks.append(current)
        current = part[:max_chars].strip()
    if current:
        chunks.append(current)
    return chunks[:6]


def _hash_content(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _embed_texts(texts: list[str]) -> list[list[float] | None]:
    if not texts:
        return []
    if not settings.can_use_openai():
        return [None for _ in texts]
    try:
        client = OpenAI(
            api_key=settings.openai_api_key,
            base_url=settings.openai_base_url,
            timeout=settings.openai_timeout_seconds,
            max_retries=settings.openai_max_retries,
        )
        resp = client.embeddings.create(model=settings.openai_embedding_model, input=texts)
        vectors = [item.embedding for item in (resp.data or [])]
        if len(vectors) != len(texts):
            return [None for _ in texts]
        return vectors
    except Exception:
        return [None for _ in texts]


def store_response_memory(
    db: Session,
    *,
    project_id: int,
    session_id: int | None,
    response_id: int | None,
    question_text: str,
    answer_text: str,
) -> int:
    answer = (answer_text or "").strip()
    question = (question_text or "").strip()
    if not answer:
        return 0

    topic = _topic_from_question(question)
    base_text = f"Question: {question}\nAnswer: {answer}"
    chunks = _chunk_text(base_text)
    if not chunks:
        return 0

    vectors = _embed_texts(chunks)
    created = 0
    try:
        for idx, chunk in enumerate(chunks):
            content_hash = _hash_content(f"{project_id}|{response_id}|{chunk}")
            exists = (
                db.query(MemoryChunk.id)
                .filter(MemoryChunk.content_hash == content_hash)
                .first()
            )
            if exists:
                continue
            row = MemoryChunk(
                project_id=project_id,
                session_id=session_id,
                response_id=response_id,
                source_type="questionnaire_response",
                topic_tag=topic,
                content_text=chunk,
                content_hash=content_hash,
                embedding=vectors[idx] if idx < len(vectors) else None,
                metadata_json=json.dumps(
                    {
                        "question_text": question,
                        "topic": topic,
                        "chunk_index": idx,
                    }
                ),
            )
            db.add(row)
            created += 1
    except Exception:
        return 0
    return created


def _lexical_score(text: str, query: str) -> int:
    query_tokens = {t for t in re.findall(r"[a-zA-Z]{3,}", query.lower())}
    if not query_tokens:
        return 0
    text_tokens = {t for t in re.findall(r"[a-zA-Z]{3,}", (text or "").lower())}
    return len(query_tokens & text_tokens)


def retrieve_relevant_memory(
    db: Session,
    *,
    project_id: int,
    query: str,
    top_k: int | None = None,
    session_id: int | None = None,
) -> list[dict]:
    q = (query or "").strip()
    if not q:
        return []
    limit = max(1, min(12, top_k or settings.memory_top_k))

    base_filter = [MemoryChunk.project_id == project_id]
    if session_id:
        base_filter.append(MemoryChunk.session_id == session_id)

    if settings.can_use_openai():
        try:
            client = OpenAI(
                api_key=settings.openai_api_key,
                base_url=settings.openai_base_url,
                timeout=settings.openai_timeout_seconds,
                max_retries=settings.openai_max_retries,
            )
            emb = client.embeddings.create(model=settings.openai_embedding_model, input=[q])
            query_vector = emb.data[0].embedding
            try:
                rows = (
                    db.query(MemoryChunk)
                    .filter(and_(*base_filter), MemoryChunk.embedding.is_not(None))
                    .order_by(MemoryChunk.embedding.cosine_distance(query_vector))
                    .limit(limit)
                    .all()
                )
                if rows:
                    return [
                        {
                            "id": r.id,
                            "topic_tag": r.topic_tag or "",
                            "content_text": r.content_text,
                            "metadata": json.loads(r.metadata_json or "{}"),
                        }
                        for r in rows
                    ]
            except Exception:
                pass
        except Exception:
            pass

    try:
        rows = (
            db.query(MemoryChunk)
            .filter(and_(*base_filter))
            .order_by(MemoryChunk.id.desc())
            .limit(120)
            .all()
        )
    except Exception:
        return []
    ranked = sorted(rows, key=lambda r: _lexical_score(r.content_text, q), reverse=True)
    selected = [r for r in ranked if _lexical_score(r.content_text, q) > 0][:limit]
    if not selected:
        selected = ranked[:limit]
    return [
        {
            "id": r.id,
            "topic_tag": r.topic_tag or "",
            "content_text": r.content_text,
            "metadata": json.loads(r.metadata_json or "{}"),
        }
        for r in selected
    ]
