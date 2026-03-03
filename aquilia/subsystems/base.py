"""
Subsystem Initializer -- Protocol and base implementation.

Architecture v2: Defines the contract for all subsystem initializers
and provides a base class with common lifecycle patterns.
"""

from __future__ import annotations

import asyncio
import logging
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Protocol, runtime_checkable

from ..health import HealthRegistry, HealthStatus, SubsystemStatus
from ..manifest import AppManifest

logger = logging.getLogger("aquilia.subsystems")


# ============================================================================
# Boot Context
# ============================================================================

@dataclass
class BootContext:
    """
    Shared context passed to all subsystem initializers during boot.

    Contains everything a subsystem needs to initialize itself:
    configuration, manifests, the runtime registry, middleware stack,
    health registry, and a shared state dict for cross-subsystem data.
    """
    config: Dict[str, Any]                    # Merged workspace configuration
    manifests: List[AppManifest]              # All loaded app manifests
    registry: Any = None                      # RuntimeRegistry (set during boot)
    middleware_stack: Any = None               # MiddlewareStack (set during boot)
    health: HealthRegistry = field(default_factory=HealthRegistry)
    shared_state: Dict[str, Any] = field(default_factory=dict)

    def get_config(self, key: str, default: Any = None) -> Any:
        """Get a configuration value by dotted key path."""
        parts = key.split(".")
        value = self.config
        for part in parts:
            if isinstance(value, dict):
                value = value.get(part, default)
            else:
                return default
        return value

    def get_manifest(self, module_name: str) -> Optional[AppManifest]:
        """Get a manifest by module name."""
        for m in self.manifests:
            if m.name == module_name:
                return m
        return None


# ============================================================================
# Protocol
# ============================================================================

@runtime_checkable
class SubsystemInitializer(Protocol):
    """
    Protocol for subsystem lifecycle management.

    Each subsystem:
    - Has a unique name and boot priority
    - Can be required (failure stops startup) or optional (failure degrades)
    - Initializes in priority order with timeout protection
    - Reports health status
    - Shuts down gracefully in reverse order
    """

    @property
    def name(self) -> str:
        """Unique subsystem name."""
        ...

    @property
    def priority(self) -> int:
        """Boot priority (lower = earlier). Range: 0-1000."""
        ...

    @property
    def required(self) -> bool:
        """If True, initialization failure stops the entire server startup."""
        ...

    async def initialize(self, ctx: BootContext) -> HealthStatus:
        """
        Initialize the subsystem.

        Args:
            ctx: Shared boot context with config, manifests, etc.

        Returns:
            HealthStatus indicating initialization result

        Raises:
            Exception: If initialization fails and subsystem is required
        """
        ...

    async def health_check(self) -> HealthStatus:
        """Report current health status."""
        ...

    async def shutdown(self) -> None:
        """Graceful shutdown with resource cleanup."""
        ...


# ============================================================================
# Base Implementation
# ============================================================================

class BaseSubsystem(ABC):
    """
    Base class for subsystem initializers with common lifecycle patterns.

    Provides:
    - Automatic timing and health status reporting
    - Structured logging
    - Timeout-protected initialization
    - Template methods for subclasses to override
    """

    _name: str = "unknown"
    _priority: int = 100
    _required: bool = False
    _timeout: float = 30.0

    def __init__(self):
        self._initialized = False
        self._init_time_ms: float = 0.0
        self._logger = logging.getLogger(f"aquilia.subsystems.{self._name}")

    @property
    def name(self) -> str:
        return self._name

    @property
    def priority(self) -> int:
        return self._priority

    @property
    def required(self) -> bool:
        return self._required

    @property
    def timeout(self) -> float:
        return self._timeout

    async def initialize(self, ctx: BootContext) -> HealthStatus:
        """Initialize with timing and error handling."""
        start = time.monotonic()
        try:
            await self._do_initialize(ctx)
            self._init_time_ms = (time.monotonic() - start) * 1000
            self._initialized = True
            self._logger.info(
                f"{self._name} initialized ({self._init_time_ms:.1f}ms)"
            )
            return HealthStatus(
                name=self._name,
                status=SubsystemStatus.HEALTHY,
                latency_ms=self._init_time_ms,
                message="Initialized successfully",
            )
        except Exception as e:
            elapsed = (time.monotonic() - start) * 1000
            self._logger.error(
                f"{self._name} failed ({elapsed:.1f}ms): {e}"
            )
            return HealthStatus(
                name=self._name,
                status=SubsystemStatus.UNHEALTHY,
                latency_ms=elapsed,
                message=str(e),
            )

    async def health_check(self) -> HealthStatus:
        """Default health check -- reports based on init status."""
        if not self._initialized:
            return HealthStatus(
                name=self._name,
                status=SubsystemStatus.STOPPED,
                message="Not initialized",
            )
        return HealthStatus(
            name=self._name,
            status=SubsystemStatus.HEALTHY,
            latency_ms=self._init_time_ms,
        )

    async def shutdown(self) -> None:
        """Shutdown with logging."""
        if not self._initialized:
            return
        try:
            await self._do_shutdown()
            self._initialized = False
            self._logger.info(f"{self._name} shut down")
        except Exception as e:
            self._logger.error(f"{self._name} shutdown error: {e}")

    @abstractmethod
    async def _do_initialize(self, ctx: BootContext) -> None:
        """Subclass initialization logic."""
        ...

    async def _do_shutdown(self) -> None:
        """Subclass shutdown logic. Override if cleanup is needed."""
        pass
