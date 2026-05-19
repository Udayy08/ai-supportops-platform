"""
Custom exception classes and FastAPI exception handlers.

All API errors use RFC 7807 Problem Details format:
{
    "type": "https://supportops.ai/errors/not-found",
    "title": "Resource Not Found",
    "status": 404,
    "detail": "Ticket with id 'abc' was not found.",
    "instance": "/api/v1/tickets/abc"
}
"""

from __future__ import annotations

from typing import Any

from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import ORJSONResponse

from app.core.logging import get_logger

logger = get_logger(__name__)


# ── Base Exception ─────────────────────────────────────────────────────────────

class SupportOpsException(Exception):
    """Base exception for all domain-level errors."""

    status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR
    error_type: str = "internal-error"
    title: str = "Internal Server Error"

    def __init__(self, detail: str = "An unexpected error occurred.", **extra: Any) -> None:
        self.detail = detail
        self.extra = extra
        super().__init__(detail)

    def to_problem_detail(self, request: Request) -> dict[str, Any]:
        return {
            "type": f"https://supportops.ai/errors/{self.error_type}",
            "title": self.title,
            "status": self.status_code,
            "detail": self.detail,
            "instance": str(request.url.path),
            **self.extra,
        }


# ── HTTP Exceptions ────────────────────────────────────────────────────────────

class NotFoundException(SupportOpsException):
    status_code = status.HTTP_404_NOT_FOUND
    error_type = "not-found"
    title = "Resource Not Found"


class ConflictException(SupportOpsException):
    status_code = status.HTTP_409_CONFLICT
    error_type = "conflict"
    title = "Resource Conflict"


class UnauthorizedException(SupportOpsException):
    status_code = status.HTTP_401_UNAUTHORIZED
    error_type = "unauthorized"
    title = "Authentication Required"


class ForbiddenException(SupportOpsException):
    status_code = status.HTTP_403_FORBIDDEN
    error_type = "forbidden"
    title = "Permission Denied"


class ValidationException(SupportOpsException):
    status_code = status.HTTP_422_UNPROCESSABLE_ENTITY
    error_type = "validation-error"
    title = "Validation Error"


class RateLimitException(SupportOpsException):
    status_code = status.HTTP_429_TOO_MANY_REQUESTS
    error_type = "rate-limit-exceeded"
    title = "Rate Limit Exceeded"


class ServiceUnavailableException(SupportOpsException):
    status_code = status.HTTP_503_SERVICE_UNAVAILABLE
    error_type = "service-unavailable"
    title = "Service Temporarily Unavailable"


# ── Exception Handlers ─────────────────────────────────────────────────────────

async def supportops_exception_handler(
    request: Request, exc: SupportOpsException
) -> ORJSONResponse:
    logger.warning(
        "domain_exception",
        error_type=exc.error_type,
        detail=exc.detail,
        path=request.url.path,
        status_code=exc.status_code,
    )
    return ORJSONResponse(
        status_code=exc.status_code,
        content=exc.to_problem_detail(request),
    )


async def validation_exception_handler(
    request: Request, exc: RequestValidationError
) -> ORJSONResponse:
    errors = exc.errors()
    logger.warning("validation_error", errors=errors, path=request.url.path)
    return ORJSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "type": "https://supportops.ai/errors/validation-error",
            "title": "Validation Error",
            "status": 422,
            "detail": "One or more fields failed validation.",
            "instance": str(request.url.path),
            "errors": errors,
        },
    )


async def unhandled_exception_handler(
    request: Request, exc: Exception
) -> ORJSONResponse:
    logger.exception("unhandled_exception", exc_info=exc, path=request.url.path)
    return ORJSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "type": "https://supportops.ai/errors/internal-error",
            "title": "Internal Server Error",
            "status": 500,
            "detail": "An unexpected error occurred. Please try again later.",
            "instance": str(request.url.path),
        },
    )


def register_exception_handlers(app: FastAPI) -> None:
    """Register all exception handlers on the FastAPI app instance."""
    app.add_exception_handler(SupportOpsException, supportops_exception_handler)  # type: ignore[arg-type]
    app.add_exception_handler(RequestValidationError, validation_exception_handler)  # type: ignore[arg-type]
    app.add_exception_handler(Exception, unhandled_exception_handler)
