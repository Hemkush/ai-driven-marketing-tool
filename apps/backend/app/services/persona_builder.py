import json

from openai import OpenAI

from app.core.config import settings
from app.core.llm_tracker import tracked_responses
from app.core.quality_scorer import score_personas


def _extract_context(analysis_report: dict, positioning: dict | None) -> dict:
    """Pull the useful fields from a competitive benchmarking report for persona generation."""
    market = analysis_report.get("market_overview") or {}
    competitors = analysis_report.get("competitors") or []
    swot = analysis_report.get("swot_analysis") or {}

    top_competitor_services = []
    review_snippets = []
    review_summaries = []

    for c in competitors[:6]:
        top_competitor_services.extend(c.get("services_offered") or [])
        # Collect raw review snippets (real customer voice)
        for snippet in (c.get("review_snippets") or [])[:2]:
            if snippet and len(snippet.strip()) > 20:
                review_snippets.append(snippet.strip()[:180])
        # Collect AI-generated review summaries
        summary = (c.get("review_summary") or "").strip()
        if summary:
            review_summaries.append(f"{c.get('name', '')}: {summary}")

    # Deduplicate services
    top_competitor_services = list(dict.fromkeys(top_competitor_services))[:10]

    ctx = {
        "business_type": analysis_report.get("business_keyword", "local business"),
        "location": analysis_report.get("business_location", ""),
        "market_density": market.get("market_density", "medium"),
        "opportunity_gaps": market.get("opportunity_gaps") or [],
        "competitor_services": top_competitor_services,
        "swot_strengths": swot.get("strengths") or [],
        "swot_opportunities": swot.get("opportunities") or [],
        "customer_review_snippets": review_snippets[:10],
        "competitor_review_summaries": review_summaries[:6],
    }

    if positioning:
        ctx["target_segment"] = positioning.get("target_segment", "")
        ctx["positioning_statement"] = positioning.get("positioning_statement", "")
        ctx["key_differentiators"] = positioning.get("key_differentiators") or []

    return ctx


def _fallback_personas(business_type: str, location: str) -> list[dict]:
    loc = location or "your area"
    btype = business_type or "local business"
    return [
        {
            "name": f"Loyal Local Laura",
            "basic_profile": {
                "age": "34",
                "occupation": "Teacher / Office professional",
                "income": "Mid-income",
                "location": loc,
                "family_status": "Married with children",
                "photo_prompt": f"Friendly woman in her 30s visiting a local {btype}, warm natural style",
            },
            "psychographic_profile": {
                "goals_and_motivations": f"Find a reliable, consistent {btype} she can trust and keep coming back to.",
                "pain_points_and_frustrations": "Tired of inconsistent quality and having to search for a new provider each time.",
                "values_and_priorities": "Reliability, convenience, value for money, personal relationships.",
                "lifestyle_and_interests": "Family-oriented, community-focused, values local businesses.",
            },
            "behavioral_profile": {
                "shopping_preferences": "Books in advance, prefers familiar providers, influenced by word-of-mouth.",
                "decision_making_process": "Asks friends first, checks Google reviews, books if ratings are 4.5+.",
                "information_sources": "Google Maps, Facebook, local community groups, friend referrals.",
                "buying_triggers_and_barriers": f"Trigger: strong reviews and easy booking. Barrier: no online booking or unclear pricing.",
            },
            "engagement_strategy": {
                "preferred_channels": ["Google Search", "Facebook", "Local community groups"],
                "resonant_content_topics": ["Customer testimonials", "Before/after results", "Meet the team"],
                "best_times_to_reach": "Evenings and weekends",
                "key_messages_that_convert": f"Your trusted neighbourhood {btype} — consistent quality, every time.",
            },
        },
        {
            "name": "Trendy Newcomer Nadia",
            "basic_profile": {
                "age": "26",
                "occupation": "Young professional / Recent graduate",
                "income": "Entry to mid-income",
                "location": loc,
                "family_status": "Single or newly partnered",
                "photo_prompt": f"Stylish young woman exploring a new {btype} in a vibrant neighbourhood",
            },
            "psychographic_profile": {
                "goals_and_motivations": f"Try the best {btype} options in the area and share experiences online.",
                "pain_points_and_frustrations": "Hard to discover quality local options; too many generic chain providers.",
                "values_and_priorities": "Aesthetics, novelty, social validation, Instagram-worthy experiences.",
                "lifestyle_and_interests": "Social media active, trend-conscious, explores new local spots.",
            },
            "behavioral_profile": {
                "shopping_preferences": "Discovers via Instagram or TikTok, books same-day or next-day.",
                "decision_making_process": "Visual first — photos sell her before reviews do.",
                "information_sources": "Instagram, TikTok, Google Maps photos, influencer content.",
                "buying_triggers_and_barriers": "Trigger: aspirational photos and quick response to DMs. Barrier: no social presence.",
            },
            "engagement_strategy": {
                "preferred_channels": ["Instagram", "TikTok", "Google Maps"],
                "resonant_content_topics": ["Reels/short videos", "Transformation content", "Behind-the-scenes"],
                "best_times_to_reach": "Lunch breaks and evenings",
                "key_messages_that_convert": f"The {btype} everyone in {loc} is talking about.",
            },
        },
        {
            "name": "Value-Seeker Victor",
            "basic_profile": {
                "age": "41",
                "occupation": "Self-employed / Trades / Small business owner",
                "income": "Varies — value-conscious",
                "location": loc,
                "family_status": "Married",
                "photo_prompt": f"Practical man in his 40s researching local {btype} options on his phone",
            },
            "psychographic_profile": {
                "goals_and_motivations": f"Get reliable {btype} service without overpaying or wasting time.",
                "pain_points_and_frustrations": "Overpriced services that don't deliver value; wasted trips.",
                "values_and_priorities": "Value for money, efficiency, directness, no-nonsense service.",
                "lifestyle_and_interests": "Practical, time-poor, trusts proven providers over new ones.",
            },
            "behavioral_profile": {
                "shopping_preferences": "Price-compares, reads detailed reviews, calls ahead to ask questions.",
                "decision_making_process": "Logical — compares 3 options on Google, picks best value with good reviews.",
                "information_sources": "Google Search, Google Maps reviews, direct calls.",
                "buying_triggers_and_barriers": "Trigger: transparent pricing and fast turnaround. Barrier: hidden costs or no clear pricing.",
            },
            "engagement_strategy": {
                "preferred_channels": ["Google Search", "Phone / Direct call", "Google Maps"],
                "resonant_content_topics": ["Pricing transparency", "How-it-works", "Time savings"],
                "best_times_to_reach": "Early morning or lunch",
                "key_messages_that_convert": f"Quality {btype} at a fair price — no surprises.",
            },
        },
    ]


def generate_personas(
    project_name: str,
    analysis_report: dict,
    positioning: dict | None = None,
    num_personas: int = 3,
) -> list[dict]:
    num_personas = max(2, min(3, num_personas))
    ctx = _extract_context(analysis_report, positioning)

    if not settings.can_use_openai():
        return _fallback_personas(ctx["business_type"], ctx["location"])[:num_personas]

    pos_block = ""
    if positioning:
        pos_block = (
            f"\nPositioning statement: {ctx.get('positioning_statement', '')}\n"
            f"Target segment: {ctx.get('target_segment', '')}\n"
            f"Key differentiators: {', '.join(ctx.get('key_differentiators') or [])}\n"
        )

    prompt = (
        "You are PersonaBuilderAgent for an AI marketing strategy platform.\n"
        f"Generate exactly {num_personas} distinct buyer personas for a {ctx['business_type']} "
        f"business in {ctx['location'] or 'a local area'}.\n\n"
        "Each persona must be:\n"
        "- Specific to this business type and local market — not generic\n"
        "- Distinctly different from the others (age, motivation, behaviour must not overlap)\n"
        "- Grounded in the market context provided below\n\n"
        "Return strict JSON as: {\"personas\": [...]}.\n"
        "Each persona object must have these exact keys:\n"
        "  name (memorable first name + descriptor e.g. 'Loyal Local Laura'),\n"
        "  basic_profile: { age, occupation, income, location, family_status, photo_prompt },\n"
        "  psychographic_profile: { goals_and_motivations, pain_points_and_frustrations, values_and_priorities, lifestyle_and_interests },\n"
        "  behavioral_profile: { shopping_preferences, decision_making_process, information_sources, buying_triggers_and_barriers },\n"
        "  engagement_strategy: { preferred_channels (array), resonant_content_topics (array), best_times_to_reach, key_messages_that_convert }\n\n"
        f"Business type: {ctx['business_type']}\n"
        f"Location: {ctx['location']}\n"
        f"Market density: {ctx['market_density']}\n"
        f"Market opportunity gaps: {', '.join(ctx['opportunity_gaps']) or 'none identified'}\n"
        f"SWOT strengths: {', '.join(ctx['swot_strengths']) or 'not available'}\n"
        f"SWOT opportunities: {', '.join(ctx['swot_opportunities']) or 'not available'}\n"
        f"Services competitors offer: {', '.join(ctx['competitor_services']) or 'not available'}\n"
        + (
            "Real customer reviews from Google (written in customers' own words — use these to "
            "identify actual language, motivations, and pain points):\n"
            + "\n".join(f'- "{s}"' for s in ctx["customer_review_snippets"])
            + "\n\n"
            if ctx["customer_review_snippets"] else ""
        )
        + (
            "AI-summarised sentiment per competitor (what customers love vs complain about):\n"
            + "\n".join(f"- {s}" for s in ctx["competitor_review_summaries"])
            + "\n\n"
            if ctx["competitor_review_summaries"] else ""
        )
        + f"{pos_block}\n"
        "Rules:\n"
        "- Mine the real customer reviews for exact language, emotions, and recurring themes — "
        "reflect these directly in pain_points_and_frustrations and buying_triggers_and_barriers\n"
        "- pain_points_and_frustrations must reference real frustrations specific to this business type\n"
        "- buying_triggers_and_barriers must be concrete and actionable (not vague)\n"
        "- key_messages_that_convert must be a usable marketing line written in customer language, not a description\n"
        "- preferred_channels must be a JSON array of strings\n"
        "- resonant_content_topics must be a JSON array of strings\n"
        "- photo_prompt should describe a realistic stock photo for this persona type\n"
    )

    try:
        client = OpenAI(
            api_key=settings.openai_api_key,
            base_url=settings.openai_base_url,
            timeout=25,
            max_retries=1,
        )
        resp = tracked_responses(client, agent="persona_builder",
            model=settings.openai_model, input=prompt)
        raw = resp.output_text.strip()
        if raw.startswith("```"):
            raw = raw.split("```")[1]
            if raw.startswith("json"):
                raw = raw[4:]
        parsed = json.loads(raw.strip())
        personas = parsed.get("personas", [])
        if not isinstance(personas, list) or len(personas) < 2:
            return _fallback_personas(ctx["business_type"], ctx["location"])[:num_personas]
        cleaned = [p for p in personas[:num_personas] if isinstance(p, dict) and "name" in p]
        if len(cleaned) < 2:
            return _fallback_personas(ctx["business_type"], ctx["location"])[:num_personas]
        score_personas(cleaned)
        return cleaned
    except Exception:
        return _fallback_personas(ctx["business_type"], ctx["location"])[:num_personas]
