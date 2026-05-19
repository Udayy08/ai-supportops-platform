"""
TicketAnalyticsSnapshot model — pre-aggregated daily stats per tenant.

Instead of running expensive COUNT/AVG queries on the tickets table at
dashboard load time, a nightly job materializes this snapshot table.
The analytics API reads from here — O(1) queries regardless of ticket volume.

Indexes:
  - (tenant_id, snapshot_date)  : primary lookup (unique constraint)
  - (tenant_id)                 : list all snapshots for a tenant
"""

from __future__ import annotations

import uuid
from datetime import date, datetime

from sqlalchemy import Date, DateTime, Float, ForeignKey, Index, Integer, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TenantMixin, UUIDPrimaryKeyMixin


class TicketAnalyticsSnapshot(UUIDPrimaryKeyMixin, TenantMixin, Base):
    """
    Daily materialized snapshot of ticket and AI quality metrics per tenant.
    One row per (tenant_id, snapshot_date).
    """

    __tablename__ = "ticket_analytics_snapshots"

    __table_args__ = (
        UniqueConstraint("tenant_id", "snapshot_date", name="uq_analytics_tenant_date"),
        Index("ix_analytics_tenant_date", "tenant_id", "snapshot_date"),
    )

    snapshot_date: Mapped[date] = mapped_column(Date, nullable=False, index=True)

    # ── Ticket volume ────────────────────────────────────────────────────────
    total_tickets: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    new_tickets: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    open_tickets: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    resolved_tickets: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    escalated_tickets: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    closed_tickets: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    # ── Resolution metrics ───────────────────────────────────────────────────
    ai_resolved_tickets: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    human_resolved_tickets: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    avg_resolution_time_hours: Mapped[float | None] = mapped_column(Float, nullable=True)
    avg_first_response_time_hours: Mapped[float | None] = mapped_column(Float, nullable=True)
    resolution_rate: Mapped[float | None] = mapped_column(Float, nullable=True)  # 0–1
    ai_resolution_rate: Mapped[float | None] = mapped_column(Float, nullable=True)  # 0–1

    # ── AI quality metrics ───────────────────────────────────────────────────
    avg_confidence_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    hallucination_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    hallucination_rate: Mapped[float | None] = mapped_column(Float, nullable=True)  # 0–1
    avg_faithfulness_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    avg_answer_relevancy: Mapped[float | None] = mapped_column(Float, nullable=True)

    # ── Workflow metrics ─────────────────────────────────────────────────────
    total_workflow_runs: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    failed_workflow_runs: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    avg_workflow_latency_ms: Mapped[float | None] = mapped_column(Float, nullable=True)
    total_tokens_used: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    total_cost_usd: Mapped[float | None] = mapped_column(Float, nullable=True)

    # ── Approval metrics ─────────────────────────────────────────────────────
    pending_approvals: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    approved_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    rejected_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    avg_approval_time_minutes: Mapped[float | None] = mapped_column(Float, nullable=True)

    # ── Sentiment breakdown ──────────────────────────────────────────────────
    sentiment_positive: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    sentiment_neutral: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    sentiment_negative: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    sentiment_angry: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    # ── Category breakdown (JSONB: {"billing": 12, "technical": 8, ...}) ────
    category_breakdown: Mapped[dict] = mapped_column(JSONB, default=dict, nullable=False)
    # ── Source breakdown (JSONB: {"email": 5, "slack": 3, ...}) ─────────────
    source_breakdown: Mapped[dict] = mapped_column(JSONB, default=dict, nullable=False)
    # ── Per-agent performance (JSONB keyed by agent_name) ───────────────────
    agent_performance: Mapped[dict] = mapped_column(JSONB, default=dict, nullable=False)

    computed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )

    def __repr__(self) -> str:
        return (
            f"<TicketAnalyticsSnapshot tenant={self.tenant_id} "
            f"date={self.snapshot_date} tickets={self.total_tickets}>"
        )
