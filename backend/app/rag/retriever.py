from typing import Any, Dict, List, Tuple
import uuid

from langchain_core.documents import Document

from app.rag.vectorstore import get_vectorstore


class TenantRetriever:
    """
    A service class that wraps Chroma vector search to guarantee strict tenant isolation.
    Returns both the LangChain documents and their confidence (similarity) scores.
    """

    def __init__(self, collection_name: str | None = None):
        self.vectorstore = get_vectorstore(collection_name)

    def retrieve_with_scores(
        self,
        query: str,
        tenant_id: uuid.UUID,
        top_k: int = 5,
        score_threshold: float | None = None,
    ) -> List[Tuple[Document, float]]:
        """
        Retrieve relevant document chunks with strict tenant_id filtering.
        
        Args:
            query: The semantic search query.
            tenant_id: The UUID of the tenant to restrict search space (Data Leakage Prevention).
            top_k: Number of chunks to return.
            score_threshold: Optional minimum similarity score.
            
        Returns:
            List of tuples: (Document, confidence_score)
        """
        # We must filter by tenant_id. Chroma supports where clauses.
        _filter: Dict[str, Any] = {"tenant_id": str(tenant_id)}

        # Perform similarity search with score
        # Note: Chroma by default returns distance (lower is better, depending on distance metric like L2)
        # LangChain's Chroma wrapper provides similarity_search_with_relevance_scores where higher is better (0 to 1).
        results = self.vectorstore.similarity_search_with_relevance_scores(
            query=query,
            k=top_k,
            filter=_filter,
            score_threshold=score_threshold
        )
        return results

    def get_context_and_citations(
        self,
        query: str,
        tenant_id: uuid.UUID,
        top_k: int = 5
    ) -> Tuple[str, List[Dict[str, Any]]]:
        """
        Format retrieved chunks into a single context string and a list of citations.
        Useful for LLM generation steps.
        """
        results = self.retrieve_with_scores(query, tenant_id, top_k)
        
        context_parts = []
        citations = []

        for idx, (doc, score) in enumerate(results):
            # Create a structured citation
            citation = {
                "chunk_id": doc.metadata.get("chunk_id", f"unknown-{idx}"),
                "article_id": doc.metadata.get("article_id"),
                "title": doc.metadata.get("title", "Unknown Article"),
                "category": doc.metadata.get("category", "General"),
                "confidence_score": round(score, 4)
            }
            citations.append(citation)
            
            # Format context with citation marker
            context_parts.append(
                f"--- [Source: {citation['title']}] ---\n{doc.page_content}"
            )

        context_str = "\n\n".join(context_parts)
        return context_str, citations
