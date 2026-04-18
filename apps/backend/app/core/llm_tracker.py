"""
LLM Call Tracker — wraps every OpenAI API call to log tokens, cost, and latency.

Usage (drop-in replacement at each call site):

    from app.core.llm_tracker import tracked_responses, tracked_chat, tracked_embeddings, tracked_image

    # Instead of:  resp = client.responses.create(model=..., input=prompt)
    resp = tracked_responses(client, agent="onboarding_interviewer", model=..., input=prompt)

    # Instead of:  resp = client.chat.completions.create(model=..., messages=...)
    resp = tracked_chat(client, agent="competitive_benchmarker", model=..., messages=...)

    # Instead of:  resp = client.embeddings.create(model=..., input=texts)
    resp = tracked_embeddings(client, agent="memory_store", model=..., input=texts)

    # Instead of:  resp = client.images.generate(model="dall-e-3", prompt=..., ...)
    resp = tracked_image(client, agent="content_studio", model="dall-e-3", prompt=..., ...)

Each call emits one structured log line:
    {
      "severity": "INFO",
      "message": "llm_call",
      "agent": "competitive_benchmarker",
      "call_type": "chat",
      "model": "gpt-4o-mini",
      "prompt_tokens": 842,
      "completion_tokens": 310,
      "total_tokens": 1152,
      "estimated_cost_usd": 0.000312,
      "latency_ms": 3420,
      "status": "success"          # or "error"
    }
"""

import logging
import time
from typing import Any

from app.core.metrics import record_llm_call

logger = logging.getLogger(__name__)

# ── Cost table (USD per token, as of 2025) ────────────────────────────────────
# Update these when OpenAI changes pricing.
_COST_INPUT: dict[str, float] = {
    "gpt-4o-mini":              0.15  / 1_000_000,
    "gpt-4o":                   2.50  / 1_000_000,
    "gpt-4-turbo":              10.0  / 1_000_000,
    "text-embedding-3-small":   0.02  / 1_000_000,
    "text-embedding-3-large":   0.13  / 1_000_000,
    "dall-e-3":                 0.0,   # charged per image, not tokens
}
_COST_OUTPUT: dict[str, float] = {
    "gpt-4o-mini":              0.60  / 1_000_000,
    "gpt-4o":                   10.0  / 1_000_000,
    "gpt-4-turbo":              30.0  / 1_000_000,
    "text-embedding-3-small":   0.0,
    "text-embedding-3-large":   0.0,
    "dall-e-3":                 0.0,
}
# DALL-E 3 standard 1024×1024 = $0.04/image
_COST_IMAGE: dict[str, float] = {
    "dall-e-3": 0.04,
    "dall-e-2": 0.02,
}


def _cost(model: str, prompt_tokens: int, completion_tokens: int) -> float:
    base = model.split(":")[0]   # strip fine-tune suffix if any
    in_rate  = _COST_INPUT.get(base,  _COST_INPUT.get("gpt-4o-mini",  0.0))
    out_rate = _COST_OUTPUT.get(base, _COST_OUTPUT.get("gpt-4o-mini", 0.0))
    return round(prompt_tokens * in_rate + completion_tokens * out_rate, 8)


def _log(agent: str, call_type: str, model: str,
         prompt_tokens: int, completion_tokens: int,
         latency_ms: float, status: str, error: str | None = None) -> None:
    total = prompt_tokens + completion_tokens
    cost  = _cost(model, prompt_tokens, completion_tokens)
    extra: dict[str, Any] = {
        "agent":               agent,
        "call_type":           call_type,
        "model":               model,
        "prompt_tokens":       prompt_tokens,
        "completion_tokens":   completion_tokens,
        "total_tokens":        total,
        "estimated_cost_usd":  cost,
        "latency_ms":          latency_ms,
        "status":              status,
    }
    if error:
        extra["error"] = error
    level = logging.ERROR if status == "error" else logging.INFO
    logger.log(level, "llm_call", extra=extra)
    # Emit Prometheus metrics
    record_llm_call(
        agent=agent, model=model, call_type=call_type, status=status,
        latency_ms=latency_ms, prompt_tokens=prompt_tokens,
        completion_tokens=completion_tokens, cost_usd=cost,
    )


# ── Wrapper: Responses API (client.responses.create) ─────────────────────────

def tracked_responses(client: Any, agent: str, **kwargs: Any) -> Any:
    """Wraps client.responses.create() with token + latency logging."""
    model = kwargs.get("model", "unknown")
    t0 = time.perf_counter()
    try:
        resp = client.responses.create(**kwargs)
        latency_ms = round((time.perf_counter() - t0) * 1000, 1)
        usage = getattr(resp, "usage", None)
        prompt_tokens     = getattr(usage, "input_tokens",  0) if usage else 0
        completion_tokens = getattr(usage, "output_tokens", 0) if usage else 0
        _log(agent, "responses", model, prompt_tokens, completion_tokens, latency_ms, "success")
        return resp
    except Exception as exc:
        latency_ms = round((time.perf_counter() - t0) * 1000, 1)
        _log(agent, "responses", model, 0, 0, latency_ms, "error", str(exc))
        raise


# ── Wrapper: Chat Completions API (client.chat.completions.create) ────────────

def tracked_chat(client: Any, agent: str, **kwargs: Any) -> Any:
    """Wraps client.chat.completions.create() with token + latency logging."""
    model = kwargs.get("model", "unknown")
    t0 = time.perf_counter()
    try:
        resp = client.chat.completions.create(**kwargs)
        latency_ms = round((time.perf_counter() - t0) * 1000, 1)
        usage = getattr(resp, "usage", None)
        prompt_tokens     = getattr(usage, "prompt_tokens",     0) if usage else 0
        completion_tokens = getattr(usage, "completion_tokens", 0) if usage else 0
        _log(agent, "chat", model, prompt_tokens, completion_tokens, latency_ms, "success")
        return resp
    except Exception as exc:
        latency_ms = round((time.perf_counter() - t0) * 1000, 1)
        _log(agent, "chat", model, 0, 0, latency_ms, "error", str(exc))
        raise


# ── Wrapper: Embeddings API (client.embeddings.create) ───────────────────────

def tracked_embeddings(client: Any, agent: str, **kwargs: Any) -> Any:
    """Wraps client.embeddings.create() with token + latency logging."""
    model = kwargs.get("model", "unknown")
    t0 = time.perf_counter()
    try:
        resp = client.embeddings.create(**kwargs)
        latency_ms = round((time.perf_counter() - t0) * 1000, 1)
        usage = getattr(resp, "usage", None)
        prompt_tokens = getattr(usage, "total_tokens", 0) if usage else 0
        _log(agent, "embedding", model, prompt_tokens, 0, latency_ms, "success")
        return resp
    except Exception as exc:
        latency_ms = round((time.perf_counter() - t0) * 1000, 1)
        _log(agent, "embedding", model, 0, 0, latency_ms, "error", str(exc))
        raise


# ── Wrapper: Images API (client.images.generate) ─────────────────────────────

def tracked_image(client: Any, agent: str, **kwargs: Any) -> Any:
    """Wraps client.images.generate() with per-image cost + latency logging."""
    model = kwargs.get("model", "dall-e-3")
    n     = kwargs.get("n", 1)
    t0 = time.perf_counter()
    try:
        resp = client.images.generate(**kwargs)
        latency_ms = round((time.perf_counter() - t0) * 1000, 1)
        cost = round(_COST_IMAGE.get(model, 0.04) * n, 6)
        logger.info(
            "llm_call",
            extra={
                "agent":              agent,
                "call_type":          "image",
                "model":              model,
                "images_generated":   n,
                "estimated_cost_usd": cost,
                "latency_ms":         latency_ms,
                "status":             "success",
            },
        )
        return resp
    except Exception as exc:
        latency_ms = round((time.perf_counter() - t0) * 1000, 1)
        logger.error(
            "llm_call",
            extra={
                "agent":      agent,
                "call_type":  "image",
                "model":      model,
                "latency_ms": latency_ms,
                "status":     "error",
                "error":      str(exc),
            },
        )
        raise
