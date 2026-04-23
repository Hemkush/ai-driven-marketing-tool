import json
import logging
from urllib.parse import urlparse
from statistics import mean
import re

from openai import OpenAI

from app.core.config import settings
from app.core.llm_tracker import tracked_responses
from app.core.quality_scorer import score_segment_analysis
from app.core.token_budget import trim_list, trim_str, get_budget

logger = logging.getLogger(__name__)


def _score_from_text(text: str, positive: list[str], negative: list[str]) -> int:
    score = 5
    lowered = text.lower()
    for token in positive:
        if token in lowered:
            score += 1
    for token in negative:
        if token in lowered:
            score -= 1
    return max(1, min(10, score))


def _response_to_text(resp) -> str:
    raw = getattr(resp, "output_text", None)
    if isinstance(raw, str) and raw.strip():
        return raw
    parts: list[str] = []
    for item in getattr(resp, "output", []) or []:
        for content in getattr(item, "content", []) or []:
            if getattr(content, "type", "") in {"output_text", "text"}:
                text = getattr(content, "text", None)
                if isinstance(text, str) and text.strip():
                    parts.append(text)
    return "\n".join(parts).strip()


def _extract_json(raw_text: str) -> dict | None:
    text = (raw_text or "").strip()
    if not text:
        return None
    for candidate in [text, text.replace("```json", "").replace("```", "").strip()]:
        try:
            parsed = json.loads(candidate)
            if isinstance(parsed, dict):
                return parsed
        except Exception:
            pass
    start = text.find("{")
    end = text.rfind("}")
    if start != -1 and end != -1 and end > start:
        try:
            parsed = json.loads(text[start : end + 1])
            if isinstance(parsed, dict):
                return parsed
        except Exception:
            return None
    return None


def _safe_list(value) -> list:
    return value if isinstance(value, list) else []


def _default_internal_sources() -> list[dict]:
    return [
        {
            "title": "Marketing Discovery Interview",
            "url": "internal://questionnaire-chat",
            "publisher": "MarketPilot",
            "published_at": "",
            "used_for": ["customer_insights", "competitive_landscape", "budget_constraints"],
            "note": "User-provided responses from the discovery interview.",
        },
        {
            "title": "Business Profile",
            "url": "internal://business-profile",
            "publisher": "MarketPilot",
            "published_at": "",
            "used_for": ["location_context", "business_model_context"],
            "note": "Business profile metadata including address and description.",
        },
    ]


def _sanitize_sources(raw_sources) -> list[dict]:
    def normalize_url(raw: str) -> str:
        val = (raw or "").strip()
        if not val:
            return ""
        # Extract URL from markdown style: [label](url)
        md_match = re.search(r"\((https?://[^)]+)\)", val)
        if md_match:
            val = md_match.group(1).strip()
        if val.startswith(("http://", "https://", "internal://")):
            return val
        # Promote bare domains to https URLs.
        if re.match(r"^[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}(/.*)?$", val):
            return f"https://{val}"
        return val

    sources: list[dict] = []
    seen: set[str] = set()
    for item in _safe_list(raw_sources):
        if not isinstance(item, dict):
            continue
        title = str(item.get("title", "")).strip()[:180]
        raw_url = (
            item.get("url")
            or item.get("source_url")
            or item.get("link")
            or item.get("href")
            or ""
        )
        url = normalize_url(str(raw_url))[:600]
        publisher = str(item.get("publisher", "")).strip()[:120]
        published_at = str(item.get("published_at", "")).strip()[:40]
        note = str(item.get("note", "")).strip()[:280]
        used_for = [str(x).strip()[:80] for x in _safe_list(item.get("used_for")) if str(x).strip()]
        if not url:
            continue
        # Only allow explicit web links or internal trace links for transparency.
        if not (url.startswith("http://") or url.startswith("https://") or url.startswith("internal://")):
            continue
        if ("..." in url or " " in url) and not url.startswith("internal://"):
            continue
        if url.startswith("http://") or url.startswith("https://"):
            parsed = urlparse(url)
            if not parsed.netloc or "." not in parsed.netloc:
                continue
        dedupe_key = f"{title}|{url}".lower()
        if dedupe_key in seen:
            continue
        seen.add(dedupe_key)
        sources.append(
            {
                "title": title or "Untitled source",
                "url": url,
                "publisher": publisher,
                "published_at": published_at,
                "used_for": used_for,
                "note": note,
            }
        )
    return sources


def _condense_text(text: str, limit: int = 360) -> str:
    cleaned = " ".join((text or "").strip().split())
    if len(cleaned) <= limit:
        return cleaned
    return cleaned[: limit - 3] + "..."


def _compact_transcript(responses: list[dict], max_items: int = 14) -> list[dict]:
    trimmed = responses[-max_items:] if len(responses) > max_items else responses
    output: list[dict] = []
    for r in trimmed:
        question = _condense_text(str(r.get("question_text", "")), limit=140)
        answer = _condense_text(str(r.get("answer_text", "")), limit=420)
        if not answer:
            continue
        output.append({"question": question, "answer": answer})
    return output


def _infer_fallback_segments(joined: str) -> list[dict]:
    lowered = joined.lower()

    local_terms = ["local", "nearby", "home", "residential", "community"]
    premium_terms = ["quality", "premium", "specialized", "expert", "custom"]
    repeat_terms = ["repeat", "maintenance", "subscription", "routine", "ongoing"]
    budget_terms = ["price", "affordable", "budget", "value", "cost"]
    smb_terms = ["business", "office", "commercial", "b2b", "company"]

    segments = [
        {
            "segment_name": "Local Homeowners",
            "size_growth_score": _score_from_text(joined, local_terms + repeat_terms, ["decline", "slow"]),
            "structural_score": _score_from_text(joined, ["underserved", "niche", "gap"], ["crowded", "competitive"]),
            "product_market_fit_score": _score_from_text(joined, premium_terms + ["service"], ["mismatch", "limited"]),
            "profitability_score": _score_from_text(joined, ["margin", "upsell", "bundle"], ["discount", "low budget"]),
            "notes": "Primary household segment inferred from service, location, and usage patterns.",
        },
        {
            "segment_name": "Price-Sensitive Households",
            "size_growth_score": _score_from_text(joined, budget_terms + local_terms, ["decline", "slow"]),
            "structural_score": _score_from_text(joined, ["convenience", "availability"], ["many competitors", "commoditized"]),
            "product_market_fit_score": _score_from_text(joined, ["value", "reliable", "simple"], ["premium-only", "complex"]),
            "profitability_score": _score_from_text(joined, ["volume", "repeat"], ["discount", "one-time"]),
            "notes": "Value-focused households that respond to reliability and transparent pricing.",
        },
        {
            "segment_name": "Small Commercial Clients",
            "size_growth_score": _score_from_text(joined, smb_terms + ["contract"], ["seasonal", "irregular"]),
            "structural_score": _score_from_text(joined, ["differentiated", "specialized"], ["crowded", "commoditized"]),
            "product_market_fit_score": _score_from_text(joined, ["service", "quality", "professional"], ["capacity issue", "delivery issue"]),
            "profitability_score": _score_from_text(joined, ["contract", "retainer", "high value"], ["low budget"]),
            "notes": "Small business and office accounts with recurring service potential.",
        },
    ]

    if any(x in lowered for x in ["wedding", "event", "occasion", "florist"]):
        segments.append(
            {
                "segment_name": "Event Buyers",
                "size_growth_score": _score_from_text(joined, ["wedding", "event", "corporate"], ["seasonal", "irregular"]),
                "structural_score": _score_from_text(joined, ["specialized", "differentiated"], ["many competitors", "commoditized"]),
                "product_market_fit_score": _score_from_text(joined, ["custom", "design", "service"], ["low capacity", "delivery issue"]),
                "profitability_score": _score_from_text(joined, ["high value", "bundle", "contract"], ["one-time", "low budget"]),
                "notes": "Included because responses explicitly referenced event-driven demand.",
            }
        )

    return segments[:4]


def _fallback_segment_analysis(responses: list[dict], business_address: str | None = None) -> dict:
    joined = " ".join((r.get("answer_text") or "") for r in responses)
    lowered = joined.lower()
    business_context = joined[:1200]

    geography = "local"
    if any(x in lowered for x in ["regional", "statewide"]):
        geography = "regional"
    # Do not switch to online if there is explicit local location context.
    if any(x in lowered for x in ["online only", "online-only", "ecommerce only"]):
        geography = "online"
    elif any(x in lowered for x in ["national", "global", "ecommerce"]):
        geography = "online"
    if business_address:
        geography = "local"

    geo_multiplier = {"local": 1.0, "regional": 1.8, "online": 2.6}[geography]
    base_market = int(850000 * geo_multiplier)
    tam = base_market
    sam = int(base_market * 0.38)
    som = int(base_market * 0.08)

    segments = _infer_fallback_segments(joined)
    for s in segments:
        s["overall_score"] = round(
            mean(
                [
                    s["size_growth_score"],
                    s["structural_score"],
                    s["product_market_fit_score"],
                    s["profitability_score"],
                ]
            ),
            2,
        )
    prioritized = sorted(segments, key=lambda x: x["overall_score"], reverse=True)

    cac = int(220 * (1.2 if "ads" in lowered or "paid" in lowered else 1.0))
    ltv = int(1100 * (1.2 if "repeat" in lowered or "subscription" in lowered else 1.0))
    ltv_cac = round(max(0.1, ltv / max(1, cac)), 2)

    channel_mix_efficiency = [
        {
            "channel": "Organic Social",
            "efficiency_score": _score_from_text(joined, ["social", "instagram"], ["no engagement"]),
            "est_cac_usd": int(cac * 0.7),
            "est_conversion_rate_pct": 2.8,
            "recommendation": "Use proof-driven short-form content and local trust signals.",
        },
        {
            "channel": "Local SEO / Maps",
            "efficiency_score": _score_from_text(joined, ["local", "nearby", "location"], ["online-only"]),
            "est_cac_usd": int(cac * 0.5),
            "est_conversion_rate_pct": 4.1,
            "recommendation": "Optimize local intent pages and service-area content.",
        },
        {
            "channel": "Paid Search",
            "efficiency_score": _score_from_text(joined, ["ads", "google"], ["low budget"]),
            "est_cac_usd": int(cac * 1.15),
            "est_conversion_rate_pct": 3.2,
            "recommendation": "Bid on high-intent keywords and segment landing pages by need.",
        },
    ]

    return {
        "analysis_source": "fallback",
        "deep_market_analysis": {
            "market_size_and_growth": [
                "Local TAM/SAM/SOM estimated from interview context and location assumptions.",
                "Growth potential is moderate-to-strong if recurring service behavior is captured."
            ],
            "core_market_drivers": [
                "Local intent demand and geographic relevance.",
                "Need for trusted execution and reduced customer effort.",
                "Proof-driven selection in competitive categories."
            ],
            "customer_segments": [
                "Primary segment: needs-based local buyers with recurring potential.",
                "Secondary segment: price-sensitive buyers requiring clear value framing.",
                "Expansion segment: small commercial clients with contract potential."
            ],
            "competitive_landscape_narrative": [
                "Category appears fragmented with many local alternatives.",
                "Differentiation depends on proof, speed, and service reliability."
            ],
            "industry_trends": [
                "Digital-first discovery (maps/search/social) remains decisive.",
                "Lifecycle and retention programs improve economics over one-time demand."
            ],
            "opportunities": [
                "Strengthen segment-specific offers and pages.",
                "Deploy channel spend based on CAC/LTV guardrails.",
                "Build repeat/retention motions for longer customer lifetime."
            ],
            "risks_and_constraints": [
                "Message-market mismatch risk in broad campaigns.",
                "Channel overspend risk without attribution discipline."
            ],
            "overall_outlook": "Favorable if execution stays focused, measurable, and segment-specific.",
        },
        "executive_brief": {
            "market_outlook": "Directionally positive, with demand shaped by local intent and category-specific trust signals.",
            "core_drivers": [
                "Local demand capture through geographic relevance and service reliability.",
                "Repeat-purchase or recurring-value opportunities from lifecycle-based needs.",
                "Proof-driven differentiation in a crowded but fragmented market.",
            ],
            "key_segments": [s["segment_name"] for s in prioritized[:3]],
            "competitive_snapshot": "Moderate fragmentation; smaller players can win with positioning clarity and faster execution.",
            "opportunities": [
                "Tighten segment-specific messaging and landing experiences.",
                "Prioritize highest-efficiency channels using CAC/LTV constraints.",
                "Package offers for retention and measurable outcomes.",
            ],
            "overall_outlook": "Favorable if execution stays focused on one primary segment and measurable acquisition economics.",
        },
        "segment_attractiveness_analysis": {
            "method": "heuristic_fallback",
            "business_context_excerpt": business_context,
            "business_address": business_address or "",
            "segments": prioritized,
            "recommended_primary_segment": prioritized[0]["segment_name"],
        },
        "market_sizing": {
            "geography_assumption": geography,
            "tam_estimate_usd": tam,
            "sam_estimate_usd": sam,
            "som_estimate_usd": som,
            "confidence": "medium",
        },
        "competitive_landscape": {
            "competitive_intensity_score": _score_from_text(
                joined, ["crowded", "many competitors"], ["unique", "underserved", "gap"]
            ),
            "white_space_opportunities": [
                "Niche positioning around measurable outcomes and service guarantees.",
                "Location-specific offer bundles for high-intent local searchers.",
            ],
            "barriers_to_entry": "Moderate service differentiation and trust moat required.",
        },
        "unit_economics": {
            "estimated_cac_usd": cac,
            "estimated_ltv_usd": ltv,
            "ltv_cac_ratio": ltv_cac,
            "estimated_payback_months": round(max(1.0, cac / max(1, ltv / 12)), 1),
        },
        "channel_mix_efficiency": channel_mix_efficiency,
        "pricing_power_analysis": {
            "pricing_power_score": _score_from_text(
                joined, ["quality", "premium", "expert"], ["discount", "cheap", "price sensitive"]
            ),
            "elasticity_risk": "medium",
            "recommended_pricing_motion": "Value-tiered packaging with proof-based premium upsell.",
        },
        "retention_risk_analysis": {
            "churn_risk_score": _score_from_text(
                joined, ["repeat", "subscription", "loyal"], ["one-time", "seasonal"]
            ),
            "top_retention_drivers": [
                "Education and onboarding after initial service delivery.",
                "Follow-up cadence tied to customer lifecycle milestones.",
            ],
        },
        "growth_scenarios_90_day": [
            {
                "scenario": "Base",
                "assumptions": "Current budget, moderate execution discipline.",
                "expected_pipeline_lift_pct": 12,
            },
            {
                "scenario": "Upside",
                "assumptions": "Sharper targeting + proof assets + channel optimization.",
                "expected_pipeline_lift_pct": 28,
            },
            {
                "scenario": "Downside",
                "assumptions": "Inconsistent execution and broad messaging.",
                "expected_pipeline_lift_pct": 4,
            },
        ],
        "strategic_risk_register": [
            {
                "risk": "Message-market mismatch",
                "severity": "high",
                "mitigation": "Run weekly message tests by segment and update offers monthly.",
            },
            {
                "risk": "Channel overspend with weak attribution",
                "severity": "medium",
                "mitigation": "Track channel-level CAC and pause underperforming campaigns bi-weekly.",
            },
            {
                "risk": "Competitor response to pricing/offer changes",
                "severity": "medium",
                "mitigation": "Defend with service proof, experience moat, and retention programs.",
            },
        ],
        "prioritization_matrix": [
            {"initiative": "Segment-specific landing pages", "impact": "high", "effort": "medium", "priority": "P1"},
            {"initiative": "Local SEO + Maps optimization", "impact": "high", "effort": "low", "priority": "P1"},
            {"initiative": "Proof-driven content engine", "impact": "medium", "effort": "medium", "priority": "P2"},
            {"initiative": "Pricing/offer packaging refresh", "impact": "medium", "effort": "high", "priority": "P3"},
        ],
        "executive_actions": [
            "Narrow to one primary segment and one adjacent segment for 90 days.",
            "Align channel budget to CAC/LTV performance thresholds.",
            "Deploy trust assets (proof, testimonials, outcomes) in every acquisition touchpoint.",
        ],
        "scoring_scale": "1 to 10, where 10 is strongest attractiveness",
        "assumptions": [
            "Heuristic estimates are directional until external data connectors/MCP enrichment are enabled.",
            "Financial outputs are planning estimates, not accounting forecasts.",
        ],
        "sources": _default_internal_sources(),
        "source_transparency": {
            "external_sources_used": False,
            "note": (
                "This run used fallback analysis from internal business inputs only. "
                "No external market sources were retrieved in this response."
            ),
            "verification_level": "internal_only",
        },
        "reasoning": (
            "Analysis generated from your questionnaire responses using heuristic rules. "
            "Segment scores and market sizing are directional estimates based on your business "
            "type and location context."
        ),
    }


def analyze_segments(responses: list[dict], business_address: str | None = None) -> dict:
    if not responses:
        report = _fallback_segment_analysis([], business_address=business_address)
        report["fallback_reason"] = "no_responses"
        return report

    if not settings.can_use_openai():
        report = _fallback_segment_analysis(responses, business_address=business_address)
        report["fallback_reason"] = "openai_unavailable"
        return report

    transcript = _compact_transcript(responses)

    prompt = (
        "You are SegmentAnalystAgent in a consulting-grade AI strategy platform.\n"
        "Create a high-end market and growth analysis using discovery responses and location.\n"
        "Return strict JSON only with these top-level keys:\n"
        "deep_market_analysis,"
        "segment_attractiveness_analysis, market_sizing, competitive_landscape, unit_economics,\n"
        "channel_mix_efficiency, pricing_power_analysis, retention_risk_analysis,\n"
        "growth_scenarios_90_day, strategic_risk_register, prioritization_matrix,\n"
        "executive_actions, scoring_scale, assumptions, executive_brief, sources, source_transparency.\n"
        "Rules:\n"
        "- deep_market_analysis must include: market_size_and_growth(3-6), core_market_drivers(3-6),\n"
        "  customer_segments(3-6), competitive_landscape_narrative(2-5), industry_trends(3-6),\n"
        "  opportunities(3-6), risks_and_constraints(2-5), overall_outlook.\n"
        "- Keep segment_attractiveness_analysis with method, business_context_excerpt, business_address,\n"
        "  segments (2-4), recommended_primary_segment.\n"
        "- Each segment must include size_growth_score, structural_score, product_market_fit_score,\n"
        "  profitability_score, overall_score, notes.\n"
        "- Provide numeric fields where possible for market sizing and unit economics.\n"
        "- growth_scenarios_90_day must include Base/Upside/Downside.\n"
        "- prioritization_matrix entries must include initiative, impact, effort, priority.\n"
        "- executive_brief must include market_outlook, core_drivers(3-6), key_segments(2-4), "
        "competitive_snapshot, opportunities(3-6), overall_outlook.\n"
        "- sources must be 3-10 items with keys: title, url, publisher, published_at, used_for(list), note.\n"
        "- Include only links you can provide explicitly. If unavailable, use internal:// URLs and explain in note.\n"
        "- source_transparency must include external_sources_used(bool), note, verification_level.\n"
        '- Include a top-level "reasoning" field (2-3 sentences) citing which specific user inputs '
        "drove the key segment and market conclusions. Reference actual details from the transcript.\n"
        f"Business address/location context:\n{business_address or ''}\n"
        f"Transcript:\n{json.dumps(transcript, ensure_ascii=True)}"
    )

    try:
        client = OpenAI(
            api_key=settings.openai_api_key,
            base_url=settings.openai_base_url,
            timeout=settings.openai_timeout_seconds,
            max_retries=settings.openai_max_retries,
        )
        resp = tracked_responses(client, agent="segment_analyst",
            model=settings.openai_model, input=prompt)
        parsed = _extract_json(_response_to_text(resp)) or {}
        score_segment_analysis(parsed)
        if "segment_attractiveness_analysis" not in parsed:
            report = _fallback_segment_analysis(responses, business_address=business_address)
            report["fallback_reason"] = "invalid_model_output"
            return report
        parsed["sources"] = _sanitize_sources(parsed.get("sources")) or _default_internal_sources()
        parsed["source_transparency"] = parsed.get("source_transparency") or {
            "external_sources_used": False,
            "note": "No explicit external sources provided by model; internal context shown.",
            "verification_level": "mixed",
        }
        parsed["executive_brief"] = parsed.get("executive_brief") or {
            "market_outlook": "Analysis generated from current business context.",
            "core_drivers": [],
            "key_segments": [],
            "competitive_snapshot": "",
            "opportunities": [],
            "overall_outlook": "",
        }
        parsed["deep_market_analysis"] = parsed.get("deep_market_analysis") or {
            "market_size_and_growth": [],
            "core_market_drivers": [],
            "customer_segments": [],
            "competitive_landscape_narrative": [],
            "industry_trends": [],
            "opportunities": [],
            "risks_and_constraints": [],
            "overall_outlook": "",
        }
        parsed["analysis_source"] = "ai"
        return parsed
    except Exception as exc:
        report = _fallback_segment_analysis(responses, business_address=business_address)
        report["fallback_reason"] = str(exc)[:140]
        return report


def answer_analysis_question(
    question: str,
    analysis_report: dict,
    discovery_responses: list[dict],
    business_address: str | None = None,
    chat_history: list[dict] | None = None,
    memory_context_chunks: list[dict] | None = None,
) -> dict:
    def _ensure_structured_answer(raw: str, include_validation: bool = False) -> str:
        text_raw = (raw or "").strip()
        if not text_raw:
            return ""
        lines = [ln.strip() for ln in text_raw.splitlines() if ln.strip()]
        if not lines:
            return ""

        # If already structured with headings and bullets, keep as-is.
        heading_like = sum(
            1
            for ln in lines
            if ln.endswith(":")
            and not ln.startswith("-")
            and len(ln.split()) <= 6
        )
        bullet_like = sum(1 for ln in lines if ln.startswith("-") or ln.startswith("*"))
        if heading_like >= 1 and bullet_like >= 2:
            return text_raw

        # Otherwise convert into a consistent structure.
        normalized = text_raw.replace("\r\n", "\n")
        parts = [p.strip() for p in normalized.split("\n\n") if p.strip()]

        bullets: list[str] = []
        for p in parts:
            p_clean = " ".join(p.split())
            if not p_clean:
                continue
            # Split long paragraph into concise bullet chunks.
            sentences = [s.strip() for s in p_clean.split(". ") if s.strip()]
            if len(sentences) <= 1:
                bullets.append(p_clean.rstrip("."))
            else:
                for s in sentences:
                    bullets.append(s.rstrip("."))

        if not bullets:
            bullets = [normalized.strip()]

        summary_items = bullets[:3]
        action_items = bullets[3:6]
        next_items = bullets[6:9]

        out_lines = ["Summary:"]
        out_lines.extend([f"- {x}" for x in summary_items] or ["- Key analysis insight generated from available context."])
        out_lines.append("")
        out_lines.append("Recommended Actions:")
        out_lines.extend([f"- {x}" for x in action_items] or ["- Prioritize highest-impact segment and channel opportunities."])
        if include_validation and next_items:
            out_lines.append("")
            out_lines.append("Next Questions / Validation:")
            out_lines.extend([f"- {x}" for x in next_items])
        return "\n".join(out_lines).strip()

    chat_history = chat_history or []
    q = (question or "").strip()
    if not q:
        return {
            "answer": "Please provide a question about the analysis.",
            "recommend_rerun": False,
            "rerun_reason": "",
            "source": "fallback",
        }

    lower_q = q.lower()
    include_validation = any(
        token in lower_q
        for token in [
            "validate",
            "validation",
            "assumption",
            "assumptions",
            "risk",
            "next question",
            "follow-up",
            "follow up",
            "what next",
        ]
    )

    if not settings.can_use_openai():
        recommended = analysis_report.get("segment_attractiveness_analysis", {}).get(
            "recommended_primary_segment", "the top-ranked segment"
        )
        lowered_q = q.lower()
        if "swot" in lowered_q:
            answer = (
                "SWOT Analysis (Fallback)\n\n"
                "Strengths:\n"
                "- Clear segment recommendation anchored in your discovery responses.\n"
                "- Location-aware analysis context supports local positioning.\n"
                "- Structured market and channel outputs enable quick decisions.\n\n"
                "Weaknesses:\n"
                "- External market validation may be limited in fallback mode.\n"
                "- Financial estimates are directional, not audited forecasts.\n"
                "- Insight quality depends on completeness of interview responses.\n\n"
                "Opportunities:\n"
                "- Focus campaign execution on the recommended segment.\n"
                "- Improve evidence by adding competitor and budget detail.\n"
                "- Rerun analysis after adding new business updates.\n\n"
                "Threats:\n"
                "- Competitive pressure can reduce conversion and pricing power.\n"
                "- Weak attribution can increase CAC through channel overspend.\n"
                "- Changing assumptions can invalidate current recommendations."
            )
        else:
            answer = (
                "Summary:\n"
                f"- Current analysis recommends focusing on {recommended}.\n"
                "- Strategy is strongest when tied to measurable CAC/LTV guardrails.\n\n"
                "Recommended Actions:\n"
                "- Prioritize one primary segment for the next 90 days.\n"
                "- Align channel spend to observed efficiency.\n"
                "- Add new facts and rerun analysis when assumptions change.\n\n"
                "When To Rerun:\n"
                "- Budget changed.\n"
                "- Target segment changed.\n"
                "- Competitor or location context changed."
            )
        rerun = any(token in q.lower() for token in ["rerun", "re-run", "update", "changed", "new info"])
        return {
            "answer": answer,
            "recommend_rerun": rerun,
            "rerun_reason": "User indicated updated assumptions." if rerun else "",
            "source": "fallback",
        }

    transcript = [
        {"question": r.get("question_text", ""), "answer": r.get("answer_text", "")}
        for r in discovery_responses
    ]
    memory_context_chunks = memory_context_chunks or []
    memory_context = []
    for chunk in memory_context_chunks[:8]:
        if not isinstance(chunk, dict):
            continue
        text = str(chunk.get("content_text", "")).strip()
        if not text:
            continue
        topic = str(chunk.get("topic_tag", "")).strip()
        memory_context.append({"topic": topic, "snippet": text[:400]})

    # Compact the report instead of dumping the full JSON (~10k tokens).
    # We only extract the fields actually needed to answer competitor/market questions.
    competitors = analysis_report.get("competitors") or []
    compact_competitors = []
    for c in competitors[:8]:
        ai = c.get("ai") if isinstance(c.get("ai"), dict) else {}
        compact_competitors.append({
            "name": c.get("name", ""),
            "rating": c.get("rating"),
            "price": c.get("price_label") or c.get("price_level"),
            "threat": ai.get("competitive_threat_level"),
            "how_they_compete": ai.get("how_they_compete"),
            "services": (ai.get("services_offered") or [])[:4],
            "review_summary": ai.get("review_summary", ""),
        })
    market_ai = analysis_report.get("market_overview") or {}
    compact_report = {
        "competitors": compact_competitors,
        "opportunity_gaps": (market_ai.get("opportunity_gaps") or [])[:5],
        "win_strategies": (market_ai.get("win_strategies") or [])[:5],
        "market_density": market_ai.get("market_density"),
        "swot_analysis": analysis_report.get("swot_analysis") or {},
        "hours_gap_analysis": analysis_report.get("hours_gap_analysis") or {},
    }

    prompt = (
        "You are CompetitiveBenchmarkingCopilot for a marketing strategy application.\n"
        "Answer user questions about the competitive benchmarking report clearly and concisely.\n"
        "The report contains real local competitor data fetched from Google Places, enriched with AI insights.\n"
        "Formatting rules — follow these exactly:\n"
        "- Use plain text section headings ending with ':' (e.g. 'Summary:') followed by bullet points.\n"
        "- Each bullet must start with '- ' (hyphen space).\n"
        "- If user asks for SWOT, use exactly: Strengths:, Weaknesses:, Opportunities:, Threats:\n"
        "- Provide 3-5 bullets under each heading.\n"
        "- Reference specific competitor names, ratings, and price levels where relevant.\n"
        "- Do NOT use markdown symbols (no **, no ##, no _).\n"
        "If user shares new facts that materially change their situation, set recommend_rerun to true.\n"
        "Return strict JSON only:\n"
        '{ "answer":"...", "recommend_rerun":true|false, "rerun_reason":"..." }\n\n'
        f"Business location: {business_address or ''}\n"
        f"Competitive report:\n{trim_str(json.dumps(compact_report, ensure_ascii=True), max_tokens=get_budget('segment_analyst_chat'), label='compact_report')}\n"
        f"Business interview context:\n{trim_str(json.dumps(transcript, ensure_ascii=True), max_tokens=600, label='transcript')}\n"
        f"Relevant memory snippets:\n{json.dumps(trim_list(memory_context, max_tokens=get_budget('memory_context'), label='memory_context'), ensure_ascii=True)}\n"
        f"Recent chat:\n{json.dumps(trim_list(chat_history[-6:], max_tokens=get_budget('chat_history'), label='chat_history'), ensure_ascii=True)}\n"
        f"User question: {q}"
    )
    try:
        client = OpenAI(
            api_key=settings.openai_api_key,
            base_url=settings.openai_base_url,
            timeout=max(20, settings.openai_timeout_seconds),
            max_retries=max(1, settings.openai_max_retries),
        )
        resp = tracked_responses(client, agent="segment_analyst_chat",
            model=settings.openai_model, input=prompt)
        raw_text = _response_to_text(resp)
        parsed = _extract_json(raw_text) or {}

        raw_answer = parsed.get("answer", "")
        if isinstance(raw_answer, dict):
            answer = str(raw_answer.get("answer") or raw_answer.get("content") or "").strip()
        elif isinstance(raw_answer, list):
            answer = " ".join(str(x).strip() for x in raw_answer if str(x).strip()).strip()
        else:
            answer = str(raw_answer).strip()

        # Handle nested JSON string cases, e.g. answer = '{"answer":"...","recommend_rerun":false}'
        if answer.startswith("{") and answer.endswith("}"):
            nested = _extract_json(answer) or {}
            nested_answer = nested.get("answer") or nested.get("content")
            if isinstance(nested_answer, str) and nested_answer.strip():
                answer = nested_answer.strip()
                if "recommend_rerun" not in parsed and "recommend_rerun" in nested:
                    parsed["recommend_rerun"] = nested.get("recommend_rerun")
                if "rerun_reason" not in parsed and "rerun_reason" in nested:
                    parsed["rerun_reason"] = nested.get("rerun_reason")

        # If model returned non-JSON text, still treat it as AI output.
        if not answer and raw_text.strip():
            answer = raw_text.strip()
            parsed = {}
        if not answer:
            raise ValueError("empty answer")
        return {
            "answer": _ensure_structured_answer(answer, include_validation=include_validation),
            "recommend_rerun": bool(parsed.get("recommend_rerun", False)),
            "rerun_reason": str(parsed.get("rerun_reason", "")).strip(),
            "source": "ai",
        }
    except Exception:
        recommended = analysis_report.get("segment_attractiveness_analysis", {}).get(
            "recommended_primary_segment", "the top-ranked segment"
        )
        lowered_q = q.lower()
        if "swot" in lowered_q:
            fallback_answer = (
                "SWOT Analysis (Fallback)\n\n"
                "Strengths:\n"
                f"- Recommended segment identified: {recommended}.\n"
                "- Discovery inputs provide customer and market context.\n"
                "- Action-oriented analysis artifacts are already generated.\n\n"
                "Weaknesses:\n"
                "- External validation may be limited in this response.\n"
                "- Some assumptions may require updated budget/cost inputs.\n"
                "- Results depend on completeness of captured interview data.\n\n"
                "Opportunities:\n"
                "- Sharpen positioning around the recommended segment.\n"
                "- Expand channel tests with CAC/LTV tracking.\n"
                "- Add competitor detail and rerun for stronger precision.\n\n"
                "Threats:\n"
                "- Competitor responses can reduce conversion gains.\n"
                "- Poor attribution can increase acquisition costs.\n"
                "- Macro demand shifts can impact near-term performance."
            )
        else:
            fallback_answer = (
                "Summary:\n"
                f"- Current analysis favors {recommended}.\n"
                "- Use this as directional guidance and validate with new inputs.\n\n"
                "Next Steps:\n"
                "- Continue targeted execution for the top segment.\n"
                "- Monitor channel efficiency and retention signals.\n"
                "- Rerun when business assumptions change."
            )
        return {
            "answer": fallback_answer,
            "recommend_rerun": any(token in q.lower() for token in ["rerun", "changed", "new info"]),
            "rerun_reason": "Potential input change detected.",
            "source": "fallback",
        }
