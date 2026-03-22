import asyncio
import sys
sys.path.append("/home/eldra/Virtual-Personal-Finance-Advisor/finance_advisor_backend")
from app.core.database import AsyncSessionLocal
from app.models.user import User
from app.models.asset import Asset
from app.services.instrument_resolver import all_instruments
from sqlalchemy import select

async def seed_db():
    print("Seeding database...")
    async with AsyncSessionLocal() as session:
        async with session.begin():
            # Check if user exists
            result = await session.execute(select(User).filter_by(username="bogdanmd3"))
            user = result.scalar_one_or_none()
            if not user:
                user = User(
                    id=1,
                    username="bogdanmd3",
                    email="test@example.com",
                    hashed_password="hashed_password_placeholder",
                    etoro_key="default_mock_key_if_needed",
                    is_active=True
                )
                session.add(user)
                print("User bogdanmd3 (ID=1) created.")
            
            # Asset
            instruments = all_instruments()
            for inst in instruments:
                result = await session.execute(select(Asset).filter_by(instrument_id=inst["instrument_id"]))
                asset = result.scalar_one_or_none()
                if not asset:
                    asset = Asset(
                        instrument_id=inst["instrument_id"],
                        symbol=inst["symbol"],
                        name=inst["name"],
                        asset_class=inst["asset_class"]
                    )
                    session.add(asset)
            print(f"Seeded {len(instruments)} assets if they didn't exist.")

    print("Seeding complete!")

if __name__ == "__main__":
    asyncio.run(seed_db())
