# Framework Integration Fixes

**Phase 12 — Integration Audit**
**Aquilia v1.0.1**

---

## Fix INT-01: CSRF Middleware Priority Ordering

### Problem

In `server.py:797-800`, the CSRF middleware is registered with priority 10:

```python
# Must run AFTER session middleware (priority 15) so session is available,
# but BEFORE route handlers. Priority 10 places it between CSP and CORS.
```

The comment correctly states CSRF needs session data, but priority 10 runs
BEFORE priority 15 (session/auth middleware). Lower priority numbers execute
first in the middleware chain.

### Root Cause

The original developer confused "priority number" with "execution order".
In the `MiddlewareStack`, middlewares are sorted ascending by priority and
wrapped in reverse order — meaning priority 10 becomes the outermost layer
relative to priority 15. This means CSRF runs BEFORE session.

### Fix

Changed CSRF priority from 10 → 20 and updated the comment:

```python
# ── CSRF Protection (priority 20) ────────────────────────────────
# Must run AFTER session middleware (priority 15) so session is
# available for CSRF token storage/validation.
self.middleware_stack.add(mw, scope="global", priority=20, name="csrf")
```

### Impact

- CSRF middleware now correctly sees the session data
- Session-bound CSRF tokens work properly
- No middleware conflicts (20 is between session at 15 and i18n at 24)

---

## Fix INT-02: Double DI Container Shutdown

### Problem

The request-scoped DI container is shut down in TWO places:

1. `request_scope_mw` in `server.py:225-226`:
```python
finally:
    if ctx.container and hasattr(ctx.container, 'shutdown'):
        await ctx.container.shutdown()
```

2. `handle_http()` in `asgi.py:340-346`:
```python
finally:
    try:
        if di_container is not None and hasattr(di_container, 'shutdown'):
            await di_container.shutdown()
    except Exception:
        pass
```

### Root Cause

The ASGI adapter added a defensive cleanup during an earlier phase to ensure
container shutdown even if middleware fails. However, the `request_scope_mw`
(priority 5) is inside the `FaultMiddleware` (priority 2) which catches all
exceptions, so the middleware's finally block is always reached.

### Fix

Removed the container shutdown from the ASGI adapter's finally block and
added a comment documenting the delegation:

```python
finally:
    # DI container cleanup is handled by request_scope_mw (priority 5).
    # That middleware's finally block always runs because FaultMiddleware
    # (priority 2) wraps everything and catches exceptions.
    # Container.shutdown() is idempotent, but removing the redundant call
    # saves ~1µs per request.
```

### Impact

- Saves one async call + attribute check per request
- Clearer ownership: middleware owns DI lifecycle
- Container.shutdown() idempotency provides safety net if the fix is reverted

---

## Fix Summary

| Fix | File | Change | Risk |
|-----|------|--------|------|
| INT-01 | server.py | CSRF priority 10 → 20, comment updated | Low — only affects CSRF ordering |
| INT-02 | asgi.py | Remove redundant shutdown, add comment | Low — idempotent safety net exists |
