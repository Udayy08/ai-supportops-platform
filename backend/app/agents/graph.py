"""
LangGraph StateGraph — wires all 7 agent nodes into the support workflow.

Graph topology:
  START → classifier → retriever → sentiment → resolution
        → response_writer → hallucination_checker
        → (conditional) → human_approval → END
                        → END (auto-resolve)
"""

from __future__ import annotations

from langgraph.graph import END, StateGraph

from app.agents.state import SupportState
from app.agents.nodes.classifier import classifier_node
from app.agents.nodes.retriever import retriever_node
from app.agents.nodes.sentiment import sentiment_node
from app.agents.nodes.resolution import resolution_node
from app.agents.nodes.response_writer import response_writer_node
from app.agents.nodes.hallucination import hallucination_node
from app.agents.nodes.human_approval import human_approval_node


def _route_after_hallucination(state: SupportState) -> str:
    """Conditional edge: escalate if confidence is below threshold."""
    if state.get("is_below_threshold", False):
        return "human_approval"
    # Auto-resolve: mark disposition and skip human approval
    return "auto_resolve"


def _auto_resolve_node(state: SupportState) -> dict:
    """Terminal node for auto-resolved tickets."""
    return {
        "final_disposition": "auto_resolved",
        "nodes_visited": state.get("nodes_visited", []) + ["auto_resolve"],
    }


def build_support_graph() -> StateGraph:
    """
    Construct and compile the LangGraph support workflow.

    Returns a compiled graph ready for `.invoke(state)`.
    """
    graph = StateGraph(SupportState)

    # ── Register nodes ───────────────────────────────────────────────────────
    graph.add_node("classifier", classifier_node)
    graph.add_node("retriever", retriever_node)
    graph.add_node("sentiment", sentiment_node)
    graph.add_node("resolution", resolution_node)
    graph.add_node("response_writer", response_writer_node)
    graph.add_node("hallucination_checker", hallucination_node)
    graph.add_node("human_approval", human_approval_node)
    graph.add_node("auto_resolve", _auto_resolve_node)

    # ── Wire edges ───────────────────────────────────────────────────────────
    graph.set_entry_point("classifier")
    graph.add_edge("classifier", "retriever")
    graph.add_edge("retriever", "sentiment")
    graph.add_edge("sentiment", "resolution")
    graph.add_edge("resolution", "response_writer")
    graph.add_edge("response_writer", "hallucination_checker")

    # Conditional routing after hallucination check
    graph.add_conditional_edges(
        "hallucination_checker",
        _route_after_hallucination,
        {
            "human_approval": "human_approval",
            "auto_resolve": "auto_resolve",
        },
    )

    # Both terminal paths lead to END
    graph.add_edge("human_approval", END)
    graph.add_edge("auto_resolve", END)

    return graph.compile()
