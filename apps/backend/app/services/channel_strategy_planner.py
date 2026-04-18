import json

from openai import OpenAI

from app.core.config import settings
from app.core.llm_tracker import tracked_responses
from app.core.quality_scorer import score_channel_strategy


def _fallback_strategy(
    project_name: str,
    personas: list[dict],
    research_report: dict,
) -> dict:
    persona_names = [p.get("name", "Persona") for p in personas][:3]
    return {
        "project_name": project_name,
        "prioritized_channels": [
            {
                "priority": 1,
                "channel": "Instagram",
                "why": "Strong visual storytelling and high intent discovery for local services.",
                "primary_personas": persona_names,
                "weekly_actions": [
                    "Post 3 visual case studies",
                    "Share 2 testimonial stories",
                    "Publish 1 offer-driven reel",
                ],
            },
            {
                "priority": 2,
                "channel": "Google Search / Local SEO",
                "why": "Captures active intent from customers comparing providers.",
                "primary_personas": persona_names,
                "weekly_actions": [
                    "Update local business profile",
                    "Collect 3 reviews",
                    "Publish 1 service-focused page update",
                ],
            },
            {
                "priority": 3,
                "channel": "Email",
                "why": "Converts warm leads and drives repeat/upsell opportunities.",
                "primary_personas": persona_names,
                "weekly_actions": [
                    "Send weekly campaign email",
                    "Segment by event timeline",
                    "Run one reactivation sequence",
                ],
            },
        ],
        "key_messages": [
            "Reliable execution with premium quality",
            "Clear process and responsive support",
            "Personalized outcomes for important occasions",
        ],
        "budget_guidance": {
            "content_and_creative_percent": 40,
            "paid_distribution_percent": 35,
            "retention_and_email_percent": 25,
        },
        "kpis": [
            "Qualified leads per week",
            "Cost per lead",
            "Conversion rate to consultation/order",
            "Repeat customer rate",
        ],
        "notes": research_report.get("research_summary", "")[:400],
    }


def generate_channel_strategy(
    project_name: str,
    personas: list[dict],
    research_report: dict,
) -> dict:
    if not settings.can_use_openai():
        return _fallback_strategy(project_name, personas, research_report)

    prompt = (
        "You are ChannelStrategyAgent for an AI marketing planner.\n"
        "Generate a prioritized channel strategy based on personas and research context.\n"
        "Return strict JSON with keys:\n"
        "project_name, prioritized_channels, key_messages, budget_guidance, kpis, notes.\n"
        "For prioritized_channels include 3-5 channels with keys:\n"
        "priority, channel, why, primary_personas, weekly_actions.\n"
        "budget_guidance should include percentage split that totals about 100.\n\n"
        f"Project: {project_name}\n"
        f"Personas: {json.dumps(personas, ensure_ascii=True)}\n"
        f"Research: {json.dumps(research_report, ensure_ascii=True)}"
    )

    try:
        client = OpenAI(
            api_key=settings.openai_api_key,
            base_url=settings.openai_base_url,
            timeout=15,
            max_retries=0,
        )
        resp = tracked_responses(client, agent="channel_strategy_planner",
            model=settings.openai_model,
            input=prompt,
        )
        parsed = json.loads(resp.output_text.strip())
        required = {
            "project_name",
            "prioritized_channels",
            "key_messages",
            "budget_guidance",
            "kpis",
            "notes",
        }
        if not required.issubset(parsed.keys()):
            return _fallback_strategy(project_name, personas, research_report)
        score_channel_strategy(parsed)
        return parsed
    except Exception:
        return _fallback_strategy(project_name, personas, research_report)
