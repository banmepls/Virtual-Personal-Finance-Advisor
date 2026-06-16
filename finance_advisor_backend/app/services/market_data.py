"""
app/services/market_data.py
----------------------------
Yahoo Finance market data service with:
 - Circuit Breaker protection
 - LRU + TTL caching (60-min quote cache)
 - Mock fallback when USE_MOCK_DATA=true or the upstream is unavailable

Yahoo Finance (via the `yfinance` library) needs no API key and imposes no hard
daily request quota, so the previous Alpha Vantage 25 req/day quota guard is gone.
`yfinance` is synchronous, so each call is run in a worker thread to keep the
service interface async.
"""
import asyncio
import logging
import yfinance as yf
from app.core.config import get_settings
from app.core.circuit_breaker import get_circuit_breaker, CircuitBreakerOpen
from app.services import cache_service, mock_data, instrument_resolver

logger = logging.getLogger(__name__)
settings = get_settings()

QUOTE_TTL = 3600   # 60 minutes — quotes rarely need to be fresher during dev
HISTORY_TTL = 86400  # 24 hours — daily candles

# eToro/common tickers for spot crypto are quoted on Yahoo with a "-USD" suffix.
_CRYPTO_SYMBOLS = {"BTC", "ETH", "XRP", "SOL", "ADA", "DOGE", "LTC", "DOT"}


def _to_yahoo_symbol(symbol: str) -> str:
    """Map a plain symbol to the Yahoo Finance convention (crypto → SYM-USD)."""
    s = symbol.upper()
    if s in _CRYPTO_SYMBOLS:
        return f"{s}-USD"
    return s


class MarketDataService:
    def __init__(self):
        self._cb = get_circuit_breaker("yahoo_finance")

    # ── Synchronous yfinance calls (run in a worker thread) ──────────────────

    def _fetch_quote_sync(self, symbol: str) -> dict:
        ticker = yf.Ticker(_to_yahoo_symbol(symbol))
        fi = ticker.fast_info
        price = fi.get("lastPrice") if hasattr(fi, "get") else getattr(fi, "last_price", None)
        prev = fi.get("previousClose") if hasattr(fi, "get") else getattr(fi, "previous_close", None)
        volume = fi.get("lastVolume") if hasattr(fi, "get") else getattr(fi, "last_volume", None)

        if price is None:
            raise ValueError("Symbol not found or no market data available.")

        price = float(price)
        change_pct = ((price - float(prev)) / float(prev) * 100) if prev else 0.0
        return {
            "symbol": symbol.upper(),
            "price": round(price, 4),
            "change_percent": f"{change_pct:+.2f}%",
            "volume": str(int(volume)) if volume else "0",
            "source": "live",
        }

    def _fetch_history_sync(self, symbol: str, days: int) -> list:
        ticker = yf.Ticker(_to_yahoo_symbol(symbol))
        # Pull a little extra to cover weekends/holidays, then trim to `days`.
        hist = ticker.history(period=f"{max(days + 10, 40)}d")
        if hist is None or hist.empty:
            raise ValueError(f"No history found for {symbol}")
        closes = hist["Close"].tail(days)
        return [
            {"date": idx.strftime("%Y-%m-%d"), "price": round(float(val), 4)}
            for idx, val in closes.items()
        ]

    # ── Public async entry points ────────────────────────────────────────────

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
        if settings.use_mock_data:
            logger.info(f"[YahooFinance] Mock mode — returning mock quote for {symbol}")
            return mock_data.mock_stock_quote(symbol)

        # 2. Cache hit
        cached = cache_service.cache_get(cache_key)
        if cached is not None:
            logger.info(f"[YahooFinance] Cache HIT for {symbol}")
            return cached

        # 3. Live call via circuit breaker
        try:
            result = await self._cb.call(
                lambda: asyncio.to_thread(self._fetch_quote_sync, clean_symbol)
            )
            cache_service.cache_set(cache_key, result, QUOTE_TTL)
            return result
        except ValueError as e:
            # Don't count user errors (unknown symbol/ID) toward circuit breaker failure
            logger.warning(f"[MarketDataService] Validation error: {str(e)}")
            raise
        except CircuitBreakerOpen:
            logger.warning(f"[CB:yahoo_finance] Circuit OPEN — falling back to mock for {clean_symbol}")
            return mock_data.mock_stock_quote(clean_symbol)
        except Exception as e:
            logger.error(f"[MarketDataService] Error fetching {clean_symbol}: {str(e)}")
            return mock_data.mock_stock_quote(clean_symbol)

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
        if settings.use_mock_data:
            return mock_data.mock_stock_history(clean_symbol, days)

        # 2. Cache hit (history is cached for 24h as it's daily data)
        cached = cache_service.cache_get(cache_key)
        if cached is not None:
            return cached

        # 3. Live call via circuit breaker
        try:
            result = await self._cb.call(
                lambda: asyncio.to_thread(self._fetch_history_sync, clean_symbol, days)
            )
            cache_service.cache_set(cache_key, result, HISTORY_TTL)
            return result
        except CircuitBreakerOpen:
            logger.warning(f"[CB:yahoo_finance] Circuit OPEN — mock history for {clean_symbol}")
            return mock_data.mock_stock_history(clean_symbol, days)
        except Exception as e:
            logger.error(f"[MarketDataService] Error history {clean_symbol}: {str(e)}")
            return mock_data.mock_stock_history(clean_symbol, days)
