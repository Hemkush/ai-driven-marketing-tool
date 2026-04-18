"""
DB-backed LLM Response Cache

Stores expensive LLM/API call results in the `llm_cache` table keyed by a
SHA-256 hash of the agent name + canonical input. Avoids re-running costly
pipelines (Google Places + OpenAI enrichment) when inputs haven't changed.

Usage:
    from app.core.response_cache import get_cached, set_cached

    key = make_cache_key("competitive_benchmarker", {
        "address": project.business_address,
        "responses": response_payload,
    })

    cached = get_cached(db, key, ttl_hours=24)
    if cached is not None:
        return cached   # dict — skip LLM call entirely

    result = run_expensive_pipeline(...)
    set_cached(db, key, agent="competitive_benchmarker", payload=result)
    return result

TTL guidelines:
    - competitive_benchmarking : 24h  (Google Places data changes daily at most)
    - positioning / personas    :  6h  (cheap to regenerate, user may want fresh)
    - strategy / roadmap        : 12h  (depends on positioning + personas)
"""

import hashlib
import json
import logging
from datetime import datetime, timezone, timedelta

from sqlalchemy.orm import Session

from app.core.metrics import record_cache_op
from app.models import LLMCache

logger = logging.getLogger(__name__)


def make_cache_key(agent: str, inputs: dict) -> str:
    """
    Deterministic SHA-256 cache key from agent name + inputs dict.
    Sorts dict keys recursively so key order doesn't matter.
    """
    canonical = json.dumps({"agent": agent, "inputs": inputs}, sort_keys=True, default=str)
    return hashlib.sha256(canonical.encode()).hexdigest()


def get_cached(db: Session, cache_key: str, ttl_hours: int = 24) -> dict | None:
    """
    Return cached payload if it exists and is within TTL, else None.
    Logs a cache hit or miss.
    """
    row = db.query(LLMCache).filter(LLMCache.cache_key == cache_key).first()
    if row is None:
        logger.info("cache_miss", extra={"cache_key": cache_key[:12]})
        record_cache_op("miss", "unknown")
        return None

    age = datetime.now(timezone.utc) - row.created_at.replace(tzinfo=timezone.utc)
    if age > timedelta(hours=ttl_hours):
        logger.info("cache_expired", extra={
            "cache_key": cache_key[:12],
            "agent": row.agent,
            "age_hours": round(age.total_seconds() / 3600, 1),
        })
        record_cache_op("expired", row.agent)
        return None

    logger.info("cache_hit", extra={
        "cache_key": cache_key[:12],
        "agent": row.agent,
        "age_hours": round(age.total_seconds() / 3600, 1),
    })
    record_cache_op("hit", row.agent)
    try:
        return json.loads(row.payload_json)
    except Exception as exc:
        logger.error("cache_deserialize_error", extra={"error": str(exc)})
        return None


def set_cached(db: Session, cache_key: str, agent: str, payload: dict) -> None:
    """
    Upsert a cache entry. If the key already exists, update payload + timestamp.
    """
    try:
        row = db.query(LLMCache).filter(LLMCache.cache_key == cache_key).first()
        if row:
            row.payload_json = json.dumps(payload, default=str)
            row.created_at = datetime.now(timezone.utc)
        else:
            row = LLMCache(
                cache_key=cache_key,
                agent=agent,
                payload_json=json.dumps(payload, default=str),
            )
            db.add(row)
        db.commit()
        logger.info("cache_set", extra={"cache_key": cache_key[:12], "agent": agent})
        record_cache_op("set", agent)
    except Exception as exc:
        logger.error("cache_set_error", extra={"agent": agent, "error": str(exc)})
        record_cache_op("error", agent)
        db.rollback()


def invalidate_cached(db: Session, cache_key: str) -> None:
    """Delete a specific cache entry (e.g. after user edits interview answers)."""
    try:
        db.query(LLMCache).filter(LLMCache.cache_key == cache_key).delete()
        db.commit()
        logger.info("cache_invalidated", extra={"cache_key": cache_key[:12]})
    except Exception as exc:
        logger.error("cache_invalidate_error", extra={"error": str(exc)})
        db.rollback()
