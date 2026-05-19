"""Auth routes — register, login, token refresh, current user."""

from __future__ import annotations

from fastapi import APIRouter, status

from app.api.deps import CurrentUser, DBSession
from app.core.exceptions import ConflictException, UnauthorizedException
from app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    hash_password,
    verify_password,
)
from app.config import settings
from app.db.repositories.user_repo import UserRepository
from app.db.repositories.tenant_repo import TenantRepository
from app.schemas.user import (
    TokenRefreshRequest,
    TokenResponse,
    UserLoginRequest,
    UserRegisterRequest,
    UserResponse,
)

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post(
    "/register",
    response_model=TokenResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register new tenant and admin user",
)
async def register(body: UserRegisterRequest, db: DBSession) -> TokenResponse:
    """
    Creates a new Tenant and the first Admin user in one transaction.
    Returns access + refresh tokens on success.
    """
    user_repo = UserRepository(db)
    tenant_repo = TenantRepository(db)

    # Check for duplicate email
    existing = await user_repo.get_by_email(body.email)
    if existing:
        raise ConflictException(detail=f"Email '{body.email}' is already registered.")

    # Create tenant
    import re
    slug = re.sub(r"[^a-z0-9]+", "-", body.tenant_name.lower()).strip("-")
    tenant = await tenant_repo.create(name=body.tenant_name, slug=slug)

    # Create admin user
    from app.models.user import UserRole
    user = await user_repo.create(
        tenant_id=tenant.id,
        email=body.email,
        hashed_password=hash_password(body.password),
        full_name=body.full_name,
        role=UserRole.ADMIN,
    )

    access_token = create_access_token(
        subject=str(user.id),
        extra_claims={"tenant_id": str(tenant.id), "role": user.role.value},
    )
    refresh_token = create_refresh_token(subject=str(user.id))

    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        expires_in=settings.access_token_expire_minutes * 60,
    )


@router.post("/login", response_model=TokenResponse, summary="Login with email and password")
async def login(body: UserLoginRequest, db: DBSession) -> TokenResponse:
    user_repo = UserRepository(db)
    user = await user_repo.get_by_email(body.email)

    if not user or not verify_password(body.password, user.hashed_password):
        raise UnauthorizedException(detail="Invalid email or password.")
    if not user.is_active:
        raise UnauthorizedException(detail="Account is deactivated.")

    access_token = create_access_token(
        subject=str(user.id),
        extra_claims={"tenant_id": str(user.tenant_id), "role": user.role.value},
    )
    refresh_token = create_refresh_token(subject=str(user.id))

    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        expires_in=settings.access_token_expire_minutes * 60,
    )


@router.post("/refresh", response_model=TokenResponse, summary="Refresh access token")
async def refresh_token(body: TokenRefreshRequest, db: DBSession) -> TokenResponse:
    payload = decode_token(body.refresh_token, expected_type="refresh")
    user_repo = UserRepository(db)

    import uuid
    user = await user_repo.get_by_id(uuid.UUID(payload["sub"]))
    if not user or not user.is_active:
        raise UnauthorizedException(detail="User not found or deactivated.")

    access_token = create_access_token(
        subject=str(user.id),
        extra_claims={"tenant_id": str(user.tenant_id), "role": user.role.value},
    )
    new_refresh = create_refresh_token(subject=str(user.id))

    return TokenResponse(
        access_token=access_token,
        refresh_token=new_refresh,
        expires_in=settings.access_token_expire_minutes * 60,
    )


@router.get("/me", response_model=UserResponse, summary="Get current user profile")
async def get_me(current_user: CurrentUser) -> UserResponse:
    return UserResponse.model_validate(current_user)
