import json

from openai import OpenAI

from app.core.config import settings


def _extract_benchmarking_context(analysis_report: dict) -> dict:
    """Pull the relevant fields from a competitive benchmarking report for positioning."""
    report_type = analysis_report.get("report_type", "")

    # New competitive benchmarking format
    if report_type == "competitive_benchmarking":
        market = analysis_report.get("market_overview") or {}
        competitors = analysis_report.get("competitors") or []
        swot = analysis_report.get("swot_analysis") or {}
        hours_gap = analysis_report.get("hours_gap_analysis") or {}

        top_competitors = [
            {
                "name": c.get("name", ""),
                "threat": c.get("competitive_threat_level", ""),
                "rating": c.get("rating"),
                "price_label": c.get("price_label", ""),
                "how_they_compete": c.get("how_they_compete", ""),
                "services": c.get("services_offered", [])[:4],
            }
            for c in competitors[:5]
        ]

        return {
            "format": "competitive_benchmarking",
            "business_type": analysis_report.get("business_keyword", ""),
            "location": analysis_report.get("business_location", ""),
            "market_density": market.get("market_density", ""),
            "avg_rating": market.get("avg_rating"),
            "opportunity_gaps": market.get("opportunity_gaps") or [],
            "win_strategies": market.get("win_strategies") or [],
            "top_competitors": top_competitors,
            "swot": swot,
            "hours_recommendation": hours_gap.get("recommendation", ""),
        }

    # Legacy segment analysis format (fallback)
    return {
        "format": "legacy_segment_analysis",
        "segment": (
            analysis_report
            .get("segment_attractiveness_analysis", {})
            .get("recommended_primary_segment", "Primary customers")
        ),
        "raw": analysis_report,
    }


def _fallback_positioning(ctx: dict, owner_feedback: str = "") -> dict:
    business_type = ctx.get("business_type") or ctx.get("segment", "local customers")
    location = ctx.get("location", "your area")
    statement = (
        f"For people in {location} looking for trusted {business_type} services, "
        "our business delivers personalized, high-quality results that larger competitors can't match — "
        "backed by a deep commitment to the local community."
    )
    return {
        "target_segment": f"Local {business_type} customers in {location}",
        "positioning_statement": statement,
        "key_differentiators": [
            "Personalized service tailored to each client",
            "Deep local market knowledge",
            "Consistent quality and reliability",
        ],
        "proof_points": [
            "Owner-operated with direct accountability",
            "Local reputation built on repeat customers",
        ],
        "tagline": f"Your trusted local {business_type}.",
        "rationale": "Generated from baseline positioning heuristics."
        + (f" Owner feedback: {owner_feedback.strip()[:300]}" if owner_feedback.strip() else ""),
    }


def generate_positioning(
    analysis_report: dict,
    owner_feedback: str = "",
) -> dict:
    if not settings.can_use_openai():
        ctx = _extract_benchmarking_context(analysis_report)
        return _fallback_positioning(ctx, owner_feedback)

    ctx = _extract_benchmarking_context(analysis_report)

    if ctx["format"] == "competitive_benchmarking":
        context_block = (
            f"Business type: {ctx['business_type']}\n"
            f"Location: {ctx['location']}\n"
            f"Market density: {ctx['market_density']}\n"
            f"Average competitor rating: {ctx['avg_rating']}\n\n"
            f"Top competitors:\n{json.dumps(ctx['top_competitors'], ensure_ascii=True)}\n\n"
            f"Market opportunity gaps:\n" + "\n".join(f"- {g}" for g in ctx["opportunity_gaps"]) + "\n\n"
            f"Recommended win strategies:\n" + "\n".join(f"- {s}" for s in ctx["win_strategies"]) + "\n\n"
            f"SWOT summary:\n{json.dumps(ctx['swot'], ensure_ascii=True)}\n\n"
            + (f"Hours opportunity: {ctx['hours_recommendation']}\n" if ctx["hours_recommendation"] else "")
        )
    else:
        context_block = f"Analysis data:\n{json.dumps(ctx.get('raw', {}), ensure_ascii=True)}\n"

    feedback_block = f"\nOwner feedback to incorporate:\n{owner_feedback.strip()}" if owner_feedback.strip() else ""

    prompt = (
        "You are PositioningCopilotAgent for an AI marketing strategy platform.\n"
        "You help local small business owners craft a sharp, specific market positioning.\n\n"
        "Use the competitive benchmarking data and optional owner feedback below to generate "
        "a positioning statement that is:\n"
        "- Specific to this business type and local market (not generic)\n"
        "- Differentiated from the named competitors\n"
        "- Written in plain language the business owner would actually say\n"
        "- Grounded in real market gaps, not wishful thinking\n\n"
        "Return strict JSON with exactly these keys:\n"
        "{\n"
        '  "target_segment": "Who specifically this business serves (be concrete)",\n'
        '  "positioning_statement": "One focused paragraph — the core positioning message",\n'
        '  "tagline": "A punchy 5-10 word tagline the owner could use on their website",\n'
        '  "key_differentiators": ["3-5 specific things that set this business apart from the named competitors"],\n'
        '  "proof_points": ["2-4 credible, verifiable claims that back the positioning"],\n'
        '  "rationale": "1-2 sentences explaining why this positioning will win in this specific market"\n'
        "}\n\n"
        "Rules:\n"
        "- key_differentiators must reference actual gaps found in the competitor data\n"
        "- proof_points must be things the owner can actually demonstrate (not vague claims)\n"
        "- If owner feedback is provided, it takes priority over the data\n"
        "- Do NOT use phrases like 'unparalleled', 'world-class', or 'best-in-class'\n\n"
        f"Market context:\n{context_block}"
        f"{feedback_block}"
    )

    try:
        client = OpenAI(
            api_key=settings.openai_api_key,
            base_url=settings.openai_base_url,
            timeout=20,
            max_retries=1,
        )
        resp = client.responses.create(model=settings.openai_model, input=prompt)
        raw = resp.output_text.strip()
        # Strip markdown code fences if present
        if raw.startswith("```"):
            raw = raw.split("```")[1]
            if raw.startswith("json"):
                raw = raw[4:]
        parsed = json.loads(raw.strip())
        if "positioning_statement" not in parsed:
            return _fallback_positioning(ctx, owner_feedback)
        # Ensure tagline key always present
        parsed.setdefault("tagline", "")
        return parsed
    except Exception:
        return _fallback_positioning(ctx, owner_feedback)
