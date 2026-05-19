"""Message model — individual messages within a conversation."""

from __future__ import annotations

import uuid
import enum

from sqlalchemy import Enum, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class MessageRole(str, enum.Enum):
    CUSTOMER = "customer"
    AI_AGENT = "ai_agent"
    HUMAN_AGENT = "human_agent"
    SYSTEM = "system"


class Message(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "messages"

    conversation_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("conversations.id", ondelete="CASCADE"), nullable=False, index=True
    )
    role: Mapped[MessageRole] = mapped_column(
        Enum(MessageRole, name="message_role"), nullable=False
    )
    content: Mapped[str] = mapped_column(Text, nullable=False)
    # Stores: agent_name, model, prompt_tokens, completion_tokens, latency_ms
    agent_metadata: Mapped[dict] = mapped_column(JSONB, default=dict, nullable=False)
    # Stores references to knowledge articles used for this response
    sources: Mapped[list] = mapped_column(JSONB, default=list, nullable=False)
    # Links directly to LangSmith trace for deep debugging
    langsmith_run_id: Mapped[str | None] = mapped_column(String(255), nullable=True)

    # Relationships
    conversation: Mapped["Conversation"] = relationship(
        "Conversation", back_populates="messages", lazy="noload"
    )

    def __repr__(self) -> str:
        return f"<Message id={self.id} role={self.role}>"
