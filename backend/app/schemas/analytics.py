"""Pydantic schemas for Analytics endpoints."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel


class ResolutionAnalytics(BaseModel):
    auto_resolved: int
    escalated: int
    open: int
    closed: int
    human_approved: int
    human_rejected: int

class HallucinationDistribution(BaseModel):
    range_0_0_2: int
    range_0_2_0_4: int
    range_0_4_0_6: int
    range_0_6_0_8: int
    range_0_8_1_0: int

class HighLowTicket(BaseModel):
    id: str
    subject: str
    score: float

class AIQualityAnalytics(BaseModel):
    distribution: HallucinationDistribution
    avg_score: float
    highest_tickets: list[HighLowTicket]
    lowest_tickets: list[HighLowTicket]

class WorkflowPath(BaseModel):
    path: str
    frequency: int

class WorkflowAnalytics(BaseModel):
    most_common_path: str
    paths: list[WorkflowPath]
    avg_nodes: float

class HumanReviewAnalytics(BaseModel):
    approved: int
    rejected: int
    intervention_rate: float

class TimeSeriesPoint(BaseModel):
    date: str
    created: int
    resolved: int
    escalated: int

class TimeBasedAnalytics(BaseModel):
    data: list[TimeSeriesPoint]

class DashboardAnalyticsResponse(BaseModel):
    total_tickets: int
    open_tickets: int
    closed_tickets: int
    escalated_tickets: int
    auto_resolved_tickets: int
    human_reviewed_tickets: int
    resolution_rate: float
    escalation_rate: float
    avg_workflow_latency: float
    avg_hallucination_score: float

    resolution_analytics: ResolutionAnalytics
    ai_quality_analytics: AIQualityAnalytics
    workflow_analytics: WorkflowAnalytics
    human_review_analytics: HumanReviewAnalytics
    time_based_analytics: TimeBasedAnalytics
    
class NodeMetrics(BaseModel):
    id: str
    status: str
    avg_latency_ms: float
    success_rate: float
    volume_processed: int
    custom_metrics: dict[str, Any] = {}

class ArchitectureAnalyticsResponse(BaseModel):
    nodes: dict[str, NodeMetrics]
