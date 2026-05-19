"""
Message model — individual messages within a conversation.

Each message has a role (customer, ai_agent, human_agent, system) and
carries rich metadata about the AI generation and knowledge sources used.

Indexes:
  - (conversation_id, created_at)   : ordered message history
  - (conversation_id, role)         : filter by role within a conversation
"""

from __future__ import annotations

import enum
import uuid

from sqlalchemy import Enum, ForeignKey, Index, String, Text
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

    __table_args__ = (
        Index("ix_messages_conv_created", "conversation_id", "created_at"),
        Index("ix_messages_conv_role", "conversation_id", "role"),
    )

    conversation_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("conversations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    role: Mapped[MessageRole] = mapped_column(
        Enum(MessageRole, name="message_role"),
        nullable=False,
        index=True,
    )
    content: Mapped[str] = mapped_column(Text, nullable=False)

    # AI generation metadata: agent_name, model, prompt_tokens, completion_tokens, latency_ms
    agent_metadata: Mapped[dict] = mapped_column(JSONB, default=dict, nullable=False)
    # Knowledge articles used for this response: [{id, title, score, chunk}]
    sources: Mapped[list] = mapped_column(JSONB, default=list, nullable=False)
    # Direct link to LangSmith trace for this message's generation
    langsmith_run_id: Mapped[str | None] = mapped_column(String(255), nullable=True)

    # ── Relationships ────────────────────────────────────────────────────────
    conversation: Mapped["Conversation"] = relationship(
        "Conversation", back_populates="messages", lazy="noload"
    )
    hallucination_flags: Mapped[list["HallucinationFlag"]] = relationship(
        "HallucinationFlag", back_populates="message", lazy="noload"
    )
    confidence_scores: Mapped[list["ConfidenceScore"]] = relationship(
        "ConfidenceScore", back_populates="message", lazy="noload"
    )

    def __repr__(self) -> str:
        return f"<Message id={self.id} role={self.role} conv={self.conversation_id}>"
