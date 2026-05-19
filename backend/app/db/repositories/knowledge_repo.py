"""Knowledge article repository."""

from __future__ import annotations

import uuid

from sqlalchemy import func, or_, select

from app.db.repositories.base import BaseRepository
from app.models.knowledge_article import KnowledgeArticle


class KnowledgeRepository(BaseRepository[KnowledgeArticle]):
    model = KnowledgeArticle

    async def list_paginated(
        self,
        tenant_id: uuid.UUID,
        page: int,
        page_size: int,
        category: str | None = None,
        is_active: bool | None = None,
        search: str | None = None,
    ) -> tuple[list[KnowledgeArticle], int]:
        stmt = select(KnowledgeArticle).where(KnowledgeArticle.tenant_id == tenant_id)

        if category:
            stmt = stmt.where(KnowledgeArticle.category == category)
        if is_active is not None:
            stmt = stmt.where(KnowledgeArticle.is_active == is_active)
        if search:
            stmt = stmt.where(
                or_(
                    KnowledgeArticle.title.ilike(f"%{search}%"),
                    KnowledgeArticle.content.ilike(f"%{search}%"),
                )
            )

        count_stmt = select(func.count()).select_from(stmt.subquery())
        total = (await self.db.execute(count_stmt)).scalar_one()

        stmt = stmt.order_by(KnowledgeArticle.updated_at.desc()).offset((page - 1) * page_size).limit(page_size)
        result = await self.db.execute(stmt)
        return list(result.scalars().all()), total
