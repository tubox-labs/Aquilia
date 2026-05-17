# Cache API Reference

This page is generated from the current Python source using the AST. It lists public classes, public methods, public module-level functions, constants, exports, and source files.

## Source Inventory

| File | Lines | Classes | Functions | Purpose |
| --- | ---: | ---: | ---: | --- |
| `aquilia/cache/__init__.py` | 119 | 0 | 0 | AquilaCache -- Production-grade, async-first caching system for Aquilia. |
| `aquilia/cache/backends/__init__.py` | 15 | 0 | 0 | AquilaCache Backends -- Storage implementations. |
| `aquilia/cache/backends/composite.py` | 281 | 1 | 0 | AquilaCache -- Composite (L1/L2) backend. |
| `aquilia/cache/backends/memory.py` | 514 | 1 | 0 | AquilaCache -- High-performance in-memory backend. |
| `aquilia/cache/backends/null.py` | 67 | 1 | 0 | AquilaCache -- Null (no-op) backend. |
| `aquilia/cache/backends/redis.py` | 462 | 1 | 0 | AquilaCache -- Redis backend for distributed caching. |
| `aquilia/cache/core.py` | 534 | 7 | 0 | AquilaCache -- Core types, protocols, and data structures. |
| `aquilia/cache/decorators.py` | 272 | 0 | 5 | AquilaCache -- Decorators for declarative caching. |
| `aquilia/cache/di_providers.py` | 201 | 0 | 4 | AquilaCache -- DI provider registration. |
| `aquilia/cache/faults.py` | 143 | 9 | 0 | AquilaCache -- Fault domain integration. |
| `aquilia/cache/key_builder.py` | 110 | 2 | 0 | AquilaCache -- Cache key builder implementations. |
| `aquilia/cache/middleware.py` | 275 | 1 | 0 | AquilaCache -- HTTP response caching middleware. |
| `aquilia/cache/serializers.py` | 191 | 3 | 1 | AquilaCache -- Pluggable serializers for cache value encoding. |
| `aquilia/cache/service.py` | 629 | 1 | 0 | AquilaCache -- CacheService: High-level API for cache operations. |

## Public Exports

`CacheBackend`, `CacheBackendFault`, `CacheCapacityFault`, `CacheConfig`, `CacheConfigFault`, `CacheConnectionFault`, `CacheEntry`, `CacheFault`, `CacheHealthFault`, `CacheKeyBuilder`, `CacheMiddleware`, `CacheMissFault`, `CacheSerializationFault`, `CacheSerializer`, `CacheService`, `CacheStampedeFault`, `CacheStats`, `CompositeBackend`, `DefaultKeyBuilder`, `EvictionPolicy`, `HashKeyBuilder`, `JsonCacheSerializer`, `MemoryBackend`, `MsgpackCacheSerializer`, `NullBackend`, `PickleCacheSerializer`, `RedisBackend`, `cache_aside`, `cached`, `get_default_cache_service`, `invalidate`, `set_default_cache_service`

## Public Class Summary

| Class | Source | Bases | Summary |
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

| Function | Source | Signature | Summary |
| --- | --- | --- | --- |
| `set_default_cache_service` | `aquilia/cache/decorators.py` | `def set_default_cache_service(service: Any)` | Register a module-level CacheService for decorator resolution. |
| `get_default_cache_service` | `aquilia/cache/decorators.py` | `def get_default_cache_service()` | Get the module-level default CacheService. |
| `cached` | `aquilia/cache/decorators.py` | `def cached(ttl: int=300, namespace: str='default', key: str \| None=None, key_func: Callable[..., str] \| None=None, tags: tuple[str, ...]=(), unless: Callable[..., bool] \| None=None, condition: Callable[[Any], bool] \| None=None)` | Decorator to cache function results. |
| `cache_aside` | `aquilia/cache/decorators.py` | `def cache_aside(ttl: int=300, namespace: str='default', tags: tuple[str, ...]=())` | Cache-aside decorator -- identical to @cached but semantically indicates the function is the authoritative data source. |
| `invalidate` | `aquilia/cache/decorators.py` | `def invalidate(*keys: str, namespace: str='default', tags: tuple[str, ...]=())` | Decorator to invalidate cache entries after function execution. |
| `create_cache_backend` | `aquilia/cache/di_providers.py` | `def create_cache_backend(config: CacheConfig)` | Factory: create cache backend from configuration. |
| `create_cache_service` | `aquilia/cache/di_providers.py` | `def create_cache_service(config: CacheConfig)` | Factory: create CacheService from configuration. |
| `build_cache_config` | `aquilia/cache/di_providers.py` | `def build_cache_config(config_dict: dict[str, Any])` | Build CacheConfig from dictionary (e.g., from ConfigLoader). |
| `register_cache_providers` | `aquilia/cache/di_providers.py` | `def register_cache_providers(container: Any, cache_service: CacheService)` | Register cache providers in a DI container. |
| `get_serializer` | `aquilia/cache/serializers.py` | `def get_serializer(name: str='json', *, secret_key: str \| bytes \| None=None)` | Factory for serializer instances. |

## Constants And Module Flags

| Name | Source | Value or Type |
| --- | --- | --- |
| `T` | `aquilia/cache/core.py` | `TypeVar('T')` |
| `T` | `aquilia/cache/decorators.py` | `TypeVar('T')` |
| `T` | `aquilia/cache/service.py` | `TypeVar('T')` |

## Detailed Classes And Methods

### `CompositeBackend`

- Source: `aquilia/cache/backends/composite.py`
- Bases: `CacheBackend`
- Summary: Two-level cache: L1 (fast/local) + L2 (distributed/persistent).

Methods:

| Method | Signature | Summary |
| --- | --- | --- |
| `name` | `def name(self)` |  |
| `is_distributed` | `def is_distributed(self)` |  |
| `initialize` | `async def initialize(self)` | Initialize both backends. |
| `shutdown` | `async def shutdown(self)` | Shutdown both backends. |
| `get` | `async def get(self, key: str)` | Read-through: L1 → L2, promoting on L2 hit. L2 errors degrade gracefully. |
| `set` | `async def set(self, key: str, value: Any, ttl: int \| None=None, tags: tuple[str, ...]=(), namespace: str='default')` | Write-through: write to L1 always, L2 with optional async mode. |
| `delete` | `async def delete(self, key: str)` | Invalidate in both levels. |
| `exists` | `async def exists(self, key: str)` | Check existence in either level. |
| `clear` | `async def clear(self, namespace: str \| None=None)` | Clear both levels. |
| `keys` | `async def keys(self, pattern: str='*', namespace: str \| None=None)` | Union of keys from both levels. |
| `stats` | `async def stats(self)` | Combined stats from both levels. |
| `delete_by_tags` | `async def delete_by_tags(self, tags: builtins.set[str])` | Invalidate by tags in both levels. |
| `get_many` | `async def get_many(self, keys: list[str])` | Batch get with L1 → L2 fallback. |
| `set_many` | `async def set_many(self, items: dict[str, Any], ttl: int \| None=None, namespace: str='default')` | Write-through batch set with async L2 option. |
| `increment` | `async def increment(self, key: str, delta: int=1)` | Increment in L2 (authoritative) and update L1. |
| `health_check` | `async def health_check(self)` | Check health of both levels. |
| `l2_healthy` | `def l2_healthy(self)` | Whether the L2 backend is currently healthy. |

### `MemoryBackend`

- Source: `aquilia/cache/backends/memory.py`
- Bases: `CacheBackend`
- Summary: In-memory cache backend with configurable eviction policies.

Methods:

| Method | Signature | Summary |
| --- | --- | --- |
| `name` | `def name(self)` |  |
| `initialize` | `async def initialize(self)` | Start the background TTL sweeper. |
| `shutdown` | `async def shutdown(self)` | Stop sweeper and clear all data. |
| `get` | `async def get(self, key: str)` | O(1) lookup with LRU promotion and latency tracking. |
| `set` | `async def set(self, key: str, value: Any, ttl: int \| None=None, tags: tuple[str, ...]=(), namespace: str='default')` | O(1) insert with eviction if at capacity, latency tracking, and capacity warnings. |
| `delete` | `async def delete(self, key: str)` | O(1) deletion. |
| `exists` | `async def exists(self, key: str)` | O(1) existence check. |
| `clear` | `async def clear(self, namespace: str \| None=None)` | Clear all or namespaced entries. |
| `keys` | `async def keys(self, pattern: str='*', namespace: str \| None=None)` | List keys matching glob pattern. |
| `stats` | `async def stats(self)` | Return current statistics. |
| `delete_by_tags` | `async def delete_by_tags(self, tags: builtins.set[str])` | O(m) tag-based invalidation via inverted index. |
| `get_many` | `async def get_many(self, keys: list[str])` | Batch get -- single lock acquisition. |
| `set_many` | `async def set_many(self, items: dict[str, Any], ttl: int \| None=None, namespace: str='default')` | Batch set -- single lock acquisition. |
| `increment` | `async def increment(self, key: str, delta: int=1)` | Atomic increment under lock. |
| `health_check` | `async def health_check(self)` | Check if the memory backend is healthy. |

### `NullBackend`

- Source: `aquilia/cache/backends/null.py`
- Bases: `CacheBackend`
- Summary: No-op cache backend -- all operations are pass-through.

Methods:

| Method | Signature | Summary |
| --- | --- | --- |
| `name` | `def name(self)` |  |
| `initialize` | `async def initialize(self)` |  |
| `shutdown` | `async def shutdown(self)` |  |
| `get` | `async def get(self, key: str)` |  |
| `set` | `async def set(self, key: str, value: Any, ttl: int \| None=None, tags: tuple[str, ...]=(), namespace: str='default')` |  |
| `delete` | `async def delete(self, key: str)` |  |
| `exists` | `async def exists(self, key: str)` |  |
| `clear` | `async def clear(self, namespace: str \| None=None)` |  |
| `keys` | `async def keys(self, pattern: str='*', namespace: str \| None=None)` |  |
| `stats` | `async def stats(self)` |  |

### `RedisBackend`

- Source: `aquilia/cache/backends/redis.py`
- Bases: `CacheBackend`
- Summary: Redis-backed cache using aioredis (redis-py async).

Methods:

| Method | Signature | Summary |
| --- | --- | --- |
| `name` | `def name(self)` |  |
| `is_distributed` | `def is_distributed(self)` |  |
| `initialize` | `async def initialize(self)` | Connect to Redis and create connection pool. |
| `shutdown` | `async def shutdown(self)` | Close Redis connection pool. |
| `get` | `async def get(self, key: str)` | Get a value from Redis. |
| `set` | `async def set(self, key: str, value: Any, ttl: int \| None=None, tags: tuple[str, ...]=(), namespace: str='default')` | Set a value in Redis with optional TTL and tags. |
| `delete` | `async def delete(self, key: str)` | Delete a key from Redis. |
| `exists` | `async def exists(self, key: str)` | Check if key exists in Redis. |
| `clear` | `async def clear(self, namespace: str \| None=None)` | Clear cache entries. |
| `keys` | `async def keys(self, pattern: str='*', namespace: str \| None=None)` | List keys matching pattern. |
| `stats` | `async def stats(self)` | Get Redis stats. |
| `delete_by_tags` | `async def delete_by_tags(self, tags: builtins.set[str])` | Delete entries by tag using Redis sets. |
| `get_many` | `async def get_many(self, keys: list[str])` | Pipelined batch get. |
| `set_many` | `async def set_many(self, items: dict[str, Any], ttl: int \| None=None, namespace: str='default')` | Pipelined batch set. |
| `increment` | `async def increment(self, key: str, delta: int=1)` | Atomic Redis INCRBY. |
| `health_check` | `async def health_check(self)` | Check if Redis is reachable. |

### `EvictionPolicy`

- Source: `aquilia/cache/core.py`
- Bases: `str, Enum`
- Summary: Cache eviction strategies.

Fields and class attributes:

| Name | Type | Default / Value |
| --- | --- | --- |
| `LRU` | `` | `'lru'` |
| `LFU` | `` | `'lfu'` |
| `TTL` | `` | `'ttl'` |
| `FIFO` | `` | `'fifo'` |
| `RANDOM` | `` | `'random'` |

### `CacheEntry`

- Source: `aquilia/cache/core.py`
- Bases: `object`
- Summary: Single cache entry with metadata.
- Decorators: `dataclass(slots=True)`

Fields and class attributes:

| Name | Type | Default / Value |
| --- | --- | --- |
| `key` | `str` | `` |
| `value` | `Any` | `` |
| `created_at` | `float` | `field(default_factory=time.monotonic)` |
| `expires_at` | `float \| None` | `None` |
| `last_accessed` | `float` | `field(default_factory=time.monotonic)` |
| `access_count` | `int` | `0` |
| `size_bytes` | `int` | `0` |
| `tags` | `tuple[str, ...]` | `()` |
| `namespace` | `str` | `'default'` |
| `version` | `int` | `1` |

Methods:

| Method | Signature | Summary |
| --- | --- | --- |
| `is_expired` | `def is_expired(self)` | Check if entry has expired. |
| `ttl_remaining` | `def ttl_remaining(self)` | Remaining TTL in seconds, or None if no expiry. |
| `age` | `def age(self)` | Age of entry in seconds since creation. |
| `touch` | `def touch(self)` | Update access metadata. |

### `CacheStats`

- Source: `aquilia/cache/core.py`
- Bases: `object`
- Summary: Aggregate cache statistics for observability.
- Decorators: `dataclass`

Fields and class attributes:

| Name | Type | Default / Value |
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

| Method | Signature | Summary |
| --- | --- | --- |
| `hit_rate` | `def hit_rate(self)` | Cache hit rate as a percentage. |
| `total_operations` | `def total_operations(self)` | Total number of operations. |
| `avg_get_latency_ms` | `def avg_get_latency_ms(self)` | Average GET latency in milliseconds. |
| `avg_set_latency_ms` | `def avg_set_latency_ms(self)` | Average SET latency in milliseconds. |
| `p99_get_latency_ms` | `def p99_get_latency_ms(self)` | P99 GET latency in milliseconds. |
| `record_get_latency` | `def record_get_latency(self, latency_ms: float)` | Record a GET operation latency sample. |
| `record_set_latency` | `def record_set_latency(self, latency_ms: float)` | Record a SET operation latency sample. |
| `to_dict` | `def to_dict(self)` | Serialize for diagnostics/trace. |

### `CacheConfig`

- Source: `aquilia/cache/core.py`
- Bases: `object`
- Summary: Cache subsystem configuration.
- Decorators: `dataclass`

Fields and class attributes:

| Name | Type | Default / Value |
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

| Method | Signature | Summary |
| --- | --- | --- |
| `apply_jitter` | `def apply_jitter(self, ttl: int)` | Apply TTL jitter to prevent thundering herd. |
| `to_dict` | `def to_dict(self)` | Serialize to dictionary. |

### `CacheSerializer`

- Source: `aquilia/cache/core.py`
- Bases: `Protocol`
- Summary: Protocol for cache value serialization.
- Decorators: `runtime_checkable`

Methods:

| Method | Signature | Summary |
| --- | --- | --- |
| `serialize` | `def serialize(self, value: Any)` | Serialize a value to bytes. |
| `deserialize` | `def deserialize(self, data: bytes)` | Deserialize bytes back to a value. |

### `CacheKeyBuilder`

- Source: `aquilia/cache/core.py`
- Bases: `Protocol`
- Summary: Protocol for building cache keys.
- Decorators: `runtime_checkable`

Methods:

| Method | Signature | Summary |
| --- | --- | --- |
| `build` | `def build(self, namespace: str, key: str, prefix: str='')` | Build a fully qualified cache key. |

### `CacheBackend`

- Source: `aquilia/cache/core.py`
- Bases: `ABC`
- Summary: Abstract cache backend -- defines the storage contract.

Methods:

| Method | Signature | Summary |
| --- | --- | --- |
| `initialize` | `async def initialize(self)` | Initialize backend resources (connection pools, etc.). |
| `shutdown` | `async def shutdown(self)` | Clean up backend resources. |
| `get` | `async def get(self, key: str)` | Retrieve entry by key. |
| `set` | `async def set(self, key: str, value: Any, ttl: int \| None=None, tags: tuple[str, ...]=(), namespace: str='default')` | Store a value with optional TTL and tags. |
| `delete` | `async def delete(self, key: str)` | Delete entry by key. |
| `exists` | `async def exists(self, key: str)` | Check if key exists and is not expired. |
| `clear` | `async def clear(self, namespace: str \| None=None)` | Clear cache entries. |
| `keys` | `async def keys(self, pattern: str='*', namespace: str \| None=None)` | List keys matching pattern. |
| `stats` | `async def stats(self)` | Get backend statistics. |
| `delete_by_tags` | `async def delete_by_tags(self, tags: builtins.set[str])` | Delete all entries matching any of the given tags. |
| `get_many` | `async def get_many(self, keys: list[str])` | Batch get multiple keys. |
| `set_many` | `async def set_many(self, items: dict[str, Any], ttl: int \| None=None, namespace: str='default')` | Batch set multiple key-value pairs. |
| `delete_many` | `async def delete_many(self, keys: list[str])` | Batch delete multiple keys. |
| `increment` | `async def increment(self, key: str, delta: int=1)` | Atomically increment a numeric value. |
| `decrement` | `async def decrement(self, key: str, delta: int=1)` | Atomically decrement a numeric value. |
| `name` | `def name(self)` | Backend name for diagnostics. |
| `is_distributed` | `def is_distributed(self)` | Whether this backend supports distributed caching. |

### `CacheFault`

- Source: `aquilia/cache/faults.py`
- Bases: `Fault`
- Summary: Base class for all cache faults.

### `CacheMissFault`

- Source: `aquilia/cache/faults.py`
- Bases: `CacheFault`
- Summary: Cache key not found (informational, non-error).

### `CacheConnectionFault`

- Source: `aquilia/cache/faults.py`
- Bases: `CacheFault`
- Summary: Failed to connect to cache backend.

### `CacheSerializationFault`

- Source: `aquilia/cache/faults.py`
- Bases: `CacheFault`
- Summary: Failed to serialize/deserialize cache value.

### `CacheCapacityFault`

- Source: `aquilia/cache/faults.py`
- Bases: `CacheFault`
- Summary: Cache has reached maximum capacity.

### `CacheBackendFault`

- Source: `aquilia/cache/faults.py`
- Bases: `CacheFault`
- Summary: Generic cache backend error.

### `CacheConfigFault`

- Source: `aquilia/cache/faults.py`
- Bases: `CacheFault`
- Summary: Cache configuration error.

### `CacheStampedeFault`

- Source: `aquilia/cache/faults.py`
- Bases: `CacheFault`
- Summary: Cache stampede detected -- multiple concurrent loads for same key.

### `CacheHealthFault`

- Source: `aquilia/cache/faults.py`
- Bases: `CacheFault`
- Summary: Cache health check failure.

### `DefaultKeyBuilder`

- Source: `aquilia/cache/key_builder.py`
- Bases: `object`
- Summary: Default key builder using colon-separated segments.

Methods:

| Method | Signature | Summary |
| --- | --- | --- |
| `build` | `def build(self, namespace: str, key: str, prefix: str='')` | Build qualified cache key with optional version. |
| `from_args` | `def from_args(self, namespace: str, func_name: str, args: tuple=(), kwargs: dict \| None=None, prefix: str='')` | Build cache key from function call arguments. |

### `HashKeyBuilder`

- Source: `aquilia/cache/key_builder.py`
- Bases: `object`
- Summary: Hash-based key builder for long or complex keys.

Methods:

| Method | Signature | Summary |
| --- | --- | --- |
| `build` | `def build(self, namespace: str, key: str, prefix: str='')` | Build hash-based cache key. |
| `from_args` | `def from_args(self, namespace: str, func_name: str, args: tuple=(), kwargs: dict \| None=None, prefix: str='')` | Build hashed key from function call arguments. |

### `CacheMiddleware`

- Source: `aquilia/cache/middleware.py`
- Bases: `object`
- Summary: HTTP response caching middleware.

### `JsonCacheSerializer`

- Source: `aquilia/cache/serializers.py`
- Bases: `object`
- Summary: JSON serializer -- safe, human-readable, cross-language.

Methods:

| Method | Signature | Summary |
| --- | --- | --- |
| `serialize` | `def serialize(self, value: Any)` | Serialize value to JSON bytes. |
| `deserialize` | `def deserialize(self, data: bytes)` | Deserialize JSON bytes to value. |

### `PickleCacheSerializer`

- Source: `aquilia/cache/serializers.py`
- Bases: `object`
- Summary: HMAC-signed pickle serializer -- supports arbitrary Python objects.

Methods:

| Method | Signature | Summary |
| --- | --- | --- |
| `serialize` | `def serialize(self, value: Any)` | Serialize value via pickle and prepend HMAC signature. |
| `deserialize` | `def deserialize(self, data: bytes)` | Verify HMAC signature, then deserialize pickle bytes. |

### `MsgpackCacheSerializer`

- Source: `aquilia/cache/serializers.py`
- Bases: `object`
- Summary: MessagePack serializer -- compact binary, cross-language.

Methods:

| Method | Signature | Summary |
| --- | --- | --- |
| `serialize` | `def serialize(self, value: Any)` | Serialize value to msgpack bytes. |
| `deserialize` | `def deserialize(self, data: bytes)` | Deserialize msgpack bytes. |

### `CacheService`

- Source: `aquilia/cache/service.py`
- Bases: `object`
- Summary: High-level cache service -- the primary API for application code.

Methods:

| Method | Signature | Summary |
| --- | --- | --- |
| `initialize` | `async def initialize(self)` | Initialize the cache service and its backend. |
| `shutdown` | `async def shutdown(self)` | Shutdown the cache service and its backend. |
| `startup` | `async def startup(self)` | DI lifecycle startup hook. |
| `async_init` | `async def async_init(self)` | DI async initialization hook. |
| `get` | `async def get(self, key: str, namespace: str \| None=None, default: Any=None)` | Get a value from cache. |
| `set` | `async def set(self, key: str, value: Any, ttl: int \| None=None, namespace: str \| None=None, tags: tuple[str, ...]=())` | Set a value in cache. |
| `delete` | `async def delete(self, key: str, namespace: str \| None=None)` | Delete a value from cache. |
| `exists` | `async def exists(self, key: str, namespace: str \| None=None)` | Check if key exists in cache. |
| `get_or_set` | `async def get_or_set(self, key: str, loader: Callable[[], Coroutine[Any, Any, T]], ttl: int \| None=None, namespace: str \| None=None, tags: tuple[str, ...]=())` | Cache-aside pattern with stampede prevention. |
| `get_many` | `async def get_many(self, keys: list[str], namespace: str \| None=None)` | Batch get multiple keys. |
| `set_many` | `async def set_many(self, items: dict[str, Any], ttl: int \| None=None, namespace: str \| None=None)` | Batch set multiple key-value pairs. |
| `delete_many` | `async def delete_many(self, keys: list[str], namespace: str \| None=None)` | Batch delete multiple keys. |
| `invalidate_tags` | `async def invalidate_tags(self, *tags: str)` | Invalidate all entries matching given tags. |
| `invalidate_namespace` | `async def invalidate_namespace(self, namespace: str)` | Clear all entries in a namespace. |
| `increment` | `async def increment(self, key: str, delta: int=1, namespace: str \| None=None)` | Atomically increment a numeric value. |
| `decrement` | `async def decrement(self, key: str, delta: int=1, namespace: str \| None=None)` | Atomically decrement a numeric value. |
| `clear` | `async def clear(self, namespace: str \| None=None)` | Clear all or namespace-scoped entries. |
| `keys` | `async def keys(self, pattern: str='*', namespace: str \| None=None)` | List keys matching pattern. |
| `stats` | `async def stats(self)` | Get cache statistics. |
| `backend` | `def backend(self)` | Access underlying backend. |
| `config` | `def config(self)` | Access cache configuration. |
| `is_distributed` | `def is_distributed(self)` | Whether the backend supports distributed caching. |
| `is_healthy` | `def is_healthy(self)` | Whether the cache service is healthy. |
| `touch` | `async def touch(self, key: str, ttl: int, namespace: str \| None=None)` | Refresh the TTL of a key without changing its value. |
| `warm` | `async def warm(self, items: dict[str, Any], ttl: int \| None=None, namespace: str \| None=None, tags: tuple[str, ...]=())` | Bulk-preload cache entries (cache warming). |
| `health_check` | `async def health_check(self)` | Check if the cache backend is reachable and functioning. |
| `get_or_default` | `async def get_or_default(self, key: str, default_factory: Callable[[], T], namespace: str \| None=None)` | Get a cached value, or compute default (without caching it). |
