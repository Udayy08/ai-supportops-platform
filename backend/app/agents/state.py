"""
Typed workflow state shared across all LangGraph agent nodes.

Every node receives this state, reads what it needs, and returns
a partial dict of updates. LangGraph merges the updates automatically.
"""

from __future__ import annotations

import uuid
from typing import Any, TypedDict


class SupportState(TypedDict, total=False):
    """
    The shared state object flowing through the LangGraph StateGraph.

    Fields are grouped by the agent that primarily writes them,
    but any node can read any field.
    """

    # ── Input (set once at graph invocation) ──────────────────────────────────
    ticket_id: str
    tenant_id: str
    customer_message: str
    customer_name: str

    # ── Classifier Agent ─────────────────────────────────────────────────────
    category: str               # billing, shipping, account, technical, general
    subcategory: str
    priority: str               # low, medium, high, critical
    classification_confidence: float

    # ── RAG Retriever Agent ──────────────────────────────────────────────────
    retrieved_context: str
    citations: list[dict[str, Any]]
    retrieval_confidence: float
    confidence_decision: str
    num_sources_found: int
    retrieval_debug: dict[str, Any]

    # ── Sentiment & Risk Agent ───────────────────────────────────────────────
    sentiment: str              # positive, neutral, frustrated, angry
    risk_level: str             # low, medium, high
    urgency_modifier: float     # multiplier for escalation threshold
    sentiment_reasoning: str

    # ── Resolution Generator Agent ───────────────────────────────────────────
    resolution_plan: str        # structured plan for how to resolve the issue
    resolution_steps: list[str]
    requires_action: bool       # whether the resolution needs system action (refund, etc.)

    # ── Response Writer Agent ────────────────────────────────────────────────
    proposed_response: str      # the actual customer-facing response
    response_tone: str          # empathetic, professional, urgent
    generation_confidence: float

    # ── Hallucination Checker Agent ──────────────────────────────────────────
    hallucination_score: float  # 0.0 = no hallucination, 1.0 = fully hallucinated
    grounding_issues: list[str]
    overall_confidence: float   # final composite confidence
    is_below_threshold: bool

    # ── Human Approval Agent ─────────────────────────────────────────────────
    escalation_reason: str
    approval_request_id: str
    final_disposition: str      # "auto_resolved" | "escalated"

    # ── Workflow Metadata ────────────────────────────────────────────────────
    nodes_visited: list[str]
    error: str | None
    retry_count: int
