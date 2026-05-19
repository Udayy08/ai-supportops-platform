"""
Middleware stack for AI SupportOps.

Registered in order (outermost → innermost):
1. TrustedHostMiddleware   — blocks invalid Host headers
2. CORSMiddleware          — cross-origin policy
3. RequestLoggingMiddleware — structured request/response logging + request_id
4. RateLimitMiddleware     — per-IP sliding window via Redis
"""

from __future__ import annotations

import time
import uuid
from typing import Callable

import structlog
from fastapi import FastAPI, Request, Response, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import ORJSONResponse
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint

from app.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)


# ── Request Logging Middleware ────────────────────────────────────────────────

class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """
    Injects a unique request_id into structlog context for every request.
    Logs method, path, status code, and elapsed time on completion.
    Skips health check endpoint to reduce noise.
    """

    SKIP_PATHS = {"/health", "/metrics", "/favicon.ico"}

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        if request.url.path in self.SKIP_PATHS:
            return await call_next(request)

        request_id = str(uuid.uuid4())
        start_time = time.perf_counter()

        # Bind request_id to structlog context (available to all log calls in this request)
        structlog.contextvars.clear_contextvars()
        structlog.contextvars.bind_contextvars(
            request_id=request_id,
            method=request.method,
            path=request.url.path,
        )

        # Expose request_id in response headers for client-side correlation
        request.state.request_id = request_id

        response = await call_next(request)

        elapsed_ms = round((time.perf_counter() - start_time) * 1000, 2)
        response.headers["X-Request-ID"] = request_id

        logger.info(
            "http_request",
            status_code=response.status_code,
            duration_ms=elapsed_ms,
        )
        return response


# ── Rate Limit Middleware ─────────────────────────────────────────────────────

class RateLimitMiddleware(BaseHTTPMiddleware):
    """
    Sliding window rate limiter using Redis.
    Limit: settings.rate_limit_per_minute requests per minute per IP.
    Falls back gracefully if Redis is unavailable (logs warning, allows request).
    """

    SKIP_PATHS = {"/health", "/metrics"}

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        if request.url.path in self.SKIP_PATHS:
            return await call_next(request)

        client_ip = self._get_client_ip(request)
        redis = getattr(request.app.state, "redis", None)

        if redis is not None:
            try:
                is_allowed = await self._check_rate_limit(redis, client_ip)
                if not is_allowed:
                    return ORJSONResponse(
                        status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                        content={
                            "type": "https://supportops.ai/errors/rate-limit-exceeded",
                            "title": "Rate Limit Exceeded",
                            "status": 429,
                            "detail": f"Max {settings.rate_limit_per_minute} requests/min exceeded.",
                        },
                        headers={"Retry-After": "60"},
                    )
            except Exception as exc:
                logger.warning("rate_limit_redis_error", error=str(exc))
                # Fail open — don't block requests if Redis is down

        return await call_next(request)

    @staticmethod
    def _get_client_ip(request: Request) -> str:
        forwarded_for = request.headers.get("X-Forwarded-For")
        if forwarded_for:
            return forwarded_for.split(",")[0].strip()
        return request.client.host if request.client else "unknown"

    @staticmethod
    async def _check_rate_limit(redis: object, client_ip: str) -> bool:
        """
        Sliding window counter using Redis INCR + EXPIRE.
        Returns True if request is allowed, False if rate limit exceeded.
        """
        key = f"rate_limit:{client_ip}"
        count = await redis.incr(key)  # type: ignore[attr-defined]
        if count == 1:
            await redis.expire(key, 60)  # type: ignore[attr-defined]
        return count <= settings.rate_limit_per_minute


# ── Registration Helper ───────────────────────────────────────────────────────

def register_middleware(app: FastAPI) -> None:
    """Register all middleware on the FastAPI app instance."""

    # TrustedHost (outermost)
    # Note: parentheses are required — without them `+` binds tighter than `if`
    trusted_hosts = (
        settings.allowed_hosts + ["*"]
        if settings.is_development
        else settings.allowed_hosts
    )
    app.add_middleware(TrustedHostMiddleware, allowed_hosts=trusted_hosts)

    # CORS — backend_cors_origins is now list[str] so no str() conversion needed.
    # In development with an empty list, fall back to allow all origins ("*").
    cors_origins = settings.backend_cors_origins if settings.backend_cors_origins else ["*"]
    app.add_middleware(
        CORSMiddleware,
        allow_origins=cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
        expose_headers=["X-Request-ID"],
    )

    # Rate limiting (uses Redis via app.state)
    app.add_middleware(RateLimitMiddleware)

    # Request logging + request_id injection
    app.add_middleware(RequestLoggingMiddleware)

