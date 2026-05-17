# Runtime Lifecycle

This page traces the concrete boot path implemented by `aquilia/runtime.py`, `aquilia/server.py`, and `aquilia/asgi.py`. It complements the generated module API pages by describing the order in which the runtime wires the framework together.

## AquiliaRuntime Phases

`AquiliaRuntime` moves through `CREATED`, `CONFIGURING`, `DISCOVERING`, `BOOTSTRAPPING`, `READY`, `RUNNING`, `SHUTTING_DOWN`, `STOPPED`, and `FAILED`.

- `configure()` inserts the workspace root into `sys.path`, sets environment defaults, configures logging, verifies `workspace.py`, and loads config.
- `discover()` parses workspace content, imports declared manifests, dynamically discovers module directories with `manifest.py`, rebuilds app config namespaces, and loads workspace module metadata.
- `bootstrap()` builds `AquiliaServer` with the correct `RegistryMode`.
- `.app` and `.server` are only available in `READY` or `RUNNING` phases.

## Configuration Phase

`AquiliaRuntime.configure()` is the first phase that touches the user workspace. The runtime resolves the workspace root, adds it to `sys.path` when needed, sets `AQUILIA_WORKSPACE`, sets an environment mode through `AQUILIA_ENV`, configures logging, requires `workspace.py`, and loads configuration through `ConfigLoader`. A missing workspace file fails during this phase instead of allowing later server construction to proceed with partial state.

`ConfigLoader.load()` merges workspace structure, optional legacy config, explicit dotenv input, native dotenv loading, `AQ_` environment overlays, and explicit overrides. The runtime keeps the loaded config and workspace metadata for later discovery and server construction.

## Discovery Phase

`AquiliaRuntime.discover()` imports the workspace, extracts declared modules, imports each declared `modules/<name>/manifest.py`, and discovers module directories that expose a manifest. It also rebuilds namespace configuration for discovered apps and captures workspace module metadata used by `AquiliaServer`.

Discovery is intentionally source-driven: manifests contain dotted references to controllers, services, models, socket controllers, tasks, middleware, templates, and fault handlers. Invalid dotted paths are reported by validation and startup paths rather than silently ignored.

## Server Startup

`AquiliaServer.startup()` is idempotent and guarded by an async lock. It performs runtime auto-discovery, loads controllers, wires admin routes, compiles routes, runs lifecycle hooks, registers models, validates model registry completeness, starts mail/tasks/cache/storage/effects where configured, and registers health statuses.

Startup also builds or initializes the subsystems used by request execution:

| Area | Runtime behavior |
| --- | --- |
| Registry | Builds the Aquilary registry/runtime registry from manifests and workspace module metadata. |
| Dependency injection | Creates app containers, registers services/providers, and creates request-scoped containers per request. |
| Routing | Loads controller classes, compiles decorators into routes, registers admin/docs routes where enabled, and stores route metadata for inspection. |
| Middleware | Registers built-in fault and request-scope middleware, then adds configured security, sessions, auth, templates, i18n, cache, static, rate-limit, and custom middleware. |
| WebSockets | Initializes socket controller runtime and adapter when socket controllers are declared. |
| Models and database | Registers model classes, validates registry completeness, and connects configured databases where required. |
| Background services | Starts mail, cache, storage, task, effect, and health integrations where configured. |

## Request Lifecycle

`ASGIAdapter.handle_http()` builds/caches middleware, handles `/_health`, wraps ASGI in `Request`, pre-resolves versioning, matches a route, allocates request DI scope and `RequestCtx`, executes middleware, calls the controller engine, records metrics, releases the context, and sends the response.

Detailed HTTP flow:

1. `ASGIAdapter.__call__()` dispatches by scope type: `http`, `websocket`, or `lifespan`.
2. `handle_http()` serves `GET /_health` and `HEAD /_health` before normal routing.
3. `Request` wraps the ASGI scope and receive callable.
4. The adapter asks the router for a compiled route; `HEAD` can fall back to `GET`.
5. A request container and pooled `RequestCtx` are allocated.
6. Middleware descriptors execute in configured order.
7. The final handler calls `ControllerEngine.execute()`.
8. Fault handling converts structured faults and unexpected exceptions into framework responses.
9. The response is emitted with `Response.send_asgi()`.
10. Metrics are recorded and request scope resources are released.

## WebSocket Lifecycle

`ASGIAdapter.handle_websocket()` delegates WebSocket scopes to the server socket runtime. Socket controllers are declared through module manifests and decorators from `aquilia.sockets`; the socket runtime owns connection state, room membership, event dispatch, guards, middleware, and adapter integration.

## Lifespan Lifecycle

`ASGIAdapter.handle_lifespan()` receives ASGI startup and shutdown messages. Startup enters `AquiliaServer.startup()`. Shutdown enters `AquiliaServer.shutdown()`. Lifespan failures are sent back through ASGI lifespan error messages so the process manager can fail visibly.

## Shutdown

`AquiliaServer.shutdown()` runs lifecycle shutdown, mail shutdown, task stop, cache shutdown, storage shutdown, DI container shutdown, effect finalization, socket shutdown, database disconnect, and resets startup state. `graceful_shutdown()` first stops accepting new work and drains in-flight requests up to a timeout.

## Operational Checks

- `aq validate` checks workspace manifests and dotted component paths.
- `aq inspect routes` prints compiled route metadata.
- `aq inspect modules` prints discovered modules.
- `aq inspect config` prints resolved configuration.
- `aq doctor` runs broader environment, workspace, registry, integration, and deployment diagnostics.
