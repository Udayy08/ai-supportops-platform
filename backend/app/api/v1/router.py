"""
v1 API Router — aggregates all sub-routers under /api/v1.
"""

from fastapi import APIRouter

from app.api.v1 import (
    agents,
    analytics,
    auth,
    conversations,
    evaluations,
    knowledge,
    tickets,
    webhooks,
    workflow,
)

api_router = APIRouter()

api_router.include_router(auth.router)
api_router.include_router(tickets.router)
api_router.include_router(conversations.router)
api_router.include_router(knowledge.router)
api_router.include_router(analytics.router)
api_router.include_router(agents.router)
api_router.include_router(evaluations.router)
api_router.include_router(webhooks.router)
api_router.include_router(workflow.router)
