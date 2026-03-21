"""
app/api/v1/endpoints/anomaly.py
--------------------------------
Anomaly detection endpoints: analyze portfolio and fetch history.
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.core.database import get_db
from app.ml.anomaly_service import analyze_portfolio
from app.models.anomaly_log import AnomalyLog
from app.schemas.schemas import AnomalyAnalyzeRequest, AnomalyResult, AnomalyHistoryItem

router = APIRouter()


@router.post("/analyze", response_model=AnomalyResult)
async def analyze(request: AnomalyAnalyzeRequest, db: AsyncSession = Depends(get_db)):
    """
    Analyze a portfolio snapshot using the 3-model voting ensemble.
    Persists the result as an AnomalyLog (linked to user_id if provided).
    """
    positions = [pos.model_dump() for pos in request.positions]

    try:
        result = analyze_portfolio(positions)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"ML analysis error: {str(e)}")

    # Persist to DB if user_id provided
    if request.user_id:
        log = AnomalyLog(
            user_id=request.user_id,
            isolation_score=result.isolation_score,
            autoencoder_mse=result.autoencoder_mse,
            svm_score=result.svm_score,
            weighted_avg_score=result.weighted_avg_score,
            is_anomaly=result.is_anomaly,
            notes=result.notes,
        )
        db.add(log)
        await db.commit()

    return AnomalyResult(
        isolation_score=result.isolation_score,
        autoencoder_mse=result.autoencoder_mse,
        svm_score=result.svm_score,
        weighted_avg_score=result.weighted_avg_score,
        is_anomaly=result.is_anomaly,
        confidence=result.confidence,
        notes=result.notes,
    )


@router.get("/history/{user_id}", response_model=list[AnomalyHistoryItem])
async def get_history(user_id: int, limit: int = 20, db: AsyncSession = Depends(get_db)):
    """Retrieve the last N anomaly analysis results for a user."""
    result = await db.execute(
        select(AnomalyLog)
        .where(AnomalyLog.user_id == user_id)
        .order_by(AnomalyLog.created_at.desc())
        .limit(limit)
    )
    logs = result.scalars().all()
    return logs
