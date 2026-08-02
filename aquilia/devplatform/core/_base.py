"""
aquilia.devplatform.core._base — Shared singleton mixin for ADP state stores.

Several ADP modules (RuntimeStateStore, WebSocketTracker, EventLoopMonitor,
MemoryUsageTracker, SQLQueryAnalyzer, StateBridgeRegistry) each implement the
same thread-safe double-checked-locking singleton pattern. This mixin
extracts that boilerplate to a single place.
"""

from __future__ import annotations

import threading
from typing import ClassVar, TypeVar

T = TypeVar("T", bound="SingletonMixin")


class SingletonMixin:
    """
    Thread-safe singleton mixin using double-checked locking.

    Subclasses must be default-constructable (``__init__(self)`` with no
    required arguments) to use ``get_instance()``.

    Usage::

        class MyStore(SingletonMixin):
            def __init__(self) -> None:
                self._data = {}

        store = MyStore.get_instance()
    """

    _instance: ClassVar[object | None] = None
    _creation_lock: ClassVar[threading.Lock] = threading.Lock()

    @classmethod
    def get_instance(cls: type[T]) -> T:
        """Return the process-wide singleton instance, creating it if needed."""
        if cls.__dict__.get("_instance") is None:
            with cls._creation_lock:
                if cls.__dict__.get("_instance") is None:
                    cls._instance = cls()
        return cls._instance  # type: ignore[return-value]

    @classmethod
    def reset_instance(cls) -> None:
        """Reset the singleton instance. For testing only."""
        with cls._creation_lock:
            cls._instance = None
