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
    QuestionnaireResponse,
    QuestionnaireSession,
    User,
)
from app.services.persona_builder import generate_personas

from app.api.mvp.deps import (
    PersonasGenerateRequest,
    _resolve_business_profile_id,
    _owned_project_or_404,
    _latest_analysis_or_404,
    _safe_json_object,
    _serialize_persona_row,
    _quality_gate,
    _compact_discovery_responses,
)
from app.core.quality_scorer import score_personas

router = APIRouter(prefix="/api/mvp", tags=["personas"])


@router.post("/personas/generate", status_code=status.HTTP_201_CREATED)
def generate_personas_contract(
    payload: PersonasGenerateRequest,
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

    sessions = (
        db.query(QuestionnaireSession)
        .filter(QuestionnaireSession.project_id == business_profile_id)
        .all()
    )
    session_ids = [s.id for s in sessions]
    discovery_responses: list[QuestionnaireResponse] = []
    if session_ids:
        discovery_responses = (
            db.query(QuestionnaireResponse)
            .filter(
                QuestionnaireResponse.session_id.in_(session_ids),
                QuestionnaireResponse.answer_text != "",
                QuestionnaireResponse.source != "agent_rejected",
            )
            .order_by(QuestionnaireResponse.sequence_no.asc())
            .all()
        )
    discovery_payload = _compact_discovery_responses(discovery_responses, max_items=20)
    owner_feedback = (payload.owner_feedback or "").strip()

    cache_key = make_cache_key("persona_builder", {
        "analysis_report_id": analysis_row.id,
        "positioning_id": positioning_row.id if positioning_row else None,
        "discovery_count": len(discovery_payload),
        "owner_feedback": owner_feedback,
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
                discovery_responses=discovery_payload,
                owner_feedback=owner_feedback or None,
                num_personas=3,
            )
        set_cached(db, cache_key, agent="persona_builder", payload={"personas": personas})

    quality_score = score_personas(personas)
    _quality_gate(quality_score, agent="persona_builder")

    # Build generation trace for frontend transparency panel
    analysis_data = json.loads(analysis_row.report_json)
    competitors = analysis_data.get("competitors") or []
    review_snippets = []
    for c in competitors[:6]:
        for s in (c.get("review_snippets") or [])[:2]:
            if s and len(s.strip()) > 20:
                review_snippets.append(s)

    agent_steps = []
    if discovery_payload:
        agent_steps.append(
            f"Loaded {len(discovery_payload)} answers from your marketing discovery interview "
            "to understand your business, services, and target customers in your own words."
        )
    agent_steps.append(
        f"Extracted competitive intelligence: {len(competitors)} local competitor(s) analysed — "
        "services offered, market density, SWOT strengths, and opportunity gaps."
    )
    if review_snippets:
        agent_steps.append(
            f"Mined {len(review_snippets)} real customer review snippets from Google to identify "
            "authentic language, recurring pain points, and buying triggers."
        )
    if positioning_payload:
        seg = positioning_payload.get("target_segment", "")
        agent_steps.append(
            f"Applied your positioning statement and target segment ({seg}) "
            "to align personas with your defined market position."
        )
    if owner_feedback:
        preview = owner_feedback[:100] + ("…" if len(owner_feedback) > 100 else "")
        agent_steps.append(
            f"Incorporated your refinement feedback as highest-priority instructions: \"{preview}\""
        )
    agent_steps.append(
        f"Generated {len(personas)} distinct buyer persona(s) using OpenAI — "
        "each persona required to be specific to your business type, location, and market context."
    )

    data_sources = [
        {"label": "Marketing Discovery Interview",
         "detail": f"{len(discovery_payload)} Q&A answers" if discovery_payload else "Not available"},
        {"label": "Competitive Benchmarking",
         "detail": f"{len(competitors)} competitor(s) · {len(review_snippets)} review snippets"},
        {"label": "SWOT Analysis",
         "detail": f"{len(analysis_data.get('swot_analysis', {}).get('strengths') or [])} strengths · "
                   f"{len(analysis_data.get('swot_analysis', {}).get('opportunities') or [])} opportunities"},
    ]
    if positioning_payload:
        data_sources.append({"label": "Positioning Statement", "detail": "Target segment & differentiators"})
    if owner_feedback:
        data_sources.append({"label": "Owner Feedback", "detail": "Highest-priority refinement"})

    generation_context = {
        "agent_steps": agent_steps,
        "data_sources": data_sources,
        "model": "OpenAI (GPT-4o)",
        "personas_generated": len(personas),
    }

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
        "generation_context": generation_context,
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
