from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import String, Text, DateTime
from datetime import datetime, timezone
from app.core.database import Base


class CacheEntry(Base):
    """
    Persistent cache for API responses.
    Used to enforce Alpha Vantage 25 req/day policy
    and to survive process restarts.
    """
    __tablename__ = "cache_entries"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    cache_key: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    payload: Mapped[str] = mapped_column(Text)  # JSON serialized
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc)
    )
