"""
AquilaTasks — Distributed and persistent job backends.

Every backend here implements the same :class:`~aquilia.tasks.engine.TaskBackend`
interface as the built-in :class:`~aquilia.tasks.engine.MemoryBackend`, so
switching from single-process development to a distributed production
deployment is a configuration change, not a code change::

    # workspace.py — development
    Integration.tasks(backend="memory")

    # workspace.py — production
    Integration.tasks(backend="redis", redis_url="redis://cache:6379/0")

Backends:
    :class:`RedisBackend`
        Multi-process, multi-machine execution with durable job state.
        Atomic claim via Lua, lease-based crash recovery, ``SET NX``
        fingerprint reservation.

    :class:`SQLBackend`
        Durable job state on the database the application already uses.
        Claims rows under a transaction, so no extra infrastructure is
        needed to survive restarts.

Delivery semantics:
    Both provide **at-least-once** delivery.  A worker claims a job under a
    time-bounded lease and renews it by heartbeat; if the worker dies, the
    lease lapses and another worker reclaims the job instead of the job being
    lost.  A stalled-then-recovered worker can therefore execute a job twice,
    so task functions should be idempotent.

See Also:
    :mod:`aquilia.tasks.engine` for the backend contract and the in-memory
    implementation.
"""

from __future__ import annotations

from .redis import RedisBackend
from .sql import SQLBackend

__all__ = ["RedisBackend", "SQLBackend"]
