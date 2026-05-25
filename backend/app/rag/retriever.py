import threading
from typing import Any, Dict, List, Tuple
import uuid

from langchain_core.documents import Document
from sentence_transformers import CrossEncoder

from app.rag.vectorstore import get_vectorstore


# Global Cross-Encoder Instance (Singleton)
_cross_encoder = None
_cross_encoder_lock = threading.Lock()

def get_cross_encoder():
    global _cross_encoder
    if _cross_encoder is None:
        with _cross_encoder_lock:
            if _cross_encoder is None:
                # Lightweight cross-encoder model for fast CPU reranking
                _cross_encoder = CrossEncoder("cross-encoder/ms-marco-MiniLM-L-6-v2")
    return _cross_encoder

# Tenant-isolated BM25 Cache
_bm25_cache = {}
_bm25_lock = threading.Lock()

def get_bm25_retriever(tenant_id: str, vectorstore):
    from langchain_community.retrievers import BM25Retriever
    
    with _bm25_lock:
        if tenant_id in _bm25_cache:
            return _bm25_cache[tenant_id]
            
        # If not in cache, build it dynamically by fetching all chunks for the tenant
        res = vectorstore.get(where={"tenant_id": tenant_id})
        documents = []
        if res and 'documents' in res and res['documents']:
            for idx, content in enumerate(res['documents']):
                metadata = res['metadatas'][idx] if res['metadatas'] else {}
                documents.append(Document(page_content=content, metadata=metadata))
        
        if not documents:
            return None
            
        bm25_retriever = BM25Retriever.from_documents(documents)
        # We need top_k = 10 for hybrid fusion
        bm25_retriever.k = 10 
        _bm25_cache[tenant_id] = bm25_retriever
        return bm25_retriever

def invalidate_bm25_cache(tenant_id: str):
    """Invalidate the lexical cache when knowledge base changes."""
    with _bm25_lock:
        if tenant_id in _bm25_cache:
            del _bm25_cache[tenant_id]


class TenantRetriever:
    """
    A service class that implements Hybrid Retrieval (Semantic + Lexical)
    and Cross-Encoder Reranking, guaranteeing strict tenant isolation.
    """

    def __init__(self, collection_name: str | None = None):
        self.vectorstore = get_vectorstore(collection_name)

    def _reciprocal_rank_fusion(
        self,
        semantic_results: List[Tuple[Document, float]],
        lexical_results: List[Document],
        k: int = 60
    ) -> List[Dict[str, Any]]:
        """Merge semantic and lexical results using Reciprocal Rank Fusion (RRF)."""
        scores = {}
        doc_map = {}
        
        # Process Semantic Results
        for rank, (doc, sem_score) in enumerate(semantic_results, 1):
            chunk_id = doc.metadata.get("chunk_id", str(uuid.uuid4()))
            doc.metadata["chunk_id"] = chunk_id  # ensure it has an ID
            
            rrf_score = 1.0 / (k + rank)
            scores[chunk_id] = scores.get(chunk_id, 0.0) + rrf_score
            
            doc_map[chunk_id] = {
                "doc": doc,
                "semantic_score": sem_score,
                "lexical_score": 0.0,
                "pre_rerank_rank": rank
            }

        # Process Lexical Results
        for rank, doc in enumerate(lexical_results, 1):
            chunk_id = doc.metadata.get("chunk_id")
            if not chunk_id:
                chunk_id = str(uuid.uuid4())
                doc.metadata["chunk_id"] = chunk_id
                
            rrf_score = 1.0 / (k + rank)
            scores[chunk_id] = scores.get(chunk_id, 0.0) + rrf_score
            
            if chunk_id not in doc_map:
                doc_map[chunk_id] = {
                    "doc": doc,
                    "semantic_score": 0.0,
                    "lexical_score": 1.0 / rank, # Proxy for BM25 score observability
                    "pre_rerank_rank": rank
                }
            else:
                doc_map[chunk_id]["lexical_score"] = 1.0 / rank

        # Sort by RRF
        sorted_chunks = sorted(scores.items(), key=lambda x: x[1], reverse=True)
        
        merged = []
        for rank, (chunk_id, rrf_score) in enumerate(sorted_chunks, 1):
            item = doc_map[chunk_id]
            item["rrf_score"] = rrf_score
            item["pre_rerank_rank"] = rank
            merged.append(item)
            
        return merged

    def retrieve_with_scores(
        self,
        query: str,
        tenant_id: uuid.UUID,
        top_k: int = 5,
        score_threshold: float | None = None,
    ) -> List[Tuple[Document, float]]:
        """
        Backward compatibility for baseline scripts.
        WARNING: This skips Reranking. Use get_context_and_citations for full pipeline.
        """
        _filter: Dict[str, Any] = {"tenant_id": str(tenant_id)}
        return self.vectorstore.similarity_search_with_relevance_scores(
            query=query, k=top_k, filter=_filter, score_threshold=score_threshold
        )

    def hybrid_retrieve_and_rerank(
        self,
        query: str,
        tenant_id: uuid.UUID,
        top_k: int = 3,
        fetch_k: int = 20
    ) -> List[Dict[str, Any]]:
        """
        Executes Phase 1 (Hybrid Retrieval) and Phase 2 (Cross-Encoder Reranking).
        """
        tenant_id_str = str(tenant_id)
        
        # 1. Semantic Search
        _filter: Dict[str, Any] = {"tenant_id": tenant_id_str}
        semantic_results = self.vectorstore.similarity_search_with_relevance_scores(
            query=query, k=fetch_k, filter=_filter
        )
        
        # 2. Lexical Search
        lexical_results = []
        bm25_retriever = get_bm25_retriever(tenant_id_str, self.vectorstore)
        if bm25_retriever:
            # Override k for this specific query if needed, BM25Retriever takes k as instance variable
            bm25_retriever.k = fetch_k
            lexical_results = bm25_retriever.invoke(query)
            
        # 3. Candidate Merging (RRF)
        merged_candidates = self._reciprocal_rank_fusion(semantic_results, lexical_results)
        
        # Trim to fetch_k before reranking to save compute
        candidates_to_rerank = merged_candidates[:fetch_k]
        
        if not candidates_to_rerank:
            return []
            
        # 4. Cross-Encoder Reranking
        cross_encoder = get_cross_encoder()
        pairs = [[query, item["doc"].page_content] for item in candidates_to_rerank]
        
        # Returns raw logits
        ce_scores = cross_encoder.predict(pairs)
        
        for idx, item in enumerate(candidates_to_rerank):
            item["cross_encoder_score"] = float(ce_scores[idx])
            
        # Sort by Cross-Encoder score descending
        reranked_candidates = sorted(
            candidates_to_rerank, 
            key=lambda x: x["cross_encoder_score"], 
            reverse=True
        )
        
        # Assign final rank
        for rank, item in enumerate(reranked_candidates, 1):
            item["post_rerank_rank"] = rank
            
        # Prune to Top-K
        return reranked_candidates[:top_k]

    def get_context_and_citations(
        self,
        query: str,
        tenant_id: uuid.UUID,
        top_k: int = 3
    ) -> Tuple[str, List[Dict[str, Any]]]:
        """
        Full RAG pipeline fetching: Hybrid -> RRF -> Cross-Encoder Rerank.
        Returns context string and rich citation list.
        """
        reranked_results = self.hybrid_retrieve_and_rerank(query, tenant_id, top_k=top_k)
        
        context_parts = []
        citations = []

        for item in reranked_results:
            doc = item["doc"]
            
            citation = {
                "chunk_id": doc.metadata.get("chunk_id", "unknown"),
                "article_id": doc.metadata.get("article_id"),
                "title": doc.metadata.get("title", "Unknown Article"),
                "category": doc.metadata.get("category", "General"),
                # Base retrieval info
                "source_document_id": doc.metadata.get("source_document_id"),
                "source_filename": doc.metadata.get("source_filename"),
                "chunk_index": doc.metadata.get("chunk_index"),
                "preview": doc.page_content[:200] + "..." if len(doc.page_content) > 200 else doc.page_content,
                
                # Extended Observability (Phase 1 & 2 requirements)
                "semantic_score": round(item["semantic_score"], 4),
                "lexical_score": round(item["lexical_score"], 4),
                "rrf_score": round(item["rrf_score"], 4),
                "cross_encoder_score": round(item["cross_encoder_score"], 4),
                "pre_rerank_rank": item["pre_rerank_rank"],
                "post_rerank_rank": item["post_rerank_rank"],
            }
            citations.append(citation)
            
            context_parts.append(
                f"--- [Source: {citation['title']}] ---\n{doc.page_content}"
            )

        context_str = "\n\n".join(context_parts)
        return context_str, citations
