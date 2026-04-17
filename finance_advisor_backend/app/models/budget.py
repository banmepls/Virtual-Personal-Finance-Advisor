"""
app/models/budget.py
─────────────────────
User-defined monthly budgets per spending category.
"""
from sqlalchemy import Column, Integer, String, Float, DateTime
from datetime import datetime, timezone

from app.core.database import Base


class Budget(Base):
    __tablename__ = "budgets"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, nullable=False, index=True)
    category = Column(String(64), nullable=False)   # e.g. "Food & Groceries"
    month_year = Column(String(7), nullable=False)  # e.g. "2026-04"
    limit_amount = Column(Float, nullable=False)
    currency = Column(String(8), default="RON")
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc),
                        onupdate=lambda: datetime.now(timezone.utc))
