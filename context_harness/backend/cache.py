"""Simple TTL cache implementation."""

import time
from typing import Any, Optional, Dict, Tuple


class SimpleCache:
    """Simple in-memory cache with TTL (time-to-live)."""

    def __init__(self, ttl_seconds: int = 300):
        """
        Initialize cache.

        Args:
            ttl_seconds: Time-to-live in seconds (default: 300 = 5 minutes)
        """
        self.ttl_seconds = ttl_seconds
        self._cache: Dict[str, Tuple[Any, float]] = {}

    def get(self, key: str) -> Optional[Any]:
        """
        Get cached value if not expired.

        Args:
            key: Cache key

        Returns:
            Cached value if exists and not expired, None otherwise
        """
        if key not in self._cache:
            return None

        value, timestamp = self._cache[key]

        # Check if expired
        if self._is_expired(timestamp):
            # Remove expired entry
            del self._cache[key]
            return None

        return value

    def set(self, key: str, value: Any) -> None:
        """
        Set cache value with current timestamp.

        Args:
            key: Cache key
            value: Value to cache
        """
        self._cache[key] = (value, time.time())

    def delete(self, key: str) -> None:
        """
        Delete cached value.

        Args:
            key: Cache key
        """
        if key in self._cache:
            del self._cache[key]

    def clear(self) -> None:
        """Clear all cached values."""
        self._cache.clear()

    def _is_expired(self, timestamp: float) -> bool:
        """
        Check if cached entry is expired.

        Args:
            timestamp: Creation timestamp of cached entry

        Returns:
            True if expired, False otherwise
        """
        return (time.time() - timestamp) > self.ttl_seconds

    def size(self) -> int:
        """Return number of cached entries (including expired)."""
        return len(self._cache)