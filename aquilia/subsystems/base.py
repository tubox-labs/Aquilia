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
from typing import Any, Protocol, runtime_checkable

from aquilia.health import HealthRegistry, HealthStatus, SubsystemStatus
from aquilia.manifest import AppManifest

logger = logging.getLogger("aquilia.subsystems")

#: Canonical ``BootContext.shared_state`` key for an explicit DI container.
#:
#: Subsystems must not invent their own key -- they resolve DI targets through
#: :meth:`BootContext.di_containers`, which reads this key first and falls back
#: to ``BootContext.registry.di_containers``.
DI_CONTAINER_KEY = "container"


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

    Population contract
    -------------------
    The *caller* that builds the context owns these fields; subsystems only
    read them. Every field except ``config`` and ``manifests`` is optional,
    and a subsystem that needs a missing one degrades instead of failing:

    ==================== ======================================================
    Field                Who sets it / what happens when it is ``None``
    ==================== ======================================================
    ``config``           Required. Merged workspace configuration.
    ``manifests``        Required (may be empty). All loaded app manifests.
    ``registry``         ``RuntimeRegistry``. Supplies DI containers via
                         ``registry.di_containers``. When ``None`` and no
                         explicit container is shared, DI registration is
                         skipped with a warning.
    ``middleware_stack`` ``MiddlewareStack``. When ``None``, subsystems skip
                         middleware registration silently.
    ``health``           Defaults to a fresh ``HealthRegistry``.
    ``shared_state``     Cross-subsystem handoff. Well-known keys:
                         ``"container"`` (see :data:`DI_CONTAINER_KEY`) for an
                         explicit DI container overriding ``registry``,
                         ``"storage_registry"``, ``"vector_registry"``,
                         ``"effect_registry"``.
    ==================== ======================================================
    """

    config: dict[str, Any]  # Merged workspace configuration
    manifests: list[AppManifest]  # All loaded app manifests
    registry: Any = None  # RuntimeRegistry (set during boot)
    middleware_stack: Any = None  # MiddlewareStack (set during boot)
    health: HealthRegistry = field(default_factory=HealthRegistry)
    shared_state: dict[str, Any] = field(default_factory=dict)

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

    def get_manifest(self, module_name: str) -> AppManifest | None:
        """Get a manifest by module name."""
        for m in self.manifests:
            if m.name == module_name:
                return m
        return None

    def di_containers(self) -> list[Any]:
        """
        Return every DI container a subsystem should register itself into.

        Resolution order:

        1. ``shared_state[DI_CONTAINER_KEY]`` -- an explicit container wins, so
           an embedder can target one container without a ``RuntimeRegistry``.
        2. ``registry.di_containers`` -- the per-app containers built during
           boot. All of them are returned, matching how ``AquiliaServer``
           registers app-scoped values into every container rather than one.

        Returns an empty list when neither is available; callers treat that as
        "DI is not wired in this context" and skip registration.
        """
        explicit = self.shared_state.get(DI_CONTAINER_KEY)
        if explicit is not None and hasattr(explicit, "register"):
            return [explicit]

        containers = getattr(self.registry, "di_containers", None)
        if isinstance(containers, dict):
            return [c for c in containers.values() if hasattr(c, "register")]
        if isinstance(containers, (list, tuple)):
            return [c for c in containers if hasattr(c, "register")]
        return []


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
    - Timeout-protected initialization (``_timeout`` seconds, enforced)
    - Template methods for subclasses to override

    Note:
        ``required`` may be computed from configuration during
        ``_do_initialize`` (``VectorDBSubsystem`` raises it when stores are
        declared). Read it *after* :meth:`initialize` returns, never before --
        beforehand it only holds the class default.
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
        """
        Initialize with timing, timeout protection, and error handling.

        ``_do_initialize`` is bounded by ``self._timeout`` seconds so a
        subsystem that blocks on an unreachable dependency degrades to
        UNHEALTHY instead of hanging the boot forever. A non-positive
        ``_timeout`` disables the bound.
        """
        start = time.monotonic()
        try:
            if self._timeout and self._timeout > 0:
                await asyncio.wait_for(self._do_initialize(ctx), timeout=self._timeout)
            else:
                await self._do_initialize(ctx)
            self._init_time_ms = (time.monotonic() - start) * 1000
            self._initialized = True
            return HealthStatus(
                name=self._name,
                status=SubsystemStatus.HEALTHY,
                latency_ms=self._init_time_ms,
                message="Initialized successfully",
            )
        except asyncio.TimeoutError:
            elapsed = (time.monotonic() - start) * 1000
            message = f"Initialization timed out after {self._timeout:g}s"
            self._logger.error("%s %s", self._name, message)
            return HealthStatus(
                name=self._name,
                status=SubsystemStatus.UNHEALTHY,
                latency_ms=elapsed,
                message=message,
            )
        except Exception as e:
            elapsed = (time.monotonic() - start) * 1000
            self._logger.error(f"{self._name} failed ({elapsed:.1f}ms): {e}")
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
        except Exception as e:
            self._logger.error(f"{self._name} shutdown error: {e}")

    @abstractmethod
    async def _do_initialize(self, ctx: BootContext) -> None:
        """Subclass initialization logic."""
        ...

    async def _do_shutdown(self) -> None:
        """Subclass shutdown logic. Override if cleanup is needed."""
        pass
