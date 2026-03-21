"""Pydantic schemas for API request/response validation."""
from pydantic import BaseModel, EmailStr, field_validator
from typing import Optional
from datetime import datetime


# ── Auth schemas ──────────────────────────────────────────────────────────────
class UserRegisterRequest(BaseModel):
    username: str
    email: str
    password: str

    @field_validator("password")
    @classmethod
    def password_strength(cls, v):
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters")
        return v


class UserLoginRequest(BaseModel):
    username: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class UserResponse(BaseModel):
    id: int
    username: str
    email: str
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True


# ── Portfolio / Position schemas ──────────────────────────────────────────────
class PositionInput(BaseModel):
    instrument_id: int
    quantity: float
    avg_buy_price: Optional[float] = 0.0
    current_value: Optional[float] = 0.0
    unrealized_pnl: Optional[float] = 0.0

    @field_validator("quantity")
    @classmethod
    def quantity_positive(cls, v):
        if v < 0:
            raise ValueError("Quantity cannot be negative")
        return v


class AnomalyAnalyzeRequest(BaseModel):
    positions: list[PositionInput]
    user_id: Optional[int] = None


# ── Anomaly response schemas ──────────────────────────────────────────────────
class AnomalyResult(BaseModel):
    isolation_score: float
    autoencoder_mse: float
    svm_score: float
    weighted_avg_score: float
    is_anomaly: bool
    confidence: str
    notes: str


class AnomalyHistoryItem(BaseModel):
    id: int
    isolation_score: float
    autoencoder_mse: float
    svm_score: float
    weighted_avg_score: float
    is_anomaly: bool
    notes: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True


# ── Health schema ─────────────────────────────────────────────────────────────
class HealthResponse(BaseModel):
    status: str
    circuit_breakers: list[dict]
    cache_stats: dict
    alpha_vantage_quota: dict
    timestamp: datetime
