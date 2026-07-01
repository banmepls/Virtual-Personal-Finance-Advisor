"""
tests/conftest.py
=================
Shared fixtures for the functional test suite.

A *minimal* FastAPI app is assembled from the light-weight routers only
(market, etoro, anomaly, health) so the suite never imports the LangChain /
Gemini agent stack and never needs a running PostgreSQL instance.  The
database dependency `get_db` is overridden by an in-memory stub, and
`USE_MOCK_DATA=true` (the project default) keeps eToro / Yahoo Finance offline.
"""
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

# The DB / Postgres settings are normally injected by docker-compose; provide
# inert placeholders so `Settings()` validates. The async engine is created
# lazily and never actually connects during the functional suite (get_db is
# overridden and USE_MOCK_DATA keeps external calls offline).
os.environ.setdefault("DATABASE_URL", "postgresql+asyncpg://test:test@localhost:5432/testdb")
os.environ.setdefault("POSTGRES_USER", "test")
os.environ.setdefault("POSTGRES_PASSWORD", "test")
os.environ.setdefault("POSTGRES_DB", "testdb")
os.environ.setdefault("USE_MOCK_DATA", "true")

import pytest
import pytest_asyncio
from fastapi import FastAPI
from httpx import AsyncClient, ASGITransport

from app.core.database import get_db
from app.api.v1.endpoints import anomaly, health, etoro, market


class _FakeResult:
    def scalar(self):
        return 1

    def scalars(self):
        class _S:
            def all(self_inner):
                return []
        return _S()


class _FakeSession:
    """Stub AsyncSession — endpoints under test never persist real rows."""
    async def execute(self, *a, **k):
        return _FakeResult()

    def add(self, *a, **k):
        pass

    async def commit(self):
        pass

    async def close(self):
        pass


async def _fake_get_db():
    yield _FakeSession()


@pytest.fixture
def test_app() -> FastAPI:
    application = FastAPI()
    application.include_router(market.router, prefix="/api/v1/market")
    application.include_router(etoro.router, prefix="/api/v1/etoro")
    application.include_router(anomaly.router, prefix="/api/v1/anomaly")
    application.include_router(health.router, prefix="/api/v1")
    application.dependency_overrides[get_db] = _fake_get_db
    return application


@pytest_asyncio.fixture
async def client(test_app):
    transport = ASGITransport(app=test_app)
    async with AsyncClient(transport=transport, base_url="http://test") as c:
        yield c
