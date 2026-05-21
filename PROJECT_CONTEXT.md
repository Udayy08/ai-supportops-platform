# AI SupportOps — Project Context & Handover Document

## 1. Project Objective
**AI SupportOps** is a production-grade, multi-agent GenAI SaaS platform designed for customer support resolution. It is *not* a simple chatbot; it is an intelligent, workflow-driven orchestration platform that uses LangGraph to classify, retrieve knowledge, resolve issues autonomously, and gracefully escalate to human agents via approval gates when AI confidence is low.

**Core Technology Stack:**
- **Backend**: FastAPI, Python 3.10+
- **AI/LLM**: LangChain, LangGraph, LangSmith (Observability), OpenAI (`gpt-4o`)
- **RAG & Vector DB**: ChromaDB, `sentence-transformers` (`all-MiniLM-L6-v2`)
- **Database**: PostgreSQL (asyncpg) with SQLAlchemy 2.0 & Alembic
- **Evaluation**: RAGAS (Faithfulness, Relevancy, Precision)
- **Frontend** (Planned): Next.js

---

## 2. Architecture & Important Design Decisions
- **Multi-Tenant System**: Row-level isolation using a `TenantMixin`. Every core entity is strictly bound to a `tenant_id`.
- **Structured JSON Logging**: Implemented `structlog` bridged tightly with standard library `logging`. Ensures both application logs and third-party logs (Uvicorn, SQLAlchemy) are perfectly JSON-formatted in production for Datadog/CloudWatch ingestion.
- **Environment Configuration**: Used Pydantic Settings. *Design Decision*: Bypassed Pydantic v2's strict JSON-decoding for lists by storing values (like `CORS_ORIGINS`) as raw strings and parsing them dynamically via `@property` to avoid `.env` syntax crashes.
- **RAG Pipeline**: Built an isolated module (`app/rag`) wrapping ChromaDB and HuggingFace Embeddings. *Design Decision*: Configured a `ContextualRetriever` that forces `tenant_id` filtering at the vector-database level to prevent data leaks.
- **AI Observability & Traceability**: Designed the database schema to store `langsmith_run_id` directly on individual `Message` and `WorkflowRun` rows, allowing administrators to click directly from a dashboard into the exact LangSmith trace.

---

## 3. Folder Structure
```text
ai-supportops-platform/
├── backend/
│   ├── app/
│   │   ├── api/v1/         # Modular versioned routes
│   │   ├── core/           # Config, logging, middleware, exceptions
│   │   ├── db/             # Session management, Repositories
│   │   ├── models/         # SQLAlchemy declarative models
│   │   ├── rag/            # Embeddings, Vectorstore, Chunkers, Retriever
│   │   ├── schemas/        # Pydantic validation schemas
│   │   ├── services/       # Business logic layer
│   │   └── main.py         # FastAPI application entrypoint
│   ├── alembic/            # Database migration scripts
│   ├── scripts/            # CLI utilities (seed_kb.py, test_retrieval.py)
│   ├── Dockerfile          # Multi-stage container build
│   └── requirements.txt    # Python dependencies
├── infra/
│   └── docker-compose.yml  # Local dev services (Postgres, Redis, Chroma)
├── PROJECT_CONTEXT.md      # This document
└── PROJECT_PROGRESS.md     # High-level task tracker
```

---

## 4. Database Schema
A robust, highly normalized schema was designed to support complex AI workflows and human-in-the-loop governance:

**Core Domain:**
- `Tenant`: Multi-tenant boundary.
- `User`: RBAC (Super Admin, Admin, Agent, Viewer).
- `Ticket`: Core support request.
- `Conversation` & `Message`: Chat/Email turn-by-turn history.

**AI Workflow & Traceability:**
- `WorkflowRun`: A full LangGraph execution attempt.
- `WorkflowNodeExecution`: Per-agent node stats (latency, tokens, cost).

**AI Quality Gates:**
- `ApprovalRequest`: Human-in-the-loop queue for low-confidence AI responses.
- `HallucinationFlag`: Records failed factual consistency checks.
- `ConfidenceScore`: Granular retrieval and generation confidence scores.
- `Evaluation`: Stores RAGAS metrics (Faithfulness, Relevancy).

**Infrastructure & Analytics:**
- `AuditLog`: Append-only, immutable record of state changes.
- `TicketAnalyticsSnapshot`: Materialized daily pre-aggregated statistics to keep dashboard queries fast (O(1)).
- `KnowledgeArticle` & `AgentConfig`.

---

## 5. APIs Implemented
- The foundational API route structure (`/api/v1/`) is scaffolded.
- JWT Authentication dependencies (`deps.py`) and RBAC guards are implemented.
- **Note**: The actual REST endpoints for CRUD operations and Agent invocation are currently stubbed out pending Phase 5 implementation.

---

## 6. Docker & Infrastructure Setup
- **`Dockerfile`**: A multi-stage build optimizing for small image sizes and secure execution.
- **`docker-compose.yml`**: Configured to run:
  - `postgres`: Port 5432
  - `redis`: Port 6379 (For rate-limiting and Celery queues)
  - `chromadb`: Port 8001 (Vector database)

---

## 7. Environment Variables
Managed via `.env`. Crucial variables include:
- `ENVIRONMENT`: `development` | `production`
- `SECRET_KEY`: JWT signing key
- `BACKEND_CORS_ORIGINS`: Comma-separated list (e.g., `http://localhost:3000`)
- `POSTGRES_USER`, `POSTGRES_PASSWORD`, `POSTGRES_DB`
- `OPENAI_API_KEY`, `LANGCHAIN_API_KEY` (For LangSmith)

---

## 8. Features Completed
- ✅ **Phase 1**: High-level Architecture Planning.
- ✅ **Phase 2**: FastAPI Backend Foundation (Middleware, Auth stubs, Error handling, Logging).
- ✅ **Phase 3**: Database Models (15 tables with relationships, mixins, and Alembic integration).
- ✅ **Phase 4**: Complete RAG Pipeline (`sentence-transformers` embeddings, ChromaDB vectorstore, Contextual Retriever, Knowledge seeding scripts).

---

## 9. Pending Tasks
- **Phase 5: LangGraph Agents**: Implementing the actual graph nodes (Classifier, Retriever, Resolver, Quality Assessor).
- **API Controllers**: Filling in the stubbed `/api/v1/` endpoints.
- **Task Queues**: Integrating Celery to run evaluations and heavy agent workloads in the background.
- **Frontend Integration**: Building the Next.js UI dashboard.

---

## 10. Known Issues
- **Local Docker Requirement**: Alembic migrations (`alembic upgrade head`) and RAG seeding (`python -m scripts.seed_kb`) require PostgreSQL and ChromaDB to be running. If Docker Desktop is off, these commands will fail to connect.
- **Alembic Initial Migration**: The initial autogenerated schema file needs to be created against a live, clean PostgreSQL instance.

---

## 11. Next Development Steps
When development resumes, the recommended sequence is:
1. Ensure Docker Desktop is running.
2. Run `docker-compose up -d` in the `infra/` folder.
3. Generate and apply the initial Alembic migration (`alembic revision --autogenerate -m "init"` -> `alembic upgrade head`).
4. Run `python -m scripts.seed_kb` to populate the DB/Chroma with sample policies.
5. Begin **Phase 5**: Building the LangGraph multi-agent orchestration logic in `app/agents/`.
