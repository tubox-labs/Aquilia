"""
Effect System -- Typed Capabilities with Providers and Layers.

Effects represent side-effects (DB, Cache, Queue, HTTP, Storage) that handlers
declare via ``@requires()``. The runtime automatically acquires and releases
effect resources around handler execution.

Inspired by Effect-TS:
- Effects declare requirements, not implementations (no dependency leakage)
- Layers separate construction from usage
- Resources have guaranteed acquire/release lifecycle
- Type safety -- effects visible in handler signatures

Architecture:
    Effect          -- Typed token representing a capability
    EffectKind      -- Category enum (DB, CACHE, QUEUE, HTTP, STORAGE, CUSTOM)
    EffectProvider  -- ABC for provider implementations (acquire/release lifecycle)
    EffectRegistry  -- Central registry with DI integration
    EffectScope     -- Per-request scoped resource manager
    @requires       -- Declared on handlers/nodes (lives in flow.py)

Integration:
    - FlowPipeline auto-acquires effects declared by ``@requires()``
    - EffectMiddleware acquires per-request effects from handler metadata
    - EffectSubsystem initializes all providers at startup
    - EffectRegistry is registered as app-scoped DI singleton
    - Testing: MockEffectRegistry auto-stubs missing effects
"""

from __future__ import annotations

import contextlib
import logging
import time
from abc import ABC, abstractmethod
from collections.abc import Sequence
from enum import Enum
from typing import TYPE_CHECKING, Any, Generic, TypeVar, cast

if TYPE_CHECKING:
    from .db.engine import AquiliaDatabase
    from .sqlite._cursor import AsyncCursor
else:
    AsyncCursor = Any
    AquiliaDatabase = Any

from .typing.effects import EffectMap, EffectName

T = TypeVar("T")

logger = logging.getLogger("aquilia.effects")


# ---------------------------------------------------------------------------
# DBTxHandle — typed alias for the dict returned by DBTxProvider.acquire()
# ---------------------------------------------------------------------------


class DBTxHandle(dict):
    """
    Typed handle representing an acquired database transaction resource.

    Subclasses ``dict`` so existing code that inspects ``resource["connection"]``
    or ``resource["mode"]`` continues to work, while type checkers now infer
    ``DBTxHandle`` instead of ``Any`` for ``ctx.get_effect("DBTx")``.

    Exposes async query methods: ``execute()``, ``execute_many()``,
    ``fetch_all()``, ``fetch_one()``, and ``fetch_val()`` that run queries
    within the active transaction scope.
    """

    def __init__(self, data: dict, db: Any | None = None) -> None:
        super().__init__(data)
        self._db = db

    def _get_db(self) -> AquiliaDatabase:
        if self._db is not None:
            return self._db
        from .db.engine import get_database

        return get_database()

    async def execute(self, sql: str, params: Sequence[Any] | None = None) -> AsyncCursor:
        """Execute a query within the transaction. Returns a cursor-like object."""
        return await self._get_db().execute(sql, params)

    async def execute_many(self, sql: str, params_list: Sequence[Sequence[Any]] | None = None) -> None:
        """Execute multiple queries within the transaction."""
        await self._get_db().execute_many(sql, params_list)

    async def fetch_all(self, sql: str, params: Sequence[Any] | None = None) -> list[dict[str, Any]]:
        """Fetch all rows within the transaction as dicts."""
        return await self._get_db().fetch_all(sql, params)

    async def fetch_one(self, sql: str, params: Sequence[Any] | None = None) -> dict[str, Any] | None:
        """Fetch a single row within the transaction as a dict, or None."""
        return await self._get_db().fetch_one(sql, params)

    async def fetch_val(self, sql: str, params: Sequence[Any] | None = None) -> Any:
        """Fetch a single scalar value within the transaction."""
        return await self._get_db().fetch_val(sql, params)

    @property
    def connection(self) -> Any:
        """The underlying database connection / pool handle."""
        return self.get("connection")

    @property
    def mode(self) -> str:
        """Transaction mode: ``"read"`` or ``"write"``."""
        return str(self.get("mode", "read"))

    @property
    def transaction(self) -> Any:
        """The active transaction object, or ``None`` if not started."""
        return self.get("transaction")

    @property
    def acquired_at(self) -> float:
        """Monotonic timestamp at which this handle was acquired."""
        return float(self.get("acquired_at", 0.0))

    def __repr__(self) -> str:
        return f"DBTxHandle(mode={self.mode!r}, connection={self.connection!r})"


class EffectKind(Enum):
    """Categories of effects."""

    DB = "db"
    CACHE = "cache"
    QUEUE = "queue"
    HTTP = "http"
    STORAGE = "storage"
    CUSTOM = "custom"


class Effect(Generic[T]):
    """
    Effect token representing a capability.

    Example:
        DBTx['read']  - Read-only database transaction
        DBTx['write'] - Read-write database transaction
        Cache['user'] - User cache namespace
    """

    def __init__(self, name: str, mode: T | None = None, kind: EffectKind = EffectKind.CUSTOM):
        self.name: EffectName = EffectName(name)
        self.mode = mode
        self.kind = kind

    def __class_getitem__(cls, mode):
        """Support DBTx['read'] syntax."""
        instance = cls.__new__(cls)
        instance.mode = mode
        return instance

    def __repr__(self):
        if self.mode:
            return f"Effect({self.name}[{self.mode}])"
        return f"Effect({self.name})"


class EffectProvider(ABC):
    """
    Base class for effect providers.

    Providers implement the actual capability (e.g., database connection).
    Lifecycle:
        1. initialize()  -- called once at startup
        2. acquire(mode)  -- called per-request to get a resource
        3. release(resource, success) -- called at end of request
        4. finalize()    -- called once at shutdown
    """

    @abstractmethod
    async def initialize(self):
        """Initialize the provider (called once at startup)."""
        pass

    @abstractmethod
    async def acquire(self, mode: str | None = None) -> Any:
        """
        Acquire a resource for this effect (called per-request).

        Args:
            mode: Optional mode specifier (e.g., 'read', 'write')

        Returns:
            Resource handle
        """
        pass

    @abstractmethod
    async def release(self, resource: Any, success: bool = True):
        """
        Release the resource (called at end of request).

        Args:
            resource: Resource handle from acquire()
            success: Whether request completed successfully
        """
        pass

    async def finalize(self):
        """Finalize provider (called at shutdown)."""
        pass

    async def health_check(self) -> dict[str, Any]:
        """
        Check provider health. Override for custom health reporting.

        Returns:
            Dict with 'healthy' bool and optional metadata.
        """
        return {"healthy": True}


class DBTx(Effect):
    """Database transaction effect."""

    def __init__(self, mode: str = "read"):
        super().__init__("DBTx", mode=mode, kind=EffectKind.DB)


class CacheEffect(Effect):
    """Cache effect."""

    def __init__(self, namespace: str = "default"):
        super().__init__("Cache", mode=namespace, kind=EffectKind.CACHE)


class QueueEffect(Effect):
    """Queue/message publish effect."""

    def __init__(self, topic: str | None = None):
        super().__init__("Queue", mode=topic, kind=EffectKind.QUEUE)


class HTTPEffect(Effect):
    """HTTP client effect for outbound requests."""

    def __init__(self, service: str | None = None):
        super().__init__("HTTP", mode=service, kind=EffectKind.HTTP)


class StorageEffect(Effect):
    """File/blob storage effect."""

    def __init__(self, bucket: str | None = None):
        super().__init__("Storage", mode=bucket, kind=EffectKind.STORAGE)


# ============================================================================
# Providers
# ============================================================================


class DBTxProvider(EffectProvider):
    """Database transaction provider backed by AquiliaDatabase."""

    def __init__(self, connection_string: str):
        self.connection_string = connection_string
        self.db: Any = None
        self._acquire_count = 0
        self._release_count = 0

    async def initialize(self):
        """Initialize database connection."""
        from .db.engine import AquiliaDatabase

        self.db = AquiliaDatabase(self.connection_string)
        await self.db.connect()

    async def acquire(self, mode: str | None = None) -> DBTxHandle:
        """Acquire database connection and start transaction."""
        self._acquire_count += 1
        if self.db is None:
            from .db.engine import get_database

            try:
                self.db = get_database()
            except Exception as exc:
                from .faults.domains import DatabaseConnectionFault

                raise DatabaseConnectionFault(
                    backend="dbtx_effect",
                    reason=f"Database connection not initialized in DBTxProvider: {exc}",
                )

        readonly = mode == "read"
        from .models.transactions import Atomic

        txn = Atomic(db=self.db, readonly=readonly)
        await txn.__aenter__()

        return DBTxHandle(
            {
                "connection": self.db,
                "mode": mode or "read",
                "transaction": txn,
                "acquired_at": time.monotonic(),
            },
            db=self.db,
        )

    async def release(self, resource: DBTxHandle, success: bool = True) -> None:
        """Release database connection and commit/rollback transaction."""
        self._release_count += 1
        if isinstance(resource, dict) and "transaction" in resource:
            txn = resource["transaction"]
            if txn is not None:
                if success:
                    await txn.__aexit__(None, None, None)
                else:
                    await txn.__aexit__(Exception, Exception("Effect release rollback"), None)

    async def finalize(self):
        """Disconnect database pool."""
        if self.db is not None:
            await self.db.disconnect()

    async def health_check(self) -> dict[str, Any]:
        healthy = self.db is not None and self.db.is_connected()
        return {
            "healthy": healthy,
            "acquire_count": self._acquire_count,
            "release_count": self._release_count,
        }


class CacheProvider(EffectProvider):
    """
    Cache effect provider backed by the real CacheService.

    If a :class:`~aquilia.cache.service.CacheService` is provided it is used
    for all acquire/release operations; otherwise falls back to a simple
    in-memory dict (useful in tests or when the cache subsystem is disabled).
    """

    def __init__(self, backend: str = "memory", *, cache_service: Any = None):
        self.backend = backend
        self._svc = cache_service  # Optional CacheService
        self._fallback: dict = {}

    async def initialize(self):
        """Initialize cache backend."""
        if self._svc is not None:
            try:
                await self._svc.initialize()
            except Exception:
                pass  # CacheService.initialize is idempotent

    async def acquire(self, mode: str | None = None) -> CacheServiceHandle | CacheHandle:
        """Get cache handle for namespace."""
        namespace = mode or "default"
        if self._svc is not None:
            return CacheServiceHandle(self._svc, namespace)
        return CacheHandle(self._fallback, namespace)

    async def release(self, resource: CacheServiceHandle | CacheHandle, success: bool = True) -> None:
        """Nothing to release for cache."""
        pass

    async def finalize(self):
        """Shutdown underlying cache service."""
        if self._svc is not None:
            with contextlib.suppress(Exception):
                await self._svc.shutdown()

    async def health_check(self) -> dict[str, Any]:
        return {
            "healthy": True,
            "backend": self.backend,
            "has_service": self._svc is not None,
        }


class QueueProvider(EffectProvider):
    """
    Queue/message publish effect provider.

    Wraps a message broker connection (RabbitMQ, Redis Streams, etc.).
    """

    def __init__(self, broker_url: str | None = None):
        self.broker_url = broker_url
        self._connected = False
        self._messages: list[dict[str, Any]] = []  # In-memory fallback

    async def initialize(self):
        self._connected = True

    async def acquire(self, mode: str | None = None) -> QueueHandle:
        """Return a queue handle for a topic/channel."""
        topic = mode or "default"
        return QueueHandle(self._messages, topic)

    async def release(self, resource: QueueHandle, success: bool = True) -> None:
        pass

    async def finalize(self):
        self._connected = False

    async def health_check(self) -> dict[str, Any]:
        return {"healthy": self._connected, "broker_url": self.broker_url}


class TaskQueueProvider(EffectProvider):
    """
    Task queue effect provider backed by AquilaTasks TaskManager.

    Bridges the effect system with the background task subsystem,
    allowing controllers/services to enqueue tasks via ``@requires(Queue)``.

    When a TaskManager is available, ``acquire()`` returns a
    ``TaskQueueHandle`` that wraps ``manager.enqueue()``. Otherwise
    falls back to the in-memory message list.
    """

    def __init__(self, *, task_manager: Any = None):
        self._manager = task_manager
        self._fallback_messages: list[dict[str, Any]] = []

    async def initialize(self):
        pass  # Manager lifecycle is managed by the server

    async def acquire(self, mode: str | None = None) -> TaskQueueHandle | QueueHandle:
        queue = mode or "default"
        if self._manager is not None:
            return TaskQueueHandle(self._manager, queue)
        return QueueHandle(self._fallback_messages, queue)

    async def release(self, resource: TaskQueueHandle | QueueHandle, success: bool = True) -> None:
        pass

    async def finalize(self):
        pass

    async def health_check(self) -> dict[str, Any]:
        if self._manager is not None:
            return {
                "healthy": self._manager.is_running,
                "backend": self._manager.backend.__class__.__name__,
                "workers": self._manager.num_workers,
            }
        return {"healthy": True, "backend": "fallback"}


class HTTPProvider(EffectProvider):
    """
    HTTP client effect provider backed by Aquilia's native AsyncHTTPClient.
    """

    def __init__(self, base_url: str | None = None, *, timeout: float = 30.0):
        self.base_url = base_url
        self.timeout = timeout
        self.client: Any = None

    async def initialize(self):
        """Create AsyncHTTPClient session."""
        from .http.client import AsyncHTTPClient
        from .http.config import HTTPClientConfig, TimeoutConfig

        config = HTTPClientConfig(timeout=TimeoutConfig(total=self.timeout))
        self.client = AsyncHTTPClient(base_url=self.base_url, config=config)

    async def acquire(self, mode: str | None = None) -> HTTPHandle:
        """Return HTTP client handle."""
        if self.client is None:
            from .http.client import AsyncHTTPClient

            self.client = AsyncHTTPClient(base_url=self.base_url)
        return HTTPHandle(self.client, self.base_url)

    async def release(self, resource: HTTPHandle, success: bool = True) -> None:
        pass

    async def finalize(self):
        if self.client is not None:
            await self.client.close()


class StorageProvider(EffectProvider):
    """
    File/blob storage effect provider.

    Wraps local filesystem or cloud storage (S3, GCS, etc.).
    """

    def __init__(self, root_path: str = "./storage", *, storage_registry: Any = None) -> None:
        self.root_path = root_path
        self._registry = storage_registry

    async def initialize(self) -> None:
        import os

        os.makedirs(self.root_path, exist_ok=True)

    async def acquire(self, mode: str | None = None) -> StorageHandle:
        bucket = mode or "default"
        return StorageHandle(self.root_path, bucket, registry=self._registry)

    async def release(self, resource: StorageHandle, success: bool = True) -> None:
        pass

    async def health_check(self) -> dict[str, Any]:
        import os

        healthy = os.path.isdir(self.root_path)
        if self._registry is not None:
            try:
                # check registry health
                healthy = all((await self._registry.health_check()).values())
            except Exception:
                healthy = False
        return {"healthy": healthy, "root": self.root_path}


# ============================================================================
# Resource Handles
# ============================================================================


class CacheServiceHandle:
    """Handle wrapping real CacheService for a given namespace."""

    __slots__ = ("_svc", "_ns")

    def __init__(self, svc: Any, namespace: str):
        self._svc = svc
        self._ns = namespace

    async def get(self, key: str) -> Any | None:
        return await self._svc.get(key, namespace=self._ns)

    async def set(self, key: str, value: Any, ttl: int | None = None) -> None:
        await self._svc.set(key, value, ttl=ttl, namespace=self._ns)

    async def delete(self, key: str) -> bool:
        return await self._svc.delete(key, namespace=self._ns)


class CacheHandle:
    """Handle for cache operations in a namespace."""

    def __init__(self, cache: dict, namespace: str):
        self._cache = cache
        self._namespace = namespace

    def _key(self, key: str) -> str:
        return f"{self._namespace}:{key}"

    async def get(self, key: str) -> Any | None:
        """Get value from cache."""
        return self._cache.get(self._key(key))

    async def set(self, key: str, value: Any, ttl: int | None = None) -> None:
        """Set value in cache."""
        self._cache[self._key(key)] = value

    async def delete(self, key: str) -> bool:
        """Delete value from cache."""
        return bool(self._cache.pop(self._key(key), None) is not None)


class QueueHandle:
    """Handle for queue operations on a topic."""

    def __init__(self, messages: list[dict[str, Any]], topic: str):
        self._messages = messages
        self._topic = topic

    async def publish(self, payload: Any, *, headers: dict[str, str] | None = None) -> None:
        """Publish a message to the topic."""
        self._messages.append(
            {
                "topic": self._topic,
                "payload": payload,
                "headers": headers or {},
                "timestamp": time.monotonic(),
            }
        )

    async def publish_batch(self, payloads: Sequence[Any]) -> None:
        """Publish multiple messages."""
        for payload in payloads:
            await self.publish(payload)


class TaskQueueHandle:
    """Handle for enqueuing background tasks via the TaskManager."""

    def __init__(self, manager: Any, queue: str):
        self._manager = manager
        self._queue = queue

    async def enqueue(self, func: Any, *args: Any, **kwargs: Any) -> str:
        """
        Enqueue a task for background execution.

        Args:
            func: Async callable or @task-decorated function
            *args: Positional arguments for the task
            **kwargs: Keyword arguments for the task

        Returns:
            Job ID string
        """
        job_id = await self._manager.enqueue(func, *args, queue=self._queue, **kwargs)
        return cast(str, job_id)

    async def publish(self, payload: Any, *, headers: dict[str, str] | None = None) -> None:
        """Compatibility with QueueHandle -- enqueue payload as a task."""
        # For generic publish, store as a no-op message
        # Real usage should call enqueue() with a @task function
        pass

    async def publish_batch(self, payloads: Sequence[Any]) -> None:
        """Compatibility with QueueHandle."""
        pass


class HTTPHandle:
    """Handle for outbound HTTP requests wrapping AsyncHTTPClient."""

    def __init__(self, client: Any, base_url: str | None = None):
        self._client = client
        self._session = client  # backward compatibility
        self._base_url = base_url

    async def get(self, url: str, **kwargs) -> Any:
        if self._client:
            resp = await self._client.get(url, **kwargs)
            return await resp.json()
        return None

    async def post(self, url: str, *, json: Any = None, **kwargs) -> Any:
        if self._client:
            resp = await self._client.post(url, json=json, **kwargs)
            return await resp.json()
        return None

    async def put(self, url: str, *, json: Any = None, **kwargs) -> Any:
        if self._client:
            resp = await self._client.put(url, json=json, **kwargs)
            return await resp.json()
        return None

    async def delete(self, url: str, **kwargs) -> Any:
        if self._client:
            resp = await self._client.delete(url, **kwargs)
            return await resp.json()
        return None


class StorageHandle:
    """Handle for file/blob storage operations."""

    def __init__(self, root_path: str, bucket: str, registry: Any | None = None) -> None:
        self._root = root_path
        self._bucket = bucket
        self._registry = registry

    def _path(self, key: str) -> str:
        import os

        return os.path.join(self._root, self._bucket, key)

    async def read(self, key: str) -> bytes | None:
        if self._registry is not None:
            backend = self._registry.get(self._bucket) or self._registry.default
            try:
                storage_file = await backend.open(key, "rb")
                return await storage_file.read()
            except Exception:
                return None

        import os

        path = self._path(key)
        if not os.path.exists(path):
            return None
        with open(path, "rb") as f:
            return f.read()

    async def write(self, key: str, data: bytes) -> None:
        if self._registry is not None:
            backend = self._registry.get(self._bucket) or self._registry.default
            await backend.save(key, data, overwrite=True)
            return

        import os

        path = self._path(key)
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "wb") as f:
            f.write(data)

    async def delete(self, key: str) -> bool:
        if self._registry is not None:
            backend = self._registry.get(self._bucket) or self._registry.default
            try:
                await backend.delete(key)
                return True
            except Exception:
                return False

        import os

        path = self._path(key)
        if os.path.exists(path):
            os.remove(path)
            return True
        return False

    async def exists(self, key: str) -> bool:
        if self._registry is not None:
            backend = self._registry.get(self._bucket) or self._registry.default
            try:
                return await backend.exists(key)
            except Exception:
                return False

        import os

        return os.path.exists(self._path(key))


# ============================================================================
# EffectRegistry -- Central registry with lifecycle and DI integration
# ============================================================================


class EffectRegistry:
    """
    Registry for effect providers.

    Validates effect availability, manages provider lifecycles,
    and integrates with the DI system.

    Lifecycle:
        1. register() -- register providers at setup time
        2. initialize_all() -- called at startup (initializes all providers)
        3. acquire/release -- per-request via FlowPipeline or EffectScope
        4. finalize_all() -- called at shutdown

    DI Integration:
        - Registered as app-scoped singleton via register_with_container()
        - Individual providers accessible via ``effect:{name}`` tokens
        - Supports ``startup()`` / ``shutdown()`` DI lifecycle hooks

    Health:
        - ``health_check()`` aggregates health from all providers
    """

    def __init__(self):
        self.providers: dict[str, EffectProvider] = {}
        self._initialized = False
        self._metrics: dict[str, dict[str, int]] = {}  # per-effect acquire/release counts
        self._acquired_resources: EffectMap = {}

    def register(self, effect_name: str, provider: EffectProvider):
        """Register an effect provider."""
        self.providers[effect_name] = provider
        self._metrics[effect_name] = {"acquires": 0, "releases": 0, "errors": 0}

    def unregister(self, effect_name: str) -> EffectProvider | None:
        """Unregister and return an effect provider."""
        self._metrics.pop(effect_name, None)
        return self.providers.pop(effect_name, None)

    async def initialize_all(self):
        """Initialize all registered providers (lifecycle startup hook)."""
        if self._initialized:
            return
        for name, provider in self.providers.items():
            try:
                await provider.initialize()
            except Exception as exc:
                logger.error("Failed to initialize effect '%s': %s", name, exc)
                raise
        self._initialized = True

    async def finalize_all(self):
        """Finalize all providers (lifecycle shutdown hook)."""
        for name, provider in self.providers.items():
            try:
                await provider.finalize()
            except Exception as exc:
                logger.warning("Error finalizing effect '%s': %s", name, exc)
        self._initialized = False

    # -- Per-request acquire/release --------------------------------------

    async def acquire(self, effect_name: str, mode: str | None = None) -> Any:
        """
        Acquire a resource for the named effect.

        Args:
            effect_name: Registered effect name.
            mode: Optional mode specifier.

        Returns:
            Resource handle.

        Raises:
            KeyError: If effect is not registered.
        """
        provider = self.get_provider(effect_name)
        try:
            resource = await provider.acquire(mode)
            self._acquired_resources[effect_name] = resource
            metrics = self._metrics.get(effect_name)
            if metrics:
                metrics["acquires"] += 1
            return resource
        except Exception:
            metrics = self._metrics.get(effect_name)
            if metrics:
                metrics["errors"] += 1
            raise

    async def release(
        self,
        effect_name: str,
        resource: Any,
        *,
        success: bool = True,
    ) -> None:
        """
        Release a resource for the named effect.

        Args:
            effect_name: Registered effect name.
            resource: Resource handle from acquire().
            success: Whether the operation succeeded.
        """
        provider = self.get_provider(effect_name)
        try:
            await provider.release(resource, success=success)
            self._acquired_resources.pop(effect_name, None)
            metrics = self._metrics.get(effect_name)
            if metrics:
                metrics["releases"] += 1
        except Exception as exc:
            metrics = self._metrics.get(effect_name)
            if metrics:
                metrics["errors"] += 1
            logger.warning("Error releasing effect '%s': %s", effect_name, exc)

    # DI lifecycle aliases
    async def startup(self):
        """DI lifecycle startup hook."""
        await self.initialize_all()

    async def shutdown(self):
        """DI lifecycle shutdown hook."""
        await self.finalize_all()

    def has_effect(self, effect_name: str) -> bool:
        """Check if effect is available."""
        return effect_name in self.providers

    def get_provider(self, effect_name: str) -> EffectProvider:
        """Get provider for effect."""
        if effect_name not in self.providers:
            from .faults.domains import EffectNotAcquiredFault

            raise EffectNotAcquiredFault(
                effect_name=effect_name,
                reason="No provider is registered for this effect name.",
                registered_effects=list(self.providers.keys()),
                middleware_active=False,
            )
        return self.providers[effect_name]

    # -- Health -----------------------------------------------------------

    async def health_check(self) -> dict[str, Any]:
        """Aggregate health from all providers."""
        results: dict[str, Any] = {}
        all_healthy = True
        for name, provider in self.providers.items():
            try:
                health = await provider.health_check()
                results[name] = health
                if not health.get("healthy", True):
                    all_healthy = False
            except Exception as exc:
                results[name] = {"healthy": False, "error": str(exc)}
                all_healthy = False
        return {
            "healthy": all_healthy,
            "initialized": self._initialized,
            "provider_count": len(self.providers),
            "providers": results,
            "metrics": dict(self._metrics),
        }

    # -- DI Integration ---------------------------------------------------

    def register_with_container(self, container: Any):
        """
        Register this EffectRegistry and all effect providers with a DI container.

        Args:
            container: DI Container instance
        """
        from aquilia.di.providers import ValueProvider

        # Register the registry itself
        container.register(
            ValueProvider(
                value=self,
                token=EffectRegistry,
                scope="app",
            )
        )

        # Register individual providers by effect name
        for effect_name, provider in self.providers.items():
            try:
                container.register(
                    ValueProvider(
                        value=provider,
                        token=f"effect:{effect_name}",
                        scope="app",
                    )
                )
            except ValueError:
                pass  # Already registered

    # -- Introspection ----------------------------------------------------

    def list_effects(self) -> list[str]:
        """Return all registered effect names."""
        return list(self.providers.keys())

    def get_metrics(self) -> dict[str, dict[str, int]]:
        """Return per-effect metrics."""
        return dict(self._metrics)

    def __repr__(self) -> str:
        effects = list(self.providers.keys())
        return f"<EffectRegistry effects={effects} initialized={self._initialized}>"
