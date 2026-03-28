"""
Competitive Benchmarking Service
Pipeline: Geocode → Google Places Nearby Search → Place Details → OpenAI Enrichment
"""
import json

import httpx
from openai import OpenAI

from app.core.config import settings

GEOCODING_URL = "https://maps.googleapis.com/maps/api/geocode/json"
TEXT_SEARCH_URL = "https://maps.googleapis.com/maps/api/place/textsearch/json"
NEARBY_SEARCH_URL = "https://maps.googleapis.com/maps/api/place/nearbysearch/json"
PLACE_DETAILS_URL = "https://maps.googleapis.com/maps/api/place/details/json"

PRICE_LEVEL_LABELS = {0: "Free", 1: "$", 2: "$$", 3: "$$$", 4: "$$$$"}

PLACE_DETAIL_FIELDS = (
    "name,formatted_address,formatted_phone_number,website,"
    "opening_hours,reviews,price_level,rating,user_ratings_total,"
    "editorial_summary,business_status,types,url"
)



# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

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
            pass
    return None


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


def _infer_business_keyword(
    responses: list[dict],
    conversation_analysis: dict | None = None,
) -> str:
    """
    Infer the best Google Places search keyword for this business.

    Priority order:
    1. Use the stored conversation_analysis (summary + important_points) from the
       discovery interview — already computed by the AI during the chat, zero extra cost.
    2. Fall back to a targeted AI call on the transcript if no analysis is stored.
    3. Last resort: extract from the primary-service answer directly.
    """
    # --- Priority 1: use stored conversation analysis ---
    if conversation_analysis:
        # Build a short context from summary + Business-tagged important points
        summary = str(conversation_analysis.get("summary", "")).strip()
        business_points = [
            p for p in (conversation_analysis.get("important_points") or [])
            if str(p).lower().startswith("business:")
        ]
        context = summary
        if business_points:
            context = f"{summary}\n" + "\n".join(business_points)

        if context.strip() and settings.can_use_openai():
            prompt = (
                "Based on the business description below, return the single most accurate "
                "Google Places search keyword to find local competitors.\n"
                "Rules:\n"
                "- Return ONLY the keyword, nothing else.\n"
                "- Use a specific business-type term "
                "(e.g. 'florist', 'landscaping', 'hair salon', 'plumber', 'restaurant').\n"
                "- Do NOT return broad terms like 'small business' or 'local business'.\n\n"
                f"Business description:\n{context}"
            )
            try:
                client = OpenAI(
                    api_key=settings.openai_api_key,
                    base_url=settings.openai_base_url,
                    timeout=10,
                    max_retries=1,
                )
                resp = client.responses.create(model=settings.openai_model, input=prompt)
                keyword = _response_to_text(resp).strip().lower()
                keyword = keyword.splitlines()[0].strip("\"'").strip()
                if keyword and len(keyword) <= 80:
                    return keyword
            except Exception:
                pass

    # --- Priority 2: AI call on full transcript ---
    if settings.can_use_openai() and responses:
        transcript = _build_interview_context(responses)
        prompt = (
            "You are reading a marketing discovery interview for a small business.\n"
            "Return the single most accurate Google Places search keyword "
            "to find local competitors for this business.\n"
            "Rules:\n"
            "- Return ONLY the keyword, nothing else.\n"
            "- Use a specific business-type term "
            "(e.g. 'florist', 'landscaping', 'hair salon', 'plumber', 'restaurant').\n"
            "- Do NOT return broad terms like 'small business' or 'local business'.\n\n"
            f"Interview transcript:\n{transcript}"
        )
        try:
            client = OpenAI(
                api_key=settings.openai_api_key,
                base_url=settings.openai_base_url,
                timeout=15,
                max_retries=1,
            )
            resp = client.responses.create(model=settings.openai_model, input=prompt)
            keyword = _response_to_text(resp).strip().lower()
            keyword = keyword.splitlines()[0].strip("\"'").strip()
            if keyword and len(keyword) <= 80:
                return keyword
        except Exception:
            pass

    # --- Priority 3: extract from primary product/service answer ---
    for r in responses:
        q = str(r.get("question_text", "")).lower()
        if "primary product" in q or "primary service" in q or "what do you" in q:
            answer = str(r.get("answer_text", "")).strip()
            if answer:
                return answer[:60]

    return "local business"


def _geocode_address(address: str) -> tuple[tuple[float, float] | None, str]:
    """Convert address string to (lat, lng) via Google Geocoding API.
    Returns (coords, status_message)."""
    if not address:
        return None, "no_address_provided"
    if not settings.google_places_api_key:
        return None, "api_key_missing"
    try:
        resp = httpx.get(
            GEOCODING_URL,
            params={"address": address, "key": settings.google_places_api_key},
            timeout=10,
        )
        data = resp.json()
        status = data.get("status", "UNKNOWN")
        if status == "OK" and data.get("results"):
            loc = data["results"][0]["geometry"]["location"]
            return (float(loc["lat"]), float(loc["lng"])), "OK"
        return None, f"geocoding_status:{status}"
    except Exception as e:
        return None, f"geocoding_error:{e}"


def _fetch_nearby_competitors(lat: float, lng: float, keyword: str, radius: int) -> tuple[list[dict], str]:
    """Fetch nearby businesses via Google Places Nearby Search.
    Returns (results, status_message)."""
    try:
        resp = httpx.get(
            NEARBY_SEARCH_URL,
            params={
                "location": f"{lat},{lng}",
                "radius": radius,
                "keyword": keyword,
                "key": settings.google_places_api_key,
            },
            timeout=15,
        )
        data = resp.json()
        status = data.get("status", "UNKNOWN")
        if status in ("OK", "ZERO_RESULTS"):
            return data.get("results", []), status
        # Surface error_message from Google if available
        error_msg = data.get("error_message", "")
        return [], f"places_status:{status}" + (f" - {error_msg}" if error_msg else "")
    except Exception as e:
        return [], f"places_error:{e}"


def _text_search_competitors(keyword: str, location: str) -> tuple[list[dict], str]:
    """Search competitors via Google Places Text Search (no geocoding needed).
    Returns (results, status_message)."""
    query = f"{keyword} near {location}"
    try:
        resp = httpx.get(
            TEXT_SEARCH_URL,
            params={"query": query, "key": settings.google_places_api_key},
            timeout=15,
        )
        data = resp.json()
        status = data.get("status", "UNKNOWN")
        if status in ("OK", "ZERO_RESULTS"):
            return data.get("results", []), status
        error_msg = data.get("error_message", "")
        return [], f"text_search_status:{status}" + (f" - {error_msg}" if error_msg else "")
    except Exception as e:
        return [], f"text_search_error:{e}"


def _fetch_place_details(place_id: str) -> dict:
    """Fetch detailed info for a single place via Place Details API."""
    try:
        resp = httpx.get(
            PLACE_DETAILS_URL,
            params={
                "place_id": place_id,
                "fields": PLACE_DETAIL_FIELDS,
                "key": settings.google_places_api_key,
            },
            timeout=10,
        )
        data = resp.json()
        if data.get("status") == "OK":
            return data.get("result", {})
    except Exception:
        pass
    return {}


def _build_interview_context(responses: list[dict]) -> str:
    """Build compact interview transcript for OpenAI prompt."""
    lines = []
    for r in responses[-14:]:
        q = str(r.get("question_text", "")).strip()
        a = str(r.get("answer_text", "")).strip()
        if a:
            lines.append(f"Q: {q}\nA: {a}")
    return "\n\n".join(lines)


def _enrich_with_ai(
    competitors: list[dict],
    interview_context: str,
    business_address: str,
    business_keyword: str,
) -> dict:
    """Use OpenAI to enrich competitor profiles and generate market overview."""
    if not settings.can_use_openai() or not competitors:
        return {}

    # Build compact summaries for the prompt
    summaries = []
    for c in competitors:
        reviews = [r.get("text", "") for r in (c.get("reviews") or []) if r.get("text")]
        editorial = c.get("editorial_summary") or {}
        editorial_text = (
            editorial.get("overview", "")
            if isinstance(editorial, dict)
            else str(editorial)
        )
        summaries.append({
            "name": c.get("name", ""),
            "address": c.get("formatted_address") or c.get("vicinity", ""),
            "rating": c.get("rating"),
            "review_count": c.get("user_ratings_total"),
            "price_level": c.get("price_level"),
            "price_label": PRICE_LEVEL_LABELS.get(c.get("price_level"), ""),
            "types": (c.get("types") or [])[:4],
            "editorial_summary": editorial_text,
            "review_snippets": reviews[:3],
            "hours": (c.get("opening_hours") or {}).get("weekday_text", [])
            if isinstance(c.get("opening_hours"), dict)
            else [],
        })

    prompt = (
        "You are CompetitiveBenchmarkingAgent for an AI marketing strategy platform.\n"
        "You are given real competitor data fetched from Google Places for a local SMB market.\n"
        "Your job is to enrich each competitor with strategic insights, generate a market overview,\n"
        "analyse hours gaps, and produce a SWOT analysis for the business being benchmarked.\n\n"
        "Return strict JSON only with this exact structure:\n"
        "{\n"
        '  "competitors": [\n'
        "    {\n"
        '      "name": "exact name from input",\n'
        '      "business_model": "e.g. Independent owner-operated / Franchise / Chain",\n'
        '      "services_offered": ["service1", "service2", "service3"],\n'
        '      "special_services": ["differentiator1", "differentiator2"],\n'
        '      "estimated_discounts": ["seasonal bundle", "first-time discount"],\n'
        '      "pricing_notes": "Estimated price range and pricing strategy",\n'
        '      "competitive_threat_level": "high | medium | low",\n'
        '      "how_they_compete": "Brief strategic summary of their competitive position",\n'
        '      "review_summary": "What customers love and what they complain about"\n'
        "    }\n"
        "  ],\n"
        '  "market_overview": {\n'
        '    "market_density": "low | medium | high",\n'
        '    "market_size_notes": "Local market context and size estimate",\n'
        '    "opportunity_gaps": ["gap1", "gap2", "gap3"],\n'
        '    "win_strategies": ["strategy1", "strategy2", "strategy3"]\n'
        "  },\n"
        '  "hours_gap_analysis": {\n'
        '    "opportunity_windows": ["e.g. Sunday evenings — no competitor open after 5 PM"],\n'
        '    "coverage_notes": "Brief summary of how competitors cluster their hours",\n'
        '    "recommendation": "Single most actionable hours-based move for the owner"\n'
        "  },\n"
        '  "swot_analysis": {\n'
        '    "strengths": ["strength inferred from owner interview — specific, not generic"],\n'
        '    "weaknesses": ["weakness inferred from owner interview or new-entrant status"],\n'
        '    "opportunities": ["market opportunity tied to competitor gaps or unmet demand"],\n'
        '    "threats": ["concrete threat from a specific competitor or market trend"]\n'
        "  }\n"
        "}\n\n"
        "Rules:\n"
        "- Match competitor names exactly as given — do not rename.\n"
        "- Base services_offered on business type and review context.\n"
        "- Infer estimated_discounts from common patterns for the business type.\n"
        "- pricing_notes should interpret the Google price_level ($/$$/$$$/$$$$) into real ranges.\n"
        "- opportunity_gaps must be specific to THIS local market, not generic advice.\n"
        "- win_strategies must be actionable and tied to the gaps found.\n"
        "- hours_gap_analysis: examine the weekday_text hours for each competitor and identify\n"
        "  time slots (early morning, evenings, weekends, holidays) where no or few competitors operate.\n"
        "  If no hours data is available, say so in coverage_notes and give a generic recommendation.\n"
        "- swot_analysis: Strengths and Weaknesses are about the OWNER's business (use interview context).\n"
        "  Opportunities and Threats come from the competitor and market data.\n"
        "  Each list must have 3-4 items. Be specific — avoid platitudes.\n\n"
        f"Business being benchmarked: {business_keyword}\n"
        f"Business location: {business_address}\n"
        f"Owner's interview context:\n{interview_context}\n\n"
        f"Competitors from Google Places:\n{json.dumps(summaries, ensure_ascii=True)}"
    )

    try:
        client = OpenAI(
            api_key=settings.openai_api_key,
            base_url=settings.openai_base_url,
            timeout=settings.openai_timeout_seconds,
            max_retries=settings.openai_max_retries,
        )
        resp = client.responses.create(model=settings.openai_model, input=prompt)
        return _extract_json(_response_to_text(resp)) or {}
    except Exception:
        return {}


def _fallback_benchmarking(business_address: str, reason: str) -> dict:
    """Minimal fallback when Google Places API is unavailable or misconfigured."""
    return {
        "report_type": "competitive_benchmarking",
        "analysis_source": "fallback",
        "business_location": business_address,
        "competitors": [],
        "market_overview": {
            "total_competitors_found": 0,
            "market_density": "unknown",
            "avg_rating": None,
            "avg_price_level": None,
            "market_size_notes": (
                "Google Places API key is not configured. "
                "Add GOOGLE_PLACES_API_KEY to your .env to fetch real local competitor data."
            ),
            "opportunity_gaps": [],
            "win_strategies": [],
        },
        "fallback_reason": reason,
    }


# ---------------------------------------------------------------------------
# Main entry point
# ---------------------------------------------------------------------------

def run_competitive_benchmarking(
    responses: list[dict],
    business_address: str | None = None,
    conversation_analysis: dict | None = None,
) -> dict:
    """
    Full pipeline:
      1. Infer business keyword from interview responses
      2. Geocode business address
      3. Nearby Search → top competitors
      4. Place Details → enrich each competitor
      5. OpenAI enrichment → business model, services, threat level, gaps, strategies
      6. Return structured benchmarking report
    """
    if not settings.google_places_api_key:
        return _fallback_benchmarking(business_address or "", "google_places_api_key_not_configured")

    diagnostics: dict = {}
    business_keyword = _infer_business_keyword(responses, conversation_analysis=conversation_analysis)
    diagnostics["keyword"] = business_keyword

    raw_places: list[dict] = []

    # --- Strategy 1: Geocode → Nearby Search (most accurate, radius-controlled) ---
    coords, geo_status = _geocode_address(business_address or "") if business_address else (None, "no_address")
    diagnostics["geocode_status"] = geo_status

    if coords:
        lat, lng = coords
        raw_places, nearby_status = _fetch_nearby_competitors(
            lat, lng, business_keyword, settings.benchmarking_radius_meters
        )
        diagnostics["nearby_status"] = nearby_status
        # Broaden if nothing found
        if not raw_places:
            raw_places, nearby_status2 = _fetch_nearby_competitors(
                lat, lng, "business", settings.benchmarking_radius_meters * 2
            )
            diagnostics["nearby_fallback_status"] = nearby_status2

    # --- Strategy 2: Text Search fallback (works without Geocoding API) ---
    if not raw_places and business_address:
        raw_places, text_status = _text_search_competitors(business_keyword, business_address)
        diagnostics["text_search_status"] = text_status

    diagnostics["raw_places_count"] = len(raw_places)

    # Sort by rating descending and take top 10
    raw_places.sort(key=lambda x: float(x.get("rating") or 0), reverse=True)
    raw_places = raw_places[:10]

    # Fetch place details for each
    detailed: list[dict] = []
    for place in raw_places:
        place_id = place.get("place_id", "")
        if place_id:
            details = _fetch_place_details(place_id)
            detailed.append({**place, **details})
        else:
            detailed.append(place)

    # Aggregate stats
    ratings = [c["rating"] for c in detailed if c.get("rating") is not None]
    prices = [c["price_level"] for c in detailed if c.get("price_level") is not None]
    avg_rating = round(sum(ratings) / len(ratings), 1) if ratings else None
    avg_price_level = round(sum(prices) / len(prices), 1) if prices else None

    # AI enrichment
    interview_context = _build_interview_context(responses)
    enrichment = _enrich_with_ai(detailed, interview_context, business_address or "", business_keyword)

    ai_by_name = {c["name"]: c for c in (enrichment.get("competitors") or [])}
    market_ai = enrichment.get("market_overview") or {}
    hours_ai = enrichment.get("hours_gap_analysis") or {}
    swot_ai = enrichment.get("swot_analysis") or {}

    # Build final competitor profiles
    threat_order = {"high": 0, "medium": 1, "low": 2}
    final_competitors: list[dict] = []

    for c in detailed:
        name = c.get("name", "")
        ai = ai_by_name.get(name, {})

        review_snippets = [
            r.get("text", "")[:200]
            for r in (c.get("reviews") or [])
            if r.get("text")
        ]
        hours_text: list[str] = []
        oh = c.get("opening_hours") or {}
        if isinstance(oh, dict):
            hours_text = oh.get("weekday_text") or []

        editorial = c.get("editorial_summary") or {}
        editorial_text = (
            editorial.get("overview", "")
            if isinstance(editorial, dict)
            else str(editorial)
        )

        final_competitors.append({
            # --- Google Places data ---
            "name": name,
            "address": c.get("formatted_address") or c.get("vicinity", ""),
            "phone": c.get("formatted_phone_number", ""),
            "website": c.get("website", ""),
            "google_maps_url": c.get("url", ""),
            "rating": c.get("rating"),
            "review_count": c.get("user_ratings_total"),
            "price_level": c.get("price_level"),
            "price_label": PRICE_LEVEL_LABELS.get(c.get("price_level"), "N/A"),
            "hours": hours_text,
            "open_now": oh.get("open_now") if isinstance(oh, dict) else None,
            "types": (c.get("types") or [])[:4],
            "review_snippets": review_snippets,
            "editorial_summary": editorial_text,
            "business_status": c.get("business_status", "OPERATIONAL"),
            "source": "google_places",
            # --- AI enriched ---
            "business_model": ai.get("business_model", ""),
            "services_offered": ai.get("services_offered") or [],
            "special_services": ai.get("special_services") or [],
            "estimated_discounts": ai.get("estimated_discounts") or [],
            "pricing_notes": ai.get("pricing_notes", ""),
            "competitive_threat_level": ai.get("competitive_threat_level", "medium"),
            "how_they_compete": ai.get("how_they_compete", ""),
            "review_summary": ai.get("review_summary", ""),
        })

    # Sort: threat level first, then rating
    final_competitors.sort(
        key=lambda x: (
            threat_order.get(x.get("competitive_threat_level", "medium"), 1),
            -(x.get("rating") or 0),
        )
    )

    return {
        "report_type": "competitive_benchmarking",
        "analysis_source": "hybrid" if final_competitors else "ai_only",
        "business_location": business_address or "",
        "business_keyword": business_keyword,
        "competitors": final_competitors,
        "market_overview": {
            "total_competitors_found": len(final_competitors),
            "market_density": market_ai.get("market_density", "medium"),
            "avg_rating": avg_rating,
            "avg_price_level": avg_price_level,
            "market_size_notes": market_ai.get("market_size_notes", ""),
            "opportunity_gaps": market_ai.get("opportunity_gaps") or [],
            "win_strategies": market_ai.get("win_strategies") or [],
        },
        "hours_gap_analysis": {
            "opportunity_windows": hours_ai.get("opportunity_windows") or [],
            "coverage_notes": hours_ai.get("coverage_notes", ""),
            "recommendation": hours_ai.get("recommendation", ""),
        },
        "swot_analysis": {
            "strengths": swot_ai.get("strengths") or [],
            "weaknesses": swot_ai.get("weaknesses") or [],
            "opportunities": swot_ai.get("opportunities") or [],
            "threats": swot_ai.get("threats") or [],
        },
        "diagnostics": diagnostics,
    }
