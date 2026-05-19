"""
Ticket model — core entity representing a support request.

Indexes:
  - (tenant_id, status)         : list open/in-progress tickets per tenant
  - (tenant_id, priority)       : priority queue view
  - (tenant_id, category)       : category filter
  - (tenant_id, assigned_to)    : agent workload view
  - (tenant_id, created_at)     : time-ordered listing
  - external_id                 : deduplication for email/Slack ingest
"""

from __future__ import annotations

import enum
import uuid
from datetime import datetime

from sqlalchemy import DateTime, Enum, ForeignKey, Index, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, SoftDeleteMixin, TenantMixin, TimestampMixin, UUIDPrimaryKeyMixin


class TicketStatus(str, enum.Enum):
    OPEN = "open"
    IN_PROGRESS = "in_progress"
    AWAITING_CUSTOMER = "awaiting_customer"
    RESOLVED = "resolved"
    ESCALATED = "escalated"
    CLOSED = "closed"


class TicketPriority(str, enum.Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class TicketSource(str, enum.Enum):
    DASHBOARD = "dashboard"
    EMAIL = "email"
    API = "api"
    SLACK = "slack"
    WEBHOOK = "webhook"


class Ticket(UUIDPrimaryKeyMixin, TenantMixin, TimestampMixin, SoftDeleteMixin, Base):
    __tablename__ = "tickets"

    __table_args__ = (
        # Composite indexes for the most common dashboard queries
        Index("ix_tickets_tenant_status", "tenant_id", "status"),
        Index("ix_tickets_tenant_priority", "tenant_id", "priority"),
        Index("ix_tickets_tenant_category", "tenant_id", "category"),
        Index("ix_tickets_tenant_assigned", "tenant_id", "assigned_to"),
        Index("ix_tickets_tenant_created", "tenant_id", "created_at"),
    )

    # External reference (deduplicate inbound email/Slack events)
    external_id: Mapped[str | None] = mapped_column(
        String(255), unique=True, nullable=True, index=True
    )
    subject: Mapped[str] = mapped_column(String(500), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)

    status: Mapped[TicketStatus] = mapped_column(
        Enum(TicketStatus, name="ticket_status"),
        default=TicketStatus.OPEN,
        nullable=False,
        index=True,
    )
    priority: Mapped[TicketPriority] = mapped_column(
        Enum(TicketPriority, name="ticket_priority"),
        default=TicketPriority.MEDIUM,
        nullable=False,
        index=True,
    )
    category: Mapped[str | None] = mapped_column(String(100), nullable=True, index=True)
    tags: Mapped[list] = mapped_column(JSONB, default=list, nullable=False)
    source: Mapped[TicketSource] = mapped_column(
        Enum(TicketSource, name="ticket_source"),
        default=TicketSource.API,
        nullable=False,
    )

    # User references
    assigned_to: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    created_by: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )

    # AI classification output stored here after workflow runs
    ai_category: Mapped[str | None] = mapped_column(String(100), nullable=True)
    ai_sentiment: Mapped[str | None] = mapped_column(String(50), nullable=True)
    ai_confidence: Mapped[float | None] = mapped_column(nullable=True)

    # Flexible metadata (customer info, email headers, Slack context, etc.)
    metadata_: Mapped[dict] = mapped_column("metadata", JSONB, default=dict, nullable=False)

    # Timestamps for SLA / reporting
    first_response_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    resolved_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    # ── Relationships ────────────────────────────────────────────────────────
    tenant: Mapped["Tenant"] = relationship(
        "Tenant", back_populates="tickets", lazy="noload"
    )
    assignee: Mapped["User | None"] = relationship(
        "User", foreign_keys=[assigned_to], back_populates="assigned_tickets", lazy="noload"
    )
    creator: Mapped["User | None"] = relationship(
        "User", foreign_keys=[created_by], lazy="noload"
    )
    conversations: Mapped[list["Conversation"]] = relationship(
        "Conversation", back_populates="ticket", lazy="noload", cascade="all, delete-orphan"
    )
    workflow_runs: Mapped[list["WorkflowRun"]] = relationship(
        "WorkflowRun", back_populates="ticket", lazy="noload", cascade="all, delete-orphan"
    )
    approval_requests: Mapped[list["ApprovalRequest"]] = relationship(
        "ApprovalRequest", back_populates="ticket", lazy="noload", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<Ticket id={self.id} status={self.status} priority={self.priority}>"
