"""Agent config routes — view and update per-agent LLM and prompt config."""

from __future__ import annotations

from fastapi import APIRouter

from app.api.deps import CurrentUser, DBSession, require_role
from app.core.exceptions import NotFoundException
from app.models.user import UserRole
from app.schemas.agent import AgentConfigResponse, AgentConfigUpdateRequest

router = APIRouter(prefix="/agents", tags=["Agent Management"])

VALID_AGENT_NAMES = {"classifier", "sentiment", "retriever", "resolver", "quality", "escalation"}


@router.get("/configs", response_model=list[AgentConfigResponse], summary="List all agent configs")
async def list_agent_configs(current_user: CurrentUser, db: DBSession) -> list[AgentConfigResponse]:
    from app.db.repositories.agent_repo import AgentConfigRepository
    repo = AgentConfigRepository(db)
    configs = await repo.list_by_tenant(current_user.tenant_id)
    return [AgentConfigResponse.model_validate(c) for c in configs]


@router.get(
    "/configs/{agent_name}",
    response_model=AgentConfigResponse,
    summary="Get config for a specific agent",
)
async def get_agent_config(
    agent_name: str,
    current_user: CurrentUser,
    db: DBSession,
) -> AgentConfigResponse:
    if agent_name not in VALID_AGENT_NAMES:
        raise NotFoundException(detail=f"Agent '{agent_name}' does not exist.")
    from app.db.repositories.agent_repo import AgentConfigRepository
    repo = AgentConfigRepository(db)
    config = await repo.get_by_name(agent_name, tenant_id=current_user.tenant_id)
    if not config:
        raise NotFoundException(detail=f"Config for agent '{agent_name}' not found.")
    return AgentConfigResponse.model_validate(config)


@router.put(
    "/configs/{agent_name}",
    response_model=AgentConfigResponse,
    summary="Update agent config (admin only)",
    dependencies=[__import__("fastapi", fromlist=["Depends"]).Depends(require_role(UserRole.ADMIN))],
)
async def update_agent_config(
    agent_name: str,
    body: AgentConfigUpdateRequest,
    current_user: CurrentUser,
    db: DBSession,
) -> AgentConfigResponse:
    if agent_name not in VALID_AGENT_NAMES:
        raise NotFoundException(detail=f"Agent '{agent_name}' does not exist.")
    from app.db.repositories.agent_repo import AgentConfigRepository
    repo = AgentConfigRepository(db)
    config = await repo.get_by_name(agent_name, tenant_id=current_user.tenant_id)
    if not config:
        raise NotFoundException(detail=f"Config for agent '{agent_name}' not found.")
    updated = await repo.update(config, **body.model_dump(exclude_none=True))
    return AgentConfigResponse.model_validate(updated)


@router.get("/status", summary="Get real-time agent pipeline status")
async def get_agent_status(current_user: CurrentUser) -> dict:
    # TODO: Fetch real-time stats from Redis / LangSmith (Phase 2)
    return {
        "status": "operational",
        "agents": {name: {"status": "idle", "last_run": None} for name in VALID_AGENT_NAMES},
    }
