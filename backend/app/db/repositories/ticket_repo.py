"""Ticket repository with pagination and multi-field filtering."""

from __future__ import annotations

import uuid
from typing import Any

from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.repositories.base import BaseRepository
from app.models.ticket import Ticket, TicketPriority, TicketStatus


class TicketRepository(BaseRepository[Ticket]):
    model = Ticket

    async def list_paginated(
        self,
        tenant_id: uuid.UUID,
        page: int,
        page_size: int,
        status: TicketStatus | None = None,
        priority: TicketPriority | None = None,
        category: str | None = None,
        assigned_to: uuid.UUID | None = None,
        search: str | None = None,
    ) -> tuple[list[Ticket], int]:
        stmt = select(Ticket).where(Ticket.tenant_id == tenant_id)

        if status:
            stmt = stmt.where(Ticket.status == status)
        if priority:
            stmt = stmt.where(Ticket.priority == priority)
        if category:
            stmt = stmt.where(Ticket.category == category)
        if assigned_to:
            stmt = stmt.where(Ticket.assigned_to == assigned_to)
        if search:
            stmt = stmt.where(
                or_(
                    Ticket.subject.ilike(f"%{search}%"),
                    Ticket.description.ilike(f"%{search}%"),
                )
            )

        # Total count
        count_stmt = select(func.count()).select_from(stmt.subquery())
        count_result = await self.db.execute(count_stmt)
        total = count_result.scalar_one()

        # Paginated results
        stmt = stmt.order_by(Ticket.created_at.desc()).offset((page - 1) * page_size).limit(page_size)
        result = await self.db.execute(stmt)
        return list(result.scalars().all()), total
