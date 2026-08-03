# Phase 4 — Native DI Engine Specification

**Status:** design
**Targets:** Phase 2 findings B1 (`register_instance`, 3.68 µs) and B6 (`_unwrap_token`, 1.17 µs)

---

## 1. Scope decision

Phase 2 measured DI request-scope creation at **0.11 µs (0.7% of a request)** — already cheap, because `create_request_scope` is copy-on-write (`di/core.py:740`). A native replacement for scope creation would gain nothing.

The measurable DI costs are elsewhere:

| Cost | Measured | Cause |
|---|---|---|
| `register_instance(Request)` per request | 3.68 µs | ValueProvider alloc + COW dict copy + diagnostics emit + plugin check |
| COW copy at 1,000 providers | 7.2 µs | `dict.copy()` scales linearly |
| `_unwrap_token` on every resolve | 1.17 µs | 3× `hasattr` + `get_origin` + `_normalize_optional_token` |
| Cached resolve total | 1.33 µs | of which ~1.17 µs is `_unwrap_token` |

**The native DI engine therefore targets the resolve path and per-request instance registration — not scope creation, and not graph compilation** (which runs once at startup and is not on the hot path).

---

## 2. Architecture

```
┌─────────────────────────────────────────────┐
│ Python: Container (di/core.py) — UNCHANGED  │
│   register(), bind(), resolve_async(),      │
│   Provider protocol, DIPlugin hooks,        │
│   diagnostics, scope validation             │
└────────────────┬────────────────────────────┘
                 │ delegates hot lookups to
                 ▼
┌─────────────────────────────────────────────┐
│ Native: DIResolver                          │
│   token-key interner  (type → uint32)       │
│   flat cache          (uint32 → PyObject*)  │
│   provider index      (uint32 → uint32)     │
│   scope table         (uint32 → uint8)      │
└─────────────────────────────────────────────┘
```

The Python `Container` retains all semantics: scopes, cycle detection, plugin hooks, diagnostics, cross-app links, in-flight dedup. The native resolver owns only the **cache-hit fast path** and the **token→key mapping**.

This split is deliberate. The Phase 1 audit found three interacting cycle-detection mechanisms and a copy-on-write provider dict whose correctness depends on subtle `_providers_owned` bookkeeping. Reimplementing that in C++ would risk correctness for a cost that Phase 2 shows is not dominant. The native layer handles the part that is pure lookup.

---

## 3. Token interning

The single largest DI cost is `_unwrap_token` (1.17 µs), called on every resolve including cache hits. Root cause: it cannot tell a plain `type` from an `Annotated[T, Inject(...)]` without running `hasattr` and `get_origin`.

**Native solution:** intern the token once, at registration, and key the cache by `uint32`.

```cpp
class TokenInterner {
    // PyObject* (borrowed, type objects live forever) → dense id
    std::unordered_map<PyObject*, uint32_t> by_ptr_;
    std::unordered_map<std::string, uint32_t> by_name_;
    std::vector<std::string> names_;
public:
    // Fast path: pointer identity on a type object. No hasattr, no get_origin.
    uint32_t intern_type(PyObject* type) noexcept;
    uint32_t intern_name(std::string_view qualname);
    std::string_view name_of(uint32_t id) const noexcept;
};
```

`intern_type` is a single pointer-keyed hash lookup — ~15 ns versus 1,167 ns. Complex tokens (`Annotated`, `Inject`, `Optional`) are unwrapped **once** in Python at registration time and their resolved base type is interned. The hot path never sees them.

---

## 4. Flat resolution cache

```cpp
class DIResolver {
    TokenInterner interner_;
    std::vector<PyObject*> cache_;      // indexed by token id; nullptr = miss
    std::vector<uint8_t>   scopes_;     // indexed by token id
    bool frozen_ = false;

public:
    // Hot path. Returns borrowed ref or nullptr on miss.
    PyObject* get(uint32_t token_id) const noexcept {
        return token_id < cache_.size() ? cache_[token_id] : nullptr;
    }
    void put(uint32_t token_id, PyObject* obj) noexcept;  // steals a ref
    void clear_request_scope() noexcept;                  // resets request-scoped slots
};
```

A `std::vector` indexed by dense integer id replaces a Python dict keyed by string. Cache hit = one bounds check + one array load = **~5 ns** versus 22.6 ns for a raw Python `dict.get`, and versus 1,332 ns for the full `resolve_async` cache-hit path.

`clear_request_scope` walks a precomputed list of request-scoped token ids and decrefs them — O(number of request-scoped services actually resolved), not O(all providers).

---

## 5. Eliminating `register_instance` (B1, 3.68 µs)

Current per-request flow (`asgi.py:475`):
```python
await di_container.register_instance(RequestClass, request, scope="request")
di_container._cache["aquilia.request.Request"] = request
```

`register_instance` allocates a `ValueProvider`, forks the COW provider dict, emits a diagnostic event, and checks plugins — then line 476 writes the cache directly anyway, which is what actually satisfies subsequent lookups.

**Native replacement:**
```python
ctx = _core.RequestContext()
ctx.bind_request(request)        # single native slot write, ~10 ns
```

The `Request` token id is interned once at startup (`_REQUEST_TOKEN_ID`). `bind_request` writes `cache_[_REQUEST_TOKEN_ID] = request` with a single incref.

**Correctness note:** the current code's `register_instance` call also makes `Request` resolvable via `container.resolve(Request)` for user code and for `ContractProvider`. The native path preserves this because the resolver's `get()` is consulted by `Container.resolve_async` before the Python provider lookup — same visibility, same semantics, without the provider allocation.

**Gain: 3.68 µs → ~0.01 µs.**

---

## 6. Scope semantics (preserved exactly)

| Scope | Native cache behaviour | Owner |
|---|---|---|
| `singleton` | cached in root resolver, never cleared | root |
| `app` | cached in app resolver, cleared on app shutdown | app |
| `request` | cached in request slot table, cleared per request | request |
| `transient` | never cached | — |
| `pooled` | not native; delegates to Python provider | Python |
| `ephemeral` | never cached | — |

The scope byte table (`scopes_`) lets the resolver decide cacheability with one array load instead of a frozenset membership test (`_CACHEABLE_SCOPES`, `di/core.py:62`).

Scope *validation* (captive-dependency detection, `di/core.py:557-587`) stays in Python — it runs only on the miss path and its policy is configuration-driven (`DISettings.scope_enforcement`).

---

## 7. Graph compilation & cycle detection — stays in Python

`Registry.from_manifests` (`di/core.py:1527`) runs four phases at startup: load metadata, plugin hook, build graph, Tarjan SCC. Measured cost of Tarjan on a 64-node chain: **23.5 µs, once**. This is not a hot path and the Python implementation is correct and well-tested. **No native replacement.**

The three runtime cycle guards (`ResolveCtx.stack`, `_resolve_ancestors`, `_dep_ancestors`) also stay in Python. They use ContextVars for per-task isolation across `asyncio.gather` — semantics that would be fragile and expensive to reproduce in C++, and they only run on the miss path.

---

## 8. Thread safety

- `freeze()` transitions the resolver to immutable. Post-freeze, `get()` is lock-free and safe from any thread.
- Pre-freeze mutation (`add_provider`, `intern`) happens only during lifespan startup, single-threaded.
- Request-scope slot tables are **per-request objects**, never shared. No synchronisation needed.
- The app/singleton cache is written only on miss, under the GIL (the caller holds it because it is about to touch a `PyObject*`). Reads are plain array loads.

Phase 1 §8 noted the current pool is unsafe under free-threaded builds. The native design fixes this: request state is per-request, and shared state is frozen before concurrent access begins.

---

## 9. Error propagation

C++ exceptions never cross the ABI boundary. Every nanobind entry point is wrapped:

```cpp
try {
    return resolver.get(id);
} catch (const std::bad_alloc&) {
    throw nb::python_error(PyExc_MemoryError, "engine allocation failed");
}
```

DI-specific failures (not-found, cycle, scope violation) are **not** raised from C++. The native resolver returns `nullptr` on miss and the Python layer raises the existing `ProviderNotFoundError` / `DependencyCycleError` / `ScopeViolationError` with their full diagnostic payloads. This preserves the Phase 1 §9 contract that all framework errors are structured `Fault` subclasses.

---

## 10. Diagnostics & profiling

Compiled behind `AQUILIA_ENGINE_STATS=1`:

```cpp
struct ResolverStats {
    uint64_t hits = 0, misses = 0, request_clears = 0;
    uint64_t intern_hits = 0, intern_misses = 0;
};
```

Exposed as `resolver.stats()` → dict. Zero cost when the env var is unset (checked once at construction, branch predicted).

The existing `DIDiagnostics` event stream (`di/core.py:730`) is untouched — it fires on the Python miss path where it already lives.

---

## 11. Acceptance criteria

| Criterion | Target |
|---|---|
| Cached resolve | ≤ 200 ns (from 1,332 ns) |
| Per-request Request binding | ≤ 50 ns (from 3,680 ns) |
| Token intern (type) | ≤ 30 ns (from 1,167 ns) |
| Scope semantics | 100% of existing DI tests pass |
| Cycle detection | unchanged — all cycle tests pass |
| Plugin hooks | unchanged — all plugin tests pass |
| Fallback parity | identical results with `_NATIVE=False` |
