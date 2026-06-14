# Sessions Module

> `aquilia.sessions` — Cryptographic session management

The Sessions module provides a complete session management system with cryptographic cookie transport, memory and Redis stores, session policies, guards, and stateful session objects.

## When to Use

Use the Sessions module when you need:

- Server-side sessions with client-side cookie transport
- Session-based authentication
- Per-user state persistence across requests
- Session guards for route protection
- Typed session state objects (cart, preferences)

## Key Classes

| Class | Purpose |
|---|---|
| `SessionEngine` | Central session lifecycle manager |
| `Session` | Individual session with data and expiry |
| `SessionPolicy` | Session configuration (TTL, renewal, security) |
| `SessionID` | Typed session identifier |
| `CookieTransport` | HMAC-signed cookie transport |
| `MemoryStore` | In-memory session store (dev) |
| `SessionGuard` | Route guard for session requirements |
| `SessionContext` | Context manager for session operations |
| `SessionState` | Typed session data container |
| `SessionPrincipal` | Authenticated principal within a session |

## Quick Example

```python
from aquilia.sessions import SessionEngine, SessionPolicy, CookieTransport, stateful

engine = SessionEngine(
    store=MemoryStore(),
    transport=CookieTransport(secret="session-secret"),
    policy=SessionPolicy(ttl=3600, renewal=True),
)

# Stateful session data
from aquilia.sessions.state import CartState, UserPreferencesState, SessionState

class AppSession(SessionState):
    cart: CartState
    prefs: UserPreferencesState

@stateful(AppSession)
class CartController(Controller):
    @POST("/cart/add")
    async def add_item(self, ctx: RequestCtx):
        ctx.session.state.cart.add(item_id="abc", qty=2)
        return Response.json({"ok": True})
```

## Import Path

```python
from aquilia.sessions import (
    SessionEngine,
    Session,
    SessionPolicy,
    SessionID,
    CookieTransport,
    MemoryStore,
    SessionGuard,
    SessionState,
)
```

## Related Modules

- [auth](../auth/index.md) — Session-based authentication bridge
- [core/middleware](../core/middleware.md) — SessionMiddleware in the chain
- [core/signing](../core/signing.md) — SessionSigner for cookie integrity