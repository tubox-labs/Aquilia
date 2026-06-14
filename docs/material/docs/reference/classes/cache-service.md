# CacheService

## Overview

`CacheService` is the high-level, DI-injectable cache API in Aquilia. It wraps a configured backend with namespace isolation, automatic key building, TTL jitter (thundering herd prevention), stampede prevention (singleflight), fault handling, and health monitoring.

```python
from aquilia.cache import CacheService, CacheConfig

cache = CacheService(backend=RedisBackend("redis://localhost:6379/0"))

user = await cache.get_or_set(
    "user:123",
    loader=lambda: repo.find(123),
    ttl=300,
)
```

---

## `CacheService`

!!! abstract "`aquilia.cache.CacheService`"
    DI singleton

```python
class CacheService:
    def __init__(
        self,
        backend: CacheBackend,
        config: CacheConfig | None = None,
    ):
```

### Lifecycle

```python
async def initialize(self) -> None:
    """Initialize the cache service and its backend. Starts health check loop."""

async def shutdown(self) -> None:
    """Shutdown: cancel health checks, cancel inflight operations, shutdown backend."""

# DI lifecycle aliases
async def startup(self) -> None: ...     # calls initialize()
async def async_init(self) -> None: ...  # calls initialize()
```

### Core Operations

```python
async def get(
    self,
    key: str,
    namespace: str | None = None,
    default: Any = None,
) -> Any:
    """Get value from cache. Returns default on miss or error (never raises)."""

async def set(
    self,
    key: str,
    value: Any,
    *,
    ttl: int | None = None,
    namespace: str | None = None,
    tags: list[str] | None = None,
) -> bool:
    """Set cache value. Returns True on success."""

async def delete(
    self,
    key: str,
    namespace: str | None = None,
) -> bool:
    """Delete key from cache. Returns True if key existed."""

async def get_or_set(
    self,
    key: str,
    loader: Callable[[], Any],
    *,
    ttl: int | None = None,
    namespace: str | None = None,
    tags: list[str] | None = None,
    stampede_protection: bool = True,
) -> Any:
    """Get value or compute + store (cache-aside). Singleflight prevents stampede."""

async def exists(
    self,
    key: str,
    namespace: str | None = None,
) -> bool:
    """Check if key exists and is not expired."""

async def touch(
    self,
    key: str,
    *,
    ttl: int | None = None,
    namespace: str | None = None,
) -> bool:
    """Update access time and optionally extend TTL."""

async def clear(self, namespace: str | None = None) -> int:
    """Clear all entries in namespace. Returns count."""

async def get_stats(self) -> CacheStats:
    """Get aggregate cache statistics."""

async def health_check(self) -> bool:
    """Check backend health."""

async def warmup(self, entries: list[tuple[str, Any]], *, ttl: int | None = None) -> int:
    """Preload multiple entries. Returns count loaded."""
```

| Parameter | Type | Description |
|---|---|---|
| `key` | `str` | Cache key |
| `namespace` | `str \| None` | Namespace override (default: `config.namespace`) |
| `ttl` | `int \| None` | Time-to-live in seconds (default: `config.default_ttl`) |
| `tags` | `list[str] \| None` | Optional tags for tag-based invalidation |
| `loader` | `Callable[[], Any]` | Async or sync callable for cache-aside |
| `stampede_protection` | `bool` | Enable singleflight (dedup concurrent loaders) |

---

## CacheConfig

```python
class CacheConfig:
    def __init__(
        self,
        *,
        default_ttl: int = 300,
        max_size: int = 10000,
        eviction_policy: EvictionPolicy | str = EvictionPolicy.LRU,
        namespace: str = "default",
        key_prefix: str = "aq:",
        health_check_interval: int = 30,
        jitter_factor: float = 0.1,           # 10% TTL jitter
        stampede_timeout: float = 5.0,         # max wait for singleflight
        serializer: CacheSerializer | None = None,
    ):
```

| Parameter | Default | Description |
|---|---|---|
| `default_ttl` | `300` | Default TTL in seconds |
| `max_size` | `10000` | Max entries (for in-memory backends) |
| `eviction_policy` | `LRU` | Eviction strategy |
| `namespace` | `"default"` | Default namespace |
| `key_prefix` | `"aq:"` | Key prefix for isolation |
| `health_check_interval` | `30` | Seconds between health checks |
| `jitter_factor` | `0.1` | TTL random jitter (thundering herd prevention) |
| `stampede_timeout` | `5.0` | Max singleflight wait |
| `serializer` | `None` | Custom serializer |

---

## CacheEntry

```python
@dataclass(slots=True)
class CacheEntry:
    key: str
    value: Any
    created_at: float
    expires_at: float | None
    last_accessed: float
    access_count: int
    size_bytes: int
    tags: tuple[str, ...]
    namespace: str
    version: int

    @property
    def is_expired(self) -> bool: ...
    @property
    def ttl_remaining(self) -> float | None: ...
    @property
    def age(self) -> float: ...

    def touch(self) -> None:
        """Update last_accessed and increment access_count."""
```

---

## CacheStats

```python
@dataclass
class CacheStats:
    hits: int = 0
    misses: int = 0
    sets: int = 0
    deletes: int = 0
    evictions: int = 0
    errors: int = 0
    stampede_joins: int = 0    # singleflight deduplication count
    size: int = 0
    max_size: int = 0
    memory_bytes: int = 0
    backend: str = "unknown"
    uptime_seconds: float = 0.0

    @property
    def hit_rate(self) -> float: ...             # percentage
    @property
    def total_operations(self) -> int: ...
    @property
    def avg_get_latency_ms(self) -> float: ...
    @property
    def avg_set_latency_ms(self) -> float: ...
    @property
    def p99_get_latency_ms(self) -> float: ...
```

## EvictionPolicy

```python
class EvictionPolicy(str, Enum):
    LRU = "lru"       # Least Recently Used
    LFU = "lfu"       # Least Frequently Used
    TTL = "ttl"       # Time-To-Live only (no capacity eviction)
    FIFO = "fifo"     # First In First Out
    RANDOM = "random"  # Random eviction
```

---

## Backends

### `CacheBackend` (Protocol)

```python
class CacheBackend(Protocol):
    name: str

    async def initialize(self) -> None: ...
    async def shutdown(self) -> None: ...
    async def get(self, key: str) -> CacheEntry | None: ...
    async def set(self, entry: CacheEntry) -> bool: ...
    async def delete(self, key: str) -> bool: ...
    async def clear(self, namespace: str | None = None) -> int: ...
    async def get_stats(self) -> CacheStats: ...
    async def health_check(self) -> bool: ...
```

### MemoryBackend

```python
class MemoryBackend:
    def __init__(
        self,
        *,
        max_size: int = 10000,
        eviction_policy: EvictionPolicy = EvictionPolicy.LRU,
    ):
```

In-process storage with eviction. Fastest option for single-worker setups.

### RedisBackend

```python
class RedisBackend:
    def __init__(
        self,
        url: str = "redis://localhost:6379/0",
        *,
        key_prefix: str = "aq:",
        serializer: CacheSerializer | None = None,
        connection_pool_size: int = 10,
        socket_timeout: float = 5.0,
    ):
```

### CompositeBackend

```python
class CompositeBackend:
    """Multi-level cache (L1 → L2 → ...)."""
    def __init__(
        self,
        backends: list[CacheBackend],
        *,
        write_policy: str = "write_through",  # "write_through" | "write_back"
    ):
```

Example: `CompositeBackend([MemoryBackend(max_size=1000), RedisBackend(...)])`

### NullBackend

```python
class NullBackend:
    """No-op backend for testing/disabling cache."""
```

---

## Decorators

### `cached`

```python
def cached(
    key_prefix: str,
    *,
    ttl: int | None = None,
    namespace: str | None = None,
    key_builder: Callable | None = None,      # (func, args, kwargs) → key
) -> Callable:
```

```python
@cached("user:", ttl=300)
async def get_user(self, ctx, user_id: int):
    return await self.repo.get(user_id)
```

### `cache_aside`

```python
def cache_aside(
    key_template: str,                          # "user:{user_id}"
    *,
    ttl: int | None = None,
    namespace: str | None = None,
) -> Callable:
```

Wraps the function in `get_or_set` with stampede protection.

```python
@cache_aside("user:{user_id}", ttl=300)
async def get_user(self, ctx, user_id: int):
    return await self.repo.get(user_id)
```

### `invalidate`

```python
def invalidate(
    *key_templates: str,                        # "user:{user_id}", "users:list"
    namespace: str | None = None,
) -> Callable:
```

```python
@invalidate("user:{user_id}", "users:list")
async def update_user(self, ctx, user_id: int, data: dict):
    return await self.repo.update(user_id, data)
```

---

## CacheMiddleware

```python
class CacheMiddleware:
    """
    Full-page caching middleware.
    Caches response bodies based on request method + path + query.
    """
    def __init__(
        self,
        *,
        cache: CacheService,
        ttl: int = 60,
        methods: list[str] | None = None,    # default: ["GET", "HEAD"]
        exclude_paths: list[str] | None = None,
        vary_headers: list[str] | None = None,
    ):
```

---

## Serializers

### `CacheSerializer` (Protocol)

```python
class CacheSerializer(Protocol):
    def serialize(self, value: Any) -> bytes: ...
    def deserialize(self, data: bytes) -> Any: ...
```

### Built-in

```python
class JsonCacheSerializer:
    """JSON serializer. Safe, portable, human-readable."""

class MsgpackCacheSerializer:
    """MessagePack serializer. More compact than JSON (requires msgpack)."""

class PickleCacheSerializer:
    """Pickle serializer. Handles arbitrary Python objects."""
```

---

## Integration Example

```python
from aquilia.cache import CacheService, CacheConfig, EvictionPolicy
from aquilia.cache.backends import RedisBackend, MemoryBackend, CompositeBackend
from aquilia.cache.decorators import cached, cache_aside, invalidate

# Multi-level: L1 memory (fast, 1000 items) → L2 Redis (shared, persistent)
backend = CompositeBackend([
    MemoryBackend(max_size=1000, eviction_policy=EvictionPolicy.LRU),
    RedisBackend("redis://cache:6379/0"),
])

cache = CacheService(
    backend=backend,
    config=CacheConfig(
        default_ttl=300,
        namespace="myapp",
        key_prefix="aq:myapp:",
        jitter_factor=0.1,
    ),
)

# In a controller
class ProductsController(Controller):
    prefix = "/products"

    def __init__(self, cache: CacheService, product_service: ProductService):
        self.cache = cache
        self.service = product_service

    @GET("/{id:int}")
    async def get_product(self, ctx, id: int):
        product = await self.cache.get_or_set(
            f"product:{id}",
            loader=lambda: self.service.get(id),
            ttl=600,
        )
        return product

    @POST("/")
    async def create_product(self, ctx):
        data = await ctx.json()
        product = await self.service.create(**data)
        # Don't cache newly created, but invalidate list
        await self.cache.delete("products:list")
        return product, 201

    @PUT("/{id:int}")
    async def update_product(self, ctx, id: int):
        data = await ctx.json()
        product = await self.service.update(id, **data)
        await self.cache.set(f"product:{id}", product, ttl=600)
        await self.cache.delete("products:list")
        return product
```