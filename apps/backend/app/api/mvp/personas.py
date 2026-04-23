import json

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.core.auth import get_current_user
from app.core.pipeline_tracer import trace_step
from app.core.response_cache import get_cached, make_cache_key, set_cached
from app.db import get_db
from app.models import (
    PersonaProfile,
    PositioningStatement,
    User,
)
from app.services.persona_builder import generate_personas

from app.api.mvp.deps import (
    ProjectScopedRequest,
    _resolve_business_profile_id,
    _owned_project_or_404,
    _latest_analysis_or_404,
    _safe_json_object,
    _serialize_persona_row,
    _quality_gate,
)
from app.core.quality_scorer import score_personas

router = APIRouter(prefix="/api/mvp", tags=["personas"])


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

    positioning_row = (
        db.query(PositioningStatement)
        .filter(PositioningStatement.project_id == business_profile_id)
        .order_by(PositioningStatement.id.desc())
        .first()
    )
    positioning_payload = _safe_json_object(positioning_row.payload_json) if positioning_row else None

    cache_key = make_cache_key("persona_builder", {
        "analysis_report_id": analysis_row.id,
        "positioning_id": positioning_row.id if positioning_row else None,
    })
    cached_personas = get_cached(db, cache_key, ttl_hours=6)
    if cached_personas is not None:
        personas = cached_personas.get("personas", cached_personas) if isinstance(cached_personas, dict) else cached_personas
    else:
        with trace_step(db, step="persona_builder", project_id=business_profile_id):
            personas = generate_personas(
                project_name=project.name,
                analysis_report=json.loads(analysis_row.report_json),
                positioning=positioning_payload,
                num_personas=3,
            )
        set_cached(db, cache_key, agent="persona_builder", payload={"personas": personas})

    quality_score = score_personas(personas)
    _quality_gate(quality_score, agent="persona_builder")

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
            quality_score=quality_score,
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
        "personas": [_serialize_persona_row(r) for r in created_rows],
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
        "items": [_serialize_persona_row(r) for r in rows]
    }
