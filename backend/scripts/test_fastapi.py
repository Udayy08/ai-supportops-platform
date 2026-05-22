"""Test all Phase 7 FastAPI endpoints using TestClient."""

import asyncio
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from fastapi.testclient import TestClient
from app.main import app
from app.api.deps import get_current_user
from app.models.user import User, UserRole
import uuid

from sqlalchemy.future import select
from app.db.session import get_session_factory
from app.models.tenant import Tenant

async def mock_get_current_user():
    SessionLocal = get_session_factory()
    async with SessionLocal() as session:
        result = await session.execute(select(User).limit(1))
        user = result.scalar_one_or_none()
        if user:
            return user
        
        # Create a fallback user if DB is empty
        result = await session.execute(select(Tenant).limit(1))
        tenant = result.scalar_one_or_none()
        if not tenant:
            tenant = Tenant(id=uuid.uuid4(), name="Test Tenant", slug="test-tenant", settings={})
            session.add(tenant)
            await session.flush()
            
        user = User(
            id=uuid.uuid4(),
            tenant_id=tenant.id,
            email="test@example.com",
            full_name="Test User",
            role=UserRole.ADMIN,
            is_active=True,
            hashed_password="mock"
        )
        session.add(user)
        await session.commit()
        return user

app.dependency_overrides[get_current_user] = mock_get_current_user

def run_tests():
    with TestClient(app) as client:
        print("========================================")
        print("Testing Phase 7 FastAPI Endpoints")
        print("========================================")

        # 1. POST /tickets
        print("\n1. POST /api/v1/tickets")
        res = client.post("/api/v1/tickets", json={
            "subject": "Missing Refund",
            "description": "I did not get my refund for order 123",
            "priority": "high"
        })
        print(f"Status: {res.status_code}")
        print(res.json())
        ticket_id = res.json().get("id")

        # 2. POST /tickets/process
        print("\n2. POST /api/v1/tickets/process")
        res = client.post("/api/v1/tickets/process", json={
            "ticket_id": ticket_id,
            "additional_context": "Customer is very angry"
        })
        print(f"Status: {res.status_code}")
        print(res.json())

        # 3. GET /tickets
        print("\n3. GET /api/v1/tickets (History)")
        res = client.get("/api/v1/tickets?page_size=5")
        print(f"Status: {res.status_code}")
        print(res.json())

        # 4. GET /tickets/{id}
        print(f"\n4. GET /api/v1/tickets/{ticket_id}")
        res = client.get(f"/api/v1/tickets/{ticket_id}")
        print(f"Status: {res.status_code}")
        print(res.json())

        # 5. POST /tickets/{id}/human-review
        print(f"\n5. POST /api/v1/tickets/{ticket_id}/human-review")
        res = client.post(f"/api/v1/tickets/{ticket_id}/human-review", json={
            "ticket_id": ticket_id,
            "approval_decision": "APPROVED"
        })
        print(f"Status: {res.status_code}")
        print(res.json())

        # 6. GET /analytics/summary
        print("\n6. GET /api/v1/analytics/summary")
        res = client.get("/api/v1/analytics/summary")
        print(f"Status: {res.status_code}")
        print(res.json())

        # 7. GET /evaluations/metrics
        print("\n7. GET /api/v1/evaluations/metrics")
        res = client.get("/api/v1/evaluations/metrics")
        print(f"Status: {res.status_code}")
        print(res.json())

        # 8. GET /workflow/traces
        print("\n8. GET /api/v1/workflow/traces")
        res = client.get("/api/v1/workflow/traces")
        print(f"Status: {res.status_code}")
        print(res.json())

if __name__ == "__main__":
    run_tests()
