"""
AquilaCache -- Production-grade, async-first caching system for Aquilia.

Provides a multi-backend, DI-integrated, fault-aware caching layer with:
- **Multiple backends**: Memory (LRU/LFU/TTL), Redis, Composite (L1/L2)
- **Serialization**: Pluggable serializers (JSON, msgpack, pickle)
- **DI integration**: Auto-registered providers, injectable CacheService
- **Fault domain**: Typed cache faults with recovery strategies
- **Effect system**: CacheEffect for handler capability declarations
- **Middleware**: Response caching middleware with ETags
- **CLI commands**: ``aq cache stats``, ``aq cache clear``, ``aq cache keys``
- **Decorators**: ``@cached``, ``@cache_aside``, ``@invalidate``
- **Key building**: Deterministic, collision-free key generation

Architecture follows Aquilia conventions:
    Integration.cache() → ConfigLoader → Server._setup_cache() → DI → CacheService

Usage::

    from aquilia.cache import CacheService, cached, MemoryBackend

    # Via DI (recommended)
    class ProductController(Controller):
        def __init__(self, cache: CacheService):
            self.cache = cache

        @GET("/products/{id}")
        async def get_product(self, ctx, id: int):
            return await self.cache.get_or_set(
                f"product:{id}",
                lambda: self.repo.find(id),
                ttl=300,
            )

    # Via decorator
    @cached(ttl=60, namespace="api")
    async def get_users():
        return await db.fetch_all("SELECT * FROM users")
"""

from aquilia._version import __version__  # noqa: F401 — re-exported
from aquilia.cache.backends.composite import CompositeBackend
from aquilia.cache.backends.memory import MemoryBackend
from aquilia.cache.backends.null import NullBackend
from aquilia.cache.backends.redis import RedisBackend
from aquilia.cache.core import (
    CacheBackend,
    CacheConfig,
    CacheEntry,
    CacheKeyBuilder,
    CacheSerializer,
    CacheStats,
    EvictionPolicy,
)
from aquilia.cache.decorators import (
    cache_aside,
    cached,
    get_default_cache_service,
    invalidate,
    set_default_cache_service,
)
from aquilia.cache.faults import (
    CacheBackendFault,
    CacheCapacityFault,
    CacheConfigFault,
    CacheConnectionFault,
    CacheFault,
    CacheHealthFault,
    CacheMissFault,
    CacheSerializationFault,
    CacheStampedeFault,
)
from aquilia.cache.key_builder import DefaultKeyBuilder, HashKeyBuilder
from aquilia.cache.middleware import CacheMiddleware
from aquilia.cache.serializers import JsonCacheSerializer, MsgpackCacheSerializer, PickleCacheSerializer
from aquilia.cache.service import CacheService

__all__ = [
    # Core
    "CacheBackend",
    "CacheEntry",
    "CacheStats",
    "CacheConfig",
    "CacheSerializer",
    "CacheKeyBuilder",
    "EvictionPolicy",
    # Backends
    "MemoryBackend",
    "RedisBackend",
    "CompositeBackend",
    "NullBackend",
    # Service
    "CacheService",
    # Decorators
    "cached",
    "cache_aside",
    "invalidate",
    # Serializers
    "JsonCacheSerializer",
    "PickleCacheSerializer",
    "MsgpackCacheSerializer",
    # Faults
    "CacheFault",
    "CacheMissFault",
    "CacheConnectionFault",
    "CacheSerializationFault",
    "CacheCapacityFault",
    "CacheBackendFault",
    "CacheConfigFault",
    "CacheStampedeFault",
    "CacheHealthFault",
    # Middleware
    "CacheMiddleware",
    # Key builders
    "DefaultKeyBuilder",
    "HashKeyBuilder",
    # Decorator utilities
    "set_default_cache_service",
    "get_default_cache_service",
]
