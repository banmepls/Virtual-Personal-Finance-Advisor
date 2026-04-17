"""
app/models/bank_transaction.py
───────────────────────────────
Cached Banca Transilvania transactions fetched via PSD2 AISP API.
"""
from sqlalchemy import Column, Integer, String, Float, DateTime, Boolean, Text, Date
from datetime import datetime, timezone

from app.core.database import Base


class BankTransaction(Base):
    __tablename__ = "bank_transactions"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, nullable=False, index=True)
    account_id = Column(String(128), nullable=False, index=True)
    transaction_id = Column(String(256), unique=True, nullable=False)
    booking_date = Column(Date, nullable=True)
    value_date = Column(Date, nullable=True)
    amount = Column(Float, nullable=False)
    currency = Column(String(8), default="RON")
    creditor_name = Column(String(256), nullable=True)
    debtor_name = Column(String(256), nullable=True)
    remittance_info = Column(Text, nullable=True)   # transaction description
    category = Column(String(64), default="Other")
    is_recurring = Column(Boolean, default=False)
    is_debit = Column(Boolean, default=True)        # True = money out
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
