import asyncio
from sqlalchemy import select
from app.db.session import async_session_maker
from app.models.ticket import Ticket

async def main():
    async with async_session_maker() as session:
        stmt = select(Ticket).order_by(Ticket.created_at.desc()).limit(1)
        result = await session.execute(stmt)
        ticket = result.scalar_one_or_none()
        if ticket:
            print(f"Status: {ticket.status}")
            print(f"Metadata: {ticket.metadata_}")
            
if __name__ == "__main__":
    asyncio.run(main())
