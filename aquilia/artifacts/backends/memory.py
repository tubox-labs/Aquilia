"""
MemoryBackend — In-process ephemeral artifact storage.

Used for:
- Tests (no disk I/O, no cleanup required)
- Ephemeral/derived artifacts that don't need durability
- ``on_corrupt="reset"`` policy testing

Not thread/process-safe; does not take locks.  If you need shared
in-process storage with concurrency control, use the default
``JSONFileBackend`` with ``AsyncFileLock``.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any


class MemoryBackend:
    """
    In-memory artifact backend.

    Data is stored in a plain dict keyed by file path string.
    All read/write operations are synchronous; the async wrappers are
    thin coroutine wrappers that return immediately.
    """

    def __init__(self) -> None:
        self._store: dict[str, dict[str, Any]] = {}

    # ------------------------------------------------------------------
    # Sync interface
    # ------------------------------------------------------------------

    def read_sync(self, path: Path, **_kwargs: Any) -> dict[str, Any] | None:
        """Return stored data for ``path``, or ``None`` if absent."""
        return self._store.get(str(path))

    def write_sync(self, path: Path, data: dict[str, Any], **_kwargs: Any) -> None:
        """Store ``data`` for ``path``."""
        import copy

        self._store[str(path)] = copy.deepcopy(data)

    def delete_sync(self, path: Path) -> bool:
        """Remove ``path`` from the store.  Returns ``True`` if it was present."""
        return self._store.pop(str(path), None) is not None

    # ------------------------------------------------------------------
    # Async interface
    # ------------------------------------------------------------------

    async def read(self, path: Path, **kwargs: Any) -> dict[str, Any] | None:
        return self.read_sync(path, **kwargs)

    async def write(self, path: Path, data: dict[str, Any], **kwargs: Any) -> None:
        self.write_sync(path, data, **kwargs)

    async def delete(self, path: Path) -> bool:
        return self.delete_sync(path)

    # ------------------------------------------------------------------
    # Test helpers
    # ------------------------------------------------------------------

    def clear(self) -> None:
        """Remove all stored artifacts."""
        self._store.clear()

    def keys(self) -> list[str]:
        """Return all stored path strings."""
        return list(self._store.keys())

    def __len__(self) -> int:
        return len(self._store)
