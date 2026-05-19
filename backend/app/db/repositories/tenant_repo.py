"""Tenant repository — extracted from user_repo for clean module separation."""

from __future__ import annotations

from sqlalchemy import select

from app.db.repositories.base import BaseRepository
from app.models.tenant import Tenant


class TenantRepository(BaseRepository[Tenant]):
    model = Tenant

    async def get_by_slug(self, slug: str) -> Tenant | None:
        stmt = select(Tenant).where(Tenant.slug == slug)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()
