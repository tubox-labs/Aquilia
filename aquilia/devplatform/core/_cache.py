"""
aquilia.devplatform.core._cache — Small stdlib-only bounded LRU cache.

Mirrors ``aquilia.mcp.cache.LRUCache``'s shape, but importing that module
pulls in ``aquilia/mcp/__init__.py``'s heavier indexer/server dependency
chain. This is a standalone, dependency-free equivalent for ADP's own
process-lifetime caches (e.g. the hot-reload import-graph memo).
"""

from __future__ import annotations

from collections import OrderedDict
from dataclasses import dataclass, field
from typing import Generic, TypeVar

K = TypeVar("K")
V = TypeVar("V")


@dataclass
class BoundedCache(Generic[K, V]):
    """Fixed-capacity, least-recently-used eviction cache."""

    max_size: int = 512
    _items: OrderedDict[K, V] = field(default_factory=OrderedDict, init=False, repr=False)

    def get(self, key: K) -> V | None:
        """Return the cached value for ``key``, or ``None`` if absent."""
        if key not in self._items:
            return None
        value = self._items.pop(key)
        self._items[key] = value
        return value

    def set(self, key: K, value: V) -> None:
        """Store ``value`` under ``key``, evicting the oldest entry if over capacity."""
        if key in self._items:
            self._items.pop(key)
        self._items[key] = value
        while len(self._items) > self.max_size:
            self._items.popitem(last=False)

    def __len__(self) -> int:
        return len(self._items)

    def __contains__(self, key: K) -> bool:
        return key in self._items
