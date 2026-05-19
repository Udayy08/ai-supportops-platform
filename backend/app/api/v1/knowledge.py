"""Knowledge base routes — CRUD + semantic search."""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Query, status

from app.api.deps import CurrentUser, DBSession, Pagination
from app.core.exceptions import NotFoundException
from app.db.repositories.knowledge_repo import KnowledgeRepository
from app.schemas.knowledge import (
    KnowledgeArticleCreateRequest,
    KnowledgeArticleListResponse,
    KnowledgeArticleResponse,
    KnowledgeArticleUpdateRequest,
    KnowledgeSearchRequest,
    KnowledgeSearchResult,
)

router = APIRouter(prefix="/knowledge", tags=["Knowledge Base"])


@router.get("", response_model=KnowledgeArticleListResponse, summary="List knowledge articles")
async def list_articles(
    current_user: CurrentUser,
    db: DBSession,
    pagination: Pagination,
    category: str | None = Query(None),
    is_active: bool | None = Query(None),
    search: str | None = Query(None),
) -> KnowledgeArticleListResponse:
    repo = KnowledgeRepository(db)
    articles, total = await repo.list_paginated(
        tenant_id=current_user.tenant_id,
        page=pagination.page,
        page_size=pagination.page_size,
        category=category,
        is_active=is_active,
        search=search,
    )
    return KnowledgeArticleListResponse(
        items=[KnowledgeArticleResponse.model_validate(a) for a in articles],
        total=total,
        page=pagination.page,
        page_size=pagination.page_size,
        has_next=(pagination.page * pagination.page_size) < total,
    )


@router.post(
    "",
    response_model=KnowledgeArticleResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create article (auto-embeds into ChromaDB)",
)
async def create_article(
    body: KnowledgeArticleCreateRequest,
    current_user: CurrentUser,
    db: DBSession,
) -> KnowledgeArticleResponse:
    from app.config import settings
    repo = KnowledgeRepository(db)
    article = await repo.create(
        tenant_id=current_user.tenant_id,
        chroma_collection=settings.chroma_collection_name,
        **body.model_dump(),
    )
    # TODO: Trigger ChromaDB embedding ingestion (Phase 3 — RAG pipeline)
    return KnowledgeArticleResponse.model_validate(article)


@router.get("/{article_id}", response_model=KnowledgeArticleResponse, summary="Get article by ID")
async def get_article(
    article_id: uuid.UUID,
    current_user: CurrentUser,
    db: DBSession,
) -> KnowledgeArticleResponse:
    repo = KnowledgeRepository(db)
    article = await repo.get_by_id(article_id, tenant_id=current_user.tenant_id)
    if not article:
        raise NotFoundException(detail=f"Article '{article_id}' not found.")
    return KnowledgeArticleResponse.model_validate(article)


@router.put("/{article_id}", response_model=KnowledgeArticleResponse, summary="Update article + re-embed")
async def update_article(
    article_id: uuid.UUID,
    body: KnowledgeArticleUpdateRequest,
    current_user: CurrentUser,
    db: DBSession,
) -> KnowledgeArticleResponse:
    repo = KnowledgeRepository(db)
    article = await repo.get_by_id(article_id, tenant_id=current_user.tenant_id)
    if not article:
        raise NotFoundException(detail=f"Article '{article_id}' not found.")

    updated = await repo.update(article, **body.model_dump(exclude_none=True))
    # TODO: Re-trigger ChromaDB embedding (Phase 3)
    return KnowledgeArticleResponse.model_validate(updated)


@router.delete(
    "/{article_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Deactivate article + remove from vector store",
)
async def delete_article(
    article_id: uuid.UUID,
    current_user: CurrentUser,
    db: DBSession,
) -> None:
    repo = KnowledgeRepository(db)
    article = await repo.get_by_id(article_id, tenant_id=current_user.tenant_id)
    if not article:
        raise NotFoundException(detail=f"Article '{article_id}' not found.")
    await repo.update(article, is_active=False)
    # TODO: Remove from ChromaDB (Phase 3)


@router.post("/search", response_model=list[KnowledgeSearchResult], summary="Semantic search")
async def search_knowledge(
    body: KnowledgeSearchRequest,
    current_user: CurrentUser,
    db: DBSession,
) -> list[KnowledgeSearchResult]:
    # TODO: Implement ChromaDB semantic search (Phase 3 — RAG pipeline)
    return []
