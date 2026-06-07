# 📝 Changelog

Tags: #changelog #history

Notable changes and fixes. Newest first.

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
