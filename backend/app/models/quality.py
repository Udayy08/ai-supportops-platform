"""
HallucinationFlag model — quality gate that records when an AI response
fails grounding checks (source attribution, factual consistency).

ConfidenceScore model — granular per-message, per-agent numeric confidence
with breakdown dimensions (retrieval, generation, overall).

These two models power the Hallucination Rate and Confidence KPIs on the
analytics dashboard.

Indexes:
  - (workflow_run_id)           : all flags in a run
  - (message_id)                : flags on a specific AI message
  - (tenant_id, flagged_at)     : time-series hallucination trend
  - (node_execution_id)         : confidence per node
"""

from __future__ import annotations

import enum
import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, Enum, Float, ForeignKey, Index, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TenantMixin, UUIDPrimaryKeyMixin


class HallucinationSeverity(str, enum.Enum):
    LOW = "low"           # Minor inaccuracy, still usable
    MEDIUM = "medium"     # Significant inaccuracy, needs review
    HIGH = "high"         # Completely fabricated / dangerous


class HallucinationFlag(UUIDPrimaryKeyMixin, TenantMixin, Base):
    """
    Raised by the Quality Agent when an AI response fails grounding.
    Records the exact claim, the evidence checked, and the severity.
    """

    __tablename__ = "hallucination_flags"

    __table_args__ = (
        Index("ix_hall_flags_tenant_flagged", "tenant_id", "flagged_at"),
        Index("ix_hall_flags_run", "workflow_run_id"),
        Index("ix_hall_flags_message", "message_id"),
    )

    workflow_run_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("workflow_runs.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    message_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("messages.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    severity: Mapped[HallucinationSeverity] = mapped_column(
        Enum(HallucinationSeverity, name="hallucination_severity"),
        nullable=False,
        index=True,
    )

    # The specific claim that failed grounding
    flagged_claim: Mapped[str] = mapped_column(Text, nullable=False)
    # Detection method: "ragas_faithfulness", "source_check", "manual", etc.
    detection_method: Mapped[str] = mapped_column(String(100), nullable=False)
    # Score that triggered the flag (0.0–1.0; lower = worse)
    faithfulness_score: Mapped[float | None] = mapped_column(Float, nullable=True)

    # Source documents that were checked (list of {id, title, relevance})
    evidence_checked: Mapped[list] = mapped_column(JSONB, default=list, nullable=False)
    # Additional context (model, temperature, prompt hash, etc.)
    detection_metadata: Mapped[dict] = mapped_column(JSONB, default=dict, nullable=False)

    # Whether a human reviewer resolved / dismissed this flag
    is_resolved: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    resolved_by: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    resolution_notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    resolved_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    flagged_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )

    # ── Relationships ────────────────────────────────────────────────────────
    workflow_run: Mapped["WorkflowRun"] = relationship(
        "WorkflowRun", back_populates="hallucination_flags", lazy="noload"
    )
    message: Mapped["Message | None"] = relationship(
        "Message", back_populates="hallucination_flags", lazy="noload"
    )

    def __repr__(self) -> str:
        return (
            f"<HallucinationFlag id={self.id} severity={self.severity} "
            f"resolved={self.is_resolved}>"
        )


class ConfidenceScore(UUIDPrimaryKeyMixin, Base):
    """
    Records granular confidence measurements for each node execution.
    Multiple dimensions are stored to power detailed quality analytics.
    """

    __tablename__ = "confidence_scores"

    __table_args__ = (
        Index("ix_conf_scores_node_exec", "node_execution_id"),
        Index("ix_conf_scores_message", "message_id"),
    )

    node_execution_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("workflow_node_executions.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    message_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("messages.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    # Overall composite confidence (0.0–1.0)
    overall_score: Mapped[float] = mapped_column(Float, nullable=False)

    # Dimension breakdowns
    retrieval_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    generation_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    relevancy_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    faithfulness_score: Mapped[float | None] = mapped_column(Float, nullable=True)

    # Whether overall_score crossed the escalation threshold
    is_below_threshold: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    threshold_used: Mapped[float | None] = mapped_column(Float, nullable=True)

    # Stores raw model logprobs, calibration metadata, etc.
    score_metadata: Mapped[dict] = mapped_column(JSONB, default=dict, nullable=False)

    # ── Relationships ────────────────────────────────────────────────────────
    node_execution: Mapped["WorkflowNodeExecution"] = relationship(
        "WorkflowNodeExecution", back_populates="confidence_scores", lazy="noload"
    )
    message: Mapped["Message | None"] = relationship(
        "Message", back_populates="confidence_scores", lazy="noload"
    )

    def __repr__(self) -> str:
        return f"<ConfidenceScore overall={self.overall_score:.3f} below_threshold={self.is_below_threshold}>"
