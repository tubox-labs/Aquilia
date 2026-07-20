# Unified Resolution Engine

Before v1.3.2, Aquilia ran **two** resolution engines: the `Container` (constructor injection, scopes, caching) and a separate FastAPI-`Depends`-style `RequestDAG` (inline `Dep()` injection). They duplicated cycle detection, caching, and teardown logic. v1.3.2 folds them into **one engine owned by the container**.

## What Changed

`RequestDAG` is now a thin compatibility shim. Its public API is unchanged and existing code keeps working:

```python
dag = RequestDAG(container, request)
value = await dag.resolve(dep, param_type)   # delegates to container.resolve_dep(...)
await dag.teardown()                         # delegates to container._run_dep_teardowns()
```

All resolution state — the request-local cache, generator teardowns, and the resolving-set — now lives on the container. The real work moved to `Container.resolve_dep(dep, param_type, request=None)`.

The practical benefit: inline `Dep()` dependencies and constructor-injected services now share **one deduplicated graph**. A `get_db` dependency awaited by two sibling `Dep()`s and a constructor-injected repository resolves exactly once per request.

---

## Resolution Guarantees

The unified engine provides, in one place:

* **Sub-dependency dedup** — a diamond (A→C, B→C) resolves C once. A shared in-flight `Future` lets concurrent sibling branches await the same result instead of recomputing.
* **Parallel independent branches** — sub-dependencies of a `Dep` resolve concurrently via `asyncio.gather` when there is more than one.
* **Generator teardown (LIFO)** — a `yield`-style dependency registers its teardown, which runs on `container.shutdown()` before container finalizers.
* **True-cycle detection** — a task-local ancestor chain distinguishes a real self-cycle (raises `DIResolutionFault` "Circular…") from a benign diamond (awaits the shared future). Because `contextvars` copy per asyncio task, parallel `gather()` branches each see their own ancestor chain.

```python
from typing import Annotated
from aquilia.di import Dep

async def get_db():
    print("open");  yield "SESSION";  print("close")

async def get_repo(db: Annotated[str, Dep(get_db)]):  return {"db": db}
async def get_auth(db: Annotated[str, Dep(get_db)]):  return {"db": db}

@GET("/dashboard")
async def dashboard(
    self, ctx,
    repo: Annotated[dict, Dep(get_repo)],
    auth: Annotated[dict, Dep(get_auth)],
):
    return {"repo": repo, "auth": auth}
# "open" prints ONCE (dedup); "close" runs after the response (LIFO teardown).
```

---

## New Container Methods

### `add_dependency_link(app_name, container)`

The runtime counterpart to a manifest's `depends_on`. When a token is missing locally (and up the parent chain), resolution falls through to the linked sibling app container. The owning app instantiates and caches its own singletons exactly once. Wired automatically by the runtime from `depends_on` declarations.

```python
# billing's container may resolve auth-owned providers because
# billing's manifest declares depends_on=["auth"].
billing_container.add_dependency_link("auth", auth_container)
```

A cross-link cycle (A→B→A) raises `DependencyCycleError` via a task-local guard, instead of deadlocking. An undeclared cross-app dependency still raises `ProviderNotFoundError`.

### `create_child(scope="app", *, own_lifecycle=True)`

A generic hierarchical child container (copy-on-write provider dict; parent singletons resolved once at the owning level). Use it for per-tenant containers or multi-level scope trees. Distinct from `create_request_scope()`, which is specialized for the per-request hot path.

```python
root = Container(scope="app")
tenant = root.create_child(scope="app")
tenant.register(ClassProvider(TenantService, scope="app"))
```

### `await replace_provider(token, provider, *, tag=None)`

Production-safe atomic hot-swap. Copy-on-write safe (forks a shared provider dict first) and evicts the cached instance so the next resolution builds from the new provider. In-flight holders of the old instance are unaffected. Distinct from the test-only `override_container`.

```python
await container.replace_provider(
    PaymentGateway,
    ValueProvider(value=FallbackGateway(), token=PaymentGateway, scope="app"),
)
```

---

## Production Hardening

* **Persistent sync loop** — `Container.resolve()` and lazy proxies now drive the async path on one persistent per-thread event loop instead of creating and closing a fresh loop on every call. 50 sync `resolve()` calls create exactly one loop. Calling the sync path from inside a running loop raises `DIResolutionFault` (deadlock guard) — `await resolve_async()` instead.
* **Bounded pool waiters** — `PoolProvider(max_waiters=…)` (default from `pool_max_waiters`) fast-fails a burst against an exhausted pool with `DIResolutionFault` instead of thundering-herd queueing.
* **In-flight dedup** — under `parallel_resolution`, concurrent resolvers of the same uncached cacheable token share one instance, preserving the singleton/app/request identity guarantee.
* **Parallel resolution safety** — each concurrent branch gets a forked `ResolveCtx` (a copy of the cycle-guard stack), so parallelism cannot corrupt the shared resolution stack.
