# AI SupportOps Platform

## 1. Project Overview
**AI SupportOps** is a production-grade, multi-tenant, agentic GenAI SaaS platform designed to automate customer support resolution. It moves beyond simple conversational chatbots by implementing an intelligent, stateful, workflow-driven orchestration platform. The system uses a LangGraph multi-agent architecture to autonomously classify tickets, retrieve tenant-specific knowledge, generate grounded resolutions, evaluate its own hallucination risk, and gracefully escalate to human agents via approval gates when confidence falls below required thresholds.

## 2. Problem Statement
Modern customer support teams struggle with high volumes of repetitive inquiries. Traditional automation relies on rigid decision trees that fail at nuance, while naive LLM chatbots often hallucinate, leak cross-tenant data, or lack the ability to take decisive resolution actions. Teams need a system that can understand complex intent, rely strictly on verified internal policies, and know exactly when a human needs to intervene.

## 3. Business Use Case
AI SupportOps serves B2B SaaS companies or e-commerce platforms handling thousands of support tickets daily. It acts as an autonomous Tier-1 support agent that can instantly resolve billing, shipping, and technical queries based solely on a company's internal knowledge base, dramatically reducing Time to Resolution (TTR) while maintaining strict enterprise security and data isolation per tenant.

## 4. Key Features
- **Multi-Agent Orchestration**: 7-node LangGraph state machine.
- **Strict Data Isolation**: Row-level Postgres security and tenant-filtered vector searches.
- **Self-Evaluating Quality Gates**: Real-time hallucination checking and confidence scoring.
- **Human-in-the-Loop Escalation**: Automated creation of approval requests for low-confidence outputs.
- **Provider-Agnostic LLM Layer**: Designed for Groq, extensible to OpenAI/Anthropic.
- **Full Traceability**: Granular execution tracking across all agent nodes for continuous evaluation.

## 5. Multi-Tenant Architecture
The platform enforces strict row-level isolation using a `TenantMixin` across all PostgreSQL tables. Every core entity (Tickets, Conversations, Vector Documents) is strictly bound to a `tenant_id`. In the vector database (ChromaDB), all searches explicitly map a `tenant_id` metadata filter directly into the `where` clause, guaranteeing that one company's AI agent can never hallucinate policies from another company's knowledge base.

## 6. Phase 4 RAG Architecture
The RAG (Retrieval-Augmented Generation) pipeline employs a **dual-storage synchronization architecture**:
1. **Source of Truth**: Raw text and structured metadata are stored securely in PostgreSQL (`KnowledgeArticle` table).
2. **Vector Index**: Document chunks are embedded via HuggingFace `all-MiniLM-L6-v2` and indexed in ChromaDB for high-speed semantic search.
3. **Asynchrony**: Computationally heavy IO calls are pushed to FastAPI's background threadpool to prevent blocking the async event loop.

## 7. Phase 5 LangGraph Architecture
A **LangGraph `StateGraph`** orchestrates 7 sequential agent nodes through a typed `SupportState` dictionary. Each node reads the shared state, calls the LLM, and returns partial state updates that LangGraph merges automatically. A conditional edge routes the flow based on a configurable confidence threshold.

## 8. Phase 6 Evaluation & Observability Architecture

The platform includes a dedicated evaluation and observability layer that continuously measures AI quality, workflow performance, and operational reliability.

### LangSmith Observability

The system supports optional LangSmith integration for:

- End-to-end workflow tracing
- Node-level execution visibility
- Token usage monitoring
- Latency tracking
- Workflow auditing and debugging

LangSmith integration is fully configurable through environment variables and gracefully degrades when disabled.

### RAGAS Evaluation Framework

The platform evaluates generated responses using RAGAS metrics:

- Faithfulness
- Answer Relevancy
- Context Precision
- Context Recall

RAGAS evaluations run using the configured Groq Fast Model (`llama-3.1-8b-instant`) and do not require OpenAI.

### Confidence Scoring System

The workflow persists:

- Retrieval confidence
- Generation confidence
- Overall confidence
- Threshold comparison results

These scores are used to determine escalation and approval routing decisions.

### Hallucination Detection

The platform records:

- Grounding issues
- Hallucination severity
- Evidence citations
- Faithfulness measurements

These signals are stored for analytics, monitoring, and future quality improvements.

### Sampling-Based Evaluation

To control API usage and evaluation costs:

- Evaluations are optional
- Sampling percentage is configurable
- Evaluation execution can be disabled entirely

Configuration:

```env
ENABLE_RAGAS=true
EVALUATION_SAMPLE_PERCENTAGE=10
```

This allows production deployments to balance quality monitoring with operational cost.

## 9. Workflow Diagram
```mermaid
graph TD
    START([Ticket Submitted]) --> CLASSIFY[Classifier Agent]
    CLASSIFY --> SENTIMENT[Sentiment Agent]
    SENTIMENT --> RETRIEVE[RAG Retriever Agent]
    RETRIEVE --> RESOLVE[Resolution Generator]
    RESOLVE --> RESPONSE[Response Writer]
    RESPONSE --> QUALITY[Hallucination Checker]
    QUALITY -->|Confidence >= Threshold| AUTO_RESOLVE[Auto-Resolve]
    QUALITY -->|Confidence < Threshold| ESCALATE[Human Approval Escalation]
    AUTO_RESOLVE --> DONE([END])
    ESCALATE --> DONE
```

## 10. Tech Stack
- **Backend Framework**: FastAPI (Python 3.10+)
- **Database**: PostgreSQL (asyncpg), SQLAlchemy 2.0, Alembic
- **Agent Orchestration**: LangGraph, LangChain
- **LLM Provider**: Groq (`llama-3.3-70b-versatile`)
- **Vector Database**: ChromaDB
- **Embeddings**: `sentence-transformers` (`all-MiniLM-L6-v2`) via HuggingFace
- **Caching & Queues**: Redis
- **Containerization**: Docker, Docker Compose

## 11. Project Structure
```text
ai-supportops-platform/
├── backend/
│   ├── app/
│   │   ├── agents/         # LangGraph nodes, state, prompts, LLM factory
│   │   ├── api/v1/         # Modular versioned REST routes
│   │   ├── core/           # Config, logging, middleware, exceptions
│   │   ├── db/             # Session management, Repositories
│   │   ├── models/         # SQLAlchemy declarative models
│   │   ├── rag/            # Embeddings, Vectorstore, Chunkers, Retriever
│   │   ├── schemas/        # Pydantic validation schemas
│   │   ├── services/       # Business logic (WorkflowService)
│   │   └── main.py         # FastAPI application entrypoint
│   ├── alembic/            # Database migration scripts
│   ├── scripts/            # CLI utilities (seed, test scripts)
│   ├── Dockerfile          # Multi-stage container build
│   └── requirements.txt    # Python dependencies
├── PROJECT_PROGRESS.md     # Official Handover and Task Tracker
└── docker-compose.yml      # Infrastructure services
```

## 12. Database Architecture
A highly normalized, 15-table schema designed for AI workflow traceability:
- **Core Domain**: `Tenant`, `User`, `Ticket`, `Conversation`, `Message`
- **Workflow State**: `WorkflowRun`, `WorkflowNodeExecution`
- **Governance**: `ApprovalRequest`, `HallucinationFlag`, `ConfidenceScore`
- **Knowledge**: `KnowledgeArticle`, `AgentConfig`

## 13. ChromaDB Integration
ChromaDB runs as a standalone Docker service. The `TenantRetriever` seamlessly interfaces with it via an HTTP client, ensuring that `similarity_search_with_relevance_scores` returns highly contextualized document chunks filtered by `tenant_id`.

## 14. Groq Integration
The LLM layer is built around a provider-agnostic factory (`app/agents/llm.py`) currently defaulting to Groq via `langchain-groq`. It utilizes `llama-3.3-70b-versatile` for high-quality reasoning tasks and `llama-3.1-8b-instant` for faster, lightweight operations. JSON outputs are safely parsed to handle markdown block wrapping inherently generated by Llama models.

## 15. Docker Setup
The project utilizes a `docker-compose.yml` to spin up the required infrastructure layer locally:
- `postgres` (Port 5432)
- `redis` (Port 6379)
- `chromadb` (Port 8001)

## 16. Installation Instructions
1. Clone the repository.
2. Ensure Docker and Docker Compose are installed.
3. Start infrastructure: `docker compose up -d`
4. Set up the Python environment:
   ```bash
   cd backend
   python -m venv .venv
   source .venv/bin/activate
   pip install -r requirements.txt
   ```

## 17. Environment Variables
Create a `.env` file in the `backend/` directory:
```env
ENVIRONMENT="development"
SECRET_KEY="your_super_secret_key"
POSTGRES_USER="supportops"
POSTGRES_PASSWORD="supportops_dev_password"
POSTGRES_DB="supportops_db"
POSTGRES_HOST="localhost"
CHROMA_HOST="localhost"
CHROMA_PORT=8001
GROQ_API_KEY="gsk_your_groq_api_key"
AGENT_CONFIDENCE_THRESHOLD=0.7

# Observability & Evaluation
LANGCHAIN_TRACING_V2=false
LANGCHAIN_API_KEY="ls__..."
ENABLE_RAGAS=true
EVALUATION_SAMPLE_PERCENTAGE=10
```

## 18. Running Migrations
Run Alembic to initialize the PostgreSQL schema:
```bash
cd backend
source .venv/bin/activate
alembic upgrade head
```

## 19. Seeding Knowledge Base
Populate PostgreSQL and ChromaDB with demo corporate policies:
```bash
python scripts/seed_kb.py
```
*(This generates a `demo_tenant_id.txt` file used by the testing scripts.)*

## 20. Running RAG Tests
Validate tenant-scoped semantic retrieval:
```bash
python scripts/test_retrieval.py
```

## 21. Running Workflow Tests
Execute the end-to-end LangGraph multi-agent pipeline:
```bash
python scripts/test_workflow.py
```

## 22. Current Project Status
The platform is successfully built up to the agent orchestration layer. The infrastructure, database schemas, RAG pipeline, and LangGraph workflow are fully operational in a local testing environment. The next major step is integrating these components into the FastAPI HTTP layer.

## 23. Completed Phases
- ✅ **Phase 1**: Backend Foundation
- ✅ **Phase 2**: Infrastructure (Docker)
- ✅ **Phase 3**: Database Layer (SQLAlchemy/Alembic)
- ✅ **Phase 4**: RAG Pipeline (ChromaDB + sentence-transformers)
- ✅ **Phase 5**: LangGraph Multi-Agent Workflow (Groq integration)
- ✅ **Phase 6**: Evaluation & Observability (LangSmith & RAGAS)
- ✅ **Phase 7**: API Integration & Background Tasks (FastAPI, Pydantic)

## 24. Future Roadmap
- **Phase 8**: Frontend Dashboard (Next.js enterprise UI).
- **Phase 9**: Production Deployment & Kubernetes orchestration.

## 25. Known Limitations
1. **CPU Bound Embeddings**: `all-MiniLM-L6-v2` runs on the CPU. Large document ingestions will spike CPU usage without GPU acceleration.
2. **Synchronous Execution**: The LangGraph pipeline currently runs sequentially. Total latency per ticket can be 3-5 seconds.
3. **Ghost Vectors**: Deleting an article in Postgres directly (bypassing the application layer) does not automatically delete corresponding ChromaDB vectors.

## 26. Future Enhancements
- **Parallel Agent Execution**: Run the Classifier and Sentiment nodes concurrently.
- **Automated Re-indexing**: Add database triggers/webhooks to auto-sync Postgres updates to ChromaDB.
- **Provider Fallbacks**: Implement automatic failover from Groq to Anthropic/OpenAI during API outages.
