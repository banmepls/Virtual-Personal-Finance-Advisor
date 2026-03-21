"""
app/api/v1/endpoints/health.py
-------------------------------
Health check endpoint exposing:
 - Circuit breaker states per service
 - In-memory cache statistics
 - Alpha Vantage daily quota remaining
 - DB connectivity ping
"""
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from datetime import datetime, timezone
from app.core.database import get_db
from app.core.circuit_breaker import all_circuit_breaker_statuses
from app.services.cache_service import cache_stats, av_quota_remaining, av_quota_exceeded, ALPHA_VANTAGE_DAILY_LIMIT
from app.schemas.schemas import HealthResponse

router = APIRouter()


@router.get("/health", response_model=HealthResponse)
async def health_check(db: AsyncSession = Depends(get_db)):
    """Full system health status for monitoring and debugging."""
    # DB ping
    db_ok = False
    try:
        await db.execute(text("SELECT 1"))
        db_ok = True
    except Exception:
        db_ok = False

    circuit_breakers = all_circuit_breaker_statuses()
    c_stats = cache_stats()
    c_stats["db_connected"] = db_ok

    return HealthResponse(
        status="healthy" if db_ok else "degraded",
        circuit_breakers=circuit_breakers,
        cache_stats=c_stats,
        alpha_vantage_quota={
            "daily_limit": ALPHA_VANTAGE_DAILY_LIMIT,
            "remaining": av_quota_remaining(),
            "exceeded": av_quota_exceeded(),
        },
        timestamp=datetime.now(timezone.utc),
    )
