"""
Custom Prometheus Metrics for MarketPilot AI

Exposes AI-specific metrics beyond what prometheus_fastapi_instrumentator provides.
All metrics are available at GET /metrics (already wired in main.py via Instrumentator).

Metrics defined here:
  llm_calls_total{agent, model, call_type, status}     - Counter
  llm_latency_seconds{agent, call_type}                - Histogram
  llm_tokens_total{agent, token_type}                  - Counter (prompt / completion)
  llm_cost_usd_total{agent}                            - Counter
  llm_quality_score{agent}                             - Histogram
  pipeline_step_duration_seconds{step, status}         - Histogram
  cache_operations_total{operation, agent}             - Counter (hit/miss/set/expired)
  embedding_calls_total{agent, status}                 - Counter

Usage (in llm_tracker.py and response_cache.py — already done below):
    from app.core.metrics import (
        record_llm_call, record_llm_quality, record_pipeline_step, record_cache_op
    )
"""

from prometheus_client import Counter, Histogram

# ── LLM Call Counters ─────────────────────────────────────────────────────────

LLM_CALLS = Counter(
    "llm_calls_total",
    "Total number of LLM API calls",
    ["agent", "model", "call_type", "status"],  # status: success | error
)

LLM_TOKENS = Counter(
    "llm_tokens_total",
    "Total tokens consumed by LLM calls",
    ["agent", "token_type"],  # token_type: prompt | completion
)

LLM_COST = Counter(
    "llm_cost_usd_total",
    "Estimated total cost of LLM calls in USD",
    ["agent"],
)

# ── LLM Latency Histogram ─────────────────────────────────────────────────────

LLM_LATENCY = Histogram(
    "llm_latency_seconds",
    "LLM API call latency in seconds",
    ["agent", "call_type"],
    buckets=[0.5, 1.0, 2.0, 5.0, 10.0, 20.0, 30.0, 60.0, 120.0],
)

# ── Quality Score Histogram ───────────────────────────────────────────────────

LLM_QUALITY = Histogram(
    "llm_quality_score",
    "LLM output quality score (0.0 to 1.0)",
    ["agent"],
    buckets=[0.0, 0.3, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0],
)

# ── Pipeline Step Histogram ───────────────────────────────────────────────────

PIPELINE_STEP = Histogram(
    "pipeline_step_duration_seconds",
    "Duration of each pipeline step",
    ["step", "status"],  # status: success | error | cached
    buckets=[0.1, 0.5, 1.0, 5.0, 10.0, 30.0, 60.0, 120.0],
)

# ── Cache Operations Counter ──────────────────────────────────────────────────

CACHE_OPS = Counter(
    "cache_operations_total",
    "Cache operation counts",
    ["operation", "agent"],  # operation: hit | miss | set | expired | error
)

# ── Embedding Calls Counter ───────────────────────────────────────────────────

EMBEDDING_CALLS = Counter(
    "embedding_calls_total",
    "Total embedding API calls",
    ["agent", "status"],
)


# ── Convenience helpers ───────────────────────────────────────────────────────

def record_llm_call(
    agent: str,
    model: str,
    call_type: str,
    status: str,
    latency_ms: float,
    prompt_tokens: int = 0,
    completion_tokens: int = 0,
    cost_usd: float = 0.0,
) -> None:
    LLM_CALLS.labels(agent=agent, model=model, call_type=call_type, status=status).inc()
    LLM_LATENCY.labels(agent=agent, call_type=call_type).observe(latency_ms / 1000)
    if prompt_tokens:
        LLM_TOKENS.labels(agent=agent, token_type="prompt").inc(prompt_tokens)
    if completion_tokens:
        LLM_TOKENS.labels(agent=agent, token_type="completion").inc(completion_tokens)
    if cost_usd:
        LLM_COST.labels(agent=agent).inc(cost_usd)
    if call_type == "embedding":
        EMBEDDING_CALLS.labels(agent=agent, status=status).inc()


def record_llm_quality(agent: str, score: float) -> None:
    LLM_QUALITY.labels(agent=agent).observe(score)


def record_pipeline_step(step: str, status: str, duration_seconds: float) -> None:
    PIPELINE_STEP.labels(step=step, status=status).observe(duration_seconds)


def record_cache_op(operation: str, agent: str) -> None:
    CACHE_OPS.labels(operation=operation, agent=agent).inc()
