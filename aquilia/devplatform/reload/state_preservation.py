"""
aquilia.devplatform.reload.state_preservation — Resource bridge across reload boundaries.

Snapshots long-lived resources (DB pools, cache backends, session stores,
WebSocket registries) before a partial module reload and re-binds them
to the freshly loaded service instances after reload.

Resources are stored in a global registry by string key. This decouples
the resource object from the module that instantiated it, allowing the module
to be reloaded without destroying the underlying connection pool.
"""

from __future__ import annotations

import logging
import threading
from dataclasses import dataclass, field
from typing import Any

from aquilia.devplatform.core._base import SingletonMixin
from aquilia.devplatform.faults import ReloadFault, report_fault

logger = logging.getLogger("aquilia.devplatform.reload.state_preservation")

# Resource keys — must match keys used by Aquilia services
_DB_POOL_KEY = "db_connection_pool"
_SESSION_STORE_KEY = "session_store"
_CACHE_BACKEND_KEY = "cache_backend"
_WS_REGISTRY_KEY = "websocket_registry"

PRESERVED_RESOURCE_KEYS = [
    _DB_POOL_KEY,
    _SESSION_STORE_KEY,
    _CACHE_BACKEND_KEY,
    _WS_REGISTRY_KEY,
]


@dataclass
class ResourceSnapshot:
    """Point-in-time capture of long-lived resource references."""

    resources: dict[str, Any] = field(default_factory=dict)

    def has(self, key: str) -> bool:
        return key in self.resources and self.resources[key] is not None

    def get(self, key: str) -> Any:
        return self.resources.get(key)


class StateBridgeRegistry(SingletonMixin):
    """
    Global registry that holds resource references across reload boundaries.

    Services register their long-lived resources here at startup.
    The executor snapshots the registry before reload and calls restore()
    after reload to re-bind references to the new service instances.

    Singleton — obtain via StateBridgeRegistry.get_instance().
    """

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._resources: dict[str, Any] = {}

    # ── Registration ─────────────────────────────────────────────────────

    def register(self, key: str, resource: Any) -> None:
        """Register a long-lived resource under the given key."""
        with self._lock:
            self._resources[key] = resource
        logger.debug("StateBridge: registered resource '%s'", key)

    def unregister(self, key: str) -> None:
        with self._lock:
            self._resources.pop(key, None)

    def get(self, key: str) -> Any:
        with self._lock:
            return self._resources.get(key)

    # ── Snapshot / Restore ───────────────────────────────────────────────

    def snapshot(self) -> ResourceSnapshot:
        """
        Capture current resource references.
        Called by ModuleReloadExecutor BEFORE reloading modules.
        """
        with self._lock:
            snap = ResourceSnapshot(resources=dict(self._resources))
        logger.debug("StateBridge: snapshot captured (%d resources)", len(snap.resources))
        return snap

    def restore(self, snapshot: ResourceSnapshot) -> None:
        """
        Attempt to re-bind snapshot resources to the active service instances
        after a partial reload.

        For each known resource type, this pushes the preserved reference back
        into the newly-loaded service's attribute so no connections are dropped.
        """
        self._rebind_db_pool(snapshot)
        self._rebind_session_store(snapshot)
        self._rebind_cache_backend(snapshot)
        logger.debug("StateBridge: restoration complete.")

    def _rebind_db_pool(self, snapshot: ResourceSnapshot) -> None:
        if not snapshot.has(_DB_POOL_KEY):
            return
        pool = snapshot.get(_DB_POOL_KEY)
        try:
            from aquilia.db.engine import AquiliaDatabase

            db = AquiliaDatabase.get_active()
            if db is not None and hasattr(db, "_pool"):
                db._pool = pool
                logger.debug("StateBridge: DB pool re-bound.")
        except Exception as exc:
            report_fault(ReloadFault(f"DB pool re-bind after reload failed: {exc}"))

    def _rebind_session_store(self, snapshot: ResourceSnapshot) -> None:
        if not snapshot.has(_SESSION_STORE_KEY):
            return
        store = snapshot.get(_SESSION_STORE_KEY)
        try:
            from aquilia.sessions.store import SessionStoreRegistry

            SessionStoreRegistry.set_active(store)
            logger.debug("StateBridge: session store re-bound.")
        except Exception as exc:
            logger.debug("StateBridge: session store re-bind skipped: %s", exc)

    def _rebind_cache_backend(self, snapshot: ResourceSnapshot) -> None:
        if not snapshot.has(_CACHE_BACKEND_KEY):
            return
        backend = snapshot.get(_CACHE_BACKEND_KEY)
        try:
            from aquilia.cache import CacheService

            CacheService.set_backend(backend)
            logger.debug("StateBridge: cache backend re-bound.")
        except Exception as exc:
            logger.debug("StateBridge: cache backend re-bind skipped: %s", exc)
