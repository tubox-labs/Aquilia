# Aquilia v1.4.0b0 Release Notes — "Foredeck Watch"

Aquilia v1.4.0b0 rebuilds `aquilia.devplatform` — the Aquilia Native Development
Platform (ADP) — into a fully native ASGI development server. The previous
toy HTTP parser is replaced with a real h11-based HTTP/1.1 transport, a
dependency-free RFC 6455 WebSocket engine is added, the browser dashboard and
Textual TUI are removed in favor of Aquilia's existing Inspector, hot-reload's
dependency detection moves from a broken object-identity scan to AST-based
static import analysis, and per-request CPU profiling is wired into the
request pipeline for the first time.

## Table of Contents

1. [Architecture](architecture.md)
   * Boot sequence: `AquiliaDevelopmentServer.start()` → lifespan → socket bind.
   * HTTP request flow through `H11Connection` → `ADPProtocolHandler` → `ASGIHTTPConnection` → the Aquilia app.
   * WebSocket upgrade flow.
   * Hot-reload flow: watcher → analyzer → executor.
2. [Transport Layer](transport.md)
   * `H11Connection` — the native h11-based HTTP/1.1 transport.
   * `serve_websocket` — the native RFC 6455 WebSocket engine.
   * `AquiliaDevelopmentConfig` network fields (`http`, `ws`, `uds`, `fd`).
   * CLI flags and config precedence.
3. [Hot Reload](reload.md)
   * `DependencyGraphAnalyzer` — AST-based reverse dependency detection, and the false-positive bug that was fixed.
   * `AutoDiscoveryEngine` integration for workspace-module diffing.
   * `StabilityTier` classification and `ModuleReloadExecutor` strategies (FULL / PARTIAL / HOT_PATCH).
   * The graceful-shutdown-before-`execv` fix.
4. [Diagnostics & Profiling](diagnostics.md)
   * `cProfilingRunner` wiring into `ASGIHTTPConnection.execute()`.
   * `MemoryUsageTracker`, `EventLoopMonitor` — what's actually running.
   * `SQLQueryAnalyzer`, `WebSocketTracker`, flamegraph/call-tree formatters — what's built but not yet wired.
   * `RuntimeStateStore` and the plugin hook surface.
5. [Migration Guide](migration.md)
   * Dashboard/TUI removal — what to do if you depended on it.
   * `textual` dependency drop.
   * New `aq dev` / `aq inspector` commands.
   * `--http`/`--ws`/`--uds`/`--fd` flags and config precedence.

---

## Key Goals

1. **Native transport, not a uvicorn wrapper.** ADP's own `AquiliaDevelopmentServer.start()` path — previously a barely-functional fallback used only when uvicorn wasn't installed — is now the default, backed by a real HTTP/1.1 state machine (`h11`) instead of a single-shot line parser with no keep-alive support.
2. **One debugging surface.** The ADP dashboard and Textual TUI duplicated what Aquilia's Inspector already does. They're removed; Inspector (`/__aquilia__/inspector`) is now the only debugging surface ADP ships.
3. **Correct hot-reload dependency tracking.** The previous reverse-dependency scan compared `__dict__` values by identity — it didn't work. The AST-based rewrite parses real import statements, and in the process a serious false-positive bug was found and fixed (see [reload.md](reload.md)).
4. **No unjustified new dependencies.** The WebSocket engine is implemented directly against `hashlib`/`base64`/`struct` rather than pulling in `websockets` or `wsproto` for the default path.
5. **Framework-native integration.** DevPlatform is a first-class Aquilia subsystem, not a parallel architecture: it raises structured `DevPlatformFault` subclasses on the `devplatform` fault domain (surfaced automatically through Inspector), loads config through `aquilia.pyconfig.Env`, reuses `aquilia.typing` aliases and a shared `SingletonMixin`, and emits `Lane.DEVPLATFORM` spans. It is also explicitly development-only — `aq run` forces uvicorn in production mode.
