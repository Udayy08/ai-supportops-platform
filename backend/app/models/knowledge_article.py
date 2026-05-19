"""KnowledgeArticle model — documents ingested into ChromaDB for RAG."""

from __future__ import annotations

import uuid

from sqlalchemy import Boolean, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TenantMixin, TimestampMixin, UUIDPrimaryKeyMixin


class KnowledgeArticle(UUIDPrimaryKeyMixin, TenantMixin, TimestampMixin, Base):
    __tablename__ = "knowledge_articles"

    title: Mapped[str] = mapped_column(String(500), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    category: Mapped[str | None] = mapped_column(String(100), nullable=True, index=True)
    # Extra fields: author, version, tags, source_url, etc.
    metadata_: Mapped[dict] = mapped_column("metadata", JSONB, default=dict, nullable=False)
    # Name of the ChromaDB collection this article is embedded into
    chroma_collection: Mapped[str] = mapped_column(String(255), nullable=False)
    # Whether the article is active in the vector store
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    def __repr__(self) -> str:
        return f"<KnowledgeArticle id={self.id} title={self.title!r}>"
