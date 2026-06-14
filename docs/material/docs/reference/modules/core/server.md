# AquiliaServer

> `aquilia.server` — Main server orchestrator

`AquiliaServer` is the central orchestrator that wires together all Aquilia subsystems. It consumes module manifests, builds the Aquilary registry, resolves the DI graph, compiles controllers into routes, constructs the middleware stack, and produces the final ASGI application.

## Boot Sequence

```
Manifests → Aquilary → RuntimeRegistry → Controllers → ASGI
```

1. **Manifest load** — Module manifests are collected from `workspace.py` and `modules/*/manifest.py`
2. **Aquilary registry** — Manifests are validated and the component graph is built
3. **RuntimeRegistry** — DI containers are resolved, services registered, routes compiled
4. **ControllerRouter** — Route table is built from controller decorators
5. **MiddlewareStack** — Middleware chain is constructed with deterministic ordering
6. **ASGIAdapter** — The final ASGI callable is exported

## Key Responsibilities

| Responsibility | Mechanism |
|---|---|
| Manifest collection | Reads workspace config, discovers modules |
| Signing bootstrap | Configures HMAC keys for sessions, CSRF, cache |
| Health tracking | Maintains `HealthRegistry` for all subsystems |
| Fault handling | Configures `FaultEngine` with debug/recovery strategies |
| DI wiring | Resolves provider DAG, applies integration patches |
| Lifecycle management | Coordinates startup/shutdown hooks via `LifecycleCoordinator` |
| OpenAPI generation | Produces Swagger/Redoc documentation |
| WebSocket setup | Initializes `SocketRouter` and adapter |
| Template integration | Registers template providers and middleware |

## Constructor

```python
AquiliaServer(
    manifests: ManifestCollection | None = None,
    config: ConfigLoader | None = None,
    mode: RegistryMode = RegistryMode.PROD,
    aquilary_registry: AquilaryRegistry | None = None,
    workspace_modules: dict[str, dict[str, Any]] | None = None,
)
```

| Parameter | Description |
|---|---|
| `manifests` | List of `AppManifest` instances for app discovery |
| `config` | Configuration loader (defaults to empty `ConfigLoader`) |
| `mode` | Registry mode: `DEV`, `PROD`, or `TEST` |
| `aquilary_registry` | Pre-built `AquilaryRegistry` for advanced usage |
| `workspace_modules` | Module configs from `workspace.py` (route_prefix, etc.) |

## Simple Example

```python
from aquilia import AquiliaServer, AppManifest

# Define manifests
manifests = [
    AppManifest(
        name="users",
        version="1.0.0",
        controllers=["modules.users.controllers:UsersController"],
    ),
]

# Create server
server = AquiliaServer(manifests=manifests, mode="dev")

# Access internals
print(server.health_registry)    # HealthRegistry instance
print(server.router)             # ControllerRouter instance
print(server.fault_engine)       # FaultEngine instance
```

## Production Usage

In production, `AquiliaServer` is created automatically by `AquiliaRuntime`:

```python
# aquilia/entrypoint.py
from aquilia.runtime import AquiliaRuntime

# This is what "uvicorn aquilia.entrypoint:app" resolves to
app = AquiliaRuntime.create_app()
```

The server instance is exposed as `aquilia.entrypoint.server`.

## Subsystem Integration

`AquiliaServer` coordinates these subsystems:

| Subsystem | Module | Role |
|---|---|---|
| Auth | `aquilia.auth` | Identity, tokens, guards |
| Cache | `aquilia.cache` | Cache backends, middleware |
| DB | `aquilia.db` | Database connections |
| Sessions | `aquilia.sessions` | Session engine, stores |
| Sockets | `aquilia.sockets` | WebSocket routing |
| Storage | `aquilia.storage` | File storage backends |
| Tasks | `aquilia.tasks` | Background job manager |
| Templates | `aquilia.templates` | Jinja2 rendering |

## Related

- [Runtime](runtime.md) — The structured lifecycle around `AquiliaServer`
- [Entrypoint](entrypoint.md) — Zero-config `create_app()` factory
- [ASGI](asgi.md) — How the ASGI adapter uses the compiled server
- [Middleware](middleware.md) — Middleware stack composition