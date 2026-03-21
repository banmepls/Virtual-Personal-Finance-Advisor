from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import String, Boolean, DateTime, Text
from datetime import datetime, timezone
from app.core.database import Base


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    username: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    hashed_password: Mapped[str] = mapped_column(String(255))
    # AES-256-GCM encrypted eToro user key (stored as hex string)
    encrypted_etoro_key: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc)
    )

    # Relationships
    portfolio_positions: Mapped[list["PortfolioPosition"]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )
    anomaly_logs: Mapped[list["AnomalyLog"]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )
