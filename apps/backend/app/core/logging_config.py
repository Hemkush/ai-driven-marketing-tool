"""
Structured JSON logging for Cloud Run / Google Cloud Logging.

Google Cloud Logging parses JSON log lines and maps:
  - "severity"  → log severity (INFO, WARNING, ERROR, CRITICAL)
  - "message"   → the main log message
  - "timestamp" → log timestamp (auto-set by GCL if omitted)
  - Any extra keys → indexed as jsonPayload fields, searchable in Log Explorer

Usage:
    from app.core.logging_config import setup_logging
    setup_logging()   # call once at app startup

    import logging
    logger = logging.getLogger(__name__)
    logger.info("Embedding created", extra={"agent": "memory_store", "chunks": 4})
"""

import json
import logging
import sys
import os
from datetime import datetime, timezone


class _JsonFormatter(logging.Formatter):
    """Formats log records as single-line JSON for Cloud Run stdout ingestion."""

    # Map Python log level names to Google Cloud Logging severity strings
    _SEVERITY = {
        "DEBUG":    "DEBUG",
        "INFO":     "INFO",
        "WARNING":  "WARNING",
        "ERROR":    "ERROR",
        "CRITICAL": "CRITICAL",
    }

    def format(self, record: logging.LogRecord) -> str:
        payload: dict = {
            "severity": self._SEVERITY.get(record.levelname, "DEFAULT"),
            "message":  record.getMessage(),
            "logger":   record.name,
            "time":     datetime.now(timezone.utc).isoformat(),
        }

        # Include any extra= fields passed by the caller
        _skip = {
            "args", "created", "exc_info", "exc_text", "filename", "funcName",
            "levelname", "levelno", "lineno", "message", "module", "msecs",
            "msg", "name", "pathname", "process", "processName",
            "relativeCreated", "stack_info", "taskName", "thread", "threadName",
        }
        for key, value in record.__dict__.items():
            if key not in _skip and not key.startswith("_"):
                payload[key] = value

        # Attach exception info when present
        if record.exc_info:
            payload["exception"] = self.formatException(record.exc_info)

        return json.dumps(payload, default=str)


def setup_logging(level: str | None = None) -> None:
    """
    Configure root logger with JSON output.
    Call once at application startup (before any logger is used).
    """
    log_level = level or os.getenv("LOG_LEVEL", "INFO").upper()

    root = logging.getLogger()
    root.setLevel(log_level)

    # Remove any existing handlers (e.g. uvicorn default)
    root.handlers.clear()

    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(_JsonFormatter())
    root.addHandler(handler)

    # Silence noisy third-party loggers
    for noisy in ("uvicorn.access", "httpx", "httpcore"):
        logging.getLogger(noisy).setLevel(logging.WARNING)
