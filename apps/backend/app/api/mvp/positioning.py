import json

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.auth import get_current_user
from app.db import get_db
from app.models import (
    PositioningStatement,
    User,
)
from app.services.positioning_copilot import generate_positioning

from app.api.mvp.deps import (
    PositioningRefineRequest,
    ProjectScopedRequest,
    _resolve_business_profile_id,
    _owned_project_or_404,
    _latest_analysis_or_404,
    _serialize_positioning_row,
)

router = APIRouter(prefix="/api/mvp", tags=["positioning"])


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
    session_id: int | None = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    _owned_project_or_404(db, current_user, project_id)
    q = db.query(PositioningStatement).filter(PositioningStatement.project_id == project_id)
    if session_id is not None:
        q = q.filter(PositioningStatement.source_session_id == session_id)
    rows = q.order_by(PositioningStatement.version.desc(), PositioningStatement.id.desc()).all()
    return {
        "items": [_serialize_positioning_row(row) for row in rows]
    }
