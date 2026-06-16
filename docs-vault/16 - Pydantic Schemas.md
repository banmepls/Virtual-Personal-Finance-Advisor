# 📋 Pydantic Schemas

Tags: #schemas #pydantic #api #validation

## Overview

All request/response validation is handled by **Pydantic v2** schemas defined in `app/schemas/schemas.py`.

---

## Authentication Schemas

### `UserRegisterRequest`
```python
class UserRegisterRequest(BaseModel):
    username: str
    email: str
    password: str                     # Validated: min 8 chars
    etoro_nickname: Optional[str] = None

    @field_validator("password")
    def password_strength(cls, v):
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters")
        return v
```

### `UserLoginRequest`
```python
class UserLoginRequest(BaseModel):
    username: str
    password: str
```

### `TokenResponse`
```python
class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
```

### `UserResponse`
```python
class UserResponse(BaseModel):
    id: int
    username: str
    email: str
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True     # ORM mode
```

### `UserRegisterResponse`
```python
class UserRegisterResponse(BaseModel):
    user: UserResponse
    bt_consent_id: Optional[str] = None
    bt_message: Optional[str] = None
```

---

## Anomaly Detection Schemas

### `PositionInput`
```python
class PositionInput(BaseModel):
    instrument_id: int
    quantity: float               # Validated: must be >= 0
    avg_buy_price: Optional[float] = 0.0
    current_value: Optional[float] = 0.0
    unrealized_pnl: Optional[float] = 0.0
```

### `AnomalyAnalyzeRequest`
```python
class AnomalyAnalyzeRequest(BaseModel):
    positions: list[PositionInput]
    user_id: Optional[int] = None     # If set, result is saved to AnomalyLog
```

### `AnomalyResult`
```python
class AnomalyResult(BaseModel):
    isolation_score: float          # [0, 1]
    autoencoder_mse: float          # [0, 1]
    svm_score: float                # [0, 1]
    weighted_avg_score: float       # [0, 1]
    is_anomaly: bool
    confidence: str                 # "HIGH" | "MEDIUM" | "LOW"
    notes: str                      # Breakdown string
```

### `AnomalyHistoryItem`
```python
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
```

---

## Health Schema

### `HealthResponse`
```python
class HealthResponse(BaseModel):
    status: str                     # "healthy" | "degraded"
    circuit_breakers: list[dict]    # [{name, state, failure_count, ...}]
    cache_stats: dict               # {size, capacity, db_connected}
    timestamp: datetime
```

---

## Bank / BT PSD2 Schemas

### `BankAccountResponse`
```python
class BankAccountResponse(BaseModel):
    resource_id: str
    iban: str
    currency: str
    name: str
    status: str
    product: Optional[str] = None
    cash_account_type: Optional[str] = None
```

### `BankBalanceResponse`
```python
class BankBalanceResponse(BaseModel):
    account_id: str
    iban: str
    balances: List[BankBalanceItem]

class BankBalanceItem(BaseModel):
    balance_type: str              # e.g. "closingBooked"
    balance_amount: BankBalanceAmount
    credit_limit_included: Optional[bool]
    reference_date: Optional[str]

class BankBalanceAmount(BaseModel):
    currency: str
    amount: str                   # String from BT API
```

### `BankTransactionResponse`
```python
class BankTransactionResponse(BaseModel):
    id: int
    transaction_id: str
    booking_date: Optional[date]
    amount: float                  # Negative = debit
    currency: str
    creditor_name: Optional[str]
    debtor_name: Optional[str]
    remittance_info: Optional[str]
    category: str
    is_recurring: bool
    is_debit: bool

    class Config:
        from_attributes = True
```

### `SpendingSummaryResponse`
```python
class SpendingSummaryResponse(BaseModel):
    month_year: str                # "YYYY-MM"
    categories: dict               # {"Food & Groceries": 650.0, ...}
    total_spent: float
    currency: str = "RON"
```

### `SubscriptionResponse`
```python
class SubscriptionResponse(BaseModel):
    merchant: str
    amount: float
    currency: str
    category: str
    last_charge: str               # "YYYY-MM-DD"
    frequency: str                 # "monthly"
```

### `BankConnectResponse`
```python
class BankConnectResponse(BaseModel):
    consent_id: str
    is_sandbox: bool
    message: str
    auth_url: Optional[str] = None  # None if already authorized
```

---

## Budget Schemas

### `BudgetCreateRequest`
```python
class BudgetCreateRequest(BaseModel):
    category: str              # e.g. "Food & Groceries"
    month_year: str            # "YYYY-MM"
    limit_amount: float
    currency: str = "RON"
```

### `BudgetStatusItem`
```python
class BudgetStatusItem(BaseModel):
    budget_id: int             # used by the UI to delete a budget by id
    category: str
    limit_amount: float
    spent_amount: float
    remaining: float
    percentage_used: float
    currency: str
    status: str                # "ok" | "warning" | "exceeded"
```

---

## Expense Schemas

### `ExpenseInsightResponse`
```python
class ExpenseInsightResponse(BaseModel):
    month_year: str
    ai_summary: str            # Gemini-generated narrative
    top_category: str          # Highest spending category
    total_spent: float
    currency: str = "RON"
```

---

## Schema Validation Rules Summary

| Schema | Field | Validation |
|---|---|---|
| `UserRegisterRequest` | `password` | Min length 8 |
| `PositionInput` | `quantity` | Must be ≥ 0 |
| `BudgetCreateRequest` | `month_year` | Expected format "YYYY-MM" (not enforced by Pydantic) |

---

## Related Notes
- [[04 - API Endpoints Reference]]
- [[03 - FastAPI Application]]
- [[05 - Database Models]]
