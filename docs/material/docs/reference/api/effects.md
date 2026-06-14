# Effect System

The Effect system represents side-effects (DB, Cache, Queue, HTTP, Storage) as typed capabilities that handlers declare via `@requires()`. The runtime automatically acquires and releases effect resources around handler execution.

## Architecture

```
Effect → EffectKind → EffectProvider → EffectRegistry
```

- **Effect**: Typed token representing a capability
- **EffectKind**: Category enum (DB, CACHE, QUEUE, HTTP, STORAGE, CUSTOM)
- **EffectProvider**: ABC for provider implementations (acquire/release lifecycle)
- **EffectRegistry**: Central registry with DI integration

---

## EffectKind

```python
class EffectKind(Enum):
    DB = "db"
    CACHE = "cache"
    QUEUE = "queue"
    HTTP = "http"
    STORAGE = "storage"
    CUSTOM = "custom"
```

---

## Effect

```python
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
```

## Built-in Effect Types

### `DBTx`

```python
class DBTx(Effect):
    """Database transaction effect."""

    def __init__(self, mode: str = "read"):
        super().__init__("DBTx", mode=mode, kind=EffectKind.DB)
```

### `CacheEffect`

```python
class CacheEffect(Effect):
    """Cache effect."""

    def __init__(self, namespace: str = "default"):
        super().__init__("Cache", mode=namespace, kind=EffectKind.CACHE)
```

### `QueueEffect`

```python
class QueueEffect(Effect):
    """Queue/message publish effect."""

    def __init__(self, topic: str | None = None):
        super().__init__("Queue", mode=topic, kind=EffectKind.QUEUE)
```

### `HTTPEffect`

```python
class HTTPEffect(Effect):
    """HTTP client effect for outbound requests."""

    def __init__(self, service: str | None = None):
        super().__init__("HTTP", mode=service, kind=EffectKind.HTTP)
```

### `StorageEffect`

```python
class StorageEffect(Effect):
    """File/blob storage effect."""

    def __init__(self, bucket: str | None = None):
        super().__init__("Storage", mode=bucket, kind=EffectKind.STORAGE)
```

---

## EffectProvider (Abstract Base)

```python
class EffectProvider(ABC):
    """
    Base class for effect providers.

    Providers implement the actual capability (e.g., database connection).
    """

    @abstractmethod
    async def initialize(self):
        """Initialize the provider (called once at startup)."""

    @abstractmethod
    async def acquire(self, mode: str | None = None) -> Any:
        """
        Acquire a resource for this effect (called per-request).

        Args:
            mode: Optional mode specifier (e.g., 'read', 'write')
        Returns:
            Resource handle
        """

    @abstractmethod
    async def release(self, resource: Any, success: bool = True):
        """
        Release the resource (called at end of request).

        Args:
            resource: Resource handle from acquire()
            success: Whether request completed successfully
        """

    async def finalize(self):
        """Finalize provider (called at shutdown)."""

    async def health_check(self) -> dict[str, Any]:
        """
        Check provider health. Override for custom health reporting.
        Returns: {'healthy': True/False, ...}
        """
        return {"healthy": True}
```

### Lifecycle

```
initialize() → [acquire() → release()]* → finalize()
   startup           per-request             shutdown
```

---

## Provider Implementations

### `DBTxProvider`

```python
class DBTxProvider(EffectProvider):
    """Database transaction provider."""

    def __init__(self, connection_string: str):
        self.connection_string = connection_string
        self.pool = None

    async def initialize(self): ...
    async def acquire(self, mode: str | None = None) -> dict:
        """Returns connection handle with mode and acquired_at timestamp."""
    async def release(self, resource: Any, success: bool = True): ...
    async def health_check(self) -> dict: ...

```

### `CacheProvider`

```python
class CacheProvider(EffectProvider):
    """
    Cache effect provider backed by the real CacheService.

    If a CacheService is provided it is used for all operations;
    otherwise falls back to a simple in-memory dict.
    """

    def __init__(self, backend: str = "memory", *, cache_service: Any = None):
```

```python
    async def initialize(self): ...
    async def acquire(self, mode: str | None = None) -> CacheServiceHandle | CacheHandle:
        """Returns cache handle for namespace."""
    async def release(self, resource: Any, success: bool = True): ...
    async def finalize(self): ...
    async def health_check(self) -> dict: ...
```

### `QueueProvider`

```python
class QueueProvider(EffectProvider):
    """Queue/message publish effect provider."""

    def __init__(self, broker_url: str | None = None):

    async def initialize(self): ...
    async def acquire(self, mode: str | None = None) -> QueueHandle:
        """Returns queue handle for topic."""
    async def release(self, resource: Any, success: bool = True): ...
    async def finalize(self): ...
    async def health_check(self) -> dict: ...
```

### `TaskQueueProvider`

```python
class TaskQueueProvider(EffectProvider):
    """
    Task queue effect provider backed by AquiliaTasks TaskManager.

    Bridges the effect system with the background task subsystem.
    """

    def __init__(self, *, task_manager: Any = None):
```

```python
    async def acquire(self, mode: str | None = None) -> TaskQueueHandle | QueueHandle:
        """Returns handle for enqueuing tasks."""
```

### `HTTPProvider`

```python
class HTTPProvider(EffectProvider):
    """HTTP client effect provider for outbound requests."""

    def __init__(self, base_url: str | None = None, *, timeout: float = 30.0):
```

```python
    async def initialize(self):
        """Creates aiohttp.ClientSession with connection pooling."""

    async def acquire(self, mode: str | None = None) -> HTTPHandle:
        """Returns HTTP client handle."""

    async def finalize(self):
        """Closes the client session."""
```

### `StorageProvider`

```python
class StorageProvider(EffectProvider):
    """File/blob storage effect provider."""

    def __init__(self, root_path: str = "./storage"):
```

```python
    async def initialize(self):
        """Creates root directory."""

    async def acquire(self, mode: str | None = None) -> StorageHandle:
        """Returns storage handle for bucket."""

    async def health_check(self) -> dict: ...
```

---

## Resource Handles

### `CacheServiceHandle`

```python
class CacheServiceHandle:
    """Handle wrapping real CacheService for a given namespace."""

    async def get(self, key: str) -> Any | None: ...
    async def set(self, key: str, value: Any, ttl: int | None = None): ...
    async def delete(self, key: str): ...
```

### `CacheHandle`

```python
class CacheHandle:
    """Handle for fallback in-memory cache operations."""

    async def get(self, key: str) -> Any | None: ...
    async def set(self, key: str, value: Any, ttl: int | None = None): ...
    async def delete(self, key: str): ...
```

### `QueueHandle`

```python
class QueueHandle:
    """Handle for queue operations on a topic."""

    async def publish(self, payload: Any, *, headers: dict[str, str] | None = None):
        """Publish a message to the topic."""

    async def publish_batch(self, payloads: Sequence[Any]):
        """Publish multiple messages."""
```

### `TaskQueueHandle`

```python
class TaskQueueHandle:
    """Handle for enqueuing background tasks via the TaskManager."""

    async def enqueue(self, func, *args, **kwargs) -> str:
        """
        Enqueue a task for background execution.

        Args:
            func: Async callable or @task-decorated function
            *args: Positional arguments
            **kwargs: Keyword arguments
        Returns:
            Job ID string
        """
```

### `HTTPHandle`

```python
class HTTPHandle:
    """Handle for outbound HTTP requests."""

    async def get(self, url: str, **kwargs) -> Any: ...
    async def post(self, url: str, *, json: Any = None, **kwargs) -> Any: ...
    async def put(self, url: str, *, json: Any = None, **kwargs) -> Any: ...
    async def delete(self, url: str, **kwargs) -> Any: ...
```

### `StorageHandle`

```python
class StorageHandle:
    """Handle for file/blob storage operations."""

    async def read(self, key: str) -> bytes | None: ...
    async def write(self, key: str, data: bytes) -> None: ...
    async def delete(self, key: str) -> bool: ...
    async def exists(self, key: str) -> bool: ...
```

---

## EffectRegistry

```python
class EffectRegistry:
    """
    Registry for effect providers.

    Validates effect availability, manages provider lifecycles,
    and integrates with the DI system.
    """

    def __init__(self):
        self.providers: dict[str, EffectProvider] = {}
```

### Registration

```python
def register(self, effect_name: str, provider: EffectProvider):
    """Register an effect provider."""

def unregister(self, effect_name: str) -> EffectProvider | None:
    """Unregister and return an effect provider."""
```

### Lifecycle

```python
async def initialize_all(self):
    """Initialize all registered providers (lifecycle startup hook)."""

async def finalize_all(self):
    """Finalize all providers (lifecycle shutdown hook)."""

# DI lifecycle aliases
async def startup(self):
    """DI lifecycle startup hook."""

async def shutdown(self):
    """DI lifecycle shutdown hook."""
```

### Per-request Acquire/Release

```python
async def acquire(self, effect_name: str, mode: str | None = None) -> Any:
    """
    Acquire a resource for the named effect.

    Args:
        effect_name: Registered effect name
        mode: Optional mode specifier
    Returns:
        Resource handle
    Raises:
        KeyError: If effect is not registered
    """

async def release(self, effect_name: str, resource: Any, *, success: bool = True) -> None:
    """
    Release a resource for the named effect.

    Args:
        effect_name: Registered effect name
        resource: Resource handle from acquire()
        success: Whether the operation succeeded
    """
```

### Queries

```python
def has_effect(self, effect_name: str) -> bool:
    """Check if effect is available."""

def get_provider(self, effect_name: str) -> EffectProvider:
    """Get provider for effect. Raises EffectFault if not registered."""

def list_effects(self) -> list[str]:
    """Return all registered effect names."""

def get_metrics(self) -> dict[str, dict[str, int]]:
    """Return per-effect metrics: {'DBTx': {'acquires': 100, 'releases': 95, 'errors': 5}}."""
```

### Health

```python
async def health_check(self) -> dict[str, Any]:
    """Aggregate health from all providers.

    Returns:
        {
            "healthy": True,
            "initialized": True,
            "provider_count": 5,
            "providers": {
                "DBTx": {"healthy": True, ...},
                "Cache": {"healthy": True, ...},
                ...
            },
            "metrics": {...}
        }
    """
```

### DI Integration

```python
def register_with_container(self, container: Any):
    """
    Register this EffectRegistry and all effect providers with a DI container.

    - Registers EffectRegistry itself as app-scoped singleton
    - Registers individual providers as 'effect:{name}' tokens
    """
```

---

## Usage Patterns

### Basic Effect Registration

```python
from aquilia.effects import EffectRegistry, DBTxProvider, CacheProvider

registry = EffectRegistry()
registry.register("DBTx", DBTxProvider("sqlite:///app.db"))
registry.register("Cache", CacheProvider("redis", cache_service=redis_svc))

# At startup
await registry.initialize_all()

# At shutdown
await registry.finalize_all()
```

### Handler with Effects

```python
from aquilia.flow import requires

@requires("DBTx", "Cache")
async def get_user(ctx: FlowContext, user_id: int):
    cache = ctx.get_effect("Cache")
    cached = await cache.get(f"user:{user_id}")
    if cached:
        return cached

    db = ctx.get_effect("DBTx")
    user = await db.users.get(user_id)
    await cache.set(f"user:{user_id}", user.to_dict())
    return user
```

### Layer Composition

```python
from aquilia.flow import Layer

db_layer = Layer(
    name="DBTx",
    factory=lambda cfg: DBTxProvider(cfg.database_url),
    deps=["Config"],
)
cache_layer = Layer(
    name="Cache",
    factory=lambda cfg: CacheProvider("redis"),
    deps=["Config"],
)
http_layer = Layer(
    name="HTTP",
    factory=lambda: HTTPProvider(timeout=10.0),
)

# Compose and build
composition = Layer.merge(db_layer, cache_layer, http_layer)
await composition.register_with(registry, {"Config": app_config})
```