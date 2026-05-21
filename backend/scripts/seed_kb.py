import asyncio
import uuid
import sys
import os

# Add the backend directory to sys.path so we can import 'app'
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.db.session import init_db, close_db, get_session_factory
from app.models.tenant import Tenant
from app.rag.knowledge_manager import KnowledgeManager


POLICIES = [
    {
        "title": "Refund Policy",
        "category": "Refunds",
        "content": (
            "We offer a 30-day money-back guarantee for all unused products in their original packaging. "
            "To initiate a refund, customers must contact support within 30 days of delivery. "
            "Refunds are processed within 5-7 business days to the original payment method. "
            "Shipping costs are non-refundable unless the return is due to a defective product."
        ),
    },
    {
        "title": "Shipping Policy",
        "category": "Shipping",
        "content": (
            "Orders are processed within 1-2 business days. Standard shipping takes 3-5 business days. "
            "Expedited shipping is available for an additional fee and guarantees delivery within 1-2 business days. "
            "We currently ship internationally to select countries. International shipping times vary from 7-14 days. "
            "Customers will receive a tracking number via email once the order has shipped."
        ),
    },
    {
        "title": "Cancellation Policy",
        "category": "Cancellations",
        "content": (
            "Orders can only be cancelled within 1 hour of placement. Once an order has entered the "
            "fulfillment stage, it cannot be cancelled, but the customer may return the item after delivery "
            "following our standard Refund Policy. Digital product subscriptions can be cancelled at any time "
            "from the account settings page."
        ),
    },
    {
        "title": "Subscription Rules",
        "category": "Subscriptions",
        "content": (
            "Monthly and annual subscriptions renew automatically unless cancelled prior to the renewal date. "
            "If a payment fails, we will retry the charge 3 times over a 7-day grace period. "
            "During the grace period, access to premium features will remain active. "
            "If payment is not resolved, the account will be downgraded to the free tier."
        ),
    },
    {
        "title": "Frequently Asked Questions",
        "category": "FAQ",
        "content": (
            "Q: Can I change my shipping address after placing an order? "
            "A: You can update your shipping address within 1 hour of placing the order by contacting support. "
            "Q: Do you offer bulk discounts? "
            "A: Yes, for orders over 50 items, please contact our enterprise sales team for a custom quote. "
            "Q: How do I reset my password? "
            "A: Click on 'Forgot Password' on the login screen and follow the instructions sent to your email."
        ),
    },
]


async def seed_knowledge_base():
    await init_db()
    session_factory = get_session_factory()

    async with session_factory() as session:
        try:
            # Check for existing tenant or create one
            result = await session.execute(select(Tenant).where(Tenant.slug == "demo-tenant"))
            tenant = result.scalars().first()
            if not tenant:
                tenant = Tenant(
                    id=uuid.uuid4(),
                    name="Demo Corp",
                    slug="demo-tenant",
                    settings={},
                )
                session.add(tenant)
                await session.flush()
                print(f"Created Tenant: {tenant.name} ({tenant.id})")
            else:
                print(f"Using existing Tenant: {tenant.name} ({tenant.id})")

            # Initialize KnowledgeManager
            km = KnowledgeManager(session=session)

            print("Seeding Knowledge Base...")
            for policy in POLICIES:
                print(f"  Ingesting: {policy['title']}")
                article = await km.ingest_article(
                    tenant_id=tenant.id,
                    title=policy["title"],
                    content=policy["content"],
                    category=policy["category"],
                    chunk_size=500,
                    chunk_overlap=100,
                )
                print(f"    -> Article ID: {article.id}")

            print("Knowledge Base Seeding Complete!")
            await session.commit()
            
            # Save tenant ID to a file for test_retrieval.py to use easily
            with open("demo_tenant_id.txt", "w") as f:
                f.write(str(tenant.id))
                
        except Exception as e:
            await session.rollback()
            print(f"Error seeding database: {e}")
            raise
        finally:
            await close_db()

if __name__ == "__main__":
    asyncio.run(seed_knowledge_base())
