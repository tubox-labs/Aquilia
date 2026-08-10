# Aquilia v1.4.0b3 Release Notes — "Helmsman's Compass"

Aquilia v1.4.0b3 continues the beta cycle for the 1.4 series with the new **`aquilia.vectordb`** subsystem, a comprehensive overhaul of the **CLI architecture**, introduction of the **Unified Health Checks Engine**, single-source **Exit Code contract**, lazy **`AqContext` state thread**, a documented and enforced **subsystem boot contract**, and native C++ **router memory leak resolution**.

---

## Table of Contents

1. [Release Overview](#release-overview)
2. [Highlights](#highlights)
3. [Vector Database Subsystem](vectordb.md)
   - `aquilia.vectordb` — typed models over embedded elips
   - `VectorDatabaseIntegration`, `Workspace.vectordb()`, `AquilaConfig.VectorDB`
   - `AppManifest.vector_models` and `vector_models/` discovery
   - `VectorDBSubsystem` — priority 28, conditional required-ness
   - SQL-ORM interop: `Link`, `resolve`, `mirror`, `as_models`, `reindex`
4. [`aq vectordb` Command Reference](vectordb_cli.md)
   - `status`, `gpu`, `models`, `inspect`, `stats`
   - `compact`, `vacuum`, `compress`, `reindex`, `reembed`
   - Lock discipline and common workflows
5. [CLI Architecture Overhaul](cli_modernization.md)
   - `aquilia.cli.core` subsystem layout
   - `AqContext` — thread-safe, lazily resolved ambient CLI state
   - `ExitCode` — single source of truth for process return codes
   - `CliFault` — structured fault domain replacing `sys.exit()`
   - `LoadedWorkspace` — Python-first workspace loader with regex fallback
   - `CommandSpec` — category-driven command registry & help grouping
6. [Unified Health Checks Engine](checks_engine.md)
   - `Finding` & `Check` protocol (`@register_check`)
   - Standardized runners and human/JSON report renderers
   - Config-driven subsystem probes across core framework modules
   - The new `vectordb.driver` check
   - Workspace integrity probes & route extraction checking
7. [Subsystem Boot Contract](subsystem_boot_contract.md)
   - `BootContext.di_containers()` and `DI_CONTAINER_KEY`
   - `_timeout` enforcement in `BaseSubsystem.initialize()`
   - Live `/health` checks replacing the boot-time snapshot
   - Who drives subsystems, and why there is no `SubsystemOrchestrator`
8. [Admin Lifecycle & Rate Limiter](admin_lifecycle.md)
   - Admin startup/shutdown hooks wired into `AquiliaServer`
   - `AdminRateLimiter.force_cleanup()` public sweep API
9. [Native Router Memory Leak Fix](router_memory_leak_fix.md)
   - Native C++ nanobind Router instance cleanup on server shutdown
   - `ControllerRouter.clear()` protocol
   - `ASGIAdapter.shutdown()` lifecycle hook
10. [Bug Fixes & Refactorings](bug_fixes.md)
    - Silent exit code 0 bug on workspace/DB failures fixed
    - Route count reporting mismatch fixed (real HTTP routes vs controller counts)
    - Non-existent route attribute inspection bug fixed
    - Subsystem DI registration, timeout, and health-check defects fixed
    - Admin lifecycle never invoked; rate-limit sweep no-op on fresh hosts
    - Workspace integration detection returning bound methods
    - Docsite TS2657 React fragment build error fixed
11. [Migration Guide & Breaking Changes](migration.md)
    - Removal of legacy CLI parsers (`discovery_cli.py`, `parsers/`)
    - Exit code changes for CI/CD pipelines
    - Optional `vectordb` extra and the Python 3.10 marker
    - Upgrade checklist & compatibility matrix

---

## Release Overview

Aquilia v1.4.0b3 does two things: it adds a whole new data subsystem, and it pays down operational debt in the layers that boot and diagnose everything else.

**`aquilia.vectordb`** is the new surface. Retrieval-augmented workloads previously had no home in the framework — applications bolted a vector client onto a service, hand-rolled serialization between the ORM and the store, and got no boot validation, no health reporting, no CLI, and no fault taxonomy. The subsystem gives vector collections the same declarative shape the SQL ORM gives tables, keeps its driver (`elips`) an optional extra, and makes the two failure modes that produce *silently wrong* results — dimension mismatch and embedder-lineage mismatch — hard errors instead of confident nonsense.

The rest is repair. Prior to this release, `aq doctor` and `aq validate` relied on ~1,000 lines of duplicated, drifting logic that silently caught errors, printed warning banners, and exited with status code `0`. Commands scraped `workspace.py` with brittle regex patterns and probed non-existent controller attributes. The subsystem layer documented a timeout it never enforced and a DI key nothing ever set. Admin's lifecycle hooks were written, tested, and never called. `/health` served a boot-time snapshot that could not notice a dependency dying an hour later.

v1.4.0b3 fixes each of those where it lives: a unified, modular CLI architecture (`aquilia.cli.core`, `aquilia.cli.checks`, `aquilia.cli.introspect`) built around a single source of truth for exit codes, and a subsystem layer whose contract is now written down and enforced by tests.

---

## Highlights

### 1. Vector Database Subsystem

`aquilia.vectordb` — 24 modules — brings typed vector models, similarity search, embedders, chunking, GPU policy, quantization, and SQL-ORM interop into the framework:

```python
from aquilia.vectordb import VectorModel, KeyField, TextField, VectorField, Field

class Document(VectorModel):
    key:    str         = KeyField(prefix="doc_")
    body:   str         = TextField(embed=True, min_length=1)
    vector: list[float] = VectorField(dimension=384)
    source: str         = Field(default="web", indexed=True)

    class Meta:
        collection = "documents"
        store = "default"

hits = await Document.vectors.query().filter(source="docs").search(text="release notes", limit=10)
```

The driver is an optional extra (`pip install 'aquilia[vectordb]'`). An install without it behaves exactly as before: importing the package succeeds, and `VectorNotInstalledFault` surfaces at first *use*. Discovery imports nothing when no module declares a vector model.

See [vectordb.md](vectordb.md) and [vectordb_cli.md](vectordb_cli.md).

### 2. Unified Health Checks Engine & Single-Source Exit Codes

The fragmented `doctor.py` and `validate.py` implementations are merged into a single health check registry (`aquilia.cli.checks`). Every check yields structured `Finding` objects with stable error codes (e.g. `AQ_DB_MISSING`, `AQ_ROUTE_CONFLICT`), a severity (`INFO`, `WARN`, `ERROR`, `FATAL`), a location, and actionable remedies.

Exit codes are governed strictly by `aquilia.cli.core.exits.exit_code_for()`:
- `ExitCode.OK` (`0`) — All checks pass or emit only `INFO`/`WARN` findings.
- `ExitCode.FAILED` (`1`) — At least one `ERROR` or `FATAL` finding was discovered.
- `ExitCode.USAGE` (`2`) — Argument/invocation error.
- `ExitCode.CONFIG` (`3`) — Workspace or configuration file could not be loaded.
- `ExitCode.INTERNAL` (`4`) — Unhandled internal CLI exception.

### 3. `AqContext` & Python-First Workspace Loading

Ad-hoc `ctx.obj` dictionary manipulation is replaced by `AqContext`. Workspace discovery is lazy: non-workspace commands like `aq init`, `aq version`, and `aq --help` execute instantaneously without incurring workspace import overhead.

When loaded, `workspace.py` is executed as Python code rather than parsed with regular expressions. Declared starter controllers (`.starter("name")`) and module-level `route_prefix` definitions are accurately parsed into `LoadedWorkspace`. Regex parsing remains solely as an automatic fallback when user code contains import errors.

### 4. Subsystem Coverage Expansion

Framework subsystems totalling ~45,000 lines of code had zero CLI health monitoring in previous releases. `aquilia.cli.checks.subsystems` introduces config-driven probes for:
`tasks`, `templates`, `storage`, `cache`, `mail`, `i18n`, `otel`, `sse`, `versioning`, `http`, `auth`, `sockets`, `contracts`, `mlops`, `vectordb`, and `admin`.

Probes are strictly config-driven and remain silent for unused subsystems, avoiding noise in minimal applications. `vectordb` additionally gets a dedicated `vectordb.driver` check that reports `AQ_VECTORDB_DRIVER_MISSING` when a workspace declares vector stores on an install without `elips`.

### 5. Subsystem Boot Contract Documented and Enforced

`aquilia.subsystems` declared a 30-second initialization timeout that nothing read, and a DI `shared_state` key that nothing set. Both are fixed:

- `BaseSubsystem.initialize()` now wraps `_do_initialize` in `asyncio.wait_for(...)`, so a subsystem blocking on an unreachable dependency degrades to `UNHEALTHY` with a named cause instead of hanging the boot forever.
- `BootContext.di_containers()` is the single DI resolution path — explicit container first, then every container in `registry.di_containers`. `StorageSubsystem` and `EffectSubsystem` both use it, so both actually register.
- `/health` now calls `HealthRegistry.run_checks()` before rendering, so a backend that died an hour after boot is no longer masked by the boot-time snapshot.

The package docstring also states plainly what it is: the entry point for hosts that drive subsystems themselves. `AquiliaServer` boots storage, cache, tasks, mail and effects through its own ordered `_setup_*` methods, and there is deliberately no `SubsystemOrchestrator` to keep in sync with it.

See [subsystem_boot_contract.md](subsystem_boot_contract.md).

### 6. Admin Lifecycle Wired

`AdminLifecycle.on_startup()` / `on_shutdown()` were written, tested in isolation, and never called by anything. Admin routes worked; the audit log was never flushed, the rate limiter never swept, and the cache service and task manager were never resolved from DI. `AquiliaServer.startup()` gained Step 3.25 and `shutdown()` its mirror, both gated on `config["integrations"]["admin"]` and non-fatal on failure.

See [admin_lifecycle.md](admin_lifecycle.md).

### 7. Native Router Memory Leak Resolution

During server shutdown, ASGI lifespan termination, or test teardown, native C++ `Router` instances wrapping nanobind bindings could remain referenced in memory, producing nanobind leak warnings on process termination.

v1.4.0b3 adds `ControllerRouter.clear()` and updates `AquiliaServer.shutdown()` and `ASGIAdapter.shutdown()` to explicitly reset C++ router references and internal route tables, eliminating leak warnings.

---

## Summary of Subsystem Changes

| Subsystem / Module | Status | Summary |
|---|---|---|
| `aquilia.vectordb` | **New** | 24-module typed vector layer over embedded elips — models, fields, queries, EQL, embedders, chunking, GPU policy, quantization, ORM interop |
| `aquilia.vectordb.subsystem` | **New** | `VectorDBSubsystem` — priority 28, 60s timeout, `_required` raised when stores are declared |
| `aquilia.integrations.vectordb` | **New** | `VectorDatabaseIntegration` — typed store declaration, normalizes `{alias: config}` into store entries |
| `aquilia.cli.commands.vectordb` | **New** | `aq vectordb` group — `status`, `gpu`, `models`, `inspect`, `stats`, `compact`, `vacuum`, `compress`, `reindex`, `reembed` |
| `aquilia.pyconfig` | **Improved** | `AquilaConfig.VectorDB` nested config class (disabled by default) |
| `aquilia.workspace` | **Improved** | `Workspace.vectordb()` builder; `vectordb` recognised by `integrate()`; emitted into `to_dict()` |
| `aquilia.config._loader` | **Improved** | `ConfigLoader.get_vectordb_config()` with disabled-by-default defaults |
| `aquilia.manifest` | **Improved** | `AppManifest.vector_models`, `ComponentKind.VECTOR_MODEL`, `vector_models` in default `auto_discovery` |
| `aquilia.aquilary.core` | **Improved** | `AppContext.vector_models`; `_discover_vector_models()` scan and `_register_vector_models()` import pass |
| `aquilia.subsystems.base` | **Improved** | `DI_CONTAINER_KEY`, `BootContext.di_containers()`, enforced `_timeout`, documented population contract |
| `aquilia.subsystems.effects` | **Fixed** | DI registration via `di_containers()`; `health_check()` uses `details=` not the non-existent `metadata=` |
| `aquilia.storage.subsystem` | **Fixed** | DI registration repaired (dead `_di_registry` key); registers a live health check |
| `aquilia.asgi` | **Improved** | `/health` runs `HealthRegistry.run_checks()` before rendering; `ASGIAdapter.shutdown()` releases runtime, container & middleware chain |
| `aquilia.server` | **Improved** | Admin lifecycle startup (Step 3.25) and shutdown wired; `shutdown()` invokes `controller_router.clear()` |
| `aquilia.admin.security` | **Improved** | `AdminRateLimiter.force_cleanup()` public sweep API; `_sweep()` returns exact removal counts |
| `aquilia.admin.subsystems` | **Fixed** | `rate_limit_cleanup()` no longer pokes private state — no-op on hosts up < `cleanup_interval` fixed |
| `aquilia.cli.checks.subsystems`| **Improved** | `_integration()` reads `Workspace._integrations` and skips callables; new `vectordb.driver` check |
| `aquilia.cli.core.registry` | **Improved** | `vectordb` categorised under **Database** in `aq --help` |
| `aquilia.cli.core.exits` | **New** | `ExitCode` enum, `SEVERITY_ORDER`, `exit_code_for()` single source of truth |
| `aquilia.cli.core.faults` | **New** | `CliFault` hierarchy (`WorkspaceNotFoundFault`, `WorkspaceLoadFault`, etc.) |
| `aquilia.cli.core.context` | **New** | `AqContext` lazy state thread replacing `ctx.obj` dictionary access |
| `aquilia.cli.core.workspace` | **New** | `LoadedWorkspace`, `load_workspace()`, `ensure_importable()` |
| `aquilia.cli.checks.base` | **New** | `Finding`, `Check`, `CheckResult`, `@register_check()`, `run_checks()` |
| `aquilia.cli.checks.report` | **New** | `render_human()`, `render_json()`, `summarise()`, `result_exit_code()` |
| `aquilia.cli.checks.workspace` | **New** | Core health checks (Python version, modules, manifests, routes, DI, DB) |
| `aquilia.cli.introspect.routes`| **New** | Route introspection via `ControllerCompiler` (replaces legacy attribute probes) |
| `aquilia.cli.discovery_cli` | **Removed** | Legacy discovery CLI helper deleted |
| `aquilia.cli.parsers` | **Removed** | Legacy manifest regex parsers (`module.py`, `workspace.py`) deleted |
| `aquilia.controller.router` | **Improved** | `ControllerRouter.clear()` releases C++ nanobind `_native` instance |
| `pyproject.toml` | **Improved** | New `vectordb` extra (`elips>=1.1.0; python_version >= '3.11'`), folded into `full` |
| `aqdocx` | **Fixed** | Fixed TS2657 JSX single-parent return error in `MiddlewareOverview.tsx` |

---

## Performance Improvements

1. **Lazy CLI Execution**: Commands that do not require workspace inspection (`aq init`, `aq version`, `aq --help`, `aq mcp`) run in `<15ms` by avoiding workspace file discovery and import overhead.
2. **Cached Manifest Resolution**: `LoadedWorkspace.manifest()` caches `AppManifest` references during multi-check runs, eliminating redundant disk reads.
3. **Native Router Deallocation**: Timely release of native C++ CPython extension structures reduces memory overhead during unit testing and server restarts.
4. **Zero-Cost Vector Layer When Unused**: `aquilia.vectordb.__init__` defers `engine`, `gpu`, `interop`, `embedders`, `eql`, `chunking` and `subsystem` behind `_LAZY_ATTRS`, so nothing reaches `elips` on import. Vector-model discovery imports nothing when no module declares one, so an app without vector models pays no import cost at all.
5. **Dedicated Vector Thread Pool**: elips calls run on a named `aquilia-vdb` `ThreadPoolExecutor` rather than the default executor, so a long `compact()` cannot starve unrelated `run_in_executor` callers, and a stalled vector operation is identifiable in a stack dump.
6. **Bounded Subsystem Boot**: enforced `_timeout` turns an unreachable dependency from an indefinite hang into a bounded `UNHEALTHY` result.

---

## Developer Experience Improvements

- **Actionable CLI Diagnostics**: Every health finding displays a stable error code (e.g. `[AQ_DB_MISSING]`), source location (`at: db.sqlite3`), and a concrete fix (`fix: Run migrations to create the DB`).
- **Machine-Readable Output**: `aq doctor --json`, `aq validate --json`, and every `aq vectordb` subcommand's `--json` emit standardized payloads structured for CI/CD test runners.
- **Accurate Route Tree**: `aq inspect routes` compiles routes using `ControllerCompiler`, displaying exact paths served (including module prefixes and starter routes).
- **Vector Slot Introspection**: `aq vectordb models` shows how each attribute was routed (key / text / vector / payload / link) — routing is resolved at class creation and is otherwise invisible in the source.
- **Honest `/health`**: the endpoint re-runs registered checks per request, so a dead dependency is visible without a restart.

---

## Documentation Improvements

- New `docs/vectordb.md` — the complete `aquilia.vectordb` reference (fields, codecs, queries, EQL, embedders, chunking, GPU, faults, operations), linked from `docs/README.md`.
- New release pages: [vectordb.md](vectordb.md), [vectordb_cli.md](vectordb_cli.md), [subsystem_boot_contract.md](subsystem_boot_contract.md), [admin_lifecycle.md](admin_lifecycle.md).
- `aquilia.subsystems` package docstring now states who drives subsystems and why there is no `SubsystemOrchestrator`, with a composable ordered-boot example.
- `BootContext` carries a field-by-field population contract table naming who sets each field and what happens when it is `None`.
- `BaseSubsystem` documents that `required` may be computed during `_do_initialize` and must be read after `initialize()` returns.

---

## Upgrade Checklist

- [ ] Update `aquilia` to `1.4.0b3` in `pyproject.toml` / `requirements.txt`.
- [ ] Update CI/CD pipelines to expect non-zero exit codes (code `1` or `3`) when `aq validate` or `aq doctor` encounters errors.
- [ ] Remove any internal references to deprecated `aquilia.cli.parsers` modules.
- [ ] Run `aq doctor` to perform a full workspace health check under the new engine.
- [ ] If adopting vector search: `pip install 'aquilia[vectordb]'` (Python 3.11+), add `.vectordb(stores={...})` to `workspace.py`, declare models under `modules/<app>/vector_models.py`, then verify with `aq vectordb status` and `aq vectordb models`.
- [ ] If you build `BootContext` by hand: replace `shared_state["_di_registry"]` with `shared_state[DI_CONTAINER_KEY]`, or pass `registry=`.
- [ ] If you subclass `BaseSubsystem`: confirm `_do_initialize` is cancellation-safe, or set `_timeout = 0` to opt out of the bound.
- [ ] If you poke `AdminRateLimiter` privates: switch to `force_cleanup()`.
- [ ] If `/health` is polled aggressively: budget for one check invocation per registered subsystem per request.

---

## Known Issues

- **`elips` has no cp310 wheels.** On Python 3.10 the `vectordb` extra installs nothing and vector support degrades to `VectorNotInstalledFault` at first use. The environment marker is deliberate — without it, `aquilia[full]` would be unresolvable on 3.10 rather than simply omitting vector support.
- **Single-writer stores and `workers > 1`.** elips takes an exclusive lock per database directory. Multi-worker deployments must give each worker its own store path or mark the shared store `read_only=True`. There is no shared-writer mode planned; elips is embedded by design.
- **`VectorDBSubsystem` is not driven by `AquiliaServer`.** Like every other `BootContext` subsystem, it is initialized by the host — an embedder, an alternative runner, a test, or a module lifecycle hook. The `aq vectordb` commands configure and shut down `VectorRegistry` themselves and need none of this. See [vectordb.md](vectordb.md#wiring-the-store-lifecycle).

---

## Credits

Special thanks to the Aquilia core team and community contributors for auditing CLI failure modes, the subsystem boot layer, and admin lifecycle wiring, and for implementing native C++ lifetime bounds and the vector database subsystem.

