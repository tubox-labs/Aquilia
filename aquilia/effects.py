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

from typing import Any, Generic, TypeVar, Optional, Dict, List, Set, Sequence
from abc import ABC, abstractmethod
from enum import Enum
import logging
import time

T = TypeVar("T")

logger = logging.getLogger("aquilia.effects")


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

    def __init__(self, name: str, mode: Optional[T] = None, kind: EffectKind = EffectKind.CUSTOM):
        self.name = name
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
    async def acquire(self, mode: Optional[str] = None) -> Any:
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

    async def health_check(self) -> Dict[str, Any]:
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

    def __init__(self, topic: Optional[str] = None):
        super().__init__("Queue", mode=topic, kind=EffectKind.QUEUE)


class HTTPEffect(Effect):
    """HTTP client effect for outbound requests."""

    def __init__(self, service: Optional[str] = None):
        super().__init__("HTTP", mode=service, kind=EffectKind.HTTP)


class StorageEffect(Effect):
    """File/blob storage effect."""

    def __init__(self, bucket: Optional[str] = None):
        super().__init__("Storage", mode=bucket, kind=EffectKind.STORAGE)


# ============================================================================
# Providers
# ============================================================================


class DBTxProvider(EffectProvider):
    """Database transaction provider."""

    def __init__(self, connection_string: str):
        self.connection_string = connection_string
        self.pool = None
        self._acquire_count = 0
        self._release_count = 0

    async def initialize(self):
        """Initialize connection pool."""
        self.pool = {"initialized": True, "connection_string": self.connection_string}

    async def acquire(self, mode: Optional[str] = None):
        """Acquire database connection."""
        self._acquire_count += 1
        return {
            "connection": self.pool,
            "mode": mode or "read",
            "transaction": None,
            "acquired_at": time.monotonic(),
        }

    async def release(self, resource: Any, success: bool = True):
        """Release connection and commit/rollback transaction."""
        self._release_count += 1
        if success:
            pass  # Commit
        else:
            pass  # Rollback

    async def health_check(self) -> Dict[str, Any]:
        return {
            "healthy": self.pool is not None,
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

    async def acquire(self, mode: Optional[str] = None):
        """Get cache handle for namespace."""
        namespace = mode or "default"
        if self._svc is not None:
            return CacheServiceHandle(self._svc, namespace)
        return CacheHandle(self._fallback, namespace)

    async def release(self, resource: Any, success: bool = True):
        """Nothing to release for cache."""
        pass

    async def finalize(self):
        """Shutdown underlying cache service."""
        if self._svc is not None:
            try:
                await self._svc.shutdown()
            except Exception:
                pass

    async def health_check(self) -> Dict[str, Any]:
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

    def __init__(self, broker_url: Optional[str] = None):
        self.broker_url = broker_url
        self._connected = False
        self._messages: List[Dict[str, Any]] = []  # In-memory fallback

    async def initialize(self):
        self._connected = True

    async def acquire(self, mode: Optional[str] = None):
        """Return a queue handle for a topic/channel."""
        topic = mode or "default"
        return QueueHandle(self._messages, topic)

    async def release(self, resource: Any, success: bool = True):
        pass

    async def finalize(self):
        self._connected = False

    async def health_check(self) -> Dict[str, Any]:
        return {"healthy": self._connected, "broker_url": self.broker_url}


class HTTPProvider(EffectProvider):
    """
    HTTP client effect provider for outbound requests.

    Manages an HTTP client session with connection pooling.
    """

    def __init__(self, base_url: Optional[str] = None, *, timeout: float = 30.0):
        self.base_url = base_url
        self.timeout = timeout
        self._session: Any = None

    async def initialize(self):
        """Create HTTP client session."""
        try:
            import aiohttp
            self._session = aiohttp.ClientSession(
                base_url=self.base_url,
                timeout=aiohttp.ClientTimeout(total=self.timeout),
            )
        except ImportError:
            self._session = None  # Will use fallback

    async def acquire(self, mode: Optional[str] = None):
        """Return HTTP client handle."""
        return HTTPHandle(self._session, self.base_url)

    async def release(self, resource: Any, success: bool = True):
        pass

    async def finalize(self):
        if self._session is not None:
            try:
                await self._session.close()
            except Exception:
                pass


class StorageProvider(EffectProvider):
    """
    File/blob storage effect provider.

    Wraps local filesystem or cloud storage (S3, GCS, etc.).
    """

    def __init__(self, root_path: str = "./storage"):
        self.root_path = root_path

    async def initialize(self):
        import os
        os.makedirs(self.root_path, exist_ok=True)

    async def acquire(self, mode: Optional[str] = None):
        bucket = mode or "default"
        return StorageHandle(self.root_path, bucket)

    async def release(self, resource: Any, success: bool = True):
        pass

    async def health_check(self) -> Dict[str, Any]:
        import os
        return {"healthy": os.path.isdir(self.root_path), "root": self.root_path}


# ============================================================================
# Resource Handles
# ============================================================================


class CacheServiceHandle:
    """Handle wrapping real CacheService for a given namespace."""

    __slots__ = ("_svc", "_ns")

    def __init__(self, svc: Any, namespace: str):
        self._svc = svc
        self._ns = namespace

    async def get(self, key: str) -> Optional[Any]:
        return await self._svc.get(key, namespace=self._ns)

    async def set(self, key: str, value: Any, ttl: Optional[int] = None):
        await self._svc.set(key, value, ttl=ttl, namespace=self._ns)

    async def delete(self, key: str):
        await self._svc.delete(key, namespace=self._ns)


class CacheHandle:
    """Handle for cache operations in a namespace."""

    def __init__(self, cache: dict, namespace: str):
        self._cache = cache
        self._namespace = namespace

    def _key(self, key: str) -> str:
        return f"{self._namespace}:{key}"

    async def get(self, key: str) -> Optional[Any]:
        """Get value from cache."""
        return self._cache.get(self._key(key))

    async def set(self, key: str, value: Any, ttl: Optional[int] = None):
        """Set value in cache."""
        self._cache[self._key(key)] = value

    async def delete(self, key: str):
        """Delete value from cache."""
        self._cache.pop(self._key(key), None)


class QueueHandle:
    """Handle for queue operations on a topic."""

    def __init__(self, messages: List[Dict[str, Any]], topic: str):
        self._messages = messages
        self._topic = topic

    async def publish(self, payload: Any, *, headers: Optional[Dict[str, str]] = None):
        """Publish a message to the topic."""
        self._messages.append({
            "topic": self._topic,
            "payload": payload,
            "headers": headers or {},
            "timestamp": time.monotonic(),
        })

    async def publish_batch(self, payloads: Sequence[Any]):
        """Publish multiple messages."""
        for payload in payloads:
            await self.publish(payload)


class HTTPHandle:
    """Handle for outbound HTTP requests."""

    def __init__(self, session: Any, base_url: Optional[str] = None):
        self._session = session
        self._base_url = base_url

    async def get(self, url: str, **kwargs) -> Any:
        if self._session:
            async with self._session.get(url, **kwargs) as resp:
                return await resp.json()
        return None

    async def post(self, url: str, *, json: Any = None, **kwargs) -> Any:
        if self._session:
            async with self._session.post(url, json=json, **kwargs) as resp:
                return await resp.json()
        return None

    async def put(self, url: str, *, json: Any = None, **kwargs) -> Any:
        if self._session:
            async with self._session.put(url, json=json, **kwargs) as resp:
                return await resp.json()
        return None

    async def delete(self, url: str, **kwargs) -> Any:
        if self._session:
            async with self._session.delete(url, **kwargs) as resp:
                return await resp.json()
        return None


class StorageHandle:
    """Handle for file/blob storage operations."""

    def __init__(self, root_path: str, bucket: str):
        self._root = root_path
        self._bucket = bucket

    def _path(self, key: str) -> str:
        import os
        return os.path.join(self._root, self._bucket, key)

    async def read(self, key: str) -> Optional[bytes]:
        import os
        path = self._path(key)
        if not os.path.exists(path):
            return None
        with open(path, "rb") as f:
            return f.read()

    async def write(self, key: str, data: bytes) -> None:
        import os
        path = self._path(key)
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "wb") as f:
            f.write(data)

    async def delete(self, key: str) -> bool:
        import os
        path = self._path(key)
        if os.path.exists(path):
            os.remove(path)
            return True
        return False

    async def exists(self, key: str) -> bool:
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
        self.providers: Dict[str, EffectProvider] = {}
        self._initialized = False
        self._metrics: Dict[str, Dict[str, int]] = {}  # per-effect acquire/release counts

    def register(self, effect_name: str, provider: EffectProvider):
        """Register an effect provider."""
        self.providers[effect_name] = provider
        self._metrics[effect_name] = {"acquires": 0, "releases": 0, "errors": 0}

    def unregister(self, effect_name: str) -> Optional[EffectProvider]:
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

    async def acquire(self, effect_name: str, mode: Optional[str] = None) -> Any:
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
            metrics = self._metrics.get(effect_name)
            if metrics:
                metrics["acquires"] += 1
            return resource
        except Exception as exc:
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
            raise KeyError(f"Effect '{effect_name}' not registered")
        return self.providers[effect_name]

    # -- Health -----------------------------------------------------------

    async def health_check(self) -> Dict[str, Any]:
        """Aggregate health from all providers."""
        results: Dict[str, Any] = {}
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

    def register_with_container(self, container: "Any"):
        """
        Register this EffectRegistry and all effect providers with a DI container.

        Args:
            container: DI Container instance
        """
        from aquilia.di.providers import ValueProvider

        # Register the registry itself
        container.register(ValueProvider(
            value=self,
            token=EffectRegistry,
            scope="app",
        ))

        # Register individual providers by effect name
        for effect_name, provider in self.providers.items():
            try:
                container.register(ValueProvider(
                    value=provider,
                    token=f"effect:{effect_name}",
                    scope="app",
                ))
            except ValueError:
                pass  # Already registered

    # -- Introspection ----------------------------------------------------

    def list_effects(self) -> List[str]:
        """Return all registered effect names."""
        return list(self.providers.keys())

    def get_metrics(self) -> Dict[str, Dict[str, int]]:
        """Return per-effect metrics."""
        return dict(self._metrics)

    def __repr__(self) -> str:
        effects = list(self.providers.keys())
        return f"<EffectRegistry effects={effects} initialized={self._initialized}>"
