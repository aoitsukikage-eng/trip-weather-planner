"""In-memory TTL cache with stale retention and async single-flight primitive.

Phase 1 uses a process-local cache with deterministic fresh/stale/miss support.
Existing get() retains fresh-only compatibility.
"""

from __future__ import annotations

import asyncio
import inspect
import threading
import time
from collections.abc import Callable, Coroutine
from enum import StrEnum
from typing import Any, NamedTuple, TypeVar

T = TypeVar("T")


class CacheStatus(StrEnum):
    FRESH = "fresh"
    STALE = "stale"
    MISS = "miss"


class CacheEntry(NamedTuple):
    status: str
    value: Any | None = None

    @property
    def is_fresh(self) -> bool:
        return self.status == CacheStatus.FRESH.value

    @property
    def is_stale(self) -> bool:
        return self.status == CacheStatus.STALE.value

    @property
    def is_miss(self) -> bool:
        return self.status == CacheStatus.MISS.value


class TTLCache:
    def __init__(
        self,
        default_ttl: int = 1800,
        stale_retention: int = 3600,
        clock: Callable[[], float] = time.monotonic,
    ) -> None:
        self._default_ttl = default_ttl
        self._default_stale_retention = stale_retention
        self._clock = clock
        self._store: dict[str, tuple[float, float, Any]] = {}
        self._lock = threading.Lock()

    def get_entry(self, key: str) -> CacheEntry:
        """Lookup an item and determine whether it is fresh, stale, or miss."""
        with self._lock:
            item = self._store.get(key)
            if item is None:
                return CacheEntry(CacheStatus.MISS.value, None)
            fresh_until, stale_until, value = item
            now = self._clock()
            if now < fresh_until:
                return CacheEntry(CacheStatus.FRESH.value, value)
            if now < stale_until:
                return CacheEntry(CacheStatus.STALE.value, value)
            # Stale retention exceeded; lazy eviction.
            self._store.pop(key, None)
            return CacheEntry(CacheStatus.MISS.value, None)

    def get(self, key: str) -> Any | None:
        """Fresh-only get for backward compatibility."""
        with self._lock:
            item = self._store.get(key)
            if item is None:
                return None
            fresh_until, stale_until, value = item
            now = self._clock()
            if now < fresh_until:
                return value
            if now >= stale_until:
                # Lazy eviction only when past stale retention.
                self._store.pop(key, None)
            return None

    def get_with_status(self, key: str) -> tuple[str, Any | None]:
        """Convenience method returning (status, value)."""
        entry = self.get_entry(key)
        return entry.status, entry.value

    def lookup(self, key: str) -> CacheEntry:
        """Alias for get_entry."""
        return self.get_entry(key)

    def get_stale(self, key: str) -> Any | None:
        """Return the cached value if fresh or stale; otherwise None."""
        entry = self.get_entry(key)
        valid_statuses = (CacheStatus.FRESH.value, CacheStatus.STALE.value)
        return entry.value if entry.status in valid_statuses else None

    def set(
        self,
        key: str,
        value: Any,
        ttl: int | None = None,
        stale_retention: int | None = None,
    ) -> None:
        with self._lock:
            fresh_sec = ttl if ttl is not None else self._default_ttl
            stale_sec = (
                stale_retention
                if stale_retention is not None
                else self._default_stale_retention
            )
            now = self._clock()
            fresh_until = now + fresh_sec
            stale_until = fresh_until + stale_sec
            self._store[key] = (fresh_until, stale_until, value)

    def delete(self, key: str) -> bool:
        with self._lock:
            return self._store.pop(key, None) is not None

    def clear(self) -> None:
        with self._lock:
            self._store.clear()

    def __len__(self) -> int:
        with self._lock:
            return len(self._store)


class AsyncSingleFlight:
    """Per-key async single-flight primitive for coalescing concurrent calls."""

    def __init__(self) -> None:
        self._inflight: dict[str, asyncio.Task[Any]] = {}
        self._waiters: dict[str, int] = {}

    async def run(
        self,
        key: str,
        fn: Callable[..., Coroutine[Any, Any, T]] | Coroutine[Any, Any, T],
        *args: Any,
        **kwargs: Any,
    ) -> T:
        if key in self._inflight:
            if inspect.iscoroutine(fn):
                fn.close()
            task = self._inflight[key]
        else:
            coro = fn if inspect.iscoroutine(fn) else fn(*args, **kwargs)
            task = asyncio.create_task(coro)
            self._inflight[key] = task
            self._waiters[key] = 0

            def _cleanup(_: asyncio.Task[Any]) -> None:
                if self._inflight.get(key) is task:
                    del self._inflight[key]
                    self._waiters.pop(key, None)

            task.add_done_callback(_cleanup)

        self._waiters[key] = self._waiters.get(key, 0) + 1
        cancelled = False
        try:
            return await asyncio.shield(task)
        except asyncio.CancelledError:
            cancelled = True
            raise
        finally:
            remaining = self._waiters.get(key, 1) - 1
            self._waiters[key] = remaining
            if cancelled and remaining <= 0 and not task.done():
                task.cancel()

    def is_inflight(self, key: str) -> bool:
        return key in self._inflight

    def clear(self) -> None:
        self._inflight.clear()
        self._waiters.clear()
