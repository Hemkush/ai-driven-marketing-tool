import json

from openai import OpenAI

from app.core.config import settings


def _fallback_personas(project_name: str, research_report: dict) -> list[dict]:
    summary = research_report.get("research_summary", "")
    return [
        {
            "name": "Practical Planner Priya",
            "basic_profile": {
                "age": "32",
                "occupation": "Operations Manager",
                "income": "Mid-income",
                "location": "Urban/Suburban",
                "family_status": "Married",
                "photo_prompt": "Professional woman planning an event, warm natural style",
            },
            "psychographic_profile": {
                "goals_and_motivations": "Deliver reliable outcomes with minimal risk.",
                "pain_points_and_frustrations": "Last-minute uncertainty and inconsistent service quality.",
                "values_and_priorities": "Reliability, clarity, and responsive support.",
                "lifestyle_and_interests": "Time-constrained, detail-oriented, value-conscious.",
            },
            "behavioral_profile": {
                "shopping_preferences": "Compares shortlists, prefers transparent packages.",
                "decision_making_process": "Researches first, then validates with reviews/referrals.",
                "information_sources": "Google search, Instagram, peer recommendations.",
                "buying_triggers_and_barriers": "Triggers: proof of reliability. Barrier: unclear pricing.",
            },
            "engagement_strategy": {
                "preferred_channels": ["Email", "Instagram", "Google Search"],
                "resonant_content_topics": ["Case studies", "Before/after examples", "Process clarity"],
                "best_times_to_reach": "Weekday mornings",
                "key_messages_that_convert": "Predictable delivery with high-quality execution.",
            },
            "fit_note": f"Derived from fallback research context for {project_name}. {summary[:120]}",
        },
        {
            "name": "Premium Experience Elena",
            "basic_profile": {
                "age": "29",
                "occupation": "Marketing Specialist",
                "income": "Upper-mid income",
                "location": "City center",
                "family_status": "Engaged",
                "photo_prompt": "Stylish young professional reviewing premium event options",
            },
            "psychographic_profile": {
                "goals_and_motivations": "Create memorable, high-quality experiences.",
                "pain_points_and_frustrations": "Generic offerings and weak personalization.",
                "values_and_priorities": "Aesthetics, premium quality, trust.",
                "lifestyle_and_interests": "Socially active, design-conscious, digital-first.",
            },
            "behavioral_profile": {
                "shopping_preferences": "Prefers curated options and portfolio proof.",
                "decision_making_process": "Emotion-led shortlist, then practical validation.",
                "information_sources": "Instagram, Pinterest, influencer content, referrals.",
                "buying_triggers_and_barriers": "Trigger: premium social proof. Barrier: poor communication.",
            },
            "engagement_strategy": {
                "preferred_channels": ["Instagram", "Pinterest", "WhatsApp/DM"],
                "resonant_content_topics": ["Visual storytelling", "Premium packages", "Testimonials"],
                "best_times_to_reach": "Evenings and weekends",
                "key_messages_that_convert": "Premium personalized outcomes with effortless coordination.",
            },
            "fit_note": f"Persona reflects premium-oriented segment signals in {project_name}.",
        },
    ]


def generate_personas(
    project_name: str,
    analysis_report: dict,
    research_report: dict,
    num_personas: int = 3,
) -> list[dict]:
    num_personas = max(2, min(3, num_personas))

    if not settings.can_use_openai():
        return _fallback_personas(project_name, research_report)[:num_personas]

    prompt = (
        "You are PersonaBuilderAgent for an AI marketing application.\n"
        f"Generate exactly {num_personas} primary buyer personas.\n"
        "Return strict JSON as: {\"personas\": [...]}.\n"
        "Each persona object must contain keys:\n"
        "name, basic_profile, psychographic_profile, behavioral_profile, engagement_strategy.\n"
        "basic_profile keys: age, occupation, income, location, family_status, photo_prompt.\n"
        "psychographic_profile keys: goals_and_motivations, pain_points_and_frustrations, "
        "values_and_priorities, lifestyle_and_interests.\n"
        "behavioral_profile keys: shopping_preferences, decision_making_process, information_sources, "
        "buying_triggers_and_barriers.\n"
        "engagement_strategy keys: preferred_channels, resonant_content_topics, "
        "best_times_to_reach, key_messages_that_convert.\n\n"
        f"Project: {project_name}\n"
        f"Analysis: {json.dumps(analysis_report, ensure_ascii=True)}\n"
        f"Research: {json.dumps(research_report, ensure_ascii=True)}"
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
        personas = parsed.get("personas", [])
        if not isinstance(personas, list) or len(personas) < 2:
            return _fallback_personas(project_name, research_report)[:num_personas]
        cleaned = []
        for p in personas[:num_personas]:
            if not isinstance(p, dict):
                continue
            if "name" not in p:
                continue
            cleaned.append(p)
        if len(cleaned) < 2:
            return _fallback_personas(project_name, research_report)[:num_personas]
        return cleaned
    except Exception:
        return _fallback_personas(project_name, research_report)[:num_personas]
