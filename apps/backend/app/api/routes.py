from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field
from app.services.generator import generate_campaign_brief, generate_channel_assets
from app.services.storage import save_generation, list_generations
from fastapi import Depends
from app.core.security import require_internal_api_key
from fastapi import Request
from app.core.rate_limit import limiter

router = APIRouter(prefix="/api")

class CampaignRequest(BaseModel):
    product: str = Field(min_length=2, max_length=120)
    audience: str = Field(min_length=2, max_length=120)
    goal: str = Field(min_length=2, max_length=200)

@router.get("/ping")
def ping():
    return {"message": "pong"}

@router.post("/generate")
@limiter.limit("10/minute")
def generate_campaign(request: Request, payload: CampaignRequest):
    try:
        result = generate_campaign_brief(
            product=payload.product,
            audience=payload.audience,
            goal=payload.goal,
        )
        save_generation(payload.model_dump(), result)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Generation failed: {str(e)}")

@router.post("/generate-assets")
@limiter.limit("10/minute")
def generate_assets(request: Request, payload: CampaignRequest):
    try:
        result = generate_channel_assets(
            product=payload.product,
            audience=payload.audience,
            goal=payload.goal,
        )
        save_generation(payload.model_dump(), result)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Asset generation failed: {str(e)}")

@router.get("/generations", dependencies=[Depends(require_internal_api_key)])
def get_generations(limit: int = Query(default=20, ge=1, le=100)):
    return {"items": list_generations(limit=limit)}
