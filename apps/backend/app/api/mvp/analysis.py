import json
import logging
from concurrent.futures import ThreadPoolExecutor, as_completed

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.auth import get_current_user
from app.core.pipeline_tracer import trace_step

logger = logging.getLogger(__name__)
from app.core.response_cache import get_cached, make_cache_key, set_cached
from app.db import get_db
from app.models import (
    AnalysisReport,
    QuestionnaireResponse,
    QuestionnaireSession,
    User,
)
from app.services.segment_analyst import answer_analysis_question
from app.services.competitive_benchmarker import run_competitive_benchmarking
from app.services.memory_store import retrieve_relevant_memory

from app.api.mvp.deps import (
    AnalysisAssistantRequest,
    AnalysisRunRequest,
    _resolve_business_profile_id,
    _owned_project_or_404,
    _latest_analysis_or_404,
    _latest_session_for_project,
    _compact_discovery_responses,
    _serialize_analysis_report_row,
)

router = APIRouter(prefix="/api/mvp", tags=["analysis"])


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

    cache_key = make_cache_key("competitive_benchmarker", {
        "address": project.business_address or "",
        "responses": response_payload,
    })
    report_payload = get_cached(db, cache_key, ttl_hours=24)
    if report_payload is None:
        with trace_step(db, step="competitive_benchmarker", project_id=business_profile_id):
            report_payload = run_competitive_benchmarking(
                response_payload,
                business_address=project.business_address,
                conversation_analysis=conversation_analysis,
            )
        set_cached(db, cache_key, agent="competitive_benchmarker", payload=report_payload)
    else:
        logger.info("pipeline_step", extra={"step": "competitive_benchmarker",
            "project_id": business_profile_id, "status": "cached"})

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
    analysis_payload = json.loads(analysis_report.report_json)

    # Run memory retrieval (embedding API call) in parallel with response_payload build
    with ThreadPoolExecutor(max_workers=2) as executor:
        memory_future = executor.submit(
            retrieve_relevant_memory,
            db, business_profile_id, payload.message,
        )
        memory_context_chunks = memory_future.result()

    assistant = answer_analysis_question(
        question=payload.message,
        analysis_report=analysis_payload,
        discovery_responses=response_payload,
        business_address=project.business_address,
        chat_history=payload.history,
        memory_context_chunks=memory_context_chunks,
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
