"""Conversation and message routes."""

from __future__ import annotations

import uuid

from fastapi import APIRouter, status

from app.api.deps import CurrentUser, DBSession
from app.core.exceptions import NotFoundException
from app.db.repositories.conversation_repo import ConversationRepository
from app.db.repositories.ticket_repo import TicketRepository
from app.schemas.conversation import (
    ConversationListResponse,
    ConversationResponse,
    MessageCreateRequest,
    MessageResponse,
)

router = APIRouter(tags=["Conversations"])


@router.get(
    "/tickets/{ticket_id}/conversations",
    response_model=ConversationListResponse,
    summary="List conversations for a ticket",
)
async def list_conversations(
    ticket_id: uuid.UUID,
    current_user: CurrentUser,
    db: DBSession,
) -> ConversationListResponse:
    # Verify ticket belongs to tenant
    ticket_repo = TicketRepository(db)
    ticket = await ticket_repo.get_by_id(ticket_id, tenant_id=current_user.tenant_id)
    if not ticket:
        raise NotFoundException(detail=f"Ticket '{ticket_id}' not found.")

    repo = ConversationRepository(db)
    conversations = await repo.list_by_ticket(ticket_id)
    return ConversationListResponse(
        items=[ConversationResponse.model_validate(c) for c in conversations],
        total=len(conversations),
    )


@router.get(
    "/conversations/{conversation_id}",
    response_model=ConversationResponse,
    summary="Get conversation with all messages",
)
async def get_conversation(
    conversation_id: uuid.UUID,
    current_user: CurrentUser,
    db: DBSession,
) -> ConversationResponse:
    repo = ConversationRepository(db)
    conversation = await repo.get_by_id_with_messages(
        conversation_id, tenant_id=current_user.tenant_id
    )
    if not conversation:
        raise NotFoundException(detail=f"Conversation '{conversation_id}' not found.")
    return ConversationResponse.model_validate(conversation)


@router.post(
    "/conversations/{conversation_id}/messages",
    response_model=MessageResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Add message to conversation (triggers agent if customer role)",
)
async def add_message(
    conversation_id: uuid.UUID,
    body: MessageCreateRequest,
    current_user: CurrentUser,
    db: DBSession,
) -> MessageResponse:
    repo = ConversationRepository(db)
    conversation = await repo.get_by_id_with_messages(
        conversation_id, tenant_id=current_user.tenant_id
    )
    if not conversation:
        raise NotFoundException(detail=f"Conversation '{conversation_id}' not found.")

    message = await repo.add_message(
        conversation_id=conversation_id,
        role=body.role,
        content=body.content,
    )
    # TODO: If body.role == MessageRole.CUSTOMER, dispatch agent workflow (Phase 2)
    return MessageResponse.model_validate(message)
