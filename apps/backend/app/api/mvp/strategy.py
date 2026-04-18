import json

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.auth import get_current_user
from app.core.pipeline_tracer import trace_step
from app.core.response_cache import get_cached, make_cache_key, set_cached
from app.db import get_db
from app.models import (
    ChannelStrategy,
    PersonaProfile,
    ResearchReport,
    RoadmapPlan,
    User,
)
from app.services.channel_strategy_planner import generate_channel_strategy
from app.services.roadmap_planner import generate_roadmap_plan

from app.api.mvp.deps import (
    ProjectScopedRequest,
    _resolve_business_profile_id,
    _owned_project_or_404,
    _serialize_strategy_row,
    _serialize_roadmap_row,
)

router = APIRouter(prefix="/api/mvp", tags=["strategy"])


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
    cache_key = make_cache_key("channel_strategy_planner", {
        "research_report_id": research_row.id,
        "persona_ids": sorted([r.id for r in persona_rows]),
    })
    strategy_payload = get_cached(db, cache_key, ttl_hours=12)
    if strategy_payload is None:
        with trace_step(db, step="channel_strategy_planner", project_id=business_profile_id):
            strategy_payload = generate_channel_strategy(
                project_name=project.name,
                personas=personas,
                research_report=json.loads(research_row.report_json),
            )
        set_cached(db, cache_key, agent="channel_strategy_planner", payload=strategy_payload)

    row = ChannelStrategy(
        project_id=business_profile_id,
        source_session_id=research_row.source_session_id or persona_rows[0].source_session_id,
        strategy_json=json.dumps(strategy_payload),
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    result = _serialize_strategy_row(row) or {}
    return {**result, "status": "ready"}


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
    cache_key = make_cache_key("roadmap_planner", {
        "strategy_id": strategy_row.id,
        "persona_ids": sorted([r.id for r in persona_rows]),
    })
    roadmap_payload = get_cached(db, cache_key, ttl_hours=12)
    if roadmap_payload is None:
        with trace_step(db, step="roadmap_planner", project_id=business_profile_id):
            roadmap_payload = generate_roadmap_plan(
                project_name=project.name,
                strategy=json.loads(strategy_row.strategy_json),
                personas=personas,
            )
        set_cached(db, cache_key, agent="roadmap_planner", payload=roadmap_payload)

    row = RoadmapPlan(
        project_id=business_profile_id,
        source_session_id=strategy_row.source_session_id or persona_rows[0].source_session_id,
        plan_json=json.dumps(roadmap_payload),
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
