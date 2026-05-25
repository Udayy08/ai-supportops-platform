"""Knowledge base routes — Document Management + RAG Integration."""

from __future__ import annotations

import uuid
from fastapi import APIRouter, Query, status, UploadFile, File, Form, Depends

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
from app.rag.knowledge_manager import KnowledgeManager
from app.utils.extractor import extract_text_from_upload
from app.config import settings

router = APIRouter(prefix="/knowledge", tags=["Knowledge Base"])


@router.get("", response_model=KnowledgeArticleListResponse, summary="List knowledge documents")
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
    "/upload",
    response_model=KnowledgeArticleResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Upload a document to the Knowledge Base",
)
async def upload_document(
    current_user: CurrentUser,
    db: DBSession,
    file: UploadFile = File(...),
    category: str | None = Form(None),
) -> KnowledgeArticleResponse:
    content = await extract_text_from_upload(file)
    filename = file.filename or "Untitled Document"
    file_type = filename.split(".")[-1].lower() if "." in filename else "unknown"

    metadata = {
        "filename": filename,
        "file_type": file_type
    }

    manager = KnowledgeManager(session=db, collection_name=settings.chroma_collection_name)
    
    # Check for existing article by filename and tenant_id
    from sqlalchemy import select
    from app.models.knowledge_article import KnowledgeArticle
    
    query = select(KnowledgeArticle).where(
        KnowledgeArticle.tenant_id == current_user.tenant_id,
        KnowledgeArticle.title == filename
    )
    result = await db.execute(query)
    existing_article = result.scalar_one_or_none()
    
    if existing_article:
        # Update existing article
        existing_article.content = content
        existing_article.category = category
        
        db_meta = dict(existing_article.metadata_ or {})
        db_meta.update(metadata)
        existing_article.metadata_ = db_meta
        
        await db.commit()
        article = await manager.reindex_article(existing_article)
    else:
        # Ingest new article
        article = await manager.ingest_article(
            tenant_id=current_user.tenant_id,
            title=filename,
            content=content,
            category=category,
            metadata=metadata
        )
    
    return KnowledgeArticleResponse.model_validate(article)


@router.post(
    "",
    response_model=KnowledgeArticleResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create article manually (auto-embeds into ChromaDB)",
)
async def create_article(
    body: KnowledgeArticleCreateRequest,
    current_user: CurrentUser,
    db: DBSession,
) -> KnowledgeArticleResponse:
    manager = KnowledgeManager(session=db, collection_name=settings.chroma_collection_name)
    article = await manager.ingest_article(
        tenant_id=current_user.tenant_id,
        title=body.title,
        content=body.content,
        category=body.category,
        metadata=body.metadata
    )
    return KnowledgeArticleResponse.model_validate(article)


@router.get("/{article_id}", response_model=KnowledgeArticleResponse, summary="Get document by ID")
async def get_article(
    article_id: uuid.UUID,
    current_user: CurrentUser,
    db: DBSession,
) -> KnowledgeArticleResponse:
    repo = KnowledgeRepository(db)
    article = await repo.get_by_id(article_id, tenant_id=current_user.tenant_id)
    if not article:
        raise NotFoundException(detail=f"Document '{article_id}' not found.")
    return KnowledgeArticleResponse.model_validate(article)


@router.post(
    "/{article_id}/reindex",
    response_model=KnowledgeArticleResponse,
    summary="Reindex a document into ChromaDB"
)
async def reindex_article(
    article_id: uuid.UUID,
    current_user: CurrentUser,
    db: DBSession,
) -> KnowledgeArticleResponse:
    repo = KnowledgeRepository(db)
    article = await repo.get_by_id(article_id, tenant_id=current_user.tenant_id)
    if not article:
        raise NotFoundException(detail=f"Document '{article_id}' not found.")
        
    manager = KnowledgeManager(session=db, collection_name=settings.chroma_collection_name)
    updated_article = await manager.reindex_article(article)
    return KnowledgeArticleResponse.model_validate(updated_article)


@router.post(
    "/{article_id}/refresh",
    response_model=KnowledgeArticleResponse,
    summary="Refresh document status"
)
async def refresh_article(
    article_id: uuid.UUID,
    current_user: CurrentUser,
    db: DBSession,
) -> KnowledgeArticleResponse:
    repo = KnowledgeRepository(db)
    article = await repo.get_by_id(article_id, tenant_id=current_user.tenant_id)
    if not article:
        raise NotFoundException(detail=f"Document '{article_id}' not found.")
    return KnowledgeArticleResponse.model_validate(article)


@router.put("/{article_id}", response_model=KnowledgeArticleResponse, summary="Update document + re-embed")
async def update_article(
    article_id: uuid.UUID,
    body: KnowledgeArticleUpdateRequest,
    current_user: CurrentUser,
    db: DBSession,
) -> KnowledgeArticleResponse:
    repo = KnowledgeRepository(db)
    article = await repo.get_by_id(article_id, tenant_id=current_user.tenant_id)
    if not article:
        raise NotFoundException(detail=f"Document '{article_id}' not found.")

    updated = await repo.update(article, **body.model_dump(exclude_none=True))
    manager = KnowledgeManager(session=db, collection_name=settings.chroma_collection_name)
    await manager.reindex_article(updated)
    return KnowledgeArticleResponse.model_validate(updated)


@router.delete(
    "/{article_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete document and remove from vector store",
)
async def delete_article(
    article_id: uuid.UUID,
    current_user: CurrentUser,
    db: DBSession,
) -> None:
    repo = KnowledgeRepository(db)
    article = await repo.get_by_id(article_id, tenant_id=current_user.tenant_id)
    if not article:
        raise NotFoundException(detail=f"Document '{article_id}' not found.")
        
    manager = KnowledgeManager(session=db, collection_name=settings.chroma_collection_name)
    await manager.delete_article(article)


@router.post("/search", response_model=list[KnowledgeSearchResult], summary="Semantic search")
async def search_knowledge(
    body: KnowledgeSearchRequest,
    current_user: CurrentUser,
    db: DBSession,
) -> list[KnowledgeSearchResult]:
    # Placeholder for direct semantic search API endpoint if needed later
    return []
