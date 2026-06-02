"""
app/services/bt_service.py
───────────────────────────
Banca Transilvania PSD2 AISP integration.

OAuth2 flow (Sandbox):
  Step 1 – Consent    : POST /bt-psd2-aisp/v2/consents  (no auth header needed in sandbox)
                        → consentId; we build the Keycloak auth URL manually with PKCE
  Step 2 – User auth  : User opens Keycloak URL in browser
                        → BT calls back /oauth2/callback?code=...
  Step 3 – User token : POST /oauth/token  (authorization_code + PKCE verifier)
                        → access_token stored in BTConnection

If credentials are missing or the API errors, all calls fall back to locally
generated mock data so the thesis demo always works.
"""
import random
import hashlib
from datetime import date, timedelta
from typing import Optional
import logging
import httpx
import uuid

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

def _generate_mock_transactions(account_id: str, days_back: int = 120) -> list[dict]:
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
    Wraps BT PSD2 AISP API calls for the BT Sandbox.
    """

    # BT NextGenPSD2 AISP API base (v2)
    _AISP_PATH = "/bt-psd2-aisp/v2"
    # Keycloak authorization endpoint (from .well-known)
    _AUTH_ENDPOINT = "https://apistorebt.ro/auth/realms/psd2-sb/protocol/openid-connect/auth"

    def __init__(self, use_sandbox: bool = True,
                 client_id: Optional[str] = None,
                 client_secret: Optional[str] = None,
                 base_url: str = "https://api.apistorebt.ro/bt/sb"):
        self.use_sandbox = use_sandbox
        self.client_id = client_id
        self.client_secret = client_secret
        self.base_url = base_url.rstrip('/')
        self.redirect_uri = "http://localhost:8001/api/v1/bank/oauth2/callback"

    @property
    def _aisp(self) -> str:
        return f"{self.base_url}{self._AISP_PATH}"

    def _get_headers(self, access_token: Optional[str] = None, consent_id: Optional[str] = None) -> dict:
        headers = {
            "X-Request-ID": str(uuid.uuid4()),
            "Content-Type": "application/json",
            "Accept": "application/json",
        }
        if access_token:
            headers["Authorization"] = f"Bearer {access_token}"
        if consent_id:
            headers["Consent-ID"] = consent_id
        return headers

    async def create_consent(self, user_id: int) -> dict:
        """Create a PSD2 AIS consent and get authorization URL.

        If real credentials are configured, calls the BT API and returns the
        real scaRedirect URL so the user can log in via BT's sandbox portal.
        Falls back to a local mock page when no credentials are set.
        """
        _placeholder_ids = {"sandbox_client_id", "", None}
        if self.client_id not in _placeholder_ids and self.client_secret not in _placeholder_ids:
            try:
                result = await self._try_real_consent(user_id)
                if result:
                    return result
            except Exception as e:
                logger.warning(f"Real BT consent failed ({e}), falling back to local mock")

        # Local mock fallback — works without any BT credentials
        from urllib.parse import urlencode
        state = f"user_{user_id}_{uuid.uuid4().hex[:8]}"
        sandbox_login_url = self.redirect_uri.replace("/oauth2/callback", "/sandbox-login")
        params = {"client_id": self.client_id, "redirect_uri": self.redirect_uri, "state": state}
        return {
            "consentId": f"consent-{state}",
            "consentStatus": "awaitingAuthorization",
            "scaRedirect": f"{sandbox_login_url}?{urlencode(params)}",
            "_sandbox": True,
        }

    async def _try_real_consent(self, user_id: int) -> Optional[dict]:
        """Call the real BT NextGenPSD2 v2 API to create an AIS consent.

        BT does NOT return a scaRedirect link — we build the Keycloak auth URL
        ourselves using the consentId as the AIS scope, with PKCE.
        Returns a dict that includes the generated auth URL and the PKCE
        code_verifier so the caller can persist it for the token exchange.
        """
        import secrets as _secrets
        import hashlib as _hashlib
        import base64 as _base64
        from urllib.parse import urlencode as _urlencode

        # PKCE
        code_verifier  = _secrets.token_urlsafe(64)
        digest         = _hashlib.sha256(code_verifier.encode()).digest()
        code_challenge = _base64.urlsafe_b64encode(digest).rstrip(b"=").decode()
        state          = _secrets.token_urlsafe(32)
        nonce          = _secrets.token_urlsafe(32)

        # POST /bt-psd2-aisp/v2/consents  (no Authorization header — BT sandbox accepts without one)
        url = f"{self._aisp}/consents"
        body = {
            "access": {"availableAccounts": "allAccounts"},
            "recurringIndicator": True,
            "validUntil": (date.today() + timedelta(days=179)).isoformat(),
            "frequencyPerDay": 4,
            "combinedServiceIndicator": False,
        }
        headers = {
            "X-Request-ID": str(uuid.uuid4()),
            "PSU-IP-Address": "127.0.0.1",
            "Content-Type": "application/json",
            "Accept": "application/json",
        }

        async with httpx.AsyncClient(timeout=15.0) as client:
            resp = await client.post(url, json=body, headers=headers)
            resp.raise_for_status()
            data = resp.json()

        consent_id = data.get("consentId")
        if not consent_id:
            logger.warning(f"No consentId in BT consent response: {data}")
            return None

        # Build Keycloak auth URL with PKCE
        params = {
            "client_id":             self.client_id,
            "redirect_uri":          self.redirect_uri,
            "response_type":         "code",
            "scope":                 f"AIS:{consent_id}",
            "state":                 state,
            "nonce":                 nonce,
            "code_challenge":        code_challenge,
            "code_challenge_method": "S256",
        }
        sca_redirect = f"{self._AUTH_ENDPOINT}?{_urlencode(params)}"

        return {
            "consentId":    consent_id,
            "consentStatus": data.get("consentStatus", "received"),
            "scaRedirect":  sca_redirect,
            "_code_verifier": code_verifier,   # caller must persist this
            "_sandbox":     True,
        }

    async def exchange_token(self, code: str, code_verifier: Optional[str] = None) -> dict:
        """Exchange OAuth2 authorization code for access token (with optional PKCE verifier)."""
        url = f"{self.base_url}/oauth/token"
        data = {
            "grant_type":   "authorization_code",
            "code":         code,
            "redirect_uri": self.redirect_uri,
            "client_id":    self.client_id,
            "client_secret": self.client_secret,
        }
        if code_verifier:
            data["code_verifier"] = code_verifier
        async with httpx.AsyncClient(timeout=15.0) as client:
            response = await client.post(url, data=data)
            if not response.is_success:
                raise ValueError(
                    f"BT token exchange failed — HTTP {response.status_code}: {response.text}"
                )
            return response.json()

    async def get_accounts(self, consent_id: str, access_token: Optional[str] = None) -> dict:
        """List available payment accounts via BT NextGenPSD2 v2."""
        if not access_token:
            return {"accounts": []}

        url = f"{self._aisp}/accounts"
        headers = self._get_headers(access_token, consent_id)
        headers["PSU-IP-Address"] = "127.0.0.1"

        async with httpx.AsyncClient(timeout=15.0) as client:
            try:
                response = await client.get(url, headers=headers)
                response.raise_for_status()
                return response.json()
            except httpx.HTTPError as e:
                logger.warning(f"BT accounts failed ({e}), falling back to mock")
                return {"accounts": _MOCK_ACCOUNTS}

    async def get_balances(self, account_id: str, consent_id: str,
                           access_token: Optional[str] = None) -> dict:
        """Get account balances via BT NextGenPSD2 v2."""
        if not access_token:
            return _MOCK_BALANCE

        url = f"{self._aisp}/accounts/{account_id}/balances"
        headers = self._get_headers(access_token, consent_id)
        headers["PSU-IP-Address"] = "127.0.0.1"

        async with httpx.AsyncClient(timeout=15.0) as client:
            try:
                response = await client.get(url, headers=headers)
                response.raise_for_status()
                return response.json()
            except httpx.HTTPError:
                return _MOCK_BALANCE

    async def get_transactions(self, account_id: str, consent_id: str,
                               date_from: Optional[date] = None,
                               date_to: Optional[date] = None,
                               access_token: Optional[str] = None) -> dict:
        """Get account transaction history via BT NextGenPSD2 v2.

        Sandbox notes (from bt_apis.md):
        - 7-day window restriction is removed — up to 120 days in one request.
        - bookingStatus is mandatory.
        - PSU-IP-Address bypasses frequencyPerDay limit entirely.
        - Pagination via limit/page params; follow _links.next.href until exhausted.
        """
        mock_txns = {"transactions": {"booked": _generate_mock_transactions(account_id, days_back=120), "pending": []}}

        if not access_token:
            return mock_txns

        url = f"{self._aisp}/accounts/{account_id}/transactions"
        headers = self._get_headers(access_token, consent_id)
        headers["PSU-IP-Address"] = "127.0.0.1"  # signals user presence → bypasses frequencyPerDay

        start = date_from or (date.today() - timedelta(days=120))
        params: dict = {
            "bookingStatus": "both",
            "dateFrom":      start.isoformat(),
            "limit":         100,
            "page":          1,
        }
        if date_to:
            params["dateTo"] = date_to.isoformat()

        all_booked:  list = []
        all_pending: list = []

        async with httpx.AsyncClient(timeout=20.0) as client:
            while True:
                try:
                    resp = await client.get(url, headers=headers, params=params)
                    resp.raise_for_status()
                    body = resp.json()
                except httpx.HTTPError as e:
                    logger.warning(f"BT transactions failed ({e}), using mock")
                    return mock_txns

                txns = body.get("transactions", {})
                all_booked  += txns.get("booked",  [])
                all_pending += txns.get("pending", [])

                # Follow pagination until no next link
                next_href = body.get("_links", {}).get("next", {}).get("href")
                if not next_href:
                    break
                params["page"] = params["page"] + 1

        return {"transactions": {"booked": all_booked, "pending": all_pending}}

    # ── Factory ───────────────────────────────────────────────────────────────

    @classmethod
    def from_settings(cls) -> "BTService":
        try:
            from app.core.config import get_settings
            s = get_settings()
            use_sandbox = getattr(s, "use_bt_sandbox", True)
            client_id = getattr(s, "bt_client_id", None)
            client_secret = getattr(s, "bt_client_secret", None)
            base_url = getattr(s, "bt_base_url", "https://api.apistorebt.ro/bt/sb")
            
            # Allow redirect_uri to be configured via settings
            svc = cls(use_sandbox=use_sandbox, client_id=client_id,
                       client_secret=client_secret, base_url=base_url)
            redirect_uri = getattr(s, "bt_redirect_uri", None)
            if redirect_uri:
                svc.redirect_uri = redirect_uri
            return svc
        except Exception:
            return cls(use_sandbox=True)


# Singleton
bt_service = BTService.from_settings()
