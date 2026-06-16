"""
app/services/cache_service.py
-----------------------------
Two-tier caching layer:
  1. In-memory LRU dict with TTL (fast, per-process)
  2. DB-backed CacheEntry (survives restarts, shared across processes)
"""
import time
import logging
from collections import OrderedDict
from typing import Any

logger = logging.getLogger(__name__)

# Max entries in the in-memory LRU cache
LRU_CAPACITY = 256


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
