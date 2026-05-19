"""Tenant model — top-level organizational unit for multi-tenancy."""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class Tenant(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "tenants"

    name: Mapped[str] = mapped_column(String(255), nullable=False)
    slug: Mapped[str] = mapped_column(String(100), unique=True, nullable=False, index=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    settings: Mapped[dict] = mapped_column(JSONB, default=dict, nullable=False)

    # Relationships
    users: Mapped[list["User"]] = relationship("User", back_populates="tenant", lazy="noload")
    tickets: Mapped[list["Ticket"]] = relationship("Ticket", back_populates="tenant", lazy="noload")

    def __repr__(self) -> str:
        return f"<Tenant id={self.id} slug={self.slug!r}>"
