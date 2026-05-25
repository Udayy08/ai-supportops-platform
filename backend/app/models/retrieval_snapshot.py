"""
Retrieval Evaluation Snapshot model — stores persistent historical aggregations
of retrieval performance to establish baselines before optimizations.
"""

from __future__ import annotations

from datetime import date

from sqlalchemy import Date, Float, Index
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TenantMixin, UUIDPrimaryKeyMixin


class RetrievalEvaluationSnapshot(UUIDPrimaryKeyMixin, TenantMixin, Base):
    __tablename__ = "retrieval_evaluation_snapshots"

    __table_args__ = (
        Index("ix_retrieval_eval_snapshots_tenant_date", "tenant_id", "snapshot_date", unique=True),
    )

    snapshot_date: Mapped[date] = mapped_column(Date, nullable=False)

    avg_similarity: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    avg_top1_similarity: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    avg_top3_similarity: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    
    avg_latency: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    
    auto_resolution_rate: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    escalation_rate: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    hallucination_score: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    
    retrieval_health_score: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)

    def __repr__(self) -> str:
        return f"<RetrievalEvaluationSnapshot date={self.snapshot_date} health={self.retrieval_health_score}>"
