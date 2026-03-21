"""
app/core/circuit_breaker.py
---------------------------
Simple async-safe Circuit Breaker implementation.

States:
  CLOSED   → Normal operation; failures are counted.
  OPEN     → Failures exceeded threshold; calls are rejected immediately.
  HALF_OPEN→ Testing if the service recovered; one probe call allowed.

Usage:
    cb = CircuitBreaker("etoro")
    async with cb:
        response = await httpx_client.get(url)
"""
import asyncio
import time
import logging
from enum import Enum
from dataclasses import dataclass, field
from typing import Callable, Awaitable

logger = logging.getLogger(__name__)


class CBState(str, Enum):
    CLOSED = "CLOSED"
    OPEN = "OPEN"
    HALF_OPEN = "HALF_OPEN"


@dataclass
class CircuitBreakerConfig:
    failure_threshold: int = 5       # failures before opening
    recovery_timeout: float = 60.0   # seconds before trying HALF_OPEN
    success_threshold: int = 2       # successes in HALF_OPEN to close again


class CircuitBreakerOpen(Exception):
    """Raised when a call is attempted while the circuit is OPEN."""
    pass


class CircuitBreaker:
    def __init__(self, name: str, config: CircuitBreakerConfig | None = None):
        self.name = name
        self.config = config or CircuitBreakerConfig()
        self._state = CBState.CLOSED
        self._failure_count = 0
        self._success_count = 0
        self._last_failure_time: float = 0.0
        self._lock = asyncio.Lock()

    @property
    def state(self) -> CBState:
        return self._state

    def status_dict(self) -> dict:
        return {
            "name": self.name,
            "state": self._state.value,
            "failure_count": self._failure_count,
            "last_failure_time": self._last_failure_time,
        }

    async def _check_state(self):
        async with self._lock:
            if self._state == CBState.OPEN:
                elapsed = time.monotonic() - self._last_failure_time
                if elapsed >= self.config.recovery_timeout:
                    logger.info(f"[CB:{self.name}] Transitioning OPEN → HALF_OPEN")
                    self._state = CBState.HALF_OPEN
                    self._success_count = 0
                else:
                    raise CircuitBreakerOpen(
                        f"Circuit breaker '{self.name}' is OPEN. "
                        f"Retry in {self.config.recovery_timeout - elapsed:.1f}s"
                    )

    async def _on_success(self):
        async with self._lock:
            if self._state == CBState.HALF_OPEN:
                self._success_count += 1
                if self._success_count >= self.config.success_threshold:
                    logger.info(f"[CB:{self.name}] Transitioning HALF_OPEN → CLOSED")
                    self._state = CBState.CLOSED
                    self._failure_count = 0
            elif self._state == CBState.CLOSED:
                self._failure_count = 0

    async def _on_failure(self):
        async with self._lock:
            self._failure_count += 1
            self._last_failure_time = time.monotonic()
            if (self._state == CBState.CLOSED and
                    self._failure_count >= self.config.failure_threshold):
                logger.warning(f"[CB:{self.name}] Transitioning CLOSED → OPEN after {self._failure_count} failures")
                self._state = CBState.OPEN
            elif self._state == CBState.HALF_OPEN:
                logger.warning(f"[CB:{self.name}] Probe failed, back to OPEN")
                self._state = CBState.OPEN
                self._success_count = 0

    async def call(self, coro_func: Callable[[], Awaitable]):
        """Execute an async callable with circuit breaker protection."""
        await self._check_state()
        try:
            result = await coro_func()
            await self._on_success()
            return result
        except Exception as exc:
            await self._on_failure()
            raise exc


# ── Global registry ──────────────────────────────────────────────────────────
_breakers: dict[str, CircuitBreaker] = {}


def get_circuit_breaker(name: str) -> CircuitBreaker:
    if name not in _breakers:
        _breakers[name] = CircuitBreaker(name)
    return _breakers[name]


def all_circuit_breaker_statuses() -> list[dict]:
    return [cb.status_dict() for cb in _breakers.values()]
