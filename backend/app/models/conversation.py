"""
Conversation model — groups all messages for a single ticket interaction session.

One Ticket → many Conversations (one per workflow run session)
One Conversation → many Messages
One Conversation → many Evaluations
One Conversation → many WorkflowRuns

Indexes:
  - (tenant_id, ticket_id)      : conversations for a ticket
  - (tenant_id, status)         : active conversation filter
  - (tenant_id, created_at)     : time-ordered listing
"""

from __future__ import annotations

import enum
import uuid

from sqlalchemy import Enum, Float, ForeignKey, Index, Integer, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TenantMixin, TimestampMixin, UUIDPrimaryKeyMixin


class ConversationStatus(str, enum.Enum):
    ACTIVE = "active"
    COMPLETED = "completed"
    ESCALATED = "escalated"
    AWAITING_APPROVAL = "awaiting_approval"


class Conversation(UUIDPrimaryKeyMixin, TenantMixin, TimestampMixin, Base):
    __tablename__ = "conversations"

    __table_args__ = (
        Index("ix_conversations_tenant_ticket", "tenant_id", "ticket_id"),
        Index("ix_conversations_tenant_status", "tenant_id", "status"),
        Index("ix_conversations_tenant_created", "tenant_id", "created_at"),
    )

    ticket_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("tickets.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    status: Mapped[ConversationStatus] = mapped_column(
        Enum(ConversationStatus, name="conversation_status"),
        default=ConversationStatus.ACTIVE,
        nullable=False,
    )
    turn_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    # Aggregate confidence across all AI turns in this conversation
    confidence_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    # The channel this conversation is happening on
    channel: Mapped[str | None] = mapped_column(String(50), nullable=True)

    # ── Relationships ────────────────────────────────────────────────────────
    ticket: Mapped["Ticket"] = relationship(
        "Ticket", back_populates="conversations", lazy="noload"
    )
    messages: Mapped[list["Message"]] = relationship(
        "Message",
        back_populates="conversation",
        lazy="noload",
        cascade="all, delete-orphan",
        order_by="Message.created_at",
    )
    evaluations: Mapped[list["Evaluation"]] = relationship(
        "Evaluation", back_populates="conversation", lazy="noload"
    )
    workflow_runs: Mapped[list["WorkflowRun"]] = relationship(
        "WorkflowRun", back_populates="conversation", lazy="noload"
    )

    def __repr__(self) -> str:
        return f"<Conversation id={self.id} status={self.status} turns={self.turn_count}>"
