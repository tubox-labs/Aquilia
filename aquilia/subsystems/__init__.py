"""
Subsystem Initializers -- ``BootContext`` lifecycle API for embedders.

Each subsystem here is an isolated unit with its own lifecycle: it reads a
shared :class:`~aquilia.subsystems.base.BootContext`, initializes itself under
a timeout, registers into DI and the health registry, and shuts down cleanly.

Who drives these
----------------
``AquiliaServer`` does **not**. The server boots storage, cache, tasks, mail and
effects through its own ordered ``_setup_*`` methods, and that is the production
path. This package is the entry point for hosts that drive subsystems
themselves -- embedders, alternative runners, and tests -- where there is no
``AquiliaServer`` to own the sequence.

Both paths share the same underlying registries (``StorageRegistry``,
``VectorRegistry``, ``EffectRegistry``), so behaviour does not diverge; only the
orchestration does. There is deliberately no ``SubsystemOrchestrator``: adding
one would create a second production boot sequence to keep in sync with the
server's. A host that wants ordered boot composes it directly::

    subsystems = sorted([StorageSubsystem(), EffectSubsystem()], key=lambda s: s.priority)
    ctx = BootContext(config=cfg, manifests=[], registry=runtime_registry)

    for sub in subsystems:
        status = await sub.initialize(ctx)
        ctx.health.register(sub.name, status)
        # `required` is only final after initialize() -- see BaseSubsystem.
        if status.status is SubsystemStatus.UNHEALTHY and sub.required:
            raise RuntimeError(f"required subsystem {sub.name} failed: {status.message}")

    # ... shutdown in reverse priority order
    for sub in reversed(subsystems):
        await sub.shutdown()
"""

from __future__ import annotations

from aquilia.subsystems.base import (
    DI_CONTAINER_KEY,
    BaseSubsystem,
    BootContext,
    SubsystemInitializer,
)
from aquilia.subsystems.effects import EffectSubsystem


def _get_storage_subsystem():
    """Lazy import to break circular dependency."""
    from aquilia.storage.subsystem import StorageSubsystem

    return StorageSubsystem


def _get_vectordb_subsystem():
    """Lazy import — keeps ``elips`` untouched unless the subsystem is used."""
    from aquilia.vectordb.subsystem import VectorDBSubsystem

    return VectorDBSubsystem


__all__ = [
    "SubsystemInitializer",
    "BootContext",
    "BaseSubsystem",
    "DI_CONTAINER_KEY",
    "EffectSubsystem",
    "StorageSubsystem",
    "VectorDBSubsystem",
]


def __getattr__(name):
    if name == "StorageSubsystem":
        return _get_storage_subsystem()
    if name == "VectorDBSubsystem":
        return _get_vectordb_subsystem()
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
