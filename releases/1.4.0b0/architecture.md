# ADP Architecture — v1.4.0b0

All diagrams below trace actual call paths in `aquilia/devplatform/`, verified
against the source for this release. Class/function names match the code
exactly.

### 1. Component Interaction Diagram

```mermaid
graph TD
    Client[Client Socket] -->|ASGI HTTP/WS| Proto[protocol.py]

    Proto -->|Execute App| App[Aquilia Application]

    App -->|SQL Queries| SQLDiag[diagnostics/sql.py]
    App -->|DI Events| DIListener[di_listener.py]
    App -->|cProfile| Prof[profiler/engine.py]

    SQLDiag -->|Trace spans| Inspector[aquilia/inspector]
    DIListener -->|Trace spans| Inspector
    Prof -->|Flamegraph stats| Inspector

    Proto -->|Request Metrics| Inspector

    Watcher[watcher.py] -->|File events| Reload[reload/executor.py]
    Reload -->|Preserve Refs| Preserve[state_preservation.py]
    Preserve -->|Reload Modules| App

    Runtime[runtime.py] -->|Runtime Context| Inspector
    State[state.py] -->|Lifecycle State| Inspector
```

---


## Boot Sequence

`AquiliaDevelopmentServer.start()` (`aquilia/devplatform/devserver.py`):

```mermaid
sequenceDiagram
    participant CLI as aq run / aq dev
    participant Server as AquiliaDevelopmentServer
    participant Lifespan as ASGILifespanManager
    participant Protocol as ADPProtocolHandler
    participant Platform as AquiliaDevelopmentPlatform
    participant App as Aquilia app (workspace)

    CLI->>Server: start(app)
    Server->>Server: _configure_logging()
    Server->>Lifespan: wrap app -> lifespan_app
    Server->>Protocol: wrap lifespan_app -> self._wrapped_app
    Server->>Platform: load_plugins()
    Server->>Server: _run_lifespan_startup(app)
    Server->>Lifespan: send lifespan.startup
    Lifespan->>App: forward lifespan.startup
    App-->>Lifespan: lifespan.startup.complete
    Lifespan->>Lifespan: _adp_startup()
    Note over Lifespan: _start_telemetry()<br/>_register_core_listeners()<br/>_start_hot_reload()
    Lifespan-->>Server: lifespan.startup.complete
    Server->>Server: bind socket (uds / fd / host:port)
    Server->>Server: serve_forever()
```

`_adp_startup()` (`core/lifespan.py`) boots, in order:

1. `_start_telemetry()` — starts `MemoryUsageTracker` (if `inspector_enabled`) and `EventLoopMonitor` unconditionally.
2. `_register_core_listeners()` — attaches `InspectorDiagnosticListener` to any DI containers reachable via `app.server.runtime.di_containers`.
3. `_start_hot_reload()` — spawns `WorkspaceWatcher.watch()` as a background task, if `config.reload` is true.

## HTTP Request Flow

Socket accept → `H11Connection` (native h11 transport) → `ADPProtocolHandler` → `ASGIHTTPConnection` → the Aquilia app.

```mermaid
sequenceDiagram
    participant Sock as asyncio.start_server
    participant H11 as H11Connection (h11_transport.py)
    participant Wrapped as self._wrapped_app
    participant PH as ADPProtocolHandler (protocol.py)
    participant HC as ASGIHTTPConnection
    participant App as Aquilia app

    Sock->>H11: _accept_connection(reader, writer)
    H11->>H11: run() -> _read_request() via h11.Connection
    alt Upgrade: websocket
        H11->>H11: ws_upgrade_hook(self, request)
        Note over H11: hands off to serve_websocket()<br/>(see WebSocket flow)
    else HTTP request
        H11->>H11: _dispatch(request) -> build ASGI scope
        H11->>Wrapped: await app(scope, receive, send)
        Wrapped->>PH: __call__(scope, receive, send)
        PH->>HC: ASGIHTTPConnection(scope, receive, send, config, runtime)
        HC->>HC: _make_profiler_if_requested()
        Note over HC: profiler_enabled config OR<br/>X-Aquilia-Profile header
        HC->>App: execute(app) -> app(scope, receive, _instrumented_send)
        App-->>HC: http.response.start / http.response.body
        HC->>HC: commit RequestRecord to RuntimeStateStore
        HC-->>H11: response sent via h11.Connection.send()
    end
    H11->>H11: keep-alive? start_next_cycle() : close
```

Notes verified against `h11_transport.py`:
- `H11Connection` keeps one `h11.Connection(h11.SERVER)` per TCP connection — keep-alive and pipelining are handled by h11's own state machine (`start_next_cycle()`), not re-implemented.
- On an unhandled exception from the app with no response yet started, `H11Connection._dispatch()` sends a `500` and does **not** re-raise. If the app raised after already sending `http.response.start`, the exception propagates and the connection is closed (no safe partial response to send).
- `App` above is whatever `ASGILifespanManager` wraps — for `http`/`websocket` scope types `ASGILifespanManager.__call__` passes through directly to the real Aquilia app unchanged; only `lifespan` scope is intercepted.

## WebSocket Upgrade Flow

`aquilia/devplatform/core/websocket_transport.py`. Handshake happens directly
against the raw socket (h11 is HTTP/1.1 only — it hands off once the Upgrade
request is parsed).

```mermaid
sequenceDiagram
    participant H11 as H11Connection
    participant WS as serve_websocket()
    participant Conn as _WebSocketConnection
    participant PH as ADPProtocolHandler
    participant WC as ASGIWebSocketConnection
    participant App as Aquilia app

    H11->>H11: detect Connection: Upgrade, Upgrade: websocket
    H11->>WS: ws_upgrade_hook(self, request)
    WS->>Conn: accept() -> RFC 6455 101 handshake<br/>(Sec-WebSocket-Accept = base64(sha1(key + GUID)))
    WS->>App: app(scope["type"]="websocket", receive, send)
    App->>PH: __call__ -> dispatch scope_type == "websocket"
    PH->>WC: ASGIWebSocketConnection(scope, receive, send, runtime).execute(app)
    loop until close or disconnect
        WS->>Conn: read_frame() -> (opcode, payload)
        alt text/binary
            WS->>App: websocket.receive {text|bytes}
            App-->>WS: websocket.send (via ASGI send)
            WS->>Conn: send_text() / send_bytes()
        else close
            WS->>Conn: close(code)
            WS->>App: websocket.disconnect
        else ping
            WS->>Conn: send_pong(payload)
        end
    end
```

The ASGI app receives `websocket.connect` *before* it may call
`send({"type": "websocket.accept"})` — `receive()` in `serve_websocket()` is a
plain `asyncio.Queue.get()` with no gating on acceptance, which is required by
the ASGI spec's connect-then-accept ordering.

## Hot Reload Flow

`aquilia/devplatform/reload/`.

```mermaid
sequenceDiagram
    participant FS as watchfiles.awatch
    participant Watcher as WorkspaceWatcher
    participant Analyzer as DependencyGraphAnalyzer
    participant Discovery as AutoDiscoveryEngine
    participant Executor as ModuleReloadExecutor
    participant Bridge as StateBridgeRegistry
    participant Server as AquiliaServer (wrapped app)

    FS-->>Watcher: batched file change events (50ms debounce)
    Watcher->>Watcher: _filter_paths() (excludes, __pycache__, .pyc)
    Watcher->>Analyzer: compute_strategy(changed_paths)
    Analyzer->>Analyzer: _path_to_module_name() + _classify_tier() per path
    alt any CORE tier module changed
        Analyzer-->>Watcher: ReloadPlan(strategy=FULL)
    else FRAMEWORK/APP/LEAF tier
        Analyzer->>Analyzer: _get_reverse_deps() (AST-based, exact match)
        Analyzer->>Discovery: discover(module_name) for modules/ paths
        Discovery-->>Analyzer: ClassifiedComponent list (component kind diff)
        Analyzer-->>Watcher: ReloadPlan(strategy=PARTIAL|HOT_PATCH, discovery_summary=...)
    end
    Watcher->>Executor: ModuleReloadExecutor(plan, runtime, shutdown_timeout).execute()
    alt FULL
        Executor->>Server: graceful_shutdown(timeout) [bounded wait_for]
        Executor->>Executor: os.execv(sys.executable, ...)
    else PARTIAL
        Executor->>Bridge: snapshot() long-lived resources
        Executor->>Executor: importlib.reload() each affected module
        Executor->>Bridge: restore() -> rebind DB pool / session store / cache backend
        Executor->>Server: _rebind_aquilia_runtime() -> recompile routes
    else HOT_PATCH
        Executor->>Executor: swap __code__ on matching functions
        Note over Executor: falls back to PARTIAL on any failure
    end
```

`_classify_tier()` maps path fragments to `StabilityTier`:

| Tier | Path fragments | Strategy |
|---|---|---|
| `CORE` (1) | `aquilary`, `/di/`, `patterns` | `FULL` |
| `FRAMEWORK` (2) | `/db/`, `routing`, `middleware` | `PARTIAL` |
| `APP` (3, default) | `controller`, `models`, `auth`, `sessions` | `PARTIAL` |
| `LEAF` (4) | `debug`, `testing`, `devplatform` | `HOT_PATCH` |

If a changed file isn't resolvable to a loaded module (`_path_to_module_name()`
returns `None`, or it's not in `sys.modules`), the plan always defaults to
`FULL` — this covers new files and config changes the running process has no
way to hot-patch.

## Framework Integration Points

The ADP is a first-class Aquilia subsystem, wired into the same core
machinery every other subsystem uses rather than a parallel architecture.

**Faults.** `aquilia/devplatform/faults.py` defines `DEVPLATFORM_DOMAIN`
(`FaultDomain.DEVPLATFORM`, registered in `aquilia/faults/core.py`) and the
`DevPlatformFault` hierarchy: `StartupFault`, `ReloadFault`,
`InspectorFault`, `WorkerFault`, `ConfigurationFault`. Non-fatal failures
throughout the subsystem call `report_fault(fault, app=...)`, which forwards
to the wrapped app's `FaultEngine.process()` when reachable. Because
`aquilia/inspector/fault_bridge.py`'s listener is already registered on that
engine (`server.py`), DevPlatform faults surface in Inspector's
`Lane.EXCEPTION` automatically — no Inspector-side code. Fatal faults
(`StartupFault`, `ConfigurationFault`) propagate to the CLI boundary and exit
non-zero.

**Config.** `AquiliaDevelopmentConfig` resolves each field through
`aquilia.pyconfig.Env` and validates in `__post_init__` (raising
`ConfigurationFault`). `to_dict()` is the single serialization source of
truth, consumed by both `_build_adp_config()` and the codegen'd
`runtime/_adp_app.py` wrapper.

**Typing / datastructures.** Types live in `aquilia/typing/devplatform.py`
(re-exported from `aquilia.typing`). The six state stores share
`core/_base.SingletonMixin`; `core/_cache.BoundedCache` bounds the reload
import-graph memo; header redaction uses `aquilia._datastructures.Headers`.

**Inspector spans & profile serving.** SQL diagnostics read
`Lane.DATABASE` spans off the request trace (see [diagnostics.md](diagnostics.md));
a dedicated `Lane.DEVPLATFORM` carries reload/plugin events; captured
profiles are served at
`/__aquilia__/inspector/devplatform/profile/{request_id}/`.

```mermaid
flowchart LR
    ADP[devplatform subsystem] -->|report_fault| FE[FaultEngine.process]
    FE -->|fault_bridge listener| INS[Inspector Lane.EXCEPTION]
    ADP -->|Env resolve + validate| CFG[AquiliaDevelopmentConfig]
    ADP -->|Lane.DATABASE / DEVPLATFORM spans| TRACE[current_trace]
    TRACE --> INS
```
