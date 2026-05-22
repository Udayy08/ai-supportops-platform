"""Ticket routes — full CRUD with pagination, filtering, and agent workflow trigger."""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Query, status, BackgroundTasks

from app.api.deps import CurrentUser, DBSession, Pagination
from app.core.exceptions import ForbiddenException, NotFoundException
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
import asyncio

router = APIRouter(prefix="/tickets", tags=["Tickets"])

async def run_workflow_background(tenant_id: str, ticket_id: str, customer_message: str, customer_name: str):
    """Background task to run the workflow and persist any DB updates separately."""
    SessionLocal = get_session_factory()
    async with SessionLocal() as session:
        service = WorkflowService(session=session)
        # run_async ensures the heavy sync LangGraph doesn't block the async event loop
        result = await service.run_async(
            tenant_id=tenant_id,
            ticket_id=ticket_id,
            customer_message=customer_message,
            customer_name=customer_name
        )
        
        # Here we could update the ticket status based on final_disposition
        # For Phase 7, the core request is triggering it
        if result.get("final_disposition") == "resolved":
            from app.db.repositories.ticket_repo import TicketRepository
            repo = TicketRepository(session)
            ticket = await repo.get_by_id(uuid.UUID(ticket_id), tenant_id=uuid.UUID(tenant_id))
            if ticket:
                await repo.update(ticket, status=TicketStatus.CLOSED)


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
    updated = await repo.update(ticket, status=new_status)
    return TicketResponse.model_validate(updated)
