"""
app/api/v1/endpoints/bank.py
────────────────────────────
Banca Transilvania PSD2 AISP proxy endpoints.
Handles consent creation, account listing, balance, transactions, sync, and subscriptions.
"""
import json
import logging
from datetime import date, timedelta
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete

from app.core.database import get_db
from app.models.bank_connection import BTConnection
from app.models.bank_transaction import BankTransaction
from app.services.bt_service import bt_service
from app.services.expense_categorizer import (
    categorize_transaction, detect_recurring,
    get_spending_by_category, extract_subscriptions,
)
from app.schemas.schemas import (
    BankConnectResponse, BankAccountResponse, BankBalanceResponse,
    BankBalanceItem, BankBalanceAmount, BankTransactionResponse,
    SpendingSummaryResponse, SubscriptionResponse,
)

router = APIRouter()
logger = logging.getLogger(__name__)

DEFAULT_USER_ID = 1  # TODO: extract from JWT token in production


# ── Connect / Consent ──────────────────────────────────────────────────────────

@router.post("/connect", response_model=BankConnectResponse)
async def connect_bank(user_id: int = DEFAULT_USER_ID, db: AsyncSession = Depends(get_db)):
    """
    Initiate Banca Transilvania PSD2 consent.
    In sandbox mode returns a mock consent immediately.
    In production mode initiates OAuth2 redirect flow.
    """
    try:
        consent_data = await bt_service.create_consent(user_id)
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"BT consent creation failed: {e}")

    consent_id = consent_data["consentId"]
    is_sandbox = consent_data.get("_sandbox", False)

    # Upsert connection record
    result = await db.execute(
        select(BTConnection).where(BTConnection.user_id == user_id)
    )
    conn = result.scalar_one_or_none()
    if conn:
        conn.consent_id = consent_id
        conn.is_active = True
        conn.is_sandbox = is_sandbox
    else:
        conn = BTConnection(user_id=user_id, consent_id=consent_id, is_sandbox=is_sandbox)
        db.add(conn)
    await db.commit()

    return BankConnectResponse(
        consent_id=consent_id,
        is_sandbox=is_sandbox,
        message="✅ BT Sandbox connected. Transactions will use realistic mock Romanian data."
        if is_sandbox else "🔗 BT consent created. Please complete the OAuth2 authorization.",
    )


# ── Accounts ──────────────────────────────────────────────────────────────────

@router.get("/accounts", response_model=list[BankAccountResponse])
async def get_accounts(user_id: int = DEFAULT_USER_ID, db: AsyncSession = Depends(get_db)):
    """List BT payment accounts for the user."""
    conn = await _get_connection(user_id, db)
    try:
        data = await bt_service.get_accounts(conn.consent_id)
    except Exception as e:
        raise HTTPException(status_code=503, detail=str(e))

    accounts = []
    for acc in data.get("accounts", []):
        accounts.append(BankAccountResponse(
            resource_id=acc.get("resourceId", ""),
            iban=acc.get("iban", ""),
            currency=acc.get("currency", "RON"),
            name=acc.get("name", ""),
            status=acc.get("status", "enabled"),
        ))
    return accounts


# ── Balances ──────────────────────────────────────────────────────────────────

@router.get("/balances/{account_id}", response_model=BankBalanceResponse)
async def get_balances(account_id: str, user_id: int = DEFAULT_USER_ID,
                       db: AsyncSession = Depends(get_db)):
    """Get balance for a specific BT account."""
    conn = await _get_connection(user_id, db)
    try:
        data = await bt_service.get_balances(account_id, conn.consent_id)
    except Exception as e:
        raise HTTPException(status_code=503, detail=str(e))

    iban = data.get("account", {}).get("iban", account_id)
    balances = []
    for b in data.get("balances", []):
        amt = b.get("balanceAmount", {})
        balances.append(BankBalanceItem(
            balance_type=b.get("balanceType", ""),
            balance_amount=BankBalanceAmount(
                currency=amt.get("currency", "RON"),
                amount=amt.get("amount", "0.00"),
            ),
        ))
    return BankBalanceResponse(account_id=account_id, iban=iban, balances=balances)


# ── Transactions (cached) ─────────────────────────────────────────────────────

@router.get("/transactions", response_model=list[BankTransactionResponse])
async def get_transactions(
    user_id: int = DEFAULT_USER_ID,
    account_id: Optional[str] = Query(None),
    month_year: Optional[str] = Query(None, description="YYYY-MM filter"),
    limit: int = Query(100, le=500),
    db: AsyncSession = Depends(get_db),
):
    """Get cached bank transactions, optionally filtered by account or month."""
    q = select(BankTransaction).where(BankTransaction.user_id == user_id)
    if account_id:
        q = q.where(BankTransaction.account_id == account_id)
    if month_year:
        q = q.where(BankTransaction.booking_date.cast(str).like(f"{month_year}%"))
    q = q.order_by(BankTransaction.booking_date.desc()).limit(limit)

    result = await db.execute(q)
    rows = result.scalars().all()

    # If no cached transactions, auto-sync
    if not rows:
        logger.info("No cached transactions — auto-syncing from BT")
        await _sync_transactions(user_id, db)
        result = await db.execute(q)
        rows = result.scalars().all()

    return rows


# ── Sync ──────────────────────────────────────────────────────────────────────

@router.post("/sync")
async def sync_transactions(user_id: int = DEFAULT_USER_ID, db: AsyncSession = Depends(get_db)):
    """Force re-sync of bank transactions from BT API."""
    count = await _sync_transactions(user_id, db)
    return {"synced": count, "message": f"✅ Synced {count} transactions"}


async def _sync_transactions(user_id: int, db: AsyncSession) -> int:
    """Internal: fetch from BT, categorize, persist to DB."""
    conn = await _get_connection(user_id, db)

    # Fetch accounts
    account_data = await bt_service.get_accounts(conn.consent_id)
    accounts = account_data.get("accounts", [])
    if not accounts:
        return 0

    total = 0
    for acc in accounts:
        account_id = acc.get("resourceId", "")
        date_from = date.today() - timedelta(days=90)
        tx_data = await bt_service.get_transactions(
            account_id, conn.consent_id, date_from=date_from
        )
        raw_txns = tx_data.get("transactions", {}).get("booked", [])

        # Apply recurring detection
        raw_txns = detect_recurring(raw_txns)

        for tx in raw_txns:
            tx_id = tx.get("transactionId", "")
            if not tx_id:
                continue

            # Check for duplicate
            exists = await db.execute(
                select(BankTransaction).where(BankTransaction.transaction_id == tx_id)
            )
            if exists.scalar_one_or_none():
                continue

            amt_data = tx.get("transactionAmount", {})
            try:
                amount = float(amt_data.get("amount", 0))
            except (TypeError, ValueError):
                amount = 0.0

            remittance = tx.get("remittanceInformationUnstructured", "")
            creditor = tx.get("creditorName", "")
            # Use pre-computed category if available (sandbox), else keyword classify
            category = (tx.get("_category")
                        or categorize_transaction(remittance, creditor))

            bd_str = tx.get("bookingDate")
            vd_str = tx.get("valueDate")
            try:
                bd = date.fromisoformat(bd_str) if bd_str else None
                vd = date.fromisoformat(vd_str) if vd_str else None
            except ValueError:
                bd = vd = None

            row = BankTransaction(
                user_id=user_id,
                account_id=account_id,
                transaction_id=tx_id,
                booking_date=bd,
                value_date=vd,
                amount=amount,
                currency=amt_data.get("currency", "RON"),
                creditor_name=creditor or None,
                debtor_name=tx.get("debtorName") or None,
                remittance_info=remittance or None,
                category=category,
                is_recurring=bool(tx.get("_isRecurring", False)),
                is_debit=amount < 0,
            )
            db.add(row)
            total += 1

    await db.commit()
    return total


# ── Spending Summary ──────────────────────────────────────────────────────────

@router.get("/spending-summary", response_model=SpendingSummaryResponse)
async def spending_summary(
    user_id: int = DEFAULT_USER_ID,
    month_year: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db),
):
    """Monthly spending breakdown by AI category."""
    if not month_year:
        month_year = date.today().strftime("%Y-%m")

    q = (select(BankTransaction)
         .where(BankTransaction.user_id == user_id)
         .where(BankTransaction.is_debit == True)
         .where(BankTransaction.booking_date.cast(str).like(f"{month_year}%")))
    result = await db.execute(q)
    rows = result.scalars().all()

    # Map ORM rows to dict for categorizer
    tx_dicts = [{"bookingDate": str(r.booking_date), "amount": r.amount,
                 "_category": r.category, "transactionAmount": {"amount": str(r.amount)}}
                for r in rows]
    categories = get_spending_by_category(tx_dicts, month_year)
    total = sum(categories.values())

    return SpendingSummaryResponse(
        month_year=month_year, categories=categories, total_spent=round(total, 2)
    )


# ── Subscriptions ─────────────────────────────────────────────────────────────

@router.get("/subscriptions", response_model=list[SubscriptionResponse])
async def get_subscriptions(user_id: int = DEFAULT_USER_ID, db: AsyncSession = Depends(get_db)):
    """Auto-detected recurring subscription charges."""
    q = (select(BankTransaction)
         .where(BankTransaction.user_id == user_id)
         .where(BankTransaction.is_recurring == True)
         .order_by(BankTransaction.booking_date.desc()))
    result = await db.execute(q)
    rows = result.scalars().all()

    tx_dicts = [{
        "creditorName": r.creditor_name,
        "bookingDate": str(r.booking_date),
        "transactionAmount": {"amount": str(r.amount), "currency": r.currency},
        "_category": r.category,
        "_isRecurring": r.is_recurring,
    } for r in rows]

    subs = extract_subscriptions(tx_dicts)
    return [SubscriptionResponse(**s) for s in subs]


# ── Helper ────────────────────────────────────────────────────────────────────

async def _get_connection(user_id: int, db: AsyncSession) -> BTConnection:
    result = await db.execute(
        select(BTConnection).where(BTConnection.user_id == user_id, BTConnection.is_active == True)
    )
    conn = result.scalar_one_or_none()
    if not conn:
        # Auto-create sandbox connection
        consent_data = await bt_service.create_consent(user_id)
        conn = BTConnection(
            user_id=user_id,
            consent_id=consent_data["consentId"],
            is_sandbox=consent_data.get("_sandbox", True),
        )
        db.add(conn)
        await db.commit()
        await db.refresh(conn)
    return conn
