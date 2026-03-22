from fastapi import APIRouter, HTTPException
from app.services.market_data import MarketDataService
from app.services import cache_service

router = APIRouter()
market_service = MarketDataService()

@router.get("/flush")
async def flush_cache():
    cache_service.cache_clear()
    return {"status": "Cache flushed"}

@router.get("/quote/{symbol}")
async def get_quote(symbol: str):
    try:
        data = await market_service.get_stock_quote(symbol)
        if "error" in data:
            raise HTTPException(status_code=400, detail=data["error"])
        return data
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Market data error: {str(e)}")

@router.get("/history/{symbol}")
async def get_history(symbol: str):
    try:
        data = await market_service.get_stock_history(symbol)
        return data
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Market history error: {str(e)}")