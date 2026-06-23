"""Structured (JSON) logging setup.

JSON logs aggregate into a dashboard later; free-text logs do not. Each request
carries a correlation id so detector, decision, and LLM-call events can be
joined. Call ``configure_logging()`` once at application startup.
"""

from __future__ import annotations

import logging

import structlog


def configure_logging(level: int = logging.INFO) -> None:
    structlog.configure(
        processors=[
            structlog.contextvars.merge_contextvars,
            structlog.processors.add_log_level,
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.JSONRenderer(),
        ],
        wrapper_class=structlog.make_filtering_bound_logger(level),
        cache_logger_on_first_use=True,
    )
