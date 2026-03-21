"""
app/services/market_data.py
----------------------------
Alpha Vantage market data service with:
 - Circuit Breaker protection
 - LRU + TTL caching (60-min quote cache)
 - Hard 25 req/day quota enforcement
 - Mock fallback when USE_MOCK_DATA=true or quota exceeded
"""
import os
import logging
import httpx
from app.core.config import get_settings
from app.core.circuit_breaker import get_circuit_breaker, CircuitBreakerOpen
from app.services import cache_service, mock_data

logger = logging.getLogger(__name__)
settings = get_settings()
USE_MOCK = os.getenv("USE_MOCK_DATA", "false").lower() == "true"

QUOTE_TTL = 3600   # 60 minutes — quotes rarely need to be fresher during dev
SENTIMENT_TTL = 1800  # 30 minutes


class MarketDataService:
    BASE_URL = "https://www.alphavantage.co/query"

    def __init__(self):
        self._cb = get_circuit_breaker("alpha_vantage")

    async def _fetch_quote_from_api(self, symbol: str) -> dict:
        params = {
            "function": "GLOBAL_QUOTE",
            "symbol": symbol,
            "apikey": settings.alpha_vantage_api_key,
        }
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.get(self.BASE_URL, params=params)
            response.raise_for_status()
            data = response.json()
        quote = data.get("Global Quote", {})
        if not quote:
            raise ValueError("Simbolul nu a fost găsit sau limita API a fost atinsă.")
        cache_service.av_increment_counter()
        return {
            "symbol": quote.get("01. symbol"),
            "price": float(quote.get("05. price", 0)),
            "change_percent": quote.get("10. change percent"),
            "volume": quote.get("06. volume"),
            "source": "live",
        }

    async def get_stock_quote(self, symbol: str) -> dict:
        cache_key = f"quote:{symbol.upper()}"

        # 1. Mock mode
        if USE_MOCK:
            logger.info(f"[AlphaVantage] Mock mode — returning mock quote for {symbol}")
            return mock_data.mock_stock_quote(symbol)

        # 2. Cache hit
        cached = cache_service.cache_get(cache_key)
        if cached is not None:
            logger.info(f"[AlphaVantage] Cache HIT for {symbol}")
            return cached

        # 3. Quota guard
        if cache_service.av_quota_exceeded():
            logger.warning(f"[AlphaVantage] Daily quota exceeded — using mock for {symbol}")
            result = mock_data.mock_stock_quote(symbol)
            result["_fallback"] = "quota_exceeded"
            return result

        # 4. Live API call via circuit breaker
        try:
            result = await self._cb.call(lambda: self._fetch_quote_from_api(symbol))
            cache_service.cache_set(cache_key, result, QUOTE_TTL)
            return result
        except CircuitBreakerOpen as e:
            logger.warning(f"[AlphaVantage] {e} — using mock for {symbol}")
            result = mock_data.mock_stock_quote(symbol)
            result["_fallback"] = "circuit_breaker_open"
            return result
        except ValueError as e:
            return {"error": str(e)}
        except Exception as e:
            logger.error(f"[AlphaVantage] API error for {symbol}: {e}")
            return {"error": str(e)}

    def quota_status(self) -> dict:
        return {
            "daily_limit": cache_service.ALPHA_VANTAGE_DAILY_LIMIT,
            "remaining": cache_service.av_quota_remaining(),
            "exceeded": cache_service.av_quota_exceeded(),
        }
