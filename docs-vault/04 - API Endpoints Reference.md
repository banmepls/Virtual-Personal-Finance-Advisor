# 🔌 API Endpoints Reference

Tags: #api #endpoints #rest

## Base URL
- **Development:** `http://localhost:8000/api/v1`
- **Docker:** `http://localhost:8001/api/v1`
- **Swagger UI:** `/docs`

---

## Authentication (`/api/v1/auth`)

| Method | Path | Description | Auth Required |
|---|---|---|---|
| `POST` | `/auth/register` | Register new user + init BT consent | ❌ |
| `POST` | `/auth/login` | Login → JWT access token | ❌ |

### `POST /auth/register`
**Request:**
```json
{
  "username": "john_doe",
  "email": "john@example.com",
  "password": "securepassword",
  "etoro_nickname": "optional_etoro_nick"
}
```
**Response (201):**
```json
{
  "user": { "id": 1, "username": "john_doe", "email": "...", "is_active": true, "created_at": "..." },
  "bt_consent_id": "abc-123",
  "bt_message": "BT Sandbox connected."
}
```

### `POST /auth/login`
**Request:**
```json
{ "username": "john_doe", "password": "securepassword" }
```
**Response (200):**
```json
{ "access_token": "eyJ...", "token_type": "bearer" }
```

---

## Bank / BT PSD2 (`/api/v1/bank`)

| Method | Path | Description |
|---|---|---|
| `POST` | `/bank/connect` | Create PSD2 consent + get BT auth URL |
| `POST` | `/bank/disconnect` | Clear BT connection (re-authorize from scratch) |
| `POST` | `/bank/sandbox-authorize` | Demo mode — store mock token instantly |
| `POST` | `/bank/sandbox-auto-connect` | Programmatic sandbox OAuth (no browser) |
| `GET` | `/bank/sandbox-login` | Simulated BT Keycloak login page (HTML) |
| `GET` | `/bank/oauth2/callback` | OAuth2 redirect handler |
| `GET` | `/bank/accounts` | List BT payment accounts |
| `GET` | `/bank/balances/{account_id}` | Account balance details |
| `GET` | `/bank/transactions` | Cached transactions (filter: `month_year`, `account_id`, `limit`) |
| `POST` | `/bank/sync` | Force re-sync from BT API |
| `GET` | `/bank/spending-summary` | Monthly spending by category |
| `GET` | `/bank/subscriptions` | Auto-detected recurring charges |

### `POST /bank/connect` Response
```json
{
  "consent_id": "consent-123",
  "is_sandbox": true,
  "message": "🔗 BT consent created. Please complete the OAuth2 authorization.",
  "auth_url": "https://btkeycloak.ro/authorize?..."
}
```

---

## Budget Manager (`/api/v1/budget`)

| Method | Path | Description |
|---|---|---|
| `GET` | `/budget/` | List budgets (filter: `month_year`) |
| `POST` | `/budget/` | Create a budget |
| `DELETE` | `/budget/{id}` | Delete a budget |
| `GET` | `/budget/status` | Budget status with spending vs. limits |

### `GET /budget/status` Response Item
```json
{
  "budget_id": 7,        // used by the app for swipe-to-delete
  "category": "Food & Groceries",
  "limit_amount": 800.0,
  "spent_amount": 650.0,
  "remaining": 150.0,
  "percentage_used": 81.25,
  "currency": "RON",
  "status": "warning"    // "ok" | "warning" | "exceeded"
}
```

> `DELETE /budget/{id}` is wired into the UI: each budget card is swipe-to-delete (uses `budget_id`).
> `GET /bank/oauth2/callback` auto-redirects the browser back to `bt_frontend_redirect_uri` on success.

---

## Expense Analytics (`/api/v1/expenses`)

| Method | Path | Description |
|---|---|---|
| `GET` | `/expenses/insights` | AI-generated spending summary (Gemini) |
| `GET` | `/expenses/categories` | Spending totals by category |

---

## Anomaly Detection (`/api/v1/anomaly`)

| Method | Path | Description |
|---|---|---|
| `POST` | `/anomaly/analyze` | Run ML ensemble on portfolio snapshot |
| `GET` | `/anomaly/history/{user_id}` | Retrieve anomaly history |

### `POST /anomaly/analyze` Request
```json
{
  "positions": [
    {
      "instrument_id": 1234,
      "quantity": 10.0,
      "avg_buy_price": 150.0,
      "current_value": 1600.0,
      "unrealized_pnl": 100.0
    }
  ],
  "user_id": 1
}
```

### `POST /anomaly/analyze` Response
```json
{
  "isolation_score": 0.23,
  "autoencoder_mse": 0.41,
  "svm_score": 0.18,
  "weighted_avg_score": 0.306,
  "is_anomaly": false,
  "confidence": "LOW",
  "notes": "Weighted score: 0.306 | IF=0.230 AE=0.410 SVM=0.180 | Models agreed: 0/3 | Confidence: LOW"
}
```

---

## AI Agent — Tori (`/api/v1/agent`)

| Method | Path | Description |
|---|---|---|
| `POST` | `/agent/chat` | Send message to Tori |
| `GET` | `/agent/history/{user_id}` | Conversation history |

### `POST /agent/chat` Request
```json
{ "user_id": 1, "message": "How much did I spend on groceries this month?" }
```

---

## Market Data (`/api/v1/market`)

| Method | Path | Description |
|---|---|---|
| `GET` | `/market/quote/{symbol}` | Real-time stock quote (Alpha Vantage) |
| `GET` | `/market/history/{symbol}` | OHLCV history |

---

## Health (`/api/v1/health`)

| Method | Path | Description |
|---|---|---|
| `GET` | `/health` | Full system health status |

### `GET /health` Response
```json
{
  "status": "healthy",
  "circuit_breakers": [
    { "name": "etoro", "state": "CLOSED", "failure_count": 0, "last_failure_time": 0.0 },
    { "name": "alpha_vantage", "state": "CLOSED", "failure_count": 0, "last_failure_time": 0.0 }
  ],
  "cache_stats": { "size": 12, "capacity": 256, "db_connected": true },
  "alpha_vantage_quota": { "daily_limit": 25, "remaining": 23, "exceeded": false },
  "timestamp": "2026-06-07T13:00:00Z"
}
```

---

## eToro (`/api/v1/etoro`)

| Method | Path | Description |
|---|---|---|
| `GET` | `/etoro/portfolio` | Live portfolio from eToro |
| `GET` | `/etoro/instruments` | All known eToro instruments |

---

## Related Notes
- [[03 - FastAPI Application]]
- [[09 - BT PSD2 Bank Integration]]
- [[08 - ML Anomaly Detection]]
- [[06 - Tori Agent]]
