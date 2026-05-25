import uuid
from datetime import datetime, timezone
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

        base_meta = metadata or {}
        base_meta.update({
            "processing_status": "PROCESSING",
            "indexed_status": "PENDING"
        })

        # 1. Create DB Record
        article = KnowledgeArticle(
            id=article_id,
            tenant_id=tenant_id,
            title=title,
            content=content,
            category=category,
            metadata_=base_meta,
            chroma_collection=chroma_collection,
            is_active=True,
        )
        self.session.add(article)
        await self.session.flush() # Get DB ID ready, but don't commit until vectors succeed

        try:
            # 2. Chunk Document
            # Base metadata for every chunk to enable strict filtering and citations
            chunk_metadata = {
                "article_id": str(article.id),
                "tenant_id": str(tenant_id),
                "title": title,
                "category": category or "General",
                # Traceability requested by user
                "source_document_id": str(article.id),
                "source_filename": base_meta.get("filename", title)
            }
            if metadata:
                # Add extra stringified metadata
                for k, v in metadata.items():
                    if isinstance(v, (str, int, float, bool)):
                        chunk_metadata[k] = v
                    else:
                        chunk_metadata[k] = str(v)

            chunks = chunk_document(
                text=content,
                metadata=chunk_metadata,
                chunk_size=chunk_size,
                chunk_overlap=chunk_overlap,
            )

            # Assign unique chunk IDs and chunk_index
            for i, chunk in enumerate(chunks):
                chunk.metadata["chunk_id"] = f"{article.id}-chunk-{i}"
                chunk.metadata["chunk_index"] = i

            # 3. Add to ChromaDB (blocking IO, run in threadpool)
            await run_in_threadpool(
                self.vectorstore.add_documents,
                documents=chunks
            )
            
            # Update DB Metadata for success
            db_meta = dict(article.metadata_)
            db_meta.update({
                "chunk_count": len(chunks),
                "processing_status": "COMPLETED",
                "indexed_status": "SUCCESS",
                "last_indexed_at": datetime.now(timezone.utc).isoformat()
            })
            article.metadata_ = db_meta

            # 4. Commit DB Transaction
            await self.session.commit()
            await self.session.refresh(article)
            
            return article
            
        except Exception as e:
            # If ChromaDB insertion fails, update DB to FAILED
            db_meta = dict(article.metadata_)
            db_meta.update({
                "processing_status": "FAILED",
                "indexed_status": "FAILED",
                "error": str(e)
            })
            article.metadata_ = db_meta
            await self.session.commit()
            raise

    async def reindex_article(self, article: KnowledgeArticle) -> KnowledgeArticle:
        """
        Re-chunk and re-embed an existing article into ChromaDB.
        """
        from sqlalchemy.orm.attributes import flag_modified
        
        db_meta = dict(article.metadata_ or {})
        db_meta.update({
            "processing_status": "PROCESSING",
            "indexed_status": "PENDING",
            "processing_started_at": datetime.now(timezone.utc).isoformat(),
            "processing_error": None
        })
        article.metadata_ = db_meta
        flag_modified(article, "metadata_")
        await self.session.commit()

        try:
            # 1. Delete old chunks from ChromaDB
            await run_in_threadpool(
                self.vectorstore._collection.delete,
                where={"article_id": str(article.id)}
            )

            # 2. Chunk and insert new
            chunk_metadata = {
                "article_id": str(article.id),
                "tenant_id": str(article.tenant_id),
                "title": article.title,
                "category": article.category or "General",
                "source_document_id": str(article.id),
                "source_filename": db_meta.get("filename", article.title)
            }
            
            chunks = chunk_document(
                text=article.content,
                metadata=chunk_metadata,
            )

            for i, chunk in enumerate(chunks):
                chunk.metadata["chunk_id"] = f"{article.id}-chunk-{i}"
                chunk.metadata["chunk_index"] = i

            if chunks:
                await run_in_threadpool(
                    self.vectorstore.add_documents,
                    documents=chunks
                )

            # 3. Mark success
            db_meta.update({
                "chunk_count": len(chunks),
                "processing_status": "COMPLETED",
                "indexed_status": "SUCCESS",
                "last_indexed_at": datetime.now(timezone.utc).isoformat(),
                "processing_completed_at": datetime.now(timezone.utc).isoformat(),
            })
            article.metadata_ = db_meta
            flag_modified(article, "metadata_")
            await self.session.commit()
            await self.session.refresh(article)
            return article
            
        except Exception as e:
            db_meta.update({
                "processing_status": "FAILED",
                "indexed_status": "FAILED",
                "error": str(e),
                "processing_error": str(e),
                "processing_completed_at": datetime.now(timezone.utc).isoformat(),
            })
            article.metadata_ = db_meta
            flag_modified(article, "metadata_")
            await self.session.commit()
            raise

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
