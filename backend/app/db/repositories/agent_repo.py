"""Agent config and Evaluation repositories."""

from __future__ import annotations

import uuid

from sqlalchemy import select

from app.db.repositories.base import BaseRepository
from app.models.agent_config import AgentConfig
from app.models.evaluation import Evaluation


class AgentConfigRepository(BaseRepository[AgentConfig]):
    model = AgentConfig

    async def list_by_tenant(self, tenant_id: uuid.UUID) -> list[AgentConfig]:
        stmt = select(AgentConfig).where(AgentConfig.tenant_id == tenant_id)
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def get_by_name(self, agent_name: str, tenant_id: uuid.UUID) -> AgentConfig | None:
        stmt = select(AgentConfig).where(
            AgentConfig.agent_name == agent_name,
            AgentConfig.tenant_id == tenant_id,
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()


class EvaluationRepository(BaseRepository[Evaluation]):
    model = Evaluation

    async def list_by_tenant(
        self, tenant_id: uuid.UUID, limit: int = 20, offset: int = 0
    ) -> list[Evaluation]:
        stmt = (
            select(Evaluation)
            .where(Evaluation.tenant_id == tenant_id)
            .order_by(Evaluation.evaluated_at.desc())
            .limit(limit)
            .offset(offset)
        )
        result = await self.db.execute(stmt)
        return list(result.scalars().all())
