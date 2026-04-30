import json
import logging

from openai import OpenAI

from app.core.config import settings
from app.core.llm_tracker import tracked_responses
from app.core.quality_scorer import score_roadmap

logger = logging.getLogger(__name__)


def _compact_analysis(analysis_report: dict) -> dict:
    """Extract only the fields needed for service recommendations."""
    competitors = analysis_report.get("competitors") or []
    services = []
    for c in competitors[:6]:
        services.extend(c.get("services_offered") or [])
    return {
        "business_keyword": analysis_report.get("business_keyword", ""),
        "market_overview": str(analysis_report.get("market_overview", ""))[:400],
        "competitor_services": list(set(services))[:20],
        "swot_opportunities": (analysis_report.get("swot_analysis") or {}).get("opportunities", [])[:4],
    }


def _fallback_roadmap(
    project_name: str,
    personas: list[dict],
    analysis_report: dict | None = None,
) -> dict:
    persona_names = [p.get("name", "Persona") for p in personas][:3]
    business_type = (analysis_report or {}).get("business_keyword", "local business")

    weeks = []
    for i in range(1, 13):
        phase = "Foundation" if i <= 4 else "Execution" if i <= 9 else "Optimization"
        week_item = {
            "week": i,
            "phase": phase,
            "objective": f"Week {i} objective for {project_name}",
            "tasks": [],
            "owner": "Business Owner",
            "kpi": "Qualified leads",
        }
        if i <= 4:
            week_item["tasks"] = [
                "Finalize core messaging and positioning",
                "Set up channel baselines and tracking",
                "Prepare initial content calendar",
            ]
            week_item["kpi"] = "Baseline traffic and lead volume"
        elif i <= 9:
            week_item["tasks"] = [
                "Run weekly campaigns on priority channels",
                "Publish persona-targeted content",
                "Review performance and iterate offers",
            ]
            week_item["kpi"] = "Lead-to-consult conversion"
        else:
            week_item["tasks"] = [
                "Scale top-performing channels",
                "Pause low-performing tactics",
                "Design next-quarter test plan",
            ]
            week_item["kpi"] = "Cost per qualified lead"
        weeks.append(week_item)

    return {
        "project_name": project_name,
        "duration_days": 90,
        "target_personas": persona_names,
        "priority_channels": ["Google Business Profile", "Instagram", "Email"],
        "weekly_plan": weeks,
        "milestones": [
            {"day": 30, "goal": "Foundation complete and first optimization cycle started"},
            {"day": 60, "goal": "Consistent lead flow from prioritized channels"},
            {"day": 90, "goal": "Documented playbook and scale plan for next quarter"},
        ],
        "success_metrics": [
            "Qualified leads per week",
            "Cost per qualified lead",
            "Conversion rate to booking/sale",
            "Retention or repeat purchase trend",
        ],
        "communication_plan": [
            {
                "channel": "Email",
                "frequency": "2x per week (Tuesday + Thursday)",
                "phase_1_theme": "Introduce your story, team, and core service promise to build trust",
                "phase_2_theme": "Share customer results and run limited-time offers tied to booking triggers",
                "phase_3_theme": "Launch a referral campaign with a clear incentive for each new booking referred",
                "example_message": f"Subject: Why {project_name} customers keep coming back",
            },
            {
                "channel": "Instagram",
                "frequency": "5x per week (Mon–Fri)",
                "phase_1_theme": "Behind-the-scenes and team introductions to humanise the brand",
                "phase_2_theme": "Before/after results and customer testimonials to drive social proof",
                "phase_3_theme": "Seasonal promotions and limited availability posts to create urgency",
                "example_message": "Caption: Most people don't realise how much difference [service] makes until they try it — swipe to see →",
            },
            {
                "channel": "Google Business Profile",
                "frequency": "Daily review responses + 2 posts per week",
                "phase_1_theme": "Respond to all existing reviews and complete your profile with photos and services",
                "phase_2_theme": "Post weekly offers and service highlights to boost local search ranking",
                "phase_3_theme": "Run a review collection campaign — ask every satisfied customer directly",
                "example_message": "Post: This week only — book before [date] and get [offer]. Limited slots available.",
            },
        ],
        "product_checklist": [
            {"item": "Google Business Profile fully completed with photos, hours, and all services listed", "category": "Online Presence", "priority": "must-have", "why_it_matters": "Incomplete profiles lose customers to competitors — it's the highest-ROI free action available"},
            {"item": "Clear pricing displayed on website or profile (ranges are fine)", "category": "Online Presence", "priority": "must-have", "why_it_matters": "Price uncertainty is the #1 reason potential customers don't enquire — clarity converts browsers into bookings"},
            {"item": "Booking or enquiry system in place (even a simple contact form)", "category": "Operations", "priority": "must-have", "why_it_matters": "If customers can't easily book or enquire, all your marketing spend drives traffic that never converts"},
            {"item": "At least 10 Google reviews (5-star average or above)", "category": "Online Presence", "priority": "must-have", "why_it_matters": "Businesses with fewer than 10 reviews are ignored by 70% of local searchers comparing options"},
            {"item": "Professional photos of your service, team, and premises", "category": "Content", "priority": "must-have", "why_it_matters": "Listings with photos get 42% more requests for directions and 35% more website clicks than those without"},
            {"item": "Email list with at least existing customers loaded in", "category": "Tools", "priority": "must-have", "why_it_matters": "Email marketing to existing customers costs nothing and converts at 3–5x the rate of cold advertising"},
            {"item": "Social media accounts claimed and branded consistently", "category": "Online Presence", "priority": "must-have", "why_it_matters": "Inconsistent or empty profiles undermine trust when prospects research you before booking"},
            {"item": f"Service menu written in customer language (benefits, not just {business_type} jargon)", "category": "Content", "priority": "must-have", "why_it_matters": "Customers buy outcomes, not processes — describing what they get (not what you do) lifts conversion"},
            {"item": "Customer follow-up process in place (even a simple text or email)", "category": "Operations", "priority": "nice-to-have", "why_it_matters": "A 48-hour post-visit follow-up increases repeat booking rate by up to 30% in service businesses"},
            {"item": "Loyalty or referral incentive defined (discount, free add-on, etc.)", "category": "Tools", "priority": "nice-to-have", "why_it_matters": "Word-of-mouth is your cheapest acquisition channel — a clear referral offer makes it systematic"},
        ],
        "service_recommendations": [
            {
                "service": "Gift vouchers / prepaid packages",
                "rationale": "A common offering among successful local service businesses that captures impulse purchases and brings in new customers as gifts",
                "revenue_impact": "Typically adds 12–18% to monthly revenue by converting gifters into net-new customers",
                "effort": "low",
                "competitors_offering": True,
            },
            {
                "service": "Introductory bundle or first-visit offer",
                "rationale": "Reduces the perceived risk for first-time customers who are comparing options — lowers the barrier to try",
                "revenue_impact": "Increases new customer conversion rate by 20–35% and seeds loyalty if the experience is strong",
                "effort": "low",
                "competitors_offering": False,
            },
            {
                "service": "Subscription / membership plan",
                "rationale": "Converts one-off customers into recurring revenue, smooths cash flow, and dramatically increases lifetime value",
                "revenue_impact": "Members visit 2.4x more frequently than non-members and are 5x less likely to switch to a competitor",
                "effort": "medium",
                "competitors_offering": False,
            },
        ],
        "reasoning": (
            f"Roadmap structured around {len(persona_names)} persona(s) ({', '.join(persona_names) or 'your target customers'}). "
            "Timeline follows a Foundation → Execution → Optimization arc. "
            "Communication plan, checklist, and service recommendations are based on standard patterns for this business type."
        ),
        "_is_fallback": True,
    }


def generate_roadmap_plan(
    project_name: str,
    personas: list[dict],
    analysis_report: dict | None = None,
) -> dict:
    if not settings.can_use_openai():
        return _fallback_roadmap(project_name, personas, analysis_report)

    compact_analysis = _compact_analysis(analysis_report) if analysis_report else {}

    prompt = (
        "You are RoadmapPlannerAgent.\n"
        "Generate a practical 90-day marketing implementation roadmap tailored to this specific business.\n"
        "Every item must be concrete and directly actionable — no generic advice.\n\n"
        "Return strict JSON with these exact top-level keys:\n"
        "project_name, duration_days, target_personas, priority_channels,\n"
        "weekly_plan, milestones, success_metrics,\n"
        "communication_plan, product_checklist, service_recommendations, reasoning\n\n"
        "Schema:\n"
        "- weekly_plan: 12 entries, each: {week, phase (Foundation|Execution|Optimization),\n"
        "    objective (1 sentence), tasks (array of 3 strings), owner, kpi}\n"
        "- milestones: at least day 30/60/90 — {day, goal (specific measurable target)}\n"
        "- success_metrics: 4-6 specific KPIs for this business type\n\n"
        "- communication_plan: array of 3-5 objects — one per priority channel:\n"
        "    {channel, frequency (e.g. '2x per week, Tue+Thu'),\n"
        "     phase_1_theme (weeks 1-4, 1 sentence),\n"
        "     phase_2_theme (weeks 5-9, 1 sentence),\n"
        "     phase_3_theme (weeks 10-12, 1 sentence),\n"
        "     example_message (one concrete subject line or opening line specific to this business)}\n"
        "  Rules: channels must match the priority_channels list. Messages must use the business name or type.\n\n"
        "- product_checklist: 8-12 items — operational prerequisites before marketing can work:\n"
        "    {item (specific action), category (Online Presence|Operations|Content|Tools),\n"
        "     priority (must-have|nice-to-have), why_it_matters (1 sentence — cite specific impact)}\n"
        "  Rules: items must be specific to this business type, not generic. Ordered must-have first.\n\n"
        "- service_recommendations: 2-4 services this business should consider offering:\n"
        "    {service (name), rationale (cite specific competitor data or market gap),\n"
        "     revenue_impact (specific % or $ estimate with reasoning),\n"
        "     effort (low|medium|high), competitors_offering (true|false)}\n"
        "  Rules: base on competitor_services and swot_opportunities from analysis. Be specific.\n\n"
        "- reasoning: 2-3 sentences citing which persona/channel/competitor inputs shaped priorities\n\n"
        f"Project: {project_name}\n"
        f"Personas:\n{json.dumps(personas, ensure_ascii=True)}\n\n"
        f"Competitor analysis summary:\n{json.dumps(compact_analysis, ensure_ascii=True)}"
    )

    try:
        client = OpenAI(
            api_key=settings.openai_api_key,
            base_url=settings.openai_base_url,
            timeout=90,
            max_retries=0,
        )
        resp = tracked_responses(
            client,
            agent="roadmap_planner",
            model=settings.openai_model,
            input=prompt,
        )
        raw = resp.output_text.strip()
        if raw.startswith("```"):
            raw = raw.split("```")[1]
            if raw.startswith("json"):
                raw = raw[4:]
        parsed = json.loads(raw.strip())
        required = {
            "project_name", "duration_days", "target_personas", "priority_channels",
            "weekly_plan", "milestones", "success_metrics",
            "communication_plan", "product_checklist", "service_recommendations",
        }
        if not required.issubset(parsed.keys()):
            logger.warning(
                "roadmap_planner_schema_incomplete",
                extra={"missing_keys": list(required - parsed.keys())},
            )
            return _fallback_roadmap(project_name, personas, analysis_report)
        score_roadmap(parsed)
        return parsed
    except Exception:
        logger.exception("roadmap_planner_llm_error")
        return _fallback_roadmap(project_name, personas, analysis_report)
