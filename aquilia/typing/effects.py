"""
Effect system type definitions.

This module provides:
- Named type aliases (``EffectName``, ``EffectMode``)
- Generic protocol for typed effect providers
- ``EffectResourceTypeMap`` — the authoritative mapping of built-in
  effect name → resource handle type, used to drive ``@overload``
  signatures on ``get_effect()``
- ``get_effect()`` overload helpers for IDE type inference

Built-in effect resource types
-------------------------------

+----------------+-----------------------------------+-------------------------------+
| Effect name    | Provider                          | Resource handle type          |
+================+===================================+===============================+
| ``"DBTx"``     | ``DBTxProvider``                  | ``DBTxHandle``                |
| ``"db"``       | ``DBTxProvider``                  | ``DBTxHandle``                |
+----------------+-----------------------------------+-------------------------------+
| ``"Cache"``    | ``CacheProvider``                 | ``CacheHandle | CacheServiceHandle`` |
| ``"cache"``    | ``CacheProvider``                 | ``CacheHandle | CacheServiceHandle`` |
+----------------+-----------------------------------+-------------------------------+
| ``"Queue"``    | ``QueueProvider``                 | ``QueueHandle``               |
| ``"queue"``    | ``QueueProvider``                 | ``QueueHandle``               |
| ``"Queue"``    | ``TaskQueueProvider``             | ``TaskQueueHandle``           |
+----------------+-----------------------------------+-------------------------------+
| ``"HTTP"``     | ``HTTPProvider``                  | ``HTTPHandle``                |
| ``"http"``     | ``HTTPProvider``                  | ``HTTPHandle``                |
+----------------+-----------------------------------+-------------------------------+
| ``"Storage"``  | ``StorageProvider``               | ``StorageHandle``             |
| ``"storage"``  | ``StorageProvider``               | ``StorageHandle``             |
+----------------+-----------------------------------+-------------------------------+

Custom effects
--------------

Effects registered outside this list are looked up with a fallback
``get_effect(name: str) -> Any`` overload so they don't break type
checking — but IDE autocompletion won't know their concrete type.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Literal, NewType, Protocol, TypeAlias, TypeVar

EffectName = NewType("EffectName", str)
EffectMode = NewType("EffectMode", str)

EffectResourceT = TypeVar("EffectResourceT")
EffectResourceT_co = TypeVar("EffectResourceT_co", covariant=True)

EffectMap: TypeAlias = dict[str, object]
EffectMetadata: TypeAlias = dict[str, object]


# ---------------------------------------------------------------------------
# Typed Protocol for effect providers
# ---------------------------------------------------------------------------


class EffectProviderProtocol(Protocol[EffectResourceT_co]):
    """
    Structural protocol for typed effect providers.

    Type-safe alternative to subclassing ``EffectProvider``.  Any class that
    implements ``initialize``, ``acquire``, ``release``, and ``finalize``
    with the correct signatures satisfies this protocol.

    Type parameter:
        ``EffectResourceT_co``: The concrete resource handle type returned
        by ``acquire()``.

    Examples::

        class MyProvider:
            async def initialize(self) -> None: ...
            async def acquire(self, mode: str | None = None) -> MyHandle: ...
            async def release(self, resource: MyHandle, success: bool = True) -> None: ...
            async def finalize(self) -> None: ...

        def register(name: str, provider: EffectProviderProtocol[MyHandle]) -> None: ...
    """

    async def initialize(self) -> None: ...

    async def acquire(self, mode: str | None = None) -> EffectResourceT_co: ...

    async def release(self, resource: EffectResourceT_co, success: bool = True) -> None: ...

    async def finalize(self) -> None: ...


# ---------------------------------------------------------------------------
# Resource handle forward references (resolved at runtime via TYPE_CHECKING)
# ---------------------------------------------------------------------------

if TYPE_CHECKING:
    from ..effects import (
        CacheHandle,
        CacheServiceHandle,
        QueueHandle,
        TaskQueueHandle,
    )

    # The canonical union types for each built-in effect
    CacheResource: TypeAlias = CacheHandle | CacheServiceHandle
    QueueResource: TypeAlias = QueueHandle | TaskQueueHandle

    # Authoritative mapping: effect name → resource handle type.
    # Used by IDEs for ``get_effect()`` return type inference.
    # Custom effects not in this map fall back to ``Any``.
    EffectResourceTypeMap: TypeAlias = (
        # DB
        Literal["DBTx"]  # → DBTxHandle
        | Literal["db"]  # → DBTxHandle
        # Cache
        | Literal["Cache"]  # → CacheResource
        | Literal["cache"]  # → CacheResource
        # Queue
        | Literal["Queue"]  # → QueueResource
        | Literal["queue"]  # → QueueResource
        # HTTP
        | Literal["HTTP"]  # → HTTPHandle
        | Literal["http"]  # → HTTPHandle
        # Storage
        | Literal["Storage"]  # → StorageHandle
        | Literal["storage"]  # → StorageHandle
    )
