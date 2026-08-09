# Middleware Package Restructure — v1.4.0b2

## Overview

Aquilia v1.4.0b2 replaces the monolithic `aquilia/middleware.py` (647 lines) with a structured package at `aquilia/middleware/`. The restructure resolves a long-standing circular import between `aquilia.middleware` and `aquilia.faults`, enables isolated middleware imports in scripts and unit tests, and establishes clear dependency boundaries enforced by the test suite.

---

## Package Layout

```
aquilia/middleware/
├── __init__.py               public API (lazy re-exports via aquilia.lazy)
├── core/                     fault-free leaf zone
│   ├── __init__.py
│   ├── base.py               Middleware base class + hook sentinels
│   ├── descriptor.py         MiddlewareDescriptor, MiddlewareMeta
│   ├── priority.py           Priority constants + sort_key
│   └── types.py              Handler, RequestHandler, Scope, MiddlewareCallable
├── stack/                    registration and compilation
│   ├── __init__.py
│   ├── builder.py            ChainBuilder (closure fold)
│   ├── errors.py             MiddlewareRegistrationFault, MiddlewarePriorityCollisionFault, MiddlewareContractFault
│   ├── registry.py           MiddlewareStack
│   └── validation.py         startup contract checks
├── instrumentation/          tracing and metrics wrappers
│   ├── __init__.py
│   ├── base.py               Instrument protocol
│   ├── metrics.py            MetricsInstrument
│   └── tracing.py            TracingInstrument
├── builtin/                  framework-owned middleware
│   ├── __init__.py
│   ├── compression.py        CompressionMiddleware
│   ├── effects.py            EffectMiddleware
│   ├── exceptions.py         ExceptionMiddleware
│   ├── logging.py            LoggingMiddleware
│   ├── rate_limit.py         RateLimitMiddleware (HTTP)
│   ├── request_id.py         RequestIdMiddleware
│   ├── request_scope.py      ServerRequestScopeMiddleware
│   ├── session.py            SessionMiddleware
│   ├── static.py             StaticMiddleware
│   ├── timeout.py            TimeoutMiddleware
│   └── security/             security middleware subpackage
│       ├── __init__.py
│       ├── cors.py           CORSMiddleware
│       ├── csp.py            CSPMiddleware
│       ├── csrf.py           CSRFMiddleware
│       ├── headers.py        SecurityHeadersMiddleware
│       ├── hsts.py           HSTSMiddleware
│       ├── https_redirect.py HTTPSRedirectMiddleware
│       └── proxy_fix.py      ProxyFixMiddleware
└── utils/                    transport-agnostic helpers
    ├── __init__.py
    ├── negotiation.py        content negotiation
    ├── ordering.py           scope_rank, find_collision, collision_message
    ├── status.py             HTTP status utilities
    └── throttling.py         TokenBucket, SlidingWindowCounter, BucketStore
```

---

## The Circular Import Problem (Fixed)

### Previous Behavior

Any isolated script or unit test importing `Middleware` first crashed with `ImportError`:

```python
# This crashed in v1.4.0b1 and earlier:
from aquilia import Middleware
from aquilia.middleware import Middleware
```

**Root cause**: The import cycle was:
```
aquilia/middleware.py    → from aquilia.faults import Fault, FaultDomain
aquilia/faults/__init__ → re-exports from aquilia.faults.engine
aquilia/faults/engine.py → from aquilia.middleware import Middleware
```

Real apps avoided this by accident — normal bootstrap imports `AquiliaServer`, which pulls in `aquilia.faults` before `aquilia.middleware` and resolves the cycle in the safe order. Any isolated script or unit test importing `Middleware` first crashed.

### New Behavior

The `Middleware` base class lives in `aquilia/middleware/core/base.py`, a fault-free leaf module that imports nothing from `aquilia.faults`. Both sides (`aquilia.middleware` and `aquilia.faults.engine`) import the base from there.

`aquilia.middleware` itself resolves exports lazily via `aquilia.lazy.install_lazy_exports` — the same primitive the top-level `aquilia` barrel uses. An eager façade would pull `aquilia.faults`, `aquilia.debug`, and `aquilia.inspector` into the graph at import time, resurrecting the cycle through the package rather than the module.

`tests/test_import_order.py` enforces the boundary in a subprocess so sys.modules caching cannot hide order-sensitivity.

---

## New `Middleware` Base Class Hooks

The `Middleware` base class now provides four hook entry points in addition to `__call__`:

```python
from aquilia.middleware import Middleware

class TenantMiddleware(Middleware):
    # Declarative metadata — used by stack.add() as defaults
    name = "tenant"
    priority = 50           # from Priority class
    scope = "global"        # "global", "app", "controller:users", etc.
    tags = ("multi-tenant",)

    # Hook 1: inspect the request BEFORE the chain continues
    async def before(self, request, ctx) -> Response | None:
        tenant = request.header("x-tenant-id")
        if not tenant:
            return Response.json({"error": "missing tenant"}, status=400)
        ctx.state["tenant"] = tenant
        return None  # continue

    # Hook 2: inspect/rewrite the response on the way OUT
    async def after(self, request, ctx, response) -> Response:
        response.headers["X-Tenant"] = ctx.state["tenant"]
        return response

    # Hook 3 (opt-in): decide per request whether this middleware runs
    async def should_run(self, request, ctx) -> bool:
        return request.path.startswith("/api/")

    # Hook 4 (opt-in): acquire resources at lifespan startup
    async def setup(self, app) -> None:
        self._db = await connect_tenant_db()

    # Hook 5 (opt-in): release resources at lifespan shutdown
    async def teardown(self, app) -> None:
        await self._db.close()
```

**Design**:
- `handle()` is the primary hook — wraps the continuation. The default dispatches `before` then `after`.
- Override `__call__(request, ctx, next_handler)` directly for full control (all pre-v1.3 middleware works unchanged).
- Hook resolution happens at registration time, not per request. A subclass overriding only `before` gets a compiled chain that never calls `after` on the base class.

---

## Priority Constants

Priority constants moved from scattered docstring tables in `server.py` to `aquilia.middleware.core.priority.Priority`:

```python
from aquilia.middleware.core.priority import Priority

class Priority:
    # Plumbing (0-9)
    EXCEPTION = 1
    FAULTS = 2
    PROXY_FIX = 3       # must precede anything IP-dependent
    HTTPS_REDIRECT = 4
    REQUEST_SCOPE = 5
    VERSIONING = 5      # known collision with REQUEST_SCOPE (documented)
    STATIC = 6

    # Security (10-29)
    SECURITY_HEADERS = 7
    HSTS = 8
    CSP = 9
    REQUEST_ID = 10
    CORS = 11
    RATE_LIMIT_ANON = 12   # anonymous/IP rules only
    INSPECTOR = 13          # moved from 11 to fix collision with CORS
    INSPECTOR_TOOLBAR = 14  # moved from 12 to fix collision with RATE_LIMIT_ANON
    AUTH = 15               # AquilAuthMiddleware / SessionMiddleware
    RATE_LIMIT_IDENTITY = 16  # identity rules; must follow AUTH
    CSRF = 20               # needs session established by AUTH

    # Framework features (30-49)
    I18N = 24
    TEMPLATES = 25
    CACHE = 26

    # Application (50-99)
    APPLICATION_DEFAULT = 50
```

The old values (inspector at 11/12) were colliding with CORS and RATE_LIMIT_ANON. Collisions were silently resolved by registration order. Now:
1. They are documented explicitly.
2. Inspector moved to 13/14 to eliminate the collisions.
3. The collision detection system warns about any remaining same-scope/same-priority pairs.

---

## Priority Collision Detection

`MiddlewareStack.add()` now detects same-scope, same-priority pairs:

```python
from aquilia.middleware import MiddlewareStack
from aquilia.middleware.stack.errors import MiddlewarePriorityCollisionFault

# Default: warn at boot
stack = MiddlewareStack()
stack.add(MyMiddlewareA(), priority=50)
stack.add(MyMiddlewareB(), priority=50)  # → WARNING: priority collision at scope=global, priority=50

# Strict: raise at boot
stack = MiddlewareStack(strict_priorities=True)
stack.add(MyMiddlewareA(), priority=50)
stack.add(MyMiddlewareB(), priority=50)  # → MiddlewarePriorityCollisionFault
```

The warning names both participants, so manual priority misregistration is immediately visible rather than buried in a sort-order surprise on production.

---

## `middleware_ext/` Removed

`aquilia/middleware_ext/` held no implementations after the `builtin/` move — only re-exports to two import paths for one object. It has been removed.

**Import path migration:**

| Old path | New canonical path | Via lazy re-export |
|---|---|---|
| `aquilia.middleware_ext.SecurityHeadersMiddleware` | `aquilia.middleware.builtin.security.headers.SecurityHeadersMiddleware` | `aquilia.middleware.SecurityHeadersMiddleware` |
| `aquilia.middleware_ext.CORSMiddleware` | `aquilia.middleware.builtin.security.cors.CORSMiddleware` | `aquilia.middleware.CORSMiddleware` |
| `aquilia.middleware_ext.CSRFMiddleware` | `aquilia.middleware.builtin.security.csrf.CSRFMiddleware` | `aquilia.middleware.CSRFMiddleware` |
| `aquilia.middleware_ext.RateLimitMiddleware` | `aquilia.middleware.builtin.rate_limit.RateLimitMiddleware` | `aquilia.middleware.RateLimitMiddleware` |
| `aquilia.middleware_ext.rate_limit._TokenBucket` | `aquilia._ratelimit.TokenBucket` | Aliases in `middleware_ext/rate_limit.py` preserved |

The top-level `aquilia.middleware` barrel re-exports everything via lazy exports, so:

```python
# These all still work:
from aquilia import Middleware
from aquilia.middleware import Middleware, CORSMiddleware, Priority
```

The effect middleware install hints in `faults/domains.py` and workspace examples in `builtin/effects.py` docstrings have been updated to point at the new paths.

---

## `build_fast_handler()` Removed

`MiddlewareStack.build_fast_handler()` has been removed. The module docstring had advertised a "v3 scalability fast lane" that skipped `LoggingMiddleware` and `TimeoutMiddleware` for latency-sensitive routes, but no call sites existed in the framework, tests, benchmarks, or examples — `ASGIAdapter` only ever called `build_handler()`. Wiring it up requires per-route chain selection, which is a design change rather than a missing line.

Use `build_handler()` for all chain compilation.

---

## Rate Limit Algorithm Extraction

The token bucket, sliding-window counter, and bucket store moved to `aquilia/_ratelimit.py`, a leaf module with no framework imports. Both the HTTP and socket rate limiters use the shared module.

### New: `BucketStore.discard(key)`

```python
# Socket rate limiter releases bucket on disconnect
bucket_store.discard(client_key)
```

### Bug fix: Zero refill rate guard

`TokenBucket.consume()` now guards against `limit=0` (refill_rate=0.0). Previously raised `ZeroDivisionError`; now reports a finite retry-after.

---

## New Instrumentation Layer

`aquilia.middleware.instrumentation` provides composable instruments for the HTTP middleware stack:

```python
from aquilia.middleware.instrumentation import TracingInstrument, MetricsInstrument
from aquilia.middleware import MiddlewareStack

stack = MiddlewareStack(instruments=[TracingInstrument(), MetricsInstrument()])
```

- `TracingInstrument`: Records middleware execution duration via `time.monotonic()`.
- `MetricsInstrument`: Counts per-middleware invocations and errors.

---

## asyncio.TimeoutError Fix (Python 3.10)

On Python 3.10, `asyncio.TimeoutError` and the builtin `TimeoutError` are unrelated classes — `asyncio.wait_for` raises `asyncio.TimeoutError`, not the builtin. The `except TimeoutError` clause never fired on 3.10, producing 500 instead of 408. Both names are now caught. Redundant on 3.11+, load-bearing on 3.10.

---

## EncryptedMixin Key Stretching Fix

`EncryptedMixin.configure_encryption_key()` documents that any string or bytes value is accepted, stretched to 32 bytes via SHA-256 on the stdlib path. With `cryptography` installed, `Fernet(key)` rejects non-base64-encoded 32-byte values by raising `ValueError`. Only `ImportError` was caught, so the same call succeeded or crashed depending on whether an unrelated package was installed. `ValueError`/`TypeError` are now caught alongside `ImportError` and fall through to `_StdlibAESGCM`, which already stretches arbitrary key material.

---

## Cross-platform Worker ID Fix

WebSocket worker ID generation replaced `os.uname()` (Unix-only) with `platform.node()` (cross-platform). Worker IDs are used in Redis adapter pub/sub channel routing for horizontal scaling.
