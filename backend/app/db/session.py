"""
Async SQLAlchemy session factory and engine management.

Architecture:
  - Single AsyncEngine per process, initialized once at startup
  - async_sessionmaker creates a session per request
  - get_db() yields a session with automatic commit/rollback
  - Unit of Work pattern: each request is a single transaction
"""

from __future__ import annotations

from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.pool import NullPool

from app.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)

# Module-level singletons (set in init_db, cleared in close_db)
_engine: AsyncEngine | None = None
_session_factory: async_sessionmaker[AsyncSession] | None = None


async def init_db() -> None:
    """
    Create the async engine and session factory.
    Called once during application startup via core/events.py lifespan.

    Pool configuration:
      pool_size=10     — persistent connections kept alive
      max_overflow=20  — extra connections allowed under burst load
      pool_pre_ping    — validate connections before use (handles DB restarts)
      pool_recycle     — recycle connections after 1 hour to avoid stale state
    """
    global _engine, _session_factory

    _engine = create_async_engine(
        settings.database_url,
        echo=settings.debug,
        pool_size=10,
        max_overflow=20,
        pool_pre_ping=True,
        pool_recycle=3600,
        pool_timeout=30,
        connect_args={
            "server_settings": {
                "application_name": settings.app_name,
                "jit": "off",  # Disable JIT for short-lived OLTP queries
            }
        },
    )

    _session_factory = async_sessionmaker(
        bind=_engine,
        class_=AsyncSession,
        expire_on_commit=False,   # Avoid implicit lazy-load after commit
        autocommit=False,
        autoflush=False,
    )

    logger.info("db_engine_initialized", host=settings.postgres_host, db=settings.postgres_db)


async def close_db() -> None:
    """Dispose engine connection pool on application shutdown."""
    global _engine
    if _engine is not None:
        await _engine.dispose()
        _engine = None
        logger.info("db_engine_disposed")


def get_engine() -> AsyncEngine:
    """Return the raw engine (needed for Alembic migrations, direct DDL, etc.)."""
    if _engine is None:
        raise RuntimeError("Database not initialized. Call init_db() first.")
    return _engine


def get_session_factory() -> async_sessionmaker[AsyncSession]:
    """Return the session factory. Raises if init_db() has not been called."""
    if _session_factory is None:
        raise RuntimeError("Database not initialized. Call init_db() first.")
    return _session_factory


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    FastAPI dependency that yields a database session per HTTP request.

    Pattern: Unit of Work
      - Session opened at request start
      - Committed on success
      - Rolled back on any unhandled exception
      - Always closed in finally

    Usage:
        async def my_route(db: AsyncSession = Depends(get_db)):
            result = await db.execute(select(Ticket))
    """
    factory = get_session_factory()
    async with factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()
