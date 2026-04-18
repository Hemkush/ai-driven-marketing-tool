"""
Prompt Token Budget Enforcer

Estimates token count (4 chars ≈ 1 token) and trims content to stay
within a per-agent budget. Logs a warning when truncation occurs.

Usage:
    from app.core.token_budget import enforce_budget, trim_list, trim_str

    # Trim a string field to a token limit
    context = trim_str(json.dumps(big_dict), max_tokens=1500, label="analysis_report")

    # Trim a list to keep only first N items worth of tokens
    snippets = trim_list(memory_chunks, max_tokens=600, label="memory_chunks")
"""

import json
import logging
from typing import Any

logger = logging.getLogger(__name__)

# Per-agent prompt token budgets (approximate — 4 chars ≈ 1 token)
BUDGETS: dict[str, int] = {
    "segment_analyst":          3000,
    "segment_analyst_chat":     2000,
    "competitive_benchmarker":  3500,
    "positioning_copilot":      2000,
    "persona_builder":          2500,
    "market_researcher":        2000,
    "channel_strategy_planner": 2000,
    "roadmap_planner":          2000,
    "onboarding_interviewer":   1500,
    "content_studio":           1500,
    "memory_context":            600,
    "chat_history":              400,
}


def _estimate_tokens(text: str) -> int:
    return max(1, len(text) // 4)


def trim_str(text: str, max_tokens: int, label: str = "") -> str:
    """Trim a string to max_tokens. Logs a warning if truncation occurs."""
    max_chars = max_tokens * 4
    if len(text) <= max_chars:
        return text
    trimmed = text[:max_chars]
    logger.warning(
        "token_budget_exceeded",
        extra={
            "label":           label,
            "original_tokens": _estimate_tokens(text),
            "max_tokens":      max_tokens,
            "action":          "truncated",
        },
    )
    return trimmed


def trim_list(items: list[Any], max_tokens: int, label: str = "") -> list[Any]:
    """Keep as many list items as fit within max_tokens (serialised)."""
    result = []
    used = 0
    for item in items:
        serialised = json.dumps(item, default=str)
        cost = _estimate_tokens(serialised)
        if used + cost > max_tokens:
            logger.warning(
                "token_budget_exceeded",
                extra={
                    "label":      label,
                    "kept_items": len(result),
                    "total_items": len(items),
                    "max_tokens": max_tokens,
                    "action":     "list_truncated",
                },
            )
            break
        result.append(item)
        used += cost
    return result


def get_budget(agent: str) -> int:
    return BUDGETS.get(agent, 2000)
