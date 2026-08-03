# Phase 2 — Evidence-Based Performance Audit

**Status:** complete
**Method:** instrumented micro-benchmarks (`benchmarks/engine/profile_baseline.py`, `evidence.py`, `evidence2.py`) + end-to-end attribution (`e2e_attribution.py`) + cProfile on 3,000 real requests through the real `ASGIAdapter`. All numbers are `min(7 samples)` to suppress noise. Machine: Apple M-series, Python 3.11.15, single event loop.

---

## 1. Baseline numbers

| Metric | Value |
|---|---|
| Full request, static route, no params | **16.49 µs** (60,644 req/s) |
| Full request, dynamic route, 1 int param | **20.21 µs** (49,484 req/s) |
| Theoretical floor (raw dict lookups + await) | ~0.5 µs |

---

## 2. Per-request cost budget

Measured inside a single event loop run to eliminate `run_until_complete` overhead (~25 µs/call).

| Component | Cost | % of 16.49 µs | Source |
|---|---|---|---|
| `register_instance(Request)` + request scope | **3.68 µs** | 22.3% | `asgi.py:475`, `di/core.py:400` |
| `get_type_hints()` uncached per request | **2.64 µs** | 16.0% | `engine.py:1494` |
| `RequestCtx.__setattr__` overhead (24 calls) | **1.26 µs** | 7.6% | `controller/base.py:175` |
| `Response.json()` + `_prepare_headers()` | **1.14 µs** | 6.9% | `response.py` |
| `router.match_sync()` static | **0.79 µs** | 4.8% | `router.py:230` |
| `os.urandom(16).hex()` in ctx pool | **0.72 µs** | 4.3% | `controller/base.py:269` |
| **Accounted** | **10.23 µs** | **62.0%** | |
| Async machinery, middleware, misc | 6.26 µs | 38.0% | |

---

## 3. Finding B1 — `register_instance` is the largest single cost (3.68 µs, 22%)

**Root cause:** `asgi.py:475` calls `await container.register_instance(Request, req, scope="request")` on every request. This triggers:

1. `ValueProvider(...)` allocation — 608 ns
2. COW dict copy of the entire `_providers` dict — 118 ns at 50 providers, **7.2 µs at 1,000 providers**
3. `DIEventType.REGISTRATION` diagnostic emit
4. `_notify_provider_registered` plugin check
5. `_unwrap_token` + `_token_to_key` on the Request type

The COW copy scales linearly with provider count. At 1,000 providers the operation costs 7.2 µs — 44% of a request.

**What it should cost:** a plain `dict.__setitem__` is 41 ns. The operation is logically "store this request object so DI can inject it" — a single dict write.

**Fix:** bypass `register_instance` for the per-request `Request` injection. Write directly to `child._cache[request_key]` after `create_request_scope()`. The cache is already the fast path for all subsequent lookups; the provider registration is only needed if something calls `container.register()` on the same key later, which never happens for `Request`.

```python
# asgi.py — replace the register_instance call with a direct cache write
child = app_container.create_request_scope()
child._cache[_REQUEST_CACHE_KEY] = request   # ~41 ns vs 3,680 ns
```

where `_REQUEST_CACHE_KEY = f"{Request.__module__}.{Request.__qualname__}"` is a module-level constant.

**Ceiling:** eliminates 3.68 µs → **22% end-to-end gain** at 50 providers, larger at higher provider counts.

---

## 4. Finding B2 — `get_type_hints()` called uncached on every request (2.64 µs, 16%)

**Root cause:** `engine.py:1494` calls `get_type_hints(handler_method)` inside `_bind_special_parameters`, which runs on every request. `_get_cached_signature` (engine.py:1474) caches `inspect.signature` but not type hints.

`get_type_hints` costs 2,640–7,430 ns depending on annotation count. It re-evaluates string annotations against `__globals__` every call.

**Fix:** extend `_signature_cache` to also store type hints, keyed by the same callable id.

```python
# engine.py — _bind_special_parameters
sig = self._get_cached_signature(handler_method)
type_hints = self._signature_cache.get(id(handler_method) + 1)  # or a separate dict
if type_hints is None:
    try:
        type_hints = get_type_hints(handler_method)
    except Exception:
        type_hints = {}
    self._signature_cache[id(handler_method) + 1] = type_hints
```

Simpler: add a `_type_hints_cache: dict[int, dict]` class variable alongside `_signature_cache`.

**Ceiling:** 2.64 µs → ~14 ns (dict lookup) = **16% end-to-end gain**.

---

## 5. Finding B3 — `RequestCtx.__setattr__` is 3.1× slower than native slots (1.26 µs, 7.6%)

**Root cause:** `controller/base.py:175` overrides `__setattr__` with a `try/except AttributeError` to route unknown attributes to `_extra`. Every pool `acquire()` sets 8 fields, `release()` sets 8 more = 24 `__setattr__` calls per request. Each costs 78 ns vs 25 ns native = 53 ns overhead × 24 = 1.26 µs.

The pool was designed to eliminate allocation overhead, but the `__setattr__` override makes it **3.3× slower than just constructing a new `RequestCtx`** (1,990 ns vs 598 ns).

**Fix option A (recommended):** remove the pool entirely. `RequestCtx.__init__` costs 598 ns; the pool costs 1,990 ns. The pool is net-negative.

**Fix option B:** keep the pool, remove the `__setattr__` override. Use `object.__setattr__` directly in `acquire()` and `release()` for the known slots. Move the `_extra` escape hatch to `__getattr__` only (already present at base.py:167) — `__getattr__` is only called for *missing* attributes, so it has zero cost on the common path.

```python
# controller/base.py — acquire(): replace setattr calls with object.__setattr__
_sa = object.__setattr__
_sa(ctx, "request", request)
_sa(ctx, "identity", identity)
# ... etc
```

**Ceiling (option A):** 1.26 µs overhead + 0.72 µs urandom = **1.98 µs → 12% end-to-end gain**.

---

## 6. Finding B4 — `os.urandom(16).hex()` in every pool acquire (0.72 µs, 4.3%)

**Root cause:** `controller/base.py:269-272` generates a fresh random request ID on every `acquire()`, even when the caller already has one from `request.state["request_id"]`. The `import os` inside the function adds another 33 ns.

**Fix:** move `import os` to module level (already imported elsewhere in the file). Pass `request_id` from the ASGI layer where it is already generated by `RequestIdMiddleware`, and only generate a fallback if truly absent.

```python
# controller/base.py — module level
import os as _os

# acquire(): replace the urandom block
if request_id is None:
    request_id = _os.urandom(16).hex()
```

This alone saves 33 ns. The full 716 ns is only avoidable if the caller always provides a request_id (which `asgi.py:488` does via `request.state.get("request_id")`).

**Ceiling:** 0.72 µs → **4.3% end-to-end gain** if caller always provides request_id.

---

## 7. Finding B5 — `_version_matches` is 64% of a static route match (492 ns of 782 ns)

**Root cause:** `router.py:361` is called on every candidate during match. It runs two `from aquilia.versioning.core import VERSION_MISSING, VERSION_NEUTRAL` statements (E1: 421 ns for two imports) plus version comparison logic. For the common case (no versioning), this is pure overhead.

**Fix:** hoist the imports to module level in `router.py`. The function-local imports exist to break an import cycle (confirmed by the SCC analysis), but `aquilia.versioning.core` is a leaf module — it does not import back into `aquilia.controller`. Moving these to module level is safe.

```python
# router.py — top of file
from aquilia.versioning.core import VERSION_MISSING, VERSION_NEUTRAL
```

**Ceiling:** 421 ns saved per match → static match drops from 782 ns to ~360 ns = **2.6% end-to-end gain** (small because routing is only 4.8% of a request, but this is a one-line fix).

---

## 8. Finding B6 — `_unwrap_token` runs on every DI resolve (1,167 ns)

**Root cause:** `di/core.py:1246` runs on every `resolve_async` call, including the cache-hit path. It performs:
- 3× `hasattr(_inject_*)` on a plain type: 225 ns
- `get_origin(type)`: 95 ns
- `import + _normalize_optional_token`: 572 ns

For the 99% case (a plain Python class, no `Annotated`, no `Inject`), all of this is wasted.

**Fix:** fast-exit for the common case before any `hasattr` or `get_origin`:

```python
def _unwrap_token(self, token, tag=None, optional=False):
    # Fast path: plain type or string — the 99% case
    if isinstance(token, (type, str)):
        return token, tag, optional
    # ... existing logic for Annotated/Inject/Optional
```

`isinstance(token, (type, str))` costs ~30 ns. This eliminates 1,137 ns for plain types.

**Ceiling:** cached resolve drops from 1,332 ns to ~195 ns (dict lookup + isinstance). **Not directly visible in end-to-end** because DI cache hits are only ~8% of a request, but this matters for DI-heavy handlers.

---

## 9. Finding B7 — `_to_response` runs a `try/import SSEResponse` on every response (uncached)

**Root cause:** `engine.py:1793`:
```python
try:
    from aquilia.sse import SSEResponse
    if isinstance(result, SSEResponse): ...
except ImportError:
    pass
```

This runs on every non-`Response` return value. The import is cached by Python's import machinery after the first call, but the `try/except` frame and `isinstance` check still run.

**Fix:** hoist to module level with a `None` fallback:

```python
# engine.py — module level
try:
    from aquilia.sse import SSEResponse as _SSEResponse
except ImportError:
    _SSEResponse = None
```

Then in `_to_response`: `if _SSEResponse is not None and isinstance(result, _SSEResponse)`.

---

## 10. Routing scales correctly — no algorithmic work needed

E5 confirms the trie is O(k) in path depth, not O(n) in route count:

| Routes | Static | Dynamic | Miss |
|---|---|---|---|
| 15 | 832 ns | 1,228 ns | 284 ns |
| 3,000 | 858 ns | 1,300 ns | 299 ns |

200× the routes costs +3% lookup. **The routing algorithm is not a problem.** The 782 ns static cost is entirely constant-factor Python overhead (import in `_version_matches`, function call chain), not complexity.

---

## 11. The native engine ROI question

**If routing + DI-scope became free (0 ns), the request drops from 16.49 µs to 15.59 µs — a 5.5% best-case gain.**

A native router/DI engine written in C++ or Rust would not materially improve end-to-end throughput because:
1. Routing is 4.8% of a request.
2. DI scope creation is 0.7% of a request.
3. The dominant costs (B1–B4) are in Python glue code that a native engine cannot eliminate.

**The correct target for a native engine is B1 (register_instance) and B3 (RequestCtx pool).** Both are Python-level allocation/dispatch overhead that a native request-context object could eliminate entirely. A native `RequestContext` that holds the request, identity, session, container reference, and state dict — and is reset in C++ — would save ~5 µs/request (30%) without touching the router or DI graph.

**Pure Python fixes (B1–B6) are available today and collectively save ~8–10 µs/request (50–60%) with no native code.** They should be implemented first to establish a new baseline before any native work begins.

---

## 12. Priority ranking

| Priority | Finding | Fix | Gain | Effort |
|---|---|---|---|---|
| 1 | B1 — `register_instance` per request | Direct `_cache` write | 22% | 5 lines |
| 2 | B2 — `get_type_hints` uncached | `_type_hints_cache` class var | 16% | 8 lines |
| 3 | B3 — `RequestCtx.__setattr__` + pool | Remove pool or use `object.__setattr__` | 12% | 20 lines |
| 4 | B4 — `os.urandom` in pool | Module-level import + caller provides id | 4% | 2 lines |
| 5 | B5 — imports in `_version_matches` | Hoist to module level | 2.6% | 2 lines |
| 6 | B6 — `_unwrap_token` on cache hits | Fast-exit for plain type/str | DI-heavy only | 3 lines |
| 7 | B7 — SSEResponse import in `_to_response` | Module-level with None fallback | small | 3 lines |

**Combined ceiling (B1+B2+B3+B4):** ~10 µs saved → request drops from 16.49 µs to ~6.5 µs = **60% throughput improvement, pure Python, no native code**.

---

## 13. Benchmark artifacts

| File | Purpose |
|---|---|
| `benchmarks/engine/profile_baseline.py` | Routing, DI, request, metadata baselines |
| `benchmarks/engine/evidence.py` | Root-cause isolation (E1–E6) |
| `benchmarks/engine/evidence2.py` | Dominant-cost isolation (F1–F5) |
| `benchmarks/engine/e2e_attribution.py` | End-to-end attribution + cProfile |
| `benchmarks/engine/import_graph.py` | Static AST import-graph analysis |
| `benchmarks/engine/baseline_100.json` | Baseline numbers (JSON) |
| `benchmarks/engine/evidence.json` | Evidence numbers (JSON) |
