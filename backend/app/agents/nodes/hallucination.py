"""Hallucination Checker Agent — verifies factual grounding of the response."""

from __future__ import annotations

import json

from langchain_core.messages import HumanMessage, SystemMessage

from app.agents.llm import get_llm, parse_json_response
from app.agents.prompts.templates import HALLUCINATION_SYSTEM, HALLUCINATION_USER
from app.agents.state import SupportState
from app.config import settings


def hallucination_node(state: SupportState) -> dict:
    """Check the proposed response for hallucinations against source context."""
    llm = get_llm()

    messages = [
        SystemMessage(content=HALLUCINATION_SYSTEM.format(
            proposed_response=state.get("proposed_response", ""),
            retrieved_context=state.get("retrieved_context", ""),
            citations=json.dumps(state.get("citations", [])),
        )),
        HumanMessage(content=HALLUCINATION_USER),
    ]

    response = llm.invoke(messages)
    result = parse_json_response(response)

    hallucination_score = float(result.get("hallucination_score", 0.5))
    overall_confidence = float(result.get("overall_confidence", 0.5))

    # Adjust threshold by urgency modifier (angry customers → stricter threshold)
    urgency_modifier = state.get("urgency_modifier", 1.0)
    effective_threshold = settings.agent_confidence_threshold * urgency_modifier

    is_below = overall_confidence < effective_threshold

    return {
        "hallucination_score": hallucination_score,
        "grounding_issues": result.get("grounding_issues", []),
        "overall_confidence": overall_confidence,
        "is_below_threshold": is_below,
        "nodes_visited": state.get("nodes_visited", []) + ["hallucination_checker"],
    }
