"""
WorkflowRun model — tracks a complete LangGraph agent pipeline execution.
WorkflowNodeExecution model — tracks each individual agent node within a run.

One Ticket → many WorkflowRuns (re-runs, retries)
One WorkflowRun → many WorkflowNodeExecutions (one per agent node)

Indexes:
  - (tenant_id, ticket_id)      : all runs for a ticket
  - (tenant_id, status)         : filter failed/running runs
  - (tenant_id, started_at)     : time-series view
  - (workflow_run_id, node_name): trace a node within a run
"""

from __future__ import annotations

import enum
import uuid
from datetime import datetime

from sqlalchemy import DateTime, Enum, Float, ForeignKey, Index, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TenantMixin, TimestampMixin, UUIDPrimaryKeyMixin


class WorkflowRunStatus(str, enum.Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    ESCALATED = "escalated"
    CANCELLED = "cancelled"


class NodeStatus(str, enum.Enum):
    SKIPPED = "skipped"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


class WorkflowRun(UUIDPrimaryKeyMixin, TenantMixin, Base):
    """
    Represents a single end-to-end invocation of the LangGraph pipeline
    for a ticket. A ticket can have multiple runs (retries, re-processing).
    """

    __tablename__ = "workflow_runs"

    __table_args__ = (
        Index("ix_workflow_runs_tenant_ticket", "tenant_id", "ticket_id"),
        Index("ix_workflow_runs_tenant_status", "tenant_id", "status"),
        Index("ix_workflow_runs_tenant_started", "tenant_id", "started_at"),
    )

    ticket_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("tickets.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    conversation_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("conversations.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    status: Mapped[WorkflowRunStatus] = mapped_column(
        Enum(WorkflowRunStatus, name="workflow_run_status"),
        default=WorkflowRunStatus.PENDING,
        nullable=False,
        index=True,
    )

    # LangSmith trace IDs for deep observability
    langsmith_run_id: Mapped[str | None] = mapped_column(String(255), nullable=True, index=True)
    langsmith_trace_url: Mapped[str | None] = mapped_column(String(500), nullable=True)

    # Graph input/output snapshots for replay/debugging
    input_state: Mapped[dict] = mapped_column(JSONB, default=dict, nullable=False)
    output_state: Mapped[dict] = mapped_column(JSONB, default=dict, nullable=False)

    # Ordered list of node names visited (e.g. ["classifier","sentiment","resolver"])
    nodes_visited: Mapped[list] = mapped_column(JSONB, default=list, nullable=False)

    # Final resolution produced by the workflow
    final_response: Mapped[str | None] = mapped_column(Text, nullable=True)
    resolution_source: Mapped[str | None] = mapped_column(
        String(50), nullable=True
    )  # "ai", "human", "escalated"

    # Aggregate metrics
    total_latency_ms: Mapped[int | None] = mapped_column(Integer, nullable=True)
    total_tokens_used: Mapped[int | None] = mapped_column(Integer, nullable=True)
    total_cost_usd: Mapped[float | None] = mapped_column(Float, nullable=True)

    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)

    started_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )
    completed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    # ── Relationships ────────────────────────────────────────────────────────
    ticket: Mapped["Ticket"] = relationship(
        "Ticket", back_populates="workflow_runs", lazy="noload"
    )
    conversation: Mapped["Conversation | None"] = relationship(
        "Conversation", back_populates="workflow_runs", lazy="noload"
    )
    node_executions: Mapped[list["WorkflowNodeExecution"]] = relationship(
        "WorkflowNodeExecution",
        back_populates="workflow_run",
        lazy="noload",
        cascade="all, delete-orphan",
        order_by="WorkflowNodeExecution.sequence_order",
    )
    hallucination_flags: Mapped[list["HallucinationFlag"]] = relationship(
        "HallucinationFlag", back_populates="workflow_run", lazy="noload"
    )

    def __repr__(self) -> str:
        return f"<WorkflowRun id={self.id} ticket={self.ticket_id} status={self.status}>"


class WorkflowNodeExecution(UUIDPrimaryKeyMixin, Base):
    """
    Per-agent-node execution record within a WorkflowRun.
    One row = one agent node invocation (classifier, sentiment, retriever, etc.)
    """

    __tablename__ = "workflow_node_executions"

    __table_args__ = (
        Index("ix_node_exec_run_node", "workflow_run_id", "node_name"),
        Index("ix_node_exec_run_sequence", "workflow_run_id", "sequence_order"),
    )

    workflow_run_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("workflow_runs.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # LangGraph node identifier
    node_name: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    sequence_order: Mapped[int] = mapped_column(Integer, nullable=False)

    status: Mapped[NodeStatus] = mapped_column(
        Enum(NodeStatus, name="node_status"),
        default=NodeStatus.RUNNING,
        nullable=False,
    )

    # Raw input/output at this node for replay + debugging
    input_data: Mapped[dict] = mapped_column(JSONB, default=dict, nullable=False)
    output_data: Mapped[dict] = mapped_column(JSONB, default=dict, nullable=False)

    # LLM usage for this specific node
    model_name: Mapped[str | None] = mapped_column(String(100), nullable=True)
    prompt_tokens: Mapped[int | None] = mapped_column(Integer, nullable=True)
    completion_tokens: Mapped[int | None] = mapped_column(Integer, nullable=True)
    latency_ms: Mapped[int | None] = mapped_column(Integer, nullable=True)
    cost_usd: Mapped[float | None] = mapped_column(Float, nullable=True)

    # Node-level confidence (from the agent's own self-assessment)
    confidence: Mapped[float | None] = mapped_column(Float, nullable=True)

    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)

    started_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )
    completed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    # ── Relationships ────────────────────────────────────────────────────────
    workflow_run: Mapped["WorkflowRun"] = relationship(
        "WorkflowRun", back_populates="node_executions", lazy="noload"
    )
    confidence_scores: Mapped[list["ConfidenceScore"]] = relationship(
        "ConfidenceScore", back_populates="node_execution", lazy="noload"
    )

    def __repr__(self) -> str:
        return (
            f"<WorkflowNodeExecution node={self.node_name!r} "
            f"seq={self.sequence_order} status={self.status}>"
        )
