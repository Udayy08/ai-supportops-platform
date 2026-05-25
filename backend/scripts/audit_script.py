import sys
import os
import asyncio
import uuid
from sqlalchemy import text
from app.db.session import init_db, get_session_factory, close_db
from app.rag.retriever import TenantRetriever, get_bm25_retriever

async def run_audit():
    results = {}
    # 1. Check DB
    try:
        await init_db()
        factory = get_session_factory()
        async with factory() as session:
            res = await session.execute(text("SELECT 1"))
            results['postgres'] = 'PASS'
    except Exception as e:
        results['postgres'] = f'FAIL: {e}'

    # 2. Check KB & Retrieval
    try:
        retriever = TenantRetriever()
        tenant_id = uuid.uuid4() # Mock tenant ID
        
        # Test semantic (skip actual retrieval if collection is empty, just check it works)
        _filter = {"tenant_id": "test"}
        res = retriever.vectorstore.similarity_search_with_relevance_scores("test", k=1, filter=_filter)
        results['semantic_search'] = 'PASS'
        
    except Exception as e:
        results['retrieval'] = f'FAIL: {e}'
    finally:
        await close_db()
        
    for k, v in results.items():
        print(f"{k}: {v}")

if __name__ == "__main__":
    asyncio.run(run_audit())
