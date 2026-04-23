import json

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.auth import get_current_user
from app.core.pipeline_tracer import trace_step
from app.core.response_cache import get_cached, make_cache_key, set_cached
from app.db import get_db
from app.models import PersonaProfile, RoadmapPlan, User
from app.services.roadmap_planner import generate_roadmap_plan

from app.api.mvp.deps import (
    ProjectScopedRequest,
    _resolve_business_profile_id,
    _owned_project_or_404,
    _serialize_roadmap_row,
    _quality_gate,
)
from app.core.quality_scorer import score_roadmap

router = APIRouter(prefix="/api/mvp", tags=["roadmap"])


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
    cache_key = make_cache_key("roadmap_planner", {
        "persona_ids": sorted([r.id for r in persona_rows]),
    })
    roadmap_payload = get_cached(db, cache_key, ttl_hours=12)
    if roadmap_payload is None:
        with trace_step(db, step="roadmap_planner", project_id=business_profile_id):
            roadmap_payload = generate_roadmap_plan(
                project_name=project.name,
                personas=personas,
            )
        set_cached(db, cache_key, agent="roadmap_planner", payload=roadmap_payload)

    quality_score = score_roadmap(roadmap_payload)
    _quality_gate(quality_score, agent="roadmap_planner")

    row = RoadmapPlan(
        project_id=business_profile_id,
        source_session_id=persona_rows[0].source_session_id,
        plan_json=json.dumps(roadmap_payload),
        quality_score=quality_score,
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    result = _serialize_roadmap_row(row) or {}
    return {**result, "status": "ready"}


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
