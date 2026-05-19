"""
ApprovalRequest model — human-in-the-loop escalation gate.

When the Quality Agent or Escalation Agent determines that a response needs
human review before being sent to the customer, it creates an ApprovalRequest.
The assigned human agent can APPROVE (send as-is), REJECT (discard), or
MODIFY (edit then send) the AI-generated response.

Indexes:
  - (tenant_id, status)         : queue of pending approvals per tenant
  - (tenant_id, assigned_to)    : workload per agent
  - (tenant_id, requested_at)   : time-ordered approval queue
  - (ticket_id)                 : all approvals for a ticket
"""

from __future__ import annotations

import enum
import uuid
from datetime import datetime

from sqlalchemy import DateTime, Enum, ForeignKey, Index, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TenantMixin, UUIDPrimaryKeyMixin


class ApprovalStatus(str, enum.Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    MODIFIED = "modified"   # Human edited the response before approving
    EXPIRED = "expired"     # SLA timeout — auto-escalated


class ApprovalPriority(str, enum.Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    URGENT = "urgent"


class ApprovalRequest(UUIDPrimaryKeyMixin, TenantMixin, Base):
    """
    Human-in-the-loop review gate for AI-generated responses.
    """

    __tablename__ = "approval_requests"

    __table_args__ = (
        Index("ix_approvals_tenant_status", "tenant_id", "status"),
        Index("ix_approvals_tenant_assigned", "tenant_id", "assigned_to"),
        Index("ix_approvals_tenant_requested", "tenant_id", "requested_at"),
        Index("ix_approvals_ticket", "ticket_id"),
    )

    ticket_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("tickets.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    workflow_run_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("workflow_runs.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    status: Mapped[ApprovalStatus] = mapped_column(
        Enum(ApprovalStatus, name="approval_status"),
        default=ApprovalStatus.PENDING,
        nullable=False,
        index=True,
    )
    priority: Mapped[ApprovalPriority] = mapped_column(
        Enum(ApprovalPriority, name="approval_priority"),
        default=ApprovalPriority.MEDIUM,
        nullable=False,
    )

    # Who should review (can be NULL for queue-based assignment)
    assigned_to: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    # Why this request was created
    reason: Mapped[str] = mapped_column(Text, nullable=False)
    # The AI-generated response pending review
    proposed_response: Mapped[str] = mapped_column(Text, nullable=False)
    # Human-modified version (only populated when status=MODIFIED)
    final_response: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Context passed to the reviewer (confidence scores, sources, flags, etc.)
    context: Mapped[dict] = mapped_column(JSONB, default=dict, nullable=False)

    # Review outcome
    reviewed_by: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    review_notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    # SLA: auto-expire after this timestamp
    expires_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True, index=True
    )

    requested_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, index=True
    )
    reviewed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    # ── Relationships ────────────────────────────────────────────────────────
    ticket: Mapped["Ticket"] = relationship(
        "Ticket", back_populates="approval_requests", lazy="noload"
    )
    reviewer: Mapped["User | None"] = relationship(
        "User", foreign_keys=[reviewed_by], back_populates="approval_requests", lazy="noload"
    )
    assignee: Mapped["User | None"] = relationship(
        "User", foreign_keys=[assigned_to], lazy="noload"
    )

    def __repr__(self) -> str:
        return (
            f"<ApprovalRequest id={self.id} ticket={self.ticket_id} status={self.status}>"
        )
