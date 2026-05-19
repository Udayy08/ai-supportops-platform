"""
AuditLog model — immutable append-only record of all state-changing actions.

Never updated or deleted — only inserted. Use for compliance, debugging,
and security forensics.

Indexes:
  - (tenant_id, action)         : filter by action type
  - (tenant_id, resource_type, resource_id) : all changes to a resource
  - (tenant_id, created_at)     : time-ordered audit trail
  - (user_id, created_at)       : actions by a specific user
"""

from __future__ import annotations

import enum
import uuid
from datetime import datetime

from sqlalchemy import DateTime, Enum, ForeignKey, Index, String, func
from sqlalchemy.dialects.postgresql import INET, JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TenantMixin, UUIDPrimaryKeyMixin


class AuditAction(str, enum.Enum):
    # Ticket actions
    TICKET_CREATED = "ticket.created"
    TICKET_UPDATED = "ticket.updated"
    TICKET_ASSIGNED = "ticket.assigned"
    TICKET_RESOLVED = "ticket.resolved"
    TICKET_ESCALATED = "ticket.escalated"
    TICKET_CLOSED = "ticket.closed"
    TICKET_DELETED = "ticket.deleted"
    # Approval actions
    APPROVAL_REQUESTED = "approval.requested"
    APPROVAL_APPROVED = "approval.approved"
    APPROVAL_REJECTED = "approval.rejected"
    APPROVAL_MODIFIED = "approval.modified"
    # User actions
    USER_CREATED = "user.created"
    USER_ROLE_CHANGED = "user.role_changed"
    USER_DEACTIVATED = "user.deactivated"
    # AI Quality
    HALLUCINATION_FLAGGED = "hallucination.flagged"
    HALLUCINATION_RESOLVED = "hallucination.resolved"
    # Knowledge base
    KNOWLEDGE_ARTICLE_CREATED = "knowledge.article_created"
    KNOWLEDGE_ARTICLE_UPDATED = "knowledge.article_updated"
    KNOWLEDGE_ARTICLE_DELETED = "knowledge.article_deleted"
    # Auth
    USER_LOGIN = "auth.login"
    USER_LOGOUT = "auth.logout"
    TOKEN_REFRESHED = "auth.token_refreshed"


class AuditLog(UUIDPrimaryKeyMixin, TenantMixin, Base):
    __tablename__ = "audit_logs"

    __table_args__ = (
        Index("ix_audit_tenant_action", "tenant_id", "action"),
        Index("ix_audit_tenant_resource", "tenant_id", "resource_type", "resource_id"),
        Index("ix_audit_tenant_created", "tenant_id", "created_at"),
        Index("ix_audit_user_created", "user_id", "created_at"),
    )

    user_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    action: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    resource_type: Mapped[str] = mapped_column(String(100), nullable=False)
    resource_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)

    # Before/after state snapshot for auditable changes
    before_state: Mapped[dict] = mapped_column(JSONB, default=dict, nullable=False)
    after_state: Mapped[dict] = mapped_column(JSONB, default=dict, nullable=False)
    # Legacy alias kept for compatibility with existing code
    changes: Mapped[dict] = mapped_column(JSONB, default=dict, nullable=False)

    # Request context
    ip_address: Mapped[str | None] = mapped_column(String(45), nullable=True)
    user_agent: Mapped[str | None] = mapped_column(String(500), nullable=True)
    request_id: Mapped[str | None] = mapped_column(String(100), nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=func.now(),
        server_default=func.now(),
        nullable=False,
        index=True,
    )

    def __repr__(self) -> str:
        return (
            f"<AuditLog id={self.id} action={self.action!r} resource={self.resource_type}>"
        )
