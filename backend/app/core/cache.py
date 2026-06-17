from __future__ import annotations

import json
import time
from dataclasses import dataclass
from typing import Any

from app.core.config import get_settings


@dataclass
class CacheItem:
    value: str
    expires_at: float


class TtlCache:
    """Small process-local TTL cache.

    This is intentionally tiny for local/dev/test. In production, keep the interface and
    back it with Redis so cache survives process restarts and works across replicas.
    """

    def __init__(self) -> None:
        self._data: dict[str, CacheItem] = {}

    def get_json(self, key: str) -> Any | None:
        item = self._data.get(key)
        if not item:
            return None
        if item.expires_at < time.time():
            self._data.pop(key, None)
            return None
        return json.loads(item.value)

    def set_json(self, key: str, value: Any, ttl_seconds: int | None = None) -> None:
        ttl = ttl_seconds or get_settings().CACHE_TTL_SECONDS
        self._data[key] = CacheItem(value=json.dumps(value), expires_at=time.time() + ttl)

    def delete_prefix(self, prefix: str) -> None:
        for key in list(self._data.keys()):
            if key.startswith(prefix):
                self._data.pop(key, None)

    def clear(self) -> None:
        self._data.clear()


cache = TtlCache()
