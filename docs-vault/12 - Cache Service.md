# 💾 Cache Service

Tags: #cache #lru #performance #market-data

## Architecture

The cache layer is implemented in `app/services/cache_service.py` as a two-tier system:

```
Request
  │
  ▼
L1: In-Memory LRU (256 entries, TTL per entry)  ← fast, volatile
  │ miss
  ▼
L2: DB-backed CacheEntry table                   ← slower, persistent
  │ miss
  ▼
External API Call
  │
  └── update both L1 + L2
```

---

## L1 — In-Memory LRU

```python
class _InMemoryLRU:
    def __init__(self, capacity: int = 256):
        self._cache: OrderedDict[str, tuple[Any, float]] = OrderedDict()
        self._capacity = capacity

    def get(self, key: str) -> Any | None:
        if key not in self._cache: return None
        value, expires_at = self._cache[key]
        if time.monotonic() > expires_at:
            del self._cache[key]   # Lazy TTL eviction
            return None
        self._cache.move_to_end(key)   # Promote to MRU
        return value

    def set(self, key: str, value: Any, ttl_seconds: float):
        if key in self._cache:
            self._cache.move_to_end(key)
        self._cache[key] = (value, time.monotonic() + ttl_seconds)
        if len(self._cache) > self._capacity:
            self._cache.popitem(last=False)   # Evict LRU entry
```

### Characteristics

| Property | Value |
|---|---|
| Capacity | 256 entries (configurable via `LRU_CAPACITY`) |
| TTL check | Lazy (on read) — no background cleanup thread |
| Eviction | LRU via `OrderedDict.move_to_end()` |
| Default TTL | 300 seconds (5 minutes) |
| Thread safety | Single-process asyncio — no lock needed |

---

## Public API

```python
# Read from L1
cache_get(key: str) -> Any | None

# Write to L1 with TTL
cache_set(key: str, value: Any, ttl_seconds: float = 300)

# Wipe L1 entirely
cache_clear()

# Get stats dict: {size: int, capacity: int}
cache_stats() -> dict
```

> **Note:** The market-data source is now **Yahoo Finance** (`yfinance`), which has no fixed daily request quota — so the previous Alpha Vantage quota guard (`ALPHA_VANTAGE_DAILY_LIMIT`, `av_quota_*`, daily counter) has been **removed**. Market resilience now relies solely on the cache + circuit breaker.

---

## Cache Keys (Conventions)

| Key Pattern | Data | TTL |
|---|---|---|
| `quote:{symbol}` | Yahoo Finance stock quote | 3600s |
| `portfolio:{user_id}` | eToro portfolio | 300s |
| `instruments` | eToro instrument list | 3600s |

---

## Health Exposure

Cache stats are included in the `/health` response:

```json
{
  "cache_stats": {
    "size": 12,
    "capacity": 256,
    "db_connected": true
  }
}
```

---

## Related Notes
- [[11 - Fault Tolerance]]
- [[03 - FastAPI Application]]
