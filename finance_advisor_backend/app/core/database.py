from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase
from.config import get_settings

settings = get_settings()

# Create async engine for postgresql+asyncpg
engine = create_async_engine(
    settings.database_url,
    echo=True, # Set False in Production
    future=True
)

# Factory for async sessions
AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False
)

# Base model class
class Base(DeclarativeBase):
    pass

# FastAPI Dependency for session injection in endpoints
async def get_db():
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()
