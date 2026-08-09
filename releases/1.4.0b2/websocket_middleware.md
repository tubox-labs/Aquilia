# WebSocket Middleware Subsystem — v1.4.0b2

## Overview

Aquilia v1.4.0b2 introduces a full WebSocket middleware pipeline at `aquilia/sockets/middleware/`. Previously, per-connection security was limited to `SocketGuard.check_handshake()` (which runs before a connection exists) and `SocketGuard.check_message()` — which was never called by the runtime and has now been deprecated.

The new subsystem mirrors the ergonomics of `aquilia.middleware` so HTTP intuition transfers directly.

---

## Architecture

### Three Lifecycle Hooks

A WebSocket connection has three distinct moments that need middleware:

```
Client → connect → [on_connect chain] → handler
Client → message → [on_message chain] → handler
Client → close   → [on_disconnect chain] → handler
```

One registration feeds three chains. A middleware appears only in the chains whose hook it overrides, so an `on_message`-only middleware costs nothing at connect time.

### Package Layout

```
aquilia/sockets/middleware/
├── __init__.py               public API + backward compat aliases
├── base.py                   SocketMiddleware base + hook detection
├── chain.py                  SocketMiddlewareChain fluent builder
├── context.py                SocketCtx per-connection context
├── stack.py                  SocketMiddlewareStack registration + ordering
├── types.py                  ConnectHandler, MessageHandler, DisconnectHandler
└── builtin/
    ├── __init__.py
    ├── auth.py               SocketAuthMiddleware
    ├── authorization.py      SocketPermissionMiddleware
    ├── faults.py             SocketFaultMiddleware
    ├── logging.py            SocketLoggingMiddleware
    ├── metrics.py            SocketMetricsMiddleware
    ├── rate_limit.py         SocketRateLimitMiddleware
    └── validation.py         MessageValidationMiddleware
```

---

## `SocketMiddleware` Base Class

```python
from aquilia.sockets.middleware import SocketMiddleware

class PresenceMiddleware(SocketMiddleware):
    """Track connection presence across all namespaces."""

    async def on_connect(self, ctx, next_handler):
        """Called when a client establishes a WebSocket connection."""
        user_id = ctx.state.get("identity", {}).get("id")
        if user_id:
            await presence_store.mark_online(user_id)
        await next_handler(ctx)

    async def on_message(self, envelope, ctx, next_handler):
        """Called for each incoming WebSocket message.
        
        Returns None or a dict reply. Unlike HTTP, None is valid —
        most socket events legitimately reply with nothing.
        """
        await last_seen_store.update(ctx.connection_id)
        return await next_handler(envelope, ctx)

    async def on_disconnect(self, ctx, reason):
        """Called when a client disconnects. No next_handler — always terminal."""
        user_id = ctx.state.get("identity", {}).get("id")
        if user_id:
            await presence_store.mark_offline(user_id)
```

**Rules:**
- Override only the hooks you need.
- All hooks must be `async def`; validated at registration time.
- `on_message` may return `None`. A non-dict, non-None return is a `ConfigInvalidFault`.

---

## `SocketCtx` — Per-Connection Context

```python
from aquilia.sockets.middleware import SocketCtx

# ctx.state is a mutable dict for connection-scoped data
ctx.state["tenant_id"] = "acme"
ctx.state["identity"] = {"id": 42, "role": "admin"}
ctx.state["auth_checked_at"] = time.monotonic()  # used by SocketAuthMiddleware
```

`SocketCtx` is passed through every hook in the chain. Middleware may read and write `ctx.state` freely; no lifecycle cleanup is needed (the dict is garbage-collected with the connection).

---

## `SocketMiddlewareStack` — Registration and Ordering

```python
from aquilia.sockets.middleware import SocketMiddlewareStack, SocketMiddlewareDescriptor

stack = SocketMiddlewareStack(strict_priorities=False)

# Add middleware — appears in all three chains
stack.add(PresenceMiddleware(), scope="global", priority=50, name="presence")

# Add middleware scoped to a specific namespace
stack.add(ChatRoomMiddleware(), scope="namespace:/chat", priority=60, name="chatroom")

# Add middleware scoped to a specific event
stack.add(MessageFilterMiddleware(), scope="event:message.send", priority=70, name="filter")
```

### Scope System

| Scope | Format | Runs for |
|---|---|---|
| Global | `"global"` | All connections and messages |
| Namespace | `"namespace:/chat"` | Connections to `/chat` namespace |
| Event | `"event:message.send"` | Messages with event `message.send` |

Sort order: `global` (0) < `namespace:*` (1) < `event:*` (2), then by priority ascending. **Ascending priority = outer = runs first** — same contract as the HTTP stack.

### Priority Bands

| Band | Range | Purpose |
|---|---|---|
| Framework plumbing | 0–9 | Faults, logging, metrics |
| Framework security | 10–19 | Validation, rate limiting, auth |
| Reserved | 20–49 | Future framework use |
| Application | 50–99 | Your middleware (default: 50) |

---

## `SocketMiddlewareChain` — Fluent Builder

```python
from aquilia.sockets.middleware import SocketMiddlewareChain

# Empty chain — add your own
chain = SocketMiddlewareChain.chain()

# Fault handling only — bare minimum for any production socket
chain = SocketMiddlewareChain.minimal()

# Fault handling + message validation — recommended for most apps
chain = SocketMiddlewareChain.defaults()

# Fault + metrics + validation + rate limiting — production-ready
chain = SocketMiddlewareChain.production()

# Custom chain
chain = (
    SocketMiddlewareChain.chain()
    .use("aquilia.sockets.middleware.builtin.SocketFaultMiddleware", priority=2)
    .use("aquilia.sockets.middleware.builtin.SocketAuthMiddleware", priority=11)
    .use("modules.chat.middleware.PresenceMiddleware", priority=50)
    .use("modules.chat.middleware.ChatRoomMiddleware", priority=60, scope="namespace:/chat")
)
```

### `use()` Parameters

| Parameter | Type | Default | Description |
|---|---|---|---|
| `path` | `str` | required | Dotted import path of the middleware class |
| `priority` | `int` | `50` | Lower runs first |
| `scope` | `str` | `"global"` | `"global"`, `"namespace:<path>"`, or `"event:<name>"` |
| `name` | `str \| None` | class name | Display name for logging and diagnostics |
| `**kwargs` | | | Constructor keyword arguments |

### Preset Definitions

```
minimal()   = [SocketFaultMiddleware(priority=2)]

defaults()  = [SocketFaultMiddleware(priority=2),
               MessageValidationMiddleware(priority=10)]

production() = [SocketFaultMiddleware(priority=2),
                SocketMetricsMiddleware(priority=6),
                MessageValidationMiddleware(priority=10, max_payload_size=32768),
                SocketRateLimitMiddleware(priority=12, messages_per_second=10, burst=20)]
```

---

## Workspace Configuration

```python
# workspace.py
from aquilia import Workspace, Module
from aquilia.sockets.middleware import SocketMiddlewareChain

workspace = (
    Workspace("myapp")
    .module(
        Module("chat").route_prefix("/chat")
    )
    .socket_middleware(
        SocketMiddlewareChain.production()
    )
)
```

Custom chain with authentication:

```python
workspace = (
    Workspace("myapp")
    .socket_middleware(
        SocketMiddlewareChain.chain()
        .use("aquilia.sockets.middleware.builtin.SocketFaultMiddleware", priority=2)
        .use("aquilia.sockets.middleware.builtin.SocketAuthMiddleware", priority=11)
        .use("aquilia.sockets.middleware.builtin.SocketPermissionMiddleware", priority=12)
        .use("aquilia.sockets.middleware.builtin.MessageValidationMiddleware", priority=13)
        .use("aquilia.sockets.middleware.builtin.SocketRateLimitMiddleware",
             priority=14, messages_per_second=5, burst=10)
        .use("modules.chat.middleware.PresenceMiddleware", priority=50)
    )
)
```

---

## Built-in Middleware Reference

### `SocketFaultMiddleware` (priority=2)
Catches exceptions raised in `on_message` handlers and sends a structured fault envelope back to the client. Without this, faults are logged and the client is told nothing. Included in every preset.

### `SocketLoggingMiddleware`
Logs connection, disconnection, and message events with structured fields (connection ID, namespace, event type, timing).

### `SocketMetricsMiddleware` (priority=6)
Tracks per-connection message counts, bytes transferred, and error rates. Call `middleware.snapshot()` to retrieve counters.

### `MessageValidationMiddleware` (priority=10)
Enforces payload size limits (`max_payload_size`, default: 65536 bytes) and validates message envelope structure. Returns a structured fault if validation fails.

### `SocketRateLimitMiddleware` (priority=12)
Token bucket rate limiter keyed by client identity (authenticated users) or connection ID (anonymous). Default: `key_by="client"` so a user cannot multiply their message budget by reconnecting. Releases its bucket on disconnect via `BucketStore.discard()`.

```python
SocketRateLimitMiddleware(
    messages_per_second=10,  # sustained rate
    burst=20,                # token bucket capacity
    key_by="client",         # "client" | "connection" | "namespace"
)
```

### `SocketAuthMiddleware`
Re-checks authentication on long-lived connections (JWTs expire, sessions can be revoked). Stores the recheck timestamp in `ctx.state["auth_checked_at"]` rather than in a middleware-owned dict, so nothing leaks per connection.

### `SocketPermissionMiddleware`
Enforces permission checks on incoming messages. Configurable required permissions per event type.

---

## Security Parity Warning

> **Important:** The WebSocket middleware system is **separate** from the HTTP middleware system.
>
> HTTP middleware configured through `Workspace.security(...)` — CORS, rate limiting, CSRF, auth — does **NOT** apply to WebSocket messages. WebSocket connections are upgraded from HTTP but then operate on their own channel.
>
> **A socket surface is protected only by middleware registered on its own chain.**

This separation is intentional: the signatures and lifecycles genuinely differ. Rate-limiting algorithm implementations are shared (`aquilia._ratelimit`), but the pipeline stays separate.

---

## Deprecated: `SocketGuard.check_message`

`SocketGuard.check_message` is deprecated. No runtime code path has ever called it, so `MessageAuthGuard` and `RateLimitGuard` have never executed. An application relying on per-message guards has been running with no per-message auth and no rate limiting.

**Before (non-functional):**
```python
class MyGuard(SocketGuard):
    async def check_message(self, message, ctx):
        # This was never called
        return True
```

**After (functional):**
```python
class AuthCheckMiddleware(SocketMiddleware):
    async def on_message(self, envelope, ctx, next_handler):
        if not ctx.state.get("identity"):
            raise PermissionError("Authentication required")
        return await next_handler(envelope, ctx)
```

`check_handshake` is **not** deprecated and remains the supported way to gate a connection before it is established.

---

## Backward Compatibility

- `RateLimitMiddleware` resolves to `SocketRateLimitMiddleware` (alias preserved).
- `MiddlewareChain`, `LoggingMiddleware`, `MetricsMiddleware` raise `ImportError` with migration guidance (not bare `AttributeError`).
