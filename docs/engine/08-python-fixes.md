# Phase 8 — Python-Side Fixes (Pre-Native Baseline)

**Status:** design
**Rationale:** Phase 2 identified seven pure-Python fixes worth ~60% end-to-end gain. These must land before the native engine so the native work targets the *post-fix* hot spots, not the ones that Python can already eliminate.

---

## 1. Fix P1 — Eliminate `register_instance` per request (B1, 3.68 µs → ~0.04 µs)

**File:** `aquilia/asgi.py:475`

**Root cause:** `register_instance` allocates a `ValueProvider`, forks the COW provider dict, emits a diagnostic event, and checks plugins — then the next line writes `_cache` directly anyway.

**Fix:** write directly to `_cache` using a module-level constant key.

```python
# aquilia/asgi.py — module level
from aquilia.request import Request as _Request
_REQUEST_CACHE_KEY: str = f"{_Request.__module__}.{_Request.__qualname__}"

# inside handle_http, replacing lines 475-476:
child = app_container.create_request_scope()
child._cache[_REQUEST_CACHE_KEY] = request   # ~41 ns
```

**Correctness:** `_cache` is the fast path for all subsequent `resolve_async` calls. The provider registration was only needed to make `Request` resolvable via `container.resolve(Request)` — but `_cache` is checked *before* the provider lookup (`di/core.py:530-532`), so a direct cache write is semantically equivalent and takes priority.

**Risk:** any code that calls `container.is_registered(Request)` will return `False` (it checks `_providers`, not `_cache`). Audit: `grep -r "is_registered.*Request" aquilia/` — zero hits. Safe.

---

## 2. Fix P2 — Cache `get_type_hints` in `_bind_special_parameters` (B2, 2.64 µs → ~14 ns)

**File:** `aquilia/controller/engine.py:1494`

**Root cause:** `get_type_hints(handler_method)` is called on every request. `_get_cached_signature` caches `inspect.signature` but not type hints.

**Fix:** add a `_type_hints_cache` class variable alongside `_signature_cache`.

```python
# engine.py — class ControllerEngine:
_type_hints_cache: dict[int, dict] = {}   # id(callable) → hints dict

# _bind_special_parameters:
sig = self._get_cached_signature(handler_method)
hid = id(handler_method)
type_hints = ControllerEngine._type_hints_cache.get(hid)
if type_hints is None:
    try:
        type_hints = get_type_hints(handler_method)
    except Exception:
        type_hints = {}
    ControllerEngine._type_hints_cache[hid] = type_hints
```

**Risk:** same `id()` reuse hazard as the existing `_signature_cache` (Phase 1 §7). Acceptable for the same reason: handlers live for process lifetime. Hot-reload must clear both caches — add `_type_hints_cache.clear()` alongside the existing `_signature_cache.clear()` call in the reload path.

---

## 3. Fix P3 — Remove the `RequestCtx` object pool (B3, 1.26 µs overhead → 0)

**File:** `aquilia/controller/base.py:234-311`

**Root cause:** the pool's `__setattr__` override makes acquire+release (1,990 ns) 3.3× slower than direct construction (598 ns). The pool is net-negative.

**Fix:** delete `_RequestCtxPool` and `_ctx_pool`. Replace all `_ctx_pool.acquire(...)` calls with `RequestCtx(...)` and all `_ctx_pool.release(ctx)` calls with nothing.

```python
# aquilia/asgi.py — replace pool acquire:
ctx = RequestCtx(
    request=request,
    identity=request.state.get("identity"),
    session=request.state.get("session"),
    auth=request.state.get("auth"),
    container=child,
    state=request.state,
    request_id=request.state.get("request_id"),
)
# replace pool release: delete the line entirely
```

**Also:** remove the `__setattr__` override from `RequestCtx` (base.py:175-185). The `_extra` escape hatch is preserved via `__getattr__` (already present at base.py:167), which only fires for *missing* attributes and has zero cost on the common path. Dynamic attribute *writes* via `ctx.some_dynamic_key = value` will now raise `AttributeError` — replace with `ctx._extra = {}; ctx._extra["key"] = value` or `ctx.state["key"] = value` (the documented pattern for middleware).

**Risk:** any code that writes a non-slot attribute directly to `ctx` will break. Audit: `grep -rn "ctx\." aquilia/ | grep -v "ctx\.\(request\|identity\|session\|auth\|container\|state\|request_id\|_extra\|path\|method\|headers\|get_effect\|has_effect\)"` — review hits before merging.

---

## 4. Fix P4 — Eliminate `os.urandom` from the hot path (B4, 0.72 µs → 0)

**File:** `aquilia/controller/base.py:269-272`

**Root cause:** `acquire()` generates a random request ID even when the caller already has one from `RequestIdMiddleware`. With P3 applied (pool removed), this fix is automatic — `RequestCtx.__init__` does not generate a random ID; the caller passes one.

**Residual fix (if pool is kept):** move `import os` to module level and only generate when `request_id is None`.

```python
# controller/base.py — module level (already imported elsewhere)
import os as _os

# acquire():
if request_id is None:
    request_id = _os.urandom(16).hex()
```

With P3 applied, this fix is a no-op — included for completeness.

---

## 5. Fix P5 — Hoist imports in `_version_matches` (B5, 421 ns → 0)

**File:** `aquilia/controller/router.py:382-386`

**Root cause:** two `from aquilia.versioning.core import ...` statements execute per `_version_matches` call. Phase 1 SCC analysis confirmed `aquilia.versioning.core` is a leaf — it does not import back into `aquilia.controller`. The function-local placement was a cycle-break that is no longer needed.

**Fix:**

```python
# router.py — top of file, with existing imports
from aquilia.versioning.core import VERSION_MISSING, VERSION_NEUTRAL
```

Remove the two `from aquilia.versioning.core import ...` lines inside `_version_matches`.

**Verification:** `python -c "import aquilia.controller.router"` must succeed without `ImportError`. Run `benchmarks/engine/import_graph.py` and confirm no new SCC members.

---

## 6. Fix P6 — Fast-exit `_unwrap_token` for plain types (B6, 1.17 µs → ~30 ns)

**File:** `aquilia/di/core.py:1246`

**Root cause:** `_unwrap_token` runs on every `resolve_async` call, including cache hits. For a plain `type` or `str` (the 99% case), all of the `hasattr` + `get_origin` + `_normalize_optional_token` work is wasted.

**Fix:** add a two-line fast exit at the top of `_unwrap_token`:

```python
def _unwrap_token(self, token, tag=None, optional=False):
    # Fast path: plain type or string — the 99% case, ~30 ns
    if type(token) is type or isinstance(token, str):
        return token, tag, optional
    # ... existing logic unchanged
```

`type(token) is type` is faster than `isinstance(token, type)` because it avoids the MRO walk — it returns `True` for concrete classes and `False` for `Annotated`, `Optional`, `Inject`, etc.

**Risk:** `type(token) is type` returns `False` for metaclass instances (e.g. `ABCMeta` subclasses). Replace with `isinstance(token, type)` if any registered service uses a metaclass. Audit: `grep -rn "__metaclass__\|ABCMeta\|metaclass=" aquilia/` — review hits.

---

## 7. Fix P7 — Hoist `SSEResponse` import in `_to_response` (B7, small)

**File:** `aquilia/controller/engine.py:1793`

**Root cause:** `try: from aquilia.sse import SSEResponse` runs on every non-`Response` return value.

**Fix:**

```python
# engine.py — module level
try:
    from aquilia.sse import SSEResponse as _SSEResponse
except ImportError:
    _SSEResponse = None

# _to_response:
if _SSEResponse is not None and isinstance(result, _SSEResponse):
    return Response.sse(result._resolve_source(), status=result._status)
```

---

## 8. Rollout order

| Step | Fix | Gate |
|---|---|---|
| 1 | P5 (import hoist) | `import aquilia.controller.router` succeeds; import_graph.py shows no new SCC |
| 2 | P7 (SSE import) | existing tests pass |
| 3 | P6 (`_unwrap_token` fast exit) | all DI tests pass; `di_resolve_cached_ns` ≤ 200 ns |
| 4 | P2 (`get_type_hints` cache) | all controller tests pass; `get_type_hints` benchmark ≤ 20 ns |
| 5 | P4 (`os.urandom` module-level) | no behaviour change |
| 6 | P1 (`register_instance` → direct cache) | all integration tests pass; `di_per_request_register_ns` ≤ 100 ns |
| 7 | P3 (remove pool + `__setattr__`) | full suite passes; `ctx_pool_acquire_release_ns` replaced by `ctx_direct_construct_ns` ≤ 650 ns |

Each step is a separate commit so bisection is clean. Steps 1–5 are safe to batch; steps 6 and 7 each touch the request hot path and warrant individual review.

---

## 9. Expected post-fix baseline

| Metric | Before | After | Change |
|---|---|---|---|
| Full request, static | 16.49 µs | ~6.5 µs | −60% |
| `register_instance` | 3.68 µs | ~0.04 µs | −99% |
| `get_type_hints` | 2.64 µs | ~0.01 µs | −99% |
| `RequestCtx` acquire | 1.93 µs | ~0.60 µs | −69% |
| Static route match | 0.79 µs | ~0.36 µs | −54% |
| DI cached resolve | 1.33 µs | ~0.20 µs | −85% |

After these fixes, the new hot spots will be: async machinery overhead (~3–4 µs), response serialisation (~1.1 µs), and the remaining controller engine call chain. The native engine then targets those.

---

## 10. Re-benchmark after fixes

Run `benchmarks/engine/e2e_attribution.py` and `benchmarks/engine/profile_baseline.py` after each step and commit the updated `baseline_100.json`. The Phase 9 implementation spec is written against the post-fix numbers, not the pre-fix ones.
