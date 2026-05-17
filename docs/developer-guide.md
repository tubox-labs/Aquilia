# Developer Guide

This guide documents the implementation patterns visible in the source tree. For exhaustive symbol signatures, use each module's `api-reference.md`; this page focuses on how those pieces fit together when extending Aquilia.

## Build A Module

1. Add a module with `aq add module <name>`.
2. Put transport code in `modules/<name>/controllers.py`.
3. Put business logic in `modules/<name>/services.py`.
4. Declare controllers/services/models/socket controllers/tasks in `modules/<name>/manifest.py`.
5. Point the workspace at the module with `Module("name").route_prefix("/name")`.

The checked CRUD example uses this shape:

```python
from aquilia import Integration, Module, Workspace

workspace = (
    Workspace("project-tracker", version="1.0.0")
    .runtime(mode="dev", port=8010, reload=True)
    .database(url="sqlite:///runtime/projects.db", auto_create=True, auto_migrate=False)
    .module(Module("projects", version="1.0.0").route_prefix("/projects").tags("crud", "projects"))
    .integrate(Integration.di(auto_wire=True, manifest_validation=True))
    .integrate(Integration.routing(strict_matching=True))
    .integrate(Integration.fault_handling(default_strategy="propagate"))
    .security(cors_enabled=True, helmet_enabled=True)
)
```

Its module manifest declares concrete dotted references:

```python
from aquilia import AppManifest
from aquilia.manifest import FaultHandlingConfig

manifest = AppManifest(
    name="projects",
    version="1.0.0",
    controllers=["modules.projects.controllers:ProjectsController"],
    services=["modules.projects.services:ProjectsService"],
    models=["modules.projects.models:Project"],
    base_path="modules.projects",
    tags=["projects"],
    faults=FaultHandlingConfig(default_domain="PROJECTS", strategy="propagate"),
)
```

## Extend With Services

Declare services in `AppManifest.services`. The runtime registry registers services into app DI containers before controller factories are created. Constructor injection is preferred because `ControllerFactory` and DI providers can resolve annotated dependencies.

Service classes are ordinary Python objects. The runtime sees them through manifest paths and DI registration. Tests can instantiate them directly, as the checked examples do, when behavior does not require ASGI or container state.

## Add Controllers

Controllers extend `Controller` and use route decorators such as `GET`, `POST`, `PATCH`, and `DELETE`. Handler methods receive `RequestCtx`; they can read JSON with `await ctx.json()`, access query parameters through `ctx.query_param(...)`, and return `Response` instances.

```python
from aquilia import Controller, GET, POST, RequestCtx, Response

class ProjectsController(Controller):
    prefix = "/"

    @GET("/")
    async def list_projects(self, ctx: RequestCtx):
        return Response.json({"items": []})

    @POST("/", status_code=201)
    async def create_project(self, ctx: RequestCtx):
        payload = await ctx.json()
        return Response.json(payload, status=201)
```

## Add Blueprints

Blueprints are annotation-driven request/response contracts. The repository examples use `Blueprint` classes with typed attributes, `Spec` options, and `seal_<field>` methods that mutate or reject incoming data.

```python
from aquilia.blueprints import Blueprint

class ProjectCreateBlueprint(Blueprint):
    key: str
    name: str
    owner_email: str

    class Spec:
        extra_fields = "reject"

    def seal_key(self, data):
        data["key"] = data.get("key", "").strip().upper()
        if not data["key"]:
            self.reject("key", "Project key is required")
```

## Add Middleware

Use `Integration.middleware(...)` or manifest middleware declarations. Internal framework middleware is always registered: fault handling and request-scope cleanup. Security/static/rate-limit/session/auth/template/i18n/cache middleware are added by server setup when configured.

## Add CLI Commands

Mounted commands live in `aquilia/cli/__main__.py` and implementation helpers live under `aquilia/cli/commands/`. Subsystem-local CLI helpers exist in some modules, but only commands mounted in the root Click tree appear in `aq --help` and this documentation.

## Add Providers Or Backends

Follow existing backend/provider contracts: cache backends implement `CacheBackend`, storage backends extend `StorageBackend`, mail providers implement `IMailProvider`, socket scaling backends implement `Adapter`, database adapters extend `DatabaseAdapter`, and MLOps runtimes extend runtime base classes.

When adding a backend, keep the implementation behind the subsystem contract and wire it through the existing config or provider registry. Avoid calling optional third-party packages at import time unless that subsystem already requires them; several modules load optional dependencies only when a configured backend needs them.

## Add WebSocket Controllers

Socket controllers use decorators from `aquilia.sockets` and are declared in the module manifest. The checked WebSocket example shows room membership, event schemas, and ack events:

```python
from aquilia.sockets import Connection, Event, OnConnect, Schema, Socket, SocketController

@Socket("/ws/chat/:room", allowed_origins=["*"])
class ChatSocket(SocketController):
    namespace = "chat"

    @OnConnect()
    async def connected(self, conn: Connection):
        room = conn.scope.path_params.get("room", "lobby")
        await conn.join(room)

    @Event("message.send", schema=Schema({"room": str, "text": str}), ack=True)
    async def send_message(self, conn: Connection, payload: dict):
        await self.publish_room(payload["room"], "message.received", payload)
        return {"delivered": True}
```

## Add Background Tasks

The tasks subsystem exposes `@task` and schedule helpers. Tasks are declared by dotted path in the module manifest and are started by server startup when task integration is configured.

```python
from aquilia.tasks import Priority, every, task

@task(queue="mail", priority=Priority.HIGH, max_retries=5, retry_delay=2.0)
async def send_welcome_email(email: str, name: str) -> dict:
    return {"sent": True, "email": email, "name": name}

@task(queue="maintenance", schedule=every(minutes=30))
async def cleanup_old_jobs() -> dict:
    return {"cleaned": True}
```

## Testing

Use `aquilia.testing` for `TestClient`, `TestServer`, base test cases, config overrides, DI mocks, effect mocks, mail outbox helpers, and request factories. The CLI command `aq test` sets `AQUILIA_ENV=test` and delegates to pytest with Aquilia-aware defaults.

## Change Checklist

1. Update `workspace.py` when the workspace should know about a module or integration.
2. Update `modules/<name>/manifest.py` when runtime discovery should load a controller, service, model, socket controller, middleware, task, template, or fault handler.
3. Run `aq validate` after manifest edits.
4. Run `aq inspect routes`, `aq inspect modules`, or `aq inspect config` when debugging runtime wiring.
5. Add tests under `tests/` or the example app's test directory for behavior that can be exercised without a running server.
