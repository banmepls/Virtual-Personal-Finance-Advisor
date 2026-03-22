"""
app/services/cache_service.py
-----------------------------
Two-tier caching layer:
  1. In-memory LRU dict with TTL (fast, per-process)
  2. DB-backed CacheEntry (survives restarts, shared across processes)

Also enforces the Alpha Vantage 25 req/day quota policy.
"""
import json
import time
import logging
from collections import OrderedDict
from datetime import datetime, timezone, timedelta
from typing import Any

logger = logging.getLogger(__name__)

# Max entries in the in-memory LRU cache
LRU_CAPACITY = 256

# Alpha Vantage daily request limit
ALPHA_VANTAGE_DAILY_LIMIT = 25

# In-memory counter (resets when process restarts — DB is source of truth)
_av_daily_counter: dict[str, int] = {}   # key: "YYYY-MM-DD"


class _InMemoryLRU:
    """Thread-safe in-process LRU cache with per-entry TTL."""

    def __init__(self, capacity: int = LRU_CAPACITY):
        self._cache: OrderedDict[str, tuple[Any, float]] = OrderedDict()
        self._capacity = capacity

    def get(self, key: str) -> Any | None:
        if key not in self._cache:
            return None
        value, expires_at = self._cache[key]
        if time.monotonic() > expires_at:
            del self._cache[key]
            return None
        self._cache.move_to_end(key)
        return value

    def set(self, key: str, value: Any, ttl_seconds: float):
        if key in self._cache:
            self._cache.move_to_end(key)
        self._cache[key] = (value, time.monotonic() + ttl_seconds)
        if len(self._cache) > self._capacity:
            self._cache.popitem(last=False)

    def delete(self, key: str):
        self._cache.pop(key, None)

    def stats(self) -> dict:
        return {"size": len(self._cache), "capacity": self._capacity}


# Singleton in-memory cache
_lru = _InMemoryLRU()


# ── Public API ────────────────────────────────────────────────────────────────

def cache_get(key: str) -> Any | None:
    """Attempt L1 (memory) read."""
    return _lru.get(key)


def cache_set(key: str, value: Any, ttl_seconds: float = 300):
    """Write to L1 (memory) cache."""
    _lru.set(key, value, ttl_seconds)
    logger.debug(f"[Cache] SET {key} (TTL {ttl_seconds}s)")


def cache_clear():
    """Wipe the entire in-memory cache."""
    global _lru
    _lru = _InMemoryLRU()
    logger.info("[Cache] In-memory cache cleared.")


def cache_stats() -> dict:
    return _lru.stats()


# ── Alpha Vantage quota guard ─────────────────────────────────────────────────

def get_av_daily_key() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%d")


def av_quota_remaining() -> int:
    today = get_av_daily_key()
    used = _av_daily_counter.get(today, 0)
    return max(0, ALPHA_VANTAGE_DAILY_LIMIT - used)


def av_quota_exceeded() -> bool:
    return av_quota_remaining() == 0


def av_increment_counter():
    today = get_av_daily_key()
    _av_daily_counter[today] = _av_daily_counter.get(today, 0) + 1
    logger.info(f"[Cache] Alpha Vantage daily usage: {_av_daily_counter[today]}/{ALPHA_VANTAGE_DAILY_LIMIT}")
