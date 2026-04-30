import json

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.auth import get_current_user
from app.core.pipeline_tracer import trace_step
from app.core.response_cache import get_cached, make_cache_key, set_cached
from app.db import get_db
from app.models import (
    PersonaProfile,
    QuestionnaireResponse,
    QuestionnaireSession,
    ResearchReport,
    User,
)
from app.services.market_researcher import generate_research_report

from app.api.mvp.deps import (
    ResearchRunRequest,
    _resolve_business_profile_id,
    _owned_project_or_404,
    _latest_analysis_or_404,
    _serialize_research_report_row,
    _quality_gate,
)
from app.core.quality_scorer import score_output

router = APIRouter(prefix="/api/mvp", tags=["research"])


@router.post("/research/run", status_code=status.HTTP_201_CREATED)
def run_research_contract(
    payload: ResearchRunRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    business_profile_id = _resolve_business_profile_id(
        payload.business_profile_id, payload.project_id
    )
    project = _owned_project_or_404(db, current_user, business_profile_id)
    analysis_row = _latest_analysis_or_404(db, business_profile_id)

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

    # Fetch latest personas so research can personalise buying journeys per segment
    persona_rows = (
        db.query(PersonaProfile)
        .filter(PersonaProfile.project_id == business_profile_id)
        .order_by(PersonaProfile.id.asc())
        .all()
    )
    personas_payload = []
    for row in persona_rows:
        try:
            personas_payload.append(json.loads(row.persona_json))
        except Exception:
            pass

    focus_area = (payload.focus_area or "").strip()

    cache_key = make_cache_key("market_researcher", {
        "analysis_report_id": analysis_row.id,
        "persona_ids": [r.id for r in persona_rows],
        "focus_area": focus_area,
    })
    research_payload = None if payload.force_refresh else get_cached(db, cache_key, ttl_hours=6)
    if research_payload is None:
        with trace_step(db, step="market_researcher", project_id=business_profile_id):
            research_payload = generate_research_report(
                project_name=project.name,
                questionnaire_responses=response_payload,
                analysis_report=json.loads(analysis_row.report_json),
                business_address=project.business_address,
                personas=personas_payload,
                focus_area=focus_area or None,
            )
        if not research_payload.get("_is_fallback"):
            set_cached(db, cache_key, agent="market_researcher", payload=research_payload)

    quality_score = score_output(
        agent="market_researcher",
        output=research_payload,
        required_keys=["project_name", "target_customer_insights", "competitor_insights", "research_summary"],
        list_keys=["target_customer_insights", "competitor_insights"],
        min_length=200,
    )
    _quality_gate(quality_score, agent="market_researcher")

    report = ResearchReport(
        project_id=business_profile_id,
        source_session_id=analysis_row.source_session_id,
        status="ready",
        report_json=json.dumps(research_payload),
        quality_score=quality_score,
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
