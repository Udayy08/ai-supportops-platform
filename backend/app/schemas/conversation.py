"""Pydantic schemas for Conversation and Message endpoints."""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field

from app.models.conversation import ConversationStatus
from app.models.message import MessageRole


# ── Message Schemas ───────────────────────────────────────────────────────────

class MessageResponse(BaseModel):
    id: uuid.UUID
    conversation_id: uuid.UUID
    role: MessageRole
    content: str
    agent_metadata: dict[str, Any]
    sources: list[Any]
    langsmith_run_id: str | None
    created_at: datetime

    model_config = {"from_attributes": True}


class MessageCreateRequest(BaseModel):
    """Used when a human agent or customer adds a message manually."""
    role: MessageRole
    content: str = Field(..., min_length=1)


# ── Conversation Schemas ──────────────────────────────────────────────────────

class ConversationResponse(BaseModel):
    id: uuid.UUID
    ticket_id: uuid.UUID
    tenant_id: uuid.UUID
    status: ConversationStatus
    turn_count: int
    confidence_score: float | None
    messages: list[MessageResponse] = []
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class ConversationListResponse(BaseModel):
    items: list[ConversationResponse]
    total: int
