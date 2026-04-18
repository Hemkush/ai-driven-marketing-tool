import json
import logging
from uuid import uuid4

from openai import OpenAI

from app.core.config import settings
from app.core.llm_tracker import tracked_chat, tracked_image
from app.core.quality_scorer import score_content

logger = logging.getLogger(__name__)

# ── Type classification ────────────────────────────────────────────────────────

VISUAL_TYPES = {"logo", "poster", "banner", "social_visual", "social_media_visual"}

TONE_DESCRIPTIONS = {
    "professional": "formal, authoritative, and polished — industry-standard language",
    "friendly":     "warm, conversational, and approachable — like talking to a trusted local",
    "urgent":       "action-oriented, time-sensitive, and compelling — motivates immediate action",
    "playful":      "fun, energetic, and lighthearted — memorable and personality-driven",
    "bold":         "direct, confident, and striking — no fluff, maximum impact",
}

TYPE_PROMPTS = {
    "social_post": (
        "Generate a social media post. Return JSON:\n"
        '{"caption": "full post text", "hook": "opening line that stops the scroll", '
        '"hashtags": ["tag1","tag2","tag3","tag4","tag5"], "cta": "call-to-action text", '
        '"image_prompt": "describe the ideal photo or graphic to pair with this post"}'
    ),
    "instagram_caption": (
        "Generate an Instagram caption. Return JSON:\n"
        '{"caption": "full caption with line breaks", "hook": "strong opening line", '
        '"hashtags": ["tag1",...,"tag10"], "cta": "call-to-action", '
        '"image_prompt": "describe the ideal Instagram visual to pair with this"}'
    ),
    "google_business_post": (
        "Generate a Google Business Profile post (max 1500 chars). Return JSON:\n"
        '{"title": "post title", "body": "post body text", "cta": "Book / Call / Learn More", '
        '"event_or_offer": "optional offer or event details"}'
    ),
    "email_newsletter": (
        "Generate a full email newsletter. Return JSON:\n"
        '{"subject": "subject line", "preview_text": "preview/preheader text (max 90 chars)", '
        '"sections": [{"heading": "section title", "body": "section content"}], '
        '"cta": "primary CTA text", "cta_url_placeholder": "https://yoursite.com/page", '
        '"ps_line": "optional P.S. line at the bottom"}'
    ),
    "blog_post_intro": (
        "Generate a blog post introduction. Return JSON:\n"
        '{"title": "SEO-optimised post title", "meta_description": "meta description under 160 chars", '
        '"intro": "opening 2–3 paragraphs", '
        '"outline": ["Section 1 title", "Section 2 title", "Section 3 title", "Section 4 title"], '
        '"keywords": ["keyword1", "keyword2", "keyword3"]}'
    ),
    "landing_page_copy": (
        "Generate landing page copy. Return JSON:\n"
        '{"headline": "main headline", "subheadline": "supporting copy under headline", '
        '"sections": [{"heading": "heading", "body": "copy for this section"}], '
        '"cta": "primary CTA text", '
        '"trust_signals": ["social proof or trust element 1", "element 2", "element 3"]}'
    ),
    "ad_copy": (
        "Generate Google / Meta ad copy. Return JSON:\n"
        '{"headline_1": "max 30 chars", "headline_2": "max 30 chars", "headline_3": "max 30 chars", '
        '"description_1": "max 90 chars", "description_2": "max 90 chars", '
        '"cta": "single action word e.g. Book/Shop/Call", "platform_notes": "any platform-specific advice"}'
    ),
    "sms_campaign": (
        "Generate an SMS marketing message (max 160 chars). Return JSON:\n"
        '{"message": "full SMS text under 160 chars including opt-out", '
        '"cta": "action e.g. Reply YES, Click link", "char_count_note": "estimated character count"}'
    ),
    "press_release": (
        "Generate a press release. Return JSON:\n"
        '{"headline": "press release headline", "subheadline": "supporting headline", '
        '"dateline": "CITY, Date —", "lead_paragraph": "who/what/when/where/why opening", '
        '"body_paragraphs": ["paragraph 1", "paragraph 2", "paragraph 3"], '
        '"boilerplate": "About [company] — one paragraph company description", '
        '"contact": "Media contact placeholder"}'
    ),
}

VISUAL_BRIEF_PROMPT = (
    "Generate a detailed visual design brief AND a DALL-E image generation prompt. Return JSON:\n"
    '{"design_brief": {'
    '"concept": "core visual concept and brand story", '
    '"color_palette": ["#hex1", "#hex2", "#hex3"], '
    '"typography": "font style recommendation", '
    '"style": "visual style e.g. minimalist, bold, vintage", '
    '"mood": "emotional tone of the design", '
    '"usage_notes": "where and how to use this asset"'
    '}, '
    '"dalle_prompt": "detailed, specific DALL-E 3 prompt (describe exactly what to generate)"}'
)


def _normalize(asset_type: str) -> str:
    return (asset_type or "").strip().lower().replace(" ", "_").replace("/", "_")


def _is_visual(normalized: str) -> bool:
    return normalized in VISUAL_TYPES


def _get_tone_desc(tone: str) -> str:
    return TONE_DESCRIPTIONS.get(tone.lower().strip(), TONE_DESCRIPTIONS["professional"])


def _storage_uri(project_name: str, normalized: str) -> str:
    slug = project_name.lower().replace(" ", "-")
    return f"mcp://object_storage/{slug}/{normalized}/{uuid4().hex}.json"


# ── Fallback (no OpenAI) ───────────────────────────────────────────────────────

def _fallback_assets(project_name: str, normalized: str, prompt_text: str, num_variants: int) -> list[dict]:
    variants = []
    for idx in range(1, num_variants + 1):
        if _is_visual(normalized):
            metadata = {
                "image_data": None,
                "dalle_error": "OpenAI not configured — design brief generated as fallback",
                "design_brief": {
                    "concept": f"Clean, modern {normalized} for {project_name}",
                    "color_palette": ["#1e40af", "#f8fafc", "#0f172a"],
                    "typography": "Sans-serif, geometric",
                    "style": "Minimalist, professional",
                    "mood": "Trustworthy and approachable",
                    "usage_notes": f"Use across all {normalized} placements",
                },
                "dalle_prompt": f"Professional {normalized} design for {project_name}, minimalist, clean, modern brand identity",
            }
        else:
            metadata = {
                "title": f"{normalized.replace('_', ' ').title()} — {project_name} (variant {idx})",
                "body": f"{prompt_text}\n\nBuilt for {project_name}. Contact us to learn more.",
                "cta": "Get in touch today",
            }
        variants.append({
            "asset_type": normalized,
            "storage_uri": _storage_uri(project_name, normalized),
            "metadata": metadata,
            "status": "ready",
        })
    return variants


# ── Text generation ────────────────────────────────────────────────────────────

def _generate_text_assets(
    client: OpenAI,
    project_name: str,
    strategy: dict,
    roadmap: dict,
    normalized: str,
    prompt_text: str,
    tone: str,
    num_variants: int,
) -> list[dict]:
    type_instruction = TYPE_PROMPTS.get(normalized, (
        f'Generate a {normalized.replace("_", " ")} asset. Return JSON with relevant fields '
        '(title, body, cta, and any type-specific fields).'
    ))
    tone_desc = _get_tone_desc(tone)

    system = (
        f"You are ContentStudioAgent for {project_name}.\n"
        f"Tone: {tone_desc}\n"
        "Output strict JSON only — no markdown, no explanation.\n"
        f"Business strategy summary: {json.dumps(strategy, ensure_ascii=True)[:800]}\n"
        f"Roadmap summary: {json.dumps(roadmap, ensure_ascii=True)[:600]}"
    )
    user = f"{type_instruction}\n\nAdditional context: {prompt_text}"

    results = []
    for _ in range(num_variants):
        try:
            resp = tracked_chat(client, agent="content_studio",
                model=settings.openai_model,
                messages=[{"role": "system", "content": system}, {"role": "user", "content": user}],
                response_format={"type": "json_object"},
                temperature=0.8,
                timeout=30,
            )
            raw = resp.choices[0].message.content.strip()
            metadata = json.loads(raw)
            if not isinstance(metadata, dict):
                metadata = {"content": raw}
        except Exception:
            metadata = {"title": f"{normalized} for {project_name}", "body": prompt_text, "cta": "Contact us"}

        results.append({
            "asset_type": normalized,
            "storage_uri": _storage_uri(project_name, normalized),
            "metadata": metadata,
            "status": "ready",
        })
    return results


# ── Visual generation (DALL-E 3 + design brief) ───────────────────────────────

def _generate_visual_assets(
    client: OpenAI,
    project_name: str,
    strategy: dict,
    normalized: str,
    prompt_text: str,
    tone: str,
    num_variants: int,
) -> list[dict]:
    tone_desc = _get_tone_desc(tone)

    # Step 1: Generate design brief + DALL-E prompt via chat
    brief_system = (
        f"You are a senior brand designer creating a {normalized.replace('_', ' ')} for {project_name}.\n"
        f"Tone/style: {tone_desc}\n"
        "Output strict JSON only — no markdown, no explanation.\n"
        f"Strategy context: {json.dumps(strategy, ensure_ascii=True)[:600]}"
    )
    brief_user = f"{VISUAL_BRIEF_PROMPT}\n\nAdditional direction: {prompt_text}"

    results = []
    for _ in range(num_variants):
        image_url = None
        dalle_prompt = None
        design_brief = {}

        try:
            brief_resp = tracked_chat(client, agent="content_studio_brief",
                model=settings.openai_model,
                messages=[{"role": "system", "content": brief_system}, {"role": "user", "content": brief_user}],
                response_format={"type": "json_object"},
                temperature=0.85,
                timeout=25,
            )
            brief_data = json.loads(brief_resp.choices[0].message.content.strip())
            design_brief = brief_data.get("design_brief", {})
            dalle_prompt = brief_data.get("dalle_prompt", "")
        except Exception:
            dalle_prompt = (
                f"Professional {normalized.replace('_', ' ')} design for {project_name}, "
                f"{tone_desc}, clean and modern"
            )

        # Step 2: Generate image with DALL-E 3
        # Use response_format="b64_json" so the image is returned as base64 — it is
        # stored directly in the DB and never expires (unlike temporary DALL-E URLs).
        image_data = None  # base64 data URL — permanent, works after reload
        dalle_error = None
        if dalle_prompt:
            try:
                img_resp = tracked_image(client, agent="content_studio",
                    model="dall-e-3",
                    prompt=dalle_prompt[:4000],
                    size="1024x1024",
                    quality="standard",
                    response_format="b64_json",
                    n=1,
                )
                b64 = img_resp.data[0].b64_json
                if b64:
                    image_data = f"data:image/png;base64,{b64}"
            except Exception as e:
                dalle_error = str(e)

        results.append({
            "asset_type": normalized,
            "storage_uri": _storage_uri(project_name, normalized),
            "metadata": {
                "image_data": image_data,   # permanent base64 data URL
                "dalle_error": dalle_error, # surfaced to UI if generation failed
                "design_brief": design_brief,
                "dalle_prompt": dalle_prompt,
            },
            "status": "ready",
        })
    return results


# ── Public entry point ─────────────────────────────────────────────────────────

def generate_content_assets(
    project_name: str,
    roadmap: dict,
    strategy: dict,
    asset_type: str,
    prompt_text: str,
    num_variants: int = 3,
    tone: str = "professional",
) -> list[dict]:
    num_variants = max(1, min(5, num_variants))
    normalized = _normalize(asset_type)

    if not settings.can_use_openai():
        return _fallback_assets(project_name, normalized, prompt_text, num_variants)

    client = OpenAI(
        api_key=settings.openai_api_key,
        base_url=settings.openai_base_url,
        timeout=45,
        max_retries=0,
    )

    try:
        if _is_visual(normalized):
            assets = _generate_visual_assets(client, project_name, strategy, normalized, prompt_text, tone, num_variants)
        else:
            assets = _generate_text_assets(client, project_name, strategy, roadmap, normalized, prompt_text, tone, num_variants)
        score_content(assets)
        return assets
    except Exception:
        return _fallback_assets(project_name, normalized, prompt_text, num_variants)
