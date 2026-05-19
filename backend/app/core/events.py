"""
Application lifespan event handlers.

Manages startup and shutdown of:
- Database connection pool (SQLAlchemy async engine)
- Redis connection pool
- Sentry SDK initialization
"""

from __future__ import annotations

from contextlib import asynccontextmanager
from typing import AsyncGenerator

import redis.asyncio as aioredis
import sentry_sdk
from fastapi import FastAPI
from sentry_sdk.integrations.fastapi import FastApiIntegration
from sentry_sdk.integrations.sqlalchemy import SqlalchemyIntegration

from app.config import settings
from app.core.logging import get_logger
from app.db.session import close_db, init_db

logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """
    FastAPI lifespan context manager.
    Everything before `yield` runs on startup; after `yield` runs on shutdown.
    """
    # ── Startup ───────────────────────────────────────────────────────────────
    logger.info("application_startup", environment=settings.environment)

    # Sentry (before anything else so it can capture startup errors)
    _init_sentry()

    # Database engine + connection pool
    await init_db()
    logger.info("database_connected", host=settings.postgres_host, db=settings.postgres_db)

    # Redis connection pool
    redis_client = aioredis.from_url(
        settings.redis_url,
        encoding="utf-8",
        decode_responses=True,
        socket_connect_timeout=5,
    )
    app.state.redis = redis_client
    try:
        await redis_client.ping()
        logger.info("redis_connected", host=settings.redis_host)
    except Exception as exc:
        logger.warning("redis_connection_failed", error=str(exc))
        # Non-fatal: rate limiting degrades gracefully

    logger.info("application_ready", version=settings.app_version)

    yield  # ── Application is running ───────────────────────────────────────

    # ── Shutdown ──────────────────────────────────────────────────────────────
    logger.info("application_shutdown")

    # Close Redis pool
    if hasattr(app.state, "redis"):
        await app.state.redis.aclose()
        logger.info("redis_disconnected")

    # Dispose SQLAlchemy engine pool
    await close_db()
    logger.info("database_disconnected")


def _init_sentry() -> None:
    """Initialize Sentry SDK if DSN is configured."""
    if not settings.sentry_dsn:
        return
    sentry_sdk.init(
        dsn=settings.sentry_dsn,
        environment=settings.environment,
        release=settings.app_version,
        traces_sample_rate=settings.sentry_traces_sample_rate,
        integrations=[
            FastApiIntegration(transaction_style="endpoint"),
            SqlalchemyIntegration(),
        ],
    )
    logger.info("sentry_initialized")
