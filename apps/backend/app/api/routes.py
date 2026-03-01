from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field
from app.services.generator import generate_campaign_brief, generate_channel_assets
from app.services.storage import save_generation, list_generations

router = APIRouter(prefix="/api")

class CampaignRequest(BaseModel):
    product: str = Field(min_length=2, max_length=120)
    audience: str = Field(min_length=2, max_length=120)
    goal: str = Field(min_length=2, max_length=200)

@router.get("/ping")
def ping():
    return {"message": "pong"}

@router.post("/generate")
def generate_campaign(payload: CampaignRequest):
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
def generate_assets(payload: CampaignRequest):
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

@router.get("/generations")
def get_generations(limit: int = Query(default=20, ge=1, le=100)):
    return {"items": list_generations(limit=limit)}
