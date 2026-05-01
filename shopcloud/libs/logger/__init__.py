"""Structured JSON logger.

Every log line is a single JSON object with consistent keys.
This makes CloudWatch Insights queries actually work.

Usage:
    from libs.logger import get_logger, bind_request_context

    logger = get_logger(__name__)
    logger.info("order created", extra={"order_id": "abc-123"})
"""
import json
import logging
import sys
import time
from contextvars import ContextVar
from typing import Any

# Request-scoped context populated by middleware (request_id, user_id, etc.)
_request_context: ContextVar[dict[str, Any]] = ContextVar(
    "_request_context", default={}
)


def bind_request_context(**kwargs: Any) -> None:
    """Add fields that will appear on every log line for this request."""
    current = _request_context.get()
    _request_context.set({**current, **kwargs})


def clear_request_context() -> None:
    _request_context.set({})


# Service-level fields set once at startup
_service_context: dict[str, Any] = {}


def init_service_context(service: str, version: str, environment: str) -> None:
    """Call once at app startup. Adds service/version/env to every log line."""
    _service_context.update(
        {"service": service, "version": version, "environment": environment}
    )


class JsonFormatter(logging.Formatter):
    """Render LogRecord as a single-line JSON object."""

    # LogRecord attributes we don't want to duplicate in `extra`
    _RESERVED = {
        "name", "msg", "args", "levelname", "levelno", "pathname", "filename",
        "module", "exc_info", "exc_text", "stack_info", "lineno", "funcName",
        "created", "msecs", "relativeCreated", "thread", "threadName",
        "processName", "process", "message", "asctime", "taskName",
    }

    def format(self, record: logging.LogRecord) -> str:
        payload: dict[str, Any] = {
            "timestamp": int(time.time() * 1000),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }

        # Attach service/version/environment
        payload.update(_service_context)

        # Attach per-request context (request_id, user_id, etc.)
        payload.update(_request_context.get())

        # Attach anything passed via `extra=`
        for key, value in record.__dict__.items():
            if key not in self._RESERVED and not key.startswith("_"):
                payload[key] = value

        if record.exc_info:
            payload["exception"] = self.formatException(record.exc_info)

        return json.dumps(payload, default=str)


def get_logger(name: str = "app") -> logging.Logger:
    """Return a logger configured for JSON output to stdout."""
    logger = logging.getLogger(name)
    if logger.handlers:
        return logger  # already configured

    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(JsonFormatter())
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)
    logger.propagate = False
    return logger


def configure_root_logger(level: str = "INFO") -> None:
    """Replace the root logger's handlers with our JSON handler.

    Call once at app startup so libraries (uvicorn, sqlalchemy) also log JSON.
    """
    root = logging.getLogger()
    root.handlers.clear()
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(JsonFormatter())
    root.addHandler(handler)
    root.setLevel(level)

    # Quiet down noisy libraries
    for noisy in ("uvicorn.access",):
        logging.getLogger(noisy).setLevel(logging.WARNING)
