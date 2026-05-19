"""Pydantic schemas for Analytics endpoints."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel


class KPIOverviewResponse(BaseModel):
    total_tickets: int
    open_tickets: int
    resolved_tickets: int
    escalated_tickets: int
    resolution_rate: float        # 0.0 – 1.0
    avg_resolution_time_hours: float
    ai_resolution_rate: float     # Resolved by AI without escalation


class TicketVolumePoint(BaseModel):
    date: str                     # ISO date string
    total: int
    resolved: int
    escalated: int


class TicketVolumeResponse(BaseModel):
    data: list[TicketVolumePoint]
    period_days: int


class CategoryBreakdownItem(BaseModel):
    category: str
    count: int
    percentage: float


class SentimentDistributionResponse(BaseModel):
    positive: int
    neutral: int
    negative: int
    angry: int
    total: int


class AgentPerformanceResponse(BaseModel):
    agent_name: str
    total_runs: int
    avg_latency_ms: float
    avg_confidence: float
    error_rate: float
