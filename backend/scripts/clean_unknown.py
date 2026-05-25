import sys
import os
import asyncio
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from sqlalchemy import select
from app.db.session import init_db, get_session_factory
from app.models.knowledge_article import KnowledgeArticle

async def clean():
    await init_db()
    SessionLocal = get_session_factory()
    async with SessionLocal() as s:
        res = await s.execute(select(KnowledgeArticle))
        articles = res.scalars().all()
        for a in articles:
            meta = a.metadata_ or {}
            if meta.get('processing_status') in ['UNKNOWN', 'PROCESSING'] or not meta.get('filename'):
                await s.delete(a)
        await s.commit()
        print("Done")

if __name__ == "__main__":
    asyncio.run(clean())
