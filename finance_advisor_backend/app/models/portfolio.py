from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import Float, DateTime, ForeignKey, Integer
from datetime import datetime, timezone
from app.core.database import Base


class PortfolioPosition(Base):
    """
    Represents a user's position in a specific asset at a point in time.
    """
    __tablename__ = "portfolio_positions"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    asset_id: Mapped[int] = mapped_column(ForeignKey("assets.id"), index=True)
    quantity: Mapped[float] = mapped_column(Float)
    avg_buy_price: Mapped[float] = mapped_column(Float)
    current_value: Mapped[float] = mapped_column(Float)
    unrealized_pnl: Mapped[float] = mapped_column(Float, default=0.0)
    recorded_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc)
    )

    # Relationships
    user: Mapped["User"] = relationship(back_populates="portfolio_positions")
    asset: Mapped["Asset"] = relationship(back_populates="portfolio_positions")
