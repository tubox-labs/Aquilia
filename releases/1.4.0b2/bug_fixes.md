# Bug Fixes — v1.4.0b2

Aquilia v1.4.0b2 resolves six critical bugs across middleware, WebSocket routing, and the ORM encryption field. All are covered by regression tests.

---

## 1. Rate Limiting Returned 500 Instead of 429

**Previous behavior:**
Every request that tripped a rate limit raised `NameError: name 'Response' is not defined` instead of returning `429 Too Many Requests`. This propagated as an unhandled exception producing a 500 Internal Server Error. Only the rejection path was broken — under-limit requests were unaffected, which is why the issue was not caught earlier.

**Root cause:**
`Response` was imported in `middleware_ext/rate_limit.py` under `TYPE_CHECKING` only:
```python
if TYPE_CHECKING:
    from aquilia.response import Response
```
The `_rate_limited_response()` function constructed a `Response` at runtime, but the name was absent from the module namespace at call time.

**Fix:**
`Response` is now imported at runtime. `aquilia.response` does not import `middleware_ext`, so no cycle is introduced.

**User impact:**
Rate limiting now works correctly. Every deployment with `RateLimitMiddleware` configured was silently not rate-limiting anyone. After upgrading, rate limits will actually be enforced. Review limit values before upgrading in production.

---

## 2. Per-User Rate Limiting Was a Silent No-Op

**Previous behavior:**
Configurations using `user_key_extractor` (per-user rate limits) were not enforced. Every request from every user passed through regardless of limit configuration.

**Root cause:**
`RateLimitMiddleware` registered at priority 12 and `AquilAuthMiddleware` at priority 15. Since ascending priority means outer/earlier, the rate limiter always ran before auth. `user_key_extractor` reads `request.state["identity"]`, which auth had not set yet, so it returned `None`. Rules with a `None` key were skipped via `continue` — silently, with no log, no error, no metric.

**Fix:**
- `RateLimitRule` gains a `requires_identity` field, auto-detected for `user_key_extractor` and overridable for custom extractors.
- Identity-dependent rules register at `_RATE_LIMIT_IDENTITY_PRIORITY` (16), after `_AUTH_PRIORITY` (15). IP-only rules stay at 12.
- Auth and session middleware now read their priority from `_AUTH_PRIORITY` so the two values cannot drift apart again.
- A rule that requires identity but finds none now warns once per server start instead of skipping silently.

**User impact:**
Per-user rate limits now work. If you relied on per-user limits for security, they were not enforced before this fix. Upgrade and verify limits in production.

```python
# This now works correctly — enforced AFTER auth at priority 16
RateLimitRule(
    limit=100,
    window=60.0,
    key_func=user_key_extractor,  # requires_identity auto-detected
)

# This still runs at priority 12 (before auth) — IP-only rules unaffected
RateLimitRule(
    limit=200,
    window=60.0,
    key_func=ip_key_extractor,
)
```

---

## 3. Middleware Circular Import Crash

**Previous behavior:**
Any isolated script or unit test importing `Middleware` first crashed:
```
ImportError: cannot import name 'Middleware' from partially initialized module 'aquilia.middleware'
```

**Root cause:**
The import cycle was:
```
aquilia/middleware.py    → from aquilia.faults import Fault, FaultDomain
aquilia/faults/__init__ → from aquilia.faults.engine import ...
aquilia/faults/engine.py → from aquilia.middleware import Middleware
```
Real apps avoided this by accident (normal bootstrap imports `AquiliaServer`, which pulls in `aquilia.faults` first). Isolated scripts and unit tests importing `Middleware` first crashed.

**Fix:**
The `Middleware` base class moved to `aquilia/middleware/core/base.py`, a fault-free leaf module with no `aquilia.faults` imports. `aquilia.faults.engine` now imports from there. `aquilia.middleware` uses lazy exports so its module body never eagerly pulls in the faults subsystem.

**User impact:**
`from aquilia import Middleware` and `from aquilia.middleware import Middleware` now work unconditionally, regardless of import order.

---

## 4. Duplicate Middleware Priorities Silently Reordered

**Previous behavior:**
Two middlewares registered at the same scope and priority resolved by insertion order — a Python stable-sort detail, not a contract. Collisions were accepted silently. Reordering registration calls could reorder security middleware with nothing to catch it.

**Root cause:**
`MiddlewareStack.add()` had no collision check. The INSPECTOR middleware (priority 11) collided with CORS (priority 11), and INSPECTOR_TOOLBAR (priority 12) collided with RATE_LIMIT_ANON (priority 12). Both collisions were resolved by registration order — correct coincidentally.

**Fix:**
`MiddlewareStack.add()` now detects a collision (same scope + same priority) and:
- Warns by default, naming both participants.
- Raises `MiddlewarePriorityCollisionFault` if `strict_priorities=True`.

Inspector priorities moved: 11 → 13, 12 → 14.

**User impact:**
If your workspace registers two middlewares at the same scope and priority, you will see a warning at boot. Resolve by assigning distinct priorities. Use `strict_priorities=True` to make collisions fatal.

---

## 5. WebSocket Parameterized Routes Never Matched

**Previous behavior:**
`@Socket("/chat/:room")` only ever matched the literal path `/chat/:room`. Path parameters were never extracted. Every connection with a parameterized path "matched" but produced an empty `path_params` dict. The runtime also emitted `RuntimeWarning: coroutine was never awaited` for every connection attempt.

**Root cause:**
`SocketRouter.match()` called `PatternMatcher.match(compiled, path)` without `await`. `PatternMatcher.match` is `async`. The returned coroutine object has no `.matched` attribute, producing `AttributeError` which was swallowed by a bare `except:` clause. Control fell through to an exact-string comparison against the literal pattern string `"/chat/:room"`, which matched only the literal path.

**Fix:**
Compiled patterns are now registered on the matcher with a reverse map back to the namespace. `match()` is awaited properly. The swallowed exception is now logged at `DEBUG` rather than discarded. The bare string fallback is reachable again when the patterns subsystem is unavailable.

**User impact:**
Path parameters in WebSocket routes now work correctly:
```python
@Socket("/chat/:room")
async def on_chat_message(self, envelope, ctx):
    room = ctx.path_params["room"]  # now populated correctly
    ...
```

---

## 6. WebSocket Policy Rejections Used Wrong Close Code

**Previous behavior:**
`WS_AUTH_REQUIRED`, `WS_FORBIDDEN`, and `WS_ORIGIN_NOT_ALLOWED` closed connections with WebSocket code **1003 "unsupported data"**. This tells the client to stop sending that kind of message — incorrect since the frame was fine and the issue was authorization, not message format.

**Fix:**
All three now close with WebSocket code **1008 "policy violation"**, which is the correct code for access control rejections.

**User impact:**
WebSocket clients that interpret close codes can now distinguish between format errors (1003) and policy violations (1008) and react accordingly (e.g., redirect to login on 1008).

---

## 7. `EncryptedMixin` Crashed When `cryptography` Was Installed

**Previous behavior:**
```python
EncryptedMixin.configure_encryption_key("test-key-material")
# ValueError: Fernet key must be 32 url-safe base64-encoded bytes.
```
This crashed only when the `cryptography` package was installed. Without it, arbitrary string keys worked fine via the stdlib AES-GCM path.

**Root cause:**
`Fernet(key)` raises `ValueError` for non-base64-encoded keys. Only `ImportError` was caught. Whether `configure_encryption_key("any-string")` succeeded or crashed depended on whether an unrelated package happened to be installed.

**Fix:**
`ValueError`/`TypeError` are now caught alongside `ImportError` and fall through to `_StdlibAESGCM`, which already stretches arbitrary key material via SHA-256. A genuine Fernet key (32 bytes, URL-safe base64) still takes the Fernet path, so no existing ciphertext changes.

**User impact:**
`configure_encryption_key()` now behaves identically regardless of whether `cryptography` is installed.

---

## 8. asyncio.TimeoutError Not Caught on Python 3.10

**Previous behavior:**
On Python 3.10, requests exceeding the timeout limit returned 500 instead of 408 Request Timeout.

**Root cause:**
On Python 3.10, `asyncio.TimeoutError` is not a subclass of the builtin `TimeoutError` (they were unified in 3.11). `except TimeoutError` never fired on 3.10; the asyncio error escaped to `ExceptionMiddleware` and surfaced as 500.

**Fix:**
Both `asyncio.TimeoutError` and `TimeoutError` are now caught. Redundant on 3.11+, load-bearing on 3.10.

**User impact:**
Request timeouts produce 408 responses on Python 3.10.
