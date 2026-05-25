"""Human Approval Agent — creates an ApprovalRequest when confidence is low."""

from __future__ import annotations

import uuid

from app.agents.state import SupportState


def human_approval_node(state: SupportState) -> dict:
    """
    Create an escalation record when the hallucination checker flags
    the response as below the confidence threshold.

    NOTE: In a full production system, this would write an ApprovalRequest
    to the database via the workflow service. For the standalone graph,
    we prepare the escalation data that the service layer will persist.
    """
    reasons = []

    if state.get("is_below_threshold"):
        reasons.append(
            f"Overall confidence {state.get('overall_confidence', 0):.2f} "
            f"is below threshold"
        )

    grounding_issues = state.get("grounding_issues", [])
    if grounding_issues:
        reasons.append(f"Grounding issues detected: {'; '.join(grounding_issues)}")

    if state.get("risk_level") == "high":
        reasons.append(f"High risk customer (sentiment: {state.get('sentiment', 'unknown')})")

    if state.get("confidence_decision") == "escalated":
        reason = state.get("retrieval_debug", {}).get("retrieval_failure_reason", "Low retrieval confidence")
        score = state.get("retrieval_debug", {}).get("retrieval_confidence_score", 0.0)
        reasons.append(f"Retrieval Escalted ({reason}): score {score}")

    escalation_reason = " | ".join(reasons) if reasons else "Low confidence response"

    # Set fallback response if escalating from retrieval phase
    proposed_response = state.get("proposed_response")
    if not proposed_response and state.get("confidence_decision") == "escalated":
        proposed_response = "I'm unable to find a confident answer for your query. Escalating this ticket to a human agent."

    return {
        "escalation_reason": escalation_reason,
        "approval_request_id": str(uuid.uuid4()),
        "final_disposition": "escalated",
        "proposed_response": proposed_response,
        "nodes_visited": state.get("nodes_visited", []) + ["human_approval"],
    }
