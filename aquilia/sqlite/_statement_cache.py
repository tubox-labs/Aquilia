"""
Statement Cache — Per-connection LRU cache for prepared statements.

Caches the SQL text of recently executed statements to avoid re-parsing.
sqlite3 in Python doesn't expose ``sqlite3_prepare_v2`` directly, but
its statement cache (``cached_statements`` parameter on ``connect()``)
works at the C level.  This module tracks cache hits / misses at the
Python level for observability and manages a logical LRU to keep the
working set within bounds.
"""

from __future__ import annotations

from collections import OrderedDict
from dataclasses import dataclass, field
from typing import Any


__all__ = ["StatementCache", "CacheStats"]


@dataclass
class CacheStats:
    """Observable statistics for a statement cache."""

    hits: int = 0
    misses: int = 0
    evictions: int = 0
    size: int = 0
    capacity: int = 0

    @property
    def hit_rate(self) -> float:
        """Fraction of hits out of total accesses (0.0 – 1.0)."""
        total = self.hits + self.misses
        if total == 0:
            return 0.0
        return self.hits / total

    def snapshot(self) -> dict[str, Any]:
        """Return a JSON-friendly snapshot."""
        return {
            "hits": self.hits,
            "misses": self.misses,
            "evictions": self.evictions,
            "size": self.size,
            "capacity": self.capacity,
            "hit_rate": round(self.hit_rate, 4),
        }


class StatementCache:
    """
    LRU statement cache for tracking SQL statement reuse.

    This is a Python-level bookkeeping layer.  The actual sqlite3 C-level
    statement cache is configured via the ``cached_statements`` parameter
    in ``sqlite3.connect()``.  This class tracks which SQL texts have been
    seen recently and provides hit / miss counters for observability.

    Usage::

        cache = StatementCache(capacity=256)
        is_cached = cache.touch("SELECT * FROM users WHERE id = ?")
        # is_cached is False on first call (miss), True on subsequent (hit)

    The cache does **not** hold sqlite3 cursor objects — it only tracks
    SQL text strings to report metrics.  The actual prepared statement
    caching is handled by sqlite3's internal implementation.
    """

    __slots__ = ("_capacity", "_lru", "_stats")

    def __init__(self, capacity: int = 256) -> None:
        if capacity < 0:
            from aquilia.faults.domains import ConfigInvalidFault
            raise ConfigInvalidFault(
                key="sqlite.statement_cache.capacity",
                reason=f"capacity must be >= 0, got {capacity}",
            )
        self._capacity = capacity
        self._lru: OrderedDict[str, None] = OrderedDict()
        self._stats = CacheStats(capacity=capacity)

    @property
    def stats(self) -> CacheStats:
        """Current cache statistics."""
        return self._stats

    def touch(self, sql: str) -> bool:
        """
        Record an SQL statement access.

        If the statement was already in the cache, count as a hit and
        move to the front (most-recently-used).  Otherwise, count as a
        miss and insert; evict the LRU entry if over capacity.

        Args:
            sql: The SQL text string.

        Returns:
            True if the statement was already cached (hit),
            False if it was newly inserted (miss).
        """
        if self._capacity == 0:
            self._stats.misses += 1
            return False

        if sql in self._lru:
            self._lru.move_to_end(sql)
            self._stats.hits += 1
            return True

        # Miss — insert
        self._lru[sql] = None
        self._stats.misses += 1

        # Evict if over capacity
        while len(self._lru) > self._capacity:
            self._lru.popitem(last=False)
            self._stats.evictions += 1

        self._stats.size = len(self._lru)
        return False

    def clear(self) -> None:
        """Clear all cached statement entries."""
        self._lru.clear()
        self._stats.size = 0

    def __len__(self) -> int:
        return len(self._lru)

    def __contains__(self, sql: str) -> bool:
        return sql in self._lru

    def __repr__(self) -> str:
        return (
            f"StatementCache(size={len(self._lru)}, "
            f"capacity={self._capacity}, "
            f"hit_rate={self._stats.hit_rate:.2%})"
        )
