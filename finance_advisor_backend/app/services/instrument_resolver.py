"""
app/services/instrument_resolver.py
------------------------------------
Translates eToro numeric instrumentId → readable {symbol, name, asset_class}.

Priority order:
  1. Static mapping (fast, no API call, no quota cost)
  2. Graceful fallback: "UNKNOWN_<id>"

The static map covers the most commonly traded instruments on eToro.
Additional IDs discovered at runtime are cached in memory.
"""
import logging

logger = logging.getLogger(__name__)

# ── Static instrument map ─────────────────────────────────────────────────────
# Format: { instrument_id: (symbol, name, asset_class) }
_INSTRUMENT_MAP: dict[int, tuple[str, str, str]] = {
    # Stocks
    1:  ("AAPL",  "Apple Inc.",                "Stocks"),
    2:  ("TSLA",  "Tesla Inc.",                "Stocks"),
    3:  ("AMZN",  "Amazon.com Inc.",           "Stocks"),
    4:  ("GOOGL", "Alphabet Inc.",             "Stocks"),
    5:  ("MSFT",  "Microsoft Corporation",     "Stocks"),
    6:  ("NVDA",  "NVIDIA Corporation",        "Stocks"),
    7:  ("META",  "Meta Platforms Inc.",       "Stocks"),
    8:  ("AMD",   "Advanced Micro Devices",    "Stocks"),
    9:  ("NFLX",  "Netflix Inc.",              "Stocks"),
    10: ("DIS",   "The Walt Disney Company",   "Stocks"),
    11: ("BA",    "Boeing Company",            "Stocks"),
    12: ("JPM",   "JPMorgan Chase & Co.",      "Stocks"),
    13: ("GS",    "Goldman Sachs Group Inc.",  "Stocks"),
    14: ("V",     "Visa Inc.",                 "Stocks"),
    15: ("PFE",   "Pfizer Inc.",               "Stocks"),
    16: ("XOM",   "Exxon Mobil Corporation",   "Stocks"),
    17: ("WMT",   "Walmart Inc.",              "Stocks"),
    18: ("COIN",  "Coinbase Global Inc.",      "Stocks"),
    19: ("UBER",  "Uber Technologies Inc.",    "Stocks"),
    20: ("PLTR",  "Palantir Technologies",     "Stocks"),
    # ETFs
    30: ("SPY",   "SPDR S&P 500 ETF",          "ETF"),
    31: ("QQQ",   "Invesco QQQ Trust",         "ETF"),
    32: ("VTI",   "Vanguard Total Stock ETF",  "ETF"),
    33: ("ARKK",  "ARK Innovation ETF",        "ETF"),
    # Crypto
    50: ("BTC",   "Bitcoin",                   "Crypto"),
    51: ("ETH",   "Ethereum",                  "Crypto"),
    52: ("SOL",   "Solana",                    "Crypto"),
    53: ("ADA",   "Cardano",                   "Crypto"),
    54: ("XRP",   "Ripple",                    "Crypto"),
    55: ("DOGE",  "Dogecoin",                  "Crypto"),
    56: ("BNB",   "Binance Coin",              "Crypto"),
    57: ("AVAX",  "Avalanche",                 "Crypto"),
    # Forex
    70: ("EUR/USD", "Euro / US Dollar",        "Forex"),
    71: ("GBP/USD", "British Pound / USD",     "Forex"),
    72: ("USD/JPY", "US Dollar / Japanese Yen","Forex"),
    73: ("AUD/USD", "Australian Dollar / USD", "Forex"),
    # Commodities
    90: ("GOLD",  "Gold Spot",                 "Commodities"),
    91: ("SILVER","Silver Spot",               "Commodities"),
    64: ("OIL",   "Crude Oil WTI",             "Commodities"),
    # Adding more common IDs found in logs/mock
    100: ("GOOG",  "Alphabet Inc. (Class C)",   "Stocks"),
    1112: ("F", "Ford Motor Company", "Stocks"),
    1253: ("MC.PA", "LVMH Moet Hennessy Louis Vuitton SE", "Stocks"),
    100003: ("XRP",   "Ripple",  "Crypto"),
}

# Runtime-populated cache for IDs discovered dynamically
_runtime_cache: dict[int, dict] = {}


def is_mapped(instrument_id: int) -> bool:
    """Check if we have a real mapping for this ID (static or runtime)."""
    return instrument_id in _INSTRUMENT_MAP or (
        instrument_id in _runtime_cache and _runtime_cache[instrument_id]["asset_class"] != "Unknown"
    )


def is_seen(instrument_id: int) -> bool:
    """Check if we have already encountered this ID in this session."""
    return instrument_id in _INSTRUMENT_MAP or instrument_id in _runtime_cache


def resolve(instrument_id: int) -> dict:
    """
    Resolve a numeric eToro instrument_id to human-readable info.

    Returns:
        {
          "instrument_id": int,
          "symbol": str,
          "name": str,
          "asset_class": str,
        }
    """
    if instrument_id in _runtime_cache:
        return _runtime_cache[instrument_id]

    if instrument_id in _INSTRUMENT_MAP:
        symbol, name, asset_class = _INSTRUMENT_MAP[instrument_id]
        result = {
            "instrument_id": instrument_id,
            "symbol": symbol,
            "name": name,
            "asset_class": asset_class,
        }
        _runtime_cache[instrument_id] = result
        return result

    logger.warning(f"[InstrumentResolver] Unknown instrument_id={instrument_id}, using fallback")
    fallback = {
        "instrument_id": instrument_id,
        "symbol": f"ID_{instrument_id}",
        "name": f"Unknown Instrument #{instrument_id}",
        "asset_class": "Unknown",
    }
    _runtime_cache[instrument_id] = fallback
    return fallback


def register(instrument_id: int, symbol: str, name: str, asset_class: str):
    """Dynamically register a new instrument mapping at runtime."""
    _runtime_cache[instrument_id] = {
        "instrument_id": instrument_id,
        "symbol": symbol,
        "name": name,
        "asset_class": asset_class,
    }


def all_instruments() -> list[dict]:
    """Return all known instruments from the static map."""
    result = []
    for iid, (symbol, name, asset_class) in _INSTRUMENT_MAP.items():
        result.append({
            "instrument_id": iid,
            "symbol": symbol,
            "name": name,
            "asset_class": asset_class,
        })
    return result
