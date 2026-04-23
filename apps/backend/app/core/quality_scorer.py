"""
LLM Output Quality Scorer

Validates LLM outputs for schema completeness, field sanity, and length.
Emits one structured log line per scored output — no exceptions raised.

Usage:
    from app.core.quality_scorer import score_output

    parsed = ...  # dict from LLM
    score_output("segment_analyst", parsed, required_keys=[
        "segment_attractiveness_analysis", "deep_market_analysis", "unit_economics"
    ])

Log output:
    {
      "severity": "INFO",          # WARNING when score < 0.7
      "message": "llm_quality",
      "agent": "segment_analyst",
      "score": 0.83,
      "checks_passed": 5,
      "checks_total": 6,
      "failed_checks": ["unit_economics.cac is missing"],
      "output_length": 3241
    }
"""

import logging
from typing import Any

from app.core.metrics import record_llm_quality

logger = logging.getLogger(__name__)


def _check_required_keys(output: dict, keys: list[str]) -> list[str]:
    """Returns list of missing top-level keys."""
    return [k for k in keys if k not in output or output[k] is None]


def _check_non_empty_lists(output: dict, list_keys: list[str]) -> list[str]:
    """Returns list of keys that are empty lists or non-lists."""
    failed = []
    for k in list_keys:
        val = output.get(k)
        if not isinstance(val, list) or len(val) == 0:
            failed.append(f"{k} is empty or not a list")
    return failed


def _check_nested_keys(output: dict, path: str) -> list[str]:
    """
    Checks a dot-separated path exists and is non-None.
    e.g. path="unit_economics.cac" checks output["unit_economics"]["cac"]
    """
    parts = path.split(".")
    node: Any = output
    for part in parts:
        if not isinstance(node, dict) or part not in node:
            return [f"{path} is missing"]
        node = node[part]
    if node is None or node == "" or node == []:
        return [f"{path} is empty"]
    return []


def _check_score_range(output: dict, score_keys: list[str], lo: int = 1, hi: int = 10) -> list[str]:
    """Returns failed checks for scores outside [lo, hi]."""
    failed = []
    for k in score_keys:
        val = output.get(k)
        if val is not None:
            try:
                v = float(val)
                if not (lo <= v <= hi):
                    failed.append(f"{k}={v} out of range [{lo},{hi}]")
            except (TypeError, ValueError):
                failed.append(f"{k} is not a number")
    return failed


def score_output(
    agent: str,
    output: dict,
    required_keys: list[str] | None = None,
    list_keys: list[str] | None = None,
    nested_keys: list[str] | None = None,
    score_keys: list[str] | None = None,
    min_length: int = 50,
) -> float:
    """
    Score an LLM output dict. Returns float 0.0–1.0.
    Emits a structured log line regardless of score.
    """
    if not isinstance(output, dict):
        logger.warning(
            "llm_quality",
            extra={"agent": agent, "score": 0.0, "failed_checks": ["output is not a dict"],
                   "checks_passed": 0, "checks_total": 1, "output_length": 0},
        )
        return 0.0

    failed: list[str] = []
    total_checks = 0

    # 1. Required top-level keys
    if required_keys:
        total_checks += len(required_keys)
        failed += _check_required_keys(output, required_keys)

    # 2. Non-empty list fields
    if list_keys:
        total_checks += len(list_keys)
        failed += _check_non_empty_lists(output, list_keys)

    # 3. Nested key paths
    if nested_keys:
        total_checks += len(nested_keys)
        for path in nested_keys:
            failed += _check_nested_keys(output, path)

    # 4. Numeric score range checks
    if score_keys:
        total_checks += len(score_keys)
        failed += _check_score_range(output, score_keys)

    # 5. Minimum output length (serialised)
    total_checks += 1
    import json
    output_len = len(json.dumps(output, default=str))
    if output_len < min_length:
        failed.append(f"output too short ({output_len} chars < {min_length})")

    passed = total_checks - len(failed)
    score = round(passed / total_checks, 3) if total_checks > 0 else 0.0

    level = logging.WARNING if score < 0.7 else logging.INFO
    logger.log(
        level,
        "llm_quality",
        extra={
            "agent":          agent,
            "score":          score,
            "checks_passed":  passed,
            "checks_total":   total_checks,
            "failed_checks":  failed,
            "output_length":  output_len,
        },
    )
    record_llm_quality(agent=agent, score=score)
    return score


# ── Per-agent convenience wrappers ────────────────────────────────────────────

def score_segment_analysis(output: dict) -> float:
    return score_output(
        agent="segment_analyst",
        output=output,
        required_keys=[
            "segment_attractiveness_analysis",
            "deep_market_analysis",
            "unit_economics",
            "channel_mix_efficiency",
            "growth_scenarios",
            "risk_register",
            "executive_actions",
        ],
        list_keys=["growth_scenarios", "risk_register", "executive_actions"],
        nested_keys=["unit_economics.estimated_cac", "unit_economics.estimated_ltv"],
        min_length=500,
    )


def score_competitive_benchmarking(output: dict) -> float:
    return score_output(
        agent="competitive_benchmarker",
        output=output,
        required_keys=["competitors", "market_overview", "swot_analysis", "hours_gap_analysis"],
        list_keys=["competitors"],
        nested_keys=[
            "market_overview.opportunity_gaps",
            "market_overview.win_strategies",
            "swot_analysis.strengths",
            "swot_analysis.opportunities",
        ],
        min_length=300,
    )


def score_positioning(output: dict) -> float:
    return score_output(
        agent="positioning_copilot",
        output=output,
        required_keys=[
            "target_segment", "positioning_statement",
            "key_differentiators", "proof_points", "tagline",
        ],
        list_keys=["key_differentiators", "proof_points"],
        min_length=100,
    )


def score_personas(personas: list) -> float:
    """Score a list of persona dicts."""
    if not isinstance(personas, list) or len(personas) == 0:
        logger.warning("llm_quality", extra={
            "agent": "persona_builder", "score": 0.0,
            "failed_checks": ["personas list is empty"],
            "checks_passed": 0, "checks_total": 1, "output_length": 0,
        })
        return 0.0
    scores = []
    for i, p in enumerate(personas):
        scores.append(score_output(
            agent=f"persona_builder[{i}]",
            output=p if isinstance(p, dict) else {},
            required_keys=["name", "basic_profile", "psychographic_profile",
                           "behavioral_profile", "engagement_strategy"],
            min_length=100,
        ))
    return round(sum(scores) / len(scores), 3)


def score_roadmap(output: dict) -> float:
    return score_output(
        agent="roadmap_planner",
        output=output,
        required_keys=["project_name", "weeks", "milestones"],
        list_keys=["weeks", "milestones"],
        min_length=300,
    )


def score_content(assets: list) -> float:
    """Score a list of generated content assets."""
    if not isinstance(assets, list) or len(assets) == 0:
        logger.warning("llm_quality", extra={
            "agent": "content_studio", "score": 0.0,
            "failed_checks": ["assets list is empty"],
            "checks_passed": 0, "checks_total": 1, "output_length": 0,
        })
        return 0.0
    scores = []
    for i, a in enumerate(assets):
        scores.append(score_output(
            agent=f"content_studio[{i}]",
            output=a if isinstance(a, dict) else {},
            required_keys=["asset_type", "metadata", "status"],
            nested_keys=["metadata"],
            min_length=50,
        ))
    return round(sum(scores) / len(scores), 3)
