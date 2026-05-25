"""
Workflow Service — orchestrates graph invocation and persists execution records.

This service layer bridges the LangGraph agent pipeline with the existing
database models (WorkflowRun, WorkflowNodeExecution) for full traceability.
"""

from __future__ import annotations

import time
import uuid
from datetime import datetime, timezone
import random
import asyncio
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.agents.graph import build_support_graph
from app.agents.state import SupportState
from app.config import settings
from app.models.workflow import WorkflowRun, WorkflowRunStatus
from app.observability.langsmith_tracer import get_tracer_context, get_run_url
from app.observability.metrics import get_run_metrics


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
            with get_tracer_context() as cb:
                latest_state = dict(initial_state)
                # Stream to capture intermediate states
                for step in self.graph.stream(initial_state):
                    for key, val in step.items():
                        latest_state.update(val)
                
                result = latest_state
                
                # Extract LangSmith details if tracing is enabled
                if cb and cb.latest_run:
                    run_id = str(cb.latest_run.id)
                    result["langsmith_run_id"] = run_id
                    result["langsmith_run_url"] = get_run_url(run_id)
                    
                    # Fetch token metrics
                    metrics = get_run_metrics(run_id)
                    result["metrics"] = metrics
                
            elapsed_ms = int((time.time() - start_time) * 1000)
            result["total_latency_ms"] = elapsed_ms
            
            # ── Evaluation Sampling ───────────────────────────────────────────
            result["queued_for_evaluation"] = False
            if settings.enable_ragas:
                # E.g. sample_percentage=10 means 10% chance
                if random.randint(1, 100) <= settings.evaluation_sample_percentage:
                    result["queued_for_evaluation"] = True
            
            return result
        except Exception as e:
            import traceback
            traceback.print_exc()
            elapsed_ms = int((time.time() - start_time) * 1000)
            
            # Use the latest state we accumulated, so downstream failures don't erase upstream successes
            result = locals().get("latest_state", dict(initial_state))
            
            error_str = str(e).lower()
            if "429" in error_str or "rate limit" in error_str:
                result["failure_type"] = "rate_limit"
                result["provider"] = "groq"
                result["retry_attempts"] = 3  # The max attempts configured in llm.py
            else:
                result["failure_type"] = "execution_error"
                
            result["error"] = str(e)
            result["total_latency_ms"] = elapsed_ms
            result["final_disposition"] = "failed"
            return result

    async def run_async(
        self,
        tenant_id: str,
        customer_message: str,
        ticket_id: str | None = None,
        customer_name: str = "Customer",
    ) -> dict[str, Any]:
        """
        Execute the full agent workflow asynchronously using a background thread.
        This prevents blocking the main FastAPI event loop.
        """
        initial_state = {
            "ticket_id": ticket_id or str(uuid.uuid4()),
            "tenant_id": tenant_id,
            "customer_message": customer_message,
            "customer_name": customer_name,
        }

        run_record = None
        if self.session and ticket_id:
            run_record = WorkflowRun(
                id=uuid.uuid4(),
                tenant_id=uuid.UUID(tenant_id),
                ticket_id=uuid.UUID(ticket_id),
                status=WorkflowRunStatus.RUNNING,
                input_state=dict(initial_state),
                started_at=datetime.now(timezone.utc)
            )
            self.session.add(run_record)
            await self.session.commit()
            
        result = await asyncio.to_thread(
            self.run_sync,
            tenant_id=tenant_id,
            customer_message=customer_message,
            ticket_id=ticket_id,
            customer_name=customer_name,
        )

        if self.session and run_record:
            disposition = result.get("final_disposition")
            if disposition == "auto_resolved":
                status = WorkflowRunStatus.COMPLETED
            elif disposition == "escalated":
                status = WorkflowRunStatus.ESCALATED
            else:
                status = WorkflowRunStatus.FAILED
                
            run_record.status = status
            run_record.output_state = dict(result)
            run_record.nodes_visited = result.get("nodes_visited", [])
            run_record.final_response = result.get("proposed_response")
            run_record.total_latency_ms = result.get("total_latency_ms")
            run_record.error_message = result.get("error")
            run_record.completed_at = datetime.now(timezone.utc)
            
            await self.session.commit()

        return result
