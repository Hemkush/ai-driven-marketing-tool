import json

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.auth import get_current_user
from app.db import get_db
from app.models import (
    ChannelStrategy,
    MediaAsset,
    RoadmapPlan,
    User,
)
from app.services.content_studio import generate_content_assets

from app.api.mvp.deps import (
    ContentGenerationRequest,
    _resolve_business_profile_id,
    _owned_project_or_404,
    _serialize_asset_row,
)

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
        tone=payload.tone,
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
