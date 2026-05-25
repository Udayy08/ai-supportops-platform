"""Pydantic schemas for Evaluation metrics."""

from __future__ import annotations

from typing import Any
from datetime import datetime
from pydantic import BaseModel

class EvaluationMetricsResponse(BaseModel):
    total_evaluations: int
    avg_faithfulness: float
    avg_answer_relevancy: float
    avg_context_precision: float
    avg_context_recall: float
    period_start: datetime | None = None
    period_end: datetime | None = None

    model_config = {"from_attributes": True}

class RetrievalMetrics(BaseModel):
    avg_latency_ms: float
    median_latency_ms: float
    p95_latency_ms: float
    avg_top1_similarity: float
    avg_top3_similarity: float
    avg_retrieved_chunks: float
    avg_confidence_score: float

class ResolutionMetrics(BaseModel):
    auto_resolution_rate: float
    escalation_rate: float
    avg_hallucination_score: float
    avg_processing_time_ms: float

class DocumentAnalytics(BaseModel):
    document_id: str | None = None
    filename: str
    retrieval_count: int
    avg_similarity: float
    avg_rank: float
    auto_resolution_contribution: int
    escalation_contribution: int
    last_retrieved_at: str | None = None
    days_since_last_retrieval: int | None = None

class FailureAnalytics(BaseModel):
    no_source_count: int
    no_source_percent: float
    low_similarity_count: int
    low_similarity_percent: float
    hallucination_escalation_count: int
    hallucination_escalation_percent: float
    human_review_escalation_count: int
    human_review_escalation_percent: float
    confidence_escalation_count: int
    confidence_escalation_percent: float

class RetrievalEvaluationResponse(BaseModel):
    retrieval_health_score: float
    retrieval_metrics: RetrievalMetrics
    resolution_metrics: ResolutionMetrics
    most_retrieved_documents: list[DocumentAnalytics]
    least_retrieved_documents: list[DocumentAnalytics]
    never_retrieved_documents: list[DocumentAnalytics]
    failure_analytics: FailureAnalytics

class TrendPoint(BaseModel):
    date: str
    retrieval_health_score: float
    avg_latency_ms: float
    avg_similarity: float
    hallucination_score: float
    auto_resolution_rate: float
    escalation_rate: float

class RetrievalTrendsResponse(BaseModel):
    trends: list[TrendPoint]
