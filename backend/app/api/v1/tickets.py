"""Ticket routes — full CRUD with pagination, filtering, and agent workflow trigger."""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Query, status

from app.api.deps import CurrentUser, DBSession, Pagination
from app.core.exceptions import ForbiddenException, NotFoundException
from app.db.repositories.ticket_repo import TicketRepository
from app.models.ticket import TicketPriority, TicketStatus
from app.schemas.ticket import (
    TicketCreateRequest,
    TicketListResponse,
    TicketResponse,
    TicketUpdateRequest,
)

router = APIRouter(prefix="/tickets", tags=["Tickets"])


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
    # TODO: Dispatch LangGraph workflow as a background task (Phase 2)
    return TicketResponse.model_validate(ticket)


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


@router.post("/{ticket_id}/reprocess", response_model=TicketResponse, summary="Re-run agent workflow")
async def reprocess_ticket(
    ticket_id: uuid.UUID,
    current_user: CurrentUser,
    db: DBSession,
) -> TicketResponse:
    repo = TicketRepository(db)
    ticket = await repo.get_by_id(ticket_id, tenant_id=current_user.tenant_id)
    if not ticket:
        raise NotFoundException(detail=f"Ticket '{ticket_id}' not found.")

    # TODO: Re-dispatch LangGraph workflow (Phase 2)
    return TicketResponse.model_validate(ticket)
