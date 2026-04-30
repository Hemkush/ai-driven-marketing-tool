import json

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.auth import get_current_user
from app.core.response_cache import get_cached, make_cache_key, set_cached
from app.db import get_db
from app.models import (
    AnalysisReport,
    MediaAsset,
    PersonaProfile,
    RoadmapPlan,
    User,
)
from app.services.content_studio import generate_content_assets, suggest_tone

from app.api.mvp.deps import (
    ContentGenerationRequest,
    _resolve_business_profile_id,
    _owned_project_or_404,
    _serialize_asset_row,
    _quality_gate,
)
from app.core.quality_scorer import score_content

router = APIRouter(prefix="/api/mvp", tags=["content"])


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
        strategy={},
        asset_type=payload.asset_type,
        prompt_text=payload.prompt_text,
        num_variants=payload.num_variants,
        tone=payload.tone,
    )

    quality_score = score_content(generated)
    _quality_gate(quality_score, agent="content_studio")

    rows = []
    for item in generated:
        row = MediaAsset(
            project_id=business_profile_id,
            source_session_id=roadmap_row.source_session_id,
            asset_type=item["asset_type"],
            prompt_text=payload.prompt_text,
            storage_uri=item["storage_uri"],
            metadata_json=json.dumps(item["metadata"]),
            status=item.get("status", "ready"),
            quality_score=quality_score,
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


@router.get("/content/suggest-tone/{project_id}")
def suggest_tone_contract(
    project_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    project = _owned_project_or_404(db, current_user, project_id)

    persona_rows = (
        db.query(PersonaProfile)
        .filter(PersonaProfile.project_id == project_id)
        .order_by(PersonaProfile.id.asc())
        .all()
    )
    if not persona_rows:
        raise HTTPException(
            status_code=404,
            detail="No personas found. Run /api/mvp/personas/generate first.",
        )

    personas = [json.loads(row.persona_json) for row in persona_rows]

    research_row = (
        db.query(AnalysisReport)
        .filter(AnalysisReport.project_id == project_id)
        .order_by(AnalysisReport.id.desc())
        .first()
    )
    research = json.loads(research_row.report_json) if research_row else None

    cache_key = make_cache_key("tone_suggester", {
        "persona_ids": sorted([r.id for r in persona_rows]),
        "research_id": research_row.id if research_row else None,
    })
    result = get_cached(db, cache_key, ttl_hours=24)
    if result is None:
        result = suggest_tone(
            project_name=project.name,
            personas=personas,
            research=research,
        )
        set_cached(db, cache_key, agent="tone_suggester", payload=result)

    return result
