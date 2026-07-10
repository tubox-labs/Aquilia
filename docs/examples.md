# Examples Index

The repository contains checked example applications under `examples/`:

| Example | Purpose |
| --- | --- |
| `examples/crud_app` | CRUD workspace with database, module manifest, controllers, contracts, models, and service tests. |
| `examples/rest_api_contract` | REST API using contracts for request/response contracts. |
| `examples/auth_app` | Auth-oriented app with account module and tests. |
| `examples/background_jobs` | Background task module and task service tests. |
| `examples/websocket_app` | WebSocket chat/presence module with socket controller tests. |
| `examples/multi_module_native_app` | Multi-module workspace using accounts, orders, notifications, operations, realtime, templates, and locales. |

## How To Run Examples

Each example is a workspace-shaped application with its own `workspace.py` and `runtime.py`. From an example directory, the source-backed operational flow is:

```bash
aq validate
aq inspect modules
aq inspect routes
aq run
```

Tests live under each example's `tests/` directory and can be run with `pytest` or through the framework command:

```bash
aq test
```

## Workspace Pattern

The CRUD example wires runtime, database, one module, DI, routing, fault handling, and security:

```python
from aquilia import Integration, Module, Workspace

workspace = (
    Workspace("project-tracker", version="1.0.0", description="CRUD starter application")
    .runtime(mode="dev", port=8010, reload=True)
    .database(url="sqlite:///runtime/projects.db", auto_create=True, auto_migrate=False)
    .module(Module("projects", version="1.0.0").route_prefix("/projects").tags("crud", "projects"))
    .integrate(Integration.di(auto_wire=True, manifest_validation=True))
    .integrate(Integration.routing(strict_matching=True))
    .integrate(Integration.fault_handling(default_strategy="propagate"))
    .security(cors_enabled=True, helmet_enabled=True)
)
```

The auth starter adds sessions and rate limiting:

```python
from aquilia import Integration, Module, Workspace
from aquilia.sessions import DEFAULT_USER_POLICY

workspace = (
    Workspace("auth-starter", version="1.0.0", description="Authentication starter application")
    .runtime(mode="dev", port=8020, reload=True)
    .module(Module("accounts", version="1.0.0").route_prefix("/accounts").tags("auth", "users"))
    .integrate(Integration.di(auto_wire=True, manifest_validation=True))
    .integrate(Integration.routing(strict_matching=True))
    .integrate(Integration.fault_handling(default_strategy="propagate"))
    .sessions(policies=[DEFAULT_USER_POLICY])
    .security(cors_enabled=True, csrf_protection=False, helmet_enabled=True, rate_limiting=True)
)
```

## Manifest Pattern

```python
from aquilia import AppManifest
from aquilia.manifest import FaultHandlingConfig

manifest = AppManifest(
    name="projects",
    version="1.0.0",
    description="Project CRUD module",
    controllers=["modules.projects.controllers:ProjectsController"],
    services=["modules.projects.services:ProjectsService"],
    models=["modules.projects.models:Project"],
    base_path="modules.projects",
    tags=["projects"],
    faults=FaultHandlingConfig(default_domain="PROJECTS", strategy="propagate"),
)
```

## HTTP Controller Pattern

The CRUD example controller uses route decorators, request JSON, query parameters, contract validation, and structured `Response` objects:

```python
from aquilia import Controller, DELETE, GET, PATCH, POST, RequestCtx, Response

from .contracts import ProjectCreateContract, ProjectUpdateContract
from .services import ProjectsService

class ProjectsController(Controller):
    prefix = "/"
    tags = ["projects"]

    def __init__(self, service: ProjectsService | None = None):
        self.service = service or ProjectsService()

    @GET("/")
    async def list_projects(self, ctx: RequestCtx):
        include_archived = (ctx.query_param("archived", "false") or "false").lower() == "true"
        return Response.json({"items": await self.service.list_projects(include_archived=include_archived)})

    @POST("/", status_code=201)
    async def create_project(self, ctx: RequestCtx):
        contract = ProjectCreateContract(data=await ctx.json())
        await contract.is_sealed_async()
        return Response.json(await self.service.create_project(contract.validated_data), status=201)
```

## Contract Validation Pattern

```python
from aquilia.contracts import Contract

class ProjectCreateContract(Contract):
    key: str
    name: str
    summary: str | None = None
    owner_email: str
    status: str = "planned"

    class Spec:
        extra_fields = "reject"

    def seal_key(self, data):
        key = data.get("key", "").strip().upper()
        if not key:
            self.reject("key", "Project key is required")
        data["key"] = key

    def seal_owner_email(self, data):
        email = data.get("owner_email", "")
        if "@" not in email:
            self.reject("owner_email", "Owner email must look like an email address")
```

## Service And Fault Pattern

The checked service layer raises framework faults that the fault middleware can map into responses:

```python
from aquilia.faults import ConflictFault, NotFoundFault

class ProjectRepository:
    async def get(self, key: str) -> dict:
        row = self._rows.get(key.upper())
        if row is None:
            raise NotFoundFault(detail=f"Project {key!r} was not found")
        return row.to_dict()

    async def create(self, data: dict) -> dict:
        key = data["key"].upper()
        if key in self._rows:
            raise ConflictFault(detail=f"Project {key!r} already exists")
        row = ProjectRecord(**data)
        self._rows[key] = row
        return row.to_dict()
```

## WebSocket Pattern

The WebSocket example uses socket decorators, room membership, payload schemas, and acknowledgement events:

```python
from aquilia.sockets import AckEvent, Connection, Event, OnConnect, Schema, Socket, SocketController

@Socket("/ws/chat/:room", allowed_origins=["*"], message_rate_limit=20, max_message_size=16384)
class ChatSocket(SocketController):
    namespace = "chat"

    @OnConnect()
    async def connected(self, conn: Connection):
        room = conn.scope.path_params.get("room", "lobby")
        await conn.join(room)
        await conn.send_event("system.welcome", {"room": room, "connection_id": conn.id})

    @Event("message.send", schema=Schema({"room": str, "text": str}), ack=True)
    async def send_message(self, conn: Connection, payload: dict):
        await self.publish_room(payload["room"], "message.received", {"from": conn.id, "text": payload["text"]})
        return {"delivered": True, "room": payload["room"]}

    @AckEvent("presence.snapshot")
    async def presence_snapshot(self, conn: Connection, payload: dict):
        return {}
```

## Background Task Pattern

The background jobs example uses `@task`, priority, retry, timeout, and schedule helpers:

```python
from aquilia.tasks import Priority, every, task

@task(queue="mail", priority=Priority.HIGH, max_retries=5, retry_delay=2.0, tags=["mail", "user"])
async def send_welcome_email(email: str, name: str) -> dict:
    return {"sent": True, "email": email, "name": name}

@task(queue="maintenance", schedule=every(minutes=30), tags=["maintenance"])
async def cleanup_old_jobs() -> dict:
    return {"cleaned": True}
```

Module-specific examples are in `docs/modules/<module>/examples.md`.
