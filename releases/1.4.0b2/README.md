# Aquilia v1.4.0b2 Release Notes — "Foredeck Watch"

Aquilia v1.4.0b2 continues the "Foredeck Watch" beta cycle, building on the native engine foundation of v1.4.0b1 with three major subsystem improvements: a complete middleware package restructure, a full WebSocket middleware subsystem, and a new `AquilaConfig.Accelerator` configuration layer for native C++ engine control. This release also resolves five critical middleware bugs that caused rate limiting to be non-functional and import-order-dependent crashes.

## Table of Contents

1. [Middleware Package Restructure](middleware_restructure.md)
   * The monolithic `aquilia/middleware.py` split into a modular package.
   * New subpackages: `core/`, `stack/`, `builtin/`, `instrumentation/`, `utils/`.
   * `middleware_ext/` removal and migration paths.
   * New `Middleware` base class with `before`/`after`/`handle`/`should_run`/`setup`/`teardown` hooks.
   * Priority constants consolidated in `aquilia.middleware.core.priority.Priority`.
2. [WebSocket Middleware Subsystem](websocket_middleware.md)
   * Full WebSocket middleware pipeline at `aquilia/sockets/middleware/`.
   * `SocketMiddleware` base class with three lifecycle hooks.
   * Seven built-in socket middleware classes.
   * `SocketMiddlewareChain` fluent builder with preset configurations.
   * Workspace-level socket middleware configuration.
3. [Accelerator Configuration](accelerator.md)
   * `AquilaConfig.Accelerator` inner class for controlling native C++ engines.
   * New `aq run --engine/--no-engine` and `--dataengine/--no-dataengine` CLI flags.
   * Priority chain: CLI > env var > workspace.py > framework default.
4. [Bug Fixes](bug_fixes.md)
   * Rate limiting returning 500 instead of 429 (critical).
   * Per-user rate limiting silent no-op (identity ordering).
   * Middleware circular import crash on isolated imports.
   * Duplicate middleware priority silent reordering.
   * WebSocket parameterized route matching failure.
   * WebSocket close code 1003 to 1008 for policy rejections.
5. [Migration Guide](migration.md)
   * Breaking: `middleware_ext/` removed (but top-level `aquilia.middleware` still works).
   * Breaking: `build_fast_handler()` removed from `MiddlewareStack`.
   * Deprecated: `SocketGuard.check_message`.
   * Import path updates for security middleware.

---

## Key Goals

1. **Fix Critical Middleware Bugs.**
   Rate limiting was non-functional — every rate-limited request returned 500 instead of 429 due to a `TYPE_CHECKING`-only `Response` import. Per-user rate limiting was a silent no-op because `RateLimitMiddleware` ran before `AquilAuthMiddleware`, so `user_key_extractor` always returned `None`. Both are fixed, and regression tests covering the rejection path are now part of the suite.

2. **Restructure Middleware into a Coherent Package.**
   The `aquilia/middleware.py` monolith (647 lines) is replaced by a structured package that enforces the dependency boundaries that prevented isolated imports from working at all. The circular import between `aquilia.middleware` and `aquilia.faults` that crashed any script importing `Middleware` first is eliminated by moving the base class to a fault-free leaf module.

3. **Full WebSocket Middleware Parity.**
   WebSocket connections previously had no middleware layer — guards on individual messages were the only option, and `SocketGuard.check_message` was never called by the runtime. v1.4.0b2 introduces a complete three-hook middleware pipeline (connect/message/disconnect) with the same ergonomics as the HTTP stack, seven built-in classes, and workspace-level configuration.

4. **Declarative Native Engine Control.**
   The `AquilaConfig.Accelerator` inner class and `aq run --no-engine`/`--no-dataengine` flags give teams fine-grained, layered control over the C++ acceleration introduced in v1.4.0b1. The fail-soft behavior is unchanged; this adds explicit opt-out for CI parity gates and debugging workflows.

---

## Highlights by Feature Area

### Middleware Package

- **`aquilia/middleware/core/`**: Fault-free leaf zone containing the `Middleware` base class (`base.py`), descriptor system (`descriptor.py`), priority constants (`priority.py`), and transport types (`types.py`). Nothing in this layer imports `aquilia.faults`.
- **`aquilia/middleware/stack/`**: Registration (`registry.py`), chain compilation (`builder.py`), fault types (`errors.py`), hook validation (`validation.py`). `MiddlewarePriorityCollisionFault` is a new fault type.
- **`aquilia/middleware/builtin/`**: Framework-owned middleware. Security subpackage (`builtin/security/`) containing `CORSMiddleware`, `CSPMiddleware`, `CSRFMiddleware`, `SecurityHeadersMiddleware`, `HSTSMiddleware`, `HTTPSRedirectMiddleware`, `ProxyFixMiddleware`. Direct middleware: `CompressionMiddleware`, `ExceptionMiddleware`, `LoggingMiddleware`, `RateLimitMiddleware`, `RequestIdMiddleware`, `RequestScopeMiddleware`, `SessionMiddleware`, `StaticMiddleware`, `TimeoutMiddleware`.
- **`aquilia/middleware/instrumentation/`**: `Instrument` protocol, `TracingInstrument`, `MetricsInstrument`.
- **`aquilia/middleware/utils/`**: Transport-agnostic helpers shared with the socket stack. `ordering.py` (scope/priority sort), `throttling.py` (rate limit algorithms), `negotiation.py`, `status.py`.

### WebSocket Middleware

- **`SocketMiddleware`**: Three-hook base class. Override only the hooks needed — the stack omits a middleware from chains whose hooks are not implemented, so an `on_message`-only middleware costs nothing at connect time.
- **`SocketMiddlewareStack`**: Mirrors HTTP `MiddlewareStack` ergonomics. One registration feeds three chains (connect, message, disconnect). Same collision detection.
- **`SocketMiddlewareChain`**: Fluent builder with three presets (`minimal()`, `defaults()`, `production()`). Scope system: `global` < `namespace:<path>` < `event:<name>`.
- **Seven built-in classes**: `SocketFaultMiddleware`, `SocketLoggingMiddleware`, `SocketMetricsMiddleware`, `MessageValidationMiddleware`, `SocketRateLimitMiddleware`, `SocketAuthMiddleware`, `SocketPermissionMiddleware`.

### Accelerator Configuration

Priority order (highest wins):
1. CLI flag (`aq run --no-engine`)
2. Process environment (`AQUILIA_ENGINE=0`)
3. `workspace.py` `AquilaConfig.Accelerator`
4. Framework default (enabled)

Both engines remain fail-soft: absent native extensions degrade to pure Python automatically. These controls exist for teams that want explicit rather than implicit fallback.

---

## Breaking Changes Summary

| Change | Scope | Migration |
|--------|-------|-----------|
| `middleware_ext/` removed | Breaking | Update import paths; `aquilia.middleware` lazy re-exports all names |
| `build_fast_handler()` removed | Breaking | Use `build_handler()` — the fast lane was never called |
| Security middleware import paths changed | Breaking if importing from `aquilia.middleware_ext.security` | Use `aquilia.middleware.builtin.security.*` |
| `SocketGuard.check_message` deprecated | Non-breaking (warning) | Use `SocketMiddleware` instead |
| Inspector priorities changed 11/12 to 13/14 | Internal only | No user action required |
| Rate limit identity priority 12 to 16 | Behavioral | Intentional fix; per-user limits now enforced |

Please read the subsequent documents in this release for detailed technical breakdowns of each area.
