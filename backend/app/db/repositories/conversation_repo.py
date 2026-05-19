"""Conversation and Message repositories."""

from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.db.repositories.base import BaseRepository
from app.models.conversation import Conversation
from app.models.message import Message, MessageRole


class ConversationRepository(BaseRepository[Conversation]):
    model = Conversation

    async def list_by_ticket(self, ticket_id: uuid.UUID) -> list[Conversation]:
        stmt = (
            select(Conversation)
            .where(Conversation.ticket_id == ticket_id)
            .order_by(Conversation.created_at.asc())
        )
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def get_by_id_with_messages(
        self, conversation_id: uuid.UUID, tenant_id: uuid.UUID
    ) -> Conversation | None:
        stmt = (
            select(Conversation)
            .options(selectinload(Conversation.messages))
            .where(
                Conversation.id == conversation_id,
                Conversation.tenant_id == tenant_id,
            )
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def add_message(
        self,
        conversation_id: uuid.UUID,
        role: MessageRole,
        content: str,
        agent_metadata: dict | None = None,
        sources: list | None = None,
        langsmith_run_id: str | None = None,
    ) -> Message:
        message = Message(
            conversation_id=conversation_id,
            role=role,
            content=content,
            agent_metadata=agent_metadata or {},
            sources=sources or [],
            langsmith_run_id=langsmith_run_id,
        )
        self.db.add(message)
        await self.db.flush()
        await self.db.refresh(message)

        # Increment turn count
        conv_result = await self.db.execute(
            select(Conversation).where(Conversation.id == conversation_id)
        )
        conv = conv_result.scalar_one()
        conv.turn_count += 1
        await self.db.flush()

        return message
