"""Ticket routes — full CRUD with pagination, filtering, and agent workflow trigger."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, Query, status, BackgroundTasks

from app.api.deps import CurrentUser, DBSession, Pagination
from app.core.exceptions import ForbiddenException, NotFoundException
from app.core.logging import get_logger
from app.db.repositories.ticket_repo import TicketRepository
from app.models.ticket import TicketPriority, TicketStatus
from app.schemas.ticket import (
    TicketCreateRequest,
    TicketListResponse,
    TicketResponse,
    TicketUpdateRequest,
    TicketProcessRequest,
    HumanReviewRequest,
)
from app.services.workflow_service import WorkflowService
from app.db.session import get_session_factory

router = APIRouter(prefix="/tickets", tags=["Tickets"])
logger = get_logger(__name__)

# ── Disposition → TicketStatus mapping ───────────────────────────────────────
# These are the EXACT strings emitted by graph.py / human_approval.py.
_DISPOSITION_STATUS_MAP: dict[str, TicketStatus] = {
    "auto_resolved": TicketStatus.CLOSED,
    "escalated":     TicketStatus.ESCALATED,
    "failed":        TicketStatus.OPEN,      # reopen so it can be retried
}


async def run_workflow_background(
    tenant_id: str,
    ticket_id: str,
    customer_message: str,
    customer_name: str,
) -> None:
    """
    Background task: run the LangGraph workflow and persist all outputs.

    Lifecycle:
      1. Mark ticket IN_PROGRESS
      2. Run workflow (in a thread via run_async)
      3. Map final_disposition → TicketStatus
      4. Persist AI outputs (confidence, sentiment, category, response)
      5. Update ticket status and commit
    """
    SessionLocal = get_session_factory()
    async with SessionLocal() as session:
        repo = TicketRepository(session)

        # ── Step 1: Mark IN_PROGRESS so the UI shows activity ─────────────────
        ticket = await repo.get_by_id(
            uuid.UUID(ticket_id), tenant_id=uuid.UUID(tenant_id)
        )
        if not ticket:
            logger.error(
                "workflow_ticket_not_found",
                ticket_id=ticket_id,
                tenant_id=tenant_id,
            )
            return

        await repo.update(ticket, status=TicketStatus.IN_PROGRESS)
        await session.commit()

        logger.info(
            "workflow_started",
            ticket_id=ticket_id,
            tenant_id=tenant_id,
            customer_message_length=len(customer_message),
        )

        # ── Step 2: Run the LangGraph workflow ────────────────────────────────
        try:
            service = WorkflowService(session=session)
            result: dict = await service.run_async(
                tenant_id=tenant_id,
                ticket_id=ticket_id,
                customer_message=customer_message,
                customer_name=customer_name,
            )
        except Exception as exc:  # noqa: BLE001
            logger.exception(
                "workflow_crashed",
                ticket_id=ticket_id,
                error=str(exc),
            )
            # Reopen the ticket so it is not stuck in IN_PROGRESS
            ticket = await repo.get_by_id(
                uuid.UUID(ticket_id), tenant_id=uuid.UUID(tenant_id)
            )
            if ticket:
                await repo.update(ticket, status=TicketStatus.OPEN)
                await session.commit()
            return

        # ── Step 3: Extract workflow outputs ──────────────────────────────────
        disposition: str = result.get("final_disposition", "failed")
        confidence: float | None = result.get("overall_confidence")
        hallucination: float | None = result.get("hallucination_score")
        sentiment: str | None = result.get("sentiment")
        category: str | None = result.get("category")
        proposed_response: str | None = result.get("proposed_response")
        latency_ms: int | None = result.get("total_latency_ms")
        error: str | None = result.get("error")
        nodes_visited: list = result.get("nodes_visited", [])
        retrieval_debug: dict | None = result.get("retrieval_debug")

        logger.info(
            "workflow_completed",
            ticket_id=ticket_id,
            tenant_id=tenant_id,
            final_disposition=disposition,
            confidence_score=confidence,
            hallucination_score=hallucination,
            sentiment=sentiment,
            category=category,
            latency_ms=latency_ms,
            nodes_visited=nodes_visited,
            error=error,
        )

        # ── Step 4: Map disposition → TicketStatus ────────────────────────────
        new_status: TicketStatus = _DISPOSITION_STATUS_MAP.get(
            disposition, TicketStatus.OPEN
        )

        if disposition not in _DISPOSITION_STATUS_MAP:
            logger.warning(
                "workflow_unknown_disposition",
                ticket_id=ticket_id,
                disposition=disposition,
                fallback_status=new_status.value,
            )

        # ── Step 5: Persist AI outputs + update status ────────────────────────
        # Re-fetch within the same session to avoid stale state after run_async
        ticket = await repo.get_by_id(
            uuid.UUID(ticket_id), tenant_id=uuid.UUID(tenant_id)
        )
        if not ticket:
            logger.error(
                "workflow_ticket_missing_after_run",
                ticket_id=ticket_id,
            )
            return

        update_kwargs: dict = {"status": new_status}

        if confidence is not None:
            update_kwargs["ai_confidence"] = round(confidence, 4)
        if sentiment is not None:
            update_kwargs["ai_sentiment"] = sentiment
        if category is not None:
            update_kwargs["ai_category"] = category
        if new_status == TicketStatus.CLOSED:
            update_kwargs["resolved_at"] = datetime.now(tz=timezone.utc)

        # Store proposed response and workflow metadata in the flexible JSONB field
        metadata_patch: dict = {
            "workflow_final_disposition": disposition,
            "workflow_latency_ms": latency_ms,
            "nodes_visited": nodes_visited,
            "hallucination_score": hallucination,
        }
        if retrieval_debug:
            metadata_patch["retrieval_debug"] = retrieval_debug
            if "documents" in retrieval_debug:
                metadata_patch["sources_used"] = retrieval_debug["documents"]
        if proposed_response:
            metadata_patch["ai_proposed_response"] = proposed_response
        if error:
            metadata_patch["workflow_error"] = error
            if "failure_type" in result:
                metadata_patch["failure_type"] = result["failure_type"]
            if "provider" in result:
                metadata_patch["provider"] = result["provider"]
            if "retry_attempts" in result:
                metadata_patch["retry_attempts"] = result["retry_attempts"]

        existing_metadata: dict = ticket.metadata_ or {}
        update_kwargs["metadata_"] = {**existing_metadata, **metadata_patch}

        await repo.update(ticket, **update_kwargs)
        await session.commit()

        logger.info(
            "ticket_status_updated",
            ticket_id=ticket_id,
            old_status=TicketStatus.IN_PROGRESS.value,
            new_status=new_status.value,
            disposition=disposition,
        )


@router.get("", response_model=TicketListResponse, summary="List tickets (paginated + filtered)")
async def list_tickets(
    current_user: CurrentUser,
    db: DBSession,
    pagination: Pagination,
    status: TicketStatus | None = Query(None),
    priority: TicketPriority | None = Query(None),
    category: str | None = Query(None),
    assigned_to: uuid.UUID | None = Query(None),
    search: str | None = Query(None, description="Full-text search on subject/description"),
) -> TicketListResponse:
    repo = TicketRepository(db)
    tickets, total = await repo.list_paginated(
        tenant_id=current_user.tenant_id,
        page=pagination.page,
        page_size=pagination.page_size,
        status=status,
        priority=priority,
        category=category,
        assigned_to=assigned_to,
        search=search,
    )
    return TicketListResponse(
        items=[TicketResponse.model_validate(t) for t in tickets],
        total=total,
        page=pagination.page,
        page_size=pagination.page_size,
        has_next=(pagination.page * pagination.page_size) < total,
    )


@router.post(
    "",
    response_model=TicketResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create ticket (triggers agent workflow)",
)
async def create_ticket(
    body: TicketCreateRequest,
    current_user: CurrentUser,
    db: DBSession,
) -> TicketResponse:
    repo = TicketRepository(db)
    ticket = await repo.create(
        tenant_id=current_user.tenant_id,
        created_by=current_user.id,
        **body.model_dump(),
    )
    
    return TicketResponse.model_validate(ticket)

@router.post(
    "/process",
    response_model=dict,
    status_code=status.HTTP_202_ACCEPTED,
    summary="Process ticket manually (triggers agent workflow)",
    description="Queues a ticket for asynchronous AI processing."
)
async def process_ticket(
    body: TicketProcessRequest,
    background_tasks: BackgroundTasks,
    current_user: CurrentUser,
    db: DBSession,
) -> dict:
    repo = TicketRepository(db)
    ticket = await repo.get_by_id(body.ticket_id, tenant_id=current_user.tenant_id)
    if not ticket:
        raise NotFoundException(detail=f"Ticket '{body.ticket_id}' not found.")
        
    message = body.additional_context or ticket.description
    
    background_tasks.add_task(
        run_workflow_background,
        tenant_id=str(current_user.tenant_id),
        ticket_id=str(ticket.id),
        customer_message=message,
        customer_name="Customer"
    )
    
    return {"status": "accepted", "ticket_id": str(ticket.id), "message": "Workflow queued."}


@router.get("/{ticket_id}", response_model=TicketResponse, summary="Get ticket by ID")
async def get_ticket(
    ticket_id: uuid.UUID,
    current_user: CurrentUser,
    db: DBSession,
) -> TicketResponse:
    repo = TicketRepository(db)
    ticket = await repo.get_by_id(ticket_id, tenant_id=current_user.tenant_id)
    if not ticket:
        raise NotFoundException(detail=f"Ticket '{ticket_id}' not found.")
    return TicketResponse.model_validate(ticket)


@router.patch("/{ticket_id}", response_model=TicketResponse, summary="Update ticket")
async def update_ticket(
    ticket_id: uuid.UUID,
    body: TicketUpdateRequest,
    current_user: CurrentUser,
    db: DBSession,
) -> TicketResponse:
    repo = TicketRepository(db)
    ticket = await repo.get_by_id(ticket_id, tenant_id=current_user.tenant_id)
    if not ticket:
        raise NotFoundException(detail=f"Ticket '{ticket_id}' not found.")

    updated = await repo.update(ticket, **body.model_dump(exclude_none=True))
    return TicketResponse.model_validate(updated)


@router.delete(
    "/{ticket_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Soft-delete ticket (sets status to closed)",
)
async def delete_ticket(
    ticket_id: uuid.UUID,
    current_user: CurrentUser,
    db: DBSession,
) -> None:
    from app.models.user import UserRole
    if current_user.role not in (UserRole.ADMIN, UserRole.AGENT):
        raise ForbiddenException(detail="Only admins and agents can delete tickets.")

    repo = TicketRepository(db)
    ticket = await repo.get_by_id(ticket_id, tenant_id=current_user.tenant_id)
    if not ticket:
        raise NotFoundException(detail=f"Ticket '{ticket_id}' not found.")

    await repo.update(ticket, status=TicketStatus.CLOSED)


@router.post(
    "/{ticket_id}/human-review",
    response_model=TicketResponse,
    summary="Submit human review decision",
    description="Resolves an escalated ticket by approving or rejecting the AI's proposal."
)
async def human_review_ticket(
    ticket_id: uuid.UUID,
    body: HumanReviewRequest,
    current_user: CurrentUser,
    db: DBSession,
) -> TicketResponse:
    from app.models.user import UserRole
    if current_user.role not in (UserRole.ADMIN, UserRole.AGENT):
        raise ForbiddenException(detail="Only admins and agents can review tickets.")

    repo = TicketRepository(db)
    ticket = await repo.get_by_id(ticket_id, tenant_id=current_user.tenant_id)
    if not ticket:
        raise NotFoundException(detail=f"Ticket '{ticket_id}' not found.")

    if ticket.status != TicketStatus.ESCALATED:
        # In a real app we might return 400 Bad Request if it's not escalated
        pass

    new_status = TicketStatus.CLOSED if body.approval_decision == "APPROVED" else TicketStatus.OPEN
    
    # Update metadata with review details
    # Create a shallow copy to ensure SQLAlchemy detects the change
    metadata = dict(ticket.metadata_ or {})
    metadata["reviewed_by"] = str(current_user.id)
    from datetime import datetime, timezone
    metadata["reviewed_at"] = datetime.now(tz=timezone.utc).isoformat()
    metadata["review_decision"] = body.approval_decision.value
    
    if body.agent_override_notes:
        metadata["reviewer_notes"] = body.agent_override_notes
        
    if body.edited_response:
        metadata["ai_proposed_response"] = body.edited_response

    updated = await repo.update(ticket, status=new_status, metadata_=metadata)
    
    # Explicit commit
    await db.commit()
    
    return TicketResponse.model_validate(updated)
