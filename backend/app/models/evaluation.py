"""Evaluation model — stores RAGAS and custom metric results per conversation."""

from __future__ import annotations

import uuid
import enum
from datetime import datetime

from sqlalchemy import DateTime, Enum, ForeignKey, String, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TenantMixin, UUIDPrimaryKeyMixin


class EvalType(str, enum.Enum):
    RAGAS = "ragas"
    CUSTOM = "custom"
    MANUAL = "manual"


class Evaluation(UUIDPrimaryKeyMixin, TenantMixin, Base):
    __tablename__ = "evaluations"

    conversation_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("conversations.id", ondelete="SET NULL"), nullable=True, index=True
    )
    eval_type: Mapped[EvalType] = mapped_column(
        Enum(EvalType, name="eval_type"), nullable=False
    )
    # Stores: faithfulness, answer_relevancy, context_relevancy, etc.
    scores: Mapped[dict] = mapped_column(JSONB, default=dict, nullable=False)
    # Stores: question, ground_truth, contexts used for evaluation
    dataset_info: Mapped[dict] = mapped_column(JSONB, default=dict, nullable=False)
    langsmith_dataset_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    evaluated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=func.now(), nullable=False
    )

    # Relationships
    conversation: Mapped["Conversation | None"] = relationship(
        "Conversation", back_populates="evaluations", lazy="noload"
    )

    def __repr__(self) -> str:
        return f"<Evaluation id={self.id} type={self.eval_type}>"
