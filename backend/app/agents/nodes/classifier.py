"""Ticket Classifier Agent — categorizes and prioritizes the support ticket."""

from __future__ import annotations

import json

from langchain_core.messages import HumanMessage, SystemMessage

from app.agents.llm import get_llm, parse_json_response
from app.agents.prompts.templates import CLASSIFIER_SYSTEM, CLASSIFIER_USER
from app.agents.state import SupportState


def classifier_node(state: SupportState) -> dict:
    """Classify the ticket into category, subcategory, priority."""
    llm = get_llm()

    messages = [
        SystemMessage(content=CLASSIFIER_SYSTEM),
        HumanMessage(content=CLASSIFIER_USER.format(
            customer_message=state["customer_message"]
        )),
    ]

    response = llm.invoke(messages)
    result = parse_json_response(response)

    return {
        "category": result.get("category", "general"),
        "subcategory": result.get("subcategory", "unknown"),
        "priority": result.get("priority", "medium"),
        "classification_confidence": float(result.get("confidence", 0.5)),
        "nodes_visited": state.get("nodes_visited", []) + ["classifier"],
    }
