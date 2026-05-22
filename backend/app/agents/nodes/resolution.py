"""Resolution Generator Agent — creates a resolution plan from RAG context."""

from __future__ import annotations

import json

from langchain_core.messages import HumanMessage, SystemMessage

from app.agents.llm import get_llm, parse_json_response
from app.agents.prompts.templates import RESOLUTION_SYSTEM, RESOLUTION_USER
from app.agents.state import SupportState


def resolution_node(state: SupportState) -> dict:
    """Generate a structured resolution plan grounded in retrieved context."""
    llm = get_llm()

    messages = [
        SystemMessage(content=RESOLUTION_SYSTEM.format(
            retrieved_context=state.get("retrieved_context", "No context available."),
            category=state.get("category", "general"),
            sentiment=state.get("sentiment", "neutral"),
            risk_level=state.get("risk_level", "low"),
        )),
        HumanMessage(content=RESOLUTION_USER.format(
            customer_message=state["customer_message"]
        )),
    ]

    response = llm.invoke(messages)
    result = parse_json_response(response)

    return {
        "resolution_plan": result.get("resolution_plan", ""),
        "resolution_steps": result.get("resolution_steps", []),
        "requires_action": result.get("requires_action", False),
        "nodes_visited": state.get("nodes_visited", []) + ["resolution"],
    }
