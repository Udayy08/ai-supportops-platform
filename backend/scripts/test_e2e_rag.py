import asyncio
import uuid
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.db.session import init_db, get_session_factory
from app.models.tenant import Tenant
from app.rag.knowledge_manager import KnowledgeManager
from sqlalchemy.future import select

async def run_e2e():
    await init_db()
    factory = get_session_factory()
    async with factory() as db:
        # 1. Get Tenant
        result = await db.execute(select(Tenant).limit(1))
        tenant = result.scalar_one_or_none()
        if not tenant:
            print("No tenant found. Run seed_kb.py first.")
            return
            
        print(f"=== [1] Using Tenant: {tenant.name} ({tenant.id}) ===")
        
        # 2. Upload Document
        print("\n=== [2] Uploading Knowledge Document ===")
        content = "Premium Gold customers receive refunds within exactly 3 business days."
        filename = "premium_gold_policy.md"
        
        km = KnowledgeManager(db)
        
        # Call ingestion (this takes string)
        article = await km.ingest_article(
            tenant_id=tenant.id,
            title="Premium Gold Refund Policy",
            content=content,
            category="Policies",
            metadata={"filename": filename}
        )
        print(f"Uploaded Article ID: {article.id}")
        print(f"Article processing status: {article.metadata_.get('processing_status')}")
        
        # 3. Verify Retriever Output directly
        print("\n=== [3] Verifying Retriever Directly ===")
        from app.rag.retriever import TenantRetriever
        retriever = TenantRetriever()
        
        query = "How long does it take for a Premium Gold customer to get a refund?"
        results = retriever.retrieve_with_scores(query=query, tenant_id=tenant.id, top_k=2)
        
        for idx, (doc, score) in enumerate(results):
            print(f"\n--- Chunk {idx} (Score: {score:.4f}) ---")
            print(f"Content: {doc.page_content}")
            print("Metadata:")
            for k, v in doc.metadata.items():
                print(f"  {k}: {v}")
                
            # Quick check to ensure it's our new doc
            if doc.metadata.get("source_filename") == filename:
                print(">>> SUCCESS: Found chunk from our newly uploaded file!")

        # 4. Create a Ticket
        print("\n=== [4] Creating Ticket ===")
        from app.models.ticket import Ticket, TicketPriority
        
        ticket = Ticket(
            id=uuid.uuid4(),
            tenant_id=tenant.id,
            subject="Refund time?",
            description=query,
            priority=TicketPriority.HIGH,
            category="Billing",
            metadata_={"customer_email": "goldmember@example.com", "customer_name": "Gold Member"}
        )
        db.add(ticket)
        await db.commit()
        await db.refresh(ticket)
        print(f"Created Ticket ID: {ticket.id}")
        
        # 5. Run Workflow
        print("\n=== [5] Running AI Workflow ===")
        from app.agents.graph import build_support_graph
        
        graph = build_support_graph()
        initial_state = {
            "ticket_id": str(ticket.id),
            "tenant_id": str(tenant.id),
            "customer_message": ticket.description,
            "category": ticket.category,
            "priority": ticket.priority.value,
            "proposed_response": "",
            "hallucination_score": 0.0,
            "final_disposition": "pending",
            "nodes_visited": [],
        }
        
        result_state = await graph.ainvoke(initial_state)
        
        print("\n=== [6] AI Final Response ===")
        print(result_state.get("proposed_response", "No response generated"))
        
        print("\n=== Workflow Metadata ===")
        print(f"Final Disposition: {result_state.get('final_disposition')}")
        print(f"Hallucination Score: {result_state.get('hallucination_score')}")

if __name__ == "__main__":
    asyncio.run(run_e2e())
