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

    import time
    start_time = time.time()
    
    retriever = TenantRetriever()
    top_k = 3
    context, citations = retriever.get_context_and_citations(
        query=query,
        tenant_id=tenant_id,
        top_k=top_k,
    )

    elapsed_ms = int((time.time() - start_time) * 1000)

    from app.config import settings
    # Format documents for retrieval_debug
    debug_documents = []
    for idx, c in enumerate(citations):
        debug_documents.append({
            "document_id": c.get("source_document_id"),
            "filename": c.get("source_filename"),
            "chunk_index": c.get("chunk_index"),
            "similarity_score": c.get("semantic_score"),
            "cross_encoder_score": c.get("cross_encoder_score"),
            "pre_rerank_rank": c.get("pre_rerank_rank"),
            "post_rerank_rank": c.get("post_rerank_rank"),
            "retrieval_rank": idx + 1,
            "used_for_generation": True,
            "chunk_preview": c.get("preview")
        })

    retrieval_debug = {
        "query": query,
        "top_k": top_k,
        "retrieval_latency_ms": elapsed_ms,
        "documents": debug_documents
    }

    # Compute retrieval confidence as the MAX cross_encoder_score across candidates
    scores = [c.get("cross_encoder_score", -99.0) for c in citations]
    max_score = max(scores) if scores else -99.0
    
    threshold = settings.retrieval_confidence_threshold
    
    # Store confidence decision
    if max_score < threshold:
        confidence_decision = "escalated"
        failure_reason = "low_confidence_score"
    else:
        confidence_decision = "proceed"
        failure_reason = None
        
    retrieval_debug["retrieval_confidence_score"] = round(max_score, 4)
    retrieval_debug["retrieval_confidence_threshold"] = threshold
    retrieval_debug["confidence_decision"] = confidence_decision
    retrieval_debug["retrieval_failure_reason"] = failure_reason

    return {
        "retrieved_context": context,
        "citations": citations,
        "retrieval_confidence": round(max_score, 4),
        "confidence_decision": confidence_decision,
        "num_sources_found": len(citations),
        "retrieval_debug": retrieval_debug,
        "nodes_visited": state.get("nodes_visited", []) + ["retriever"],
    }
