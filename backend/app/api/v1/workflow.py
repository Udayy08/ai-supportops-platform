"""Workflow routes — fetching LangSmith traces and workflow execution logs."""

from __future__ import annotations

import uuid
from typing import Any

from fastapi import APIRouter, Query

from app.api.deps import CurrentUser, DBSession, Pagination
from app.schemas.workflow import WorkflowTraceListResponse, WorkflowTraceResponse

router = APIRouter(prefix="/workflow", tags=["Workflow"])

from sqlalchemy import select, func
from app.models.workflow import WorkflowRun

@router.get(
    "/traces",
    response_model=WorkflowTraceListResponse,
    summary="List LangGraph workflow traces",
    description="Returns a paginated list of workflow executions including metadata."
)
async def list_traces(
    current_user: CurrentUser,
    db: DBSession,
    pagination: Pagination,
) -> WorkflowTraceListResponse:
    # Build query
    query = select(WorkflowRun).where(
        WorkflowRun.tenant_id == current_user.tenant_id
    ).order_by(WorkflowRun.started_at.desc())

    # Get total count
    count_query = select(func.count()).select_from(query.subquery())
    total = await db.scalar(count_query) or 0

    # Get paginated items
    paginated_query = query.offset(pagination.offset).limit(pagination.page_size)
    result = await db.execute(paginated_query)
    traces = result.scalars().all()

    # Map to response schema. Note that started_at maps to created_at in schema.
    items = []
    for t in traces:
        items.append(WorkflowTraceResponse(
            id=t.id,
            ticket_id=t.ticket_id,
            status=t.status.value if t.status else "unknown",
            nodes_visited=t.nodes_visited,
            total_latency_ms=t.total_latency_ms,
            created_at=t.started_at,
            input_state=t.input_state,
            output_state=t.output_state,
            final_response=t.final_response,
            error_message=t.error_message,
        ))

    return WorkflowTraceListResponse(
        items=items,
        total=total,
        page=pagination.page,
        page_size=pagination.page_size,
        has_next=(pagination.page * pagination.page_size) < total
    )

@router.get(
    "/traces/{trace_id}",
    response_model=WorkflowTraceResponse,
    summary="Get workflow trace details",
)
async def get_trace(
    trace_id: uuid.UUID,
    current_user: CurrentUser,
    db: DBSession,
) -> WorkflowTraceResponse:
    query = select(WorkflowRun).where(
        WorkflowRun.id == trace_id,
        WorkflowRun.tenant_id == current_user.tenant_id
    )
    result = await db.execute(query)
    t = result.scalar_one_or_none()
    
    from app.core.exceptions import NotFoundException
    if not t:
        raise NotFoundException(detail="Trace not found.")
        
    return WorkflowTraceResponse(
        id=t.id,
        ticket_id=t.ticket_id,
        status=t.status.value if t.status else "unknown",
        nodes_visited=t.nodes_visited,
        total_latency_ms=t.total_latency_ms,
        created_at=t.started_at,
        input_state=t.input_state,
        output_state=t.output_state,
        final_response=t.final_response,
        error_message=t.error_message,
    )
