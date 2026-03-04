"""
Effect Subsystem -- Subsystem initializer for the effect system.

Integrates effects into the Aquilia boot lifecycle:
1. Discovers effect providers from manifests and configuration
2. Registers providers with the EffectRegistry
3. Builds Layer compositions (Effect-TS pattern)
4. Initializes all providers at startup
5. Registers EffectMiddleware in the middleware stack
6. Registers EffectRegistry with DI container
7. Reports health status
8. Cleans up at shutdown

Priority: 45 (after database=30, before controllers=60)
"""

from __future__ import annotations

import logging
import time
from typing import Any, Dict, List, Optional, TYPE_CHECKING

from .base import BaseSubsystem, BootContext

if TYPE_CHECKING:
    from ..effects import EffectRegistry, EffectProvider
    from ..flow import Layer, LayerComposition

logger = logging.getLogger("aquilia.subsystems.effects")


class EffectSubsystem(BaseSubsystem):
    """
    Subsystem initializer for the Aquilia effect system.

    Responsibilities:
    - Discover and register effect providers
    - Build and resolve Layer compositions
    - Initialize all providers
    - Wire EffectMiddleware into the middleware stack
    - Wire EffectRegistry into DI
    - Provide health reporting
    - Graceful shutdown with finalization

    Configuration (via BootContext.config):
        effects:
          providers:
            DBTx:
              class: "myapp.effects.MyDBProvider"
              args:
                connection_string: "postgresql://..."
            Cache:
              class: "aquilia.effects.CacheProvider"
              args:
                backend: "redis"
          middleware:
            enabled: true        # Auto-register EffectMiddleware
            priority: 15         # Middleware stack priority
            auto_detect: true    # Auto-detect @requires on handlers
          layers: []             # Layer compositions (advanced)
    """

    _name = "effects"
    _priority = 45  # After DB (30), before controllers (60)
    _required = False
    _timeout = 15.0

    def __init__(self):
        super().__init__()
        self._registry: Optional["EffectRegistry"] = None
        self._layers: List[Any] = []
        self._middleware_registered = False

    async def _do_initialize(self, ctx: BootContext) -> None:
        """
        Initialize the effect subsystem.

        Steps:
        1. Create or retrieve EffectRegistry
        2. Discover providers from config
        3. Build Layer compositions
        4. Initialize all providers
        5. Register middleware
        6. Register with DI
        """
        from ..effects import EffectRegistry

        # Step 1: Get or create registry
        self._registry = self._get_or_create_registry(ctx)

        # Step 2: Discover providers from config
        await self._discover_providers(ctx)

        # Step 3: Build layers
        await self._build_layers(ctx)

        # Step 4: Initialize all providers
        await self._registry.initialize_all()
        self._logger.info(
            "Initialized %d effect providers: %s",
            len(self._registry.providers),
            list(self._registry.providers.keys()),
        )

        # Step 5: Register middleware
        self._register_middleware(ctx)

        # Step 6: Register with DI
        self._register_with_di(ctx)

    def _get_or_create_registry(self, ctx: BootContext) -> "EffectRegistry":
        """Get existing registry from DI or create a new one."""
        from ..effects import EffectRegistry

        # Try to get from shared state (set by server.__init__)
        registry = ctx.shared_state.get("effect_registry")
        if isinstance(registry, EffectRegistry):
            return registry

        # Create new
        registry = EffectRegistry()
        ctx.shared_state["effect_registry"] = registry
        return registry

    async def _discover_providers(self, ctx: BootContext) -> None:
        """Discover and register effect providers from configuration."""
        from ..effects import (
            EffectProvider,
            DBTxProvider,
            CacheProvider,
            QueueProvider,
            HTTPProvider,
            StorageProvider,
        )
        import importlib

        config = ctx.config
        effects_config = None

        # Try to get effects config
        if hasattr(config, "get"):
            effects_config = config.get("effects", {})
        elif isinstance(config, dict):
            effects_config = config.get("effects", {})

        if not effects_config:
            return

        providers_config = effects_config.get("providers", {})

        for effect_name, provider_cfg in providers_config.items():
            if isinstance(provider_cfg, str):
                # Simple class path
                provider_cfg = {"class": provider_cfg}

            if not isinstance(provider_cfg, dict):
                continue

            cls_path = provider_cfg.get("class", "")
            args = provider_cfg.get("args", {})

            try:
                # Import provider class
                if ":" in cls_path:
                    module_path, cls_name = cls_path.split(":", 1)
                else:
                    module_path, cls_name = cls_path.rsplit(".", 1)

                module = importlib.import_module(module_path)
                provider_cls = getattr(module, cls_name)

                # Instantiate
                if isinstance(args, dict):
                    provider = provider_cls(**args)
                else:
                    provider = provider_cls()

                self._registry.register(effect_name, provider)

            except Exception as exc:
                self._logger.warning(
                    "Failed to register effect '%s' from config: %s",
                    effect_name, exc,
                )

    async def _build_layers(self, ctx: BootContext) -> None:
        """Build and resolve Layer compositions from config."""
        from ..flow import Layer, LayerComposition

        config = ctx.config
        effects_config = None

        if hasattr(config, "get"):
            effects_config = config.get("effects", {})
        elif isinstance(config, dict):
            effects_config = config.get("effects", {})

        if not effects_config:
            return

        layers_config = effects_config.get("layers", [])
        if not layers_config:
            return

        # Build layers from config
        layers: List[Layer] = []
        for layer_cfg in layers_config:
            if not isinstance(layer_cfg, dict):
                continue
            try:
                layer = Layer(
                    name=layer_cfg["name"],
                    factory=self._import_factory(layer_cfg.get("factory", "")),
                    deps=layer_cfg.get("deps", []),
                    scope=layer_cfg.get("scope", "app"),
                )
                layers.append(layer)
            except Exception as exc:
                self._logger.warning(
                    "Failed to build layer '%s': %s",
                    layer_cfg.get("name", "?"), exc,
                )

        if layers:
            composition = LayerComposition(layers)
            initial_deps = {"Config": ctx.config}
            await composition.register_with(self._registry, initial_deps)
            self._logger.info("Built %d effect layers", len(layers))

    def _register_middleware(self, ctx: BootContext) -> None:
        """Register EffectMiddleware in the middleware stack."""
        from ..middleware_ext.effect_middleware import (
            EffectMiddleware,
            FlowContextMiddleware,
        )

        config = ctx.config
        effects_config = {}

        if hasattr(config, "get"):
            effects_config = config.get("effects", {})
        elif isinstance(config, dict):
            effects_config = config.get("effects", {})

        mw_config = effects_config.get("middleware", {})
        enabled = mw_config.get("enabled", True)  # Enabled by default
        priority = mw_config.get("priority", 15)
        auto_detect = mw_config.get("auto_detect", True)

        if not enabled or not ctx.middleware_stack:
            return

        # Register FlowContext middleware (creates FlowContext per request)
        try:
            flow_ctx_mw = FlowContextMiddleware(self._registry)
            ctx.middleware_stack.add(flow_ctx_mw, scope="request", priority=priority - 1)
        except Exception as exc:
            self._logger.warning("Failed to register FlowContextMiddleware: %s", exc)

        # Register Effect middleware (acquire/release per request)
        if self._registry and self._registry.providers:
            try:
                effect_mw = EffectMiddleware(self._registry, auto_detect=auto_detect)
                ctx.middleware_stack.add(effect_mw, scope="request", priority=priority)
                self._middleware_registered = True
            except Exception as exc:
                self._logger.warning("Failed to register EffectMiddleware: %s", exc)

    def _register_with_di(self, ctx: BootContext) -> None:
        """Register EffectRegistry with the DI container."""
        if not self._registry:
            return

        # Try from shared state
        container = ctx.shared_state.get("container")
        if container:
            try:
                self._registry.register_with_container(container)
            except Exception as exc:
                self._logger.warning("Failed to register with DI: %s", exc)

    def _import_factory(self, factory_path: str):
        """Import a factory function from a dotted path."""
        import importlib
        if not factory_path:
            raise ValueError("Empty factory path")
        if ":" in factory_path:
            module_path, func_name = factory_path.split(":", 1)
        else:
            module_path, func_name = factory_path.rsplit(".", 1)
        module = importlib.import_module(module_path)
        return getattr(module, func_name)

    async def health_check(self):
        """Report effect system health."""
        from .base import HealthStatus, SubsystemStatus

        if not self._initialized or not self._registry:
            return HealthStatus(
                name=self._name,
                status=SubsystemStatus.STOPPED,
                message="Not initialized",
            )

        try:
            health = await self._registry.health_check()
            status = (
                SubsystemStatus.HEALTHY if health.get("healthy", False)
                else SubsystemStatus.DEGRADED
            )
            return HealthStatus(
                name=self._name,
                status=status,
                latency_ms=self._init_time_ms,
                message=f"{health.get('provider_count', 0)} providers registered",
                metadata=health,
            )
        except Exception as exc:
            return HealthStatus(
                name=self._name,
                status=SubsystemStatus.UNHEALTHY,
                message=str(exc),
            )

    async def _do_shutdown(self) -> None:
        """Finalize all effect providers."""
        if self._registry:
            await self._registry.finalize_all()
            self._logger.info("All effect providers finalized")

    @property
    def registry(self) -> Optional["EffectRegistry"]:
        """Access the EffectRegistry."""
        return self._registry
