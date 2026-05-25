"""
Shared FastAPI dependencies — injected into route handlers via Depends().

Provides:
- get_db: Database session per request
- get_current_user: Authenticated user from JWT (or X-Mock-Auth in development)
- require_role: RBAC role guard factory
- get_redis: Redis client from app state
- PaginationParams: Standard pagination query params
"""

from __future__ import annotations

import uuid
from typing import Annotated

from fastapi import Depends, Header, Query, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.core.exceptions import ForbiddenException, NotFoundException, UnauthorizedException
from app.core.security import decode_token
from app.db.session import get_db
from app.models.user import User, UserRole

# Re-export get_db so route files only need to import from deps
DBSession = Annotated[AsyncSession, Depends(get_db)]

# ── JWT Bearer ─────────────────────────────────────────────────────────────────

_bearer_scheme = HTTPBearer(auto_error=False)


async def _resolve_mock_user(db: AsyncSession) -> User:
    """
    Development-only: fetch the first active user from the DB, or create a
    demo tenant + admin user if the database is empty.

    This mirrors the dependency override used in test_fastapi.py so that the
    frontend X-Mock-Auth header works without a real JWT token.
    """
    from sqlalchemy.future import select
    from app.models.tenant import Tenant

    result = await db.execute(select(User).where(User.is_active == True).limit(1))
    user = result.scalar_one_or_none()
    if user:
        return user

    # No users exist — seed a demo tenant + admin so the UI is usable immediately
    result = await db.execute(select(Tenant).limit(1))
    tenant = result.scalar_one_or_none()
    if not tenant:
        tenant = Tenant(
            id=uuid.uuid4(),
            name="Demo Corp",
            slug="demo-tenant",
            settings={},
        )
        db.add(tenant)
        await db.flush()

    user = User(
        id=uuid.uuid4(),
        tenant_id=tenant.id,
        email="test@example.com",
        full_name="Test User",
        role=UserRole.ADMIN,
        is_active=True,
        hashed_password="mock",
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user


async def get_current_user(
    db: DBSession,
    credentials: HTTPAuthorizationCredentials | None = Depends(_bearer_scheme),
    x_mock_auth: str | None = Header(default=None),
) -> User:
    """
    Resolve the authenticated user.

    In development (ENVIRONMENT=development):
      - If the request carries X-Mock-Auth: true, skip JWT validation and
        return the first active user from the DB (auto-creating a demo user
        if none exists).  This is the same strategy used by test_fastapi.py.

    In all environments:
      - Decode the Bearer JWT, validate it, and fetch the user from the DB.
    """
    # ── Development mock bypass ────────────────────────────────────────────────
    if settings.is_development and x_mock_auth == "true":
        return await _resolve_mock_user(db)

    # ── Normal JWT path ────────────────────────────────────────────────────────
    if credentials is None:
        raise UnauthorizedException(detail="Authentication credentials not provided.")

    payload = decode_token(credentials.credentials, expected_type="access")
    user_id_str = payload.get("sub")

    if not user_id_str:
        raise UnauthorizedException(detail="Token missing subject claim.")

    try:
        user_id = uuid.UUID(user_id_str)
    except ValueError:
        raise UnauthorizedException(detail="Invalid token subject format.")

    # Lazy import to avoid circular imports
    from app.db.repositories.user_repo import UserRepository
    repo = UserRepository(db)
    user = await repo.get_by_id(user_id)

    if user is None or not user.is_active:
        raise UnauthorizedException(detail="User not found or account deactivated.")

    return user


CurrentUser = Annotated[User, Depends(get_current_user)]


def require_role(*roles: UserRole):
    """
    RBAC dependency factory.

    Usage:
        @router.delete("/{id}", dependencies=[Depends(require_role(UserRole.ADMIN))])
    """
    async def _check(current_user: CurrentUser) -> User:
        if current_user.role not in roles:
            raise ForbiddenException(
                detail=f"This action requires one of: {[r.value for r in roles]}"
            )
        return current_user
    return _check


# ── Redis ──────────────────────────────────────────────────────────────────────

async def get_redis(request: Request):
    """Return the Redis client stored on app.state during startup."""
    return getattr(request.app.state, "redis", None)


# ── Pagination ─────────────────────────────────────────────────────────────────

class PaginationParams:
    """Standard cursor-less pagination params (page + page_size)."""
    def __init__(
        self,
        page: int = Query(default=1, ge=1, description="Page number (1-indexed)"),
        page_size: int = Query(
            default=settings.default_page_size,
            ge=1,
            le=settings.max_page_size,
            description="Items per page",
        ),
    ) -> None:
        self.page = page
        self.page_size = page_size

    @property
    def offset(self) -> int:
        return (self.page - 1) * self.page_size

    @property
    def limit(self) -> int:
        return self.page_size


Pagination = Annotated[PaginationParams, Depends(PaginationParams)]
