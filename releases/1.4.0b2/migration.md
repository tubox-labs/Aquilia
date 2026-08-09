# Migration Guide — 1.4.0b1 → 1.4.0b2

v1.4.0b2 contains several breaking changes, all in the middleware subsystem. The core breaking change is the removal of `middleware_ext/` and the restructure of the middleware package. The top-level import surface (`from aquilia.middleware import ...`) is preserved via lazy re-exports, so simple imports are unaffected.

---

## 1. `middleware_ext` Import Paths

**Breaking for**: code that imports directly from `aquilia.middleware_ext` or `aquilia.middleware_ext.security`.

### Impact

The `aquilia/middleware_ext/` package has been removed. All implementations have moved to `aquilia/middleware/builtin/`.

### Migration

```python
# BEFORE (v1.4.0b1 and earlier)
from aquilia.middleware_ext import RateLimitMiddleware, RateLimitRule
from aquilia.middleware_ext.security import CORSMiddleware, CSPMiddleware, CSRFMiddleware
from aquilia.middleware_ext.security import SecurityHeadersMiddleware, HSTSMiddleware
from aquilia.middleware_ext.security import HTTPSRedirectMiddleware, ProxyFixMiddleware

# AFTER — option 1: use top-level aquilia.middleware (recommended, lazy re-exports)
from aquilia.middleware import RateLimitMiddleware, CORSMiddleware

# AFTER — option 2: use canonical paths
from aquilia.middleware.builtin.rate_limit import RateLimitMiddleware, RateLimitRule
from aquilia.middleware.builtin.security.cors import CORSMiddleware
from aquilia.middleware.builtin.security.csp import CSPMiddleware
from aquilia.middleware.builtin.security.csrf import CSRFMiddleware
from aquilia.middleware.builtin.security.headers import SecurityHeadersMiddleware
from aquilia.middleware.builtin.security.hsts import HSTSMiddleware
from aquilia.middleware.builtin.security.https_redirect import HTTPSRedirectMiddleware
from aquilia.middleware.builtin.security.proxy_fix import ProxyFixMiddleware
```

### Workspace dotted-path strings

If your `workspace.py` or manifest uses dotted-path strings for middleware registration, update them:

```python
# BEFORE
.use("aquilia.middleware_ext.SecurityHeadersMiddleware", priority=7)
.use("aquilia.middleware_ext.security.CORSMiddleware", priority=11)

# AFTER
.use("aquilia.middleware.builtin.security.headers.SecurityHeadersMiddleware", priority=7)
.use("aquilia.middleware.builtin.security.cors.CORSMiddleware", priority=11)
```

### EffectMiddleware install hints

If your code produced EffectMiddleware install hints (from `FaultDomain` error messages), those paths have also been updated. The hints now reference `aquilia.middleware.builtin.effects.EffectMiddleware`.

---

## 2. `build_fast_handler()` Removed

**Breaking for**: any code calling `MiddlewareStack.build_fast_handler()`.

### Migration

```python
# BEFORE
handler = stack.build_fast_handler(final_handler)

# AFTER
handler = stack.build_handler(final_handler)
```

`build_fast_handler()` was never called anywhere in the framework, tests, benchmarks, or examples. If you were calling it yourself, `build_handler()` produces the same output since the "fast lane" was never wired up.

---

## 3. Priority Collision Behavior Change

**Breaking for**: deployments where two middlewares share the same scope and priority.

### Previous behavior
Silently resolved by registration order.

### New behavior
Warning at boot (naming both participants). `strict_priorities=True` raises `MiddlewarePriorityCollisionFault`.

### Migration
Assign distinct priorities to all middleware. Use `strict_priorities=True` in staging to catch problems before production:

```python
from aquilia.middleware import MiddlewareStack

stack = MiddlewareStack(strict_priorities=True)  # fail fast
```

---

## 4. Inspector Priority Change (Internal)

The Inspector middleware priorities changed:
- `INSPECTOR`: 11 → 13
- `INSPECTOR_TOOLBAR`: 12 → 14

This prevents collisions with `CORS` (11) and `RATE_LIMIT_ANON` (12). No user action required unless you were explicitly relying on inspector running between CORS and rate limiting.

---

## 5. Rate Limit Ordering Change (Behavioral)

**Intentional behavioral change**: identity-based rate limit rules now run at priority 16, after auth (priority 15).

If you had `user_key_extractor` rules, they were silently not enforced before this release. After upgrading, they will be enforced. Verify your limits are appropriate before deploying to production.

```python
# IP-only rule — still at priority 12 (before auth)
RateLimitRule(limit=100, window=60.0, key_func=ip_key_extractor)

# User rule — now at priority 16 (after auth at 15)
RateLimitRule(limit=1000, window=3600.0, key_func=user_key_extractor)

# Custom extractor — set requires_identity explicitly
RateLimitRule(limit=50, window=60.0, key_func=my_extractor, requires_identity=True)
```

---

## 6. `SocketGuard.check_message` Deprecated

`SocketGuard.check_message` is deprecated and was never called by the runtime. If you relied on per-message guards, you have been running with no enforcement. Migrate to socket middleware:

```python
# BEFORE (never executed)
class MyGuard(SocketGuard):
    async def check_message(self, message, ctx):
        if not authorized(ctx):
            return False
        return True

# AFTER — use SocketMiddleware
from aquilia.sockets.middleware import SocketMiddleware

class AuthCheckMiddleware(SocketMiddleware):
    async def on_message(self, envelope, ctx, next_handler):
        if not ctx.state.get("identity"):
            raise PermissionError("Authentication required")
        return await next_handler(envelope, ctx)
```

Register in `workspace.py`:
```python
workspace = (
    Workspace("myapp")
    .socket_middleware(
        SocketMiddlewareChain.chain()
        .use("aquilia.sockets.middleware.builtin.SocketFaultMiddleware", priority=2)
        .use("modules.myapp.middleware.AuthCheckMiddleware", priority=11)
    )
)
```

`SocketGuard.check_handshake` is **not** deprecated and remains the correct way to gate connections before they are established.

---

## 7. Removed Socket Names

These names were removed from `aquilia.sockets.middleware` and now raise `ImportError` with guidance:

| Removed name | Replacement |
|---|---|
| `MiddlewareChain` | `SocketMiddlewareStack` (programmatic) or `SocketMiddlewareChain` (workspace config) |
| `LoggingMiddleware` | `SocketLoggingMiddleware` |
| `MetricsMiddleware` | `SocketMetricsMiddleware` |

`RateLimitMiddleware` is preserved as an alias for `SocketRateLimitMiddleware`.

---

## 8. pytest Now Optional

`pytest` is no longer a required dependency for the CLI or testing imports. If your code imports from `aquilia.testing` in production contexts where `pytest` is not installed, it will no longer fail at import time.

---

## Upgrade Checklist

- [ ] Update `aquilia` to `1.4.0b2` in your `requirements.txt` / `pyproject.toml`.
- [ ] Search for `aquilia.middleware_ext` imports and update to `aquilia.middleware` or the canonical paths.
- [ ] Search for `.use("aquilia.middleware_ext.*")` in workspace.py / manifest files and update.
- [ ] Search for `build_fast_handler` calls and replace with `build_handler`.
- [ ] Check rate limit configurations — per-user limits now actually enforced; review values.
- [ ] If using `SocketGuard.check_message`, migrate to `SocketMiddleware.on_message`.
- [ ] Add `SocketMiddlewareChain` to workspace.py for any WebSocket endpoints that need security.
- [ ] Run the test suite, watching for priority collision warnings at boot.

## Compatibility Matrix

| Component | Minimum | Recommended |
|---|---|---|
| **Python** | 3.10 | 3.12+ |
| **OS** | Linux, macOS 11+, Windows 10+ | Ubuntu 22.04 / macOS 14 |
| **SQLite** | 3.35.0 | 3.42.0+ |
