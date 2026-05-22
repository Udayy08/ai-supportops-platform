"""Pydantic schemas for Workflow traces."""

from __future__ import annotations

import uuid
from typing import Any
from datetime import datetime

from pydantic import BaseModel

class WorkflowTraceResponse(BaseModel):
    id: uuid.UUID
    langsmith_run_id: str | None
    langsmith_run_url: str | None
    total_latency_ms: int
    tokens_used: int
    nodes_visited: list[str]
    created_at: datetime

    model_config = {"from_attributes": True}

class WorkflowTraceListResponse(BaseModel):
    items: list[WorkflowTraceResponse]
    total: int
    page: int
    page_size: int
    has_next: bool
