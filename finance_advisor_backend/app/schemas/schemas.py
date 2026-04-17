"""Pydantic schemas for API request/response validation."""
from pydantic import BaseModel, EmailStr, field_validator
from typing import Optional, List
from datetime import datetime, date


# ── Auth schemas ──────────────────────────────────────────────────────────────
class UserRegisterRequest(BaseModel):
    username: str
    email: str
    password: str
    etoro_nickname: Optional[str] = None

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


class UserRegisterResponse(BaseModel):
    user: UserResponse
    bt_consent_id: Optional[str] = None
    bt_message: Optional[str] = None


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


# ── Bank (BT PSD2) schemas ────────────────────────────────────────────────────
class BankAccountResponse(BaseModel):
    resource_id: str
    iban: str
    currency: str
    name: str
    status: str


class BankBalanceAmount(BaseModel):
    currency: str
    amount: str


class BankBalanceItem(BaseModel):
    balance_type: str
    balance_amount: BankBalanceAmount


class BankBalanceResponse(BaseModel):
    account_id: str
    iban: str
    balances: List[BankBalanceItem]


class BankTransactionResponse(BaseModel):
    id: int
    transaction_id: str
    booking_date: Optional[date]
    amount: float
    currency: str
    creditor_name: Optional[str]
    debtor_name: Optional[str]
    remittance_info: Optional[str]
    category: str
    is_recurring: bool
    is_debit: bool

    class Config:
        from_attributes = True


class SpendingSummaryResponse(BaseModel):
    month_year: str
    categories: dict
    total_spent: float
    currency: str = "RON"


class SubscriptionResponse(BaseModel):
    merchant: str
    amount: float
    currency: str
    category: str
    last_charge: str
    frequency: str


class BankConnectResponse(BaseModel):
    consent_id: str
    is_sandbox: bool
    message: str


# ── Budget schemas ────────────────────────────────────────────────────────────
class BudgetCreateRequest(BaseModel):
    category: str
    month_year: str   # YYYY-MM
    limit_amount: float
    currency: str = "RON"


class BudgetResponse(BaseModel):
    id: int
    category: str
    month_year: str
    limit_amount: float
    currency: str
    created_at: datetime

    class Config:
        from_attributes = True


class BudgetStatusItem(BaseModel):
    category: str
    limit_amount: float
    spent_amount: float
    remaining: float
    percentage_used: float
    currency: str
    status: str   # "ok", "warning", "exceeded"


class BudgetStatusResponse(BaseModel):
    month_year: str
    budgets: List[BudgetStatusItem]


# ── Expense insights schemas ──────────────────────────────────────────────────
class ExpenseInsightResponse(BaseModel):
    month_year: str
    ai_summary: str
    top_category: str
    total_spent: float
    currency: str = "RON"
