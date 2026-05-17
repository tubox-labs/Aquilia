# Cache API Reference

This page is extracted from the current Python source. It includes public classes, methods, functions, constants, dataclass-like fields, decorators, and notable attributes.

## Public Class Summary

| Name | Source | Bases | Purpose |
| --- | --- | --- | --- |
| `CompositeBackend` | `aquilia/cache/backends/composite.py` | CacheBackend | Two-level cache: L1 (fast/local) + L2 (distributed/persistent). |
| `MemoryBackend` | `aquilia/cache/backends/memory.py` | CacheBackend | In-memory cache backend with configurable eviction policies. |
| `NullBackend` | `aquilia/cache/backends/null.py` | CacheBackend | No-op cache backend -- all operations are pass-through. |
| `RedisBackend` | `aquilia/cache/backends/redis.py` | CacheBackend | Redis-backed cache using aioredis (redis-py async). |
| `EvictionPolicy` | `aquilia/cache/core.py` | str, Enum | Cache eviction strategies. |
| `CacheEntry` | `aquilia/cache/core.py` | object | Single cache entry with metadata. |
| `CacheStats` | `aquilia/cache/core.py` | object | Aggregate cache statistics for observability. |
| `CacheConfig` | `aquilia/cache/core.py` | object | Cache subsystem configuration. |
| `CacheSerializer` | `aquilia/cache/core.py` | Protocol | Protocol for cache value serialization. |
| `CacheKeyBuilder` | `aquilia/cache/core.py` | Protocol | Protocol for building cache keys. |
| `CacheBackend` | `aquilia/cache/core.py` | ABC | Abstract cache backend -- defines the storage contract. |
| `CacheFault` | `aquilia/cache/faults.py` | Fault | Base class for all cache faults. |
| `CacheMissFault` | `aquilia/cache/faults.py` | CacheFault | Cache key not found (informational, non-error). |
| `CacheConnectionFault` | `aquilia/cache/faults.py` | CacheFault | Failed to connect to cache backend. |
| `CacheSerializationFault` | `aquilia/cache/faults.py` | CacheFault | Failed to serialize/deserialize cache value. |
| `CacheCapacityFault` | `aquilia/cache/faults.py` | CacheFault | Cache has reached maximum capacity. |
| `CacheBackendFault` | `aquilia/cache/faults.py` | CacheFault | Generic cache backend error. |
| `CacheConfigFault` | `aquilia/cache/faults.py` | CacheFault | Cache configuration error. |
| `CacheStampedeFault` | `aquilia/cache/faults.py` | CacheFault | Cache stampede detected -- multiple concurrent loads for same key. |
| `CacheHealthFault` | `aquilia/cache/faults.py` | CacheFault | Cache health check failure. |
| `DefaultKeyBuilder` | `aquilia/cache/key_builder.py` | object | Default key builder using colon-separated segments. |
| `HashKeyBuilder` | `aquilia/cache/key_builder.py` | object | Hash-based key builder for long or complex keys. |
| `CacheMiddleware` | `aquilia/cache/middleware.py` | object | HTTP response caching middleware. |
| `JsonCacheSerializer` | `aquilia/cache/serializers.py` | object | JSON serializer -- safe, human-readable, cross-language. |
| `PickleCacheSerializer` | `aquilia/cache/serializers.py` | object | HMAC-signed pickle serializer -- supports arbitrary Python objects. |
| `MsgpackCacheSerializer` | `aquilia/cache/serializers.py` | object | MessagePack serializer -- compact binary, cross-language. |
| `CacheService` | `aquilia/cache/service.py` | object | High-level cache service -- the primary API for application code. |

## Public Function Summary

| Name | Source | Signature | Purpose |
| --- | --- | --- | --- |
| `set_default_cache_service` | `aquilia/cache/decorators.py` | `def set_default_cache_service(service: Any) -> None` | Register a module-level CacheService for decorator resolution. |
| `get_default_cache_service` | `aquilia/cache/decorators.py` | `def get_default_cache_service() -> Any &#124; None` | Get the module-level default CacheService. |
| `cached` | `aquilia/cache/decorators.py` | `def cached(ttl: int = 300, namespace: str = 'default', key: str &#124; None = None, key_func: Callable[..., str] &#124; None = None, tags: tuple[str, ...] = (), unless: Callable[..., bool] &#124; None = None, condition: Callable[[Any], bool] &#124; None = None)` | Decorator to cache function results. |
| `cache_aside` | `aquilia/cache/decorators.py` | `def cache_aside(ttl: int = 300, namespace: str = 'default', tags: tuple[str, ...] = ())` | Cache-aside decorator -- identical to @cached but semantically |
| `invalidate` | `aquilia/cache/decorators.py` | `def invalidate(*keys: str, namespace: str = 'default', tags: tuple[str, ...] = ())` | Decorator to invalidate cache entries after function execution. |
| `create_cache_backend` | `aquilia/cache/di_providers.py` | `def create_cache_backend(config: CacheConfig) -> CacheBackend` | Factory: create cache backend from configuration. |
| `create_cache_service` | `aquilia/cache/di_providers.py` | `def create_cache_service(config: CacheConfig) -> CacheService` | Factory: create CacheService from configuration. |
| `build_cache_config` | `aquilia/cache/di_providers.py` | `def build_cache_config(config_dict: dict[str, Any]) -> CacheConfig` | Build CacheConfig from dictionary (e.g., from ConfigLoader). |
| `register_cache_providers` | `aquilia/cache/di_providers.py` | `def register_cache_providers(container: Any, cache_service: CacheService) -> None` | Register cache providers in a DI container. |
| `get_serializer` | `aquilia/cache/serializers.py` | `def get_serializer(name: str = 'json', *, secret_key: str &#124; bytes &#124; None = None)` | Factory for serializer instances. |

## Constants

| Name | Source | Value or type |
| --- | --- | --- |
| `T` | `aquilia/cache/core.py` | `TypeVar('T')` |
| `T` | `aquilia/cache/decorators.py` | `TypeVar('T')` |
| `T` | `aquilia/cache/service.py` | `TypeVar('T')` |

## Detailed Classes And Methods

### Class: `CompositeBackend`

- Source: `aquilia/cache/backends/composite.py`
- Bases: `CacheBackend`
- Summary: Two-level cache: L1 (fast/local) + L2 (distributed/persistent).

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `name` | `def name(self) -> str` | property | Method. |
| `is_distributed` | `def is_distributed(self) -> bool` | property | Method. |
| `initialize` | `async def initialize(self) -> None` |  | Initialize both backends. |
| `shutdown` | `async def shutdown(self) -> None` |  | Shutdown both backends. |
| `get` | `async def get(self, key: str) -> CacheEntry &#124; None` |  | Read-through: L1 -> L2, promoting on L2 hit. L2 errors degrade gracefully. |
| `set` | `async def set(self, key: str, value: Any, ttl: int &#124; None = None, tags: tuple[str, ...] = (), namespace: str = 'default') -> None` |  | Write-through: write to L1 always, L2 with optional async mode. |
| `delete` | `async def delete(self, key: str) -> bool` |  | Invalidate in both levels. |
| `exists` | `async def exists(self, key: str) -> bool` |  | Check existence in either level. |
| `clear` | `async def clear(self, namespace: str &#124; None = None) -> int` |  | Clear both levels. |
| `keys` | `async def keys(self, pattern: str = '*', namespace: str &#124; None = None) -> list[str]` |  | Union of keys from both levels. |
| `stats` | `async def stats(self) -> CacheStats` |  | Combined stats from both levels. |
| `delete_by_tags` | `async def delete_by_tags(self, tags: builtins.set[str]) -> int` |  | Invalidate by tags in both levels. |
| `get_many` | `async def get_many(self, keys: list[str]) -> dict[str, CacheEntry &#124; None]` |  | Batch get with L1 -> L2 fallback. |
| `set_many` | `async def set_many(self, items: dict[str, Any], ttl: int &#124; None = None, namespace: str = 'default') -> None` |  | Write-through batch set with async L2 option. |
| `increment` | `async def increment(self, key: str, delta: int = 1) -> int &#124; None` |  | Increment in L2 (authoritative) and update L1. |
| `health_check` | `async def health_check(self) -> bool` |  | Check health of both levels. |
| `l2_healthy` | `def l2_healthy(self) -> bool` | property | Whether the L2 backend is currently healthy. |

### Class: `MemoryBackend`

- Source: `aquilia/cache/backends/memory.py`
- Bases: `CacheBackend`
- Summary: In-memory cache backend with configurable eviction policies.

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `name` | `def name(self) -> str` | property | Method. |
| `initialize` | `async def initialize(self) -> None` |  | Start the background TTL sweeper. |
| `shutdown` | `async def shutdown(self) -> None` |  | Stop sweeper and clear all data. |
| `get` | `async def get(self, key: str) -> CacheEntry &#124; None` |  | O(1) lookup with LRU promotion and latency tracking. |
| `set` | `async def set(self, key: str, value: Any, ttl: int &#124; None = None, tags: tuple[str, ...] = (), namespace: str = 'default') -> None` |  | O(1) insert with eviction if at capacity, latency tracking, and capacity warnings. |
| `delete` | `async def delete(self, key: str) -> bool` |  | O(1) deletion. |
| `exists` | `async def exists(self, key: str) -> bool` |  | O(1) existence check. |
| `clear` | `async def clear(self, namespace: str &#124; None = None) -> int` |  | Clear all or namespaced entries. |
| `keys` | `async def keys(self, pattern: str = '*', namespace: str &#124; None = None) -> list[str]` |  | List keys matching glob pattern. |
| `stats` | `async def stats(self) -> CacheStats` |  | Return current statistics. |
| `delete_by_tags` | `async def delete_by_tags(self, tags: builtins.set[str]) -> int` |  | O(m) tag-based invalidation via inverted index. |
| `get_many` | `async def get_many(self, keys: list[str]) -> dict[str, CacheEntry &#124; None]` |  | Batch get -- single lock acquisition. |
| `set_many` | `async def set_many(self, items: dict[str, Any], ttl: int &#124; None = None, namespace: str = 'default') -> None` |  | Batch set -- single lock acquisition. |
| `increment` | `async def increment(self, key: str, delta: int = 1) -> int &#124; None` |  | Atomic increment under lock. |
| `health_check` | `async def health_check(self) -> bool` |  | Check if the memory backend is healthy. |

### Class: `NullBackend`

- Source: `aquilia/cache/backends/null.py`
- Bases: `CacheBackend`
- Summary: No-op cache backend -- all operations are pass-through.

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `name` | `def name(self) -> str` | property | Method. |
| `initialize` | `async def initialize(self) -> None` |  | Method. |
| `shutdown` | `async def shutdown(self) -> None` |  | Method. |
| `get` | `async def get(self, key: str) -> CacheEntry &#124; None` |  | Method. |
| `set` | `async def set(self, key: str, value: Any, ttl: int &#124; None = None, tags: tuple[str, ...] = (), namespace: str = 'default') -> None` |  | Method. |
| `delete` | `async def delete(self, key: str) -> bool` |  | Method. |
| `exists` | `async def exists(self, key: str) -> bool` |  | Method. |
| `clear` | `async def clear(self, namespace: str &#124; None = None) -> int` |  | Method. |
| `keys` | `async def keys(self, pattern: str = '*', namespace: str &#124; None = None) -> list[str]` |  | Method. |
| `stats` | `async def stats(self) -> CacheStats` |  | Method. |

### Class: `RedisBackend`

- Source: `aquilia/cache/backends/redis.py`
- Bases: `CacheBackend`
- Summary: Redis-backed cache using aioredis (redis-py async).

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `name` | `def name(self) -> str` | property | Method. |
| `is_distributed` | `def is_distributed(self) -> bool` | property | Method. |
| `initialize` | `async def initialize(self) -> None` |  | Connect to Redis and create connection pool. |
| `shutdown` | `async def shutdown(self) -> None` |  | Close Redis connection pool. |
| `get` | `async def get(self, key: str) -> CacheEntry &#124; None` |  | Get a value from Redis. |
| `set` | `async def set(self, key: str, value: Any, ttl: int &#124; None = None, tags: tuple[str, ...] = (), namespace: str = 'default') -> None` |  | Set a value in Redis with optional TTL and tags. |
| `delete` | `async def delete(self, key: str) -> bool` |  | Delete a key from Redis. |
| `exists` | `async def exists(self, key: str) -> bool` |  | Check if key exists in Redis. |
| `clear` | `async def clear(self, namespace: str &#124; None = None) -> int` |  | Clear cache entries. |
| `keys` | `async def keys(self, pattern: str = '*', namespace: str &#124; None = None) -> list[str]` |  | List keys matching pattern. |
| `stats` | `async def stats(self) -> CacheStats` |  | Get Redis stats. |
| `delete_by_tags` | `async def delete_by_tags(self, tags: builtins.set[str]) -> int` |  | Delete entries by tag using Redis sets. |
| `get_many` | `async def get_many(self, keys: list[str]) -> dict[str, CacheEntry &#124; None]` |  | Pipelined batch get. |
| `set_many` | `async def set_many(self, items: dict[str, Any], ttl: int &#124; None = None, namespace: str = 'default') -> None` |  | Pipelined batch set. |
| `increment` | `async def increment(self, key: str, delta: int = 1) -> int &#124; None` |  | Atomic Redis INCRBY. |
| `health_check` | `async def health_check(self) -> bool` |  | Check if Redis is reachable. |

### Class: `EvictionPolicy`

- Source: `aquilia/cache/core.py`
- Bases: `str, Enum`
- Summary: Cache eviction strategies.

Attributes and fields:

| Name | Type | Default |
| --- | --- | --- |
| `LRU` |  | `'lru'` |
| `LFU` |  | `'lfu'` |
| `TTL` |  | `'ttl'` |
| `FIFO` |  | `'fifo'` |
| `RANDOM` |  | `'random'` |

### Class: `CacheEntry`

- Source: `aquilia/cache/core.py`
- Bases: `object`
- Decorators: `dataclass`
- Summary: Single cache entry with metadata.

Attributes and fields:

| Name | Type | Default |
| --- | --- | --- |
| `key` | `str` |  |
| `value` | `Any` |  |
| `created_at` | `float` | `field(default_factory=time.monotonic)` |
| `expires_at` | `float &#124; None` | `None` |
| `last_accessed` | `float` | `field(default_factory=time.monotonic)` |
| `access_count` | `int` | `0` |
| `size_bytes` | `int` | `0` |
| `tags` | `tuple[str, ...]` | `()` |
| `namespace` | `str` | `'default'` |
| `version` | `int` | `1` |

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `is_expired` | `def is_expired(self) -> bool` | property | Check if entry has expired. |
| `ttl_remaining` | `def ttl_remaining(self) -> float &#124; None` | property | Remaining TTL in seconds, or None if no expiry. |
| `age` | `def age(self) -> float` | property | Age of entry in seconds since creation. |
| `touch` | `def touch(self) -> None` |  | Update access metadata. |

### Class: `CacheStats`

- Source: `aquilia/cache/core.py`
- Bases: `object`
- Decorators: `dataclass`
- Summary: Aggregate cache statistics for observability.

Attributes and fields:

| Name | Type | Default |
| --- | --- | --- |
| `hits` | `int` | `0` |
| `misses` | `int` | `0` |
| `sets` | `int` | `0` |
| `deletes` | `int` | `0` |
| `evictions` | `int` | `0` |
| `errors` | `int` | `0` |
| `stampede_joins` | `int` | `0` |
| `size` | `int` | `0` |
| `max_size` | `int` | `0` |
| `memory_bytes` | `int` | `0` |
| `backend` | `str` | `'unknown'` |
| `uptime_seconds` | `float` | `0.0` |

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `hit_rate` | `def hit_rate(self) -> float` | property | Cache hit rate as a percentage. |
| `total_operations` | `def total_operations(self) -> int` | property | Total number of operations. |
| `avg_get_latency_ms` | `def avg_get_latency_ms(self) -> float` | property | Average GET latency in milliseconds. |
| `avg_set_latency_ms` | `def avg_set_latency_ms(self) -> float` | property | Average SET latency in milliseconds. |
| `p99_get_latency_ms` | `def p99_get_latency_ms(self) -> float` | property | P99 GET latency in milliseconds. |
| `record_get_latency` | `def record_get_latency(self, latency_ms: float) -> None` |  | Record a GET operation latency sample. |
| `record_set_latency` | `def record_set_latency(self, latency_ms: float) -> None` |  | Record a SET operation latency sample. |
| `to_dict` | `def to_dict(self) -> dict[str, Any]` |  | Serialize for diagnostics/trace. |

### Class: `CacheConfig`

- Source: `aquilia/cache/core.py`
- Bases: `object`
- Decorators: `dataclass`
- Summary: Cache subsystem configuration.

Attributes and fields:

| Name | Type | Default |
| --- | --- | --- |
| `enabled` | `bool` | `True` |
| `backend` | `str` | `'memory'` |
| `default_ttl` | `int` | `300` |
| `max_size` | `int` | `10000` |
| `eviction_policy` | `str` | `'lru'` |
| `namespace` | `str` | `'default'` |
| `key_prefix` | `str` | `'aq:'` |
| `serializer` | `str` | `'json'` |
| `ttl_jitter` | `bool` | `True` |
| `ttl_jitter_percent` | `float` | `0.1` |
| `stampede_prevention` | `bool` | `True` |
| `stampede_timeout` | `float` | `30.0` |
| `health_check_interval` | `float` | `60.0` |
| `capacity_warning_threshold` | `float` | `0.85` |
| `key_version` | `int` | `1` |
| `redis_url` | `str` | `'redis://localhost:6379/0'` |
| `redis_max_connections` | `int` | `10` |
| `redis_socket_timeout` | `float` | `5.0` |
| `redis_socket_connect_timeout` | `float` | `5.0` |
| `redis_retry_on_timeout` | `bool` | `True` |
| `redis_decode_responses` | `bool` | `True` |
| `l1_max_size` | `int` | `1000` |
| `l1_ttl` | `int` | `60` |
| `l2_backend` | `str` | `'redis'` |
| `l2_async_write` | `bool` | `False` |
| `middleware_enabled` | `bool` | `False` |
| `middleware_cacheable_methods` | `tuple[str, ...]` | `('GET', 'HEAD')` |
| `middleware_default_ttl` | `int` | `60` |
| `middleware_vary_headers` | `tuple[str, ...]` | `('Accept', 'Accept-Encoding')` |
| `middleware_stale_while_revalidate` | `int` | `0` |
| `trace_enabled` | `bool` | `True` |
| `metrics_enabled` | `bool` | `True` |
| `log_level` | `str` | `'WARNING'` |

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `apply_jitter` | `def apply_jitter(self, ttl: int) -> int` |  | Apply TTL jitter to prevent thundering herd. |
| `to_dict` | `def to_dict(self) -> dict[str, Any]` |  | Serialize to dictionary. |

### Class: `CacheSerializer`

- Source: `aquilia/cache/core.py`
- Bases: `Protocol`
- Decorators: `runtime_checkable`
- Summary: Protocol for cache value serialization.

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `serialize` | `def serialize(self, value: Any) -> bytes` |  | Serialize a value to bytes. |
| `deserialize` | `def deserialize(self, data: bytes) -> Any` |  | Deserialize bytes back to a value. |

### Class: `CacheKeyBuilder`

- Source: `aquilia/cache/core.py`
- Bases: `Protocol`
- Decorators: `runtime_checkable`
- Summary: Protocol for building cache keys.

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `build` | `def build(self, namespace: str, key: str, prefix: str = '') -> str` |  | Build a fully qualified cache key. |

### Class: `CacheBackend`

- Source: `aquilia/cache/core.py`
- Bases: `ABC`
- Summary: Abstract cache backend -- defines the storage contract.

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `initialize` | `async def initialize(self) -> None` | abstractmethod | Initialize backend resources (connection pools, etc.). |
| `shutdown` | `async def shutdown(self) -> None` | abstractmethod | Clean up backend resources. |
| `get` | `async def get(self, key: str) -> CacheEntry &#124; None` | abstractmethod | Retrieve entry by key. |
| `set` | `async def set(self, key: str, value: Any, ttl: int &#124; None = None, tags: tuple[str, ...] = (), namespace: str = 'default') -> None` | abstractmethod | Store a value with optional TTL and tags. |
| `delete` | `async def delete(self, key: str) -> bool` | abstractmethod | Delete entry by key. |
| `exists` | `async def exists(self, key: str) -> bool` | abstractmethod | Check if key exists and is not expired. |
| `clear` | `async def clear(self, namespace: str &#124; None = None) -> int` | abstractmethod | Clear cache entries. |
| `keys` | `async def keys(self, pattern: str = '*', namespace: str &#124; None = None) -> list[str]` | abstractmethod | List keys matching pattern. |
| `stats` | `async def stats(self) -> CacheStats` | abstractmethod | Get backend statistics. |
| `delete_by_tags` | `async def delete_by_tags(self, tags: builtins.set[str]) -> int` |  | Delete all entries matching any of the given tags. |
| `get_many` | `async def get_many(self, keys: list[str]) -> dict[str, CacheEntry &#124; None]` |  | Batch get multiple keys. |
| `set_many` | `async def set_many(self, items: dict[str, Any], ttl: int &#124; None = None, namespace: str = 'default') -> None` |  | Batch set multiple key-value pairs. |
| `delete_many` | `async def delete_many(self, keys: list[str]) -> int` |  | Batch delete multiple keys. |
| `increment` | `async def increment(self, key: str, delta: int = 1) -> int &#124; None` |  | Atomically increment a numeric value. |
| `decrement` | `async def decrement(self, key: str, delta: int = 1) -> int &#124; None` |  | Atomically decrement a numeric value. |
| `name` | `def name(self) -> str` | property, abstractmethod | Backend name for diagnostics. |
| `is_distributed` | `def is_distributed(self) -> bool` | property | Whether this backend supports distributed caching. |

### Class: `CacheFault`

- Source: `aquilia/cache/faults.py`
- Bases: `Fault`
- Summary: Base class for all cache faults.

### Class: `CacheMissFault`

- Source: `aquilia/cache/faults.py`
- Bases: `CacheFault`
- Summary: Cache key not found (informational, non-error).

### Class: `CacheConnectionFault`

- Source: `aquilia/cache/faults.py`
- Bases: `CacheFault`
- Summary: Failed to connect to cache backend.

### Class: `CacheSerializationFault`

- Source: `aquilia/cache/faults.py`
- Bases: `CacheFault`
- Summary: Failed to serialize/deserialize cache value.

### Class: `CacheCapacityFault`

- Source: `aquilia/cache/faults.py`
- Bases: `CacheFault`
- Summary: Cache has reached maximum capacity.

### Class: `CacheBackendFault`

- Source: `aquilia/cache/faults.py`
- Bases: `CacheFault`
- Summary: Generic cache backend error.

### Class: `CacheConfigFault`

- Source: `aquilia/cache/faults.py`
- Bases: `CacheFault`
- Summary: Cache configuration error.

### Class: `CacheStampedeFault`

- Source: `aquilia/cache/faults.py`
- Bases: `CacheFault`
- Summary: Cache stampede detected -- multiple concurrent loads for same key.

### Class: `CacheHealthFault`

- Source: `aquilia/cache/faults.py`
- Bases: `CacheFault`
- Summary: Cache health check failure.

### Class: `DefaultKeyBuilder`

- Source: `aquilia/cache/key_builder.py`
- Bases: `object`
- Summary: Default key builder using colon-separated segments.

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `build` | `def build(self, namespace: str, key: str, prefix: str = '') -> str` |  | Build qualified cache key with optional version. |
| `from_args` | `def from_args(self, namespace: str, func_name: str, args: tuple = (), kwargs: dict &#124; None = None, prefix: str = '') -> str` |  | Build cache key from function call arguments. |

### Class: `HashKeyBuilder`

- Source: `aquilia/cache/key_builder.py`
- Bases: `object`
- Summary: Hash-based key builder for long or complex keys.

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `build` | `def build(self, namespace: str, key: str, prefix: str = '') -> str` |  | Build hash-based cache key. |
| `from_args` | `def from_args(self, namespace: str, func_name: str, args: tuple = (), kwargs: dict &#124; None = None, prefix: str = '') -> str` |  | Build hashed key from function call arguments. |

### Class: `CacheMiddleware`

- Source: `aquilia/cache/middleware.py`
- Bases: `object`
- Summary: HTTP response caching middleware.

### Class: `JsonCacheSerializer`

- Source: `aquilia/cache/serializers.py`
- Bases: `object`
- Summary: JSON serializer -- safe, human-readable, cross-language.

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `serialize` | `def serialize(self, value: Any) -> bytes` |  | Serialize value to JSON bytes. |
| `deserialize` | `def deserialize(self, data: bytes) -> Any` |  | Deserialize JSON bytes to value. |

### Class: `PickleCacheSerializer`

- Source: `aquilia/cache/serializers.py`
- Bases: `object`
- Summary: HMAC-signed pickle serializer -- supports arbitrary Python objects.

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `serialize` | `def serialize(self, value: Any) -> bytes` |  | Serialize value via pickle and prepend HMAC signature. |
| `deserialize` | `def deserialize(self, data: bytes) -> Any` |  | Verify HMAC signature, then deserialize pickle bytes. |

### Class: `MsgpackCacheSerializer`

- Source: `aquilia/cache/serializers.py`
- Bases: `object`
- Summary: MessagePack serializer -- compact binary, cross-language.

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `serialize` | `def serialize(self, value: Any) -> bytes` |  | Serialize value to msgpack bytes. |
| `deserialize` | `def deserialize(self, data: bytes) -> Any` |  | Deserialize msgpack bytes. |

### Class: `CacheService`

- Source: `aquilia/cache/service.py`
- Bases: `object`
- Summary: High-level cache service -- the primary API for application code.

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `initialize` | `async def initialize(self) -> None` |  | Initialize the cache service and its backend. |
| `shutdown` | `async def shutdown(self) -> None` |  | Shutdown the cache service and its backend. |
| `startup` | `async def startup(self) -> None` |  | DI lifecycle startup hook. |
| `async_init` | `async def async_init(self) -> None` |  | DI async initialization hook. |
| `get` | `async def get(self, key: str, namespace: str &#124; None = None, default: Any = None) -> Any` |  | Get a value from cache. |
| `set` | `async def set(self, key: str, value: Any, ttl: int &#124; None = None, namespace: str &#124; None = None, tags: tuple[str, ...] = ()) -> None` |  | Set a value in cache. |
| `delete` | `async def delete(self, key: str, namespace: str &#124; None = None) -> bool` |  | Delete a value from cache. |
| `exists` | `async def exists(self, key: str, namespace: str &#124; None = None) -> bool` |  | Check if key exists in cache. |
| `get_or_set` | `async def get_or_set(self, key: str, loader: Callable[[], Coroutine[Any, Any, T]], ttl: int &#124; None = None, namespace: str &#124; None = None, tags: tuple[str, ...] = ()) -> T` |  | Cache-aside pattern with stampede prevention. |
| `get_many` | `async def get_many(self, keys: list[str], namespace: str &#124; None = None) -> dict[str, Any]` |  | Batch get multiple keys. |
| `set_many` | `async def set_many(self, items: dict[str, Any], ttl: int &#124; None = None, namespace: str &#124; None = None) -> None` |  | Batch set multiple key-value pairs. |
| `delete_many` | `async def delete_many(self, keys: list[str], namespace: str &#124; None = None) -> int` |  | Batch delete multiple keys. |
| `invalidate_tags` | `async def invalidate_tags(self, *tags: str) -> int` |  | Invalidate all entries matching given tags. |
| `invalidate_namespace` | `async def invalidate_namespace(self, namespace: str) -> int` |  | Clear all entries in a namespace. |
| `increment` | `async def increment(self, key: str, delta: int = 1, namespace: str &#124; None = None) -> int &#124; None` |  | Atomically increment a numeric value. |
| `decrement` | `async def decrement(self, key: str, delta: int = 1, namespace: str &#124; None = None) -> int &#124; None` |  | Atomically decrement a numeric value. |
| `clear` | `async def clear(self, namespace: str &#124; None = None) -> int` |  | Clear all or namespace-scoped entries. |
| `keys` | `async def keys(self, pattern: str = '*', namespace: str &#124; None = None) -> list[str]` |  | List keys matching pattern. |
| `stats` | `async def stats(self) -> CacheStats` |  | Get cache statistics. |
| `backend` | `def backend(self) -> CacheBackend` | property | Access underlying backend. |
| `config` | `def config(self) -> CacheConfig` | property | Access cache configuration. |
| `is_distributed` | `def is_distributed(self) -> bool` | property | Whether the backend supports distributed caching. |
| `is_healthy` | `def is_healthy(self) -> bool` | property | Whether the cache service is healthy. |
| `touch` | `async def touch(self, key: str, ttl: int, namespace: str &#124; None = None) -> bool` |  | Refresh the TTL of a key without changing its value. |
| `warm` | `async def warm(self, items: dict[str, Any], ttl: int &#124; None = None, namespace: str &#124; None = None, tags: tuple[str, ...] = ()) -> int` |  | Bulk-preload cache entries (cache warming). |
| `health_check` | `async def health_check(self) -> bool` |  | Check if the cache backend is reachable and functioning. |
| `get_or_default` | `async def get_or_default(self, key: str, default_factory: Callable[[], T], namespace: str &#124; None = None) -> T` |  | Get a cached value, or compute default (without caching it). |

## Functions

| Name | Source | Signature | Purpose |
| --- | --- | --- | --- |
| `set_default_cache_service` | `aquilia/cache/decorators.py` | `def set_default_cache_service(service: Any) -> None` | Register a module-level CacheService for decorator resolution. |
| `get_default_cache_service` | `aquilia/cache/decorators.py` | `def get_default_cache_service() -> Any &#124; None` | Get the module-level default CacheService. |
| `cached` | `aquilia/cache/decorators.py` | `def cached(ttl: int = 300, namespace: str = 'default', key: str &#124; None = None, key_func: Callable[..., str] &#124; None = None, tags: tuple[str, ...] = (), unless: Callable[..., bool] &#124; None = None, condition: Callable[[Any], bool] &#124; None = None)` | Decorator to cache function results. |
| `cache_aside` | `aquilia/cache/decorators.py` | `def cache_aside(ttl: int = 300, namespace: str = 'default', tags: tuple[str, ...] = ())` | Cache-aside decorator -- identical to @cached but semantically |
| `invalidate` | `aquilia/cache/decorators.py` | `def invalidate(*keys: str, namespace: str = 'default', tags: tuple[str, ...] = ())` | Decorator to invalidate cache entries after function execution. |
| `create_cache_backend` | `aquilia/cache/di_providers.py` | `def create_cache_backend(config: CacheConfig) -> CacheBackend` | Factory: create cache backend from configuration. |
| `create_cache_service` | `aquilia/cache/di_providers.py` | `def create_cache_service(config: CacheConfig) -> CacheService` | Factory: create CacheService from configuration. |
| `build_cache_config` | `aquilia/cache/di_providers.py` | `def build_cache_config(config_dict: dict[str, Any]) -> CacheConfig` | Build CacheConfig from dictionary (e.g., from ConfigLoader). |
| `register_cache_providers` | `aquilia/cache/di_providers.py` | `def register_cache_providers(container: Any, cache_service: CacheService) -> None` | Register cache providers in a DI container. |
| `get_serializer` | `aquilia/cache/serializers.py` | `def get_serializer(name: str = 'json', *, secret_key: str &#124; bytes &#124; None = None)` | Factory for serializer instances. |

## Constants

| Name | Source | Value or type |
| --- | --- | --- |
| `T` | `aquilia/cache/core.py` | `TypeVar('T')` |
| `T` | `aquilia/cache/decorators.py` | `TypeVar('T')` |
| `T` | `aquilia/cache/service.py` | `TypeVar('T')` |
