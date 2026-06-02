# Virtual Personal Finance Advisor

A platform that helps users manage finances by tracking bank transactions, suggesting investments via AI, and detecting portfolio anomalies.

## Features

- **Tori AI Agent** — Personalized financial advice using Model Context Protocol (MCP) with live data access
- **BT Open Banking** — Real transaction sync via Banca Transilvania PSD2 AISP API (NextGenPSD2 / BerlinGroup)
- **ML Anomaly Detection** — Ensemble voting (Isolation Forest, Autoencoder, SVM) for unusual portfolio activity
- **Fault-Tolerant Architecture** — Circuit breakers and 2-tier caching
- **Modern UI** — Dark-themed Flutter dashboard with real-time charts and AI chat

---

## Quick Start (Development)

### Backend

```bash
cd finance_advisor_backend
pip install -r ../requirements.txt
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

API docs: `http://localhost:8000/docs`

### Flutter App

```bash
cd flutter_app
flutter pub get
flutter run -d chrome          # web (no FFI issues)
flutter run -d android         # physical device — set API_BASE_URL below
```

> **Note:** If you see `NativeCallable` FFI crashes on desktop, use `-d chrome` as a workaround (Dart 3.12 / objective_c 9.x issue).

---

## Docker Deployment

### 1. Configure environment

Edit `finance_advisor_backend/.env`:

```env
# Backend Keys
ETORO_API_KEY=your_etoro_api_key
ETORO_USER_KEY=your_etoro_user_key
ETORO_BASE_URL=https://api.etoro.com
ETORO_ENV=demo
ETORO_USERNAME=your_username
ALPHA_VANTAGE_API_KEY=your_alpha_vantage_key
SECRET_KEY=your_generated_secret_key   # python -c "import secrets; print(secrets.token_hex(32))"
GOOGLE_API_KEY=your_gemini_api_key

# Database
POSTGRES_USER=postgres
POSTGRES_PASSWORD=password
POSTGRES_DB=finance_advisor

# Mock Data
USE_MOCK_DATA=true

# Frontend (used for Flutter web build arg)
API_BASE_URL=http://localhost:8001/api/v1

# Banca Transilvania Open Banking — see section below
BT_CLIENT_ID=your_bt_client_id
BT_CLIENT_SECRET=your_bt_client_secret
BT_REDIRECT_URI=https://your-ngrok-url.ngrok-free.app/api/v1/bank/oauth2/callback
USE_BT_SANDBOX=true
```

> `finance_advisor_backend/.env` is loaded by Docker Compose at runtime via `env_file`. You never need to rebuild the image when changing credentials — only `docker-compose up -d backend`.

### 2. Deploy

```bash
docker-compose up --build -d
```

| Service  | URL |
|---|---|
| Backend API | `http://localhost:8001` |
| Swagger UI | `http://localhost:8001/docs` |
| Flutter Web | `http://localhost` |

---

## Banca Transilvania Open Banking (PSD2 Sandbox)

The app integrates with the [BT API Store](https://apistorebt.ro) sandbox using the NextGenPSD2 BerlinGroup AISP API v2 with OAuth2 PKCE.

### How it works

1. The app calls `POST /api/v1/bank/connect` → backend creates a PSD2 consent and builds a BT Keycloak authorization URL
2. Flutter opens that URL in the phone/browser
3. User authenticates on BT's page → BT redirects back to `BT_REDIRECT_URI` with an authorization code
4. Backend exchanges the code (+ PKCE verifier) for an access token → real account data loads

If no real credentials are configured, the app falls back to locally-generated demo data automatically.

### Initial setup

BT requires HTTPS for the OAuth redirect URI. Use [ngrok](https://ngrok.com) to tunnel your local backend:

```bash
ngrok http 8001
# Outputs something like: https://xxxx-xx-xx-xx-xx.ngrok-free.app
```

Register your application with that URL:

```bash
curl -X POST https://api.apistorebt.ro/bt/sb/oauth/register \
  -H "Content-Type: application/json" \
  -d '{
    "redirect_uris": ["https://xxxx-xx-xx-xx-xx.ngrok-free.app/api/v1/bank/oauth2/callback"],
    "client_name": "Virtual Finance Advisor"
  }'
```

Copy the returned `client_id` and `client_secret` into `finance_advisor_backend/.env`:

```env
BT_CLIENT_ID=<returned client_id>
BT_CLIENT_SECRET=<returned client_secret>
BT_REDIRECT_URI=https://xxxx-xx-xx-xx-xx.ngrok-free.app/api/v1/bank/oauth2/callback
```

Apply without rebuilding:

```bash
docker-compose up -d backend
```

### When ngrok restarts (URL changes)

The registered `redirect_uri` for a BT client is fixed at registration time. Every time ngrok gives you a new URL you must register a new client — reusing the old `client_id` with a new redirect URI will cause BT Keycloak to show **"A intervenit o eroare. Va rugam sa reincercati."**

```bash
# 1. Start ngrok with the new URL
ngrok http 8001

# 2. Register a new BT client
curl -X POST https://api.apistorebt.ro/bt/sb/oauth/register \
  -H "Content-Type: application/json" \
  -d '{"redirect_uris":["https://NEW-URL.ngrok-free.app/api/v1/bank/oauth2/callback"],"client_name":"Virtual Finance Advisor"}'

# 3. Update .env with new client_id, client_secret, and BT_REDIRECT_URI

# 4. Recreate the container (no rebuild needed)
docker-compose up -d backend
```

> **Tip:** A paid ngrok account provides a static domain, eliminating this re-registration step.

### Demo mode (no BT account needed)

On the Bank screen, tap **Connect Demo Data** to load realistic mock Romanian transactions without any BT credentials.

---

## Security

- **AES-256-CBC** — Field-level encryption for sensitive user keys
- **bcrypt** — Password hashing
- **JWT** — Secure session management
- **PKCE (RFC 7636)** — Required for BT OAuth2 authorization code flow

---

## API Reference

| Endpoint | Description |
|---|---|
| `GET /api/v1/health` | Health check |
| `POST /api/v1/bank/connect` | Initiate BT PSD2 consent + get auth URL |
| `GET /api/v1/bank/accounts` | List BT accounts |
| `GET /api/v1/bank/balances/{id}` | Account balance |
| `GET /api/v1/bank/transactions` | Cached transactions (filter by month) |
| `POST /api/v1/bank/sync` | Force re-sync from BT API |
| `GET /api/v1/bank/spending-summary` | Monthly spending by category |
| `GET /api/v1/bank/subscriptions` | Auto-detected recurring charges |
