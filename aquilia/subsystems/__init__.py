"""
Subsystem Initializers — Protocol and base classes for server decomposition.

Architecture v2: Each subsystem is an isolated unit with its own lifecycle.
The server orchestrates subsystems in priority order, with graceful degradation
for optional subsystems.
"""

from __future__ import annotations

from .base import SubsystemInitializer, BootContext, BaseSubsystem


__all__ = [
    "SubsystemInitializer",
    "BootContext",
    "BaseSubsystem",
]
