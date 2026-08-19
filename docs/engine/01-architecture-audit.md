# Phase 1 — Aquilia Architectural Audit

**Status:** complete
**Method:** direct source reading of the hot path (~24k lines) + static AST import-graph analysis (`benchmarks/engine/import_graph.py`, 639 modules, zero parse failures). No assumptions; every claim below cites `file:line`.
**Repo state:** branch `feature/aquilia-core-engine`, base `a3eda3d1`, version 1.4.0b0.

---

## 1. Scale

| Metric | Value |
|---|---|
| Python files in `aquilia/` | 639 |
| Total LOC in `aquilia/` | 256,710 |
| Hot-path LOC (asgi, di, controller, aquilary, middleware, request/response) | ~23,800 |
| Subpackages | 40 |
| Internal import edges | 2,199 |
| Tests | 189 files |

Largest subsystems by LOC: `models/` (30k), `admin/` (24.8k), `cli/` (23.8k), `contracts/` (12.8k), `auth/` (11.4k), `controller/` (8.5k), `di/` (7.3k).

---

## 2. Boot sequence

Confirmed against source, matching the documented `Manifests → Aquilary → RuntimeRegistry → Controllers → ASGI` chain.

```
aquilia/entrypoint.py:98  create_app()
      │  reads AQUILIA_WORKSPACE (default /app), AQUILIA_ENV (default prod)
      │  entrypoint.py:81 _sanitise_env — rejects NUL bytes, allowlists mode
      ▼
aquilia/runtime.py  AquiliaRuntime.from_workspace()
      │  loads workspace.py via ConfigLoader
      │  discovers modules/*/manifest.py via importlib
      ▼
aquilia/server.py:AquiliaServer.__init__
      │  _bootstrap_signing()            — shared signing key for sessions/CSRF/cache
      │  HealthRegistry()                — subsystem health
      │  FaultEngine(debug=...)          — structured error engine
      │  Aquilary.from_manifests(...)    — static validation phase (no app code imported)
      ▼
aquilia/aquilary/core.py  AquilaryRegistry
      │  AppContext per module (name, version, route_prefix, lazy import paths)
      │  dependency graph + RegistryFingerprint (SHA-256, deployment gating)
      ▼
RuntimeRegistry
      │  per-app DI Container, service registration, cross-app dependency links
      ▼
ControllerCompiler.compile_controller()  (controller/compiler.py:81)
      │  extract_controller_metadata()   (controller/metadata.py:171)
      │  → CompiledController / CompiledRoute
      ▼
ControllerRouter.initialize()            (controller/router.py:106)
      │  builds static hash map + segment trie + regex fallback + name index
      ▼
MiddlewareStack.build_handler()          (middleware.py:170)
      ▼
ASGIAdapter                              (asgi.py:40)
```

**Startup is lifespan-driven, not import-driven.** `ASGIAdapter.handle_lifespan` (asgi.py:735) awaits `server.startup()` then invalidates four caches (asgi.py:745-749) — `_cached_middleware_chain`, `_default_container`, `_has_routes_cache`, `_debug`, `_server_runtime`. This matters for any native engine: **the route table and DI graph are not final until after `lifespan.startup`**, so an engine cannot compile them at import time.

**Shutdown** (asgi.py:765) awaits `server.shutdown()` and always replies `shutdown.complete` even on error — deliberate, so orchestrators aren't blocked.

**Failure policy:** `entrypoint.py:183-222` swallows all startup exceptions into a 500-stub app unless `AQUILIA_FAIL_FAST` is set. Any native engine load failure must therefore be **non-fatal by default**, or it will silently turn a working app into a 500-stub.

---

## 3. Request lifecycle (the hot path)

`ASGIAdapter.handle_http` (asgi.py:374) — annotated with real measurements from §Phase 2:

| # | Step | Source | Cost |
|---|---|---|---|
| 1 | Build middleware chain (once, idempotent) | asgi.py:384 | amortised |
| 2 | `/_health` fast path | asgi.py:397 | — |
| 3 | `Request(scope, receive)` | asgi.py:405 | 0.20 µs |
| 4 | `_resolve_route_inputs` — version pre-resolution | asgi.py:411 | ~0 when versioning off |
| 5 | `controller_router.match_sync` | asgi.py:423 | **0.79 µs** static / **1.17 µs** dynamic |
| 6 | 405/HEAD fallback | asgi.py:431-449 | miss-path only |
| 7 | `app_container.create_request_scope()` | asgi.py:467 | 0.11 µs |
| 8 | `register_instance(Request, ...)` + `_cache` write | asgi.py:475-476 | **3.68 µs** |
| 9 | `_ctx_pool.acquire(...)` | asgi.py:479 | **1.93 µs** |
| 10 | 5–6 `request.state[...]` writes | asgi.py:488-499 | small |
| 11 | metrics + `time.monotonic()` | asgi.py:502-509 | small |
| 12 | `await handler(request, ctx)` → middleware → `_final_handler` → `ControllerEngine.execute` | asgi.py:511 | remainder |
| 13 | `metrics.request_finished`, `_ctx_pool.release(ctx)` | asgi.py:561-580 | included in 9 |
| 14 | `response.send_asgi(send, request)` | asgi.py:590 | 1.14 µs |

Measured total: **16.49 µs/request** static (60,644 req/s in-process), **20.21 µs** dynamic.

### 3.1 Controller execution

`ControllerEngine.execute` (controller/engine.py:148) branches three ways:

1. **Monkeypatched handler** (engine.py:175) — OpenAPI/admin routes, bypasses DI.
2. **Simple fast path** (engine.py:356) — skips `_bind_parameters`, contracts, lifecycle hooks. Gated by `_simple_route_cache[id(route)]` (engine.py:318), with a weak-reference ownership check so a reused object ID cannot inherit another route's classification.
3. **Full path** (engine.py:404) — `_bind_parameters`, filters, pagination, contracts, content negotiation.

The route caches key on `id(route)` with weak-reference ownership checks; a reused object ID is rejected and recomputed. Callable caches still use stable underlying function identities.

### 3.2 Middleware

`MiddlewareStack` (middleware.py:89) sorts by priority (`_sort_middlewares`, middleware.py:159) and pre-wraps closures once (`build_handler`, middleware.py:170). Chain is built once and cached in `ASGIAdapter._cached_middleware_chain` — correct design, no per-request rebuild.

Container cleanup is delegated to `ServerRequestScopeMiddleware` (server.py:100), whose `finally` calls `ctx.container.shutdown()`. asgi.py:569-576 documents that the redundant shutdown was deliberately removed to save ~1 µs, relying on `FaultMiddleware` wrapping the chain. **This is a coupling worth noting: removing `request_scope_mw` leaks request containers.**

---

## 4. Dependency Injection

`aquilia/di/core.py:208` — `Container`, `__slots__`-based, 14 slots.

**Scopes:** `singleton`, `app`, `request`, `transient`, `pooled`, `ephemeral`. Cacheable set is a frozenset (`_CACHEABLE_SCOPES`, core.py:62).

**Request scope creation is copy-on-write** (core.py:740): `child._providers = self._providers` by reference, `_providers_owned = False`, forked on first `register()`. Measured at 0.11 µs — genuinely cheap, and it scales flat (0.11 µs at 10 providers, same at 1000).

**Resolution** (`resolve_async`, core.py:496):
- Inlines `token_to_key` for str/type (core.py:516-524) with a bounded module cache `_type_key_cache` (8192 entries, flushed wholesale — core.py:28-36).
- Cache hit returns at core.py:530-532.
- Miss path: provider lookup → cross-app links → scope delegation to parent → scope validation → `ResolveCtx` cycle guard → cross-link cycle guard via `_resolve_ancestors` ContextVar → in-flight dedup Future → `provider.instantiate(ctx)`.

**Three independent cycle-detection mechanisms**, each necessary and documented:
1. `ResolveCtx.stack` (core.py:142) — per-container.
2. `_resolve_ancestors` ContextVar (core.py:57) — crosses container-link boundaries (core.py:609-620).
3. `_dep_ancestors` ContextVar (core.py:50) — distinguishes a true cycle from a benign diamond in `Dep()` resolution (core.py:968-987).

Static validation is separate: `Registry.from_manifests` (core.py:1527) runs 4 phases — load metadata, plugin hook, build graph, Tarjan SCC cycle detection (`di/graph.py:41`), cross-app `depends_on` validation.

**Concurrency:** in-flight `asyncio.Future` dedup (core.py:623-639) ensures parallel branches share one singleton instance. Correct, and required by `parallel_resolution` in `providers.py:31`.

---

## 5. Routing

`ControllerRouter` (controller/router.py:68) — three tiers:

| Tier | Structure | Complexity | Source |
|---|---|---|---|
| 1 | static hash map `{method: {path: [(route, params, query)]}}` | O(1) | router.py:260 |
| 2 | segment trie `_TrieNode` | O(k), k = depth | router.py:279 |
| 3 | regex list | O(n) | router.py:286 |

Trie insertion (`_trie_insert`, router.py:181) returns `False` for patterns it can't represent (regex constraints, wildcards), which then fall to tier 3 — a clean, correct degradation.

**Measured scaling (E5) proves the trie works:**

| routes | static | dynamic | miss |
|---|---|---|---|
| 15 | 832 ns | 1,228 ns | 284 ns |
| 150 | 840 ns | 1,239 ns | 291 ns |
| 750 | 865 ns | 1,248 ns | 288 ns |
| 3000 | 858 ns | 1,300 ns | 299 ns |

**200× the routes costs +3% lookup.** The algorithm is not the problem — constant-factor Python overhead is (see Phase 2 §B1).

Reverse routing uses `_name_index` built at `initialize()` (router.py:163-172) for O(1) `url_for`.

---

## 6. Import graph & package boundaries

From `benchmarks/engine/import_graph.py`:

- **2,199 internal import edges**; 1,641 top-level, **1,072 function-local (39.5% deferred)**.
- **One SCC containing all 40 subpackages.** There are no clean layers at the subpackage level.
- 11 module-level SCCs, largest = **92 modules** (`auth`, `sessions`, `http`, `contracts`, `models`…).
- Highest fan-in: `aquilia.<root>` (37), `faults` (34), `di` (16), `inspector` (15).
- Highest fan-out: `aquilia.<root>` (40), `cli` (19), `admin` (13), `controller` (10).

Worst offenders for deferred imports: `server.py` (52), `di/core.py` (43), `admin/controller.py` (32), `controller/engine.py` (31), `aquilary/core.py` (30).

**Interpretation.** The function-local imports are a *deliberate and load-bearing* cycle-breaking device, not sloppiness. Because the subpackage graph is a single SCC, moving these to module scope would produce genuine `ImportError`s. This constrains the engine design: **a native module must not participate in that cycle**. It must be a leaf with zero `aquilia.*` imports, or it will make the SCC worse and become unimportable.

**Cold import cost:** `aquilia` 1.3 ms (lazy façade — good), but `aquilia.controller.router` **111 ms** and `aquilia.server` **158 ms**. Startup is dominated by import, not by route/DI compilation (route build is 35–96 µs/route; 150 routes ≈ 5–14 ms).

---

## 7. Caching inventory (existing)

| Cache | Location | Key | Bound |
|---|---|---|---|
| `_type_key_cache` | di/core.py:29 | `type` | 8192, flush-all |
| `_signature_cache` | engine.py:126 | callable | **unbounded** |
| `_pipeline_param_cache` | engine.py:127 | `id(callable)` | **unbounded, id-keyed** |
| `_has_lifecycle_hooks` | engine.py:128 | class | unbounded |
| `_simple_route_cache` | engine.py:129 | `id(route)` + weakref | unbounded, stale IDs rejected |
| `_clearance_cache` | engine.py:130 | `id(route)` + weakref | unbounded, stale IDs rejected |
| `_static_routes` / `_tries` / `_dynamic_routes` / `_name_index` | router.py:85-92 | — | built at init |
| `_cached_middleware_chain` | asgi.py:75 | — | invalidated on startup |
| `_ctx_pool` | controller/base.py:311 | — | ring buffer, 256 |

Notably **absent**: no cache for `get_type_hints` (engine.py:1494) — measured 2.64 µs/request, the second-largest single cost in the budget.

---

## 8. Thread-safety & async model

- Fully async request pipeline; no threads in the hot path.
- `_ctx_pool` (controller/base.py:234) is explicitly documented as safe only for single-threaded async — a plain `list`, no lock. Correct under one event loop per process; **would corrupt under free-threaded 3.13+ or multi-loop-per-process**.
- `Container._cache` / `_providers` are plain dicts — safe under GIL + single loop, protected across concurrent tasks by the in-flight Future dedup.
- ContextVars (`_dep_ancestors`, `_resolve_ancestors`, `_CURRENT_REQUEST_CTX`) give per-task isolation and copy correctly across `asyncio.gather`.
- `di/_sync_bridge.py` drives async resolution on a persistent per-thread loop for the sync `resolve()` API; raises inside a running loop.

**Implication for a native engine:** any shared mutable native state must be explicitly synchronised, because the current Python code's safety derives from the GIL + single-loop assumption that C++ code does not inherit.

---

## 9. Extension points (the public contract that must not break)

1. `Controller` subclass + `@GET/@POST/...` decorators → `controller/decorators.py`
2. `AppManifest` declarations → `manifest.py`
3. `Middleware` protocol with priority → `middleware.py:48`
4. `Provider` protocol (`meta`/`instantiate`/`shutdown`) → `di/core.py:151`
5. `DIPlugin` hooks → `di/plugins.py` (`on_registry_build`, `on_container_built`, `on_provider_registered`)
6. `Fault` subclasses with stable `code`/`domain`/`severity` → `faults/`
7. `Dep()` / `Inject()` / `Annotated[...]` parameter markers → `di/dep.py`
8. Diagnostic listeners → `Container.add_diagnostic_listener` (core.py:730)
9. Interceptors / exception filters / guards → `controller/base.py`
10. `RequestCtx` dynamic attributes via `_extra` (controller/base.py:167-185)

Anything native must preserve all ten, and #10 in particular is what makes `RequestCtx` expensive (§Phase 2 B3).

---

## 10. Conclusions carried into Phase 2

1. The architecture is **sound and already optimised at the algorithmic level** — trie routing, COW request scopes, cached middleware chain, object pooling, bounded type-key cache.
2. Remaining costs are **constant-factor Python overhead**, not complexity. This is exactly the class of problem native code addresses — but only if the constant factors being paid are large relative to the whole request.
3. The single-SCC import graph means a native module **must be a dependency leaf**.
4. The route table is only final **after `lifespan.startup`** — compilation must be deferred.
5. Startup failure policy is **fail-soft by default** — engine load must never be fatal.
