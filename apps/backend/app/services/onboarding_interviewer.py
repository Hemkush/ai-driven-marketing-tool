import json
import re
from datetime import datetime, timezone

from openai import OpenAI

from app.core.config import settings


DEFAULT_QUESTIONS = [
    "What specific customer segment brings most of your revenue today?",
    "What is the biggest marketing challenge you face this quarter?",
    "What is your approximate monthly marketing budget range?",
]

REQUIRED_CHAT_TOPICS = ["business", "customer", "competitors", "budget", "cost", "goal"]
IMPORTANT_POINT_TOPICS = {"business", "customer", "competitors", "budget", "cost", "goal"}
POINT_STOP_WORDS = {
    "the",
    "and",
    "for",
    "with",
    "that",
    "this",
    "from",
    "into",
    "about",
    "their",
    "they",
    "them",
    "your",
    "you",
    "are",
    "have",
    "has",
    "had",
    "not",
    "but",
    "can",
    "will",
    "was",
    "were",
}


def _tokenize_point(text: str) -> set[str]:
    tokens = re.findall(r"[a-zA-Z]{3,}", text.lower())
    return {t for t in tokens if t not in POINT_STOP_WORDS}


def _normalize_point(raw_point: str) -> str:
    point = (raw_point or "").strip().replace("\n", " ")
    point = re.sub(r"\s+", " ", point)
    if not point:
        return ""

    # Ensure "Topic: detail" format.
    if ":" in point:
        left, right = point.split(":", 1)
        topic = left.strip().lower()
        detail = right.strip()
    else:
        topic = "business"
        detail = point

    if topic not in IMPORTANT_POINT_TOPICS:
        topic = "business"

    # Keep concise and readable.
    detail = re.sub(r"^[\-\u2022\d\.\)\s]+", "", detail).strip()
    words = detail.split()
    if len(words) > 20:
        detail = " ".join(words[:20]).rstrip(".,;:") + "..."
    if not detail:
        return ""

    label = topic.capitalize()
    return f"{label}: {detail}"


def _dedupe_points_semantic(points: list[str], max_points: int = 5) -> list[str]:
    kept: list[str] = []
    kept_tokens: list[set[str]] = []

    for raw in points:
        point = _normalize_point(raw)
        if not point:
            continue

        # Exact dedupe.
        if point.lower() in {k.lower() for k in kept}:
            continue

        tokens = _tokenize_point(point)
        is_dup = False
        for prev_tokens in kept_tokens:
            if not tokens or not prev_tokens:
                continue
            overlap = len(tokens & prev_tokens) / max(1, min(len(tokens), len(prev_tokens)))
            if overlap >= 0.8:
                is_dup = True
                break
        if is_dup:
            continue

        kept.append(point)
        kept_tokens.append(tokens)
        if len(kept) >= max_points:
            break

    return kept


def _derive_important_points(responses: list[dict], max_points: int = 5) -> list[str]:
    points: list[str] = []
    seen: set[str] = set()

    for row in responses:
        question = str(row.get("question_text", "")).strip().lower()
        answer = str(row.get("answer_text", "")).strip()
        if not answer:
            continue

        if any(k in question for k in ["customer", "audience", "buyer"]):
            prefix = "Customer"
        elif any(k in question for k in ["competitor", "competition", "alternative", "rival"]):
            prefix = "Competitors"
        elif any(k in question for k in ["budget", "spend"]):
            prefix = "Budget"
        elif any(k in question for k in ["cost", "cac", "expense"]):
            prefix = "Cost"
        elif any(k in question for k in ["goal", "objective", "target", "plan"]):
            prefix = "Goal"
        else:
            prefix = "Business"

        lines = [x.strip() for x in answer.splitlines() if x.strip()]
        if lines:
            base = lines[0]
            # If first line is just list numbering like "1." choose next informative line.
            if re.fullmatch(r"\d+[\).\-\s]*", base) and len(lines) > 1:
                base = lines[1]
        else:
            base = answer
        base = re.sub(r"^\d+[\).\-\s]+", "", base).strip()
        base = base.replace("  ", " ")
        if len(base) > 90:
            base = base[:87].rstrip() + "..."

        point = f"{prefix}: {base}" if base else ""
        key = point.lower().strip()
        if not point or key in seen:
            continue
        seen.add(key)
        points.append(point)
        if len(points) >= max_points:
            break

    return _dedupe_points_semantic(points, max_points=max_points)


def _build_insight_evidence(insights: list[str], important_points: list[str]) -> list[dict]:
    bundles: list[dict] = []
    norm_points = [p.lower() for p in important_points]
    for insight in insights:
        insight_norm = insight.lower()
        insight_tokens = _tokenize_point(insight_norm)
        matches: list[str] = []
        for idx, point in enumerate(important_points):
            point_norm = norm_points[idx]
            point_tokens = _tokenize_point(point_norm)
            # Avoid echoing evidence that is effectively same as insight sentence.
            if insight_tokens and point_tokens:
                overlap_ratio = len(insight_tokens & point_tokens) / max(
                    1, min(len(insight_tokens), len(point_tokens))
                )
                if overlap_ratio >= 0.8:
                    continue
            overlap = 0
            for token in re.findall(r"[a-zA-Z]{4,}", insight_norm):
                if token in point_norm:
                    overlap += 1
            if overlap > 0:
                matches.append(point)
        if not matches:
            # Fallback to first distinct points that are not near-duplicates.
            for point in important_points:
                point_tokens = _tokenize_point(point)
                if not insight_tokens or not point_tokens:
                    matches.append(point)
                else:
                    overlap_ratio = len(insight_tokens & point_tokens) / max(
                        1, min(len(insight_tokens), len(point_tokens))
                    )
                    if overlap_ratio < 0.8:
                        matches.append(point)
                if len(matches) >= 2:
                    break
        bundles.append(
            {
                "insight": insight,
                "evidence_points": matches[:2],
                "evidence_items": [],
            }
        )
    return bundles


def _build_evidence_items(
    responses: list[dict], insight: str, max_items: int = 2
) -> list[dict]:
    insight_tokens = _tokenize_point(insight)
    ranked: list[tuple[int, dict]] = []

    for row in responses:
        question = str(row.get("question_text", "")).strip()
        answer = str(row.get("answer_text", "")).strip()
        if not question or not answer:
            continue

        # Use first meaningful line/sentence as quote.
        quote = answer.splitlines()[0].strip() if answer.splitlines() else answer
        quote = quote.split(".")[0].strip() if "." in quote else quote
        if len(quote.split()) > 24:
            quote = " ".join(quote.split()[:24]).rstrip(".,;:") + "..."
        if not quote:
            continue

        quote_tokens = _tokenize_point(f"{question} {quote}")
        if not quote_tokens:
            continue
        overlap = len(insight_tokens & quote_tokens) if insight_tokens else 0
        ranked.append(
            (
                overlap,
                {
                    "question_text": question,
                    "matched_quote": quote,
                },
            )
        )

    ranked.sort(key=lambda x: x[0], reverse=True)
    picked: list[dict] = []
    seen_questions: set[str] = set()
    for score, item in ranked:
        if item["question_text"].lower() in seen_questions:
            continue
        # Prefer meaningful overlap, but allow top rows as fallback if nothing overlaps.
        if score == 0 and len(picked) >= 1:
            continue
        picked.append(item)
        seen_questions.add(item["question_text"].lower())
        if len(picked) >= max_items:
            break

    return picked


def _extract_json_from_text(raw_text: str) -> dict | None:
    text = (raw_text or "").strip()
    if not text:
        return None

    # Remove markdown code fences if present.
    fenced = re.sub(r"^```(?:json)?\s*|\s*```$", "", text, flags=re.IGNORECASE | re.DOTALL).strip()
    for candidate in [text, fenced]:
        try:
            parsed = json.loads(candidate)
            if isinstance(parsed, dict):
                return parsed
        except Exception:
            pass

    # Try extracting first JSON object block.
    start = text.find("{")
    end = text.rfind("}")
    if start != -1 and end != -1 and end > start:
        candidate = text[start : end + 1]
        try:
            parsed = json.loads(candidate)
            if isinstance(parsed, dict):
                return parsed
        except Exception:
            return None
    return None


def _response_to_text(resp) -> str:
    # SDK convenience field first.
    raw = getattr(resp, "output_text", None)
    if isinstance(raw, str) and raw.strip():
        return raw

    # Fallback: stitch text parts from response output content blocks.
    parts: list[str] = []
    for item in getattr(resp, "output", []) or []:
        for content in getattr(item, "content", []) or []:
            if getattr(content, "type", "") in {"output_text", "text"}:
                txt = getattr(content, "text", None)
                if isinstance(txt, str) and txt.strip():
                    parts.append(txt)
    return "\n".join(parts).strip()


def _fallback_questions(responses: list[dict], max_questions: int) -> list[str]:
    if not responses:
        return DEFAULT_QUESTIONS[:max_questions]

    joined = " ".join((r.get("answer_text") or "").lower() for r in responses)
    candidates: list[str] = []

    if "wedding" in joined or "event" in joined:
        candidates.append("Which event types are most profitable for your business?")
    if "local" in joined or "nearby" in joined:
        candidates.append("What geographic areas do you want to prioritize in the next 90 days?")
    if "instagram" in joined or "social" in joined:
        candidates.append("Which content themes on social currently get the best engagement?")
    if "price" in joined or "budget" in joined or "cost" in joined:
        candidates.append("What price sensitivity do you observe across different customer groups?")
    if "competitor" in joined:
        candidates.append("Which competitors win customers from you most often, and why?")

    if len(candidates) < max_questions:
        for q in DEFAULT_QUESTIONS:
            if q not in candidates:
                candidates.append(q)
            if len(candidates) >= max_questions:
                break

    return candidates[:max_questions]


def _fallback_structured_questions(
    responses: list[dict], max_questions: int
) -> list[dict]:
    return [
        {
            "question_text": q,
            "question_type": "open_ended",
            "question_options": [],
        }
        for q in _fallback_questions(responses, max_questions)
    ]


def _topic_coverage(responses: list[dict]) -> set[str]:
    text = " ".join(
        f"{r.get('question_text', '')} {r.get('answer_text', '')}" for r in responses
    ).lower()
    coverage = set()
    if any(k in text for k in ["business", "offer", "service", "product", "company"]):
        coverage.add("business")
    if any(k in text for k in ["customer", "audience", "buyer", "segment"]):
        coverage.add("customer")
    if any(k in text for k in ["competitor", "competition", "alternative", "rival"]):
        coverage.add("competitors")
    if any(k in text for k in ["budget", "spend", "ad spend", "marketing budget"]):
        coverage.add("budget")
    if any(k in text for k in ["cost", "cac", "acquisition cost", "expense"]):
        coverage.add("cost")
    if any(
        k in text
        for k in ["goal", "objective", "target", "12 months", "next year", "plan", "roadmap"]
    ):
        coverage.add("goal")
    return coverage


def _fallback_chat_question(responses: list[dict]) -> dict:
    covered = _topic_coverage(responses)
    missing = [topic for topic in REQUIRED_CHAT_TOPICS if topic not in covered]
    if missing:
        topic = missing[0]
        mapping = {
            "business": "What does your business offer, and what makes it valuable to customers?",
            "customer": "Who is your ideal customer, and what are their top needs?",
            "competitors": "Who are your top competitors, and where do they currently outperform you?",
            "budget": "What is your approximate monthly marketing budget range?",
            "cost": "What is your current average cost to acquire one customer, if known?",
            "goal": "What is your top business plan or goal for the next 12 months?",
        }
        return {
            "question_text": mapping[topic],
            "question_type": "open_ended",
            "question_options": [],
            "topic": topic,
        }

    return {
        "question_text": "What is the biggest barrier preventing faster growth right now?",
        "question_type": "open_ended",
        "question_options": [],
        "topic": "deep_dive",
    }


def generate_next_questions(responses: list[dict], max_questions: int = 3) -> list[str]:
    """Back-compat helper used in a few older call sites."""
    structured = generate_next_questions_structured(responses, max_questions=max_questions)
    return [q["question_text"] for q in structured]


def generate_next_questions_structured(
    responses: list[dict], max_questions: int = 3
) -> list[dict]:
    """Generate adaptive follow-up questions for questionnaire flow.

    Returns list of:
    {
      "question_text": str,
      "question_type": "open_ended" | "mcq",
      "question_options": [str, ...]
    }
    """
    if max_questions < 1:
        return []

    if not settings.can_use_openai():
        return _fallback_structured_questions(responses, max_questions)

    transcript = [
        {
            "question": r.get("question_text", ""),
            "answer": r.get("answer_text", ""),
            "question_type": r.get("question_type", "open_ended"),
        }
        for r in responses
    ]

    prompt = (
        "You are an onboarding interviewer for a marketing strategy product.\n"
        "Given the questionnaire transcript, generate exactly "
        f"{max_questions} high-value follow-up questions.\n"
        "Rules:\n"
        "- Include 1 multiple-choice question when useful, others can be open-ended.\n"
        "- Avoid repeating existing questions.\n"
        "- Prioritize customer segmentation, positioning, channel strategy, and profitability.\n"
        "- For mcq, include 3-5 concise options.\n"
        "- Return strict JSON only as:\n"
        "{\n"
        '  "questions": [\n'
        '    {"question_text":"...", "question_type":"open_ended", "question_options":[]},\n'
        '    {"question_text":"...", "question_type":"mcq", "question_options":["A","B","C"]}\n'
        "  ]\n"
        "}\n\n"
        f"Transcript:\n{json.dumps(transcript, ensure_ascii=True)}"
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
        raw = _response_to_text(resp)
        data = _extract_json_from_text(raw) or {}
        questions = data.get("questions", [])
        cleaned = []

        for item in questions:
            if not isinstance(item, dict):
                continue
            question_text = str(item.get("question_text", "")).strip()
            question_type = str(item.get("question_type", "open_ended")).strip().lower()
            options = item.get("question_options", [])
            if not question_text:
                continue
            if question_type not in {"open_ended", "mcq"}:
                question_type = "open_ended"
            if question_type == "mcq":
                if not isinstance(options, list):
                    options = []
                options = [str(o).strip() for o in options if str(o).strip()]
                if len(options) < 2:
                    question_type = "open_ended"
                    options = []
            else:
                options = []

            cleaned.append(
                {
                    "question_text": question_text,
                    "question_type": question_type,
                    "question_options": options[:5],
                }
            )

        if not cleaned:
            return _fallback_structured_questions(responses, max_questions)
        return cleaned[:max_questions]
    except Exception:
        return _fallback_structured_questions(responses, max_questions)


def generate_next_chat_question(responses: list[dict]) -> dict:
    """Generate exactly one adaptive chat follow-up question."""
    if not settings.can_use_openai():
        return _fallback_chat_question(responses)

    transcript = [
        {
            "question": r.get("question_text", ""),
            "answer": r.get("answer_text", ""),
        }
        for r in responses
        if (r.get("answer_text") or "").strip()
    ]
    asked_questions = [
        str(r.get("question_text", "")).strip()
        for r in responses
        if str(r.get("question_text", "")).strip()
    ]
    covered = sorted(_topic_coverage(responses))
    missing = [topic for topic in REQUIRED_CHAT_TOPICS if topic not in covered]

    prompt = (
        "You are an interactive business onboarding chatbot.\n"
        "Generate exactly one next question based on previous user answers.\n"
        "Requirements:\n"
        "- Question must be specific and non-repetitive.\n"
        "- Ask to fill missing topic coverage first, in this strict order:\n"
        "  1) business 2) customer 3) competitors 4) budget 5) cost 6) goal/plan.\n"
        "- Required topics: business, customer, competitors, budget, cost, goal/plan.\n"
        "- Do not repeat or paraphrase previously asked questions.\n"
        "- Keep question concise and practical.\n"
        "- Return strict JSON only:\n"
        '{"question_text":"...", "question_type":"open_ended", "question_options":[]}\n\n'
        f"Covered topics: {json.dumps(covered)}\n"
        f"Missing topics: {json.dumps(missing)}\n"
        f"Previously asked questions (avoid these): {json.dumps(asked_questions, ensure_ascii=True)}\n"
        f"Transcript:\n{json.dumps(transcript, ensure_ascii=True)}"
    )

    try:
        client = OpenAI(
            api_key=settings.openai_api_key,
            base_url=settings.openai_base_url,
            timeout=15,
            max_retries=0,
        )
        resp = client.responses.create(model=settings.openai_model, input=prompt)
        raw = _response_to_text(resp)
        parsed = _extract_json_from_text(raw) or {}
        question_text = str(parsed.get("question_text", "")).strip()
        if not question_text:
            return _fallback_chat_question(responses)
        return {
            "question_text": question_text,
            "question_type": "open_ended",
            "question_options": [],
            "topic": missing[0] if missing else "deep_dive",
        }
    except Exception:
        return _fallback_chat_question(responses)


def _fallback_marketing_analysis(
    responses: list[dict], business_context: dict | None = None
) -> dict:
    business_context = business_context or {}
    business_location = str(business_context.get("business_location") or "").strip()
    if not responses:
        return {
            "summary": "No answers yet. Ask foundational business questions first.",
            "important_points": [],
            "analysis_source": "fallback",
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "business_location": business_location or "Not provided",
            "understanding": {
                "business_model": "unknown",
                "target_customer": "unknown",
                "competitors": "unknown",
                "budget": "unknown",
                "cost_structure": "unknown",
                "goal": "unknown",
            },
            "marketing_insights": [
                "Start with offer clarity, ideal customer profile, and growth objective."
            ],
            "confidence": "low",
        }

    text = " ".join(
        f"{r.get('question_text', '')} {r.get('answer_text', '')}" for r in responses
    ).lower()
    understanding = {
        "business_model": "defined" if any(k in text for k in ["service", "product", "offer"]) else "partial",
        "target_customer": "defined" if any(k in text for k in ["customer", "audience", "buyer"]) else "partial",
        "competitors": "defined" if any(k in text for k in ["competitor", "competition", "alternative"]) else "partial",
        "budget": "defined" if any(k in text for k in ["budget", "spend"]) else "missing",
        "cost_structure": "defined" if any(k in text for k in ["cost", "cac", "expense"]) else "missing",
        "goal": "defined" if any(k in text for k in ["goal", "objective", "target", "plan"]) else "partial",
    }
    marketing_insights = []
    if understanding["target_customer"] != "defined":
        marketing_insights.append("Clarify target customer segment to avoid generic messaging.")
    if understanding["competitors"] != "defined":
        marketing_insights.append("Capture competitor landscape to sharpen positioning.")
    if understanding["budget"] == "missing":
        marketing_insights.append("Budget is missing; channel strategy cannot be prioritized yet.")
    if understanding["goal"] != "defined":
        marketing_insights.append("Set a measurable 12-month goal for campaign direction.")
    if business_location:
        marketing_insights.append(
            "Use location-specific messaging and local SEO to improve qualified lead capture."
        )
    if not marketing_insights:
        marketing_insights.append("Profile quality is strong enough for segmentation and strategy modeling.")

    known_count = sum(1 for v in understanding.values() if v == "defined")
    confidence = "high" if known_count >= 5 else "medium" if known_count >= 3 else "low"
    important_points = _derive_important_points(responses, max_points=5)

    insights = marketing_insights[:4]
    evidence = _build_insight_evidence(insights, important_points)
    for item in evidence:
        item["evidence_items"] = _build_evidence_items(responses, item["insight"], max_items=2)

    return {
        "summary": "Current business profile has been analyzed for marketing readiness.",
        "important_points": important_points,
        "analysis_source": "fallback",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "business_location": business_location or "Not provided",
        "understanding": understanding,
        "marketing_insights": insights,
        "insight_evidence": evidence,
        "confidence": confidence,
    }


def analyze_chat_response(
    responses: list[dict], business_context: dict | None = None
) -> dict:
    """Generate structured marketing analysis from cumulative interview answers."""
    business_context = business_context or {}
    business_location = str(business_context.get("business_location") or "").strip()
    if not settings.can_use_openai():
        fallback = _fallback_marketing_analysis(
            responses, business_context=business_context
        )
        fallback["fallback_reason"] = "openai_unavailable"
        return fallback

    transcript = [
        {
            "question": r.get("question_text", ""),
            "answer": r.get("answer_text", ""),
        }
        for r in responses
        if (r.get("answer_text") or "").strip()
    ]

    if not transcript:
        return _fallback_marketing_analysis(responses, business_context=business_context)

    prompt = (
        "You are a senior marketing strategy panel.\n"
        "Analyze the interview transcript and return strict JSON only.\n"
        "Focus on: business clarity, customer clarity, competitor intelligence, budget/cost signals, and growth plan quality.\n"
        "Important: important_points must be concise fact bullets, not copied full answers.\n"
        "Each point must be max 20 words and start with a topic tag (Business/Customer/Competitors/Budget/Cost/Goal).\n"
        "Return JSON shape:\n"
        "{\n"
        '  "summary": "short paragraph",\n'
        '  "important_points": ["short point", "short point"],\n'
        '  "business_location": "location text",\n'
        '  "understanding": {\n'
        '    "business_model": "missing|partial|defined",\n'
        '    "target_customer": "missing|partial|defined",\n'
        '    "competitors": "missing|partial|defined",\n'
        '    "budget": "missing|partial|defined",\n'
        '    "cost_structure": "missing|partial|defined",\n'
        '    "goal": "missing|partial|defined"\n'
        "  },\n"
        '  "marketing_insights": ["...", "...", "..."],\n'
        '  "confidence": "low|medium|high"\n'
        "}\n\n"
        f"Business context:\n{json.dumps({'business_location': business_location}, ensure_ascii=True)}\n"
        f"Transcript:\n{json.dumps(transcript, ensure_ascii=True)}"
    )

    try:
        client = OpenAI(
            api_key=settings.openai_api_key,
            base_url=settings.openai_base_url,
            timeout=15,
            max_retries=0,
        )
        resp = client.responses.create(model=settings.openai_model, input=prompt)
        raw = _response_to_text(resp)
        data = _extract_json_from_text(raw)
        if not isinstance(data, dict):
            return _fallback_marketing_analysis(
                responses, business_context=business_context
            )

        understanding = data.get("understanding", {})
        if not isinstance(understanding, dict):
            understanding = {}
        normalized = {}
        for key in ["business_model", "target_customer", "competitors", "budget", "cost_structure", "goal"]:
            raw = str(understanding.get(key, "missing")).strip().lower()
            normalized[key] = raw if raw in {"missing", "partial", "defined"} else "missing"

        insights = data.get("marketing_insights", [])
        if not isinstance(insights, list):
            insights = []
        insights = [str(x).strip() for x in insights if str(x).strip()][:4]

        confidence = str(data.get("confidence", "medium")).strip().lower()
        if confidence not in {"low", "medium", "high"}:
            confidence = "medium"

        summary = str(data.get("summary", "")).strip() or "Interview responses analyzed for marketing readiness."
        important_points = data.get("important_points", [])
        if not isinstance(important_points, list):
            important_points = []
        important_points = [str(x).strip().replace("\n", " ") for x in important_points if str(x).strip()]
        # If model returns verbose/raw text, replace with deterministic concise points.
        if not important_points or any(len(p.split()) > 18 for p in important_points):
            important_points = _derive_important_points(responses, max_points=5)
        else:
            important_points = _dedupe_points_semantic(important_points, max_points=5)
            if not important_points:
                important_points = _derive_important_points(responses, max_points=5)

        fallback_ref = _fallback_marketing_analysis(
            responses, business_context=business_context
        )
        final_insights = insights or fallback_ref["marketing_insights"]
        evidence = _build_insight_evidence(final_insights, important_points)
        for item in evidence:
            item["evidence_items"] = _build_evidence_items(responses, item["insight"], max_items=2)

        return {
            "summary": summary,
            "important_points": important_points,
            "analysis_source": "ai",
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "business_location": business_location
            or str(data.get("business_location") or "").strip()
            or "Not provided",
            "understanding": normalized,
            "marketing_insights": final_insights,
            "insight_evidence": evidence,
            "confidence": confidence,
        }
    except Exception as exc:
        fallback = _fallback_marketing_analysis(
            responses, business_context=business_context
        )
        fallback["fallback_reason"] = str(exc)[:120]
        return fallback
