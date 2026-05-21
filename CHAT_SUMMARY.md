# AI SupportOps — Conversation & Project History Summary

This document summarizes the entire conversation history, from the initial architectural planning to the completion of the RAG pipeline.

## 1. Project Inception & Requirements (Phase 1)
- **Objective:** Build "AI SupportOps" — a production-grade, multi-agent GenAI SaaS platform for automated customer support resolution (not just a chatbot).
- **Core Tech Stack:** FastAPI, Next.js, LangGraph, LangChain, PostgreSQL (asyncpg), SQLAlchemy 2.0, ChromaDB, LangSmith, and RAGAS.
- **Architecture Design:** 
  - Designed a monolithic FastAPI backend with a clear modular folder structure (`api`, `core`, `db`, `models`, `rag`, `services`).
  - Defined a 6-agent LangGraph workflow (Classifier → Sentiment → Retriever → Resolver → Quality Assessor → Escalation Agent).
  - Outlined the database schema and RESTful API endpoints.

## 2. FastAPI Backend Foundation (Phase 2)
- **Core Setup:** Implemented a robust FastAPI foundation including CORS, TrustedHost middleware, and Redis-backed rate limiting.
- **Security & Errors:** Added JWT authentication (`security.py`), RBAC guards, and RFC 7807 Problem Details for standardized error handling.
- **Database Foundation:** Configured an async SQLAlchemy engine with connection pooling (`session.py`) and a generic `BaseRepository` for CRUD operations.
- **Docker:** Generated a multi-stage `Dockerfile` and a `docker-compose.yml` for local services (Postgres, Redis, ChromaDB).
- **Bug Fixes:**
  - **Pydantic Settings (`BACKEND_CORS_ORIGINS`):** Fixed an issue where Pydantic v2 attempted to JSON-decode a comma-separated `.env` list and crashed. Resolved by defining the fields as raw `str` and exposing the parsed list via a dynamic `@property`.
  - **Structlog Crash:** Fixed an `AttributeError` caused by `PrintLogger` lacking a `name` attribute during FastAPI startup. Overhauled `logging.py` to use `structlog.stdlib.ProcessorFormatter`, seamlessly bridging Uvicorn's standard library logs with Structlog to guarantee uniform JSON output in production.

## 3. Database Schema Implementation (Phase 3)
- **Base Mixins:** Implemented portable `UUIDPrimaryKeyMixin`, `TimestampMixin`, `SoftDeleteMixin`, and a `TenantMixin` to enforce row-level multi-tenancy.
- **Domain Models Created:**
  - **Core:** `Tenant`, `User`, `Ticket`, `Conversation`, `Message`.
  - **AI Traceability:** `WorkflowRun`, `WorkflowNodeExecution` (tracks tokens, latency, and LangSmith traces).
  - **Quality Gates:** `ApprovalRequest` (human-in-the-loop escalation), `HallucinationFlag`, `ConfidenceScore`, `Evaluation` (RAGAS metrics).
  - **Other:** `KnowledgeArticle`, `AgentConfig`, `AuditLog` (immutable ledger).
  - **Analytics:** `TicketAnalyticsSnapshot` (materialized daily aggregates to prevent heavy SQL aggregations on the dashboard).
- **Alembic:** Set up Alembic (`alembic.ini`, `env.py`) and resolved circular dependency issues by centralizing models in `app/models/__init__.py`. Manually scaffolded the initial migration script.

## 4. RAG Pipeline Implementation (Phase 4)
- **Dependencies:** Installed `chromadb`, `sentence-transformers`, `langchain`, and associated packages.
- **Embeddings:** Implemented `app/rag/embeddings.py` using HuggingFace's `all-MiniLM-L6-v2` as a fast, CPU-friendly singleton.
- **Chunking:** Implemented `app/rag/chunkers.py` utilizing LangChain's `RecursiveCharacterTextSplitter` (1000 chars, 200 overlap).
- **Vector Store:** Configured `app/rag/vectorstore.py` to connect to ChromaDB via HTTP client and return a LangChain `Chroma` instance.
- **Contextual Retriever:** Built `app/rag/retriever.py` to wrap Chroma searches. Critically, it enforces strict `tenant_id` filtering on all vector queries to prevent data leaks, and exposes similarity scores for AI confidence tracking.
- **Knowledge Manager:** Built `app/rag/knowledge_manager.py` to atomically sync document chunks between PostgreSQL and ChromaDB using FastAPI's `run_in_threadpool`.
- **Scripts:** Created `scripts/seed_kb.py` to ingest dummy support policies (Refunds, Shipping, FAQ) and `scripts/test_retrieval.py` for testing.

## 5. Known Issues & Pending Tasks (Phase 5+)
- **Known Issue:** Docker Desktop was not running on the host Windows machine. Consequently, the local PostgreSQL and ChromaDB containers could not be started. This prevented the application of Alembic migrations (`alembic upgrade head`) and the execution of the `seed_kb.py` script.
- **Pending Tasks:**
  1. Boot up Docker Desktop and run `docker-compose up -d`.
  2. Apply the Alembic database migrations.
  3. Execute `seed_kb.py` to populate the vector database.
  4. **Start Phase 5:** Implement the LangGraph multi-agent orchestration logic in `app/agents/` (Classifier, Resolver, Quality Assessor).
  5. Build out the actual REST API controller logic for endpoints currently sitting as stubs.
  6. Integrate Celery for asynchronous background tasks.
  7. Develop the Next.js frontend UI.
