"""
app/services/expense_categorizer.py
──────────────────────────────────────
AI-powered transaction categorization using Google Gemini,
with keyword fallback to avoid API quota waste.
Also handles recurring / subscription detection.
"""
import re
from collections import defaultdict
from datetime import date
import logging

logger = logging.getLogger(__name__)

# ── Keyword-based category mapping (fast, no LLM needed) ─────────────────────

_KEYWORD_MAP = {
    "Food & Groceries": [
        "kaufland", "lidl", "carrefour", "auchan", "mega image", "profi",
        "penny", "selgros", "metro", "hypermarket", "supermarket", "groceri",
        "alimentar", "piata", "bacanie",
    ],
    "Transport": [
        "omv", "petrom", "rompetrol", "mol ", "lukoil", "benzinarie","benzina",
        "bolt", "uber", "taxi", "parcare", "parking", "autostrada", "autobuz",
        "metrou", "cfr", "tarom", "wizz", "ryanair", "bilet transport",
    ],
    "Utilities": [
        "enel", "digi", "rcs", "rds", "orange", "vodafone", "telekom",
        "electrica", "e.on", "eon", "gaze", "apa", "termoficare",
        "furnizor energie", "internet",
    ],
    "Dining": [
        "mcdonald", "kfc", "pizza hut", "burger king", "subway", "starbucks",
        "restaurant", "bistro", "crama", "pub", "bar ", "cafe", "cofetarie",
        "shaorma", "kebab", "sushi",
    ],
    "Shopping": [
        "dedeman", "altex", "emag", "zara", "h&m", "hm ", "pull&bear",
        "reserved", "lcwaikiki", "pepco", "action ", "jysk", "ikea",
        "librarie", "papetarie",
    ],
    "Health": [
        "farmacie", "catena", "dr. max", "sensiblu", "help net",
        "regina maria", "medicover", "sanador", "clinica", "spital",
        "doctor", "laborator", "optica",
    ],
    "Entertainment": [
        "cinema city", "hbo", "netflix", "spotify", "steam", "playstation",
        "nintendo", "bilet", "teatru", "muzeu", "concert", "distractie",
        "parc",
    ],
    "Subscriptions": [
        "netflix", "spotify", "adobe", "microsoft 365", "office 365",
        "apple", "google play", "youtube premium", "hbo max", "deezer",
        "dropbox", "icloud",
    ],
    "Rent": [
        "chirie", "imobiliare", "locatar", "proprietar", "rent",
        "apartament", "studio inchiriat",
    ],
    "Income": [
        "salariu", "salary", "angajator", "dividende", "transfer primit",
        "credit", "depozit",
    ],
}

_SUBSCRIPTION_KEYWORDS = set(_KEYWORD_MAP["Subscriptions"])


def categorize_transaction(remittance_info: str, creditor_name: str) -> str:
    """
    Keyword-based categorization — fast and offline.
    Returns a category string from the taxonomy.
    """
    text = f"{remittance_info or ''} {creditor_name or ''}".lower()
    for category, keywords in _KEYWORD_MAP.items():
        for kw in keywords:
            if kw in text:
                return category
    return "Other"


def detect_recurring(transactions: list[dict]) -> list[dict]:
    """
    Flag transactions as recurring / subscription based on:
    - Keyword match to subscription list
    - Same creditor appearing on same day of month for 2+ months
    Returns the same list with '_is_recurring' flag set.
    """
    # Build frequency map: creditor_name → list of dates
    creditor_dates: dict[str, list[date]] = defaultdict(list)
    for tx in transactions:
        cname = (tx.get("creditorName") or "").lower()
        bd = tx.get("bookingDate")
        if cname and bd:
            try:
                d = date.fromisoformat(bd) if isinstance(bd, str) else bd
                creditor_dates[cname].append(d)
            except ValueError:
                pass

    # Flag as recurring: same creditor, appears on same day-of-month across 2+ months
    recurring_creditors: set[str] = set()
    for cname, dates in creditor_dates.items():
        if len(dates) >= 2:
            days = [d.day for d in dates]
            months = [d.month for d in dates]
            if len(set(months)) >= 2 and (max(days) - min(days)) <= 3:
                recurring_creditors.add(cname)

    for tx in transactions:
        cname = (tx.get("creditorName") or "").lower()
        info = (tx.get("remittanceInformationUnstructured") or "").lower()
        text = f"{cname} {info}"
        is_keyword_sub = any(kw in text for kw in _SUBSCRIPTION_KEYWORDS)
        is_pattern_rec = cname in recurring_creditors
        tx["_isRecurring"] = is_keyword_sub or is_pattern_rec

    return transactions


def get_spending_by_category(transactions: list[dict],
                              month_year: str | None = None) -> dict[str, float]:
    """
    Aggregate debit transactions by category for a given month (YYYY-MM).
    Only counts debit (outgoing) transactions.
    """
    totals: dict[str, float] = defaultdict(float)
    for tx in transactions:
        bd = tx.get("bookingDate") or tx.get("booking_date", "")
        if month_year and not str(bd).startswith(month_year):
            continue
        try:
            amount = float(tx.get("transactionAmount", {}).get("amount")
                           or tx.get("amount", 0))
        except (TypeError, ValueError):
            continue
        if amount >= 0:
            continue  # only outgoing
        category = (tx.get("_category") or tx.get("category") or "Other")
        if category == "Income":
            continue
        totals[category] += abs(amount)

    return dict(sorted(totals.items(), key=lambda x: x[1], reverse=True))


def extract_subscriptions(transactions: list[dict]) -> list[dict]:
    """
    Extract unique recurring subscription charges from transaction list.
    Returns one entry per merchant with amount, frequency, last_charge.
    """
    subs: dict[str, dict] = {}
    for tx in transactions:
        if not tx.get("_isRecurring"):
            continue
        cat = tx.get("_category") or tx.get("category", "")
        if cat not in ("Subscriptions", "Utilities"):
            continue
        cname = tx.get("creditorName") or "Unknown"
        try:
            amount = abs(float(tx.get("transactionAmount", {}).get("amount")
                               or tx.get("amount", 0)))
        except (TypeError, ValueError):
            amount = 0.0
        bd = tx.get("bookingDate") or tx.get("booking_date")
        if cname not in subs or (bd and str(bd) > str(subs[cname]["last_charge"])):
            subs[cname] = {
                "merchant": cname,
                "amount": amount,
                "currency": (tx.get("transactionAmount", {}).get("currency")
                             or tx.get("currency", "RON")),
                "category": cat,
                "last_charge": str(bd) if bd else "",
                "frequency": "monthly",
            }
    return sorted(subs.values(), key=lambda x: x["amount"], reverse=True)


def generate_spending_summary_text(
    spending: dict[str, float],
    budgets: list[dict],
    month_year: str
) -> str:
    """
    Build a short human-readable spending summary that Tori can return directly.
    """
    total = sum(spending.values())
    lines = [f"📊 Spending Summary for {month_year}:", f"Total spent: {total:.2f} RON\n"]
    for cat, amt in spending.items():
        # Find matching budget
        bgt = next((b for b in budgets if b.get("category") == cat), None)
        if bgt:
            limit = bgt.get("limit_amount", 0)
            pct = (amt / limit * 100) if limit else 0
            status = "🔴 OVER" if pct > 100 else ("🟡" if pct > 75 else "🟢")
            lines.append(f"  {status} {cat}: {amt:.2f} / {limit:.2f} RON ({pct:.0f}%)")
        else:
            lines.append(f"  • {cat}: {amt:.2f} RON")
    return "\n".join(lines)
