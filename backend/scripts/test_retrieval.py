import uuid
import sys
import os

# Add the backend directory to sys.path so we can import 'app'
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.rag.retriever import TenantRetriever


def test_retrieval():
    tenant_id_str = os.environ.get("TENANT_ID")
    
    if not tenant_id_str:
        # Try reading from file created by seed_kb.py
        try:
            with open("demo_tenant_id.txt", "r") as f:
                tenant_id_str = f.read().strip()
        except FileNotFoundError:
            print("Please run seed_kb.py first or set TENANT_ID environment variable.")
            sys.exit(1)

    tenant_id = uuid.UUID(tenant_id_str)
    print(f"Testing Retrieval for Tenant ID: {tenant_id}")

    retriever = TenantRetriever()

    queries = [
        "How long do credit card refunds take?",
        "How many full refunds can a customer receive within a 12-month period?",
        "How do I reset my password?",
        "What are the shipping delivery timelines?",
    ]

    for q in queries:
        print(f"\n" + "="*60)
        print(f"Query: {q}")
        print("="*60)
        
        context, citations = retriever.get_context_and_citations(
            query=q, 
            tenant_id=tenant_id, 
            top_k=3
        )
        
        print("\n[Citations]")
        for c in citations:
            print(f" - {c['title']} ({c['category']}) | Confidence: {c['confidence_score']:.4f}")
            
        print("\n[Context Provided to LLM]")
        print(context)


if __name__ == "__main__":
    test_retrieval()
