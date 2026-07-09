# Aquilia Effect System

The Effect System provides structured, type-safe resource injection for Aquilia applications. Inspired by functional effect systems (specifically Effect-TS), it separates *what* resource a handler requires from *how* that resource is constructed, accessed, and cleaned up. This pattern decouples handlers from infrastructure, ensuring clean boundaries, testability, and robust resource safety.

An "Effect" acts as a typed token representing a dependency (e.g. database transaction, cache namespace, message queue, HTTP client, or blob storage bucket). Instead of instantiating clients directly or pulling them from global state, handlers declare their required effects using the `@requires` decorator. The Aquilia runtime automatically manages the lifecycle (acquisition, verification, and releasing/committing) of these resources around handler invocation.

---

## Core Architecture & Components

The system is built on four core layers:

1. **Effect Token (`Effect`)**:
   A symbolic description of a capability, parameterized by a name and an optional mode (e.g. `DBTx["read"]` vs. `DBTx["write"]`).
2. **EffectProvider (`EffectProvider`)**:
   The abstract base class representing the implementation backend for an effect. It manages the lifecycle of actual resources through five hook methods:
   * `initialize()`: One-time setup during application bootstrap.
   * `acquire(mode)`: Setup executed per-request or per-scope to create a handle.
   * `release(resource, success)`: Teardown executed per-request, handling commits, rollbacks, or connection cleanup.
   * `finalize()`: One-time shutdown cleanup when the server stops.
   * `health_check()`: Aggregates capability health statistics.
3. **EffectRegistry (`EffectRegistry`)**:
   A centralized registry storing mappings of effect names to providers. It integrates with the Dependency Injection (DI) system as an application-scoped singleton.
4. **Resource Handles**:
   Lightweight, specialized classes that act as the interface through which handlers interact with the underlying capability. For example, `DBTxHandle`, `CacheServiceHandle`, `QueueHandle`, `HTTPHandle`, and `StorageHandle`.

---

## Request Lifecycle Execution Flow

The framework executes a clean three-step lifecycle for every request requesting effects:

```
[HTTP Request]
       │
       ▼
[FlowContextMiddleware]  ◄─── Creates request-scoped FlowContext
       │
       ▼
[EffectMiddleware]      ◄─── 1. Detects @requires tokens on handler
       │                     2. Lazy-resolves providers via proxy
       │                     3. Runs provider.acquire() to lease handle
       │                     4. Injects handle into request state & FlowContext
       ▼
[Controller Handler]    ◄─── Interacts with ctx.get_effect("DBTx")
       │
       ▼
[EffectMiddleware]      ◄─── 1. Runs provider.release(resource, success=True/False)
       │                     2. DBTx commits on success, rolls back on exception
       ▼
[HTTP Response]
```

---

## Workspace Integration

To enable the Effect system in your workspace, register `FlowContextMiddleware` and `EffectMiddleware` in your `workspace.py` file.

> [!IMPORTANT]
> **Middleware Execution Order:**
> `FlowContextMiddleware` must come **before** `EffectMiddleware` in the middleware chain. This ensures that the `FlowContext` is initialized before the Effect Middleware attempts to propagate acquired resource handles into it.

### Code Example: Workspace Setup

```python
from aquilia.workspace import Workspace
from aquilia.middleware import MiddlewareChain

app = (
    Workspace.new("my-project")
    .middleware(
        MiddlewareChain.chain()
        .defaults()
        # FlowContextMiddleware (priority 14) executes before EffectMiddleware (priority 15)
        .use("aquilia.middleware_ext.FlowContextMiddleware", priority=14)
        .use("aquilia.middleware_ext.EffectMiddleware", priority=15)
    )
)
```

You can also explicitly register providers during integration setups:

```python
from aquilia.integrations import Integration

Integration.effects(
    providers={
        "DBTx": {
            "class": "aquilia.effects.DBTxProvider",
            "args": {"connection_string": "postgresql://user:pass@localhost:5432/db"}
        },
        "Cache": {
            "class": "aquilia.effects.CacheProvider",
            "args": {"backend": "redis"}
        }
    }
)
```

---

## Declaring Required Effects

Route handlers and flow pipeline nodes declare their capability requirements using the `@requires` decorator.

> [!WARNING]
> **Decorator Order is Critical:**
> `@requires` must be applied **closer to the function body** than the HTTP route decorator (e.g. `@POST` or `@GET`). Python applies decorators from the bottom up, so `@requires` must attach metadata to the raw function first.

```python
from aquilia.controller import Controller, POST, RequestCtx
from aquilia.flow import requires

class CorporateOrderIngestController(Controller):
    # Correct order: @POST wraps the function decorated by @requires
    @POST("/orders/ingest")
    @requires("DBTx", "Cache")
    async def ingest_corporate_order(self, ctx: RequestCtx) -> dict:
        db = ctx.get_effect("DBTx")        # Returns a DBTxHandle
        cache = ctx.get_effect("Cache")    # Returns a CacheServiceHandle
        
        body = await ctx.json()
        
        # 1. Store order payload in Database
        order_id = await db.fetch_val(
            "INSERT INTO orders (corporate_id, total, status) VALUES (?, ?, ?) RETURNING id",
            (body["corporate_id"], body["total"], "RECEIVED")
        )
        
        # 2. Update cache with hot corporate statistics
        latest_orders = await cache.get(f"corp:{body['corporate_id']}:recent") or []
        latest_orders.insert(0, {"order_id": order_id, "total": body["total"]})
        await cache.set(f"corp:{body['corporate_id']}:recent", latest_orders[:5], ttl=600)
        
        return {"status": "order_ingested", "order_id": order_id}
```

---

## Built-in Effects

Aquilia packages five core capabilities:

### 1. Database Transaction (`DBTx`)
Leases database connections and manages atomic scopes.
* **Modes**:
  * `DBTx["read"]`: Read-only connection, optimized for SELECT queries, can target read replicas.
  * `DBTx["write"]`: Starts an active transaction block. Automatically commits on successful request return, or executes a rollback on handler exception.
* **Handle Interface (`DBTxHandle`)**:
  * `await execute(sql, params)`
  * `await fetch_all(sql, params)`
  * `await fetch_one(sql, params)`
  * `await fetch_val(sql, params)`
  * `await execute_many(sql, params_list)`

### 2. Cache Effect (`CacheEffect`)
Provides key-value caching scoped by namespace to prevent key overlap.
* **Handle Interface (`CacheServiceHandle` / `CacheHandle`)**:
  * `await get(key)`: Returns deserialized value or `None` on cache miss.
  * `await set(key, value, ttl=None)`: Caches value. Optional TTL is in seconds.
  * `await delete(key)`: Deletes key, returns status.

### 3. Queue Effect (`QueueEffect`)
Publishes events to message brokers or enqueues asynchronous background tasks.
* **Modes**: Parameterized by topic name (e.g. `QueueEffect("telemetry")`).
* **Handle Interface**:
  * **Broker Publish (`QueueHandle`)**:
    * `await publish(payload, headers=None)`: Sends payload with metadata.
    * `await publish_batch(payloads)`: Sends list of payloads.
  * **Task Worker (`TaskQueueHandle`)**:
    * `await enqueue(func, *args, **kwargs)`: Submits a background task to the worker runner, returning the Job ID.

### 4. HTTP client (`HTTPEffect`)
Injects pre-configured HTTP clients with built-in connection reuse, timeout controls, and headers.
* **Handle Interface (`HTTPHandle`)**:
  * `await get(url, **kwargs)`
  * `await post(url, json=None, **kwargs)`
  * `await put(url, json=None, **kwargs)`
  * `await delete(url, **kwargs)`

### 5. Storage Effect (`StorageEffect`)
Provides read/write file and blob operations across local filesystems and cloud buckets.
* **Modes**: Scoped by bucket name (e.g. `StorageEffect("avatars")`).
* **Handle Interface (`StorageHandle`)**:
  * `await read(key)`: Reads file bytes.
  * `await write(key, bytes)`: Writes file bytes.
  * `await exists(key)`: Checks file existence.
  * `await delete(key)`: Deletes file.

---

## Defining Custom Effects

To register new, user-defined capability backends, subclass `Effect` and `EffectProvider`:

```python
import aiohttp
from typing import Any, dict
from aquilia.effects import Effect, EffectProvider, EffectKind

# 1. Custom token
class SlackEffect(Effect[str]):
    def __init__(self, channel: str = "general"):
        super().__init__("Slack", mode=channel, kind=EffectKind.CUSTOM)

# 2. Resource handle
class SlackHandle:
    def __init__(self, session: aiohttp.ClientSession, webhook_url: str, channel: str):
        self.session = session
        self.webhook_url = webhook_url
        self.channel = channel

    async def send_message(self, text: str, blocks: list[dict] | None = None) -> None:
        payload = {
            "channel": f"#{self.channel}",
            "text": text,
            "blocks": blocks or []
        }
        async with self.session.post(self.webhook_url, json=payload) as resp:
            resp.raise_for_status()

# 3. Custom provider
class SlackProvider(EffectProvider):
    def __init__(self, webhook_url: str):
        self.webhook_url = webhook_url
        self.session = None

    async def initialize(self) -> None:
        self.session = aiohttp.ClientSession()

    async def acquire(self, mode: str | None = None) -> SlackHandle:
        channel = mode or "general"
        return SlackHandle(self.session, self.webhook_url, channel)

    async def release(self, resource: SlackHandle, success: bool = True) -> None:
        pass

    async def finalize(self) -> None:
        if self.session:
            await self.session.close()
```

Register the custom provider with the registry during bootstrap:
```python
registry.register("Slack", SlackProvider(webhook_url="https://hooks.slack.com/..."))
```
Use it in controllers:
```python
@POST("/notify/incident")
@requires("Slack")
async def dispatch_incident(self, ctx: RequestCtx):
    slack = ctx.get_effect("Slack")
    await slack.send_message(text="System incident alert dispatched.")
```
