"""
Async SQLAlchemy session factory and engine management.

Provides:
- `AsyncEngine` singleton initialized via `init_db()`
- `AsyncSessionFactory` for creating database sessions
- `get_db()` dependency yielding a session per request
"""

from __future__ import annotations

from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from app.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)

# Module-level singletons (initialized in lifespan)
_engine: AsyncEngine | None = None
_session_factory: async_sessionmaker[AsyncSession] | None = None


async def init_db() -> None:
    """
    Create the async engine and session factory.
    Called once during application startup (see core/events.py).
    """
    global _engine, _session_factory

    _engine = create_async_engine(
        settings.database_url,
        echo=settings.debug,           # Log SQL in debug mode
        pool_size=10,                   # Persistent connections
        max_overflow=20,                # Extra connections under load
        pool_pre_ping=True,             # Verify connections before use
        pool_recycle=3600,              # Recycle after 1 hour
    )

    _session_factory = async_sessionmaker(
        bind=_engine,
        class_=AsyncSession,
        expire_on_commit=False,         # Avoid lazy-load issues after commit
        autocommit=False,
        autoflush=False,
    )

    logger.info("db_engine_created", url=settings.postgres_host)


async def close_db() -> None:
    """Dispose engine connection pool on application shutdown."""
    global _engine
    if _engine is not None:
        await _engine.dispose()
        _engine = None
        logger.info("db_engine_disposed")


def get_session_factory() -> async_sessionmaker[AsyncSession]:
    """Return the session factory (must call init_db first)."""
    if _session_factory is None:
        raise RuntimeError("Database not initialized. Call init_db() first.")
    return _session_factory


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    FastAPI dependency that yields a database session per request.

    Usage:
        async def my_route(db: AsyncSession = Depends(get_db)):
            ...
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
