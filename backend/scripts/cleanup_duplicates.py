import sys
import os
import asyncio
from collections import defaultdict

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from sqlalchemy import select
from app.db.session import init_db, get_session_factory
from app.models.knowledge_article import KnowledgeArticle
from app.rag.knowledge_manager import KnowledgeManager
from app.config import settings

async def cleanup_duplicates():
    await init_db()
    SessionLocal = get_session_factory()
    
    report_lines = [
        "# Duplicate Audit Report",
        "",
        "The following duplicate or stuck KnowledgeArticle records and their vectors are being permanently deleted.",
        ""
    ]
    
    report_lines.append("| Article ID | Filename | Chunks | Processing Status | Indexed Status | Reason |")
    report_lines.append("|------------|----------|--------|-------------------|----------------|--------|")
    
    async with SessionLocal() as session:
        query = select(KnowledgeArticle)
        result = await session.execute(query)
        articles = result.scalars().all()
        
        # Group by tenant_id + filename
        grouped = defaultdict(list)
        for a in articles:
            meta = a.metadata_ or {}
            filename = meta.get("filename", a.title)
            key = f"{a.tenant_id}::{filename}"
            grouped[key].append(a)
            
        manager = KnowledgeManager(session=session, collection_name=settings.chroma_collection_name)
            
        for key, group in grouped.items():
            if len(group) <= 1:
                continue
                
            # Sort group: SUCCESS first, then by updated_at desc
            def sort_key(article):
                meta = article.metadata_ or {}
                status_score = 0
                if meta.get("indexed_status") == "SUCCESS":
                    status_score = 2
                elif meta.get("processing_status") == "PROCESSING":
                    status_score = 1
                return (status_score, article.updated_at)
                
            group.sort(key=sort_key, reverse=True)
            
            keeper = group[0]
            duplicates = group[1:]
            
            for dup in duplicates:
                meta = dup.metadata_ or {}
                filename = meta.get("filename", dup.title)
                status = meta.get("processing_status", "UNKNOWN")
                indexed = meta.get("indexed_status", "UNKNOWN")
                chunks = meta.get("chunk_count", 0)
                reason = "Duplicate of " + str(keeper.id)
                
                report_lines.append(f"| `{dup.id}` | {filename} | {chunks} | {status} | {indexed} | {reason} |")
                
                # Delete from ChromaDB and Postgres
                try:
                    await manager.delete_article(dup)
                    print(f"Deleted {dup.id} ({filename})")
                except Exception as e:
                    print(f"Failed to delete {dup.id}: {e}")
                    
        # Write report artifact
        artifact_path = "/Users/shubhamraj407/.gemini/antigravity/brain/bfe9fff0-0878-4128-af55-0e0ede1329a5/duplicate_audit_report.md"
        with open(artifact_path, "w") as f:
            f.write("\n".join(report_lines))
            
        print(f"Cleanup complete. Report saved to {artifact_path}")

if __name__ == "__main__":
    asyncio.run(cleanup_duplicates())
