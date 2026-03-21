from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import Float, Boolean, DateTime, ForeignKey, Text
from datetime import datetime, timezone
from app.core.database import Base


class AnomalyLog(Base):
    """
    Records results of anomaly detection ensemble voting for auditing and history.
    """
    __tablename__ = "anomaly_logs"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)

    # Individual model anomaly scores (normalized 0.0–1.0)
    isolation_score: Mapped[float] = mapped_column(Float)
    autoencoder_mse: Mapped[float] = mapped_column(Float)
    svm_score: Mapped[float] = mapped_column(Float)

    # Weighted ensemble result
    weighted_avg_score: Mapped[float] = mapped_column(Float)
    is_anomaly: Mapped[bool] = mapped_column(Boolean)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc)
    )

    user: Mapped["User"] = relationship(back_populates="anomaly_logs")
