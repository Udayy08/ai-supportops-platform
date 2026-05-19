"""
AI SupportOps — FastAPI Application Entry Point

Initializes the FastAPI app with:
- Lifespan events (DB, Redis, Sentry)
- Middleware stack (CORS, rate limiting, request logging)
- Exception handlers (RFC 7807 Problem Details)
- API router (all v1 routes)
- Health check and metadata endpoints
"""

from __future__ import annotations

from fastapi import FastAPI
from fastapi.responses import ORJSONResponse

from app.api.v1.router import api_router
from app.config import settings
from app.core.events import lifespan
from app.core.exceptions import register_exception_handlers
from app.core.logging import setup_logging
from app.core.middleware import register_middleware

# ── Logging (must be first) ───────────────────────────────────────────────────
setup_logging()

# ── App factory ───────────────────────────────────────────────────────────────
app = FastAPI(
    title=settings.app_name,
    description=(
        "Multi-Agent Customer Support Resolution Platform — "
        "powered by LangGraph, LangChain, ChromaDB, and RAGAS."
    ),
    version=settings.app_version,
    docs_url="/docs" if not settings.is_production else None,
    redoc_url="/redoc" if not settings.is_production else None,
    openapi_url="/openapi.json" if not settings.is_production else None,
    default_response_class=ORJSONResponse,  # Faster JSON serialization
    lifespan=lifespan,
)

# ── Middleware ────────────────────────────────────────────────────────────────
register_middleware(app)

# ── Exception handlers ────────────────────────────────────────────────────────
register_exception_handlers(app)

# ── Routers ───────────────────────────────────────────────────────────────────
app.include_router(api_router, prefix=settings.api_v1_prefix)


# ── Health check ──────────────────────────────────────────────────────────────
@app.get("/health", tags=["Health"], include_in_schema=False)
async def health_check() -> dict:
    """
    Lightweight health check endpoint.
    Used by Docker HEALTHCHECK, Kubernetes liveness probes, and load balancers.
    Does NOT check database or Redis — those are checked at startup.
    """
    return {
        "status": "healthy",
        "version": settings.app_version,
        "environment": settings.environment,
    }


@app.get("/", tags=["Root"], include_in_schema=False)
async def root() -> dict:
    return {
        "name": settings.app_name,
        "version": settings.app_version,
        "docs": "/docs",
    }
