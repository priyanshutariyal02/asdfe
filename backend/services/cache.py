
import asyncio
import os
import time
from typing import Any, Awaitable, Callable


CACHE_TTL_SECONDS = int(
    os.getenv("CACHE_TTL_SECONDS", "3600")
)


class AsyncTTLCache:
    """Simple in-memory cache with expiration and safe copies."""

    def __init__(self, ttl_seconds: int = CACHE_TTL_SECONDS):
        if ttl_seconds <= 0:
            raise ValueError("Cache TTL must be greater than zero")

        self.ttl_seconds = ttl_seconds
        self._entries: dict[str, tuple[float, Any]] = {}
        self._lock = asyncio.Lock()

    async def get_or_set(
        self,
        key: str,
        factory: Callable[[], Awaitable[Any]],
    ) -> Any:
        async with self._lock:
            now = time.monotonic()
            entry = self._entries.get(key)

            if entry is not None:
                expires_at, value = entry
                if now < expires_at:
                    return value.copy(deep=True)

            value = await factory()

            self._entries[key] = (
                time.monotonic() + self.ttl_seconds,
                value.copy(deep=True),
            )

            return value.copy(deep=True)
