"""
app/api/v1/endpoints/expenses.py
──────────────────────────────────
AI expense analysis endpoints: category breakdown, insights, re-categorization.
Uses Google Gemini (via Tori) for natural language spending summaries.
"""
import logging
from datetime import date
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Body
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, String

from app.core.database import get_db
from app.models.bank_transaction import BankTransaction
from app.models.budget import Budget
from app.services.expense_categorizer import (
    get_spending_by_category, generate_spending_summary_text,
)
from app.schemas.schemas import (
    SpendingSummaryResponse, ExpenseInsightResponse,
)

router = APIRouter()
logger = logging.getLogger(__name__)

DEFAULT_USER_ID = 1

VALID_CATEGORIES = [
    "Food & Groceries", "Transport", "Utilities", "Dining",
    "Shopping", "Health", "Entertainment", "Subscriptions",
    "Rent", "Other",
]


@router.get("/categories", response_model=SpendingSummaryResponse)
async def spending_categories(
    user_id: int = DEFAULT_USER_ID,
    month_year: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db),
):
    """Return spending grouped by category for the given month."""
    if not month_year:
        month_year = date.today().strftime("%Y-%m")

    result = await db.execute(
        select(BankTransaction).where(
            BankTransaction.user_id == user_id,
            BankTransaction.is_debit == True,
            BankTransaction.booking_date.cast(String).like(f"{month_year}%"),
        )
    )
    rows = result.scalars().all()

    tx_dicts = [{"bookingDate": str(r.booking_date), "amount": r.amount,
                 "_category": r.category, "transactionAmount": {"amount": str(r.amount)}}
                for r in rows]
    categories = get_spending_by_category(tx_dicts, month_year)
    total = sum(categories.values())

    return SpendingSummaryResponse(
        month_year=month_year, categories=categories, total_spent=round(total, 2)
    )


@router.get("/insights", response_model=ExpenseInsightResponse)
async def expense_insights(
    user_id: int = DEFAULT_USER_ID,
    month_year: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db),
):
    """
    AI-generated spending insights using Tori (Gemini).
    Summarises top categories, budget gaps, and actionable tips.
    """
    if not month_year:
        month_year = date.today().strftime("%Y-%m")

    # Load transactions
    tx_result = await db.execute(
        select(BankTransaction).where(
            BankTransaction.user_id == user_id,
            BankTransaction.is_debit == True,
            BankTransaction.booking_date.cast(String).like(f"{month_year}%"),
        )
    )
    rows = tx_result.scalars().all()

    # Load budgets
    bgt_result = await db.execute(
        select(Budget).where(Budget.user_id == user_id, Budget.month_year == month_year)
    )
    budgets = [{"category": b.category, "limit_amount": b.limit_amount} for b in bgt_result.scalars().all()]

    tx_dicts = [{"bookingDate": str(r.booking_date), "amount": r.amount,
                 "_category": r.category, "transactionAmount": {"amount": str(r.amount)}}
                for r in rows]
    categories = get_spending_by_category(tx_dicts, month_year)
    total = sum(categories.values())
    top_category = max(categories, key=categories.get) if categories else "N/A"

    # Build a compact prompt for Tori
    summary_text = generate_spending_summary_text(categories, budgets, month_year)

    try:
        from app.agent.tori_agent import ask_tori
        prompt = (
            f"Based on the following spending data for {month_year}, provide a concise financial "
            f"analysis in 3-4 bullet points with actionable advice:\n\n{summary_text}\n\n"
            f"Be specific. Focus on categories that exceed budget or show high spending."
        )
        ai_summary = await ask_tori(prompt, user_id)
    except Exception as e:
        logger.warning(f"Tori AI unavailable: {e}")
        ai_summary = summary_text  # Fallback to rule-based text

    return ExpenseInsightResponse(
        month_year=month_year,
        ai_summary=ai_summary,
        top_category=top_category,
        total_spent=round(total, 2),
    )


@router.post("/categorize/{transaction_id}")
async def re_categorize(
    transaction_id: int,
    category: str = Body(..., embed=True),
    user_id: int = DEFAULT_USER_ID,
    db: AsyncSession = Depends(get_db),
):
    """Manually re-categorize a specific transaction."""
    if category not in VALID_CATEGORIES:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid category. Valid: {VALID_CATEGORIES}"
        )
    result = await db.execute(
        select(BankTransaction).where(
            BankTransaction.id == transaction_id,
            BankTransaction.user_id == user_id,
        )
    )
    tx = result.scalar_one_or_none()
    if not tx:
        raise HTTPException(status_code=404, detail="Transaction not found")
    tx.category = category
    await db.commit()
    return {"message": f"Transaction {transaction_id} re-categorized to '{category}'"}
