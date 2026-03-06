"""
Storage Subsystem -- Aquilia boot lifecycle integration for storage.

Integrates the storage system into the Aquilia server lifecycle:
1. Reads storage configuration from ``BootContext.config["storage"]``
2. Instantiates and registers backends with ``StorageRegistry``
3. Initialises all backends (connect, create dirs, etc.)
4. Registers ``StorageRegistry`` with the DI container
5. Reports health status for each backend
6. Graceful shutdown with resource cleanup

Priority: 25 (before database=30, effects=45, controllers=60)

Configuration (via Workspace.storage() or config file)::

    storage:
      backends:
        - alias: default
          backend: local
          root: ./uploads
        - alias: cdn
          backend: s3
          bucket: my-cdn-bucket
          region: us-east-1
"""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

from ..subsystems.base import BaseSubsystem, BootContext
from ..health import HealthStatus, SubsystemStatus

logger = logging.getLogger("aquilia.subsystems.storage")


class StorageSubsystem(BaseSubsystem):
    """
    Subsystem initializer for the Aquilia storage system.

    Reads storage config, builds the ``StorageRegistry``, initialises
    all backends, wires into DI, and reports health.
    """

    _name = "storage"
    _priority = 25       # Before DB (30), effects (45), controllers (60)
    _required = False    # Degraded startup if storage fails
    _timeout = 30.0

    def __init__(self) -> None:
        super().__init__()
        self._registry: Optional[Any] = None

    async def _do_initialize(self, ctx: BootContext) -> None:
        """
        Initialize the storage subsystem.

        Steps:
        1. Read storage config from ctx.config["storage"]
        2. Build StorageRegistry from config
        3. Initialize all backends
        4. Register registry with DI
        5. Register health checks
        """
        from ..storage.registry import StorageRegistry
        from ..storage.configs import config_from_dict

        # Step 1: Read config
        storage_config = ctx.get_config("storage", {})
        if not storage_config:
            self._logger.debug("No storage config found, skipping")
            return

        backend_configs: list = storage_config.get("backends", [])

        # If config has a single backend dict (shorthand), wrap it
        if isinstance(backend_configs, dict):
            backend_configs = [backend_configs]

        if not backend_configs:
            # Try legacy single-backend config
            if "backend" in storage_config:
                backend_configs = [storage_config]
            else:
                self._logger.debug("No storage backends configured")
                return

        # Step 2: Build registry
        self._registry = StorageRegistry.from_config(backend_configs)
        self._logger.info(
            "Storage registry built: %s",
            ", ".join(self._registry.aliases()),
        )

        # Step 3: Initialize all backends
        await self._registry.initialize_all()
        self._logger.info("All storage backends initialized")

        # Step 4: Register with DI
        self._register_di(ctx)

        # Step 5: Register health
        await self._register_health(ctx)

        # Step 6: Share in boot context
        ctx.shared_state["storage_registry"] = self._registry

    def _register_di(self, ctx: BootContext) -> None:
        """Register StorageRegistry in the DI container."""
        try:
            from ..storage.registry import StorageRegistry
            from ..di import ValueProvider

            registry_obj = ctx.shared_state.get("_di_registry")
            if registry_obj and hasattr(registry_obj, "register"):
                provider = ValueProvider(
                    value=self._registry,
                    token=StorageRegistry,
                    scope="app",
                )
                registry_obj.register(provider)
                self._logger.debug("StorageRegistry registered with DI")
        except Exception as e:
            self._logger.warning("Could not register StorageRegistry with DI: %s", e)

    async def _register_health(self, ctx: BootContext) -> None:
        """Register health checks for all storage backends."""
        if not self._registry:
            return

        health = ctx.health
        health_map = await self._registry.health_check()

        for alias, healthy in health_map.items():
            status = SubsystemStatus.HEALTHY if healthy else SubsystemStatus.UNHEALTHY
            health.register(
                f"storage.{alias}",
                HealthStatus(
                    name=f"storage.{alias}",
                    status=status,
                    message=f"Backend '{alias}' {'healthy' if healthy else 'unhealthy'}",
                ),
            )

    async def _do_shutdown(self) -> None:
        """Shutdown all storage backends."""
        if self._registry:
            await self._registry.shutdown_all()
            self._logger.info("All storage backends shut down")

    async def health_check(self) -> HealthStatus:
        """Check health of all storage backends."""
        if not self._initialized or not self._registry:
            return HealthStatus(
                name=self._name,
                status=SubsystemStatus.STOPPED,
                message="Storage subsystem not initialized",
            )

        health_map = await self._registry.health_check()
        all_healthy = all(health_map.values())
        any_healthy = any(health_map.values()) if health_map else False

        if all_healthy:
            status = SubsystemStatus.HEALTHY
            msg = f"All {len(health_map)} backends healthy"
        elif any_healthy:
            status = SubsystemStatus.DEGRADED
            unhealthy = [k for k, v in health_map.items() if not v]
            msg = f"Degraded: backends unhealthy: {', '.join(unhealthy)}"
        else:
            status = SubsystemStatus.UNHEALTHY
            msg = "All backends unhealthy"

        return HealthStatus(
            name=self._name,
            status=status,
            latency_ms=self._init_time_ms,
            message=msg,
        )
