"""
AquilaVectorDB — Boot subsystem.

Owns store lifecycle inside the ``BootContext`` pipeline: read config, open every
configured store, register the registry with DI, publish health, and close cleanly
on shutdown.

Priority 28 — after storage (25), before database (30). Vector stores may live
under a storage-managed path, so storage settles first; nothing in the SQL ORM is
needed to open one, so it does not wait on the database.

Required-ness is conditional, and deliberately so
--------------------------------------------------

``_required`` is ``True`` **only when stores are actually configured**. An app
with no vectordb block boots exactly as before — that is what keeps the optional
dependency optional. But an app that *declared* a store and could not open it
must fail loudly: a silently-degraded vector store answers every search with an
empty list, which reads as "no results" rather than "broken", and that is far
worse than not booting.

The usual optional-subsystem default is overridden here for that reason, and the
single-writer lock is why it matters in practice: with ``workers > 1``, every
worker after the first hits ``LockConflict``, and a degraded boot would hide it.
"""

from __future__ import annotations

import logging
from typing import Any

from aquilia.health import HealthStatus, SubsystemStatus
from aquilia.subsystems.base import BaseSubsystem, BootContext

logger = logging.getLogger("aquilia.subsystems.vectordb")


class VectorDBSubsystem(BaseSubsystem):
    """
    Subsystem initializer for the Aquilia vector database.

    Reads ``vectordb`` config, configures :class:`VectorRegistry`, opens every
    store, wires DI, and reports per-store health.
    """

    _name = "vectordb"
    _priority = 28  # After storage (25), before database (30)
    _required = False  # Raised to True in _do_initialize when stores exist
    _timeout = 60.0  # Opening a store rebuilds its index; slower than a socket

    def __init__(self) -> None:
        super().__init__()
        self._registry: Any | None = None
        self._store_count = 0

    async def _do_initialize(self, ctx: BootContext) -> None:
        """
        Initialize the vector subsystem.

        Steps:
        1. Read ``vectordb`` config; return early when absent or disabled.
        2. Verify ``elips`` is installed.
        3. Configure the registry with the declared stores.
        4. Open every store.
        5. Register the registry with DI.
        6. Publish health entries.
        """
        config = ctx.get_config("vectordb", {}) or {}
        if not config.get("enabled", False):
            return

        from aquilia.vectordb.configs import normalize_stores

        stores = normalize_stores(config)

        if not stores:
            logger.warning(
                "vectordb is enabled but declares no stores — set stores={...}, or a "
                "dimension for the single-store shorthand"
            )
            return

        # A declared store that fails to open must stop the boot. See the
        # module docstring for why this overrides the optional default.
        self._required = True

        from aquilia.vectordb._compat import require_elips

        require_elips()

        from aquilia.vectordb.registry import VectorRegistry

        VectorRegistry.configure(
            stores,
            default=config.get("default", "default"),
            pool_threads=int(config.get("pool_threads", 4)),
        )

        await VectorRegistry.connect_all()

        self._registry = VectorRegistry
        self._store_count = len(stores)

        self._register_di(ctx)
        await self._register_health(ctx)

        ctx.shared_state["vector_registry"] = VectorRegistry

        logger.info(
            "Vector database ready — %d store(s): %s",
            self._store_count,
            ", ".join(VectorRegistry.store_names()),
        )

    def _register_di(self, ctx: BootContext) -> None:
        """Register :class:`VectorRegistry` in every DI container the context exposes."""
        try:
            from aquilia.di import ValueProvider
            from aquilia.vectordb.registry import VectorRegistry

            containers = ctx.di_containers()
            if not containers:
                self._logger.debug("No DI container in boot context -- skipping VectorRegistry registration")
                return

            for container in containers:
                container.register(
                    ValueProvider(
                        value=VectorRegistry,
                        token=VectorRegistry,
                        scope="app",
                    )
                )
        except Exception as exc:
            # DI registration is a convenience: models reach the registry
            # directly through the class. Failing the boot over it would be
            # disproportionate.
            self._logger.warning("Could not register VectorRegistry with DI: %s", exc)

    async def _register_health(self, ctx: BootContext) -> None:
        """Publish one ``vectordb.<alias>`` entry per store plus a live aggregate check."""
        if self._registry is None:
            return

        health = ctx.health
        report = await self._registry.health()

        for alias, info in report.get("stores", {}).items():
            ok = bool(info.get("ok"))
            health.register(
                f"vectordb.{alias}",
                HealthStatus(
                    name=f"vectordb.{alias}",
                    status=SubsystemStatus.HEALTHY if ok else SubsystemStatus.UNHEALTHY,
                    message=(
                        f"dim={info.get('dimension')} metric={info.get('metric')} "
                        f"collections={len(info.get('collections') or [])}"
                        if ok
                        else str(info.get("error", "unavailable"))
                    ),
                ),
            )

        # Live check: a store that dies after boot must not keep reporting the
        # boot-time snapshot. See StorageSubsystem._register_health.
        health.register_check(self._name, self.health_check)

    async def _do_shutdown(self) -> None:
        """
        Close every store and drain the pool.

        Closing releases the writer lock. Skipping it would leave a stale lock
        behind for the next process — the lock is advisory and released on exit,
        but an orderly close also checkpoints pending writes.
        """
        if self._registry is not None:
            await self._registry.shutdown()
            self._registry = None

    async def health_check(self) -> HealthStatus:
        """Report aggregate health across every configured store."""
        if not self._initialized or self._registry is None:
            return HealthStatus(
                name=self._name,
                status=SubsystemStatus.STOPPED,
                message="Vector database not initialized",
            )

        report = await self._registry.health()
        stores = report.get("stores", {})
        healthy = [a for a, s in stores.items() if s.get("ok")]
        unhealthy = [a for a, s in stores.items() if not s.get("ok")]

        if not unhealthy:
            status = SubsystemStatus.HEALTHY
            message = f"{len(healthy)} store(s) healthy, {report.get('models', 0)} model(s)"
        elif healthy:
            status = SubsystemStatus.DEGRADED
            message = f"unhealthy: {', '.join(unhealthy)}"
        else:
            status = SubsystemStatus.UNHEALTHY
            message = "all stores unhealthy"

        return HealthStatus(
            name=self._name,
            status=status,
            latency_ms=self._init_time_ms,
            message=message,
        )


__all__ = ["VectorDBSubsystem"]
