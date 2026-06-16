# 📝 Changelog

Tags: #changelog #history

Notable changes and fixes. Newest first.

---

## 2026-06-08 — Market data: Alpha Vantage → Yahoo Finance

- **Replaced Alpha Vantage with Yahoo Finance** (`yfinance` library) as the market-quote/history source. No API key and **no fixed daily quota** — the old 25 req/day limit is gone. `yfinance` is synchronous, so calls run in a worker thread (`asyncio.to_thread`) behind the renamed `yahoo_finance` circuit breaker. See [[17 - eToro & Market Data]].
- **Removed the Alpha Vantage quota guard** from the cache service (`ALPHA_VANTAGE_DAILY_LIMIT`, `_av_daily_counter`, `av_quota_*`, `av_increment_counter`) and the `alpha_vantage_quota` block from `/health` + `HealthResponse`. See [[12 - Cache Service]], [[11 - Fault Tolerance]], [[16 - Pydantic Schemas]].
- Dropped `alpha_vantage_api_key` from settings; crypto symbols auto-map to Yahoo's `-USD` convention.
- **Caveat:** `yfinance` uses Yahoo's unofficial endpoints, so it can throttle (HTTP 429) or break on Yahoo-side changes — covered by circuit breaker + cache + mock fallback.

---

## 2026-06-08 — Tori bank-awareness, MCP resilience & UI fixes

### Tori can finally read bank data
- Added four DB-backed MCP tools — `get_spending_summary`, `get_budget_status`, `get_subscriptions`, `get_recent_transactions` — so the agent's "bank-aware" prompt claims are actually backed by data. Previously Tori had only portfolio/market tools and would wrongly answer "the bank isn't synced" to spending/overspend questions. See [[07 - MCP Server]], [[06 - Tori Agent]].

### MCP resilience (fixes "Tori temporarily unavailable")
- All MCP tools now catch their own errors and return `{"error": ...}` instead of raising. A raised tool exception previously aborted the whole LangGraph turn → the user saw the offline fallback. Triggered most often by `get_stock_price` (invalid symbol / market data unavailable).

### Frontend
- **Generative `action_button` is now stateful** — shows a "Working…" spinner + disables while running, then reports the real result. The "Sync Bank" button previously looked dead during the multi-second sync. See [[14 - Flutter Frontend]].
- **Quick-access deep-links to sub-tabs** — Home chips now drive State-owned `TabController`s, so "Budget"/"Subs"/"Expenses" open the correct Money-hub sub-tab instead of always landing on the first one.

---

## 2026-06-07 — Consistency refactor, dead-code cleanup & wiring

### Frontend consistency
- **Shared palette** — new `theme/app_colors.dart` (`AppColors`); the six token-block screens now reference it instead of redeclaring hex values.
- **Shared currency formatting** — new `utils/money.dart` (`Money.ron/ronCompact/usd`) used across Bank, Expense, Subscriptions.
- **Unified empty states** — all list screens use the single `EmptyState` widget.
- **No duplicate headers** — removed the redundant `SliverAppBar`s from the Money hub sub-screens (Budget/Subscriptions/Expense); the hub provides the header.
- **Error+Retry everywhere** — added proper error/retry to Chart (was silent) and a Retry to the Anomaly inline error.

### Dead-code cleanup
- Removed ~24 unused imports + unused symbols (`verify_token`, `retrain`, `app_name`, Dart `setToken`, an unused `settings` local) and 3 scratch test scripts.
- Verified: pyflakes 0 unused, `flutter analyze` 0 errors / 0 unused.
- See [[10 - Security]] — `verify_token` removal note (auth is not yet enforced; routes use `DEFAULT_USER_ID`).

### Newly wired features
- **Delete budget** — `BudgetStatusItem` now carries `budget_id`; budget cards are **swipe-to-delete** → `DELETE /budget/{id}`. See [[16 - Pydantic Schemas]], [[14 - Flutter Frontend]].
- **Frontend redirect after bank auth** — `GET /bank/oauth2/callback` now auto-redirects to `bt_frontend_redirect_uri` (default `http://localhost`). See [[09 - BT PSD2 Bank Integration]].

---

## 2026-06-07 — eToro live data + Frontend UX overhaul

### eToro integration fixed (now serves real data)
- **Corrected base URL** `api.etoro.com` → `https://public-api.etoro.com` (the old host 404'd on every call).
- **Switched to the public portfolio endpoint** `GET /api/v1/user-info/people/{username}/portfolio/live` — fetches a public user's portfolio (e.g. `Aguero1010`) and works with a standard key. The private own-account endpoint (`/trading/info/demo/pnl`) requires `demo:read` scope and returned `403 InsufficientPermissions`.
- **Rewrote `_parse_portfolio`** to the allocation-percentage model (`investmentPct`/`netProfit` on a $10k baseline), aggregating split positions by instrument.
- **Fixed instrument metadata URL** to `/api/v1/market-data/instruments` (was missing `/api/v1`) → symbols/names/asset-classes now resolve.
- **Auto-heal of unknown instruments** — `resolve()` no longer caches the `Unknown` fallback and `_enrich_positions` retries any *unmapped* ID, so instruments resolve on a later fetch instead of sticking as `ID_####`.
- Added a **credential preflight** with actionable errors (placeholder keys); an `UnregisteredApplication` key is *not* blocked since it's valid for public reads.
- See [[17 - eToro & Market Data]].

### BT sandbox realism
- `get_accounts` / `get_balances` now fall back to the **official BT Swagger example accounts** (RON `K13RONCRT0060214301`, EUR `K13EURCRT0060214301`) when the sandbox returns empty/401 (`accounts_count: 0`).
- Mock balances/transactions match the documented schema (`creditLimitIncluded`, `referenceDate`, `bankTransactionCode`, `endToEndId`).
- `bookingStatus` changed `both` → `booked` (sandbox rejects the others with 400).
- Fixed `MultipleResultsFound` crashes by replacing `scalar_one_or_none()` with ordered `.scalars().first()` across bank endpoints.
- See [[09 - BT PSD2 Bank Integration]].

### Frontend UX (see [[14 - Flutter Frontend]])
- **`IndexedStack` navigation** — tab state (scroll, chat history, input) now survives tab switches.
- **Real authentication** — login/register against `/auth/*`, JWT decoded client-side, persisted via `SharedPreferences`, session auto-restore on launch, logout via profile sheet. (Replaced the previous hardcoded fake login.)
- **New Home/Overview tab** — "Your Money" card (Investments USD + Bank RON shown separately), quick-access row to buried features, investments treemap + positions.
- **Honest data-source badge** — `LIVE`/`DEMO` derived from the data instead of an always-on "LIVE".
- **Treemap charts** replace pie/donut charts (dependency-free squarified treemap) on the dashboard allocation and the spending-by-category views.
- **Simplified Bank connect** — one primary "Connect Demo Data" CTA; developer OAuth paths folded into an "Advanced" expander; jargon rewritten in plain language.
- **Tori chat auto-scroll** reliably pins to the bottom across multi-pass markdown/widget layout.
- **Anomaly auto-runs** when positions are available, with an empty-state guard.
- Reusable **empty-state** widget; accessibility bumps to the smallest labels.

### Agent resilience
- `POST /agent/chat` degrades gracefully to a friendly offline message instead of HTTP 500 when the LLM is unreachable.

---

## Baseline (vault inception)

- Initial documentation vault created covering architecture, Docker, FastAPI, endpoints, DB models, Tori agent, MCP, ML anomaly ensemble, BT integration, security, fault tolerance, cache, expense categorizer, frontend, dependencies, and schemas.
