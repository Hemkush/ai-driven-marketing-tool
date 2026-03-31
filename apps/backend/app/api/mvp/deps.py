"""
Shared dependencies, helpers, serializers, and Pydantic schemas
used across all MVP route modules.
"""
import json
import re
from datetime import datetime
from difflib import SequenceMatcher

from fastapi import HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.models import (
    AnalysisReport,
    ChannelStrategy,
    MediaAsset,
    PersonaProfile,
    PositioningStatement,
    Project,
    QuestionnaireResponse,
    QuestionnaireSession,
    ResearchReport,
    RoadmapPlan,
    User,
)

# ── Pydantic schemas ───────────────────────────────────────────────────────────

class QuestionnaireSessionCreateRequest(BaseModel):
    business_profile_id: int | None = None
    project_id: int | None = None


class QuestionnaireChatStartRequest(BaseModel):
    business_profile_id: int | None = None
    project_id: int | None = None


class QuestionnaireChatReplyRequest(BaseModel):
    answer_text: str = Field(min_length=1, max_length=10000)


class QuestionnaireChatFinishRequest(BaseModel):
    force: bool = False


class QuestionnaireResponseCreateRequest(BaseModel):
    question_text: str = Field(min_length=2, max_length=5000)
    answer_text: str = Field(default="", max_length=10000)
    question_type: str = Field(default="open_ended", max_length=40)
    source: str = Field(default="system", max_length=40)
    question_options: list[str] = Field(default_factory=list, max_length=6)


class QuestionnaireResponseUpdateRequest(BaseModel):
    answer_text: str = Field(min_length=1, max_length=10000)


class ProjectScopedRequest(BaseModel):
    business_profile_id: int | None = None
    project_id: int | None = None


class AnalysisRunRequest(BaseModel):
    business_profile_id: int | None = None
    project_id: int | None = None
    additional_context: str | None = Field(default=None, max_length=5000)


class AnalysisAssistantRequest(BaseModel):
    business_profile_id: int | None = None
    project_id: int | None = None
    message: str = Field(min_length=1, max_length=5000)
    history: list[dict] = Field(default_factory=list)


class PositioningRefineRequest(BaseModel):
    business_profile_id: int | None = None
    project_id: int | None = None
    owner_feedback: str = Field(min_length=1, max_length=5000)


class ContentGenerationRequest(BaseModel):
    business_profile_id: int | None = None
    project_id: int | None = None
    asset_type: str = Field(min_length=2, max_length=80)
    prompt_text: str = Field(min_length=2, max_length=5000)
    num_variants: int = Field(default=3, ge=1, le=5)
    tone: str = Field(default="professional", max_length=40)


# ── Auth / ownership helpers ───────────────────────────────────────────────────

def _resolve_business_profile_id(
    business_profile_id: int | None,
    project_id: int | None,
) -> int:
    resolved = business_profile_id or project_id
    if not resolved:
        raise HTTPException(
            status_code=422,
            detail="business_profile_id is required",
        )
    return int(resolved)


def _owned_project_or_404(db: Session, user: User, project_id: int) -> Project:
    project = (
        db.query(Project)
        .filter(Project.id == project_id, Project.owner_id == user.id)
        .first()
    )
    if not project:
        raise HTTPException(status_code=404, detail="Business profile not found")
    return project


def _latest_analysis_or_404(db: Session, project_id: int) -> AnalysisReport:
    report = (
        db.query(AnalysisReport)
        .filter(AnalysisReport.project_id == project_id)
        .order_by(AnalysisReport.id.desc())
        .first()
    )
    if not report:
        raise HTTPException(
            status_code=404,
            detail="No analysis report found. Run /api/mvp/analysis/run first.",
        )
    return report


# ── Session query helpers ──────────────────────────────────────────────────────

def _latest_session_for_project(
    db: Session, project_id: int
) -> QuestionnaireSession | None:
    return (
        db.query(QuestionnaireSession)
        .filter(QuestionnaireSession.project_id == project_id)
        .order_by(QuestionnaireSession.updated_at.desc(), QuestionnaireSession.id.desc())
        .first()
    )


def _next_session_after(
    db: Session, project_id: int, created_at: datetime
) -> QuestionnaireSession | None:
    return (
        db.query(QuestionnaireSession)
        .filter(
            QuestionnaireSession.project_id == project_id,
            QuestionnaireSession.created_at > created_at,
        )
        .order_by(QuestionnaireSession.created_at.asc(), QuestionnaireSession.id.asc())
        .first()
    )


def _artifact_for_session(db: Session, model, project_id: int, session: QuestionnaireSession):
    exact = (
        db.query(model)
        .filter(
            model.project_id == project_id,
            model.source_session_id == session.id,
        )
        .order_by(model.id.desc())
        .first()
    )
    if exact:
        return exact

    next_session = _next_session_after(db, project_id, session.created_at)
    query = db.query(model).filter(
        model.project_id == project_id,
        model.created_at >= session.created_at,
    )
    if next_session:
        query = query.filter(model.created_at < next_session.created_at)
    return query.order_by(model.created_at.desc(), model.id.desc()).first()


# ── Serializers ────────────────────────────────────────────────────────────────

def _safe_json_object(raw: str | None) -> dict:
    if not raw:
        return {}
    try:
        parsed = json.loads(raw)
        return parsed if isinstance(parsed, dict) else {}
    except Exception:
        return {}


def _serialize_positioning_row(row: PositioningStatement) -> dict:
    payload = _safe_json_object(row.payload_json)
    merged = {
        "target_segment": payload.get("target_segment", ""),
        "positioning_statement": payload.get("positioning_statement", row.statement_text),
        "tagline": payload.get("tagline", ""),
        "key_differentiators": payload.get("key_differentiators", []),
        "proof_points": payload.get("proof_points", []),
        "rationale": payload.get("rationale", row.rationale),
    }
    return {
        **merged,
        "id": row.id,
        "business_profile_id": row.project_id,
        "project_id": row.project_id,
        "version": row.version,
        "created_at": row.created_at.isoformat(),
        "source_session_id": row.source_session_id,
    }


def _serialize_analysis_report_row(row: AnalysisReport | None) -> dict | None:
    if not row:
        return None
    return {
        "analysis_report_id": row.id,
        "business_profile_id": row.project_id,
        "project_id": row.project_id,
        "status": row.status,
        "report": json.loads(row.report_json),
        "created_at": row.created_at.isoformat(),
        "updated_at": row.updated_at.isoformat(),
        "source_session_id": row.source_session_id,
    }


def _serialize_research_report_row(row: ResearchReport | None) -> dict | None:
    if not row:
        return None
    return {
        "research_report_id": row.id,
        "business_profile_id": row.project_id,
        "project_id": row.project_id,
        "status": row.status,
        "report": json.loads(row.report_json),
        "created_at": row.created_at.isoformat(),
        "source_session_id": row.source_session_id,
    }


def _serialize_persona_row(row: PersonaProfile) -> dict:
    return {
        "id": row.id,
        "name": row.persona_name,
        "profile": json.loads(row.persona_json),
        "created_at": row.created_at.isoformat(),
        "source_session_id": row.source_session_id,
    }


def _serialize_strategy_row(row: ChannelStrategy | None) -> dict | None:
    if not row:
        return None
    return {
        "channel_strategy_id": row.id,
        "business_profile_id": row.project_id,
        "project_id": row.project_id,
        "strategy": json.loads(row.strategy_json),
        "created_at": row.created_at.isoformat(),
        "source_session_id": row.source_session_id,
    }


def _serialize_roadmap_row(row: RoadmapPlan | None) -> dict | None:
    if not row:
        return None
    return {
        "roadmap_plan_id": row.id,
        "business_profile_id": row.project_id,
        "project_id": row.project_id,
        "roadmap": json.loads(row.plan_json),
        "created_at": row.created_at.isoformat(),
        "source_session_id": row.source_session_id,
    }


def _serialize_asset_row(row: MediaAsset) -> dict:
    return {
        "id": row.id,
        "asset_type": row.asset_type,
        "storage_uri": row.storage_uri,
        "prompt_text": row.prompt_text,
        "metadata": json.loads(row.metadata_json),
        "status": row.status,
        "created_at": row.created_at.isoformat(),
        "source_session_id": row.source_session_id,
    }


def _serialize_session_summary(
    session: QuestionnaireSession, responses: list[QuestionnaireResponse]
) -> dict:
    answered = [r for r in responses if (r.answer_text or "").strip()]
    latest_answered = answered[-1] if answered else None
    latest_question = responses[-1] if responses else None
    return {
        "id": session.id,
        "business_profile_id": session.project_id,
        "project_id": session.project_id,
        "status": session.status,
        "created_at": session.created_at.isoformat(),
        "updated_at": session.updated_at.isoformat(),
        "response_count": len(responses),
        "answered_count": len(answered),
        "latest_answered_question": latest_answered.question_text if latest_answered else "",
        "latest_answer_excerpt": (
            " ".join((latest_answered.answer_text or "").split())[:180]
            if latest_answered
            else ""
        ),
        "current_question": latest_question.question_text if latest_question else "",
    }


# ── Questionnaire-specific helpers ────────────────────────────────────────────

def _load_question_options(raw: str | None) -> list[str]:
    if not raw:
        return []
    try:
        parsed = json.loads(raw)
        if not isinstance(parsed, list):
            return []
        return [str(x).strip() for x in parsed if str(x).strip()]
    except Exception:
        return []


def _canonicalize_question(text: str) -> str:
    cleaned = re.sub(r"[^a-z0-9\s]", " ", (text or "").lower())
    cleaned = re.sub(r"\s+", " ", cleaned).strip()
    return cleaned


def _is_duplicate_question(candidate: str, existing_questions: list[str]) -> bool:
    candidate_norm = _canonicalize_question(candidate)
    if not candidate_norm:
        return True

    existing_norms = [_canonicalize_question(q) for q in existing_questions]
    if candidate_norm in existing_norms:
        return True

    stop_words = {
        "what", "which", "who", "why", "how", "is", "are", "the", "a", "an",
        "your", "you", "to", "for", "of", "in", "and", "or", "do", "does",
        "did", "can", "could", "would", "should", "with", "on", "at", "by",
        "from", "that",
    }
    cand_tokens = {t for t in candidate_norm.split() if len(t) > 2 and t not in stop_words}

    for prev in existing_norms:
        if not prev:
            continue
        if SequenceMatcher(None, candidate_norm, prev).ratio() >= 0.82:
            return True
        if candidate_norm in prev or prev in candidate_norm:
            return True
        prev_tokens = {t for t in prev.split() if len(t) > 2 and t not in stop_words}
        if cand_tokens and prev_tokens:
            overlap = len(cand_tokens & prev_tokens) / max(1, min(len(cand_tokens), len(prev_tokens)))
            if overlap >= 0.8:
                return True
    return False


def _pick_non_duplicate_question(existing_questions: list[str], candidates: list[str]) -> str:
    for c in candidates:
        if not _is_duplicate_question(c, existing_questions):
            return c
    defaults = [
        "What customer segment has shown the highest repeat purchase intent so far?",
        "Which marketing channel currently drives the most qualified leads for your business?",
        "What offer could improve conversion by at least 20% in the next 90 days?",
    ]
    for c in defaults:
        if not _is_duplicate_question(c, existing_questions):
            return c
    return "What is one measurable marketing experiment you want to run in the next 30 days?"


def _compact_discovery_responses(
    rows: list[QuestionnaireResponse], max_items: int = 14
) -> list[dict]:
    trimmed = rows[-max_items:] if len(rows) > max_items else rows
    payload: list[dict] = []
    for r in trimmed:
        answer = (r.answer_text or "").strip()
        if not answer:
            continue
        payload.append(
            {
                "question_text": " ".join((r.question_text or "").split())[:180],
                "answer_text": " ".join(answer.split())[:700],
            }
        )
    return payload


def _serialize_response(r: QuestionnaireResponse) -> dict:
    options = _load_question_options(r.question_options_json)
    return {
        "id": r.id,
        "sequence_no": r.sequence_no,
        "question_text": r.question_text,
        "answer_text": r.answer_text,
        "question_type": r.question_type,
        "question_options": options if r.question_type == "mcq" else [],
        "source": r.source,
        "created_at": r.created_at.isoformat(),
        "updated_at": r.updated_at.isoformat(),
    }


def _seed_default_business_questions(db: Session, session: QuestionnaireSession) -> None:
    from app.api.mvp.questionnaire import DEFAULT_BUSINESS_PROFILE_QUESTIONS
    existing = (
        db.query(QuestionnaireResponse)
        .filter(QuestionnaireResponse.session_id == session.id)
        .count()
    )
    if existing > 0:
        return
    for idx, question in enumerate(DEFAULT_BUSINESS_PROFILE_QUESTIONS, start=1):
        db.add(
            QuestionnaireResponse(
                session_id=session.id,
                sequence_no=idx,
                question_text=question["question_text"].strip(),
                answer_text="",
                question_type=question["question_type"],
                question_options_json=json.dumps(question["question_options"]),
                source="system_seeded",
            )
        )
    db.flush()


def _create_chat_question(
    db: Session,
    session_id: int,
    sequence_no: int,
    question_text: str,
    source: str = "chatbot_question",
) -> QuestionnaireResponse:
    row = QuestionnaireResponse(
        session_id=session_id,
        sequence_no=sequence_no,
        question_text=question_text.strip(),
        answer_text="",
        question_type="open_ended",
        question_options_json="[]",
        source=source,
    )
    db.add(row)
    db.flush()
    return row


def _chat_topic_coverage(responses: list[QuestionnaireResponse]) -> dict:
    text = " ".join(
        f"{r.question_text or ''} {r.answer_text or ''}"
        for r in responses
        if (r.answer_text or "").strip()
    ).lower()
    checks = {
        "business": ["business", "offer", "service", "product", "company"],
        "customer": ["customer", "audience", "buyer", "segment"],
        "competitors": ["competitor", "competition", "alternative", "rival"],
        "budget": ["budget", "spend", "ad spend", "marketing budget"],
        "cost": ["cost", "cac", "acquisition cost", "expense"],
        "goal": ["goal", "objective", "target", "12 months", "next year", "plan", "roadmap"],
    }
    return {topic: any(k in text for k in keys) for topic, keys in checks.items()}


# ── Workflow snapshot (cross-domain aggregator) ────────────────────────────────

def _build_session_workflow_snapshot(
    db: Session, project: Project, session: QuestionnaireSession
) -> dict:
    from app.services.onboarding_interviewer import analyze_chat_response

    response_rows = (
        db.query(QuestionnaireResponse)
        .filter(QuestionnaireResponse.session_id == session.id)
        .order_by(QuestionnaireResponse.sequence_no.asc())
        .all()
    )
    answered_rows = [row for row in response_rows if (row.answer_text or "").strip()]
    response_payload = [
        {
            "question_text": row.question_text,
            "answer_text": row.answer_text,
            "question_type": row.question_type,
            "source": row.source,
        }
        for row in answered_rows
    ]
    conversation_analysis = (
        analyze_chat_response(
            response_payload,
            business_context={"business_location": project.business_address},
        )
        if response_payload
        else None
    )

    analysis_row = _artifact_for_session(db, AnalysisReport, project.id, session)
    positioning_row = _artifact_for_session(db, PositioningStatement, project.id, session)
    research_row = _artifact_for_session(db, ResearchReport, project.id, session)
    strategy_row = _artifact_for_session(db, ChannelStrategy, project.id, session)
    roadmap_row = _artifact_for_session(db, RoadmapPlan, project.id, session)

    persona_rows = (
        db.query(PersonaProfile)
        .filter(
            PersonaProfile.project_id == project.id,
            PersonaProfile.source_session_id == session.id,
        )
        .order_by(PersonaProfile.id.asc())
        .all()
    )
    if not persona_rows:
        next_session = _next_session_after(db, project.id, session.created_at)
        persona_query = db.query(PersonaProfile).filter(
            PersonaProfile.project_id == project.id,
            PersonaProfile.created_at >= session.created_at,
        )
        if next_session:
            persona_query = persona_query.filter(PersonaProfile.created_at < next_session.created_at)
        persona_rows = persona_query.order_by(PersonaProfile.id.asc()).all()

    content_rows = (
        db.query(MediaAsset)
        .filter(
            MediaAsset.project_id == project.id,
            MediaAsset.source_session_id == session.id,
        )
        .order_by(MediaAsset.id.desc())
        .all()
    )
    if not content_rows:
        next_session = _next_session_after(db, project.id, session.created_at)
        content_query = db.query(MediaAsset).filter(
            MediaAsset.project_id == project.id,
            MediaAsset.created_at >= session.created_at,
        )
        if next_session:
            content_query = content_query.filter(MediaAsset.created_at < next_session.created_at)
        content_rows = content_query.order_by(MediaAsset.id.desc()).all()

    snapshot = {
        "conversation_analysis": conversation_analysis,
        "analysis": _serialize_analysis_report_row(analysis_row),
        "positioning": _serialize_positioning_row(positioning_row) if positioning_row else None,
        "research": _serialize_research_report_row(research_row),
        "personas": [_serialize_persona_row(row) for row in persona_rows],
        "strategy": _serialize_strategy_row(strategy_row),
        "roadmap": _serialize_roadmap_row(roadmap_row),
        "content_assets": [_serialize_asset_row(row) for row in content_rows],
    }
    progress = {
        "/projects": True,
        "/questionnaire": session.status == "completed",
        "/analysis": bool(snapshot["analysis"]),
        "/positioning": bool(snapshot["positioning"]),
        "/research": bool(snapshot["research"]),
        "/personas": bool(snapshot["personas"]),
        "/strategy": bool(snapshot["strategy"]),
        "/roadmap": bool(snapshot["roadmap"]),
        "/content": bool(snapshot["content_assets"]),
    }
    return {
        "session": _serialize_session_summary(session, response_rows),
        "snapshot": snapshot,
        "progress": progress,
    }
