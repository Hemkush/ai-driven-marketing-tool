import json
import logging

from openai import OpenAI

from app.core.config import settings
from app.core.llm_tracker import tracked_responses

logger = logging.getLogger(__name__)


def _format_personas(personas: list[dict]) -> str:
    lines = []
    for p in personas:
        name = p.get("name", "Unnamed")
        psych = p.get("psychographic_profile", {})
        behav = p.get("behavioral_profile", {})
        eng = p.get("engagement_strategy", {})
        lines.append(
            f"Persona: {name}\n"
            f"  Goals: {psych.get('goals_and_motivations', '')}\n"
            f"  Pain points: {psych.get('pain_points_and_frustrations', '')}\n"
            f"  Decision process: {behav.get('decision_making_process', '')}\n"
            f"  Information sources: {behav.get('information_sources', '')}\n"
            f"  Preferred channels: {', '.join(eng.get('preferred_channels') or [])}\n"
            f"  Key message that converts: {eng.get('key_messages_that_convert', '')}"
        )
    return "\n\n".join(lines)


def _extract_review_snippets(analysis_report: dict) -> list[str]:
    snippets = []
    for c in (analysis_report.get("competitors") or [])[:8]:
        for s in (c.get("review_snippets") or [])[:3]:
            if s and len(s.strip()) > 20:
                snippets.append(s.strip()[:250])
    return snippets


def _fallback_research(
    project_name: str,
    questionnaire_responses: list[dict],
    analysis_report: dict,
    business_address: str | None = None,
    personas: list[dict] | None = None,
) -> dict:
    context_excerpt = " ".join(
        (r.get("answer_text") or "") for r in questionnaire_responses
    )[:1200]
    primary_segment = (
        analysis_report.get("segment_attractiveness_analysis", {}).get(
            "recommended_primary_segment", "Primary local customers"
        )
    )
    business_type = analysis_report.get("business_keyword", "local business")

    per_persona_insights = []
    for p in (personas or []):
        per_persona_insights.append({
            "persona_name": p.get("name", "Unnamed"),
            "buying_journey": {
                "awareness": "Discovers via word-of-mouth, Google Search, and local social groups.",
                "consideration": "Compares reviews, prices, and checks the business's online presence.",
                "decision": "Books when they see strong reviews and clear pricing.",
            },
            "key_message": "Reliable, local, and trusted — exactly what you need.",
            "best_channel": "Google Search and local community Facebook groups.",
        })

    persona_names = [p.get("name", "your customer") for p in (personas or [])]
    interview_questions = [
        {
            "question": f"What made you first look for a {business_type} in this area?",
            "why_ask": "Uncovers the triggering event — the moment the need became urgent.",
            "insight_unlocked": "Reveals what life circumstances drive new customer acquisition.",
        },
        {
            "question": "How did you find us specifically? What did you search or who did you ask?",
            "why_ask": "Identifies your most effective discovery channels from real customer experience.",
            "insight_unlocked": "Tells you where to invest marketing budget based on actual behaviour.",
        },
        {
            "question": "Before booking with us, what other options did you consider?",
            "why_ask": "Reveals your true competitive set — often different from what owners assume.",
            "insight_unlocked": "Helps you understand who you're actually competing against for this customer.",
        },
        {
            "question": "What nearly stopped you from booking with us?",
            "why_ask": "Surfaces hidden objections that cause drop-off before purchase.",
            "insight_unlocked": "Identifies friction points in your conversion funnel to fix immediately.",
        },
        {
            "question": "In your own words, what do we do better than anywhere else you've tried?",
            "why_ask": "Captures your real differentiators in customer language — not your assumptions.",
            "insight_unlocked": "Provides word-for-word copy for testimonials, ads, and your website.",
        },
        {
            "question": "If you were recommending us to a friend, what would you say?",
            "why_ask": "The referral pitch is your most honest positioning statement.",
            "insight_unlocked": "Gives you the exact messaging that drives word-of-mouth growth.",
        },
        {
            "question": "What's the one thing we could improve that would make you never consider going elsewhere?",
            "why_ask": "Reveals your most important retention lever straight from active customers.",
            "insight_unlocked": "Prioritises product/service improvements by impact on loyalty.",
        },
        {
            "question": "How often do you typically use a service like ours, and what drives that frequency?",
            "why_ask": "Helps you understand natural purchase cycles and LTV potential.",
            "insight_unlocked": "Informs loyalty programme design and re-engagement timing.",
        },
    ]

    return {
        "project_name": project_name,
        "target_customer_insights": [
            {"theme": "Primary motivations", "insight": "Customers value reliability, convenience, and outcome quality."},
            {"theme": "Decision barriers", "insight": "Price sensitivity and trust in provider consistency can delay purchase."},
            {"theme": "Information behavior", "insight": "Customers compare options through social proof, online presence, and referrals."},
        ],
        "competitor_insights": [
            {"theme": "Competitive intensity", "insight": "Competition appears moderate to high in common service categories."},
            {"theme": "Market gaps", "insight": "Potential gap in premium personalisation and fast-response support."},
            {"theme": "Differentiation opportunity", "insight": f"Position around segment-specific value for {primary_segment}."},
        ],
        "per_persona_insights": per_persona_insights,
        "quick_wins": [
            {
                "action": "Respond to every Google review within 24 hours.",
                "impact": "Boosts local SEO rank and signals trustworthiness to prospective customers comparing options.",
                "effort": "low",
                "timeframe": "This week",
            },
            {
                "action": "Complete your Google Business Profile with hours, photos, and services.",
                "impact": "Incomplete profiles lose customers to competitors — highest-ROI free action available.",
                "effort": "low",
                "timeframe": "This week",
            },
            {
                "action": "Ask your top 5 loyal customers for a Google review.",
                "impact": "Each new review increases visibility and conversion rate for price-sensitive searchers.",
                "effort": "low",
                "timeframe": "This month",
            },
        ],
        "voc_synthesis": {
            "praised_themes": [
                {"theme": "Quality and reliability", "quotes": ["Great results every time", "Always consistent"]},
                {"theme": "Friendly service", "quotes": ["Staff made me feel welcome", "Very professional and warm"]},
            ],
            "complained_themes": [
                {"theme": "Wait times", "quotes": ["Had to wait longer than expected", "Booking was slow"]},
                {"theme": "Pricing clarity", "quotes": ["Wasn't sure about the cost upfront", "Prices not listed online"]},
            ],
            "language_patterns": [
                "reliable", "consistent", "friendly", "professional", "worth it", "would recommend",
            ],
            "sentiment_summary": (
                f"Customer sentiment across local {business_type} businesses is generally positive, "
                "with the strongest praise around service quality and staff attitude. "
                "The most common complaints relate to wait times and unclear pricing — "
                "both are addressable operational improvements."
            ),
        },
        "interview_script": {
            "intro_note": (
                f"Use these questions in a 20-minute conversation with {', '.join(persona_names) or 'your customers'}. "
                "Record or take notes. Ask follow-ups by saying 'Can you tell me more about that?' "
                "Aim for 5–8 interviews per persona type for reliable patterns."
            ),
            "questions": interview_questions,
        },
        "jtbd_framework": [
            {
                "persona_name": p.get("name", "Unnamed"),
                "functional_job": f"Get reliable {business_type} done without wasting time or money.",
                "emotional_job": "Feel confident they made the right choice and are being looked after.",
                "social_job": "Be seen by others as someone who makes smart, quality-conscious decisions.",
                "hire_triggers": [
                    "Consistently strong reviews with recent dates",
                    "Easy and transparent booking process",
                    "Clear pricing with no hidden costs",
                ],
                "fire_triggers": [
                    "Single poor experience with no follow-up or apology",
                    "Finding a cheaper option with comparable reviews",
                    "Feeling unrecognised or treated as just another customer",
                ],
            }
            for p in (personas or [])
        ],
        "retention_signals": {
            "repeat_drivers": [
                "Personal recognition — staff remembering the customer's name or preferences",
                "Consistently high quality that removes the risk of trying someone new",
                "Convenient rebooking — reminders, easy scheduling, loyalty incentives",
            ],
            "churn_reasons": [
                "A single unresolved bad experience — no follow-up or acknowledgement",
                f"A competitor offering the same {business_type} service at a meaningfully lower price",
                "Life change — moved, changed routine, or found a closer alternative",
                "Feeling like just a number — no personal connection or recognition",
            ],
            "retention_actions": [
                {
                    "action": "Send a personalised follow-up message 48 hours after each visit.",
                    "impact": "Catches dissatisfied customers before they leave a bad review and reinforces loyalty for happy ones.",
                    "effort": "low",
                },
                {
                    "action": f"Introduce a simple loyalty card — every 5th {business_type} visit is discounted.",
                    "impact": "Increases average visit frequency and gives customers a concrete reason to return over a competitor.",
                    "effort": "low",
                },
                {
                    "action": "Proactively reach out to customers who haven't returned in 60+ days.",
                    "impact": "Recovers lapsed customers before they become permanently lost — win-back cost is far lower than acquiring new.",
                    "effort": "medium",
                },
            ],
            "ltv_insight": (
                f"For {business_type} businesses, the difference between a one-time and repeat customer "
                "is almost always the post-visit experience, not the visit itself. "
                "Customers who feel recognised and followed up with are 3–5× more likely to return and refer others."
            ),
        },
        "business_address": business_address or "",
        "context_excerpt": context_excerpt,
        "sources": [
            {"title": "Internal Questionnaire Responses", "url": "internal://questionnaire", "note": "User-provided business and customer input."},
            {"title": "Segment Attractiveness Analysis", "url": "internal://analysis", "note": "Generated by SegmentAnalystAgent."},
        ],
        "reasoning": (
            f"Research generated from your questionnaire answers and market analysis for {project_name}. "
            f"Insights reflect the recommended primary segment ({primary_segment}) identified in your analysis."
        ),
        "_is_fallback": True,
    }


def generate_research_report(
    project_name: str,
    questionnaire_responses: list[dict],
    analysis_report: dict,
    business_address: str | None = None,
    personas: list[dict] | None = None,
    focus_area: str | None = None,
) -> dict:
    if not settings.can_use_openai():
        return _fallback_research(
            project_name,
            questionnaire_responses,
            analysis_report,
            business_address=business_address,
            personas=personas,
        )

    review_snippets = _extract_review_snippets(analysis_report)

    personas_block = ""
    if personas:
        personas_block = (
            f"\nBuyer personas already generated for this business ({len(personas)} personas):\n"
            + _format_personas(personas)
            + "\n\nFor per_persona_insights and jtbd_framework, produce one entry per persona above — "
            "persona_name must match exactly.\n"
            "For interview_script, tailor the questions to these specific personas and business type.\n"
        )

    focus_block = ""
    if focus_area:
        focus_block = (
            f"\nFocus area requested by the owner: {focus_area}\n"
            "Ensure quick_wins and research_summary especially address this focus area.\n"
        )

    snippets_block = ""
    if review_snippets:
        snippets_block = (
            f"\nReal customer reviews collected from Google across local competitors "
            f"({len(review_snippets)} snippets — use these as raw material for voc_synthesis):\n"
            + "\n".join(f'- "{s}"' for s in review_snippets)
            + "\n"
        )

    prompt = (
        "You are MarketResearchAgent for an AI-driven marketing tool.\n"
        "Produce deep, specific research for this business. Every insight must be concrete and "
        "directly actionable — avoid generic advice that could apply to any business.\n\n"
        "Return strict JSON with these exact top-level keys:\n"
        "  project_name, research_summary, target_customer_insights, competitor_insights,\n"
        "  per_persona_insights, quick_wins, voc_synthesis, interview_script,\n"
        "  jtbd_framework, retention_signals, sources, reasoning\n\n"
        "Schema for each field:\n"
        "- target_customer_insights: array of 3-5 {theme, insight}\n"
        "- competitor_insights: array of 3-5 {theme, insight}\n"
        "- per_persona_insights: array — one per persona:\n"
        "    {persona_name, buying_journey: {awareness, consideration, decision}, key_message, best_channel}\n"
        "- quick_wins: array of 3-5:\n"
        "    {action, impact, effort (low|medium|high), timeframe (This week|This month|Within 3 months)}\n"
        "- voc_synthesis: object with:\n"
        "    praised_themes: array of 2-4 {theme, quotes: [exact customer phrases, max 3 per theme]}\n"
        "    complained_themes: array of 2-4 {theme, quotes: [exact customer phrases, max 3 per theme]}\n"
        "    language_patterns: array of 6-12 strings — words/short phrases customers repeat "
        "that the owner should use in marketing copy\n"
        "    sentiment_summary: 2-3 sentence summary of overall customer sentiment pattern\n"
        "  Rules for voc_synthesis: quotes must be real or near-verbatim phrases from the provided "
        "review snippets — do not invent quotes. If snippets are limited, synthesise themes "
        "from review_summary fields instead and note this in sentiment_summary.\n"
        "- interview_script: object with:\n"
        "    intro_note: 2-3 sentence instruction for the owner on how to run the interviews\n"
        "    questions: array of 8-10 objects, each: "
        "{question (string), why_ask (1 sentence), insight_unlocked (1 sentence)}\n"
        "  Rules for interview_script: questions must be specific to this business type and these "
        "personas — not generic market research questions. Cover: discovery channel, "
        "decision triggers, objections, satisfaction drivers, referral language, retention.\n"
        "- jtbd_framework: array — one entry per persona:\n"
        "    {persona_name (must match exactly),\n"
        "     functional_job (the practical task they need done — 1 sentence),\n"
        "     emotional_job (how they want to feel after — 1 sentence),\n"
        "     social_job (how they want to be perceived by others — 1 sentence),\n"
        "     hire_triggers (array of 3-4 strings — specific reasons they choose a provider),\n"
        "     fire_triggers (array of 3-4 strings — specific reasons they switch away)}\n"
        "  Rules for jtbd_framework: be specific to this business type and persona — "
        "not generic. hire/fire triggers must be concrete behaviours, not vague concepts.\n"
        "- retention_signals: object with:\n"
        "    repeat_drivers: array of 3-5 strings — what makes customers return to this business type\n"
        "    churn_reasons: array of 3-5 strings — why customers stop coming back\n"
        "    retention_actions: array of 3-5 {action, impact, effort (low|medium|high)} — "
        "specific things the owner can do to improve retention\n"
        "    ltv_insight: 2-3 sentence insight about customer lifetime value dynamics "
        "for this business type and market\n"
        "  Rules for retention_signals: base repeat_drivers and churn_reasons on the competitor "
        "review data and business type — not generic retail patterns.\n"
        "- sources: array of 2-4 {title, url, note}\n"
        "- reasoning: 2-3 sentences on which data drove key conclusions\n\n"
        f"Project name: {project_name}\n"
        f"Business address: {business_address or 'not provided'}\n"
        f"{focus_block}"
        f"{snippets_block}"
        f"{personas_block}\n"
        f"Questionnaire responses:\n{json.dumps(questionnaire_responses, ensure_ascii=True)}\n\n"
        f"Analysis report:\n{json.dumps(analysis_report, ensure_ascii=True)}"
    )

    try:
        client = OpenAI(
            api_key=settings.openai_api_key,
            base_url=settings.openai_base_url,
            timeout=120,
            max_retries=0,
        )
        resp = tracked_responses(
            client,
            agent="market_researcher",
            model=settings.openai_model,
            input=prompt,
        )
        raw = resp.output_text.strip()
        if raw.startswith("```"):
            raw = raw.split("```")[1]
            if raw.startswith("json"):
                raw = raw[4:]
        parsed = json.loads(raw.strip())
        required = {"project_name", "target_customer_insights", "competitor_insights", "research_summary"}
        if not required.issubset(parsed.keys()):
            logger.warning(
                "market_researcher_schema_incomplete",
                extra={"missing_keys": list(required - parsed.keys())},
            )
            return _fallback_research(
                project_name, questionnaire_responses, analysis_report,
                business_address=business_address, personas=personas,
            )
        return parsed
    except Exception:
        logger.exception("market_researcher_llm_error")
        return _fallback_research(
            project_name, questionnaire_responses, analysis_report,
            business_address=business_address, personas=personas,
        )
