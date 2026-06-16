# 🏗️ System Overview

Tags: #architecture #overview

## Purpose

Virtual Personal Finance Advisor is a full-stack platform that helps users:
1. **Track** real bank transactions via Banca Transilvania PSD2 AISP API
2. **Monitor** investment portfolio via eToro API + Yahoo Finance market data
3. **Detect** unusual portfolio behaviour via ML anomaly ensemble
4. **Advise** through Tori, an LLM-powered conversational financial agent

> The application is **strictly educational / decision-support** (read-only). No automated trading or fund transfers are performed. This is intentional to protect users from LLM hallucinations.

---

## High-Level Architecture

```mermaid
graph TD
    subgraph "Client Layer"
        Flutter[Flutter App\nDark-theme, Material 3]
    end

    subgraph "Backend Layer — FastAPI + uvloop"
        Auth[auth router\nJWT + bcrypt]
        Bank[bank router\nBT PSD2 proxy]
        Agent[agent router\nTori LLM]
        Anomaly[anomaly router\nML ensemble]
        Market[market router\nYahoo Finance]
        eToro[etoro router\nPortfolio]
        Budget[budget router]
        Expenses[expenses router]
        Health[health router\nCircuit breakers]
    end

    subgraph "Core Infrastructure"
        DB[(PostgreSQL 16\nasyncpg)]
        Cache[LRU Cache\n256 entries + TTL]
        CB[Circuit Breakers\neToro + Yahoo Finance]
        Vault[HashiCorp Vault\nAES-256 master key]
    end

    subgraph "External APIs"
        BTApi[Banca Transilvania\nPSD2 AISP API v2]
        EtoroApi[eToro Public API]
        AVApi[Yahoo Finance\nyfinance — no key]
        GeminiApi[Google Gemini\ngemini-3.1-flash-lite]
    end

    subgraph "ML Module"
        IF[Isolation Forest\nweight 0.35]
        AE[PCA Autoencoder\nweight 0.40]
        SVM[One-Class SVM\nweight 0.25]
        Ensemble[Voting Ensemble\nthreshold 0.5]
    end

    subgraph "MCP Layer"
        MCP[FastMCP Server\nTori Financial Tools]
    end

    Flutter -->|HTTP REST + JWT| Auth
    Flutter --> Bank
    Flutter --> Agent
    Flutter --> Anomaly
    Flutter --> Market
    Flutter --> eToro
    Flutter --> Budget
    Flutter --> Expenses

    Agent --> MCP
    MCP --> EtoroApi
    MCP --> AVApi
    MCP --> GeminiApi

    Bank --> BTApi
    Anomaly --> IF
    Anomaly --> AE
    Anomaly --> SVM
    IF & AE & SVM --> Ensemble

    Auth & Bank & Agent & Anomaly --> DB
    Market --> Cache
    Cache --> AVApi
    CB --> EtoroApi
    CB --> AVApi
    Auth --> Vault
```

---

## Technology Stack

| Layer | Technology | Version / Notes |
|---|---|---|
| **Frontend** | Flutter | Dart SDK ≥3.0.0, Material 3 |
| **Backend** | FastAPI | 0.135.1 + uvloop |
| **ORM** | SQLAlchemy (async) | 2.0.48 + asyncpg |
| **Database** | PostgreSQL | 16-alpine (Docker) |
| **Migrations** | Alembic | 1.18.4 |
| **AI Agent LLM** | Google Gemini | gemini-3.1-flash-lite |
| **Agent Framework** | LangGraph ReAct | create_react_agent |
| **MCP** | FastMCP | via `mcp` ≥1.26.0 |
| **ML** | scikit-learn | 1.5.2 + numpy 1.26.4 |
| **Cryptography** | cryptography | 44.0.2 (AES-256-CBC) |
| **JWT** | python-jose | 3.3.0 (HS256) |
| **Secrets** | HashiCorp Vault | hvac 2.1.0 |
| **HTTP Client** | httpx | 0.28.1 |
| **Container** | Docker / Compose | 3 services |

---

## Request Lifecycle (Happy Path)

```mermaid
sequenceDiagram
    participant Flutter
    participant FastAPI
    participant DB
    participant BT as BT PSD2 API

    Flutter->>FastAPI: POST /api/v1/bank/connect
    FastAPI->>DB: Check existing BTConnection
    DB-->>FastAPI: No active token
    FastAPI->>BT: POST /v2/consents (create consent)
    BT-->>FastAPI: {consentId, scaRedirect}
    FastAPI->>DB: INSERT BTConnection(consent_id)
    FastAPI-->>Flutter: {auth_url: "https://bt-keycloak/..."}
    Flutter->>Flutter: Open auth_url in browser
    Note over Flutter,BT: User authenticates on BT page
    BT->>FastAPI: GET /api/v1/bank/oauth2/callback?code=...
    FastAPI->>BT: POST /oauth/token (exchange code + PKCE)
    BT-->>FastAPI: {access_token, refresh_token}
    FastAPI->>DB: UPDATE BTConnection(access_token)
    FastAPI-->>Flutter: HTML success page
    Flutter->>FastAPI: GET /api/v1/bank/transactions
    FastAPI->>DB: SELECT BankTransaction (cached)
    DB-->>FastAPI: rows
    FastAPI-->>Flutter: [{...transactions}]
```

---

## Data Domains

| Domain | Tables | External Service |
|---|---|---|
| Identity | `users` | — |
| Sessions | `chat_messages` | — |
| Portfolio | `assets`, `portfolio_positions` | eToro |
| Anomalies | `anomaly_logs` | scikit-learn |
| Banking | `bt_connections`, `bank_transactions`, `budgets` | BT PSD2 |
| Caching | `cache_entries` | — |

---

## Related Notes
- [[00 - Index]]
- [[02 - Docker & Deployment]]
- [[03 - FastAPI Application]]
- [[09 - BT PSD2 Bank Integration]]
- [[17 - eToro & Market Data]]
- [[14 - Flutter Frontend]]
- [[11 - Fault Tolerance]]
- [[18 - Changelog]]
