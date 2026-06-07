# 💾 Cache Service

Tags: #cache #lru #performance #alpha-vantage

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

---

## Alpha Vantage Quota Guard

Alpha Vantage's free tier allows **25 requests/day**. The cache service enforces this:

```python
ALPHA_VANTAGE_DAILY_LIMIT = 25

# In-memory counter per calendar day (UTC)
_av_daily_counter: dict[str, int] = {}   # {"2026-06-07": 12, ...}

def av_quota_remaining() -> int:
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    used = _av_daily_counter.get(today, 0)
    return max(0, 25 - used)

def av_quota_exceeded() -> bool:
    return av_quota_remaining() == 0

def av_increment_counter():
    today = get_av_daily_key()
    _av_daily_counter[today] = _av_daily_counter.get(today, 0) + 1
```

> **Note:** The in-memory counter resets when the process restarts. The DB is the source of truth for persistent quota tracking. Old day entries accumulate harmlessly (only today's entry is checked).

---

## Cache Keys (Conventions)

| Key Pattern | Data | TTL |
|---|---|---|
| `quote:{symbol}` | Alpha Vantage stock quote | 300s |
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
  },
  "alpha_vantage_quota": {
    "daily_limit": 25,
    "remaining": 13,
    "exceeded": false
  }
}
```

---

## Related Notes
- [[11 - Fault Tolerance]]
- [[03 - FastAPI Application]]
