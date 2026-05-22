"""Response Writer Agent — crafts the customer-facing response."""

from __future__ import annotations

import json

from langchain_core.messages import HumanMessage, SystemMessage

from app.agents.llm import get_llm, parse_json_response
from app.agents.prompts.templates import RESPONSE_WRITER_SYSTEM, RESPONSE_WRITER_USER
from app.agents.state import SupportState


def response_writer_node(state: SupportState) -> dict:
    """Write a polished, customer-facing response based on the resolution plan."""
    llm = get_llm()

    messages = [
        SystemMessage(content=RESPONSE_WRITER_SYSTEM.format(
            resolution_plan=state.get("resolution_plan", ""),
            resolution_steps=json.dumps(state.get("resolution_steps", [])),
            sentiment=state.get("sentiment", "neutral"),
            customer_name=state.get("customer_name", "Customer"),
        )),
        HumanMessage(content=RESPONSE_WRITER_USER.format(
            customer_message=state["customer_message"]
        )),
    ]

    response = llm.invoke(messages)
    result = parse_json_response(response)

    return {
        "proposed_response": result.get("response", ""),
        "response_tone": result.get("tone", "professional"),
        "generation_confidence": float(result.get("confidence", 0.5)),
        "nodes_visited": state.get("nodes_visited", []) + ["response_writer"],
    }
