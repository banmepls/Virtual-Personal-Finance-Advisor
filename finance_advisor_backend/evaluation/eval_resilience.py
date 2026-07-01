"""
evaluation/eval_resilience.py
=============================
Empirical resilience evaluation — injects real faults and records the
*observed* behaviour of the fault-tolerance mechanisms.

Scenarios
---------
F-01  External market-data provider (Yahoo Finance) fails repeatedly.
      Expected: the circuit breaker opens on the 5th consecutive failure and
      every request is served from the mock fallback; after the 60 s recovery
      window it probes (HALF_OPEN) and closes again after 2 successes.

F-02  Downstream failure (DB unreachable) during an MCP tool call.
      Expected: the tool NEVER raises; it returns a graceful `{"error": ...}`
      payload so the agent turn survives.

F-03  HashiCorp Vault unreachable at startup.
      Expected: the key manager fails open to `FALLBACK_MASTER_KEY` and logs a
      warning instead of crashing.

Outputs evaluation/results_resilience.json and a readable trace on stdout.
Run:  python -m evaluation.eval_resilience
"""
from __future__ import annotations

import asyncio
import json
import logging
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

# Env must be set before importing app.* (config / database / vault read it).
os.environ.setdefault("DATABASE_URL", "postgresql+asyncpg://test:test@localhost:5432/testdb")
os.environ.setdefault("POSTGRES_USER", "test")
os.environ.setdefault("POSTGRES_PASSWORD", "test")
os.environ.setdefault("POSTGRES_DB", "testdb")
os.environ.setdefault("USE_MOCK_DATA", "true")
# Point Vault at a refused port and pin a known fallback key for F-03.
os.environ["VAULT_ADDR"] = "http://127.0.0.1:1"
os.environ["FALLBACK_MASTER_KEY"] = "RESILIENCE_TEST_FALLBACK_KEY_0001"

OUT_JSON = Path(__file__).resolve().parent / "results_resilience.json"


class _LogCapture(logging.Handler):
    """Collect WARNING+ log records so we can quote them as evidence."""
    def __init__(self):
        super().__init__(level=logging.WARNING)
        self.records: list[str] = []

    def emit(self, record):
        self.records.append(f"{record.levelname}:{record.name}: {record.getMessage()}")


log_capture = _LogCapture()
logging.getLogger().addHandler(log_capture)
logging.getLogger().setLevel(logging.INFO)


# ── F-01: circuit breaker on repeated upstream failure ───────────────────────
async def scenario_circuit_breaker() -> dict:
    from app.services import cache_service
    import app.services.market_data as md
    from app.services.market_data import MarketDataService
    from app.core.circuit_breaker import CBState

    md.settings.use_mock_data = False              # force the live path
    mds = MarketDataService()
    cb = mds._cb
    # reset breaker to a clean CLOSED state
    cb._state = CBState.CLOSED
    cb._failure_count = 0
    cb._success_count = 0
    cb._last_failure_time = 0.0

    def raising_fetch(symbol):
        raise RuntimeError("simulated upstream HTTP 500")

    def good_fetch(symbol):
        return {"symbol": symbol, "price": 123.45, "change_percent": "+0.00%",
                "volume": "1", "source": "live"}

    trace = []

    # 7 consecutive failures — breaker should open at the 5th.
    mds._fetch_quote_sync = raising_fetch
    for i in range(1, 8):
        cache_service.cache_clear()
        res = await mds.get_stock_quote("AAPL")
        trace.append({"call": i, "phase": "fault_injected",
                      "cb_state": cb.state.value, "failure_count": cb._failure_count,
                      "result_source": res.get("source")})

    opened_at = next((t["call"] for t in trace if t["cb_state"] == "OPEN"), None)
    health_when_open = cb.status_dict()

    # Recovery: restore upstream, simulate 60 s elapsed, probe to close.
    mds._fetch_quote_sync = good_fetch
    cb._last_failure_time -= 61.0                  # simulate recovery window elapsed
    recovery = []
    for i, sym in enumerate(("AAPL", "MSFT"), start=1):
        cache_service.cache_clear()
        res = await mds.get_stock_quote(sym)
        recovery.append({"probe": i, "cb_state_after": cb.state.value,
                         "success_count": cb._success_count,
                         "result_source": res.get("source")})

    md.settings.use_mock_data = True              # restore default
    return {
        "fault": "5x simulated HTTP 500 on Yahoo Finance",
        "opened_at_failure": opened_at,
        "health_snapshot_when_open": health_when_open,
        "trace": trace,
        "recovery_trace": recovery,
        "final_state": cb.state.value,
    }


# ── F-02: MCP tool never raises when the DB is down ──────────────────────────
async def scenario_mcp_graceful() -> dict:
    import app.mcp.server as server

    class _BrokenSession:
        async def __aenter__(self):
            raise ConnectionError("DB connection refused (simulated F-02)")

        async def __aexit__(self, *a):
            return False

    original = server.AsyncSessionLocal
    server.AsyncSessionLocal = lambda: _BrokenSession()
    try:
        spending = await server.get_spending_summary("2026-06")
        recents = await server.get_recent_transactions(5)
        subs = await server.get_subscriptions()
    finally:
        server.AsyncSessionLocal = original

    return {
        "fault": "DB unreachable during MCP tool calls",
        "get_spending_summary": {"raised": False, "returned": spending,
                                 "graceful": isinstance(spending, dict) and "error" in spending},
        "get_recent_transactions": {"raised": False, "returned_type": type(recents).__name__,
                                    "graceful": isinstance(recents, list)},
        "get_subscriptions": {"raised": False, "returned_type": type(subs).__name__,
                              "graceful": isinstance(subs, list)},
    }


# ── F-03: Vault unreachable → fail-open to env fallback key ───────────────────
def scenario_vault_failopen() -> dict:
    from app.core.vault import VaultManager
    vm = VaultManager()                            # VAULT_ADDR points to a refused port
    fallback = os.environ["FALLBACK_MASTER_KEY"]
    vault_warnings = [r for r in log_capture.records if "vault" in r.lower()
                      or "fallback master key" in r.lower()]
    return {
        "fault": "Vault unreachable at http://127.0.0.1:1",
        "master_key_available": vm.master_key is not None,
        "used_fallback": vm.master_key == fallback,
        "warning_logged": any("fallback" in w.lower() for w in vault_warnings),
        "sample_warnings": vault_warnings[-3:],
    }


def main():
    print("=== F-01: Circuit Breaker (Yahoo Finance) ===")
    cb_res = asyncio.run(scenario_circuit_breaker())
    for t in cb_res["trace"]:
        print(f"  call {t['call']}: fault -> state={t['cb_state']:9s} "
              f"fails={t['failure_count']} source={t['result_source']}")
    print(f"  -> breaker OPEN at failure #{cb_res['opened_at_failure']}; "
          f"/health snapshot: {cb_res['health_snapshot_when_open']}")
    for r in cb_res["recovery_trace"]:
        print(f"  recovery probe {r['probe']}: state={r['cb_state_after']} "
              f"successes={r['success_count']} source={r['result_source']}")
    print(f"  -> final state: {cb_res['final_state']}")

    print("\n=== F-02: MCP graceful degradation (DB down) ===")
    mcp_res = asyncio.run(scenario_mcp_graceful())
    for tool in ("get_spending_summary", "get_recent_transactions", "get_subscriptions"):
        print(f"  {tool}: raised={mcp_res[tool]['raised']} graceful={mcp_res[tool]['graceful']}")

    print("\n=== F-03: Vault fail-open ===")
    vault_res = scenario_vault_failopen()
    print(f"  master_key_available={vault_res['master_key_available']} "
          f"used_fallback={vault_res['used_fallback']} warning_logged={vault_res['warning_logged']}")
    for w in vault_res["sample_warnings"]:
        print(f"    log> {w}")

    results = {"F-01": cb_res, "F-02": mcp_res, "F-03": vault_res}
    OUT_JSON.write_text(json.dumps(results, indent=2, default=str))
    print(f"\n[out] wrote {OUT_JSON}")


if __name__ == "__main__":
    main()
