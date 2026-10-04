"""Structured application logging.

Emits one JSON object per line with at least: timestamp, level, logger,
message, and request_id (when inside an HTTP request). Never logs secrets:
callers must not pass passwords, tokens, or database credentials.
"""

from __future__ import annotations

import contextvars
import json
import logging
import sys
import uuid
from datetime import UTC, datetime

_request_id: contextvars.ContextVar[str] = contextvars.ContextVar("request_id", default="-")


def get_request_id() -> str:
    return _request_id.get()


def set_request_id(value: str | None = None) -> str:
    rid = value or uuid.uuid4().hex[:12]
    _request_id.set(rid)
    return rid


def clear_request_id() -> None:
    _request_id.set("-")


class JsonFormatter(logging.Formatter):
    def format(self, record: logging.Record) -> str:
        payload = {
            "timestamp": datetime.now(UTC).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "request_id": _request_id.get(),
        }
        if record.exc_info and record.exc_info[0] is not None:
            payload["exc_info"] = self.formatException(record.exc_info)
        return json.dumps(payload)


_configured = False


def setup_logging(level: str = "INFO") -> None:
    """Configure root logging once. Safe to call multiple times."""
    global _configured
    if _configured:
        logging.getLogger().setLevel(level.upper())
        return
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(JsonFormatter())
    root = logging.getLogger()
    root.handlers.clear()
    root.addHandler(handler)
    root.setLevel(level.upper())
    # Quiet noisy third-party loggers one notch unless debugging.
    if level.upper() != "DEBUG":
        logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    _configured = True


def get_logger(name: str) -> logging.Logger:
    return logging.getLogger(name)
