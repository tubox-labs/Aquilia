# Diagnostics & Profiling — v1.4.0b0

`aquilia/devplatform/core/protocol.py`, `aquilia/devplatform/diagnostics/`,
`aquilia/devplatform/profiler/`, `aquilia/devplatform/core/runtime.py`.

## CPU Profiling — Newly Wired

`aquilia.devplatform.profiler.engine.cProfilingRunner` existed before this
release but was never invoked from the request path — the only thing that
called it, `ProfilingMiddleware`, was itself dead code (see below). It is
now wired directly into `ASGIHTTPConnection.execute()`
(`core/protocol.py`):

```python
async def execute(self, app: Any) -> None:
    profiler = self._make_profiler_if_requested()
    try:
        if profiler is not None:
            profiler.start()
        await app(self.scope, self.receive, self._instrumented_send)
    ...
    finally:
        ...
        if profiler is not None:
            self._record.profile_stats = profiler.stop()
        self._runtime.record_request(self._record)

def _make_profiler_if_requested(self) -> Any:
    if not self._config.profiler_enabled:
        request_headers = self._record.request_headers
        if request_headers.get("x-aquilia-profile", "").lower() not in ("true", "1", "yes"):
            return None
    try:
        from aquilia.devplatform.profiler.engine import cProfilingRunner
        return cProfilingRunner()
    except Exception:
        return None
```

Two activation paths, verified against real requests:

```bash
# Global — every request profiled (config: profiler_enabled=True / adp_profiler=True)
curl http://127.0.0.1:8000/users

# Per-request — only this request profiled
curl -H "X-Aquilia-Profile: true" http://127.0.0.1:8000/users
```

`cProfilingRunner.stop()` returns the top-50 cumulative-time entries as
formatted text via `pstats.Stats(...).print_stats(50)`, stored on
`RequestRecord.profile_stats`.

`ProfilingMiddleware` (the old, framework-level middleware class in
`profiler/engine.py`) was removed in this release — it had zero references
anywhere in the codebase and didn't inherit `aquilia.middleware.Middleware`,
so `MiddlewareStack.add()` would have raised `TypeError` had anyone tried to
register it.

## Memory Tracking — Active

`aquilia.devplatform.diagnostics.memory.MemoryUsageTracker`. Started by
`ASGILifespanManager._start_telemetry()` when `config.inspector_enabled` is
true. Runs `tracemalloc.start(10)`, takes periodic snapshots on a background
daemon thread (`_snapshot_interval_s`, default 30s / `AQ_DEV_MEMORY_SNAPSHOT_INTERVAL_S`),
and warns via `logger.warning` when RSS has grown monotonically across
`leak_growth_threshold` (default 3) consecutive snapshots. Snapshot history
capped at 60 entries (~30 minutes at the default interval).

## Event Loop Monitoring — Active

`aquilia.devplatform.diagnostics.eventloop.EventLoopMonitor`. Started
unconditionally by `_start_telemetry()`. Lowers `loop.slow_callback_duration`
to 10ms and wraps the loop's exception handler to capture asyncio's own
"Executing ... took Xs" slow-callback warnings into `SlowCallbackRecord`
entries (last 200 kept).

## SQL Diagnostics

`aquilia.devplatform.diagnostics.sql.SQLQueryAnalyzer` implements SQL
normalization (`normalize_sql()` — strips literals, collapses whitespace),
N+1 detection (grouping by normalized-SQL hash), duplicate-query detection
(grouping by hash + exact params), and an async `EXPLAIN` worker queue for
slow queries.

**Wiring (as of 1.4.0b0).** `ASGIHTTPConnection.execute()` in
`core/protocol.py` calls `_analyze_sql()` after each request completes: it
reads the request's own completed `Lane.DATABASE` spans off
`aquilia.inspector.trace.current_trace()` — spans populated by
`aquilia.db.engine.AquiliaDatabase._notify_inspector()` — and feeds each into
a per-request `RequestSQLAccumulator` plus `SQLQueryAnalyzer.get_instance()`.
The resulting N+1/duplicate warnings land on
`RequestRecord.n_plus_one_warnings`. Crucially the dependency direction is
one-way: `aquilia.db` never imports `aquilia.devplatform` — devplatform
*observes* core through the trace, so the dev-only package stays optional.
Gated by `AquiliaDevelopmentConfig.n_plus_one_detection`;
`sql_explain_threshold_ms` controls the slow-query EXPLAIN queue.

## WebSocket Tracking

`aquilia.devplatform.core.websocket.WebSocketTracker` is a thread-safe
registry (connection metadata, frame counts, disconnect reasons). As of
1.4.0b0 it is wired into `core/websocket_transport.serve_websocket()`, which
`register()`s a `WebSocketEntry` on connect, records inbound/outbound frame
counts, and `unregister()`s with the disconnect code on close. The
aggregate open/close counters on `RuntimeStateStore` (fed by
`ASGIWebSocketConnection` in `core/protocol.py`) continue to run alongside it.

## Flamegraph / Call-Tree Formatters

`aquilia.devplatform.profiler.flamegraph` (Speedscope-compatible JSON) and
`aquilia.devplatform.profiler.call_tree` (`rich.Tree`-based terminal
formatter, degrading to plain text without `rich`) both operate on
`cProfilingRunner`'s pstats text output. As of 1.4.0b0 they're served
through Inspector at
`GET /__aquilia__/inspector/devplatform/profile/{request_id}/?format=flamegraph|tree`
(`AdminController.inspector_profile_api`, `ImportError`-guarded so the route
404s cleanly when devplatform isn't installed). The handler pulls the
`RequestRecord` from `RuntimeStateStore.get_instance()` and renders its
`profile_stats`; profile capture itself is enabled via `adp_profiler` or the
`X-Aquilia-Profile: true` request header.

## `RuntimeStateStore`

`aquilia/devplatform/core/runtime.py` — thread-safe singleton holding live
metrics (`active_connections`, `active_websockets`, `total_requests`,
`total_errors`, RPS over a rolling 1-second window, latency EMA with
α=0.1) and a bounded circular buffer of the last `max_request_history`
`RequestRecord`s. `record_request()` updates counters under `self._lock`,
then notifies registered listeners (`add_request_listener`) **outside** the
lock to avoid deadlocks if a listener re-enters the store.

## Plugin Hooks

`AquiliaDevelopmentPlatform` (`platform.py`) is the facade passed to every
plugin's `initialize()`. Plugins implement the `AquiliaDevelopmentPlugin`
protocol (`plugins/protocol.py`) and are discovered via `importlib.metadata`
entry points under the `aquilia_dev.plugins` group:

```toml
# a third-party package's pyproject.toml
[project.entry-points."aquilia_dev.plugins"]
my_plugin = "my_package.plugin:MyPlugin"
```

Available hooks: `on_request_start(hook)`, `on_request_end(hook)` (also
registered with `RuntimeStateStore` so it fires on every committed
`RequestRecord`), `on_exception(hook)`. All hook invocations are wrapped in
`try/except` — a broken plugin hook is logged at debug level and does not
affect the request path.
