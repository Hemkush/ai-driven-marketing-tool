import json
from uuid import uuid4

from openai import OpenAI

from app.core.config import settings


def _normalize_asset_type(asset_type: str) -> str:
    return (asset_type or "").strip().lower().replace(" ", "_")


def _fallback_assets(
    project_name: str,
    asset_type: str,
    prompt_text: str,
    num_variants: int,
) -> list[dict]:
    normalized = _normalize_asset_type(asset_type)
    variants: list[dict] = []

    for idx in range(1, num_variants + 1):
        storage_uri = f"mcp://object_storage/{project_name.lower().replace(' ', '-')}/{normalized}/{uuid4().hex}.json"
        if normalized in {"logo", "logo_concept"}:
            metadata = {
                "title": f"Logo concept {idx}",
                "description": f"Brand logo concept for {project_name}",
                "design_prompt": f"{prompt_text} | Clean, memorable, brand-forward identity",
                "format": "concept",
            }
        elif normalized in {"social_post", "instagram_post"}:
            metadata = {
                "title": f"Social post {idx}",
                "headline": f"{project_name}: Stand out with confidence",
                "caption": (
                    f"{prompt_text}\n\n"
                    "Bring your vision to life with reliable execution and premium quality."
                ),
                "cta": "Book your consultation today",
                "hashtags": ["#marketing", "#brand", "#growth"],
            }
        elif normalized in {"ad_copy", "google_ad"}:
            metadata = {
                "title": f"Ad copy {idx}",
                "headline": f"Premium results for {project_name}",
                "description": "High-quality service, clear process, and trusted delivery.",
                "cta": "Get started now",
            }
        else:
            metadata = {
                "title": f"Content asset {idx}",
                "body": f"{prompt_text}\n\nTailored content for {project_name}.",
                "cta": "Learn more",
            }
        variants.append(
            {
                "asset_type": normalized,
                "storage_uri": storage_uri,
                "metadata": metadata,
                "status": "ready",
            }
        )
    return variants


def generate_content_assets(
    project_name: str,
    roadmap: dict,
    strategy: dict,
    asset_type: str,
    prompt_text: str,
    num_variants: int = 3,
) -> list[dict]:
    num_variants = max(1, min(5, num_variants))
    normalized = _normalize_asset_type(asset_type)

    if not settings.can_use_openai():
        return _fallback_assets(project_name, normalized, prompt_text, num_variants)

    prompt = (
        "You are ContentStudioAgent.\n"
        f"Generate {num_variants} {normalized} assets for the business.\n"
        "Return strict JSON as: {\"assets\": [{\"asset_type\": \"...\", \"metadata\": {...}}]}.\n"
        "For each asset include concise market-ready copy in metadata.\n"
        "Do not include markdown.\n\n"
        f"Project: {project_name}\n"
        f"Strategy: {json.dumps(strategy, ensure_ascii=True)}\n"
        f"Roadmap: {json.dumps(roadmap, ensure_ascii=True)}\n"
        f"User prompt: {prompt_text}"
    )

    try:
        client = OpenAI(
            api_key=settings.openai_api_key,
            base_url=settings.openai_base_url,
            timeout=15,
            max_retries=0,
        )
        resp = client.responses.create(
            model=settings.openai_model,
            input=prompt,
        )
        parsed = json.loads(resp.output_text.strip())
        assets = parsed.get("assets", [])
        if not isinstance(assets, list) or not assets:
            return _fallback_assets(project_name, normalized, prompt_text, num_variants)

        generated: list[dict] = []
        for item in assets[:num_variants]:
            if not isinstance(item, dict):
                continue
            metadata = item.get("metadata", {})
            if not isinstance(metadata, dict):
                metadata = {"content": str(metadata)}
            generated.append(
                {
                    "asset_type": item.get("asset_type", normalized),
                    "storage_uri": (
                        f"mcp://object_storage/{project_name.lower().replace(' ', '-')}/"
                        f"{normalized}/{uuid4().hex}.json"
                    ),
                    "metadata": metadata,
                    "status": "ready",
                }
            )
        if not generated:
            return _fallback_assets(project_name, normalized, prompt_text, num_variants)
        return generated
    except Exception:
        return _fallback_assets(project_name, normalized, prompt_text, num_variants)
