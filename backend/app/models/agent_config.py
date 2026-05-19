"""AgentConfig model — per-tenant LLM and prompt configuration for each agent."""

from __future__ import annotations

import uuid

from sqlalchemy import Boolean, ForeignKey, String
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TenantMixin, TimestampMixin, UUIDPrimaryKeyMixin


class AgentConfig(UUIDPrimaryKeyMixin, TenantMixin, TimestampMixin, Base):
    __tablename__ = "agent_configs"

    # One of: classifier, sentiment, retriever, resolver, quality, escalation
    agent_name: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    # LLM model identifier: gpt-4o, gpt-4o-mini, claude-3-5-sonnet, etc.
    model_name: Mapped[str] = mapped_column(String(100), nullable=False)
    # Stores: system_prompt, temperature, max_tokens, etc.
    prompt_config: Mapped[dict] = mapped_column(JSONB, default=dict, nullable=False)
    # Stores: enabled tool names and their parameters
    tool_config: Mapped[dict] = mapped_column(JSONB, default=dict, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    def __repr__(self) -> str:
        return f"<AgentConfig id={self.id} agent={self.agent_name!r} model={self.model_name!r}>"
