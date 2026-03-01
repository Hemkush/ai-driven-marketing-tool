import json
from openai import OpenAI
from app.core.config import settings

def _get_client() -> OpenAI:
    settings.validate_openai()
    return OpenAI(
        api_key=settings.openai_api_key,
        base_url=settings.openai_base_url,
    )


def generate_campaign_brief(product: str, audience: str, goal: str) -> dict:
    prompt = f"""
Create a concise marketing campaign brief.

Product: {product}
Audience: {audience}
Goal: {goal}

Return only valid JSON with keys:
headline, value_proposition, cta, channels, ad_copy
"""

    client = _get_client()
    response = client.responses.create(
        model=settings.openai_model,
        input=prompt,
    )

    text = response.output_text.strip()
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        return {
            "headline": f"{product} for {audience}",
            "value_proposition": text,
            "cta": f"Try {product} now",
            "channels": ["email", "social"],
            "ad_copy": text,
        }

def generate_channel_assets(product: str, audience: str, goal: str) -> dict:
    prompt = f"""
Create channel-ready marketing assets.

Product: {product}
Audience: {audience}
Goal: {goal}

Return only valid JSON with keys:
email_subject, email_body, instagram_caption, google_ad_headlines, google_ad_descriptions
"""
    response = client.responses.create(
        model=MODEL,
        input=prompt,
    )

    text = response.output_text.strip()
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        return {
            "email_subject": f"{product} for {audience}",
            "email_body": text,
            "instagram_caption": text[:2200],
            "google_ad_headlines": [f"Try {product}", f"{product} for {audience}", "Get started today"],
            "google_ad_descriptions": [text[:90], f"Built for {audience}. Start now."],
        }
