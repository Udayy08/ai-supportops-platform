import uuid
from typing import Dict, Any

from fastapi.concurrency import run_in_threadpool
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.knowledge_article import KnowledgeArticle
from app.rag.chunkers import chunk_document
from app.rag.vectorstore import get_vectorstore


class KnowledgeManager:
    """
    Manages the lifecycle of Knowledge Articles.
    Responsible for atomic synchronization between Postgres (source of truth)
    and ChromaDB (vector index).
    """

    def __init__(self, session: AsyncSession, collection_name: str | None = None):
        self.session = session
        self.vectorstore = get_vectorstore(collection_name)

    async def ingest_article(
        self,
        tenant_id: uuid.UUID,
        title: str,
        content: str,
        category: str | None = None,
        metadata: Dict[str, Any] | None = None,
        chunk_size: int = 1000,
        chunk_overlap: int = 200,
    ) -> KnowledgeArticle:
        """
        Ingest a new article. Saves to Postgres and chunks/embeds into ChromaDB.
        """
        article_id = uuid.uuid4()
        chroma_collection = self.vectorstore._collection.name

        # 1. Create DB Record
        article = KnowledgeArticle(
            id=article_id,
            tenant_id=tenant_id,
            title=title,
            content=content,
            category=category,
            metadata_=metadata or {},
            chroma_collection=chroma_collection,
            is_active=True,
        )
        self.session.add(article)
        await self.session.flush() # Get DB ID ready, but don't commit until vectors succeed

        # 2. Chunk Document
        # Base metadata for every chunk to enable strict filtering and citations
        base_metadata = {
            "article_id": str(article.id),
            "tenant_id": str(tenant_id),
            "title": title,
            "category": category or "General",
        }
        if metadata:
            # Add extra stringified metadata
            for k, v in metadata.items():
                if isinstance(v, (str, int, float, bool)):
                    base_metadata[k] = v
                else:
                    base_metadata[k] = str(v)

        chunks = chunk_document(
            text=content,
            metadata=base_metadata,
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
        )

        # Assign unique chunk IDs
        for i, chunk in enumerate(chunks):
            chunk.metadata["chunk_id"] = f"{article.id}-chunk-{i}"

        # 3. Add to ChromaDB (blocking IO, run in threadpool)
        await run_in_threadpool(
            self.vectorstore.add_documents,
            documents=chunks
        )

        # 4. Commit DB Transaction
        await self.session.commit()
        await self.session.refresh(article)
        
        return article

    async def delete_article(self, article: KnowledgeArticle) -> None:
        """
        Delete an article from Postgres and its chunks from ChromaDB.
        """
        # Delete from ChromaDB
        # We can delete using where metadata filter
        await run_in_threadpool(
            self.vectorstore._collection.delete,
            where={"article_id": str(article.id)}
        )

        # Delete from DB
        await self.session.delete(article)
        await self.session.commit()
