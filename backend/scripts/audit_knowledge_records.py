import sys
import os
import asyncio

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from sqlalchemy import select
from app.db.session import init_db, get_session_factory
from app.models.knowledge_article import KnowledgeArticle

async def audit_postgres():
    await init_db()
    SessionLocal = get_session_factory()
    async with SessionLocal() as session:
        query = select(KnowledgeArticle)
        result = await session.execute(query)
        articles = result.scalars().all()
        
        print("=== PostgreSQL Knowledge Base Audit ===")
        print(f"Total Articles: {len(articles)}")
        
        print("\n--- Article Details ---")
        for a in articles:
            meta = a.metadata_ or {}
            filename = meta.get("filename", a.title)
            status = meta.get("processing_status", "UNKNOWN")
            indexed = meta.get("indexed_status", "UNKNOWN")
            chunks = meta.get("chunk_count", 0)
            
            print(f"ID: {a.id} | Filename: {filename}")
            print(f"  Status: {status} | Indexed: {indexed} | Chunks: {chunks}")
            print(f"  Created: {a.created_at} | Last Indexed: {meta.get('last_indexed_at', 'Never')}")
            if meta.get("error"):
                print(f"  Error: {meta.get('error')}")
            print("-" * 40)
            
if __name__ == "__main__":
    asyncio.run(audit_postgres())
