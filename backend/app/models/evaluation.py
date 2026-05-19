"""
Evaluation model — stores RAGAS and custom LLM quality metric results
per conversation or per workflow run.

Indexes:
  - (tenant_id, eval_type)      : filter RAGAS vs custom vs manual runs
  - (tenant_id, evaluated_at)   : time-series evaluation trend
  - (conversation_id)           : evaluations for a conversation
"""

from __future__ import annotations

import enum
import uuid
from datetime import datetime

from sqlalchemy import DateTime, Enum, Float, ForeignKey, Index, String
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TenantMixin, UUIDPrimaryKeyMixin


class EvalType(str, enum.Enum):
    RAGAS = "ragas"
    CUSTOM = "custom"
    MANUAL = "manual"


class Evaluation(UUIDPrimaryKeyMixin, TenantMixin, Base):
    __tablename__ = "evaluations"

    __table_args__ = (
        Index("ix_evaluations_tenant_type", "tenant_id", "eval_type"),
        Index("ix_evaluations_tenant_date", "tenant_id", "evaluated_at"),
        Index("ix_evaluations_conversation", "conversation_id"),
    )

    conversation_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("conversations.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    workflow_run_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("workflow_runs.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    eval_type: Mapped[EvalType] = mapped_column(
        Enum(EvalType, name="eval_type"),
        nullable=False,
        index=True,
    )

    # RAGAS metric scores: faithfulness, answer_relevancy, context_relevancy,
    # context_precision, context_recall, answer_correctness
    scores: Mapped[dict] = mapped_column(JSONB, default=dict, nullable=False)

    # Convenience columns for the most important RAGAS metrics
    # (avoids JSON parsing for simple aggregate queries)
    faithfulness: Mapped[float | None] = mapped_column(Float, nullable=True)
    answer_relevancy: Mapped[float | None] = mapped_column(Float, nullable=True)
    context_precision: Mapped[float | None] = mapped_column(Float, nullable=True)
    context_recall: Mapped[float | None] = mapped_column(Float, nullable=True)

    # The evaluation dataset: {question, ground_truth, answer, contexts}
    dataset_info: Mapped[dict] = mapped_column(JSONB, default=dict, nullable=False)

    # LangSmith dataset IDs for traceability
    langsmith_dataset_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    langsmith_experiment_id: Mapped[str | None] = mapped_column(String(255), nullable=True)

    evaluated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )

    # ── Relationships ────────────────────────────────────────────────────────
    conversation: Mapped["Conversation | None"] = relationship(
        "Conversation", back_populates="evaluations", lazy="noload"
    )

    def __repr__(self) -> str:
        return f"<Evaluation id={self.id} type={self.eval_type} faithful={self.faithfulness}>"
