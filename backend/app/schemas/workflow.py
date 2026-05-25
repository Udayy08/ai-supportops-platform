"""Pydantic schemas for Workflow traces."""

from __future__ import annotations

import uuid
from typing import Any
from datetime import datetime

from pydantic import BaseModel

class WorkflowTraceResponse(BaseModel):
    id: uuid.UUID
    ticket_id: uuid.UUID
    status: str
    nodes_visited: list[str]
    total_latency_ms: int | None
    created_at: datetime
    
    # Detailed fields
    input_state: dict[str, Any]
    output_state: dict[str, Any]
    final_response: str | None
    error_message: str | None

    model_config = {"from_attributes": True}

class WorkflowTraceListResponse(BaseModel):
    items: list[WorkflowTraceResponse]
    total: int
    page: int
    page_size: int
    has_next: bool
