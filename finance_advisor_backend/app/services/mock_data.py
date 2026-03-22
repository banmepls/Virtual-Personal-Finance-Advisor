"""
app/services/mock_data.py
-------------------------
Static mock responses for development and testing.

Activated automatically when USE_MOCK_DATA=true in .env
or when circuit breakers are OPEN and quota is exceeded.

Provides realistic fake data that mirrors actual API response shapes.
"""
from datetime import datetime, timezone

# ── eToro mock data ───────────────────────────────────────────────────────────

MOCK_ETORO_PORTFOLIO = {
    "username": "demo_user",
    "totalPortfolioValue": 12450.75,
    "totalPnL": 1234.50,
    "totalPnLPercent": 11.0,
    "positions": [
        {
            "instrument_id": 1,
            "instrumentId": 1,
            "symbol": "AAPL",
            "name": "Apple Inc.",
            "asset_class": "Stocks",
            "quantity": 5.0,
            "avgBuyPrice": 155.20,
            "currentPrice": 187.50,
            "currentValue": 937.50,
            "unrealizedPnL": 162.50,
            "unrealizedPnLPercent": 20.9,
        },
        {
            "instrument_id": 12,
            "instrumentId": 12,
            "symbol": "BTC/USD",
            "name": "Bitcoin",
            "asset_class": "Crypto",
            "quantity": 0.05,
            "avgBuyPrice": 35000.0,
            "currentPrice": 67800.0,
            "currentValue": 3390.0,
            "unrealizedPnL": 1390.0,
            "unrealizedPnLPercent": 69.5,
        },
        {
            "instrument_id": 6,
            "instrumentId": 6,
            "symbol": "NVDA",
            "name": "NVIDIA Corporation",
            "asset_class": "Stocks",
            "quantity": 3.0,
            "avgBuyPrice": 420.0,
            "currentPrice": 875.0,
            "currentValue": 2625.0,
            "unrealizedPnL": 1365.0,
            "unrealizedPnLPercent": 108.3,
        },
        {
            "instrument_id": 2,
            "instrumentId": 2,
            "symbol": "TSLA",
            "name": "Tesla Inc.",
            "asset_class": "Stocks",
            "quantity": 4.0,
            "avgBuyPrice": 280.0,
            "currentPrice": 195.0,
            "currentValue": 780.0,
            "unrealizedPnL": -340.0,
            "unrealizedPnLPercent": -30.4,
        },
    ],
}

MOCK_ETORO_INSTRUMENTS = [
    {"instrumentId": 1, "symbol": "AAPL", "name": "Apple Inc.", "assetClass": "Stocks"},
    {"instrumentId": 2, "symbol": "TSLA", "name": "Tesla Inc.", "assetClass": "Stocks"},
    {"instrumentId": 3, "symbol": "AMZN", "name": "Amazon.com Inc.", "assetClass": "Stocks"},
    {"instrumentId": 4, "symbol": "GOOGL", "name": "Alphabet Inc.", "assetClass": "Stocks"},
    {"instrumentId": 5, "symbol": "MSFT", "name": "Microsoft Corporation", "assetClass": "Stocks"},
    {"instrumentId": 6, "symbol": "NVDA", "name": "NVIDIA Corporation", "assetClass": "Stocks"},
    {"instrumentId": 7, "symbol": "META", "name": "Meta Platforms Inc.", "assetClass": "Stocks"},
    {"instrumentId": 8, "symbol": "AMD", "name": "Advanced Micro Devices", "assetClass": "Stocks"},
    {"instrumentId": 9, "symbol": "SPY", "name": "SPDR S&P 500 ETF", "assetClass": "ETF"},
    {"instrumentId": 10, "symbol": "QQQ", "name": "Invesco QQQ Trust", "assetClass": "ETF"},
    {"instrumentId": 11, "symbol": "ETH/USD", "name": "Ethereum", "assetClass": "Crypto"},
    {"instrumentId": 12, "symbol": "BTC/USD", "name": "Bitcoin", "assetClass": "Crypto"},
    {"instrumentId": 13, "symbol": "EUR/USD", "name": "Euro / US Dollar", "assetClass": "Forex"},
    {"instrumentId": 14, "symbol": "GBP/USD", "name": "British Pound / US Dollar", "assetClass": "Forex"},
    {"instrumentId": 15, "symbol": "GOLD", "name": "Gold Spot", "assetClass": "Commodities"},
]


# ── Alpha Vantage mock data ───────────────────────────────────────────────────

def mock_stock_quote(symbol: str) -> dict:
    """Returns a mock stock quote for any symbol."""
    mock_prices = {
        "AAPL": {"price": 187.50, "change_percent": "+1.25%", "volume": "52134200"},
        "TSLA": {"price": 195.00, "change_percent": "-2.10%", "volume": "34521000"},
        "NVDA": {"price": 875.00, "change_percent": "+3.40%", "volume": "41230100"},
        "AMZN": {"price": 182.30, "change_percent": "+0.75%", "volume": "28910500"},
        "MSFT": {"price": 415.70, "change_percent": "+0.95%", "volume": "22105400"},
        "GOOGL": {"price": 175.20, "change_percent": "-0.30%", "volume": "19542300"},
    }
    data = mock_prices.get(symbol.upper(), {
        "price": 100.00,
        "change_percent": "+0.00%",
        "volume": "1000000",
    })
    return {
        "symbol": symbol.upper(),
        "price": data["price"],
        "change_percent": data["change_percent"],
        "volume": data["volume"],
        "source": "mock",
    }
def mock_stock_history(symbol: str, days: int = 30) -> list:
    """
    Generates a unique but deterministic price history for a symbol.
    Uses the symbol string as a seed so different symbols have different waves,
    but the same symbol always has the same wave.
    """
    import random
    import math
    
    # Simple deterministic seed from symbol
    seed = sum(ord(c) for c in symbol.upper())
    rng = random.Random(seed)
    
    # Base price (seeded)
    base_price = rng.uniform(50.0, 500.0)
    history = []
    
    # Trend and Volatility (seeded)
    trend = rng.uniform(-0.02, 0.02)
    volatility = rng.uniform(0.01, 0.05)
    
    current = base_price
    for i in range(days):
        # Brownian motion-ish walk
        change = current * (trend + rng.normalvariate(0, volatility))
        current += change
        # Add a sine wave for some 'texture'
        wave = math.sin(i * 0.5) * (base_price * 0.02)
        
        history.append({
            "date": (datetime.now(timezone.utc)).strftime("%Y-%m-%d"),
            "price": round(current + wave, 2)
        })
        
    return history
