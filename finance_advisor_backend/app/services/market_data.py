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
from app.services import cache_service, mock_data, instrument_resolver

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
        """
        Public entry point for quotes.
        Handles eToro IDs (e.g. 'ID_1253' or '1253') by resolving them to symbols.
        """
        clean_symbol = symbol.upper()
        if clean_symbol.startswith("ID_") or clean_symbol.isdigit():
            iid = int(clean_symbol.replace("ID_", ""))
            resolved = instrument_resolver.resolve(iid)
            if resolved["symbol"] != f"ID_{iid}":
                clean_symbol = resolved["symbol"]
            else:
                raise ValueError(f"Instrument ID {iid} could not be resolved to a symbol.")

        cache_key = f"quote:{clean_symbol}"

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
            result = await self._cb.call(lambda: self._fetch_quote_from_api(clean_symbol))
            cache_service.cache_set(cache_key, result, QUOTE_TTL)
            return result
        except ValueError as e:
            # Don't count user errors (unknown symbol/ID) toward circuit breaker failure
            logger.warning(f"[MarketDataService] Validation error: {str(e)}")
            raise
        except CircuitBreakerOpen:
            logger.warning(f"[CB:alpha_vantage] Circuit OPEN — falling back to mock for {clean_symbol}")
            return mock_data.mock_stock_quote(clean_symbol)
        except Exception as e:
            self._cb.report_failure()
            logger.error(f"[MarketDataService] Error fetching {clean_symbol}: {str(e)}")
            return mock_data.mock_stock_quote(clean_symbol)

    async def _fetch_history_from_api(self, symbol: str) -> list:
        params = {
            "function": "TIME_SERIES_DAILY",
            "symbol": symbol,
            "apikey": settings.alpha_vantage_api_key,
        }
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(self.BASE_URL, params=params)
            response.raise_for_status()
            data = response.json()
        
        ts = data.get("Time Series (Daily)", {})
        if not ts:
            # If we get a note about API rate limit, the quota guard should have caught it, 
            # but sometimes AV returns it in the JSON body.
            if "Note" in data:
                raise ValueError("Alpha Vantage rate limit reached.")
            raise ValueError(f"No history found for {symbol}")

        cache_service.av_increment_counter()
        
        # Sort by date and take last 30 days
        sorted_dates = sorted(ts.keys(), reverse=True)[:30]
        history = []
        for d in reversed(sorted_dates):
            history.append({
                "date": d,
                "price": float(ts[d]["4. close"])
            })
        return history

    async def get_stock_history(self, symbol: str, days: int = 30) -> list:
        """
        Returns history for a symbol (resolves ID if needed).
        """
        clean_symbol = symbol.upper()
        if clean_symbol.startswith("ID_") or clean_symbol.isdigit():
            iid = int(clean_symbol.replace("ID_", ""))
            resolved = instrument_resolver.resolve(iid)
            clean_symbol = resolved["symbol"]

        cache_key = f"history:{clean_symbol}"

        # 1. Mock mode
        if USE_MOCK:
            return mock_data.mock_stock_history(clean_symbol, days)

        # 2. Cache hit (History is cached for 24h as it's daily data)
        cached = cache_service.cache_get(cache_key)
        if cached is not None:
            return cached

        # 3. Quota guard
        if cache_service.av_quota_exceeded():
            logger.warning(f"[AlphaVantage] Quota exceeded for history {clean_symbol}")
            return mock_data.mock_stock_history(clean_symbol, days)

        # 4. Live API call
        try:
            result = await self._cb.call(lambda: self._fetch_history_from_api(clean_symbol))
            cache_service.cache_set(cache_key, result, 86400) # 24 hours
            return result
        except Exception as e:
            logger.error(f"[MarketDataService] Error history {clean_symbol}: {str(e)}")
            return mock_data.mock_stock_history(clean_symbol, days)

    def quota_status(self) -> dict:
        return {
            "daily_limit": cache_service.ALPHA_VANTAGE_DAILY_LIMIT,
            "remaining": cache_service.av_quota_remaining(),
            "exceeded": cache_service.av_quota_exceeded(),
        }
