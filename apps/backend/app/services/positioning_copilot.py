import json

from openai import OpenAI

from app.core.config import settings


def _fallback_positioning(analysis_report: dict, owner_feedback: str = "") -> dict:
    analysis = analysis_report.get("segment_attractiveness_analysis", {})
    segment = analysis.get("recommended_primary_segment", "Primary local customers")
    notes = owner_feedback.strip()[:400]
    statement = (
        f"For {segment} who need reliable results, our business provides a focused, "
        "high-trust offering with personalized service and practical value."
    )
    rationale = (
        "Drafted from segment attractiveness outputs and baseline positioning heuristics."
    )
    if notes:
        rationale = f"{rationale} Owner feedback incorporated: {notes}"
    return {
        "target_segment": segment,
        "positioning_statement": statement,
        "key_differentiators": [
            "Focused solution for the top-priority segment",
            "Service quality and consistency",
            "Clear, outcome-oriented value proposition",
        ],
        "proof_points": [
            "Segment fit from questionnaire analysis",
            "Business strengths aligned with buyer needs",
        ],
        "rationale": rationale,
    }


def generate_positioning(
    analysis_report: dict,
    owner_feedback: str = "",
) -> dict:
    if not settings.can_use_openai():
        return _fallback_positioning(analysis_report, owner_feedback)

    prompt = (
        "You are PositioningCopilotAgent for an AI marketing planner.\n"
        "Use the analysis report and optional owner feedback to draft one clear targeting and "
        "positioning statement.\n"
        "Return strict JSON with keys:\n"
        "target_segment, positioning_statement, key_differentiators, proof_points, rationale.\n"
        "Constraints:\n"
        "- Positioning statement must be one concise paragraph.\n"
        "- Include 3-5 differentiators and 2-4 proof points.\n\n"
        f"Analysis report:\n{json.dumps(analysis_report, ensure_ascii=True)}\n\n"
        f"Owner feedback:\n{owner_feedback}"
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
        if "positioning_statement" not in parsed:
            return _fallback_positioning(analysis_report, owner_feedback)
        return parsed
    except Exception:
        return _fallback_positioning(analysis_report, owner_feedback)
