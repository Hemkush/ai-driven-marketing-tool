import hashlib
import json
import logging
import re

from openai import OpenAI
from sqlalchemy import and_
from sqlalchemy.orm import Session

import numpy as np

from app.core.config import settings
from app.core.llm_tracker import tracked_embeddings
from app.models import MemoryChunk

logger = logging.getLogger(__name__)


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
        logger.warning("Embeddings skipped: OpenAI not available (missing API key or test mode)")
        return [None for _ in texts]
    try:
        client = OpenAI(
            api_key=settings.openai_api_key,
            base_url=settings.openai_base_url,
            timeout=settings.openai_timeout_seconds,
            max_retries=settings.openai_max_retries,
        )
        resp = tracked_embeddings(client, agent="memory_store",
            model=settings.openai_embedding_model, input=texts)
        vectors = [item.embedding for item in (resp.data or [])]
        if len(vectors) != len(texts):
            logger.error(
                "Embedding count mismatch: sent %d texts, got %d vectors",
                len(texts), len(vectors),
            )
            return [None for _ in texts]
        logger.info("Embeddings created successfully for %d chunks", len(vectors))
        return vectors
    except Exception as exc:
        logger.error("Embedding failed: %s", exc, exc_info=True)
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
            emb = tracked_embeddings(client, agent="memory_store_query",
                model=settings.openai_embedding_model, input=[q])
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
                    # Evaluate retrieval quality: compute cosine similarity scores
                    q_vec = np.array(query_vector)
                    q_norm = np.linalg.norm(q_vec)
                    similarities = []
                    chunks = []
                    for r in rows:
                        chunk = {
                            "id": r.id,
                            "topic_tag": r.topic_tag or "",
                            "content_text": r.content_text,
                            "metadata": json.loads(r.metadata_json or "{}"),
                        }
                        if r.embedding is not None:
                            r_vec = np.array(r.embedding)
                            r_norm = np.linalg.norm(r_vec)
                            sim = float(np.dot(q_vec, r_vec) / (q_norm * r_norm)) if q_norm and r_norm else 0.0
                            similarities.append(sim)
                            chunk["similarity"] = round(sim, 4)
                        chunks.append(chunk)
                    if similarities:
                        avg_sim = round(sum(similarities) / len(similarities), 4)
                        min_sim = round(min(similarities), 4)
                        logger.info("retrieval_quality", extra={
                            "project_id": project_id,
                            "chunks_returned": len(rows),
                            "avg_similarity": avg_sim,
                            "min_similarity": min_sim,
                            "low_relevance": min_sim < 0.75,
                        })
                    return chunks
                logger.warning("Semantic search returned 0 rows (all embeddings may be NULL)")
            except Exception as exc:
                logger.error("Semantic similarity search failed: %s", exc, exc_info=True)
        except Exception as exc:
            logger.error("Query embedding failed, falling back to lexical search: %s", exc, exc_info=True)

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
