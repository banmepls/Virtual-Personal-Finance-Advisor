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

# ── Sandbox mock constants (from BT accounts-sandbox Swagger documentation) ───

_AISP_V2 = "https://apistorebt.ro/bt/sb/bt-psd2-aisp/v2"

_MOCK_ACCOUNTS = [
    {
        "resourceId": "K13RONCRT0060214301",
        "iban": "RO98BTRLRONCRT0ABCDEFGHI",
        "currency": "RON",
        "product": "Cont de disponibil",
        "name": "Cont de disponibil",
        "cashAccountType": "CurrentAccount",
        "status": "enabled",
        "_links": {
            "balances":     {"href": f"{_AISP_V2}/accounts/K13RONCRT0060214301/balances"},
            "transactions": {"href": f"{_AISP_V2}/accounts/K13RONCRT0060214301/transactions"},
        },
    },
    {
        "resourceId": "K13EURCRT0060214301",
        "iban": "RO98BTRLEURCRT0ABCDEFGHI",
        "currency": "EUR",
        "product": "Cont de disponibil",
        "name": "Cont de disponibil",
        "cashAccountType": "CurrentAccount",
        "status": "enabled",
        "_links": {
            "balances":     {"href": f"{_AISP_V2}/accounts/K13EURCRT0060214301/balances"},
            "transactions": {"href": f"{_AISP_V2}/accounts/K13EURCRT0060214301/transactions"},
        },
    },
]

_MOCK_BALANCES: dict[str, dict] = {
    "K13RONCRT0060214301": {
        "account": {"iban": "RO98BTRLRONCRT0ABCDEFGHI"},
        "balances": [
            {
                "balanceType": "closingBooked",
                "creditLimitIncluded": False,
                "balanceAmount": {"currency": "RON", "amount": "4823.55"},
                "referenceDate": "2026-06-07",
            },
            {
                "balanceType": "expected",
                "creditLimitIncluded": False,
                "balanceAmount": {"currency": "RON", "amount": "4823.55"},
                "referenceDate": "2026-06-07",
            },
        ],
    },
    "K13EURCRT0060214301": {
        "account": {"iban": "RO98BTRLEURCRT0ABCDEFGHI"},
        "balances": [
            {
                "balanceType": "closingBooked",
                "creditLimitIncluded": False,
                "balanceAmount": {"currency": "EUR", "amount": "1250.00"},
                "referenceDate": "2026-06-07",
            },
            {
                "balanceType": "expected",
                "creditLimitIncluded": False,
                "balanceAmount": {"currency": "EUR", "amount": "1250.00"},
                "referenceDate": "2026-06-07",
            },
        ],
    },
}

# Legacy alias used by get_balances fallback for unknown account IDs
_MOCK_BALANCE = _MOCK_BALANCES["K13RONCRT0060214301"]

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

def _btc(is_debit: bool, category: str) -> str:
    """Berlin Group bankTransactionCode (domain-family-subfamily)."""
    if not is_debit:
        return "PMNT-RCDT-ESCT"   # received credit transfer
    if category == "Subscriptions":
        return "PMNT-DBIT-SDCO"   # SEPA direct debit
    if category in ("Utilities", "Rent"):
        return "PMNT-DBIT-ESCT"   # issued SEPA credit transfer
    return "PMNT-CCRD-POSD"       # card payment at POS


_EUR_MERCHANTS = [
    ("Amazon EU", -89.99, "Shopping", "PMNT-CCRD-POSD"),
    ("Booking.com", -350.00, "Travel", "PMNT-DBIT-ESCT"),
    ("Airbnb Ireland", -180.00, "Travel", "PMNT-DBIT-ESCT"),
    ("Apple Store", -12.99, "Subscriptions", "PMNT-DBIT-SDCO"),
    ("Netflix International", -13.99, "Subscriptions", "PMNT-DBIT-SDCO"),
    ("Steam Games", -29.99, "Entertainment", "PMNT-CCRD-POSD"),
    ("PayPal Europe", -45.00, "Shopping", "PMNT-CCRD-POSD"),
    ("Skyscanner", -210.00, "Travel", "PMNT-DBIT-ESCT"),
]


def _generate_mock_transactions_eur(account_id: str, days_back: int = 120) -> list[dict]:
    """Generate EUR-denominated international transactions for the EUR account."""
    random.seed(77)
    transactions = []
    today = date.today()
    account_href = f"{_AISP_V2}/accounts/{account_id}"

    # Bi-weekly salary wire from abroad (if applicable) — once a month
    for day_offset in range(days_back):
        tx_date = today - timedelta(days=day_offset)
        if tx_date.day in (1, 15) and random.random() < 0.4:
            merchant, amount, category, btc = random.choice(_EUR_MERCHANTS)
            tx_id = hashlib.md5(f"{account_id}{merchant}{tx_date}".encode()).hexdigest()[:16]
            transactions.append({
                "transactionId": f"TXN-{tx_id}",
                "bookingDate": tx_date.isoformat(),
                "valueDate": tx_date.isoformat(),
                "transactionAmount": {"currency": "EUR", "amount": str(amount)},
                "creditorName": merchant,
                "debtorName": None,
                "remittanceInformationUnstructured": f"Payment to {merchant}",
                "endToEndId": f"E2E-{tx_id[:8]}",
                "mandateId": None,
                "bankTransactionCode": btc,
                "proprietaryBankTransactionCode": None,
                "_links": {"account": {"href": account_href}},
                "_category": category,
                "_isRecurring": category == "Subscriptions",
                "_isDebit": True,
            })

    transactions.sort(key=lambda x: x["bookingDate"], reverse=True)
    return transactions


def _generate_mock_transactions(account_id: str, days_back: int = 120) -> list[dict]:
    """Generate realistic Romanian bank transactions for the past N days.

    For EUR accounts, generates EUR international transactions.
    Fields match the BT accounts-sandbox Swagger documentation response schema.
    """
    if "EUR" in account_id.upper():
        return _generate_mock_transactions_eur(account_id, days_back)

    random.seed(42)  # deterministic for consistent demo
    transactions = []
    today = date.today()

    account_href = f"{_AISP_V2}/accounts/{account_id}"

    # Regular monthly expenses (subscriptions + rent)
    monthly_fixed = [
        ("Spotify Technology", -39.99, "Subscriptions"),
        ("Netflix Romania", -54.99, "Subscriptions"),
        ("Orange Romania", -49.00, "Utilities"),
        ("SC Imobiliare SRL", -2500.00, "Rent"),
        ("Digi RCS-RDS", -17.00, "Utilities"),
    ]

    for day_offset in range(days_back):
        tx_date = today - timedelta(days=day_offset)

        # 1st of month: monthly fixed payments
        if tx_date.day == 1:
            for merchant, amount, category in monthly_fixed:
                tx_id = hashlib.md5(f"{account_id}{merchant}{tx_date}".encode()).hexdigest()[:16]
                transactions.append({
                    "transactionId": f"TXN-{tx_id}",
                    "bookingDate": tx_date.isoformat(),
                    "valueDate": tx_date.isoformat(),
                    "transactionAmount": {"currency": "RON", "amount": str(amount)},
                    "creditorName": merchant,
                    "debtorName": None,
                    "remittanceInformationUnstructured": f"Plata {merchant} {tx_date.strftime('%B %Y')}",
                    "endToEndId": f"E2E-{tx_id[:8]}",
                    "mandateId": tx_id[:8] if merchant in _SUBSCRIPTION_MERCHANTS else None,
                    "bankTransactionCode": _btc(True, category),
                    "proprietaryBankTransactionCode": None,
                    "_links": {"account": {"href": account_href}},
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
            tx_id = hashlib.md5(f"{account_id}{merchant}{tx_date}{_}".encode()).hexdigest()[:16]
            transactions.append({
                "transactionId": f"TXN-{tx_id}",
                "bookingDate": tx_date.isoformat(),
                "valueDate": tx_date.isoformat(),
                "transactionAmount": {"currency": "RON", "amount": str(amt)},
                "creditorName": merchant,
                "debtorName": None,
                "remittanceInformationUnstructured": f"POS {merchant} {tx_date.strftime('%d/%m/%Y')}",
                "endToEndId": f"E2E-{tx_id[:8]}",
                "mandateId": None,
                "bankTransactionCode": _btc(True, cat),
                "proprietaryBankTransactionCode": None,
                "_links": {"account": {"href": account_href}},
                "_category": cat,
                "_isRecurring": merchant in _SUBSCRIPTION_MERCHANTS,
                "_isDebit": amt < 0,
            })

        # Salary income (25th of month)
        if tx_date.day == 25:
            tx_id = hashlib.md5(f"{account_id}SALARY{tx_date}".encode()).hexdigest()[:16]
            transactions.append({
                "transactionId": f"TXN-{tx_id}",
                "bookingDate": tx_date.isoformat(),
                "valueDate": tx_date.isoformat(),
                "transactionAmount": {"currency": "RON", "amount": "6500.00"},
                "creditorName": None,
                "debtorName": "SC Angajator SRL",
                "remittanceInformationUnstructured": "Salariu net",
                "endToEndId": f"SAL-{tx_id[:8]}",
                "mandateId": None,
                "bankTransactionCode": _btc(False, "Income"),
                "proprietaryBankTransactionCode": None,
                "_links": {"account": {"href": account_href}},
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

    async def sandbox_auto_authorize(self) -> dict:
        """
        Programmatically complete the BT sandbox OAuth2 flow without any browser interaction.

        BT's /sandbox-backend-consent/accounts endpoint returns HTTP 500 for every
        arbitrary username, so the Angular consent UI always lands on an error page.
        This method bypasses that broken step by calling AISPConsentUpdate directly
        (empty account selection is accepted), then drives Keycloak to completion.

        Returns a dict with access_token, refresh_token, expires_in, consent_id.
        """
        import secrets as _s
        import hashlib as _h
        import base64 as _b64
        import re as _re
        import time as _time
        from urllib.parse import urlencode as _urlencode, urlparse as _urlparse, parse_qs as _parse_qs, quote as _quote

        # ── Step 1: Create consent ───────────────────────────────────────────
        consent_url = f"{self._aisp}/consents"
        code_verifier = _s.token_urlsafe(64)
        code_challenge = _b64.urlsafe_b64encode(
            _h.sha256(code_verifier.encode()).digest()
        ).rstrip(b"=").decode()
        state = _s.token_urlsafe(16)

        consent_body = {
            "access": {"availableAccounts": "allAccounts"},
            "recurringIndicator": True,
            "validUntil": (date.today() + timedelta(days=89)).isoformat(),
            "frequencyPerDay": 4,
            "combinedServiceIndicator": False,
        }
        async with httpx.AsyncClient(timeout=20.0) as client:
            r = await client.post(consent_url, json=consent_body, headers={
                "X-Request-ID": str(uuid.uuid4()),
                "PSU-IP-Address": "127.0.0.1",
                "Content-Type": "application/json",
            })
            r.raise_for_status()
        consent_id = r.json()["consentId"]

        # ── Step 2: Hit Keycloak to establish a session ──────────────────────
        auth_params = {
            "response_type": "code",
            "client_id": self.client_id,
            "redirect_uri": self.redirect_uri,
            "scope": f"AIS:{consent_id}",
            "state": state,
            "code_challenge": code_challenge,
            "code_challenge_method": "S256",
        }
        keycloak_auth_url = f"{self._AUTH_ENDPOINT}?{_urlencode(auth_params)}"

        async with httpx.AsyncClient(timeout=20.0, follow_redirects=False) as client:
            kc_resp = await client.get(keycloak_auth_url)
            kc_cookies = dict(kc_resp.cookies)

        # Extract sandbox-login redirect params from Keycloak HTML
        m = _re.search(
            r"url=(https://apistorebt\.ro/sandbox-login/\?[^\"<]+)", kc_resp.text
        )
        if not m:
            raise ValueError("Could not parse Keycloak sandbox-login redirect URL")
        sandbox_url = m.group(1).replace("&amp;", "&")
        sp = _parse_qs(_urlparse(sandbox_url).query)
        session_code = sp["session_code"][0]
        execution    = sp["execution"][0]
        scope_val    = sp["scope"][0]
        tab_id       = sp.get("tab_id", [""])[0]
        client_data  = sp.get("client_data", [""])[0]
        client_name  = sp.get("client_name", ["Virtual Finance Advisor"])[0]
        redirect_uri_param = sp.get("redirect_uri", [self.redirect_uri])[0]

        ts         = int(_time.time() * 1000)
        session_id = f"{session_code}{ts}"

        sb_headers = {
            "Accept": "*/*",
            "Content-Type": "application/json",
            "Auth-Type": "NeoBT",
            "Interaction-ID": execution,
            "Request-ID":     execution,
            "Session-ID":     execution,
            "session_code":   session_id,
            "scope":          scope_val,
            "token":          "",
            "bt24SessionId":  session_id,
        }

        # ── Step 3: Sandbox login (any credentials) ──────────────────────────
        login_resp = await self._sb_post(
            "https://apistorebt.ro/sandbox-backend-authentication/authentication",
            {"username": "psd2testuser", "password": "psd2testpass"},
            sb_headers,
        )
        payload      = login_resp["payload"]
        type_id      = payload["accessCodeTypeId"]
        token_id     = payload["tokenId"]
        user_profiles = payload["userProfiles"]

        # ── Step 4: Sandbox OTP (any 7-digit code) ───────────────────────────
        otp_resp = await self._sb_post(
            "https://apistorebt.ro/sandbox-backend-authentication/two-factor-authentication",
            {
                "username":        "psd2testuser",
                "accessCodeTypeId": type_id,
                "password":        "1234567",
                "userProfiles":    user_profiles,
                "codeHead":        int(token_id),
            },
            sb_headers,
        )
        jwt_token = otp_resp["token"]

        # Decode the JWT payload (base64url, no verification needed) to extract
        # the real customer number the sandbox assigned to this session.
        import json as _json_mod
        _jwt_parts = jwt_token.split(".")
        if len(_jwt_parts) >= 2:
            _padded = _jwt_parts[1] + "=" * (4 - len(_jwt_parts[1]) % 4)
            try:
                _jwt_payload = _json_mod.loads(_b64.urlsafe_b64decode(_padded))
            except Exception:
                _jwt_payload = {}
        else:
            _jwt_payload = {}
        logger.info(f"[sandbox] JWT payload: {_jwt_payload}")

        # Use BT-specific PSU fields; sub is a Keycloak UUID and must NOT be used
        customer_no = (
            _jwt_payload.get("psu-customer-no")
            or _jwt_payload.get("psu-id")
            or _jwt_payload.get("customerNo")
            or "psd2testuser"
        )
        logger.info(f"[sandbox] Using customer_no={customer_no!r}")

        sb_headers_jwt = {**sb_headers, "token": jwt_token, "username": customer_no}

        # ── Step 5: Consent details (required to build updateBody) ───────────
        details_resp = await self._sb_post(
            "https://apistorebt.ro/sandbox-backend-consent/consent/details",
            {"consentId": consent_id},
            sb_headers_jwt,
        )
        details_payload = details_resp["payload"]
        logger.info(f"[sandbox] consent/details payload keys: {list(details_payload.keys())}")
        logger.info(f"[sandbox] consent/details accounts field: {details_payload.get('accounts')}")

        # ── Step 6: Consent update ───────────────────────────────────────────
        # AISPGetAccounts returns HTTP 500 for all sandbox users — no IBANs are
        # provisioned, so we send empty arrays. BT accepts this and marks the
        # consent valid; the resulting JWT has accounts_count: 0 (BT sandbox bug).
        update_body = {
            "consentId":        consent_id,
            "validUntil":       details_payload["validUntil"],
            "consentStatus":    "valid",
            "customerNo":       customer_no,
            "clientId":         self.client_id,
            "transactionScope": "AIS",
            "username":         customer_no,
            "accounts":         {"details": [], "balances": [], "transactions": []},
        }
        update_resp = await self._sb_post(
            "https://apistorebt.ro/sandbox-backend-consent/consent/update",
            update_body,
            sb_headers_jwt,
        )
        logger.info(f"[sandbox] consent/update payload keys: {list(update_resp.get('payload', {}).keys())}")
        access_token_claims = update_resp["payload"]["access_token"]

        # ── Step 7: Keycloak authenticate → get auth code ────────────────────
        kc_params_parts = [
            f"session_code={_quote(session_code, safe='')}",
            f"execution={_quote(execution, safe='')}",
            f"client_id={_quote(self.client_id, safe='')}",
            f"tab_id={_quote(tab_id, safe='')}",
            f"client_data={_quote(client_data, safe='')}",
            f"client_name={_quote(client_name, safe='')}",
            f"scope={_quote(scope_val, safe='')}",
            f"redirect_uri={_quote(redirect_uri_param, safe='')}",
            "response_type=code",
            f"state={_quote(state, safe='')}",
            f"code_challenge={_quote(code_challenge, safe='')}",
            "code_challenge_method=S256",
            f"claims={_quote(access_token_claims, safe='')}",
        ]
        kc_final_url = (
            "https://apistorebt.ro/auth/realms/psd2-sb/login-actions/authenticate?"
            + "&".join(kc_params_parts)
        )

        async with httpx.AsyncClient(
            timeout=20.0, follow_redirects=False, cookies=kc_cookies
        ) as client:
            kc_final = await client.get(kc_final_url)

        location = kc_final.headers.get("location", "")
        code_match = _re.search(r"[?&]code=([^&]+)", location)
        if not code_match:
            raise ValueError(
                f"Keycloak did not issue auth code. Status={kc_final.status_code}, "
                f"Location={location[:200]}"
            )
        auth_code = code_match.group(1)

        # ── Step 8: Exchange auth code for token ──────────────────────────────
        token_data = await self.exchange_token(auth_code, code_verifier=code_verifier)
        return {
            **token_data,
            "consent_id": consent_id,
        }

    async def _sb_post(self, url: str, body: dict, headers: dict) -> dict:
        """Helper: POST to a BT sandbox-backend endpoint, raise on error."""
        async with httpx.AsyncClient(timeout=20.0) as client:
            resp = await client.post(url, json=body, headers=headers)
            if not resp.is_success:
                raise ValueError(
                    f"Sandbox {url.split('/')[-1]} failed: "
                    f"HTTP {resp.status_code} — {resp.text[:400]}"
                )
            data = resp.json()
            if isinstance(data, dict) and data.get("payload", {}) == "Unauthorized":
                raise ValueError(f"Sandbox {url.split('/')[-1]} returned Unauthorized")
            return data

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
        """List available payment accounts via BT NextGenPSD2 v2.

        Falls back to the documentation example accounts when the BT API is
        unavailable (including the sandbox accounts_count:0 case).
        """
        if not access_token:
            return {"accounts": _MOCK_ACCOUNTS}

        url = f"{self._aisp}/accounts"
        headers = self._get_headers(access_token, consent_id)
        headers["PSU-IP-Address"] = "127.0.0.1"

        async with httpx.AsyncClient(timeout=15.0) as client:
            try:
                response = await client.get(url, headers=headers)
                response.raise_for_status()
                data = response.json()
                # If BT returns an empty list (sandbox accounts_count:0), fall back.
                if not data.get("accounts"):
                    logger.info("BT accounts empty — using documentation example accounts")
                    return {"accounts": _MOCK_ACCOUNTS}
                return data
            except httpx.HTTPError as e:
                logger.warning(f"BT accounts failed ({e}) — using documentation example accounts")
                return {"accounts": _MOCK_ACCOUNTS}

    async def get_balances(self, account_id: str, consent_id: str,
                           access_token: Optional[str] = None) -> dict:
        """Get account balances via BT NextGenPSD2 v2.

        Falls back to the documentation example balance for the given account.
        """
        fallback = _MOCK_BALANCES.get(account_id, _MOCK_BALANCE)

        if not access_token:
            return fallback

        url = f"{self._aisp}/accounts/{account_id}/balances"
        headers = self._get_headers(access_token, consent_id)
        headers["PSU-IP-Address"] = "127.0.0.1"

        async with httpx.AsyncClient(timeout=15.0) as client:
            try:
                response = await client.get(url, headers=headers)
                response.raise_for_status()
                return response.json()
            except httpx.HTTPError:
                return fallback

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
            "bookingStatus": "booked",
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
