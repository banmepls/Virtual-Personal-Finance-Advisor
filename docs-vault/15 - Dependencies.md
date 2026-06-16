# 📦 Dependencies

Tags: #dependencies #python #dart #requirements

## Python Backend Dependencies (`requirements.txt`)

| Package | Version | Purpose |
|---|---|---|
| **fastapi** | 0.135.1 | Web framework — async HTTP API |
| **uvicorn** | 0.41.0 | ASGI server |
| **uvloop** | 0.22.1 | Ultra-fast asyncio event loop (Linux/Mac) |
| **SQLAlchemy** | 2.0.48 | ORM with async support |
| **asyncpg** | 0.31.0 | PostgreSQL async driver |
| **alembic** | 1.18.4 | Database migration tool |
| **pydantic** | 2.12.5 | Data validation and serialization |
| **pydantic-settings** | 2.13.1 | Settings from environment |
| **cryptography** | 44.0.2 | AES-256-CBC encryption |
| **passlib[bcrypt]** | 1.7.4 | Password hashing |
| **python-jose[cryptography]** | 3.3.0 | JWT creation and verification |
| **hvac** | 2.1.0 | HashiCorp Vault Python client |
| **httpx** | 0.28.1 | Async HTTP client (eToro, BT API) |
| **yfinance** | 0.2.51 | Yahoo Finance market quotes & history (no API key) |
| **numpy** | 1.26.4 | Numerical arrays for ML features |
| **scikit-learn** | 1.5.2 | IsolationForest + OneClassSVM |
| **scipy** | 1.13.1 | Scientific computing support |
| **pandas** | 2.2.3 | Data manipulation |
| **langchain** | ≥0.3.7 | LLM orchestration framework |
| **langchain-core** | ≥1.0.0 | LangChain abstractions |
| **langchain-google-genai** | ≥2.0.0 | Google Gemini LangChain integration |
| **mcp** | ≥1.26.0 | Model Context Protocol + FastMCP |
| **python-dotenv** | 1.2.2 | `.env` file loading |
| **greenlet** | 3.3.2 | SQLAlchemy threading support |

### Key Constraints

- `numpy==1.26.4` — Pinned for sklearn compatibility
- `scikit-learn==1.5.2` — Stable release with IsolationForest, OneClassSVM
- No PyTorch/TensorFlow — Autoencoder uses numpy SVD (zero ML framework overhead)

---

## Flutter Dependencies (`pubspec.yaml`)

```yaml
name: finance_advisor_mobile
version: 1.0.0+1
environment:
  sdk: '>=3.0.0 <4.0.0'
```

| Package | Version | Purpose |
|---|---|---|
| **flutter** | SDK | Core framework |
| **cupertino_icons** | ^1.0.2 | iOS-style icons |
| **intl** | ^0.18.1 | Date/number internationalization |
| **fl_chart** | ^0.63.0 | Line charts, bar charts (OHLCV) |
| **google_fonts** | ^6.2.1 | Inter font family |
| **http** | ^1.1.0 | HTTP client for API calls |
| **provider** | ^6.1.0 | State management |
| **shared_preferences** | ^2.2.0 | Persistent JWT storage |
| **flutter_markdown** | ^0.7.2 | Markdown rendering in chat |
| **url_launcher** | ^6.3.2 | Open BT OAuth2 URL in browser |

### Dev Dependencies

| Package | Purpose |
|---|---|
| **flutter_test** | Testing framework |
| **flutter_lints** | Linting rules |

### Overrides

```yaml
dependency_overrides:
  path_provider_android: "2.2.22"
  # Prevents NativeCallable FFI crash (Dart 3.12 / objective_c 9.x)
```

---

## External APIs & Services

| Service | SDK/Protocol | Free Tier Limit |
|---|---|---|
| **Google Gemini** | `langchain-google-genai` | 15 RPM (free) |
| **Yahoo Finance** | `yfinance` library | No API key, no fixed quota (unofficial) |
| **eToro** | REST via `httpx` | Varies (public API) |
| **BT PSD2** | REST via `httpx` | Sandbox (unlimited) / Production (regulated) |
| **HashiCorp Vault** | `hvac` | Self-hosted |

---

## Python Standard Library Used

| Module | Usage |
|---|---|
| `asyncio` | Circuit breaker locks, async operations |
| `os` | Environment variables, random IV generation |
| `json` | BTConnection.selected_accounts serialization |
| `base64` | AES payload encoding, PKCE challenge |
| `time` | Monotonic clock for cache TTL |
| `collections.OrderedDict` | LRU cache backing structure |
| `collections.defaultdict` | Expense category aggregation |
| `dataclasses` | `VotingResult`, `CircuitBreakerConfig` |
| `enum` | `CBState` (CLOSED/OPEN/HALF_OPEN) |
| `re` | Transaction text pattern matching |
| `logging` | Structured application logging |
| `functools.lru_cache` | Settings singleton |

---

## Related Notes
- [[03 - FastAPI Application]]
- [[14 - Flutter Frontend]]
- [[01 - System Overview]]
