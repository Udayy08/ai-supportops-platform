"""Pydantic schemas for Agent Config and Evaluation endpoints."""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field

from app.models.evaluation import EvalType


# ── Agent Config Schemas ──────────────────────────────────────────────────────

class AgentConfigResponse(BaseModel):
    id: uuid.UUID
    tenant_id: uuid.UUID
    agent_name: str
    model_name: str
    prompt_config: dict[str, Any]
    tool_config: dict[str, Any]
    is_active: bool
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class AgentConfigUpdateRequest(BaseModel):
    model_name: str | None = None
    prompt_config: dict[str, Any] | None = None
    tool_config: dict[str, Any] | None = None
    is_active: bool | None = None


# ── Evaluation Schemas ────────────────────────────────────────────────────────

class EvaluationRunRequest(BaseModel):
    conversation_ids: list[uuid.UUID] | None = None  # None = last 24h
    eval_type: EvalType = EvalType.RAGAS


class EvaluationResponse(BaseModel):
    id: uuid.UUID
    tenant_id: uuid.UUID
    conversation_id: uuid.UUID | None
    eval_type: EvalType
    scores: dict[str, float]
    dataset_info: dict[str, Any]
    langsmith_dataset_id: str | None
    evaluated_at: datetime

    model_config = {"from_attributes": True}


class EvaluationMetricsSummary(BaseModel):
    avg_faithfulness: float
    avg_answer_relevancy: float
    avg_context_relevancy: float
    avg_context_precision: float
    total_evaluations: int
    period_days: int
