"""User and Tenant repositories."""

from __future__ import annotations

import uuid
from typing import Any

from sqlalchemy import select

from app.db.repositories.base import BaseRepository
from app.models.tenant import Tenant
from app.models.user import User


class UserRepository(BaseRepository[User]):
    model = User

    async def get_by_email(self, email: str) -> User | None:
        stmt = select(User).where(User.email == email)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def list_by_tenant(self, tenant_id: uuid.UUID) -> list[User]:
        stmt = select(User).where(User.tenant_id == tenant_id)
        result = await self.db.execute(stmt)
        return list(result.scalars().all())


class TenantRepository(BaseRepository[Tenant]):
    model = Tenant

    async def get_by_slug(self, slug: str) -> Tenant | None:
        stmt = select(Tenant).where(Tenant.slug == slug)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()
