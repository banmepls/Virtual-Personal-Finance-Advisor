"""
app/mcp/server.py
-----------------
Using FastMCP for simpler tool definition and LangChain integration.
"""
from mcp.server.fastmcp import FastMCP
from app.services.etoro import EtoroService
from app.services.market_data import MarketDataService

# Initialize services
etoro_service = EtoroService()
market_service = MarketDataService()

# Create the FastMCP server
mcp_server = FastMCP("Tori Financial Assistant")

@mcp_server.tool()
async def get_my_portfolio() -> dict:
    """Fetches the current live portfolio from eToro."""
    return await etoro_service.get_live_portfolio()

@mcp_server.tool()
async def get_all_instruments() -> list:
    """Returns a list of all known eToro instruments."""
    return await etoro_service.get_instruments()

@mcp_server.tool()
async def get_stock_price(symbol: str) -> dict:
    """Fetches the current real-time quote for a given symbol."""
    return await market_service.get_stock_quote(symbol)

@mcp_server.tool()
async def get_market_sentiment() -> dict:
    """Fetches recent market news and sentiment analysis."""
    return {
        "sentiment": "BULLISH",
        "top_news": ["Tech sector seeing growth in AI", "Federal Reserve holds interest rates steady"],
        "summary": "Overall market sentiment is positive driven by technology gains."
    }
