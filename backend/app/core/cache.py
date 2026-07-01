"""Minimal in-memory TTL cache.

Phase 1 uses a process-local cache to keep the deployable MVP lean (no Redis to
provision). The architecture diagram shows Redis as the production target; the
interface here (get/set) is deliberately swap-compatible with a Redis client.
"""

from __future__ import annotations

import threading
import time
from typing import Any


class TTLCache:
    def __init__(self, default_ttl: int = 1800) -> None:
        self._default_ttl = default_ttl
        self._store: dict[str, tuple[float, Any]] = {}
        self._lock = threading.Lock()

    def get(self, key: str) -> Any | None:
        with self._lock:
            item = self._store.get(key)
            if item is None:
                return None
            expires_at, value = item
            if time.monotonic() >= expires_at:
                # Lazy eviction of expired entries.
                self._store.pop(key, None)
                return None
            return value

    def set(self, key: str, value: Any, ttl: int | None = None) -> None:
        with self._lock:
            expires_at = time.monotonic() + (ttl if ttl is not None else self._default_ttl)
            self._store[key] = (expires_at, value)

    def clear(self) -> None:
        with self._lock:
            self._store.clear()
