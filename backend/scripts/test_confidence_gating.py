import asyncio
import os
import uuid
import time
import json
from dotenv import load_dotenv

load_dotenv()

from app.services.workflow_service import WorkflowService
from app.db.session import async_session_maker

async def main():
    tenant_id = "00000000-0000-0000-0000-000000000000"
    
    queries = [
        {"desc": "Valid In-Domain", "q": "How do I reset my password?"},
        {"desc": "Ambiguous", "q": "My system is completely broken and nothing works."},
        {"desc": "Out-of-Domain", "q": "What is the capital of France?"}
    ]
    
    print("Initializing WorkflowService...")
    
    results = []
    
    async with async_session_maker() as session:
        service = WorkflowService(session=session)
        
        for item in queries:
            desc = item["desc"]
            query = item["q"]
            print(f"\n--- Testing: {desc} ---")
            print(f"Query: {query}")
            
            ticket_id = str(uuid.uuid4())
            result = await service.run_async(
                tenant_id=tenant_id,
                customer_message=query,
                ticket_id=ticket_id
            )
            
            debug = result.get("retrieval_debug", {})
            max_ce = debug.get("retrieval_confidence_score", "N/A")
            decision = debug.get("confidence_decision", "N/A")
            disp = result.get("final_disposition", "N/A")
            resp = result.get("proposed_response", "N/A")
            nodes = result.get("nodes_visited", [])
            
            print(f"Confidence Score: {max_ce}")
            print(f"Decision: {decision}")
            print(f"Disposition: {disp}")
            print(f"Response: {resp}")
            print(f"Nodes Visited: {' -> '.join(nodes)}")
            
            results.append(f"### {desc}\n"
                           f"- Query: `{query}`\n"
                           f"- Confidence Score: {max_ce}\n"
                           f"- Confidence Decision: {decision}\n"
                           f"- Final Disposition: {disp}\n"
                           f"- Nodes Visited: {' -> '.join(nodes)}\n"
                           f"- Response: {resp}\n")

    with open("confidence_gating_validation.md", "w") as f:
        f.write("# Confidence Gating Validation\n\n")
        for res in results:
            f.write(res + "\n")
            
if __name__ == "__main__":
    asyncio.run(main())
