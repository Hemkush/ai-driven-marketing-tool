import json

from openai import OpenAI

from app.core.config import settings


def _fallback_roadmap(
    project_name: str,
    strategy: dict,
    personas: list[dict],
) -> dict:
    persona_names = [p.get("name", "Persona") for p in personas][:3]
    prioritized_channels = strategy.get("prioritized_channels", [])
    top_channels = [c.get("channel", "") for c in prioritized_channels][:3]

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
                f"Run weekly campaigns on {', '.join(top_channels) or 'priority channels'}",
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
        "priority_channels": top_channels,
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
    }


def generate_roadmap_plan(
    project_name: str,
    strategy: dict,
    personas: list[dict],
) -> dict:
    if not settings.can_use_openai():
        return _fallback_roadmap(project_name, strategy, personas)

    prompt = (
        "You are RoadmapPlannerAgent.\n"
        "Generate a practical 90-day implementation roadmap.\n"
        "Return strict JSON with keys:\n"
        "project_name, duration_days, target_personas, priority_channels, "
        "weekly_plan, milestones, success_metrics.\n"
        "weekly_plan must include 12 week entries and each entry must include:\n"
        "week, phase, objective, tasks, owner, kpi.\n"
        "Milestones should include at least day 30/60/90 goals.\n\n"
        f"Project: {project_name}\n"
        f"Strategy: {json.dumps(strategy, ensure_ascii=True)}\n"
        f"Personas: {json.dumps(personas, ensure_ascii=True)}"
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
        required = {
            "project_name",
            "duration_days",
            "target_personas",
            "priority_channels",
            "weekly_plan",
            "milestones",
            "success_metrics",
        }
        if not required.issubset(parsed.keys()):
            return _fallback_roadmap(project_name, strategy, personas)
        return parsed
    except Exception:
        return _fallback_roadmap(project_name, strategy, personas)
