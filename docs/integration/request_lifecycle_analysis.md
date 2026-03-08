# Request Lifecycle Analysis

**Phase 12 — Integration Audit**
**Aquilia v1.0.1**

---

## 1. ASGI Entry Point

The entry point is `ASGIAdapter.__call__()` which dispatches based on
`scope["type"]`:

| Scope Type | Handler | Description |
|------------|---------|-------------|
| `http` | `handle_http()` | Standard HTTP request |
| `websocket` | `handle_websocket()` | WebSocket connection |
| `lifespan` | `handle_lifespan()` | Startup/shutdown events |

---

## 2. HTTP Request Lifecycle (Detailed)

### Phase 1: Request Creation

```python
# asgi.py:handle_http()
request = Request(scope, receive)
```

The `Request` object wraps the ASGI scope dict and receive callable.
Headers, query parameters, and body are lazily parsed on first access.

### Phase 2: Route Matching

```python
# Sync matching: O(1) for static, O(k) for dynamic
controller_match = self.controller_router.match_sync(path, method)
```

Three-tier matching strategy:
1. **Static routes** — Hash map lookup by `(method, path)` → O(1)
2. **Trie routes** — Segment-by-segment walk for parameterized routes → O(k)
3. **Regex fallback** — For complex patterns the trie can't represent

### Phase 3: HEAD Auto-Support

```python
if method == "HEAD" and controller_match is None:
    controller_match = self.controller_router.match_sync(path, "GET")
```

HTTP/1.1 §9.4 compliance: HEAD must succeed wherever GET does.
Body is stripped from the response in Phase 9.

### Phase 4: 405 Detection

```python
allowed = self.controller_router.get_allowed_methods(path)
if allowed:
    await self._send_method_not_allowed(send, sorted(allowed))
```

If the path exists but the method isn't allowed, returns 405 with
`Allow` header listing valid methods.

### Phase 5: DI Container Resolution

```python
app_container = runtime.di_containers.get(app_name)
di_container = app_container.create_request_scope()
```

Creates a request-scoped child container via copy-on-write:
- Inherits all app-scoped providers without copying
- First `register()` call triggers copy (COW optimization)
- Automatically cleaned up by `request_scope_mw`

### Phase 6: RequestCtx Pooling

```python
ctx = _ctx_pool.acquire(request=request, container=di_container, ...)
```

Object pool avoids per-request allocation overhead.
Released back to pool in the finally block.

### Phase 7: Middleware Chain Execution

The cached middleware chain is built once and reused:

```
FaultMiddleware (2)
  → request_scope_mw (5)
    → [Security stack: ProxyFix(3), HTTPS(4), Static(6), ...]
      → Session/Auth (15)
        → CSRF (20) — NOW AFTER session
          → I18n (24)
            → Templates (25)
              → Cache (26)
                → _final_handler
```

### Phase 8: Controller Execution

Inside `_final_handler`:

```python
controller_match = request.state.get("_controller_match")
return await self.controller_engine.execute(
    controller_match.route, request, controller_match.params, ctx.container
)
```

The `ControllerEngine.execute()` pipeline:

1. **Fast path check** — Monkeypatched handlers (admin, docs) skip DI
2. **Build RequestCtx** — Identity, session, container, state
3. **Throttle enforcement** — Class + route level rate limits
4. **Body size limit** — Content-Length vs max_body_size
5. **Singleton lifecycle init** — Once per controller class
6. **DI instantiation** — `ControllerFactory.create()`
7. **Class-level FlowPipeline** — Guards, transforms, hooks
8. **Method-level FlowPipeline** — Per-route guards/transforms
9. **Clearance evaluation** — Declarative access control
10. **Parameter binding** — Path, query, body, blueprint deserialization
11. **Interceptor before hooks** — Pre-handler hooks
12. **Handler execution** — With optional timeout
13. **Interceptor after hooks** — Post-handler hooks
14. **Exception filters** — Structured error handling
15. **Response conversion** — Dict/str/Blueprint → Response

### Phase 9: Response Finalization

```python
# HEAD body stripping
if is_head_fallback and response is not None:
    response = Response(content=b"", status=response.status, ...)

await response.send_asgi(send)
```

### Phase 10: Cleanup

```python
finally:
    # Metrics
    metrics.request_finished(latency_ms)
    # DI container cleanup handled by request_scope_mw (FIXED: no double shutdown)
    # Return ctx to pool
    _ctx_pool.release(ctx)
```

---

## 3. WebSocket Lifecycle

```
handle_websocket(scope, receive, send)
  → AquilaSockets.handle_websocket()
    → Socket container factory (per-connection DI)
    → Route matching (SocketRouter)
    → Guard evaluation
    → Controller instantiation (DI)
    → OnConnect handler
    → Event loop (message dispatch)
    → OnDisconnect handler
    → Container cleanup
```

---

## 4. Lifespan Lifecycle

```
handle_lifespan(scope, receive, send)
  → lifespan.startup
    → server.startup()
      → autodiscovery
      → controller loading + compilation
      → admin wiring
      → lifecycle hooks
      → model registration
      → subsystem initialization
    → lifespan.startup.complete
  → lifespan.shutdown
    → server.shutdown()
      → lifecycle shutdown (reverse order)
      → mail/tasks/cache/storage shutdown
      → DI container cleanup
      → effect finalization
      → WebSocket shutdown
      → database disconnect
    → lifespan.shutdown.complete
```

---

## 5. Performance Characteristics

| Phase | Optimization | Complexity |
|-------|-------------|------------|
| Route matching (static) | Hash map | O(1) |
| Route matching (dynamic) | Segment trie | O(k), k=path depth |
| Middleware chain | Built once, cached | O(1) per request |
| DI container | Copy-on-write child | O(1) create, O(n) first write |
| RequestCtx | Object pool | Zero allocation hot path |
| Request ID | `os.urandom(16).hex()` | ~4× faster than uuid4 |
| Header scan | Raw ASGI bytes | Avoids Headers object parse |
| Metrics | Lock-free counters | Async-safe, no contention |

---

## 6. Request Lifecycle Timing (Typical)

```
┌─────────────┬──────────────────────────────────────┐
│ Phase       │ Duration                             │
├─────────────┼──────────────────────────────────────┤
│ ASGI parse  │ ~5µs (scope extraction)              │
│ Route match │ ~2µs (static) / ~10µs (dynamic)      │
│ DI create   │ ~3µs (COW child container)           │
│ Middleware   │ ~50-200µs (varies by stack depth)    │
│ Controller  │ ~100µs-50ms (depends on handler)     │
│ Cleanup     │ ~5µs (pool release + metrics)        │
└─────────────┴──────────────────────────────────────┘
```
