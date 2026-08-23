# Middleware Architecture & WebSocket Pipeline

Aquilia v1.4.0 completely overhauls the HTTP middleware architecture to eliminate cyclic dependencies and introduces a dedicated WebSocket middleware pipeline.

---

## 1. HTTP Middleware Restructure (`aquilia.middleware`)

The HTTP middleware subsystem has been split into five clean layers:

```
aquilia/middleware/
├── core/             # Base class (Middleware), Priority, Scope, Types (Fault-free leaf zone)
├── stack/            # Registration, chain compilation, MiddlewareStack, collision checks
├── builtin/          # Framework-owned middleware & security suite (CORS, CSP, CSRF, HSTS, etc.)
├── instrumentation/  # OpenTelemetry TracingInstrument and MetricsInstrument
└── utils/            # Transport-agnostic ordering, throttling, and negotiation helpers
```

### Key Enhancements:
* **Fault-Free Leaf Zone (`core/`):** `Middleware` base class lives in an isolated leaf module with zero dependencies on `aquilia.faults`, eliminating circular import errors on startup.
* **Declarative Hook Lifecycle:** Middleware can implement dedicated hook methods instead of raw `__call__`:
  ```python
  class CustomMiddleware(Middleware):
      name = "custom"
      priority = 50

      async def before(self, request, ctx):
          # Runs before route handler
          pass

      async def after(self, request, ctx, response):
          # Runs after route handler
          return response

      def should_run(self, request, ctx) -> bool:
          # Dynamic execution guard
          return True
  ```
* **Collision Detection:** `MiddlewareStack(strict_priorities=True)` raises `MiddlewarePriorityCollisionFault` on ambiguous execution orders.
* **Rate Limiting Hardening:**
  * Fixed bug where rate-limited responses returned status `500` instead of `429`.
  * Per-user identity rate limits now execute at priority `16` (after `AuthMiddleware` at `15`).

---

## 2. WebSocket Middleware Pipeline (`aquilia.sockets.middleware`)

WebSockets require distinct lifecycle stages compared to HTTP. v1.4.0 delivers a dedicated 3-hook WebSocket middleware pipeline.

```python
from aquilia.sockets.middleware import SocketMiddleware

class PresenceMiddleware(SocketMiddleware):
    name = "presence"
    priority = 20

    async def on_connect(self, ctx, next_handler):
        user_id = ctx.state.get("user_id")
        await register_online_user(user_id)
        await next_handler(ctx)

    async def on_message(self, envelope, ctx, next_handler):
        # Validate or transform incoming socket envelope
        return await next_handler(envelope, ctx)

    async def on_disconnect(self, ctx, reason):
        user_id = ctx.state.get("user_id")
        await unregister_online_user(user_id)
```

### Built-in Socket Middleware
1. **`SocketFaultMiddleware`** (Priority 2): Catches unhandled socket exceptions and emits standardized error envelopes.
2. **`SocketMetricsMiddleware`** (Priority 6): Captures active connection counts, frame counters, and throughput.
3. **`MessageValidationMiddleware`** (Priority 10): Validates incoming payload schemas.
4. **`SocketRateLimitMiddleware`** (Priority 12): Protects socket connections against message floods using transport-agnostic token buckets.
5. **`SocketAuthMiddleware`**: Authenticates incoming connection handshakes.
6. **`SocketPermissionMiddleware`**: Evaluates RBAC/ABAC clearance on socket events.
7. **`SocketLoggingMiddleware`**: Structured logging for connect, message, and disconnect events.

### Workspace Configuration:
```python
from aquilia import Workspace
from aquilia.sockets.middleware import SocketMiddlewareChain

Workspace.socket_middleware(
    SocketMiddlewareChain.production()  # or .minimal(), .defaults()
)
```
