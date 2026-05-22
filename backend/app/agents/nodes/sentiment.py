"""Sentiment & Risk Agent — detects customer sentiment and risk level."""

from __future__ import annotations

import json

from langchain_core.messages import HumanMessage, SystemMessage

from app.agents.llm import get_llm, parse_json_response
from app.agents.prompts.templates import SENTIMENT_SYSTEM, SENTIMENT_USER
from app.agents.state import SupportState


def sentiment_node(state: SupportState) -> dict:
    """Analyze customer sentiment and assess risk level."""
    llm = get_llm()

    messages = [
        SystemMessage(content=SENTIMENT_SYSTEM.format(
            category=state.get("category", "general"),
        )),
        HumanMessage(content=SENTIMENT_USER.format(
            customer_message=state["customer_message"]
        )),
    ]

    response = llm.invoke(messages)
    result = parse_json_response(response)

    return {
        "sentiment": result.get("sentiment", "neutral"),
        "risk_level": result.get("risk_level", "low"),
        "urgency_modifier": float(result.get("urgency_modifier", 1.0)),
        "sentiment_reasoning": result.get("reasoning", ""),
        "nodes_visited": state.get("nodes_visited", []) + ["sentiment"],
    }
