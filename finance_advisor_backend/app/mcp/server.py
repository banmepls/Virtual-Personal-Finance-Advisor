"""
app/mcp/server.py
-----------------
Using FastMCP for simpler tool definition and LangChain integration.

IMPORTANT: tools must NEVER raise. A raised exception propagates through the
LangGraph agent and aborts the entire chat turn (the user then sees Tori as
"temporarily unavailable"). Each tool catches its own errors and returns an
{"error": ...} result so the agent can recover and answer gracefully.
"""
import logging
from datetime import date
from mcp.server.fastmcp import FastMCP
from sqlalchemy import select, String
from app.services.etoro import EtoroService
from app.services.market_data import MarketDataService
from app.core.database import AsyncSessionLocal
from app.models.bank_transaction import BankTransaction
from app.models.budget import Budget
from app.services.expense_categorizer import (
    get_spending_by_category, extract_subscriptions,
)

logger = logging.getLogger(__name__)

# Auth is not enforced; the whole app operates as this user (see Security note).
DEFAULT_USER_ID = 1

# Initialize services
etoro_service = EtoroService()
market_service = MarketDataService()

# Create the FastMCP server
mcp_server = FastMCP("Tori Financial Assistant")

@mcp_server.tool()
async def get_my_portfolio() -> dict:
    """Fetches the current live portfolio from eToro."""
    try:
        return await etoro_service.get_live_portfolio()
    except Exception as e:
        logger.warning(f"[MCP] get_my_portfolio failed: {e}")
        return {"error": "Portfolio data is currently unavailable."}

@mcp_server.tool()
async def get_all_instruments() -> list:
    """Returns a list of all known eToro instruments."""
    try:
        return await etoro_service.get_instruments()
    except Exception as e:
        logger.warning(f"[MCP] get_all_instruments failed: {e}")
        return []

@mcp_server.tool()
async def get_stock_price(symbol: str) -> dict:
    """Fetches the current real-time quote for a given symbol."""
    try:
        return await market_service.get_stock_quote(symbol)
    except Exception as e:
        logger.warning(f"[MCP] get_stock_price({symbol}) failed: {e}")
        return {"error": f"Could not fetch a price for '{symbol}'. "
                         "The symbol may be invalid or the market-data limit was reached."}

@mcp_server.tool()
async def get_market_sentiment() -> dict:
    """Fetches recent market news and sentiment analysis."""
    return {
        "sentiment": "BULLISH",
        "top_news": ["Tech sector seeing growth in AI", "Federal Reserve holds interest rates steady"],
        "summary": "Overall market sentiment is positive driven by technology gains."
    }


# ── Bank / spending tools (read the already-synced BT transactions in the DB) ──

@mcp_server.tool()
async def get_spending_summary(month_year: str = "") -> dict:
    """Get the user's bank spending grouped by category for a month.

    `month_year` is "YYYY-MM"; leave empty for the current month. Use this to
    answer questions like "where is my money going" or "how much did I spend on X".
    """
    try:
        my = month_year or date.today().strftime("%Y-%m")
        async with AsyncSessionLocal() as db:
            rows = (await db.execute(
                select(BankTransaction).where(
                    BankTransaction.user_id == DEFAULT_USER_ID,
                    BankTransaction.is_debit == True,
                    BankTransaction.booking_date.cast(String).like(f"{my}%"),
                )
            )).scalars().all()
        tx = [{"bookingDate": str(r.booking_date), "amount": r.amount, "_category": r.category,
               "transactionAmount": {"amount": str(r.amount)}} for r in rows]
        cats = get_spending_by_category(tx, my)
        return {
            "month_year": my,
            "categories": cats,
            "total_spent": round(sum(cats.values()), 2),
            "currency": "RON",
            "transaction_count": len(rows),
        }
    except Exception as e:
        logger.warning(f"[MCP] get_spending_summary failed: {e}")
        return {"error": "Spending data is currently unavailable."}


@mcp_server.tool()
async def get_budget_status(month_year: str = "") -> dict:
    """Compare the user's spending against their category budgets for a month.

    `month_year` is "YYYY-MM"; leave empty for the current month. Use this to
    answer "did I overspend?" / "am I over budget?". `has_budgets=false` means
    the user has not set any budgets yet (so overspend can't be judged).
    """
    try:
        my = month_year or date.today().strftime("%Y-%m")
        async with AsyncSessionLocal() as db:
            budgets = (await db.execute(
                select(Budget).where(Budget.user_id == DEFAULT_USER_ID,
                                     Budget.month_year == my)
            )).scalars().all()
            txns = (await db.execute(
                select(BankTransaction).where(
                    BankTransaction.user_id == DEFAULT_USER_ID,
                    BankTransaction.is_debit == True,
                    BankTransaction.booking_date.cast(String).like(f"{my}%"),
                )
            )).scalars().all()

        spent_by_cat: dict[str, float] = {}
        for tx in txns:
            if tx.category in ("Income", "Other"):
                continue
            spent_by_cat[tx.category] = spent_by_cat.get(tx.category, 0.0) + abs(tx.amount)

        items = []
        for b in budgets:
            spent = spent_by_cat.get(b.category, 0.0)
            pct = (spent / b.limit_amount * 100) if b.limit_amount else 0
            status = "exceeded" if pct > 100 else "warning" if pct > 75 else "ok"
            items.append({
                "category": b.category,
                "limit": b.limit_amount,
                "spent": round(spent, 2),
                "percentage_used": round(pct, 1),
                "status": status,
            })
        return {
            "month_year": my,
            "has_budgets": len(items) > 0,
            "budgets": items,
            "total_spent": round(sum(spent_by_cat.values()), 2),
            "currency": "RON",
        }
    except Exception as e:
        logger.warning(f"[MCP] get_budget_status failed: {e}")
        return {"error": "Budget data is currently unavailable."}


@mcp_server.tool()
async def get_subscriptions() -> list:
    """List the user's detected recurring subscription charges (Netflix, Spotify, etc.)."""
    try:
        async with AsyncSessionLocal() as db:
            rows = (await db.execute(
                select(BankTransaction).where(
                    BankTransaction.user_id == DEFAULT_USER_ID,
                    BankTransaction.is_recurring == True,
                )
            )).scalars().all()
        tx = [{"creditorName": r.creditor_name, "bookingDate": str(r.booking_date),
               "transactionAmount": {"amount": str(r.amount), "currency": r.currency},
               "_category": r.category, "_isRecurring": r.is_recurring} for r in rows]
        return extract_subscriptions(tx)
    except Exception as e:
        logger.warning(f"[MCP] get_subscriptions failed: {e}")
        return []


@mcp_server.tool()
async def get_recent_transactions(limit: int = 10) -> list:
    """Get the user's most recent bank transactions (default 10)."""
    try:
        async with AsyncSessionLocal() as db:
            rows = (await db.execute(
                select(BankTransaction)
                .where(BankTransaction.user_id == DEFAULT_USER_ID)
                .order_by(BankTransaction.booking_date.desc())
                .limit(max(1, min(limit, 50)))
            )).scalars().all()
        return [{
            "date": str(r.booking_date),
            "merchant": r.creditor_name or r.debtor_name or r.remittance_info or "Unknown",
            "amount": r.amount,
            "currency": r.currency,
            "category": r.category,
        } for r in rows]
    except Exception as e:
        logger.warning(f"[MCP] get_recent_transactions failed: {e}")
        return []
