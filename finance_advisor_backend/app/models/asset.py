from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import String, Float, DateTime, Integer
from datetime import datetime, timezone
from app.core.database import Base


class Asset(Base):
    """
    Represents a tradable instrument on eToro.
    instrument_id is the numeric ID used internally by eToro's API.
    """
    __tablename__ = "assets"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    instrument_id: Mapped[int] = mapped_column(Integer, unique=True, index=True)
    symbol: Mapped[str] = mapped_column(String(20), index=True)
    name: Mapped[str] = mapped_column(String(255))
    asset_class: Mapped[str] = mapped_column(String(50))  # e.g. "Stocks", "Crypto", "Forex"
    last_price: Mapped[float | None] = mapped_column(Float, nullable=True)
    last_updated: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    # Relationships
    portfolio_positions: Mapped[list["PortfolioPosition"]] = relationship(
        back_populates="asset"
    )
