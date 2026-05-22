# AI SupportOps — Project Progress & Handover Document

## Documentation Maintenance Policy
1. After every future phase completion, `README.md` must be updated.
2. After every future phase completion, `PROJECT_PROGRESS.md` must be updated.
3. Every phase must include:
   - architecture summary
   - files created
   - files modified
   - dependencies added
   - validation results
   - limitations
4. Documentation updates must be included in the same git commit as the phase implementation.
5. No phase may be marked complete until documentation is updated.

---

## Current Repository Status

**Completed Phases:** 
- Phase 1: Backend Foundation
- Phase 2: Infrastructure
- Phase 3: Database Layer
- Phase 4: RAG Pipeline
- Phase 5: LangGraph Multi-Agent Workflow
- Phase 6: Evaluation & Observability

**Pending Phases:**
- Phase 7: FastAPI APIs
- Phase 8: Frontend UI
- Phase 9: Deployment
- Phase 10: Documentation & Presentation Assets

**Current Capabilities:**
- Full Multi-Tenant data isolation at the DB and Vector levels.
- Configured PostgreSQL, Redis, and ChromaDB infrastructure running locally via Docker Compose.
- Complete 15-table SQLAlchemy schema mapped and migrated via Alembic.
- Robust RAG ingestion and retrieval utilizing `sentence-transformers`.
- 7-Node LangGraph multi-agent orchestration capable of completely autonomous problem resolution, hallucination detection, and human-in-the-loop escalation.
- Provider-agnostic LLM interfacing powered by Groq.
- Native LangSmith workflow monitoring and RAGAS offline evaluation engine for Faithfulness and Context Precision scoring.

**Infrastructure Status:**
- `docker-compose.yml` configured and running perfectly locally.
- Vector store (ChromaDB) and Relational DB (Postgres) successfully synchronized.

---

## Phase 1: Backend Foundation

### Objective
Establish the foundational FastAPI project structure, configuration management, and initial application skeleton.

### Architecture Implemented
- Standardized monolithic FastAPI structure (`app/api`, `app/core`, `app/models`, `app/services`).
- Pydantic Settings-based centralized configuration management.
- Custom structured JSON logging system utilizing `structlog`.

### Files Created
- `backend/app/main.py`
- `backend/app/config.py`
- `backend/app/core/logging.py`
- `backend/app/core/exceptions.py`
- `backend/app/core/middleware.py`

### Files Modified
- `backend/requirements.txt`
- `backend/.env`

### Dependencies Added
- `fastapi`, `uvicorn`, `pydantic-settings`, `structlog`

### Database Changes
- None (Phase 1 was strictly API/Core foundation).

### Docker Changes
- Created the initial `backend/Dockerfile` using multi-stage builds.

### Validation Performed
- Started Uvicorn locally to verify health-check endpoints.
- Validated `structlog` output format.

### Results
- Fast, secure, and easily extensible FastAPI foundation established.

### Issues Encountered
- Pydantic v2 strict list parsing issues with `CORS_ORIGINS` in `.env`.

### Fixes Applied
- Configured `CORS_ORIGINS` as a raw string and used a computed property `@property` to dynamically parse it, avoiding application crashes on boot.

### Lessons Learned
- Centralized custom error handlers (in `exceptions.py`) significantly streamline future API development.

### Known Limitations
- API routes are currently stubbed and return mocked data.

### Git Commit Reference
*Completed prior to formal tracking.*

---

## Phase 2: Infrastructure

### Objective
Set up the local Docker environment required to support the application's external dependencies.

### Architecture Implemented
- Local Docker Compose orchestrator defining networks and persistent volumes for microservices.

### Files Created
- `infra/docker-compose.yml`

### Files Modified
- `backend/.env` (Updated connection strings)

### Dependencies Added
- None

### Database Changes
- None

### Docker Changes
- Created configurations for `postgres:15-alpine`, `redis:7-alpine`, and `chromadb/chroma:latest`.

### Validation Performed
- Ran `docker compose up -d` and checked container health statuses.

### Results
- All infrastructure services booted correctly with persistent data volumes.

### Issues Encountered
- ChromaDB port conflicts with existing local services.

### Fixes Applied
- Mapped ChromaDB to port `8001` explicitly.

### Lessons Learned
- Pre-defining network bridges in docker-compose prevents microservice discovery issues later.

### Known Limitations
- The infrastructure is optimized for local development, not production orchestration (Kubernetes needed later).

### Git Commit Reference
*Completed prior to formal tracking.*

---

## Phase 3: Database Layer

### Objective
Design and implement the SQLAlchemy ORM models and Alembic migrations for a highly normalized, multi-tenant environment.

### Architecture Implemented
- Base mixins (`TenantMixin`, `TimestampMixin`, `UUIDPrimaryKeyMixin`) applied across the domain to ensure consistency.
- 15 relational tables grouped by Domain (Tickets, Messages), Workflow (Runs, Executions), Governance (Approvals, Flags), and Knowledge.
- Asynchronous DB sessions (`asyncpg`).

### Files Created
- `backend/alembic.ini`
- `backend/alembic/env.py`
- `backend/app/db/session.py`
- `backend/app/db/base.py`
- `backend/app/models/base.py`
- `backend/app/models/ticket.py`, `user.py`, `conversation.py`, `message.py`, `evaluation.py`, `approval.py`, `quality.py`, `workflow.py`, `knowledge.py`

### Files Modified
- `backend/requirements.txt`

### Dependencies Added
- `sqlalchemy`, `alembic`, `asyncpg`, `psycopg2-binary`

### Database Changes
- Entire schema defined and staged for generation.

### Docker Changes
- None

### Validation Performed
- Verified SQLAlchemy model compilation and relationship integrity visually.

### Results
- A highly normalized schema prepared for complex AI workflow traceability.

### Issues Encountered
- Circular import dependencies between models when defining `relationship()`.

### Fixes Applied
- Used string-based relationship references (e.g., `"Ticket"`) and centralized the metadata registry in `db/base.py`.

### Lessons Learned
- Explicit string references in SQLAlchemy are critical in large projects to avoid import cycles.

### Known Limitations
- An Alembic schema bug prevented immediate migration (fixed in Phase 4).

### Git Commit Reference
*Completed prior to formal tracking.*

---

## Phase 4: RAG Pipeline

### Objective
Implement a production-ready, tenant-isolated Retrieval-Augmented Generation pipeline bridging PostgreSQL and ChromaDB.

### Architecture Implemented
- **Dual-Storage Synchronization**: Raw text and metadata in Postgres; vectorized chunks in ChromaDB.
- **Data Protection**: Strict `tenant_id` filtering directly injected into ChromaDB `where` clauses.
- **Asynchrony**: Heavy IO operations pushed to `fastapi.concurrency.run_in_threadpool`.

### Files Created
- `backend/app/rag/__init__.py`
- `backend/app/rag/embeddings.py`
- `backend/app/rag/chunkers.py`
- `backend/app/rag/vectorstore.py`
- `backend/app/rag/retriever.py`
- `backend/app/rag/knowledge_manager.py`
- `backend/scripts/seed_kb.py`
- `backend/scripts/test_retrieval.py`
- `backend/alembic/versions/98b47845b53a_initial_schema.py`

### Files Modified
- `backend/requirements.txt`
- `backend/app/models/base.py`
- `backend/.env`

### Dependencies Added
- `chromadb>=0.4.24`, `sentence-transformers>=2.5.1`, `langchain>=0.1.13`, `langchain-community>=0.0.29`, `langchain-chroma>=0.1.0`, `langchain-huggingface>=0.0.1`, `langchain-text-splitters>=0.0.1`, `torch>=2.2.0`

### Database Changes
- Regenerated the Alembic migration tree, creating the official migration `98b47845b53a` to build out the schema.

### Docker Changes
- None

### Validation Performed
- **Seeding Test**: `seed_kb.py` successfully completed atomic ingestion.
- **Retrieval Test**: `test_retrieval.py` successfully executed tenant-isolated similarity searches and correctly ranked retrieved documents.

### Results
- System successfully isolates tenant data and returns highly relevant context via Cosine Similarity.

### Issues Encountered
- **Database Bug**: `TenantMixin` lacked a `ForeignKey` relationship to `tenants.id`, crashing the initial migration.
- **Deprecation Warnings**: LangChain updated its HuggingFace embedding wrappers mid-development.

### Fixes Applied
- Added `ForeignKey("tenants.id")` to `TenantMixin`.
- Transitioned to the modern `langchain_huggingface` package.

### Lessons Learned
- SQLAlchemy mixin Foreign Keys must be carefully defined to prevent join resolution failures.

### Known Limitations
- `all-MiniLM-L6-v2` embedding runs on CPU. Large ingestions will cause CPU spikes.
- Hard-deleting chunks directly in Postgres causes "ghost vectors" in ChromaDB.

### Git Commit Reference
*Pending user commit (`git commit -m "feat(rag): implement Phase 4 RAG pipeline..."`)*

---

## Phase 5: LangGraph Multi-Agent Workflow

### Objective
Build the autonomous support agent orchestration layer using LangGraph and Groq.

### Architecture Implemented
- **StateGraph Machine**: 7-node sequential execution flow (`classifier → retriever → sentiment → resolution → response_writer → hallucination_checker → human_approval`).
- **Provider-Agnostic LLM**: Centralized factory utilizing `langchain-groq` and `llama-3.3-70b-versatile`.
- **Conditional Edges**: Dynamic routing based on calculated Hallucination/Confidence scores.

### Files Created
- `backend/app/agents/state.py` (Typed `SupportState`)
- `backend/app/agents/llm.py`
- `backend/app/agents/graph.py`
- `backend/app/agents/nodes/classifier.py`
- `backend/app/agents/nodes/retriever.py`
- `backend/app/agents/nodes/sentiment.py`
- `backend/app/agents/nodes/resolution.py`
- `backend/app/agents/nodes/response_writer.py`
- `backend/app/agents/nodes/hallucination.py`
- `backend/app/agents/nodes/human_approval.py`
- `backend/app/agents/prompts/templates.py`
- `backend/app/services/workflow_service.py`
- `backend/scripts/test_workflow.py`

### Files Modified
- `backend/requirements.txt`
- `backend/app/config.py`
- `backend/.env`
- `backend/app/agents/__init__.py`
- `backend/app/agents/nodes/__init__.py`

### Dependencies Added
- `langgraph>=0.0.28`, `langchain-groq>=0.1.0`

### Database Changes
- None (Utilized existing Phase 3 schema models).

### Docker Changes
- None

### Validation Performed
- Compiled LangGraph and verified Node connections.
- Executed `scripts/test_workflow.py` through 3 end-to-end customer scenarios.

### Results
- The agent correctly retrieved knowledge, formatted responses, detected ungrounded hallucinated claims, and dynamically escalated to human review when required.

### Issues Encountered
- **JSON Decoding Errors**: Groq models frequently wrapped requested JSON responses inside Markdown code blocks (e.g., ` ```json `), causing python `json.loads` to crash.

### Fixes Applied
- Implemented a centralized `parse_json_response` helper in `llm.py` that strips all markdown syntax dynamically before attempting to deserialize.

### Lessons Learned
- Always sanitize raw string outputs from LLMs before strict validation, regardless of the prompt instructions.

### Known Limitations
- Workflow operates sequentially (5-10s latency). Future optimization could parallelize Classifier and Sentiment nodes.
- Execution tracking is prepared but not yet physically persisted to Postgres (Requires Phase 6 API integration).

### Git Commit Reference
*Pending user commit (`git commit -m "feat(agents): implement Phase 5 LangGraph multi-agent workflow with Groq"`)*

---

## Phase 6: Evaluation & Observability

### Objective
Implement enterprise-grade observability and offline evaluation capabilities to monitor agent workflow execution, track AI hallucinations, and assess answer quality.

### Architecture Implemented
- **Real-time Observability (`app/observability/`)**: Deep integration with LangSmith. Traces every LangGraph node execution, capturing token usage, latency, inputs, outputs, and mapping a run URL directly to the backend. **Fully optional and configurable** via `LANGCHAIN_TRACING_V2`; fails gracefully if disabled.
- **Offline Evaluation (`app/evaluation/`)**: A dedicated evaluation engine powered by the RAGAS framework. It **strictly utilizes Groq** (`GROQ_FAST_MODEL` / `llama-3.1-8b-instant`), with zero OpenAI dependencies. Asynchronously scores historical conversations across 4 key metrics: Faithfulness, Answer Relevancy, Context Precision, and Context Recall.
- **Sampling Framework**: To conserve tokens and limit API costs, RAGAS evaluations are probabilistic. The workflow actively samples runs based on `EVALUATION_SAMPLE_PERCENTAGE` and `ENABLE_RAGAS` configuration.
- **Quality Persistence**: Granular confidence scores and hallucination flags from LangGraph states are extracted and persisted to `ConfidenceScore` and `HallucinationFlag` models.

### Files Created
- `backend/app/evaluation/ragas_evaluator.py`
- `backend/app/evaluation/confidence.py`
- `backend/app/evaluation/hallucination.py`
- `backend/app/observability/langsmith_tracer.py`
- `backend/app/observability/metrics.py`
- `backend/app/observability/monitoring.py`
- `backend/scripts/run_evaluations.py`

### Files Modified
- `backend/requirements.txt`
- `backend/app/services/workflow_service.py`

### Dependencies Added
- `ragas>=0.1.5`
- `langsmith>=0.1.20`

### Database Changes
- None required (utilized the existing schema prepared in Phase 3 for `ConfidenceScore`, `HallucinationFlag`, and `WorkflowRun`).

### Docker Changes
- None

### Validation Performed
- Executed `scripts/test_workflow.py` to verify successful LangSmith trace generation and token tracking.
- Executed `scripts/run_evaluations.py` to verify RAGAS integration via the `llama-3.3-70b-versatile` LLM.

### Results
- Workflows now successfully generate a `langsmith_run_url`.
- RAGAS evaluation properly formats HuggingFace datasets and accurately scores historical tickets using purely open-source models (Groq Llama).

### Issues Encountered
- **RAGAS Validation Errors**: RAGAS `0.4.x` requires strict column naming (`user_input`, `response`, `retrieved_contexts`, `reference`) instead of the older `question`/`answer`/`contexts` names.
- **LangSmith Auth**: Running without a valid `LANGCHAIN_API_KEY` raised `LangSmithAuthError` during multipart payload syncing.

### Fixes Applied
- Renamed HuggingFace Dataset keys in `ragas_evaluator.py` to match RAGAS `0.4.x` strict validation schemas.
- Modified `WorkflowService` to handle `langsmith_run_url` extraction safely when `LANGCHAIN_API_KEY` is not present, failing gracefully without breaking the agent loop.

### Lessons Learned
- RAGAS requires explicit `reference` texts (ground truth) to compute `context_precision` and `context_recall`. Reference-free metrics are limited to `faithfulness` and `answer_relevancy`.

### Known Limitations
- Offline batch evaluation scripts (`run_evaluations.py`) are CLI-based. They will be transitioned to Celery background workers in Phase 7.

### Git Commit Reference
*Pending user commit (`git commit -m "feat(eval): implement Phase 6 Evaluation & Observability"`)*

---

## Phase 7 Planning

### Objectives
Integrate the LangGraph multi-agent workflow into the FastAPI HTTP layer. Implement background task execution for heavy workloads, and formally persist all `WorkflowRun` telemetry into the database.

### Expected Architecture
- **API Controllers**: FastAPI routers that expose endpoints to initiate ticket resolution workflows.
- **Asynchronous Workers**: Integration with Celery/Redis to shift LangGraph execution out of the synchronous HTTP request-response cycle.
- **Telemetry Persistence**: Extending `WorkflowService` to officially write `WorkflowNodeExecution` metrics (latency, token costs) and `ApprovalRequests` to PostgreSQL.

### Expected Files
- `backend/app/api/v1/tickets.py` (Update stubs)
- `backend/app/api/v1/agents.py` (Update stubs)
- `backend/app/worker.py` (Celery initialization)

### Integration Points
- Frontend HTTP Clients -> FastAPI Endpoints
- FastAPI -> Celery Broker (Redis)
- Celery Worker -> LangGraph Workflow (`app/agents/graph.py`)
- LangGraph Workflow -> PostgreSQL (Traceability storage)
