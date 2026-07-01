"""
tests/test_functional.py
========================
Functional test suite with requirement -> test traceability.

Each test documents the functional requirement (CF-xx) it validates.  The
requirement catalogue used by the thesis:

  CF-01  Autentificare: înregistrarea impune parolă >= 8 caractere.
  CF-02  Preluarea portofoliului eToro (live sau fallback mock).
  CF-03  Preluarea cotației de piață pentru un simbol (Yahoo Finance / mock).
  CF-04  Categorizarea automată a tranzacțiilor bancare (taxonomie).
  CF-05  Detecția tranzacțiilor recurente / abonamentelor.
  CF-06  Detecția anomaliilor de portofoliu (ansamblu ML, is_anomaly+confidence).
  CF-07  Agentul Tori expune uneltele MCP corecte (tool wiring).
  CF-08  Rezumatul cheltuielilor pe categorii + semnalarea depășirii bugetului.

Run:  python -m pytest tests -v --cov=app
"""
import copy

import pytest
from pydantic import ValidationError

from app.services.expense_categorizer import (
    categorize_transaction,
    detect_recurring,
    get_spending_by_category,
    generate_spending_summary_text,
)

# A normal 6-position portfolio used by the anomaly endpoint test (CF-06).
NORMAL_PORTFOLIO = {
    "positions": [
        {"instrument_id": 1,  "quantity": 5.0,  "avg_buy_price": 155.20, "current_value": 937.50,  "unrealized_pnl": 162.50},
        {"instrument_id": 12, "quantity": 0.05, "avg_buy_price": 35000.0, "current_value": 3390.00, "unrealized_pnl": 1390.00},
        {"instrument_id": 6,  "quantity": 3.0,  "avg_buy_price": 420.00, "current_value": 2625.00, "unrealized_pnl": 1365.00},
        {"instrument_id": 2,  "quantity": 4.0,  "avg_buy_price": 280.00, "current_value": 780.00,  "unrealized_pnl": -340.00},
        {"instrument_id": 5,  "quantity": 2.0,  "avg_buy_price": 380.00, "current_value": 831.00,  "unrealized_pnl": 71.00},
        {"instrument_id": 9,  "quantity": 10.0, "avg_buy_price": 440.00, "current_value": 4550.00, "unrealized_pnl": 150.00},
    ]
}


# ── TC-01 → CF-01 ─────────────────────────────────────────────────────────────
def test_tc01_registration_enforces_password_length():
    """Precondition: —. Step: build UserRegisterRequest. Expected: <8 chars rejected."""
    from app.schemas.schemas import UserRegisterRequest
    with pytest.raises(ValidationError):
        UserRegisterRequest(username="ana", email="ana@x.com", password="scurt")   # 5 chars
    ok = UserRegisterRequest(username="ana", email="ana@x.com", password="parola12")  # 8 chars
    assert ok.password == "parola12"


# ── TC-02 → CF-02 ─────────────────────────────────────────────────────────────
async def test_tc02_etoro_portfolio_returns_positions(client):
    """Precondition: USE_MOCK_DATA=true. Step: GET /etoro/portfolio. Expected: 200 + positions."""
    r = await client.get("/api/v1/etoro/portfolio")
    assert r.status_code == 200
    body = r.json()
    assert isinstance(body.get("positions"), list) and len(body["positions"]) >= 1
    assert body["positions"][0].get("symbol")     # positions are enriched with symbols


# ── TC-03 → CF-03 ─────────────────────────────────────────────────────────────
async def test_tc03_market_quote(client):
    """Precondition: —. Step: GET /market/quote/AAPL. Expected: 200 + price>0 for AAPL."""
    r = await client.get("/api/v1/market/quote/AAPL")
    assert r.status_code == 200
    body = r.json()
    assert body["symbol"] == "AAPL"
    assert float(body["price"]) > 0


# ── TC-04 → CF-04 ─────────────────────────────────────────────────────────────
@pytest.mark.parametrize("info,creditor,expected", [
    ("", "Kaufland SRL", "Food & Groceries"),
    ("Plata la statia OMV", "", "Transport"),
    ("", "Orange Romania SA", "Utilities"),
    ("", "KFC Baneasa", "Dining"),
    ("", "eMAG.ro", "Shopping"),
    ("", "Farmacia Catena", "Health"),
    ("Adobe Creative Cloud", "", "Subscriptions"),
    ("plata necunoscuta xyz", "", "Other"),
])
def test_tc04_transaction_categorization(info, creditor, expected):
    """Precondition: —. Step: categorize_transaction(info, creditor). Expected: correct category."""
    assert categorize_transaction(info, creditor) == expected


# ── TC-05 → CF-05 ─────────────────────────────────────────────────────────────
def test_tc05_recurring_detection():
    """Precondition: mixed tx list. Step: detect_recurring. Expected: keyword & pattern flagged, one-off not."""
    txns = [
        {"creditorName": "Netflix", "bookingDate": "2026-05-10", "remittanceInformationUnstructured": ""},
        {"creditorName": "Local Shop", "bookingDate": "2026-04-15", "remittanceInformationUnstructured": ""},
        {"creditorName": "Local Shop", "bookingDate": "2026-05-16", "remittanceInformationUnstructured": ""},
        {"creditorName": "One Time Store", "bookingDate": "2026-05-02", "remittanceInformationUnstructured": ""},
    ]
    flags = {t["creditorName"]: t["_isRecurring"] for t in detect_recurring(txns)}
    assert flags["Netflix"] is True         # keyword-based subscription
    assert flags["Local Shop"] is True      # same day-of-month across 2 months
    assert flags["One Time Store"] is False # single occurrence, no keyword


# ── TC-06 → CF-06 ─────────────────────────────────────────────────────────────
async def test_tc06_anomaly_detection_flags_injected_anomaly(client):
    """Precondition: models warm-trained on a normal snapshot.
    Step: POST /anomaly/analyze with an injected value-spike position.
    Expected: is_anomaly=True, confidence HIGH, score above the normal baseline."""
    import app.ml.anomaly_service as svc
    svc._models_trained = False   # force (re)training on the first, normal, request

    r_norm = await client.post("/api/v1/anomaly/analyze", json=NORMAL_PORTFOLIO)
    assert r_norm.status_code == 200
    norm = r_norm.json()
    assert norm["is_anomaly"] is False

    anomalous = copy.deepcopy(NORMAL_PORTFOLIO)
    anomalous["positions"][1]["current_value"] *= 10      # position worth x10
    anomalous["positions"][1]["unrealized_pnl"] *= 10
    r_anom = await client.post("/api/v1/anomaly/analyze", json=anomalous)
    assert r_anom.status_code == 200
    anom = r_anom.json()
    assert anom["is_anomaly"] is True
    assert anom["confidence"] == "HIGH"
    assert anom["weighted_avg_score"] > norm["weighted_avg_score"]


# ── TC-07 → CF-07 ─────────────────────────────────────────────────────────────
def test_tc07_agent_exposes_expected_mcp_tools():
    """Precondition: MCP server imported. Step: list registered tools.
    Expected: the 8 financial tools the agent needs are present."""
    from app.mcp.server import mcp_server
    names = {t.name for t in mcp_server._tool_manager.list_tools()}
    expected = {
        "get_my_portfolio", "get_all_instruments", "get_stock_price",
        "get_market_sentiment", "get_spending_summary", "get_budget_status",
        "get_subscriptions", "get_recent_transactions",
    }
    assert expected.issubset(names), f"missing tools: {expected - names}"


# ── TC-08 → CF-08 ─────────────────────────────────────────────────────────────
def test_tc08_spending_summary_and_budget_overrun():
    """Precondition: known debit tx + a Dining budget of 200.
    Step: aggregate + summary text. Expected: correct totals, Income excluded, overrun flagged."""
    txns = [
        {"bookingDate": "2026-06-03", "amount": -450.0, "_category": "Food & Groceries", "transactionAmount": {"amount": "-450.0"}},
        {"bookingDate": "2026-06-10", "amount": -300.0, "_category": "Dining",           "transactionAmount": {"amount": "-300.0"}},
        {"bookingDate": "2026-06-12", "amount": -120.0, "_category": "Food & Groceries", "transactionAmount": {"amount": "-120.0"}},
        {"bookingDate": "2026-06-15", "amount": 2000.0, "_category": "Income",           "transactionAmount": {"amount": "2000.0"}},
    ]
    spend = get_spending_by_category(txns, "2026-06")
    assert spend["Food & Groceries"] == 570.0
    assert spend["Dining"] == 300.0
    assert "Income" not in spend

    text = generate_spending_summary_text(spend, [{"category": "Dining", "limit_amount": 200.0}], "2026-06")
    assert "OVER" in text     # Dining 300/200 = 150% -> flagged as over budget
