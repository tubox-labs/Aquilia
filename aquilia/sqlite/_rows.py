"""
SQLite Row — Dict-like row with attribute access.

Provides a lightweight row object that supports:
- Integer index access:  ``row[0]``
- String key access:     ``row["name"]``
- Attribute access:      ``row.name``
- Iteration, len, dict conversion, repr
"""

from __future__ import annotations

from collections.abc import Iterator
from typing import Any

__all__ = ["Row", "row_factory"]


class Row(dict):
    """
    Immutable row object returned by query methods that also acts as a dict.

    Supports dict-like access (by column name), index access (by position),
    and attribute access for convenience.
    """

    __slots__ = ("_keys", "_values")

    def __init__(self, keys: tuple[str, ...], values: tuple[Any, ...]) -> None:
        super().__init__(zip(keys, values))
        object.__setattr__(self, "_keys", keys)
        object.__setattr__(self, "_values", values)

    # ── Dict-like access ─────────────────────────────────────────────

    def __getitem__(self, key: str | int) -> Any:
        if isinstance(key, int):
            return self._values[key]
        return super().__getitem__(key)

    # ── Attribute access ─────────────────────────────────────────────

    def __getattr__(self, name: str) -> Any:
        try:
            return self[name]
        except KeyError:
            raise AttributeError(f"'Row' object has no attribute {name!r}") from None

    def __setattr__(self, name: str, value: Any) -> None:
        raise AttributeError("Row objects are immutable")

    def __setitem__(self, key: Any, value: Any) -> None:
        raise TypeError("Row objects are immutable")

    def __delitem__(self, key: Any) -> None:
        raise TypeError("Row objects are immutable")

    def pop(self, key: Any, *args: Any) -> Any:
        raise TypeError("Row objects are immutable")

    def popitem(self) -> Any:
        raise TypeError("Row objects are immutable")

    def clear(self) -> None:
        raise TypeError("Row objects are immutable")

    def update(self, *args: Any, **kwargs: Any) -> None:
        raise TypeError("Row objects are immutable")

    # ── Collection interface ─────────────────────────────────────────

    def keys(self) -> tuple[str, ...]:
        """Return column names."""
        return self._keys

    def values(self) -> tuple[Any, ...]:
        """Return column values."""
        return self._values

    def items(self) -> tuple[tuple[str, Any], ...]:
        """Return (key, value) pairs."""
        return tuple(zip(self._keys, self._values, strict=False))

    def to_dict(self) -> dict[str, Any]:
        """Convert to a plain dictionary."""
        return dict(self)

    # ── Dunder protocols ─────────────────────────────────────────────

    def __len__(self) -> int:
        return len(self._values)

    def __iter__(self) -> Iterator[Any]:
        return iter(self._values)

    def __eq__(self, other: object) -> bool:
        if isinstance(other, Row):
            return self._keys == other._keys and self._values == other._values
        if isinstance(other, dict):
            return dict(self) == other
        return NotImplemented

    def __hash__(self) -> int:
        return hash((self._keys, self._values))

    def __repr__(self) -> str:
        pairs = ", ".join(f"{k}={v!r}" for k, v in zip(self._keys, self._values, strict=False))
        return f"Row({pairs})"


# ═══════════════════════════════════════════════════════════════════════════
# sqlite3 Row Factory
# ═══════════════════════════════════════════════════════════════════════════


# Column-name cache for row_factory, keyed by id(cursor.description).
#
# The value keeps a strong reference to the description tuple itself, which is
# what makes the id() key sound: while the entry lives, that address cannot be
# recycled by a different tuple, so a hit cannot alias a stale result set. The
# `is` re-check costs ~3 ns and covers the one window where it could (a hit
# recorded, then _clear()ed, then a new tuple landing on the freed address).
#
# Attaching the cache to the cursor -- the lower-hazard option -- is not
# available: sqlite3.Cursor is a C type with no __dict__, so `cursor._aq_keys`
# raises AttributeError.
_KEY_CACHE: dict[int, tuple[tuple[Any, ...], tuple[str, ...]]] = {}

# ponytail: flat cap + clear rather than an LRU. Entries are one small tuple
# pair per distinct in-flight statement; an app would need 512 concurrently
# live cursors to ever trip it. Swap in an LRU only if that stops being true.
_KEY_CACHE_MAX = 512


def row_factory(cursor: Any, row_tuple: tuple[Any, ...]) -> Row:
    """
    ``sqlite3`` row factory function.

    Assign to ``connection.row_factory = row_factory`` to get :class:`Row`
    objects from all queries.

    Args:
        cursor: The sqlite3 cursor (used for ``description``).
        row_tuple: The raw row tuple from sqlite3.

    Returns:
        A :class:`Row` instance.

    Performance:
        ``cursor.description`` is a fresh tuple per statement but constant
        across every row of that statement, so rebuilding the key tuple per row
        is O(columns) of pure waste -- measured ~200 ns/row at 8 columns, paid
        before hydration even begins. Cached per description object instead.
    """
    desc = cursor.description
    entry = _KEY_CACHE.get(id(desc))
    if entry is not None and entry[0] is desc:
        return Row(entry[1], row_tuple)

    keys = tuple(d[0] for d in desc)
    if len(_KEY_CACHE) >= _KEY_CACHE_MAX:
        _KEY_CACHE.clear()
    _KEY_CACHE[id(desc)] = (desc, keys)
    return Row(keys, row_tuple)
