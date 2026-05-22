"""Persistence logic for Hallucination Flags."""

import uuid
from datetime import datetime, timezone
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.quality import HallucinationFlag, HallucinationSeverity

async def persist_hallucination_flag(
    session: AsyncSession,
    tenant_id: uuid.UUID,
    workflow_run_id: uuid.UUID,
    message_id: uuid.UUID | None,
    state: dict[str, Any]
) -> HallucinationFlag | None:
    """Create a hallucination flag if grounding issues were detected."""
    
    issues = state.get("grounding_issues", [])
    if not issues and not state.get("is_below_threshold"):
        return None
        
    severity = HallucinationSeverity.HIGH if issues else HallucinationSeverity.MEDIUM
    claim = "; ".join(issues) if issues else "Overall confidence below threshold."
    
    flag = HallucinationFlag(
        tenant_id=tenant_id,
        workflow_run_id=workflow_run_id,
        message_id=message_id,
        severity=severity,
        flagged_claim=claim,
        detection_method="hallucination_agent",
        faithfulness_score=1.0 - state.get("hallucination_score", 0.0),
        evidence_checked=state.get("citations", []),
        flagged_at=datetime.now(timezone.utc)
    )
    
    session.add(flag)
    await session.commit()
    return flag
