"""
Pipeline Step Tracer

Records every agent invocation to the `pipeline_runs` table and emits
a structured log line + Prometheus metric.

Usage (in API endpoints):
    from app.core.pipeline_tracer import trace_step

    with trace_step(db, step="competitive_benchmarker", project_id=project.id):
        result = run_competitive_benchmarking(...)

    # With extra metadata:
    with trace_step(db, step="persona_builder", project_id=project.id,
                    extra={"source": "cached"}):
        ...

If the block raises an exception, status is set to "error" and error_msg captured.
The exception is always re-raised so normal error handling still works.
"""

import json
import logging
from contextlib import contextmanager
from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.core.metrics import record_pipeline_step
from app.models import PipelineRun

logger = logging.getLogger(__name__)


@contextmanager
def trace_step(
    db: Session,
    step: str,
    project_id: int | None = None,
    extra: dict | None = None,
):
    started_at = datetime.now(timezone.utc)
    run = PipelineRun(
        project_id=project_id,
        step=step,
        status="running",
        started_at=started_at,
        extra_json=json.dumps(extra or {}, default=str),
    )
    try:
        db.add(run)
        db.flush()   # get run.id without committing outer transaction
    except Exception:
        db.rollback()
        run = None   # don't block the pipeline over tracing failures

    status = "success"
    error_msg = None
    try:
        yield
    except Exception as exc:
        status = "error"
        error_msg = str(exc)
        raise
    finally:
        completed_at = datetime.now(timezone.utc)
        duration_ms = int((completed_at - started_at).total_seconds() * 1000)

        logger.info(
            "pipeline_step",
            extra={
                "step": step,
                "project_id": project_id,
                "status": status,
                "duration_ms": duration_ms,
                "error_msg": error_msg,
            },
        )
        record_pipeline_step(step=step, status=status,
                             duration_seconds=duration_ms / 1000)

        if run is not None:
            try:
                run.status = status
                run.completed_at = completed_at
                run.duration_ms = duration_ms
                run.error_msg = error_msg
                db.commit()
            except Exception as db_exc:
                logger.error("pipeline_tracer_db_error", extra={"error": str(db_exc)})
                db.rollback()
