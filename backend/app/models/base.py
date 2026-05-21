"""
SQLAlchemy declarative base and reusable model mixins.

Mixins available:
- UUIDPrimaryKeyMixin  : UUID PK with gen_random_uuid() server default
- TimestampMixin       : created_at / updated_at with auto-management
- TenantMixin          : tenant_id FK for multi-tenant row isolation
- SoftDeleteMixin      : deleted_at for soft-deletes (non-destructive)
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy import DateTime, Index, String, func, text, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    """Declarative base for all ORM models."""
    pass


class UUIDPrimaryKeyMixin:
    """Adds a UUID primary key generated client-side (uuid4) with server fallback."""
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        server_default=text("gen_random_uuid()"),
    )


class TimestampMixin:
    """Adds created_at and updated_at with full timezone awareness."""
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        server_default=func.now(),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        server_default=func.now(),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )


class TenantMixin:
    """
    Adds tenant_id for multi-tenant row-level isolation.
    All tenant-scoped models must include this mixin.
    tenant_id is indexed individually; composite indexes are added per-table.
    """
    tenant_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("tenants.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )


class SoftDeleteMixin:
    """
    Soft-delete support — set deleted_at instead of physically removing rows.
    Queries must explicitly filter WHERE deleted_at IS NULL.
    """
    deleted_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        default=None,
        index=True,
    )

    @property
    def is_deleted(self) -> bool:
        return self.deleted_at is not None
