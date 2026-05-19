"""Evaluation routes — trigger RAGAS runs, view results, manage datasets."""

from __future__ import annotations

import uuid

from fastapi import APIRouter, status

from app.api.deps import CurrentUser, DBSession, Pagination
from app.core.exceptions import NotFoundException
from app.schemas.agent import (
    EvaluationMetricsSummary,
    EvaluationResponse,
    EvaluationRunRequest,
)

router = APIRouter(prefix="/evaluations", tags=["Evaluations"])


@router.post(
    "/run",
    status_code=status.HTTP_202_ACCEPTED,
    summary="Trigger RAGAS evaluation batch (async)",
)
async def run_evaluation(
    body: EvaluationRunRequest,
    current_user: CurrentUser,
    db: DBSession,
) -> dict:
    # TODO: Dispatch to Celery worker / background task (Phase 4)
    return {
        "message": "Evaluation run queued.",
        "eval_type": body.eval_type,
        "conversation_count": len(body.conversation_ids) if body.conversation_ids else "last 24h",
    }


@router.get("", response_model=list[EvaluationResponse], summary="List evaluation runs")
async def list_evaluations(
    current_user: CurrentUser,
    db: DBSession,
    pagination: Pagination,
) -> list[EvaluationResponse]:
    from app.db.repositories.evaluation_repo import EvaluationRepository
    repo = EvaluationRepository(db)
    evals = await repo.list_by_tenant(
        current_user.tenant_id, limit=pagination.page_size, offset=pagination.offset
    )
    return [EvaluationResponse.model_validate(e) for e in evals]


@router.get("/metrics", response_model=EvaluationMetricsSummary, summary="Aggregate eval metrics")
async def get_metrics(
    current_user: CurrentUser,
    db: DBSession,
) -> EvaluationMetricsSummary:
    # TODO: Compute real aggregations from DB (Phase 4)
    return EvaluationMetricsSummary(
        avg_faithfulness=0.0,
        avg_answer_relevancy=0.0,
        avg_context_relevancy=0.0,
        avg_context_precision=0.0,
        total_evaluations=0,
        period_days=30,
    )


@router.get("/{eval_id}", response_model=EvaluationResponse, summary="Get evaluation detail")
async def get_evaluation(
    eval_id: uuid.UUID,
    current_user: CurrentUser,
    db: DBSession,
) -> EvaluationResponse:
    from app.db.repositories.evaluation_repo import EvaluationRepository
    repo = EvaluationRepository(db)
    evaluation = await repo.get_by_id(eval_id, tenant_id=current_user.tenant_id)
    if not evaluation:
        raise NotFoundException(detail=f"Evaluation '{eval_id}' not found.")
    return EvaluationResponse.model_validate(evaluation)
