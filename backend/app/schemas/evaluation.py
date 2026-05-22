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
