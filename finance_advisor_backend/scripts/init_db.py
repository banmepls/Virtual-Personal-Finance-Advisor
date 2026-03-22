import asyncio
import sys
sys.path.append("/home/eldra/Virtual-Personal-Finance-Advisor/finance_advisor_backend")

from app.core.database import engine, Base
import app.models

async def init_db():
    print("Connecting to database...")
    async with engine.begin() as conn:
        print("Creating tables...")
        await conn.run_sync(Base.metadata.create_all)
    print("Database initialization complete!")

if __name__ == "__main__":
    asyncio.run(init_db())
