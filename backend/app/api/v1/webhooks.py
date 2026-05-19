"""Webhook routes — inbound triggers from email and Slack."""

from __future__ import annotations

from fastapi import APIRouter, Header, Request, status

from app.core.logging import get_logger

router = APIRouter(prefix="/webhooks", tags=["Webhooks"])
logger = get_logger(__name__)


@router.post("/email", status_code=status.HTTP_200_OK, summary="Inbound email → create ticket")
async def email_webhook(request: Request) -> dict:
    """
    Receives inbound email events (e.g., from SendGrid Inbound Parse).
    Parses the payload and creates a ticket via the ticket service.
    """
    payload = await request.json()
    logger.info("email_webhook_received", keys=list(payload.keys()))
    # TODO: Parse email payload → create Ticket (Phase 2)
    return {"received": True}


@router.post("/slack", status_code=status.HTTP_200_OK, summary="Slack event → create/update ticket")
async def slack_webhook(
    request: Request,
    x_slack_signature: str | None = Header(None),
    x_slack_request_timestamp: str | None = Header(None),
) -> dict:
    """
    Receives Slack Events API payloads.
    Verifies Slack signature before processing.
    """
    payload = await request.json()

    # Handle Slack URL verification challenge
    if payload.get("type") == "url_verification":
        return {"challenge": payload.get("challenge")}

    logger.info("slack_webhook_received", event_type=payload.get("event", {}).get("type"))
    # TODO: Verify Slack signature + parse event → create/update Ticket (Phase 2)
    return {"received": True}
