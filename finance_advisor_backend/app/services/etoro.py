# app/services/etoro.py
"""
eToro API service with:
 - Circuit Breaker protection
 - LRU + TTL caching (5-min portfolio cache)
 - Mock data fallback when USE_MOCK_DATA=true or circuit is OPEN
 - Instrument ID resolution → human-readable names
"""
import os
import uuid
import logging
import httpx
from app.core.config import get_settings
from app.core.circuit_breaker import get_circuit_breaker, CircuitBreakerOpen
from app.services import cache_service, mock_data, instrument_resolver

logger = logging.getLogger(__name__)
settings = get_settings()
USE_MOCK = os.getenv("USE_MOCK_DATA", "false").lower() == "true"

PORTFOLIO_CACHE_KEY = "etoro:portfolio"
PORTFOLIO_TTL = 300  # 5 minutes


class EtoroService:
    def __init__(self):
        self.base_url = settings.etoro_base_url
        self.headers = {
            "x-api-key": settings.etoro_api_key,
            "x-user-key": settings.etoro_user_key,
            "Content-Type": "application/json",
        }
        self._cb = get_circuit_breaker("etoro")

    def _enrich_positions(self, positions: list) -> list:
        """Translate instrumentId → readable fields via instrument_resolver."""
        enriched = []
        for pos in positions:
            iid = pos.get("instrumentId") or pos.get("instrument_id")
            if iid:
                info = instrument_resolver.resolve(int(iid))
                pos = {**pos, **info}
            enriched.append(pos)
        return enriched

    async def _fetch_from_api(self) -> dict:
        request_headers = {
            **self.headers,
            "x-request-id": str(uuid.uuid4()),
        }
        url = f"{self.base_url}/user-info/people/{settings.etoro_username}/portfolio/live"
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.get(url, headers=request_headers)
            response.raise_for_status()
            return response.json()

    async def get_live_portfolio(self) -> dict:
        # 1. Return mock data immediately in dev mode
        if USE_MOCK:
            logger.info("[eToro] Mock mode active — returning static portfolio")
            data = mock_data.MOCK_ETORO_PORTFOLIO.copy()
            data["positions"] = self._enrich_positions(data["positions"])
            return data

        # 2. Check in-memory cache
        cached = cache_service.cache_get(PORTFOLIO_CACHE_KEY)
        if cached is not None:
            logger.info("[eToro] Cache HIT for portfolio")
            return cached

        # 3. Try live API call through circuit breaker
        try:
            data = await self._cb.call(self._fetch_from_api)
            if "positions" in data:
                data["positions"] = self._enrich_positions(data.get("positions", []))
            cache_service.cache_set(PORTFOLIO_CACHE_KEY, data, PORTFOLIO_TTL)
            return data
        except CircuitBreakerOpen as e:
            logger.warning(f"[eToro] {e} — falling back to mock data")
            data = mock_data.MOCK_ETORO_PORTFOLIO.copy()
            data["positions"] = self._enrich_positions(data["positions"])
            data["_fallback"] = "circuit_breaker_open"
            return data
        except Exception as e:
            logger.error(f"[eToro] API error: {e}")
            return {"error": str(e), "detail": "eToro API unavailable"}

    async def get_instruments(self) -> list:
        """Returns the full static instrument list (no API call needed)."""
        return instrument_resolver.all_instruments()