# ─────────────────────────────────────────────────────────────────────────────
# AI SupportOps — Makefile
# Common development commands
# ─────────────────────────────────────────────────────────────────────────────

.PHONY: help dev stop build test lint format migrate seed

help:  ## Show this help
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

# ── Docker ────────────────────────────────────────────────────────────────────

dev:  ## Start all services in development mode
	docker compose -f infra/docker-compose.yml up --build

dev-bg:  ## Start all services in background
	docker compose -f infra/docker-compose.yml up --build -d

stop:  ## Stop all services
	docker compose -f infra/docker-compose.yml down

build:  ## Build Docker images only
	docker compose -f infra/docker-compose.yml build

logs:  ## Tail backend logs
	docker compose -f infra/docker-compose.yml logs -f backend

# ── Database ──────────────────────────────────────────────────────────────────

migrate:  ## Run Alembic migrations
	cd backend && alembic upgrade head

migrate-create:  ## Create new migration (usage: make migrate-create MSG="add foo")
	cd backend && alembic revision --autogenerate -m "$(MSG)"

migrate-down:  ## Rollback last migration
	cd backend && alembic downgrade -1

seed:  ## Seed the database with sample data
	cd backend && python -m infra.scripts.seed_db

# ── Backend ───────────────────────────────────────────────────────────────────

backend-install:  ## Install backend dependencies
	cd backend && pip install -e ".[dev]"

backend-dev:  ## Run backend locally (no Docker)
	cd backend && uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

# ── Testing ───────────────────────────────────────────────────────────────────

test:  ## Run all backend tests
	cd backend && pytest

test-cov:  ## Run tests with HTML coverage report
	cd backend && pytest --cov=app --cov-report=html

# ── Code Quality ──────────────────────────────────────────────────────────────

lint:  ## Lint backend code
	cd backend && ruff check app tests

format:  ## Format backend code
	cd backend && ruff format app tests

typecheck:  ## Run mypy type checks
	cd backend && mypy app
