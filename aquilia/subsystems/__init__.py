"""
Subsystem Initializers -- Protocol and base classes for server decomposition.

Architecture v2: Each subsystem is an isolated unit with its own lifecycle.
The server orchestrates subsystems in priority order, with graceful degradation
for optional subsystems.
"""

from __future__ import annotations

from .base import SubsystemInitializer, BootContext, BaseSubsystem
from .effects import EffectSubsystem


def _get_storage_subsystem():
    """Lazy import to break circular dependency."""
    from ..storage.subsystem import StorageSubsystem
    return StorageSubsystem


__all__ = [
    "SubsystemInitializer",
    "BootContext",
    "BaseSubsystem",
    "EffectSubsystem",
    "StorageSubsystem",
]


def __getattr__(name):
    if name == "StorageSubsystem":
        return _get_storage_subsystem()
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
