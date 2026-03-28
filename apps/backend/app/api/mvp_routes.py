import json
import re
from difflib import SequenceMatcher
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.core.auth import get_current_user
from app.core.mvp_registry import AGENT_REGISTRY, MCP_REGISTRY
from app.db import get_db
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
from app.services.onboarding_interviewer import (
    analyze_chat_response,
    generate_next_chat_question,
    generate_next_questions_structured,
)
from app.services.positioning_copilot import generate_positioning
from app.services.market_researcher import generate_research_report
from app.services.persona_builder import generate_personas
from app.services.channel_strategy_planner import generate_channel_strategy
from app.services.roadmap_planner import generate_roadmap_plan
from app.services.content_studio import generate_content_assets
from app.services.segment_analyst import answer_analysis_question
from app.services.competitive_benchmarker import run_competitive_benchmarking
from app.services.memory_store import retrieve_relevant_memory, store_response_memory

router = APIRouter(prefix="/api/mvp", tags=["mvp"])

DEFAULT_BUSINESS_PROFILE_QUESTIONS = [
    {
        "question_text": "Tell me about your business.",
        "question_type": "open_ended",
        "question_options": [],
    },
    {
        "question_text": "Tell me about your customer.",
        "question_type": "open_ended",
        "question_options": [],
    },
    {
        "question_text": "Where is your business located or primarily operating?",
        "question_type": "mcq",
        "question_options": ["Local", "Regional", "Online"],
    },
    {
        "question_text": "What is your primary product or service?",
        "question_type": "open_ended",
        "question_options": [],
    },
    {
        "question_text": "What specific customer problem does your product or service solve?",
        "question_type": "open_ended",
        "question_options": [],
    },
    {
        "question_text": "What makes your business different from competitors?",
        "question_type": "open_ended",
        "question_options": [],
    },
    {
        "question_text": "Who are your top 3 competitors?",
        "question_type": "open_ended",
        "question_options": [],
    },
    {
        "question_text": "How do customers currently find you?",
        "question_type": "mcq",
        "question_options": [
            "Social media",
            "Word of mouth",
            "Paid ads",
            "Search/SEO",
            "Partnerships or referrals",
            "Other",
        ],
    },
    {
        "question_text": "Why do customers choose you over alternatives?",
        "question_type": "mcq",
        "question_options": ["Price", "Quality", "Convenience", "Expertise", "Customization"],
    },
    {
        "question_text": "How would you estimate your current monthly marketing budget?",
        "question_type": "mcq",
        "question_options": [
            "No dedicated budget yet",
            "Under $1,000",
            "$1,000-$5,000",
            "$5,000-$15,000",
            "$15,000+",
        ],
    },
    {
        "question_text": "What is your top business goal for the next 12 months?",
        "question_type": "open_ended",
        "question_options": [],
    },
]


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
        "what",
        "which",
        "who",
        "why",
        "how",
        "is",
        "are",
        "the",
        "a",
        "an",
        "your",
        "you",
        "to",
        "for",
        "of",
        "in",
        "and",
        "or",
        "do",
        "does",
        "did",
        "can",
        "could",
        "would",
        "should",
        "with",
        "on",
        "at",
        "by",
        "from",
        "that",
    }
    cand_tokens = {t for t in candidate_norm.split() if len(t) > 2 and t not in stop_words}

    for prev in existing_norms:
        if not prev:
            continue
        # Catch near-duplicates with minor wording changes.
        if SequenceMatcher(None, candidate_norm, prev).ratio() >= 0.82:
            return True
        # Catch containment variants.
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


def _seed_default_business_questions(db: Session, session: QuestionnaireSession) -> None:
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


def _build_session_workflow_snapshot(
    db: Session, project: Project, session: QuestionnaireSession
) -> dict:
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


@router.get("/system/registry")
def get_system_registry():
    return {"agents": AGENT_REGISTRY, "mcp_servers": MCP_REGISTRY}


@router.get("/questionnaire/templates/business-profile")
def get_business_profile_template():
    return {"items": DEFAULT_BUSINESS_PROFILE_QUESTIONS}


@router.post("/questionnaire/sessions", status_code=status.HTTP_201_CREATED)
def create_questionnaire_session(
    payload: QuestionnaireSessionCreateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    business_profile_id = _resolve_business_profile_id(
        payload.business_profile_id, payload.project_id
    )
    _owned_project_or_404(db, current_user, business_profile_id)
    session = QuestionnaireSession(project_id=business_profile_id, status="in_progress")
    db.add(session)
    db.flush()
    _seed_default_business_questions(db, session)
    db.commit()
    db.refresh(session)
    return {
        "id": session.id,
        "business_profile_id": session.project_id,
        "project_id": session.project_id,
        "status": session.status,
        "created_at": session.created_at.isoformat(),
    }


@router.post("/questionnaire/chat/start", status_code=status.HTTP_201_CREATED)
def start_questionnaire_chat(
    payload: QuestionnaireChatStartRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    business_profile_id = _resolve_business_profile_id(
        payload.business_profile_id, payload.project_id
    )
    _owned_project_or_404(db, current_user, business_profile_id)

    session = QuestionnaireSession(project_id=business_profile_id, status="in_progress")
    db.add(session)
    db.flush()

    first = _create_chat_question(
        db=db,
        session_id=session.id,
        sequence_no=1,
        question_text="Tell me about your business.",
        source="chatbot_seeded",
    )
    db.commit()
    db.refresh(session)

    return {
        "session_id": session.id,
        "status": session.status,
        "business_profile_id": session.project_id,
        "project_id": session.project_id,
        "current_question": _serialize_response(first),
        "messages": [
            {
                "role": "assistant",
                "response_id": first.id,
                "sequence_no": first.sequence_no,
                "question_text": first.question_text,
                "question_type": first.question_type,
                "question_options": [],
                "source": first.source,
            }
        ],
    }


@router.get("/questionnaire/sessions/{session_id}")
def get_questionnaire_session(
    session_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    session = db.get(QuestionnaireSession, session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    _owned_project_or_404(db, current_user, session.project_id)

    responses = (
        db.query(QuestionnaireResponse)
        .filter(QuestionnaireResponse.session_id == session.id)
        .order_by(QuestionnaireResponse.sequence_no.asc())
        .all()
    )
    return {
        "id": session.id,
        "business_profile_id": session.project_id,
        "project_id": session.project_id,
        "status": session.status,
        "created_at": session.created_at.isoformat(),
        "updated_at": session.updated_at.isoformat(),
        "responses": [_serialize_response(r) for r in responses],
    }


@router.get("/questionnaire/sessions/by-business-profile/{project_id}")
def list_questionnaire_sessions_for_project(
    project_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    _owned_project_or_404(db, current_user, project_id)
    sessions = (
        db.query(QuestionnaireSession)
        .filter(QuestionnaireSession.project_id == project_id)
        .order_by(QuestionnaireSession.updated_at.desc(), QuestionnaireSession.id.desc())
        .all()
    )

    items = []
    for session in sessions:
        responses = (
            db.query(QuestionnaireResponse)
            .filter(QuestionnaireResponse.session_id == session.id)
            .order_by(QuestionnaireResponse.sequence_no.asc())
            .all()
        )
        items.append(_serialize_session_summary(session, responses))

    latest = items[0] if items else None
    return {
        "items": items,
        "latest_session_id": latest["id"] if latest else None,
    }


@router.get("/workflow/session-summary/{session_id}")
def get_session_workflow_summary(
    session_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    session = db.get(QuestionnaireSession, session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    project = _owned_project_or_404(db, current_user, session.project_id)
    payload = _build_session_workflow_snapshot(db, project, session)
    return {
        "business_profile_id": project.id,
        "project_id": project.id,
        "business_profile_name": project.name,
        "business_location": project.business_address,
        **payload,
    }


@router.get("/questionnaire/chat/{session_id}")
def get_questionnaire_chat(
    session_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    session = db.get(QuestionnaireSession, session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    project = _owned_project_or_404(db, current_user, session.project_id)

    responses = (
        db.query(QuestionnaireResponse)
        .filter(QuestionnaireResponse.session_id == session.id)
        .order_by(QuestionnaireResponse.sequence_no.asc())
        .all()
    )
    if not responses:
        raise HTTPException(status_code=404, detail="No chat messages found for this session")

    messages = []
    for r in responses:
        messages.append(
            {
                "role": "assistant",
                "response_id": r.id,
                "sequence_no": r.sequence_no,
                "question_text": r.question_text,
                "question_type": r.question_type,
                "question_options": _load_question_options(r.question_options_json),
                "source": r.source,
            }
        )
        if (r.answer_text or "").strip():
            messages.append(
                {
                    "role": "user",
                    "response_id": r.id,
                    "sequence_no": r.sequence_no,
                    "answer_text": r.answer_text,
                }
            )

    return {
        "session_id": session.id,
        "status": session.status,
        "business_profile_id": session.project_id,
        "project_id": session.project_id,
        "messages": messages,
        "current_question": _serialize_response(responses[-1]),
        "coverage": _chat_topic_coverage(responses),
        "analysis": analyze_chat_response(
            [
                {
                    "question_text": r.question_text,
                    "answer_text": r.answer_text,
                    "question_type": r.question_type,
                    "source": r.source,
                }
                for r in responses
                if (r.answer_text or "").strip()
            ],
            business_context={"business_location": project.business_address},
        ),
    }


@router.post("/questionnaire/chat/{session_id}/reply")
def reply_questionnaire_chat(
    session_id: int,
    payload: QuestionnaireChatReplyRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    session = db.get(QuestionnaireSession, session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    project = _owned_project_or_404(db, current_user, session.project_id)
    if session.status == "completed":
        raise HTTPException(
            status_code=400,
            detail="Interview is already completed. Start a new chat session to continue.",
        )

    responses = (
        db.query(QuestionnaireResponse)
        .filter(QuestionnaireResponse.session_id == session.id)
        .order_by(QuestionnaireResponse.sequence_no.asc())
        .all()
    )
    if not responses:
        raise HTTPException(status_code=400, detail="Chat session is not initialized")

    current = responses[-1]
    answer_text = payload.answer_text.strip()
    if not answer_text:
        raise HTTPException(status_code=400, detail="answer_text is required")

    current.answer_text = answer_text
    store_response_memory(
        db,
        project_id=session.project_id,
        session_id=session.id,
        response_id=current.id,
        question_text=current.question_text,
        answer_text=current.answer_text,
    )

    answered_payload = [
        {
            "id": r.id,
            "sequence_no": r.sequence_no,
            "question_text": r.question_text,
            "answer_text": r.answer_text,
            "question_type": r.question_type,
            "source": r.source,
        }
        for r in responses
        if (r.answer_text or "").strip()
    ]
    analysis_payload = analyze_chat_response(
        answered_payload,
        business_context={"business_location": project.business_address},
    )
    session.conversation_analysis_json = json.dumps(analysis_payload)

    existing_questions = [r.question_text for r in responses]
    next_question = generate_next_chat_question(answered_payload)
    next_question_text = str(next_question.get("question_text", "")).strip()
    if not next_question_text:
        next_question_text = "What is your biggest growth bottleneck right now?"

    if _is_duplicate_question(next_question_text, existing_questions):
        fallback_attempts = [
            "Who is your ideal customer, and what are they trying to achieve?",
            "Who are your top competitors, and where are they stronger than you?",
            "What monthly budget can you dedicate to marketing and growth?",
            "What is your current average customer acquisition cost, if known?",
            "What is your most important business plan or goal in the next 12 months?",
            "What is your biggest growth bottleneck right now?",
            "Which channel has brought your best-quality leads in the last 90 days?",
            "What proof points or testimonials do customers mention before purchasing?",
            "Which customer segment is most profitable for your business today?",
        ]
        next_question_text = _pick_non_duplicate_question(existing_questions, fallback_attempts)

    next_row = _create_chat_question(
        db=db,
        session_id=session.id,
        sequence_no=current.sequence_no + 1,
        question_text=next_question_text,
        source="chatbot_generated",
    )
    db.commit()
    db.refresh(current)
    db.refresh(next_row)

    return {
        "session_id": session.id,
        "status": session.status,
        "business_profile_id": session.project_id,
        "project_id": session.project_id,
        "saved_response": {
            "id": current.id,
            "sequence_no": current.sequence_no,
            "question_text": current.question_text,
            "answer_text": current.answer_text,
            "question_type": current.question_type,
            "source": current.source,
            "updated_at": current.updated_at.isoformat(),
        },
        "next_question": _serialize_response(next_row),
        "coverage": _chat_topic_coverage(responses),
        "analysis": analysis_payload,
    }


@router.post("/questionnaire/chat/{session_id}/finish")
def finish_questionnaire_chat(
    session_id: int,
    payload: QuestionnaireChatFinishRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    session = db.get(QuestionnaireSession, session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    _owned_project_or_404(db, current_user, session.project_id)

    responses = (
        db.query(QuestionnaireResponse)
        .filter(QuestionnaireResponse.session_id == session.id)
        .order_by(QuestionnaireResponse.sequence_no.asc())
        .all()
    )
    answered_count = len([r for r in responses if (r.answer_text or "").strip()])
    if answered_count < 3 and not payload.force:
        raise HTTPException(
            status_code=400,
            detail="Please answer at least 3 questions before finishing the interview.",
        )

    coverage = _chat_topic_coverage(responses)
    session.status = "completed"
    db.commit()
    db.refresh(session)

    return {
        "session_id": session.id,
        "status": session.status,
        "business_profile_id": session.project_id,
        "project_id": session.project_id,
        "answered_count": answered_count,
        "coverage": coverage,
        "missing_topics": [k for k, v in coverage.items() if not v],
    }


@router.post("/questionnaire/sessions/{session_id}/responses", status_code=status.HTTP_201_CREATED)
def add_questionnaire_response(
    session_id: int,
    payload: QuestionnaireResponseCreateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    session = db.get(QuestionnaireSession, session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    _owned_project_or_404(db, current_user, session.project_id)

    last = (
        db.query(QuestionnaireResponse)
        .filter(QuestionnaireResponse.session_id == session.id)
        .order_by(QuestionnaireResponse.sequence_no.desc())
        .first()
    )
    next_sequence = (last.sequence_no + 1) if last else 1

    question_type = payload.question_type.strip().lower()
    if question_type not in {"open_ended", "mcq"}:
        raise HTTPException(status_code=400, detail="question_type must be open_ended or mcq")

    options = [x.strip() for x in payload.question_options if x.strip()]
    if question_type == "mcq" and len(options) < 2:
        raise HTTPException(status_code=400, detail="MCQ requires at least 2 options")
    if question_type == "mcq" and payload.answer_text and payload.answer_text not in options:
        raise HTTPException(status_code=400, detail="MCQ answer must match one option")

    response = QuestionnaireResponse(
        session_id=session.id,
        sequence_no=next_sequence,
        question_text=payload.question_text.strip(),
        answer_text=payload.answer_text,
        question_type=question_type,
        question_options_json=json.dumps(options if question_type == "mcq" else []),
        source=payload.source,
    )
    db.add(response)
    db.commit()
    db.refresh(response)
    payload = _serialize_response(response)
    payload["session_id"] = response.session_id
    return payload


@router.patch("/questionnaire/responses/{response_id}")
def update_questionnaire_response(
    response_id: int,
    payload: QuestionnaireResponseUpdateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    response = db.get(QuestionnaireResponse, response_id)
    if not response:
        raise HTTPException(status_code=404, detail="Response not found")
    session = db.get(QuestionnaireSession, response.session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    _owned_project_or_404(db, current_user, session.project_id)

    answer_text = payload.answer_text.strip()
    if response.question_type == "mcq":
        options = _load_question_options(response.question_options_json)
        if options and answer_text not in options:
            raise HTTPException(status_code=400, detail="MCQ answer must match one option")

    response.answer_text = answer_text
    db.commit()
    db.refresh(response)
    return {
        "id": response.id,
        "session_id": response.session_id,
        "answer_text": response.answer_text,
        "updated_at": response.updated_at.isoformat(),
    }


@router.post("/questionnaire/sessions/{session_id}/next-questions")
def generate_next_questions_contract(
    session_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    session = db.get(QuestionnaireSession, session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    _owned_project_or_404(db, current_user, session.project_id)

    responses = (
        db.query(QuestionnaireResponse)
        .filter(QuestionnaireResponse.session_id == session.id)
        .order_by(QuestionnaireResponse.sequence_no.asc())
        .all()
    )
    response_payload = [
        {
            "id": r.id,
            "question_text": r.question_text,
            "answer_text": r.answer_text,
            "question_type": r.question_type,
            "source": r.source,
        }
        for r in responses
        if (r.answer_text or "").strip()
    ]
    questions = generate_next_questions_structured(response_payload, max_questions=3)

    existing_questions = [r.question_text for r in responses]
    last = responses[-1] if responses else None
    next_sequence = (last.sequence_no + 1) if last else 1
    created_suggestions = []

    for question in questions:
        question_text = str(question.get("question_text", "")).strip()
        question_type = str(question.get("question_type", "open_ended")).strip().lower()
        if question_type not in {"open_ended", "mcq"}:
            question_type = "open_ended"
        options = [x.strip() for x in question.get("question_options", []) if x.strip()]
        if question_type == "mcq" and len(options) < 2:
            question_type = "open_ended"
            options = []
        if _is_duplicate_question(question_text, existing_questions):
            continue
        row = QuestionnaireResponse(
            session_id=session.id,
            sequence_no=next_sequence,
            question_text=question_text,
            answer_text="",
            question_type=question_type,
            question_options_json=json.dumps(options if question_type == "mcq" else []),
            source="agent_suggested",
        )
        db.add(row)
        db.flush()
        created = _serialize_response(row)
        created_suggestions.append(
            {
                "id": created["id"],
                "sequence_no": created["sequence_no"],
                "question_text": created["question_text"],
                "question_type": created["question_type"],
                "question_options": created["question_options"],
                "source": created["source"],
            }
        )
        existing_questions.append(question_text)
        next_sequence += 1
    db.commit()

    return {
        "session_id": session.id,
        "agent_id": "onboarding_interviewer",
        "status": "ready",
        "next_questions": [r["question_text"] for r in created_suggestions],
        "suggested_responses": created_suggestions,
    }


@router.post("/questionnaire/responses/{response_id}/accept")
def accept_suggested_question(
    response_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    response = db.get(QuestionnaireResponse, response_id)
    if not response:
        raise HTTPException(status_code=404, detail="Response not found")
    session = db.get(QuestionnaireSession, response.session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    _owned_project_or_404(db, current_user, session.project_id)
    if not response.source.startswith("agent_"):
        raise HTTPException(status_code=400, detail="Only agent suggestions can be accepted")

    response.source = "agent_accepted"
    db.commit()
    db.refresh(response)
    return {
        "id": response.id,
        "session_id": response.session_id,
        "question_text": response.question_text,
        "source": response.source,
    }


@router.post("/questionnaire/responses/{response_id}/reject")
def reject_suggested_question(
    response_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    response = db.get(QuestionnaireResponse, response_id)
    if not response:
        raise HTTPException(status_code=404, detail="Response not found")
    session = db.get(QuestionnaireSession, response.session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    _owned_project_or_404(db, current_user, session.project_id)
    if not response.source.startswith("agent_"):
        raise HTTPException(status_code=400, detail="Only agent suggestions can be rejected")

    response.source = "agent_rejected"
    db.commit()
    db.refresh(response)
    return {
        "id": response.id,
        "session_id": response.session_id,
        "question_text": response.question_text,
        "source": response.source,
    }


@router.post("/analysis/run", status_code=status.HTTP_201_CREATED)
def run_analysis_contract(
    payload: AnalysisRunRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    business_profile_id = _resolve_business_profile_id(
        payload.business_profile_id, payload.project_id
    )
    project = _owned_project_or_404(db, current_user, business_profile_id)
    source_session = _latest_session_for_project(db, business_profile_id)
    sessions = (
        db.query(QuestionnaireSession)
        .filter(QuestionnaireSession.project_id == business_profile_id)
        .all()
    )
    session_ids = [s.id for s in sessions]
    responses: list[QuestionnaireResponse] = []
    if session_ids:
        responses = (
            db.query(QuestionnaireResponse)
            .filter(
                QuestionnaireResponse.session_id.in_(session_ids),
                QuestionnaireResponse.answer_text != "",
                QuestionnaireResponse.source != "agent_rejected",
            )
            .order_by(QuestionnaireResponse.sequence_no.asc())
            .all()
        )

    response_payload = _compact_discovery_responses(responses, max_items=40)
    extra_context = (payload.additional_context or "").strip()
    if extra_context:
        response_payload.append(
            {
                "question_text": "Additional context provided before analysis rerun",
                "answer_text": extra_context,
            }
        )
    conversation_analysis = None
    if source_session and source_session.conversation_analysis_json:
        try:
            conversation_analysis = json.loads(source_session.conversation_analysis_json)
        except Exception:
            pass

    report_payload = run_competitive_benchmarking(
        response_payload,
        business_address=project.business_address,
        conversation_analysis=conversation_analysis,
    )

    report = AnalysisReport(
        project_id=business_profile_id,
        source_session_id=source_session.id if source_session else None,
        status="ready",
        report_json=json.dumps(report_payload),
    )
    db.add(report)
    db.commit()
    db.refresh(report)
    return {
        "analysis_report_id": report.id,
        "business_profile_id": business_profile_id,
        "project_id": business_profile_id,
        "status": report.status,
        "report": report_payload,
        "business_location": project.business_address or "",
        "used_additional_context": bool(extra_context),
        "source_session_id": report.source_session_id,
    }


@router.post("/analysis/assistant/query")
def query_analysis_assistant(
    payload: AnalysisAssistantRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    business_profile_id = _resolve_business_profile_id(
        payload.business_profile_id, payload.project_id
    )
    project = _owned_project_or_404(db, current_user, business_profile_id)
    analysis_report = _latest_analysis_or_404(db, business_profile_id)

    sessions = (
        db.query(QuestionnaireSession)
        .filter(QuestionnaireSession.project_id == business_profile_id)
        .all()
    )
    session_ids = [s.id for s in sessions]
    responses: list[QuestionnaireResponse] = []
    if session_ids:
        responses = (
            db.query(QuestionnaireResponse)
            .filter(
                QuestionnaireResponse.session_id.in_(session_ids),
                QuestionnaireResponse.answer_text != "",
                QuestionnaireResponse.source != "agent_rejected",
            )
            .order_by(QuestionnaireResponse.sequence_no.asc())
            .all()
        )

    response_payload = _compact_discovery_responses(responses, max_items=10)
    assistant = answer_analysis_question(
        question=payload.message,
        analysis_report=json.loads(analysis_report.report_json),
        discovery_responses=response_payload,
        business_address=project.business_address,
        chat_history=payload.history,
        memory_context_chunks=retrieve_relevant_memory(
            db,
            project_id=business_profile_id,
            query=payload.message,
        ),
    )
    return {
        "business_profile_id": business_profile_id,
        "project_id": business_profile_id,
        **assistant,
    }


@router.get("/analysis/latest/{project_id}")
@router.get("/analysis/latest/by-business-profile/{project_id}")
def get_latest_analysis(
    project_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    _owned_project_or_404(db, current_user, project_id)
    report = (
        db.query(AnalysisReport)
        .filter(AnalysisReport.project_id == project_id)
        .order_by(AnalysisReport.id.desc())
        .first()
    )
    if not report:
        raise HTTPException(status_code=404, detail="No analysis report found")
    return _serialize_analysis_report_row(report)


@router.post("/positioning/generate", status_code=status.HTTP_201_CREATED)
def generate_positioning_contract(
    payload: ProjectScopedRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    business_profile_id = _resolve_business_profile_id(
        payload.business_profile_id, payload.project_id
    )
    _owned_project_or_404(db, current_user, business_profile_id)
    analysis_report = _latest_analysis_or_404(db, business_profile_id)
    analysis_payload = json.loads(analysis_report.report_json)
    existing_count = (
        db.query(PositioningStatement)
        .filter(PositioningStatement.project_id == business_profile_id)
        .count()
    )
    positioning_payload = generate_positioning(analysis_payload)
    row = PositioningStatement(
        project_id=business_profile_id,
        source_session_id=analysis_report.source_session_id,
        version=existing_count + 1,
        statement_text=positioning_payload["positioning_statement"],
        rationale=positioning_payload.get("rationale", ""),
        payload_json=json.dumps(positioning_payload),
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    return {
        "positioning_statement_id": row.id,
        "business_profile_id": business_profile_id,
        "project_id": business_profile_id,
        "version": row.version,
        "positioning": _serialize_positioning_row(row),
    }


@router.post("/positioning/refine")
def refine_positioning_contract(
    payload: PositioningRefineRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    business_profile_id = _resolve_business_profile_id(
        payload.business_profile_id, payload.project_id
    )
    _owned_project_or_404(db, current_user, business_profile_id)
    analysis_report = _latest_analysis_or_404(db, business_profile_id)
    analysis_payload = json.loads(analysis_report.report_json)
    existing_count = (
        db.query(PositioningStatement)
        .filter(PositioningStatement.project_id == business_profile_id)
        .count()
    )
    positioning_payload = generate_positioning(
        analysis_report=analysis_payload,
        owner_feedback=payload.owner_feedback,
    )
    row = PositioningStatement(
        project_id=business_profile_id,
        source_session_id=analysis_report.source_session_id,
        version=existing_count + 1,
        statement_text=positioning_payload["positioning_statement"],
        rationale=positioning_payload.get("rationale", ""),
        payload_json=json.dumps(positioning_payload),
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    return {
        "business_profile_id": business_profile_id,
        "project_id": business_profile_id,
        "agent_id": "positioning_copilot",
        "status": "ready",
        "feedback_received": True,
        "positioning": _serialize_positioning_row(row),
    }


@router.get("/positioning/latest/{project_id}")
@router.get("/positioning/latest/by-business-profile/{project_id}")
def get_latest_positioning(
    project_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    _owned_project_or_404(db, current_user, project_id)
    row = (
        db.query(PositioningStatement)
        .filter(PositioningStatement.project_id == project_id)
        .order_by(PositioningStatement.id.desc())
        .first()
    )
    if not row:
        raise HTTPException(status_code=404, detail="No positioning statement found")

    return _serialize_positioning_row(row)


@router.get("/positioning/{project_id}")
@router.get("/positioning/by-business-profile/{project_id}")
def list_positioning_versions(
    project_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    _owned_project_or_404(db, current_user, project_id)
    rows = (
        db.query(PositioningStatement)
        .filter(PositioningStatement.project_id == project_id)
        .order_by(PositioningStatement.version.desc(), PositioningStatement.id.desc())
        .all()
    )
    return {
        "items": [_serialize_positioning_row(row) for row in rows]
    }


@router.post("/research/run", status_code=status.HTTP_201_CREATED)
def run_research_contract(
    payload: ProjectScopedRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    business_profile_id = _resolve_business_profile_id(
        payload.business_profile_id, payload.project_id
    )
    project = _owned_project_or_404(db, current_user, business_profile_id)
    analysis_report = _latest_analysis_or_404(db, business_profile_id)

    sessions = (
        db.query(QuestionnaireSession)
        .filter(QuestionnaireSession.project_id == business_profile_id)
        .all()
    )
    session_ids = [s.id for s in sessions]
    responses: list[QuestionnaireResponse] = []
    if session_ids:
        responses = (
            db.query(QuestionnaireResponse)
            .filter(
                QuestionnaireResponse.session_id.in_(session_ids),
                QuestionnaireResponse.answer_text != "",
                QuestionnaireResponse.source != "agent_rejected",
            )
            .order_by(QuestionnaireResponse.sequence_no.asc())
            .all()
        )

    response_payload = [
        {
            "question_text": r.question_text,
            "answer_text": r.answer_text,
            "question_type": r.question_type,
            "source": r.source,
        }
        for r in responses
    ]
    research_payload = generate_research_report(
        project_name=project.name,
        questionnaire_responses=response_payload,
        analysis_report=json.loads(analysis_report.report_json),
        business_address=project.business_address,
    )

    report = ResearchReport(
        project_id=business_profile_id,
        source_session_id=analysis_report.source_session_id,
        status="ready",
        report_json=json.dumps(research_payload),
    )
    db.add(report)
    db.commit()
    db.refresh(report)
    return _serialize_research_report_row(report)


@router.get("/research/latest/{project_id}")
@router.get("/research/latest/by-business-profile/{project_id}")
def get_latest_research(
    project_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    _owned_project_or_404(db, current_user, project_id)
    report = (
        db.query(ResearchReport)
        .filter(ResearchReport.project_id == project_id)
        .order_by(ResearchReport.id.desc())
        .first()
    )
    if not report:
        raise HTTPException(status_code=404, detail="No research report found")
    return _serialize_research_report_row(report)


@router.post("/personas/generate", status_code=status.HTTP_201_CREATED)
def generate_personas_contract(
    payload: ProjectScopedRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    business_profile_id = _resolve_business_profile_id(
        payload.business_profile_id, payload.project_id
    )
    project = _owned_project_or_404(db, current_user, business_profile_id)
    analysis_row = _latest_analysis_or_404(db, business_profile_id)

    # Use latest positioning statement if available (optional enrichment)
    positioning_row = (
        db.query(PositioningStatement)
        .filter(PositioningStatement.project_id == business_profile_id)
        .order_by(PositioningStatement.id.desc())
        .first()
    )
    positioning_payload = _safe_json_object(positioning_row.payload_json) if positioning_row else None

    personas = generate_personas(
        project_name=project.name,
        analysis_report=json.loads(analysis_row.report_json),
        positioning=positioning_payload,
        num_personas=3,
    )

    created_rows = []
    source_session_id = analysis_row.source_session_id
    if source_session_id:
        (
            db.query(PersonaProfile)
            .filter(
                PersonaProfile.project_id == business_profile_id,
                PersonaProfile.source_session_id == source_session_id,
            )
            .delete()
        )
        db.flush()
    for persona in personas:
        row = PersonaProfile(
            project_id=business_profile_id,
            source_session_id=source_session_id,
            persona_name=persona.get("name", "Unnamed Persona"),
            persona_json=json.dumps(persona),
        )
        db.add(row)
        db.flush()
        created_rows.append(row)
    db.commit()

    return {
        "created_personas": len(created_rows),
        "business_profile_id": business_profile_id,
        "project_id": business_profile_id,
        "status": "ready",
        "personas": [
            _serialize_persona_row(r)
            for r in created_rows
        ],
    }


@router.get("/personas/{project_id}")
@router.get("/personas/by-business-profile/{project_id}")
def list_personas(
    project_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    _owned_project_or_404(db, current_user, project_id)
    rows = (
        db.query(PersonaProfile)
        .filter(PersonaProfile.project_id == project_id)
        .order_by(PersonaProfile.id.asc())
        .all()
    )
    return {
        "items": [
            _serialize_persona_row(r)
            for r in rows
        ]
    }


@router.post("/strategy/generate", status_code=status.HTTP_201_CREATED)
def generate_channel_strategy_contract(
    payload: ProjectScopedRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    business_profile_id = _resolve_business_profile_id(
        payload.business_profile_id, payload.project_id
    )
    project = _owned_project_or_404(db, current_user, business_profile_id)
    research_row = (
        db.query(ResearchReport)
        .filter(ResearchReport.project_id == business_profile_id)
        .order_by(ResearchReport.id.desc())
        .first()
    )
    if not research_row:
        raise HTTPException(
            status_code=404,
            detail="No research report found. Run /api/mvp/research/run first.",
        )
    persona_rows = (
        db.query(PersonaProfile)
        .filter(PersonaProfile.project_id == business_profile_id)
        .order_by(PersonaProfile.id.asc())
        .all()
    )
    if not persona_rows:
        raise HTTPException(
            status_code=404,
            detail="No personas found. Run /api/mvp/personas/generate first.",
        )

    personas = [json.loads(row.persona_json) for row in persona_rows]
    strategy_payload = generate_channel_strategy(
        project_name=project.name,
        personas=personas,
        research_report=json.loads(research_row.report_json),
    )

    row = ChannelStrategy(
        project_id=business_profile_id,
        source_session_id=research_row.source_session_id or persona_rows[0].source_session_id,
        strategy_json=json.dumps(strategy_payload),
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    payload = _serialize_strategy_row(row) or {}
    return {**payload, "status": "ready"}


@router.get("/strategy/latest/{project_id}")
@router.get("/strategy/latest/by-business-profile/{project_id}")
def get_latest_strategy(
    project_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    _owned_project_or_404(db, current_user, project_id)
    row = (
        db.query(ChannelStrategy)
        .filter(ChannelStrategy.project_id == project_id)
        .order_by(ChannelStrategy.id.desc())
        .first()
    )
    if not row:
        raise HTTPException(status_code=404, detail="No channel strategy found")
    return _serialize_strategy_row(row)


@router.post("/roadmap/generate", status_code=status.HTTP_201_CREATED)
def generate_roadmap_contract(
    payload: ProjectScopedRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    business_profile_id = _resolve_business_profile_id(
        payload.business_profile_id, payload.project_id
    )
    project = _owned_project_or_404(db, current_user, business_profile_id)
    strategy_row = (
        db.query(ChannelStrategy)
        .filter(ChannelStrategy.project_id == business_profile_id)
        .order_by(ChannelStrategy.id.desc())
        .first()
    )
    if not strategy_row:
        raise HTTPException(
            status_code=404,
            detail="No strategy found. Run /api/mvp/strategy/generate first.",
        )
    persona_rows = (
        db.query(PersonaProfile)
        .filter(PersonaProfile.project_id == business_profile_id)
        .order_by(PersonaProfile.id.asc())
        .all()
    )
    if not persona_rows:
        raise HTTPException(
            status_code=404,
            detail="No personas found. Run /api/mvp/personas/generate first.",
        )

    personas = [json.loads(row.persona_json) for row in persona_rows]
    roadmap_payload = generate_roadmap_plan(
        project_name=project.name,
        strategy=json.loads(strategy_row.strategy_json),
        personas=personas,
    )

    row = RoadmapPlan(
        project_id=business_profile_id,
        source_session_id=strategy_row.source_session_id or persona_rows[0].source_session_id,
        plan_json=json.dumps(roadmap_payload),
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    payload = _serialize_roadmap_row(row) or {}
    return {**payload, "status": "ready"}


@router.get("/roadmap/latest/{project_id}")
@router.get("/roadmap/latest/by-business-profile/{project_id}")
def get_latest_roadmap(
    project_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    _owned_project_or_404(db, current_user, project_id)
    row = (
        db.query(RoadmapPlan)
        .filter(RoadmapPlan.project_id == project_id)
        .order_by(RoadmapPlan.id.desc())
        .first()
    )
    if not row:
        raise HTTPException(status_code=404, detail="No roadmap found")
    return _serialize_roadmap_row(row)


@router.post("/content/generate", status_code=status.HTTP_201_CREATED)
def generate_content_contract(
    payload: ContentGenerationRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    business_profile_id = _resolve_business_profile_id(
        payload.business_profile_id, payload.project_id
    )
    project = _owned_project_or_404(db, current_user, business_profile_id)
    strategy_row = (
        db.query(ChannelStrategy)
        .filter(ChannelStrategy.project_id == business_profile_id)
        .order_by(ChannelStrategy.id.desc())
        .first()
    )
    if not strategy_row:
        raise HTTPException(
            status_code=404,
            detail="No strategy found. Run /api/mvp/strategy/generate first.",
        )
    roadmap_row = (
        db.query(RoadmapPlan)
        .filter(RoadmapPlan.project_id == business_profile_id)
        .order_by(RoadmapPlan.id.desc())
        .first()
    )
    if not roadmap_row:
        raise HTTPException(
            status_code=404,
            detail="No roadmap found. Run /api/mvp/roadmap/generate first.",
        )

    generated = generate_content_assets(
        project_name=project.name,
        roadmap=json.loads(roadmap_row.plan_json),
        strategy=json.loads(strategy_row.strategy_json),
        asset_type=payload.asset_type,
        prompt_text=payload.prompt_text,
        num_variants=payload.num_variants,
    )

    rows = []
    for item in generated:
        row = MediaAsset(
            project_id=business_profile_id,
            source_session_id=roadmap_row.source_session_id or strategy_row.source_session_id,
            asset_type=item["asset_type"],
            prompt_text=payload.prompt_text,
            storage_uri=item["storage_uri"],
            metadata_json=json.dumps(item["metadata"]),
            status=item.get("status", "ready"),
        )
        db.add(row)
        db.flush()
        rows.append(row)
    db.commit()

    return {
        "status": "ready",
        "business_profile_id": business_profile_id,
        "project_id": business_profile_id,
        "generated_count": len(rows),
        "assets": [_serialize_asset_row(r) for r in rows],
    }


@router.get("/content/assets/{project_id}")
@router.get("/content/assets/by-business-profile/{project_id}")
def list_content_assets(
    project_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    _owned_project_or_404(db, current_user, project_id)
    rows = (
        db.query(MediaAsset)
        .filter(MediaAsset.project_id == project_id)
        .order_by(MediaAsset.id.desc())
        .all()
    )
    return {
        "items": [_serialize_asset_row(r) for r in rows]
    }


@router.get("/content/assets/item/{asset_id}")
def get_content_asset(
    asset_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    row = db.get(MediaAsset, asset_id)
    if not row:
        raise HTTPException(status_code=404, detail="Asset not found")
    _owned_project_or_404(db, current_user, row.project_id)
    return {
        "business_profile_id": row.project_id,
        "project_id": row.project_id,
        **_serialize_asset_row(row),
    }
