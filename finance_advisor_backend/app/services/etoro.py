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
        cache_key = f"etoro:portfolio:{settings.etoro_username}"
        cached = cache_service.cache_get(cache_key)
        if cached is not None:
            logger.info("[eToro] Cache HIT for portfolio")
            return cached

        # 3. Try live API call through circuit breaker
        try:
            data = await self._cb.call(self._fetch_from_api)
            if "positions" in data:
                # Base assumptions for the private-facing public API
                INITIAL_TOTAL = 10000.0  # We model a $10,000 baseline
                CASH_INITIAL = INITIAL_TOTAL * (data.get("realizedCreditPct", 73.9) / 100.0)
                
                aggregated = {}
                for pos in data["positions"]:
                    iid = pos.get("instrumentId")
                    if iid not in aggregated:
                        pct = pos.get("investmentPct", 0.0)
                        np = pos.get("netProfit", 0.0)
                        
                        # Mathematical Projection:
                        # 1. How much was initially invested in this asset relative to the $10k base
                        invested = (pct / 100.0) * INITIAL_TOTAL
                        # 2. Apply the PnL (netProfit) to find the CURRENT value in dollars
                        current_val = invested * (1 + (np / 100.0))
                        
                        open_rate = pos.get("openRate", 1.0) or 1.0
                        pos["avgBuyPrice"] = open_rate
                        pos["currentPrice"] = open_rate * (1 + (np / 100.0))
                        pos["currentValue"] = current_val
                        pos["quantity"] = invested / open_rate
                        pos["unrealizedPnL"] = current_val - invested
                        pos["unrealizedPnLPercent"] = np
                        
                        # Staging for aggregation
                        pos["_baseInvested"] = invested
                        pos["_baseCurrent"] = current_val
                        pos["_baseNP"] = np
                        aggregated[iid] = pos
                    else:
                        exist = aggregated[iid]
                        pct = pos.get("investmentPct", 0.0)
                        np = pos.get("netProfit", 0.0)
                        
                        # Aggregate the splits
                        invested = (pct / 100.0) * INITIAL_TOTAL
                        current_val = invested * (1 + (np / 100.0))
                        
                        exist["_baseInvested"] += invested
                        exist["_baseCurrent"] += current_val
                        
                        # Weighted PnL %
                        if exist["_baseInvested"] > 0:
                            exist["unrealizedPnLPercent"] = ((exist["_baseCurrent"] - exist["_baseInvested"]) / exist["_baseInvested"]) * 100.0
                        
                        exist["currentValue"] = exist["_baseCurrent"]
                        exist["unrealizedPnL"] = exist["_baseCurrent"] - exist["_baseInvested"]
                        
                        # Recalculate metrics for merged position
                        # We use openRate of the first split for display consistency or weighted avg if different
                        open_rate = exist.get("openRate", 1.0) or 1.0
                        exist["avgBuyPrice"] = open_rate
                        exist["quantity"] = exist["_baseInvested"] / open_rate
                        exist["currentPrice"] = exist["currentValue"] / exist["quantity"] if exist["quantity"] > 0 else 0.0
                        
                # ── Final Portfolio Totals ──
                final_positions = list(aggregated.values())
                current_assets_total = sum(p["currentValue"] for p in final_positions)
                
                # The remaining cash doesn't fluctuate with asset PnL 
                # (but in real life eToro displays weights relative to CURRENT Total)
                new_total_value = current_assets_total + CASH_INITIAL
                
                # Clean up staging fields and enrich IDs
                for pos in final_positions:
                    pos.pop("_baseInvested", None)
                    pos.pop("_baseCurrent", None)
                    pos.pop("_baseNP", None)
                    
                data["positions"] = self._enrich_positions(final_positions)
                data["totalPortfolioValue"] = new_total_value
                data["totalPnL"] = current_assets_total - (INITIAL_TOTAL - CASH_INITIAL)
                data["totalPnLPercent"] = (data["totalPnL"] / INITIAL_TOTAL) * 100.0
                
            cache_service.cache_set(cache_key, data, PORTFOLIO_TTL)
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