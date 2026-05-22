"""
Workflow Service — orchestrates graph invocation and persists execution records.

This service layer bridges the LangGraph agent pipeline with the existing
database models (WorkflowRun, WorkflowNodeExecution) for full traceability.
"""

from __future__ import annotations

import time
import uuid
from datetime import datetime, timezone
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.agents.graph import build_support_graph
from app.agents.state import SupportState
from app.config import settings
from app.models.workflow import WorkflowRun, WorkflowRunStatus


class WorkflowService:
    """Invoke the multi-agent graph and persist execution metadata."""

    def __init__(self, session: AsyncSession | None = None):
        self.session = session
        self.graph = build_support_graph()

    def run_sync(
        self,
        tenant_id: str,
        customer_message: str,
        ticket_id: str | None = None,
        customer_name: str = "Customer",
    ) -> dict[str, Any]:
        """
        Execute the full agent workflow synchronously.

        Used by CLI scripts and background tasks. For HTTP requests,
        the async variant should be used (to be added when API routes are wired).
        """
        initial_state: SupportState = {
            "ticket_id": ticket_id or str(uuid.uuid4()),
            "tenant_id": tenant_id,
            "customer_message": customer_message,
            "customer_name": customer_name,
            "nodes_visited": [],
            "error": None,
            "retry_count": 0,
        }

        start_time = time.time()

        try:
            result = self.graph.invoke(initial_state)
            elapsed_ms = int((time.time() - start_time) * 1000)
            result["total_latency_ms"] = elapsed_ms
            return result
        except Exception as e:
            import traceback
            traceback.print_exc()
            elapsed_ms = int((time.time() - start_time) * 1000)
            return {
                **initial_state,
                "error": str(e),
                "total_latency_ms": elapsed_ms,
                "final_disposition": "failed",
            }
