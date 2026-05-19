"""
Structured logging configuration for AI SupportOps.

Uses structlog with JSON output in production and pretty console output
in development. Includes request-scoped context (request_id, tenant_id).
"""

import logging
import sys
from typing import Any

import structlog
from structlog.types import EventDict, Processor

from app.config import settings


def _add_app_info(logger: Any, method: str, event_dict: EventDict) -> EventDict:
    """Inject static app metadata into every log entry."""
    event_dict["app"] = settings.app_name
    event_dict["version"] = settings.app_version
    event_dict["environment"] = settings.environment
    return event_dict


def _drop_color_message_key(logger: Any, method: str, event_dict: EventDict) -> EventDict:
    """Remove the 'color_message' key added by uvicorn in some versions."""
    event_dict.pop("color_message", None)
    return event_dict


def setup_logging() -> None:
    """
    Configure structlog and stdlib logging.
    - Production: JSON (machine-parseable for log aggregators)
    - Development: colored console output for readability
    """
    # 1. Processors applied to structlog loggers before passing to stdlib
    structlog_processors: list[Processor] = [
        structlog.contextvars.merge_contextvars,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
        structlog.stdlib.ProcessorFormatter.wrap_for_formatter,
    ]

    structlog.configure(
        processors=structlog_processors,
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )

    # 2. Processors applied to foreign (stdlib) logs (e.g. uvicorn)
    foreign_pre_chain: list[Processor] = [
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
        _drop_color_message_key,
    ]

    # 3. Final processors applied to ALL logs just before formatting
    renderer = (
        structlog.processors.JSONRenderer()
        if settings.is_production
        else structlog.dev.ConsoleRenderer(colors=True)
    )

    formatter_processors: list[Processor] = [
        _add_app_info,
        structlog.stdlib.ProcessorFormatter.remove_processors_meta,
        renderer,
    ]

    formatter = structlog.stdlib.ProcessorFormatter(
        processors=formatter_processors,
        foreign_pre_chain=foreign_pre_chain,
    )

    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(formatter)

    root_logger = logging.getLogger()
    root_logger.handlers.clear()
    root_logger.addHandler(handler)
    root_logger.setLevel(logging.DEBUG if settings.debug else logging.INFO)

    # Quiet noisy libraries
    for noisy_logger in ("uvicorn.access", "sqlalchemy.engine"):
        logging.getLogger(noisy_logger).setLevel(
            logging.DEBUG if settings.debug else logging.WARNING
        )


def get_logger(name: str = __name__) -> structlog.stdlib.BoundLogger:
    """Return a bound structlog logger for the given module name."""
    return structlog.get_logger(name)

