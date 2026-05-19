"""Base repository providing generic CRUD operations."""

from __future__ import annotations

import uuid
from typing import Any, Generic, TypeVar

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.base import Base

ModelType = TypeVar("ModelType", bound=Base)


class BaseRepository(Generic[ModelType]):
    """Generic async repository with standard CRUD operations."""

    model: type[ModelType]

    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def get_by_id(self, id: uuid.UUID, **filters: Any) -> ModelType | None:
        stmt = select(self.model).where(self.model.id == id)  # type: ignore[attr-defined]
        for key, value in filters.items():
            stmt = stmt.where(getattr(self.model, key) == value)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def create(self, **kwargs: Any) -> ModelType:
        obj = self.model(**kwargs)  # type: ignore[call-arg]
        self.db.add(obj)
        await self.db.flush()  # Get generated ID without committing
        await self.db.refresh(obj)
        return obj

    async def update(self, obj: ModelType, **kwargs: Any) -> ModelType:
        for key, value in kwargs.items():
            setattr(obj, key, value)
        self.db.add(obj)
        await self.db.flush()
        await self.db.refresh(obj)
        return obj

    async def delete(self, obj: ModelType) -> None:
        await self.db.delete(obj)
        await self.db.flush()

    async def count(self, **filters: Any) -> int:
        stmt = select(func.count()).select_from(self.model)
        for key, value in filters.items():
            stmt = stmt.where(getattr(self.model, key) == value)
        result = await self.db.execute(stmt)
        return result.scalar_one()
