"""Analytics routes — dashboard KPIs and metrics."""

from __future__ import annotations

from fastapi import APIRouter, Query

from app.api.deps import CurrentUser, DBSession
from app.schemas.analytics import (
    AgentPerformanceResponse,
    CategoryBreakdownItem,
    KPIOverviewResponse,
    SentimentDistributionResponse,
    TicketVolumeResponse,
)

router = APIRouter(prefix="/analytics", tags=["Analytics"])


@router.get("/overview", response_model=KPIOverviewResponse, summary="Dashboard KPI overview")
async def get_overview(current_user: CurrentUser, db: DBSession) -> KPIOverviewResponse:
    # TODO: Implement real aggregation queries (Phase 2)
    return KPIOverviewResponse(
        total_tickets=0,
        open_tickets=0,
        resolved_tickets=0,
        escalated_tickets=0,
        resolution_rate=0.0,
        avg_resolution_time_hours=0.0,
        ai_resolution_rate=0.0,
    )

@router.get(
    "/summary",
    response_model=KPIOverviewResponse,
    summary="Dashboard summary",
    description="Returns aggregate KPI metrics for the entire system."
)
async def get_summary(current_user: CurrentUser, db: DBSession) -> KPIOverviewResponse:
    # Delegate to overview for now
    return await get_overview(current_user=current_user, db=db)


@router.get("/tickets", response_model=TicketVolumeResponse, summary="Ticket volume over time")
async def get_ticket_volume(
    current_user: CurrentUser,
    db: DBSession,
    days: int = Query(default=30, ge=1, le=365),
) -> TicketVolumeResponse:
    # TODO: Implement time-series aggregation
    return TicketVolumeResponse(data=[], period_days=days)


@router.get("/categories", response_model=list[CategoryBreakdownItem], summary="Category breakdown")
async def get_categories(current_user: CurrentUser, db: DBSession) -> list[CategoryBreakdownItem]:
    return []


@router.get(
    "/sentiment",
    response_model=SentimentDistributionResponse,
    summary="Sentiment distribution",
)
async def get_sentiment(current_user: CurrentUser, db: DBSession) -> SentimentDistributionResponse:
    return SentimentDistributionResponse(positive=0, neutral=0, negative=0, angry=0, total=0)


@router.get("/agents", response_model=list[AgentPerformanceResponse], summary="Agent performance")
async def get_agent_performance(
    current_user: CurrentUser, db: DBSession
) -> list[AgentPerformanceResponse]:
    return []
