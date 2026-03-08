# ASGI Integration Design

**Phase 12 — Integration Audit**
**Aquilia v1.0.1**

---

## 1. ASGI Adapter Architecture

The `ASGIAdapter` in `asgi.py` is the bridge between the ASGI protocol and
Aquilia's internal request/response model. It implements the ASGI 3.0
specification with three scope types.

### 1.1 Class Design

```python
class ASGIAdapter:
    __slots__ = (
        'controller_router',     # Route matching
        'controller_engine',     # Handler execution
        'middleware_stack',       # Middleware chain
        'socket_runtime',        # WebSocket support
        'server',                # Server back-reference
        '_cached_middleware_chain',  # Built once
        '_default_container',       # Cached container ref
        '_has_routes_cache',        # Route existence cache
        '_debug',                   # Debug mode cache
        '_server_runtime',          # Runtime registry cache
        'logger',                   # Logger
    )
```

### 1.2 Caching Strategy

The adapter aggressively caches to minimize per-request overhead:

| Cache | Purpose | Invalidated |
|-------|---------|-------------|
| `_cached_middleware_chain` | Middleware function chain | After startup |
| `_default_container` | Default DI container | After startup |
| `_has_routes_cache` | Whether any routes exist | After startup |
| `_debug` | Debug mode flag | After startup |
| `_server_runtime` | RuntimeRegistry ref | After startup |

All caches are invalidated during `handle_lifespan` after `server.startup()`
completes, ensuring post-startup state is used for actual requests.

---

## 2. HTTP Request Handling

### 2.1 Hot Path Optimization

```python
async def handle_http(self, scope, receive, send):
    # 1. Middleware chain: built once (idempotent)
    if self._cached_middleware_chain is None:
        self._build_cached_chain()

    # 2. Fast-path: /_health bypasses middleware entirely
    if path == "/_health":
        await self._serve_health(send, ...)
        return

    # 3. Route matching: sync, no await
    controller_match = self.controller_router.match_sync(path, method)

    # 4. DI container: O(1) COW child
    di_container = app_container.create_request_scope()

    # 5. RequestCtx: from object pool (zero-alloc)
    ctx = _ctx_pool.acquire(...)

    # 6. Execute cached chain
    response = await self._cached_middleware_chain(request, ctx)
```

### 2.2 Error Handling

```python
try:
    response = await self._cached_middleware_chain(request, ctx)
except Exception as e:
    metrics.request_errored()
    if self._is_debug():
        # Render beautiful debug page (React-style with dark/light mode)
        response = render_debug_exception_page(e, request, ...)
    else:
        # Generic 500 JSON response
        response = Response.json({"error": "Internal server error"}, status=500)
finally:
    metrics.request_finished(latency_ms)
    # DI cleanup delegated to request_scope_mw (FIXED: no double shutdown)
    _ctx_pool.release(ctx)
```

### 2.3 Health Endpoint

The `/_health` endpoint bypasses the entire middleware stack for minimal
latency. It includes:
- Engine metrics (in-flight, total requests, mean latency)
- Subsystem health via `HealthRegistry`
- Security headers (no-store, nosniff, deny framing)

---

## 3. WebSocket Handling

```python
async def handle_websocket(self, scope, receive, send):
    if self.socket_runtime:
        await self.socket_runtime.handle_websocket(scope, receive, send)
    else:
        await send({"type": "websocket.close", "code": 1003})
```

WebSocket connections are delegated to `AquilaSockets` which:
1. Creates a per-connection DI container via `_socket_container_factory`
2. Matches the path to a registered `@Socket` controller
3. Evaluates guards
4. Invokes `@OnConnect`, `@Event`, `@OnDisconnect` handlers

---

## 4. Lifespan Protocol

```python
async def handle_lifespan(self, scope, receive, send):
    while True:
        message = await receive()
        if message["type"] == "lifespan.startup":
            await self.server.startup()
            # Invalidate all caches after startup
            self._cached_middleware_chain = None
            self._default_container = None
            # ...
            await send({"type": "lifespan.startup.complete"})
        elif message["type"] == "lifespan.shutdown":
            await self.server.shutdown()
            await send({"type": "lifespan.shutdown.complete"})
            break
```

Notable: `SystemExit` during startup (from `DatabaseNotReadyError`) is
caught and treated as a warning — the server still reports startup.complete
to avoid uvicorn falling back to "lifespan unsupported" mode.

---

## 5. ASGI Protocol Compliance

| Feature | Status | Notes |
|---------|--------|-------|
| HTTP/1.1 scope | ✅ | Full request parsing |
| HTTP/2 scope | ✅ | Via uvicorn |
| WebSocket scope | ✅ | Controller-based |
| Lifespan scope | ✅ | Startup + shutdown |
| HEAD support | ✅ | Auto-fallback to GET |
| 405 Allow header | ✅ | Per RFC 7231 |
| Content-Length | ✅ | In health/error responses |
| Connection draining | ✅ | `graceful_shutdown()` |

---

## 6. Integration Points

### 6.1 ASGIAdapter → Server

The adapter holds a back-reference to `AquiliaServer` for:
- `server.startup()` / `server.shutdown()` during lifespan
- `server.runtime` for DI container lookup
- `server.health_registry` for health endpoint
- `server._inflight_requests` for graceful shutdown sync

### 6.2 ASGIAdapter → Middleware

The adapter builds and caches the middleware chain via `MiddlewareStack.build_handler()`.
The chain is invalidated after startup to pick up any middleware added during
the startup phase.

### 6.3 ASGIAdapter → Controller

Route matching produces a `ControllerRouteMatch` stored in `request.state["_controller_match"]`.
The `_final_handler` at the end of the middleware chain delegates to
`ControllerEngine.execute()`.
