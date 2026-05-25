import sys
import os
import asyncio
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from sqlalchemy import select
from app.db.session import init_db, get_session_factory
from app.models.knowledge_article import KnowledgeArticle
from app.rag.vectorstore import get_vectorstore

async def clean_orphaned():
    await init_db()
    SessionLocal = get_session_factory()
    
    vectorstore = get_vectorstore()
    collection = vectorstore._collection
    data = collection.get(include=["metadatas"])
    chroma_article_ids = set()
    for meta in data["metadatas"]:
        aid = meta.get("article_id")
        if aid:
            chroma_article_ids.add(aid)
            
    async with SessionLocal() as s:
        res = await s.execute(select(KnowledgeArticle.id))
        pg_ids = {str(r) for r in res.scalars().all()}
        
    orphaned_ids = chroma_article_ids - pg_ids
    print(f"Orphaned IDs found: {orphaned_ids}")
    
    for oid in orphaned_ids:
        print(f"Deleting orphans for {oid}")
        collection.delete(where={"article_id": oid})
        
    print("Done cleaning orphaned vectors.")

if __name__ == "__main__":
    asyncio.run(clean_orphaned())
