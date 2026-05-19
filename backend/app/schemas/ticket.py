"""Pydantic schemas for Ticket endpoints."""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field

from app.models.ticket import TicketPriority, TicketSource, TicketStatus


# ── Request Schemas ───────────────────────────────────────────────────────────

class TicketCreateRequest(BaseModel):
    subject: str = Field(..., min_length=1, max_length=500)
    description: str = Field(..., min_length=1)
    priority: TicketPriority = TicketPriority.MEDIUM
    source: TicketSource = TicketSource.API
    category: str | None = None
    external_id: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class TicketUpdateRequest(BaseModel):
    subject: str | None = Field(None, max_length=500)
    status: TicketStatus | None = None
    priority: TicketPriority | None = None
    category: str | None = None
    assigned_to: uuid.UUID | None = None


# ── Response Schemas ──────────────────────────────────────────────────────────

class TicketResponse(BaseModel):
    id: uuid.UUID
    tenant_id: uuid.UUID
    external_id: str | None
    subject: str
    description: str
    status: TicketStatus
    priority: TicketPriority
    category: str | None
    source: TicketSource
    assigned_to: uuid.UUID | None
    created_by: uuid.UUID | None
    metadata: dict[str, Any]
    resolved_at: datetime | None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}

    # Map SQLAlchemy `metadata_` column to Pydantic `metadata` field
    @classmethod
    def model_validate(cls, obj: Any, **kwargs: Any) -> "TicketResponse":
        if hasattr(obj, "metadata_"):
            obj.__dict__["metadata"] = obj.metadata_
        return super().model_validate(obj, **kwargs)


class TicketListResponse(BaseModel):
    items: list[TicketResponse]
    total: int
    page: int
    page_size: int
    has_next: bool
