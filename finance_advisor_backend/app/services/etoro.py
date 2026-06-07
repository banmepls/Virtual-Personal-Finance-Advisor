# app/services/etoro.py
"""
eToro API service with:
 - Circuit Breaker protection
 - LRU + TTL caching (5-min portfolio cache)
 - Mock data fallback when USE_MOCK_DATA=true or circuit is OPEN
 - Instrument ID resolution → human-readable names
"""
import json
import base64
import uuid
import logging
from typing import Optional
import httpx
from app.core.config import get_settings
from app.core.circuit_breaker import get_circuit_breaker, CircuitBreakerOpen
from app.services import cache_service, mock_data, instrument_resolver

logger = logging.getLogger(__name__)
settings = get_settings()

PORTFOLIO_CACHE_KEY = "etoro:portfolio"
PORTFOLIO_TTL = 300  # 5 minutes

# Values that mean "not configured" — README/.env placeholders + obvious defaults.
_PLACEHOLDER_VALUES = {
    "", None,
    "your_etoro_api_key", "your_etoro_user_key", "your_username", "demo_user",
}


def _decode_etoro_user_key(user_key: str) -> dict:
    """Decode the eToro user key (base64url-encoded JSON) to inspect its claims.

    The user key carries an `ean` (eToro Application Name) field. A registered
    application has a real name here; an unregistered one reads
    "UnregisteredApplication". Returns {} if it cannot be parsed.
    """
    try:
        k = user_key.rstrip("_")
        k += "=" * (-len(k) % 4)
        return json.loads(base64.urlsafe_b64decode(k))
    except Exception:
        return {}


def etoro_credential_problem() -> Optional[str]:
    """Return a human-readable reason the eToro credentials cannot work, or None.

    This is a preflight check so we surface an actionable message instead of a
    raw 404 from eToro. When a real *registered* key is dropped into .env this
    returns None and the live API call proceeds unchanged.
    """
    if settings.etoro_api_key in _PLACEHOLDER_VALUES:
        return "ETORO_API_KEY is not set (placeholder value in .env)."
    if settings.etoro_user_key in _PLACEHOLDER_VALUES:
        return "ETORO_USER_KEY is not set (placeholder value in .env)."
    if settings.etoro_username in _PLACEHOLDER_VALUES:
        return "ETORO_USERNAME is not set (placeholder value in .env)."

    # NOTE: an "UnregisteredApplication" user key is NOT a blocker for PUBLIC
    # (social-trading) portfolio reads — only for private own-account endpoints.
    # Since we fetch a public user's portfolio, we do not reject it here.
    return None


class EtoroService:
    def __init__(self):
        self.base_url = settings.etoro_base_url
        self.headers = {
            "x-api-key": settings.etoro_api_key,
            "x-user-key": settings.etoro_user_key,
            "Content-Type": "application/json",
        }
        self._cb = get_circuit_breaker("etoro")

    async def _fetch_instruments_metadata(self, instrument_ids: list[int]) -> list:
        if not instrument_ids:
            return []
        ids_str = ",".join(map(str, instrument_ids))
        request_headers = {
            **self.headers,
            "x-request-id": str(uuid.uuid4()),
        }
        url = f"{self.base_url}/api/v1/market-data/instruments?instrumentIds={ids_str}"
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(url, headers=request_headers)
                response.raise_for_status()
                data = response.json()
                return data.get("instrumentDisplayDatas", [])
        except Exception as e:
            logger.error(f"[EtoroService] Error fetching metadata for {ids_str}: {e}")
            return []

    async def _enrich_positions(self, positions: list) -> list:
        """Translate instrumentId → readable fields. Fetches unknown IDs from eToro API."""
        unknown_ids = []
        for pos in positions:
            iid = pos.get("instrumentId") or pos.get("instrument_id")
            if iid:
                iid = int(iid)
                # Fetch metadata for any ID we don't have a REAL mapping for yet.
                # Using is_mapped (not is_seen) means a previously-unresolved ID is
                # retried on the next portfolio fetch → unknown instruments auto-heal.
                if not instrument_resolver.is_mapped(iid):
                    unknown_ids.append(iid)

        if unknown_ids:
            logger.info(f"[EtoroService] Attempting to resolve {len(unknown_ids)} unknown instruments: {unknown_ids}")
            items = await self._fetch_instruments_metadata(list(set(unknown_ids)))
            for item in items:
                iid = item.get("instrumentID")
                name = item.get("instrumentDisplayName")
                symbol = item.get("symbolFull")
                # eToro instrument type IDs (from /api/v1/market-data/instrument-types)
                type_id = item.get("instrumentTypeID")
                type_map = {
                    1: "Forex", 2: "Commodities", 3: "CFD", 4: "Indices",
                    5: "Stocks", 6: "ETF", 7: "Bonds", 8: "TrustFunds",
                    9: "Options", 10: "Crypto",
                }
                asset_class = type_map.get(type_id, "Other")
                
                if iid and symbol:
                    instrument_resolver.register(int(iid), symbol, name or symbol, asset_class)
        
        # Re-resolve now that we've populated the cache
        enriched = []
        for pos in positions:
            iid = pos.get("instrumentId") or pos.get("instrument_id")
            if iid:
                info = instrument_resolver.resolve(int(iid))
                pos = {**pos, **info}
            enriched.append(pos)
        return enriched

    def _parse_portfolio(self, data: dict) -> dict:
        """Map eToro's PUBLIC user-portfolio response to our portfolio shape.

        Response (from /api/v1/user-info/people/{username}/portfolio/live):
          { "realizedCreditPct": <cash %>, "unrealizedCreditPct": <%>,
            "positions": [ {instrumentId, openRate, investmentPct, netProfit, isBuy, ...} ],
            "socialTrades": [...] }

        The public API exposes only ALLOCATION percentages, not absolute amounts —
        you cannot see another user's real balance. We model the portfolio against
        a $10,000 baseline: each position's investmentPct is applied to $10k, then
        netProfit% yields its current value. Cash = realizedCreditPct of the baseline.
        Multiple splits of the same instrument are aggregated.
        """
        INITIAL_TOTAL = 10000.0
        raw_positions = data.get("positions", []) or []
        cash = (float(data.get("realizedCreditPct", 0.0) or 0.0) / 100.0) * INITIAL_TOTAL

        aggregated: dict = {}
        for p in raw_positions:
            iid = p.get("instrumentId")
            if iid is None:
                continue
            invested = (float(p.get("investmentPct", 0.0) or 0.0) / 100.0) * INITIAL_TOTAL
            np = float(p.get("netProfit", 0.0) or 0.0)
            current_val = invested * (1 + np / 100.0)
            open_rate = float(p.get("openRate", 0.0) or 0.0)
            if iid not in aggregated:
                aggregated[iid] = {
                    "instrumentId": iid,
                    "_invested": invested,
                    "_current": current_val,
                    "_openRate": open_rate,
                    "isBuy": p.get("isBuy", True),
                }
            else:
                aggregated[iid]["_invested"] += invested
                aggregated[iid]["_current"] += current_val

        positions = []
        total_invested = 0.0
        total_current = 0.0
        for a in aggregated.values():
            invested, current_val = a["_invested"], a["_current"]
            total_invested += invested
            total_current += current_val
            pnl = current_val - invested
            open_rate = a["_openRate"] or 1.0
            quantity = invested / open_rate if open_rate else 0.0
            positions.append({
                "instrumentId": a["instrumentId"],
                "instrument_id": a["instrumentId"],
                "quantity": round(quantity, 6),
                "avgBuyPrice": round(open_rate, 4),
                "currentPrice": round(current_val / quantity, 4) if quantity else 0.0,
                "currentValue": round(current_val, 2),
                "unrealizedPnL": round(pnl, 2),
                "unrealizedPnLPercent": round((pnl / invested * 100.0) if invested else 0.0, 2),
                "isBuy": a["isBuy"],
            })

        positions.sort(key=lambda x: x["currentValue"], reverse=True)

        total_value = total_current + cash
        total_pnl = total_current - total_invested
        return {
            "username": settings.etoro_username,
            "totalPortfolioValue": round(total_value, 2),
            "totalPnL": round(total_pnl, 2),
            "totalPnLPercent": round((total_pnl / total_invested * 100.0) if total_invested else 0.0, 2),
            "credit": round(cash, 2),
            "positions": positions,
        }

    async def _fetch_from_api(self) -> dict:
        request_headers = {
            **self.headers,
            "x-request-id": str(uuid.uuid4()),
        }
        # PUBLIC (social-trading) portfolio of the configured user. This exposes
        # allocation percentages + per-position P&L for any eToro username — it does
        # NOT require own-account scopes, only valid x-api-key / x-user-key.
        # (The private own-account endpoint is /api/v1/trading/info/{demo/}pnl and
        #  needs demo:read|real:read scopes on a registered key.)
        url = f"{self.base_url}/api/v1/user-info/people/{settings.etoro_username}/portfolio/live"
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(url, headers=request_headers)
            response.raise_for_status()
            return response.json()

    async def get_live_portfolio(self) -> dict:
        # 1. Return mock data immediately in dev mode
        if settings.use_mock_data:
            logger.info("[eToro] Mock mode active — returning static portfolio")
            data = mock_data.MOCK_ETORO_PORTFOLIO.copy()
            data["positions"] = await self._enrich_positions(data["positions"])
            return data

        # 1b. Preflight credential check — fail fast with an actionable message
        #     instead of letting eToro return a cryptic 404.
        problem = etoro_credential_problem()
        if problem:
            logger.warning(f"[eToro] Credentials not usable: {problem}")
            return {"error": problem, "detail": "eToro API credentials invalid or unregistered"}

        logger.info(f"[eToro] Using live API (env={settings.etoro_env}) for user '{settings.etoro_username}'")

        # 2. Check in-memory cache
        cache_key = f"etoro:portfolio:{settings.etoro_username}"
        cached = cache_service.cache_get(cache_key)
        if cached is not None:
            logger.info("[eToro] Cache HIT for portfolio")
            return cached

        # 3. Try live API call through circuit breaker
        try:
            data = await self._cb.call(self._fetch_from_api)
            result = self._parse_portfolio(data)
            result["positions"] = await self._enrich_positions(result["positions"])
            cache_service.cache_set(cache_key, result, PORTFOLIO_TTL)
            return result
        except CircuitBreakerOpen as e:
            logger.warning(f"[eToro] {e} — falling back to mock data")
            data = mock_data.MOCK_ETORO_PORTFOLIO.copy()
            data["positions"] = await self._enrich_positions(data["positions"])
            data["_fallback"] = "circuit_breaker_open"
            return data
        except Exception as e:
            logger.error(f"[eToro] API error: {e}")
            return {"error": str(e), "detail": "eToro API unavailable"}

    async def get_instruments(self) -> list:
        """Returns the full static instrument list (no API call needed)."""
        return instrument_resolver.all_instruments()