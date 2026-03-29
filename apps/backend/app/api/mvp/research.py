import json

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.auth import get_current_user
from app.db import get_db
from app.models import (
    QuestionnaireResponse,
    QuestionnaireSession,
    ResearchReport,
    User,
)
from app.services.market_researcher import generate_research_report

from app.api.mvp.deps import (
    ProjectScopedRequest,
    _resolve_business_profile_id,
    _owned_project_or_404,
    _latest_analysis_or_404,
    _serialize_research_report_row,
)

router = APIRouter(prefix="/api/mvp", tags=["research"])


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
