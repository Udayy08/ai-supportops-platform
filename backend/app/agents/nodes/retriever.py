"""RAG Retrieval Agent — fetches relevant context from Phase 4 vector store."""

from __future__ import annotations

import uuid

from app.agents.state import SupportState
from app.rag.retriever import TenantRetriever


def retriever_node(state: SupportState) -> dict:
    """
    Execute tenant-scoped RAG retrieval using the Phase 4 TenantRetriever.
    Passes the customer message + category as the semantic query.
    """
    tenant_id = uuid.UUID(state["tenant_id"])
    query = f"{state.get('category', '')} {state['customer_message']}"

    retriever = TenantRetriever()
    context, citations = retriever.get_context_and_citations(
        query=query,
        tenant_id=tenant_id,
        top_k=3,
    )

    # Compute retrieval confidence as the average of citation scores
    scores = [c["confidence_score"] for c in citations]
    retrieval_confidence = sum(scores) / len(scores) if scores else 0.0

    return {
        "retrieved_context": context,
        "citations": citations,
        "retrieval_confidence": round(retrieval_confidence, 4),
        "num_sources_found": len(citations),
        "nodes_visited": state.get("nodes_visited", []) + ["retriever"],
    }
