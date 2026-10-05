"""Structured logging. Never log secrets: callers must not pass keys/tokens."""

from __future__ import annotations

import logging
import sys

import structlog

SENSITIVE_KEYS = {"password", "token", "api_key", "authorization", "secret"}


def _redact(_logger, _method, event_dict):
    for key in list(event_dict):
        if any(s in key.lower() for s in SENSITIVE_KEYS):
            event_dict[key] = "***"
    return event_dict


def configure_logging(level: str = "INFO") -> None:
    logging.basicConfig(level=level, stream=sys.stdout, format="%(message)s")
    structlog.configure(
        processors=[
            structlog.contextvars.merge_contextvars,
            structlog.processors.add_log_level,
            structlog.processors.TimeStamper(fmt="iso"),
            _redact,
            structlog.processors.JSONRenderer(),
        ],
        wrapper_class=structlog.make_filtering_bound_logger(logging.getLevelName(level)),
        cache_logger_on_first_use=True,
    )


def get_logger(name: str):
    return structlog.get_logger(name)
