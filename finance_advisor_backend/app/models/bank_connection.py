"""
app/models/bank_connection.py
─────────────────────────────
Stores Banca Transilvania PSD2 OAuth2 consent/token data per user.
"""
from sqlalchemy import Column, Integer, String, DateTime, Boolean, Text
from sqlalchemy.orm import DeclarativeBase
from datetime import datetime, timezone

from app.core.database import Base


class BTConnection(Base):
    __tablename__ = "bt_connections"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, nullable=False, index=True)
    consent_id = Column(String(256), nullable=True)
    access_token = Column(Text, nullable=True)
    refresh_token = Column(Text, nullable=True)
    token_expires_at = Column(DateTime(timezone=True), nullable=True)
    selected_accounts = Column(Text, nullable=True)   # JSON list of account IDs
    is_active = Column(Boolean, default=True)
    is_sandbox = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc),
                        onupdate=lambda: datetime.now(timezone.utc))
