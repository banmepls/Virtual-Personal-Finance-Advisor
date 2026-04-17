"""
app/api/v1/endpoints/budget.py
────────────────────────────────
Budget management endpoints: CRUD + status vs. actual spending.
"""
import logging
from datetime import date
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete

from app.core.database import get_db
from app.models.budget import Budget
from app.models.bank_transaction import BankTransaction
from app.schemas.schemas import (
    BudgetCreateRequest, BudgetResponse, BudgetStatusItem, BudgetStatusResponse,
)

router = APIRouter()
logger = logging.getLogger(__name__)

DEFAULT_USER_ID = 1


@router.get("/", response_model=list[BudgetResponse])
async def list_budgets(
    user_id: int = DEFAULT_USER_ID,
    month_year: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db),
):
    """List all budgets for the user, optionally filtered by month."""
    q = select(Budget).where(Budget.user_id == user_id)
    if month_year:
        q = q.where(Budget.month_year == month_year)
    result = await db.execute(q.order_by(Budget.category))
    return result.scalars().all()


@router.post("/", response_model=BudgetResponse)
async def create_or_update_budget(
    body: BudgetCreateRequest,
    user_id: int = DEFAULT_USER_ID,
    db: AsyncSession = Depends(get_db),
):
    """
    Create or update a monthly category budget.
    If a budget for the same category + month already exists, it will be updated.
    """
    result = await db.execute(
        select(Budget).where(
            Budget.user_id == user_id,
            Budget.category == body.category,
            Budget.month_year == body.month_year,
        )
    )
    budget = result.scalar_one_or_none()
    if budget:
        budget.limit_amount = body.limit_amount
        budget.currency = body.currency
    else:
        budget = Budget(
            user_id=user_id,
            category=body.category,
            month_year=body.month_year,
            limit_amount=body.limit_amount,
            currency=body.currency,
        )
        db.add(budget)
    await db.commit()
    await db.refresh(budget)
    return budget


@router.delete("/{budget_id}")
async def delete_budget(
    budget_id: int,
    user_id: int = DEFAULT_USER_ID,
    db: AsyncSession = Depends(get_db),
):
    """Delete a budget by ID."""
    result = await db.execute(
        select(Budget).where(Budget.id == budget_id, Budget.user_id == user_id)
    )
    budget = result.scalar_one_or_none()
    if not budget:
        raise HTTPException(status_code=404, detail="Budget not found")
    await db.delete(budget)
    await db.commit()
    return {"message": "Budget deleted"}


@router.get("/status", response_model=BudgetStatusResponse)
async def budget_status(
    user_id: int = DEFAULT_USER_ID,
    month_year: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db),
):
    """
    Compare each budget limit against actual spending for the month.
    Returns budget health status per category.
    """
    if not month_year:
        month_year = date.today().strftime("%Y-%m")

    # Load budgets
    bgt_result = await db.execute(
        select(Budget).where(Budget.user_id == user_id, Budget.month_year == month_year)
    )
    budgets = bgt_result.scalars().all()

    # Load spending this month
    tx_result = await db.execute(
        select(BankTransaction).where(
            BankTransaction.user_id == user_id,
            BankTransaction.is_debit == True,
            BankTransaction.booking_date.cast(str).like(f"{month_year}%"),
        )
    )
    transactions = tx_result.scalars().all()

    # Aggregate by category
    spent_by_cat: dict[str, float] = {}
    for tx in transactions:
        if tx.category in ("Income", "Other"):
            continue
        spent_by_cat[tx.category] = spent_by_cat.get(tx.category, 0.0) + abs(tx.amount)

    items: list[BudgetStatusItem] = []
    for b in budgets:
        spent = spent_by_cat.get(b.category, 0.0)
        pct = (spent / b.limit_amount * 100) if b.limit_amount else 0
        if pct > 100:
            status = "exceeded"
        elif pct > 75:
            status = "warning"
        else:
            status = "ok"
        items.append(BudgetStatusItem(
            category=b.category,
            limit_amount=b.limit_amount,
            spent_amount=round(spent, 2),
            remaining=round(max(b.limit_amount - spent, 0), 2),
            percentage_used=round(pct, 1),
            currency=b.currency,
            status=status,
        ))

    return BudgetStatusResponse(month_year=month_year, budgets=items)
