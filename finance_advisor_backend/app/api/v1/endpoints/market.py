from fastapi import APIRouter, HTTPException
from app.services.market_data import MarketDataService

router = APIRouter()
market_service = MarketDataService()

@router.get("/quote/{symbol}")
async def get_quote(symbol: str):
    data = await market_service.get_stock_quote(symbol)
    if "error" in data:
        raise HTTPException(status_code=400, detail=data["error"])
    return data