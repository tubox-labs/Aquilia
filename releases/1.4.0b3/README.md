# Aquilia v1.4.0b3 Release Notes — "Helmsman's Compass"

Aquilia v1.4.0b3 continues the beta cycle for the 1.4 series with a comprehensive overhaul of the **CLI architecture**, introduction of the **Unified Health Checks Engine**, single-source **Exit Code contract**, lazy **`AqContext` state thread**, and native C++ **router memory leak resolution**.

---

## Table of Contents

1. [Release Overview](#release-overview)
2. [Highlights](#highlights)
3. [What's New](#whats-new)
4. [CLI Architecture Overhaul](cli_modernization.md)
   - `aquilia.cli.core` subsystem layout
   - `AqContext` — thread-safe, lazily resolved ambient CLI state
   - `ExitCode` — single source of truth for process return codes
   - `CliFault` — structured fault domain replacing `sys.exit()`
   - `LoadedWorkspace` — Python-first workspace loader with regex fallback
   - `CommandSpec` — category-driven command registry & help grouping
5. [Unified Health Checks Engine](checks_engine.md)
   - `Finding` & `Check` protocol (`@register_check`)
   - Standardized runners and human/JSON report renderers
   - Config-driven subsystem probes across 13 core framework modules
   - Workspace integrity probes & route extraction checking
6. [Native Router Memory Leak Fix](router_memory_leak_fix.md)
   - Native C++ nanobind Router instance cleanup on server shutdown
   - `ControllerRouter.clear()` protocol
   - `ASGIAdapter.shutdown()` lifecycle hook
7. [Bug Fixes & Refactorings](bug_fixes.md)
   - Silent exit code 0 bug on workspace/DB failures fixed
   - Route count reporting mismatch fixed (real HTTP routes vs controller counts)
   - Non-existent route attribute inspection bug fixed
   - Docsite TS2657 React fragment build error fixed
8. [Migration Guide & Breaking Changes](migration.md)
   - Removal of legacy CLI parsers (`discovery_cli.py`, `parsers/`)
   - Exit code changes for CI/CD pipelines
   - Upgrade checklist & compatibility matrix

---

## Release Overview

Aquilia v1.4.0b3 addresses long-standing operational debt in the CLI subsystem while hardening the native C++ engine against memory leaks. 

Prior to this release, `aq doctor` and `aq validate` relied on ~1,000 lines of duplicated, drifting logic that silently caught errors, printed warning banners, and exited with status code `0`. A workspace missing its database or declaring unloadable module components would report as "healthy" to CI/CD pipelines. Furthermore, commands scraped `workspace.py` using brittle regex patterns and probed non-existent controller attributes (`__controller_routes__`).

v1.4.0b3 introduces a unified, modular CLI architecture (`aquilia.cli.core`, `aquilia.cli.checks`, `aquilia.cli.introspect`) built around a single source of truth for exit codes (`ExitCode`), structured CLI faults (`CliFault`), lazy workspace loading (`AqContext`), and a config-driven health check protocol (`@register_check`).

---

## Highlights

### 1. Unified Health Checks Engine & Single-Source Exit Codes

The fragmented `doctor.py` and `validate.py` implementations are merged into a single health check registry (`aquilia.cli.checks`). Every check yields structured `Finding` objects with stable error codes (e.g. `AQ_DB_MISSING`, `AQ_ROUTE_CONFLICT`), a severity (`INFO`, `WARN`, `ERROR`, `FATAL`), a location, and actionable remedies.

Exit codes are governed strictly by `aquilia.cli.core.exits.exit_code_for()`:
- `ExitCode.OK` (`0`) — All checks pass or emit only `INFO`/`WARN` findings.
- `ExitCode.FAILED` (`1`) — At least one `ERROR` or `FATAL` finding was discovered.
- `ExitCode.USAGE` (`2`) — Argument/invocation error.
- `ExitCode.CONFIG` (`3`) — Workspace or configuration file could not be loaded.
- `ExitCode.INTERNAL` (`4`) — Unhandled internal CLI exception.

### 2. `AqContext` & Python-First Workspace Loading

Ad-hoc `ctx.obj` dictionary manipulation is replaced by `AqContext`. Workspace discovery is lazy: non-workspace commands like `aq init`, `aq version`, and `aq --help` execute instantaneously without incurring workspace import overhead.

When loaded, `workspace.py` is executed as Python code rather than parsed with regular expressions. Declared starter controllers (`.starter("name")`) and module-level `route_prefix` definitions are accurately parsed into `LoadedWorkspace`. Regex parsing remains solely as an automatic fallback when user code contains import errors.

### 3. Subsystem Coverage Expansion

Thirteen framework subsystems (~45,000 lines of code) had zero CLI health monitoring in previous releases. `aquilia.cli.checks.subsystems` introduces config-driven probes for:
`tasks`, `templates`, `storage`, `cache`, `mail`, `i18n`, `otel`, `sse`, `versioning`, `http`, `auth`, `sockets`, `contracts`, `mlops`, and `admin`.

Probes are strictly config-driven and remain silent for unused subsystems, avoiding noise in minimal applications.

### 4. Native Router Memory Leak Resolution

During server shutdown, ASGI lifespan termination, or test teardown, native C++ `Router` instances wrapping nanobind bindings could remain referenced in memory, producing nanobind leak warnings on process termination.

v1.4.0b3 adds `ControllerRouter.clear()` and updates `AquiliaServer.shutdown()` and `ASGIAdapter.shutdown()` to explicitly reset C++ router references and internal route tables, eliminating leak warnings.

---

## Summary of Subsystem Changes

| Subsystem / Module | Status | Summary |
|---|---|---|
| `aquilia.cli.core.exits` | **New** | `ExitCode` enum, `SEVERITY_ORDER`, `exit_code_for()` single source of truth |
| `aquilia.cli.core.faults` | **New** | `CliFault` hierarchy (`WorkspaceNotFoundFault`, `WorkspaceLoadFault`, etc.) |
| `aquilia.cli.core.context` | **New** | `AqContext` lazy state thread replacing `ctx.obj` dictionary access |
| `aquilia.cli.core.workspace` | **New** | `LoadedWorkspace`, `load_workspace()`, `ensure_importable()` |
| `aquilia.cli.core.registry` | **New** | `CommandSpec`, `CATEGORY_ORDER`, category-driven help grouping |
| `aquilia.cli.checks.base` | **New** | `Finding`, `Check`, `CheckResult`, `@register_check()`, `run_checks()` |
| `aquilia.cli.checks.report` | **New** | `render_human()`, `render_json()`, `summarise()`, `result_exit_code()` |
| `aquilia.cli.checks.subsystems`| **New** | Config-driven probes for 13 framework subsystems |
| `aquilia.cli.checks.workspace` | **New** | Core health checks (Python version, modules, manifests, routes, DI, DB) |
| `aquilia.cli.introspect.routes`| **New** | Route introspection via `ControllerCompiler` (replaces legacy attribute probes) |
| `aquilia.cli.discovery_cli` | **Removed** | Legacy discovery CLI helper deleted |
| `aquilia.cli.parsers` | **Removed** | Legacy manifest regex parsers (`module.py`, `workspace.py`) deleted |
| `aquilia.controller.router` | **Improved** | `ControllerRouter.clear()` releases C++ nanobind `_native` instance |
| `aquilia.server` | **Improved** | `AquiliaServer.shutdown()` invokes `controller_router.clear()` |
| `aquilia.asgi` | **Improved** | `ASGIAdapter.shutdown()` releases server runtime, container & middleware chain |
| `aqdocx` | **Fixed** | Fixed TS2657 JSX single-parent return error in `MiddlewareOverview.tsx` |

---

## Performance Improvements

1. **Lazy CLI Execution**: Commands that do not require workspace inspection (`aq init`, `aq version`, `aq --help`, `aq mcp`) run in `<15ms` by avoiding workspace file discovery and import overhead.
2. **Cached Manifest Resolution**: `LoadedWorkspace.manifest()` caches `AppManifest` references during multi-check runs, eliminating redundant disk reads.
3. **Native Router Deallocation**: Timely release of native C++ CPython extension structures reduces memory overhead during unit testing and server restarts.

---

## Developer Experience Improvements

- **Actionable CLI Diagnostics**: Every health finding displays a stable error code (e.g. `[AQ_DB_MISSING]`), source location (`at: db.sqlite3`), and a concrete fix (`fix: Run migrations to create the DB`).
- **Machine-Readable Output**: `aq doctor --json` and `aq validate --json` emit standardized JSON payloads structured for CI/CD test runners.
- **Accurate Route Tree**: `aq inspect routes` compiles routes using `ControllerCompiler`, displaying exact paths served (including module prefixes and starter routes).

---

## Upgrade Checklist

- [ ] Update `aquilia` to `1.4.0b3` in `pyproject.toml` / `requirements.txt`.
- [ ] Update CI/CD pipelines to expect non-zero exit codes (code `1` or `3`) when `aq validate` or `aq doctor` encounters errors.
- [ ] Remove any internal references to deprecated `aquilia.cli.parsers` modules.
- [ ] Run `aq doctor` to perform a full workspace health check under the new engine.

---

## Credits

Special thanks to the Aquilia core team and community contributors for auditing CLI failure modes and implementing native C++ lifetime bounds.
