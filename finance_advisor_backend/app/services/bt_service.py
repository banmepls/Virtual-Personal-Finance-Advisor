"""
app/services/bt_service.py
───────────────────────────
Banca Transilvania PSD2 AISP integration.

In sandbox mode (USE_BT_SANDBOX=true) all calls return realistic Romanian
mock data — no network calls, no credentials required. Perfect for thesis demo.

For real BT Open Banking:
  1. Register at https://apistorebt.ro/bt/sb/
  2. Obtain client_id / client_secret
  3. Implement OAuth2 redirect flow (user opens a browser/WebView)
  4. BT base URL: https://api.bancatransilvania.ro (production)
     sandbox:     https://apistorebt.ro/bt/sb
"""
import json
import random
import hashlib
from datetime import date, timedelta, datetime, timezone
from typing import Optional
import logging

logger = logging.getLogger(__name__)

# ── Sandbox mock constants ────────────────────────────────────────────────────

_MOCK_ACCOUNTS = [
    {
        "resourceId": "BT-ACC-001",
        "iban": "RO98BTRL0045601205916301",
        "currency": "RON",
        "name": "Cont Curent RON",
        "status": "enabled",
        "bban": "0045601205916301",
        "product": "Cont curent",
    }
]

_MOCK_BALANCE = {
    "account": {"iban": "RO98BTRL0045601205916301"},
    "balances": [
        {"balanceType": "closingBooked", "balanceAmount": {"currency": "RON", "amount": "4823.55"}},
        {"balanceType": "expected", "balanceAmount": {"currency": "RON", "amount": "4823.55"}},
    ],
}

# Romanian merchants per category
_MERCHANT_CATEGORIES = {
    "Food & Groceries": ["Kaufland Romania", "Lidl Romania", "Carrefour", "Auchan", "Mega Image", "Profi"],
    "Transport": ["OMV Petrom", "Rompetrol", "MOL Romania", "Bolt Romania", "Uber Romania"],
    "Utilities": ["Enel Energie", "Digi RCS-RDS", "Orange Romania", "Vodafone Romania", "E.ON Energie"],
    "Dining": ["McDonald's Romania", "KFC Romania", "Pizza Hut Romania", "Starbucks", "Ciao Pizza"],
    "Shopping": ["Dedeman", "Altex", "eMag SRL", "Zara Romania", "H&M Romania"],
    "Health": ["Farmacia Catena", "Dr. Max Pharmacy", "Regina Maria", "Medicover Romania"],
    "Entertainment": ["Netflix Romania", "Spotify Technology", "Cinema City", "Hbo Max Romania"],
    "Subscriptions": ["Spotify Technology", "Netflix Romania", "Adobe Systems", "Microsoft Office"],
    "Rent": ["SC Imobiliare SRL"],
    "Other": ["Transfer Bancar", "ATM Retragere", "Comision Bancar"],
}

# Subscription merchants (always recurring)
_SUBSCRIPTION_MERCHANTS = {"Spotify Technology", "Netflix Romania", "Adobe Systems", "Microsoft Office", "Hbo Max Romania", "Digi RCS-RDS", "Orange Romania", "Vodafone Romania"}

def _generate_mock_transactions(account_id: str, days_back: int = 90) -> list[dict]:
    """Generate realistic Romanian bank transactions for the past N days."""
    random.seed(42)  # deterministic for consistent demo
    transactions = []
    today = date.today()

    # Regular monthly expenses (subscriptions + rent)
    monthly_fixed = [
        ("Spotify Technology", -39.99, "Subscriptions"),
        ("Netflix Romania", -54.99, "Subscriptions"),
        ("Orange Romania", -49.00, "Utilities"),
        ("SC Imobiliare SRL", -2500.00, "Rent"),
        ("Digi RCS-RDS", -17.00, "Utilities"),
    ]

    # Generate daily random spending
    for day_offset in range(days_back):
        tx_date = today - timedelta(days=day_offset)

        # 1st of month: monthly fixed payments
        if tx_date.day == 1:
            for merchant, amount, category in monthly_fixed:
                tx_id = hashlib.md5(f"{merchant}{tx_date}".encode()).hexdigest()[:16]
                transactions.append({
                    "transactionId": f"TXN-{tx_id}",
                    "bookingDate": tx_date.isoformat(),
                    "valueDate": tx_date.isoformat(),
                    "transactionAmount": {"currency": "RON", "amount": str(amount)},
                    "creditorName": merchant,
                    "debtorName": None,
                    "remittanceInformationUnstructured": f"Plata {merchant} {tx_date.strftime('%B %Y')}",
                    "_category": category,
                    "_isRecurring": merchant in _SUBSCRIPTION_MERCHANTS,
                    "_isDebit": True,
                })

        # Random daily transactions (0-4 per day)
        n_txns = random.randint(0, 4)
        category_list = list(_MERCHANT_CATEGORIES.keys())
        weights = [25, 15, 10, 15, 10, 5, 8, 0, 0, 7]  # % probability
        for _ in range(n_txns):
            cat = random.choices(category_list, weights=weights)[0]
            merchant = random.choice(_MERCHANT_CATEGORIES[cat])
            if cat == "Rent":
                continue  # rent only on 1st
            amt = round(random.uniform(10, 400) * (-1), 2)
            if cat == "Subscriptions":
                amt = round(random.choice([-39.99, -54.99, -17.0, -49.0]), 2)
            tx_id = hashlib.md5(f"{merchant}{tx_date}{_}".encode()).hexdigest()[:16]
            transactions.append({
                "transactionId": f"TXN-{tx_id}",
                "bookingDate": tx_date.isoformat(),
                "valueDate": tx_date.isoformat(),
                "transactionAmount": {"currency": "RON", "amount": str(amt)},
                "creditorName": merchant,
                "debtorName": None,
                "remittanceInformationUnstructured": f"POS {merchant} {tx_date.strftime('%d/%m/%Y')}",
                "_category": cat,
                "_isRecurring": merchant in _SUBSCRIPTION_MERCHANTS,
                "_isDebit": amt < 0,
            })

        # Occasional salary income (25th of month)
        if tx_date.day == 25:
            tx_id = hashlib.md5(f"SALARY{tx_date}".encode()).hexdigest()[:16]
            transactions.append({
                "transactionId": f"TXN-{tx_id}",
                "bookingDate": tx_date.isoformat(),
                "valueDate": tx_date.isoformat(),
                "transactionAmount": {"currency": "RON", "amount": "6500.00"},
                "creditorName": None,
                "debtorName": "SC Angajator SRL",
                "remittanceInformationUnstructured": "Salariu net",
                "_category": "Income",
                "_isRecurring": True,
                "_isDebit": False,
            })

    transactions.sort(key=lambda x: x["bookingDate"], reverse=True)
    return transactions


# ── BTService ─────────────────────────────────────────────────────────────────

class BTService:
    """
    Wraps BT PSD2 AISP API calls.
    When use_sandbox=True all methods return mock data without any network calls.
    """

    def __init__(self, use_sandbox: bool = True,
                 client_id: Optional[str] = None,
                 client_secret: Optional[str] = None,
                 base_url: str = "https://apistorebt.ro/bt/sb"):
        self.use_sandbox = use_sandbox
        self.client_id = client_id
        self.client_secret = client_secret
        self.base_url = base_url

    # ── Consent / OAuth2 ─────────────────────────────────────────────────────

    async def create_consent(self, user_id: int) -> dict:
        """Create a PSD2 AIS consent. In sandbox returns a mock consent ID."""
        if self.use_sandbox:
            return {
                "consentId": f"sandbox-consent-{user_id}-2026",
                "consentStatus": "valid",
                "scaRedirect": None,  # No redirect needed in sandbox
                "_sandbox": True,
            }
        # Real implementation: POST /v2/consents with Bearer token
        raise NotImplementedError("Real BT OAuth2 not yet configured. Set USE_BT_SANDBOX=true.")

    async def get_accounts(self, consent_id: str, access_token: Optional[str] = None) -> dict:
        """List available payment accounts."""
        if self.use_sandbox:
            return {"accounts": _MOCK_ACCOUNTS}
        raise NotImplementedError("Real BT OAuth2 not yet configured.")

    async def get_balances(self, account_id: str, consent_id: str,
                           access_token: Optional[str] = None) -> dict:
        """Get account balances."""
        if self.use_sandbox:
            return _MOCK_BALANCE
        raise NotImplementedError("Real BT OAuth2 not yet configured.")

    async def get_transactions(self, account_id: str, consent_id: str,
                               date_from: Optional[date] = None,
                               date_to: Optional[date] = None,
                               access_token: Optional[str] = None) -> dict:
        """Get account transaction history."""
        if self.use_sandbox:
            txns = _generate_mock_transactions(account_id, days_back=90)
            # Filter by date range if provided
            if date_from:
                txns = [t for t in txns if t["bookingDate"] >= date_from.isoformat()]
            if date_to:
                txns = [t for t in txns if t["bookingDate"] <= date_to.isoformat()]
            return {
                "transactions": {
                    "booked": txns,
                    "pending": [],
                }
            }
        raise NotImplementedError("Real BT OAuth2 not yet configured.")

    # ── Factory ───────────────────────────────────────────────────────────────

    @classmethod
    def from_settings(cls) -> "BTService":
        try:
            from app.core.config import get_settings
            s = get_settings()
            use_sandbox = getattr(s, "use_bt_sandbox", True)
            client_id = getattr(s, "bt_client_id", None)
            client_secret = getattr(s, "bt_client_secret", None)
            base_url = getattr(s, "bt_base_url", "https://apistorebt.ro/bt/sb")
            return cls(use_sandbox=use_sandbox, client_id=client_id,
                       client_secret=client_secret, base_url=base_url)
        except Exception:
            return cls(use_sandbox=True)


# Singleton
bt_service = BTService.from_settings()
