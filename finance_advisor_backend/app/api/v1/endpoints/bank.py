"""
app/api/v1/endpoints/bank.py
────────────────────────────
Banca Transilvania PSD2 AISP proxy endpoints.
Handles consent creation, account listing, balance, transactions, sync, and subscriptions.
"""
import json
import logging
from datetime import date, datetime, timedelta, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete, String

from app.core.database import get_db
from app.models.bank_connection import BTConnection
from app.models.bank_transaction import BankTransaction
from app.services.bt_service import bt_service
from app.core.config import get_settings
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
    Returns auth_url=null if the user already has a valid access token.
    """
    # If user already has an authorized connection, skip the consent flow —
    # UNLESS the stored token is the local mock placeholder AND real credentials
    # are now configured, in which case clear it so the real OAuth flow runs.
    _MOCK_TOKEN = "mock_access_token_123"
    _placeholder_ids = {"sandbox_client_id", "", None}
    has_real_creds = (
        bt_service.client_id not in _placeholder_ids
        and bt_service.client_secret not in _placeholder_ids
    )

    result = await db.execute(
        select(BTConnection).where(BTConnection.user_id == user_id, BTConnection.is_active == True)
    )
    existing = result.scalar_one_or_none()
    if existing and existing.access_token:
        # Check whether the user explicitly chose demo mode via sandbox-authorize
        _explicit_demo = False
        if existing.selected_accounts:
            try:
                _explicit_demo = json.loads(existing.selected_accounts).get("_demo_mode", False)
            except Exception:
                pass

        if existing.access_token == _MOCK_TOKEN and has_real_creds and not _explicit_demo:
            # Stale mock token from before real creds were configured — clear it
            existing.access_token  = None
            existing.refresh_token = None
            await db.commit()
        elif (
            existing.token_expires_at is not None
            and existing.token_expires_at < datetime.now(timezone.utc)
        ):
            # Expired real token — clear it so the user can re-authorize
            existing.access_token  = None
            existing.refresh_token = None
            existing.token_expires_at = None
            await db.commit()
        else:
            return BankConnectResponse(
                consent_id=existing.consent_id or "",
                is_sandbox=existing.is_sandbox,
                message="Already authorized",
                auth_url=None,
            )

    try:
        consent_data = await bt_service.create_consent(user_id)
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"BT consent creation failed: {e}")

    consent_id    = consent_data["consentId"]
    is_sandbox    = consent_data.get("_sandbox", False)
    auth_url      = consent_data.get("scaRedirect")
    code_verifier = consent_data.get("_code_verifier")  # present only for real PKCE flow

    # Upsert connection record
    result2 = await db.execute(
        select(BTConnection).where(BTConnection.user_id == user_id)
    )
    conn = result2.scalar_one_or_none()
    if conn:
        conn.consent_id = consent_id
        conn.is_active  = True
        conn.is_sandbox = is_sandbox
        if code_verifier:
            import json as _json
            conn.selected_accounts = _json.dumps({"_pkce_verifier": code_verifier})
    else:
        import json as _json
        conn = BTConnection(
            user_id=user_id,
            consent_id=consent_id,
            is_sandbox=is_sandbox,
            selected_accounts=_json.dumps({"_pkce_verifier": code_verifier}) if code_verifier else None,
        )
        db.add(conn)
    await db.commit()

    return BankConnectResponse(
        consent_id=consent_id,
        is_sandbox=is_sandbox,
        message="🔗 BT consent created. Please complete the OAuth2 authorization.",
        auth_url=auth_url,
    )

@router.get("/sandbox-login", response_class=HTMLResponse)
async def sandbox_login(
    client_id: Optional[str] = None,
    redirect_uri: Optional[str] = None,
    state: Optional[str] = None,
):
    """Simulated BT Keycloak login page for the sandbox OAuth2 demo flow."""
    callback_url = f"/api/v1/bank/oauth2/callback?code=mock_code_sandbox&state={state or ''}"
    html = f"""<!DOCTYPE html>
<html lang="ro">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Banca Transilvania - Autorizare PSD2</title>
  <style>
    *{{box-sizing:border-box;margin:0;padding:0}}
    body{{font-family:'Segoe UI',Tahoma,sans-serif;background:#f0f2f5;display:flex;align-items:center;justify-content:center;height:100vh}}
    .card{{background:#fff;padding:40px;border-radius:12px;box-shadow:0 4px 20px rgba(0,0,0,.12);text-align:center;max-width:420px;width:90%;border-top:5px solid #004B8D}}
    .logo{{width:64px;height:64px;background:#004B8D;border-radius:50%;display:flex;align-items:center;justify-content:center;margin:0 auto 20px}}
    h2{{color:#004B8D;margin-bottom:8px;font-size:22px}}
    p{{color:#555;font-size:14px;margin-bottom:20px;line-height:1.5}}
    .badge{{background:#fff3cd;color:#856404;padding:5px 12px;border-radius:20px;font-size:11px;font-weight:700;display:inline-block;border:1px solid #ffc107;margin-bottom:18px}}
    .btn{{background:#004B8D;color:#fff;border:none;padding:14px;border-radius:8px;font-size:16px;font-weight:600;cursor:pointer;width:100%;text-decoration:none;display:block;transition:background .2s}}
    .btn:hover{{background:#003570}}
    .note{{color:#999;font-size:11px;margin-top:14px}}
  </style>
</head>
<body>
  <div class="card">
    <div class="logo">
      <svg width="34" height="34" fill="white" viewBox="0 0 24 24"><path d="M11.8 10.9c-2.27-.59-3-1.2-3-2.15 0-1.09 1.01-1.85 2.7-1.85 1.78 0 2.44.85 2.5 2.1h2.21c-.07-1.72-1.12-3.3-3.21-3.81V3h-3v2.16c-1.94.42-3.5 1.68-3.5 3.61 0 2.31 1.91 3.46 4.7 4.13 2.5.6 3 1.48 3 2.41 0 .69-.49 1.79-2.7 1.79-2.06 0-2.87-.92-2.98-2.1h-2.2c.12 2.19 1.76 3.42 3.68 3.83V21h3v-2.15c1.95-.37 3.5-1.5 3.5-3.55 0-2.84-2.43-3.81-4.7-4.4z"/></svg>
    </div>
    <span class="badge">🧪 SANDBOX MODE</span>
    <h2>Autorizare BT PSD2</h2>
    <p>Aplicația <strong>Virtual Finance Advisor</strong> solicită acces la datele tale bancare pentru a-ți oferi sfaturi financiare personalizate.</p>
    <a href="{callback_url}" class="btn">✅ Autorizează Accesul</a>
    <p class="note">Pagină de simulare sandbox — nu sunt necesare date reale de autentificare.</p>
  </div>
</body>
</html>"""
    return HTMLResponse(content=html)


@router.get("/oauth2/callback")
async def oauth2_callback(code: str, state: Optional[str] = None, db: AsyncSession = Depends(get_db)):
    """Handle OAuth2 redirect from Banca Transilvania."""
    try:
        # Get the latest pending connection
        result = await db.execute(
            select(BTConnection).where(BTConnection.is_active == True).order_by(BTConnection.updated_at.desc())
        )
        conn = result.scalars().first()
        if not conn:
            return HTMLResponse("<h1>Eroare: Conexiune invalida</h1><p>Nu s-a gasit nicio cerere de autorizare.</p>")
            
        # Exchange code for token
        if code.startswith("mock_code"):
            access_token  = "mock_access_token_123"
            refresh_token = "mock_refresh_token_123"
            expires_in    = 3600
        else:
            # Retrieve stored PKCE code_verifier (if any)
            import json as _json
            code_verifier = None
            if conn and conn.selected_accounts:
                try:
                    meta = _json.loads(conn.selected_accounts)
                    code_verifier = meta.get("_pkce_verifier")
                except Exception:
                    pass

            token_data    = await bt_service.exchange_token(code, code_verifier=code_verifier)
            access_token  = token_data.get("access_token")
            refresh_token = token_data.get("refresh_token")
            expires_in    = token_data.get("expires_in", 3600)

        if conn and access_token:
            conn.access_token  = access_token
            conn.refresh_token = refresh_token
            conn.token_expires_at = datetime.now(timezone.utc) + timedelta(seconds=expires_in)
            conn.selected_accounts = None  # clear the temporary PKCE verifier
            await db.commit()
            
        # Display a success page telling the user to return to the app
        html = """
        <html>
        <head>
            <meta name="viewport" content="width=device-width, initial-scale=1">
            <style>
                body { font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background-color: #f4f6f8; display: flex; align-items: center; justify-content: center; height: 100vh; margin: 0; }
                .card { background: white; padding: 40px; border-radius: 12px; box-shadow: 0 4px 12px rgba(0,0,0,0.1); text-align: center; max-width: 400px; width: 90%; border-top: 5px solid #238636; }
                h2 { color: #238636; margin-top: 0; }
                p { color: #555; line-height: 1.5; }
            </style>
        </head>
        <body>
            <div class="card">
                <h2>Autorizare cu Succes</h2>
                <p>Conturile tale Banca Transilvania au fost conectate cu succes!</p>
                <p style="font-weight: bold; color: #333;">Poti inchide aceasta pagina si sa te intorci in aplicatia Virtual Advisor.</p>
            </div>
        </body>
        </html>
        """
        return HTMLResponse(content=html)
    except Exception as e:
        logger.error(f"OAuth callback failed: {e}")
        error_detail = str(e)
        return HTMLResponse(f"""<!DOCTYPE html>
<html lang="ro">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Eroare Autorizare BT</title>
  <style>
    *{{box-sizing:border-box;margin:0;padding:0}}
    body{{font-family:'Segoe UI',Tahoma,sans-serif;background:#f0f2f5;display:flex;align-items:center;justify-content:center;height:100vh}}
    .card{{background:#fff;padding:36px;border-radius:12px;box-shadow:0 4px 20px rgba(0,0,0,.12);text-align:center;max-width:460px;width:90%;border-top:5px solid #d32f2f}}
    h2{{color:#d32f2f;margin-bottom:12px;font-size:20px}}
    .detail{{background:#fff3f3;border:1px solid #ffcdd2;border-radius:8px;padding:12px;text-align:left;font-size:12px;color:#555;word-break:break-all;margin-bottom:20px;max-height:160px;overflow:auto}}
    p{{color:#666;font-size:13px;margin-bottom:16px;line-height:1.5}}
    .btn{{background:#004B8D;color:#fff;border:none;padding:12px 24px;border-radius:8px;font-size:14px;cursor:pointer;text-decoration:none;display:inline-block}}
  </style>
</head>
<body>
  <div class="card">
    <h2>Eroare de Autorizare</h2>
    <div class="detail">{error_detail}</div>
    <p>Întoarce-te în aplicație și încearcă din nou. Dacă problema persistă, ngrok-ul tău s-ar putea să fi expirat — repornește-l și actualizează <code>BT_REDIRECT_URI</code> în <code>.env</code>.</p>
    <a href="javascript:window.close()" class="btn">Închide fereastra</a>
  </div>
</body>
</html>""", status_code=200)


@router.post("/sandbox-authorize")
async def sandbox_authorize(user_id: int = DEFAULT_USER_ID, db: AsyncSession = Depends(get_db)):
    """Complete sandbox bank authorization without browser redirect.
    Stores a mock access token so accounts/transactions can be fetched immediately."""
    result = await db.execute(
        select(BTConnection)
        .where(BTConnection.user_id == user_id, BTConnection.is_active == True)
        .order_by(BTConnection.updated_at.desc())
    )
    conn = result.scalars().first()
    if not conn:
        consent_data = await bt_service.create_consent(user_id)
        conn = BTConnection(
            user_id=user_id,
            consent_id=consent_data["consentId"],
            is_sandbox=True,
        )
        db.add(conn)

    conn.access_token = "mock_access_token_123"
    conn.refresh_token = "mock_refresh_token_123"
    conn.token_expires_at = datetime.now(timezone.utc) + timedelta(hours=24)
    # Mark as explicitly chosen demo mode so connect_bank doesn't clear it
    conn.selected_accounts = json.dumps({"_demo_mode": True})
    await db.commit()
    return {"status": "authorized", "message": "Sandbox authorization complete"}


# ── Accounts ──────────────────────────────────────────────────────────────────

@router.get("/accounts", response_model=list[BankAccountResponse])
async def get_accounts(user_id: int = DEFAULT_USER_ID, db: AsyncSession = Depends(get_db)):
    """List BT payment accounts for the user."""
    conn = await _get_connection(user_id, db)
    try:
        data = await bt_service.get_accounts(conn.consent_id, conn.access_token)
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
        data = await bt_service.get_balances(account_id, conn.consent_id, conn.access_token)
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
        q = q.where(BankTransaction.booking_date.cast(String).like(f"{month_year}%"))
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
    account_data = await bt_service.get_accounts(conn.consent_id, conn.access_token)
    accounts = account_data.get("accounts", [])
    if not accounts:
        return 0

    total = 0
    for acc in accounts:
        account_id = acc.get("resourceId", "")
        date_from = date.today() - timedelta(days=120)
        tx_data = await bt_service.get_transactions(
            account_id, conn.consent_id, date_from=date_from, access_token=conn.access_token
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
         .where(BankTransaction.booking_date.cast(String).like(f"{month_year}%")))
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
