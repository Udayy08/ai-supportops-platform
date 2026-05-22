"""Persistence logic for Confidence Scores."""

import uuid
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.quality import ConfidenceScore

async def persist_confidence_score(
    session: AsyncSession,
    node_execution_id: uuid.UUID,
    message_id: uuid.UUID | None,
    state: dict[str, Any],
    threshold_used: float
) -> ConfidenceScore:
    """Extract confidence metrics from graph state and persist them."""
    
    score = ConfidenceScore(
        node_execution_id=node_execution_id,
        message_id=message_id,
        overall_score=state.get("overall_confidence", 0.0),
        retrieval_score=state.get("retrieval_confidence", 0.0),
        generation_score=state.get("generation_confidence", 0.0),
        is_below_threshold=state.get("is_below_threshold", False),
        threshold_used=threshold_used,
        score_metadata={"nodes_visited": state.get("nodes_visited", [])}
    )
    
    session.add(score)
    await session.commit()
    return score
