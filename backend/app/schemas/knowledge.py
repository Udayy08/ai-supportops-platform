"""Pydantic schemas for Knowledge Base endpoints."""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class KnowledgeArticleCreateRequest(BaseModel):
    title: str = Field(..., min_length=1, max_length=500)
    content: str = Field(..., min_length=1)
    category: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class KnowledgeArticleUpdateRequest(BaseModel):
    title: str | None = Field(None, max_length=500)
    content: str | None = None
    category: str | None = None
    is_active: bool | None = None
    metadata: dict[str, Any] | None = None

from pydantic import BaseModel, Field, model_validator

class KnowledgeArticleResponse(BaseModel):
    id: uuid.UUID
    tenant_id: uuid.UUID
    title: str
    content: str
    category: str | None
    metadata: dict[str, Any]
    chroma_collection: str
    is_active: bool
    created_at: datetime
    updated_at: datetime

    @model_validator(mode='before')
    @classmethod
    def map_metadata(cls, data: Any) -> Any:
        # If it's an ORM model, grab metadata_
        if hasattr(data, 'metadata_'):
            # Some sqlalchemy models might be passed as dicts or objects
            # Return a dict for Pydantic v2 to validate
            return {
                'id': data.id,
                'tenant_id': data.tenant_id,
                'title': data.title,
                'content': data.content,
                'category': data.category,
                'metadata': data.metadata_,
                'chroma_collection': data.chroma_collection,
                'is_active': data.is_active,
                'created_at': data.created_at,
                'updated_at': data.updated_at,
            }
        return data

    model_config = {"from_attributes": True}


class KnowledgeArticleListResponse(BaseModel):
    items: list[KnowledgeArticleResponse]
    total: int
    page: int
    page_size: int
    has_next: bool


class KnowledgeSearchRequest(BaseModel):
    query: str = Field(..., min_length=1, max_length=1000)
    top_k: int = Field(default=5, ge=1, le=20)
    category: str | None = None


class KnowledgeSearchResult(BaseModel):
    article_id: uuid.UUID
    title: str
    content_snippet: str
    category: str | None
    relevance_score: float
