# Your First Project

Build a complete CRUD API for managing projects — from workspace scaffold to running server. This walkthrough covers every layer: `workspace.py`, module `manifest.py`, `Controller`, `Blueprint` validation, `Service` + `Repository` pattern, structured `Fault`s, dependency injection, and testing.

---

## What You'll Build

A **project tracker API** with these endpoints:

| Method | Path | Purpose |
|---|---|---|
| `GET` | `/projects/` | List all projects (optional `?archived=true` filter) |
| `POST` | `/projects/` | Create a project (JSON body, validated) |
| `GET` | `/projects/<key>` | Get a single project by key |
| `PATCH` | `/projects/<key>` | Update a project (JSON body, validated) |
| `DELETE` | `/projects/<key>` | Archive a project |
| `POST` | `/projects/<key>/restore` | Restore an archived project |

---

## Step 1 — Create the Workspace

```bash
aq init workspace project-tracker
cd project-tracker
```

The generated `workspace.py` starts minimal. Replace it with:

```python title="workspace.py"
from aquilia import Module, Workspace
from aquilia.integrations import DiIntegration, RoutingIntegration, FaultHandlingIntegration

workspace = (
    Workspace("project-tracker", version="1.0.0", description="CRUD starter application")
    .runtime(mode="dev", port=8010, reload=True)
    .database(url="sqlite:///runtime/projects.db", auto_create=True, auto_migrate=False)
    .module(Module("projects", version="1.0.0").route_prefix("/projects").tags("crud", "projects"))
    .integrate(DiIntegration(auto_wire=True))
    .integrate(RoutingIntegration(strict_matching=True))
    .integrate(FaultHandlingIntegration(default_strategy="propagate"))
    .security(cors_enabled=True, helmet_enabled=True)
)
```

??? info "What's happening here"
    | Chain call | Purpose |
    |---|---|
    | `Workspace(...)` | Names and identifies the project |
    | `.runtime(mode="dev", port=8010, reload=True)` | Development server with hot reload on port 8010 |
    | `.database(url="sqlite:///...", auto_create=True)` | Auto-create a SQLite database in the `runtime/` directory |
    | `.module(Module(...).route_prefix("/projects"))` | Register the `projects` module under `/projects` |
    | `.integrate(DiIntegration(auto_wire=True))` | Enable automatic DI across all modules |
    | `.integrate(RoutingIntegration(strict_matching=True))` | Exact route matching |
    | `.integrate(FaultHandlingIntegration(...))` | Map faults to HTTP responses |
    | `.security(cors_enabled=True, helmet_enabled=True)` | CORS for API access, security headers |

---

## Step 2 — Create the Module

```bash
aq add module projects --route-prefix /projects --fault-domain PROJECTS --with-tests
```

This generates:

```
modules/projects/
├── __init__.py
├── manifest.py
├── controllers.py
├── services.py
├── models.py
└── tests/
    └── __init__.py
```

---

## Step 3 — Define the Module Manifest

The `manifest.py` declares everything this module provides. Aquilia auto-discovers it — no `import` in `workspace.py` needed.

```python title="modules/projects/manifest.py"
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

__all__ = ["manifest"]
```

??? tip "AppManifest fields"
    | Field | Purpose |
    |---|---|
    | `name` | Module identifier, used in DI and logging |
    | `version` | Module version for API versioning |
    | `description` | Human-readable description |
    | `controllers` | List of `"module.path:ClassName"` strings |
    | `services` | List of service classes for DI registration |
    | `models` | List of model classes for ORM registration |
    | `base_path` | Python import prefix for relative references |
    | `tags` | Tags for OpenAPI grouping and documentation |
    | `faults` | Default fault domain and handling strategy for this module |

---

## Step 4 — Build the Data Layer

### The Repository

A plain Python class that stores data and raises typed faults:

```python title="modules/projects/services.py"
from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from typing import Any

from aquilia.faults import ConflictFault, NotFoundFault


@dataclass(slots=True)
class ProjectRecord:
    key: str
    name: str
    owner_email: str
    summary: str | None = None
    status: str = "planned"
    archived: bool = False
    created_at: str = ""
    updated_at: str = ""

    def __post_init__(self):
        now = datetime.now(timezone.utc).isoformat()
        if not self.created_at:
            self.created_at = now
        if not self.updated_at:
            self.updated_at = now

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class ProjectRepository:
    """In-memory project storage. Replace with ORM models in production."""

    def __init__(self):
        self._rows: dict[str, ProjectRecord] = {}

    async def list(self, *, include_archived: bool = False) -> list[dict[str, Any]]:
        rows = list(self._rows.values())
        if not include_archived:
            rows = [row for row in rows if not row.archived]
        rows.sort(key=lambda row: row.updated_at, reverse=True)
        return [row.to_dict() for row in rows]

    async def get(self, key: str) -> dict[str, Any]:
        row = self._rows.get(key.upper())
        if row is None:
            raise NotFoundFault(detail=f"Project {key!r} was not found")
        return row.to_dict()

    async def create(self, data: dict[str, Any]) -> dict[str, Any]:
        key = data["key"].upper()
        if key in self._rows:
            raise ConflictFault(detail=f"Project {key!r} already exists")
        row = ProjectRecord(**data)
        self._rows[key] = row
        return row.to_dict()

    async def update(self, key: str, changes: dict[str, Any]) -> dict[str, Any]:
        row = self._rows.get(key.upper())
        if row is None:
            raise NotFoundFault(detail=f"Project {key!r} was not found")
        for field, value in changes.items():
            if value is not None and hasattr(row, field):
                setattr(row, field, value)
        row.updated_at = datetime.now(timezone.utc).isoformat()
        return row.to_dict()
```

### The Service

The service layer orchestrates business logic. The controller calls the service; the service calls the repository:

```python title="modules/projects/services.py (continued)"
class ProjectsService:
    """Business logic for project operations."""

    def __init__(self, repository: ProjectRepository | None = None):
        self.repository = repository or ProjectRepository()

    async def list_projects(self, include_archived: bool = False):
        return await self.repository.list(include_archived=include_archived)

    async def create_project(self, data: dict[str, Any]):
        return await self.repository.create(data)

    async def get_project(self, key: str):
        return await self.repository.get(key)

    async def update_project(self, key: str, changes: dict[str, Any]):
        return await self.repository.update(key, changes)

    async def archive_project(self, key: str):
        return await self.repository.update(key, {"archived": True, "status": "archived"})

    async def restore_project(self, key: str):
        return await self.repository.update(key, {"archived": False, "status": "active"})
```

!!! info "Why a separate service layer?"
    Controllers handle HTTP concerns (parsing requests, status codes, response format). Services handle business logic. The repository handles storage. This separation makes each layer independently testable and swappable.

---

## Step 5 — Validate with Blueprints

Blueprints are request/response contracts. They validate incoming data, cast types, reject unknown fields, and provide structured errors.

```python title="modules/projects/blueprints.py"
from aquilia.blueprints import Blueprint


class ProjectCreateBlueprint(Blueprint):
    """Validation contract for creating a project."""

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


class ProjectUpdateBlueprint(Blueprint):
    """Validation contract for updating a project. All fields optional."""

    name: str | None = None
    summary: str | None = None
    owner_email: str | None = None
    status: str | None = None
    archived: bool | None = None

    class Spec:
        extra_fields = "reject"
```

??? example "Blueprint in action"
    ```python
    # Valid request
    bp = ProjectCreateBlueprint(data={"key": "api", "name": "API", "owner_email": "a@b.com"})
    await bp.is_sealed_async()
    print(bp.validated_data)
    # {'key': 'API', 'name': 'API', 'owner_email': 'a@b.com', 'status': 'planned'}

    # Invalid request — missing email
    bp = ProjectCreateBlueprint(data={"key": "api", "name": "API", "owner_email": "bad"})
    await bp.is_sealed_async()  # raises SealFault with per-field errors
    ```

    Blueprints are covered in depth in the [:octicons-arrow-right-24: Blueprint reference](../reference/classes/blueprint.md).

---

## Step 6 — Wire the Controller

The controller connects HTTP requests to service methods, with blueprint validation and structured responses:

```python title="modules/projects/controllers.py"
from aquilia import Controller, DELETE, GET, PATCH, POST, RequestCtx, Response

from .blueprints import ProjectCreateBlueprint, ProjectUpdateBlueprint
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
        blueprint = ProjectCreateBlueprint(data=await ctx.json())
        await blueprint.is_sealed_async()
        return Response.json(await self.service.create_project(blueprint.validated_data), status=201)

    @GET("/<key:str>")
    async def get_project(self, ctx: RequestCtx, key: str):
        return Response.json(await self.service.get_project(key))

    @PATCH("/<key:str>")
    async def update_project(self, ctx: RequestCtx, key: str):
        blueprint = ProjectUpdateBlueprint(data=await ctx.json())
        await blueprint.is_sealed_async()
        return Response.json(await self.service.update_project(key, blueprint.validated_data))

    @DELETE("/<key:str>")
    async def archive_project(self, ctx: RequestCtx, key: str):
        return Response.json(await self.service.archive_project(key))

    @POST("/<key:str>/restore")
    async def restore_project(self, ctx: RequestCtx, key: str):
        return Response.json(await self.service.restore_project(key))
```

??? info "Controller conventions"
    - **`prefix`**: Base path for all routes in this controller. `prefix = "/"` combined with the module's `route_prefix("/projects")` means routes are served at `/projects/`.
    - **`tags`**: Used in OpenAPI spec generation for grouping endpoints.
    - **`__init__`**: Constructor injection. The `ProjectsService` parameter is optional — if not provided by DI, a default is created.
    - **Path parameters**: `<key:str>` syntax defines a named path parameter. The value is passed as a keyword argument to the handler.
    - **`RequestCtx`**: The request context object — access query params, headers, body, path params, and the DI scope.
    - **`Response.json()`**: Standardized JSON response with automatic `Content-Type` header.

---

## Step 7 — Validate and Run

```bash
# Validate the workspace
$ aq validate
✓ Workspace 'project-tracker' is valid
✓ 1 module(s) discovered
✓ 1 controller(s) with 6 route(s)
✓ 2 service(s), 1 model(s)
✓ DI graph is acyclic
✓ Route table is unambiguous

# Start the server
$ aq serve
⚓ Aquilia 1.1.2 "Crimson Gale"
├─ Workspace: project-tracker v1.0.0
├─ Environment: dev
├─ Server: http://127.0.0.1:8010
├─ Database: sqlite:///runtime/projects.db
├─ Hot reload: enabled
└─ 6 route(s) mounted
```

---

## Step 8 — Test the API

```bash
# Create a project
$ curl -X POST http://127.0.0.1:8010/projects/ \
  -H "Content-Type: application/json" \
  -d '{"key": "API", "name": "Public API", "owner_email": "lead@example.com", "summary": "REST API v2"}'

{"key": "API", "name": "Public API", "owner_email": "lead@example.com",
 "summary": "REST API v2", "status": "planned", "archived": false,
 "created_at": "2026-06-14T12:00:00+00:00", "updated_at": "2026-06-14T12:00:00+00:00"}

# List projects
$ curl http://127.0.0.1:8010/projects/
{"items": [{"key": "API", "name": "Public API", ...}]}

# Get a specific project
$ curl http://127.0.0.1:8010/projects/API
{"key": "API", "name": "Public API", ...}

# Update a project
$ curl -X PATCH http://127.0.0.1:8010/projects/API \
  -H "Content-Type: application/json" \
  -d '{"status": "in_progress"}'

{"key": "API", "name": "Public API", "status": "in_progress", ...}

# Archive a project
$ curl -X DELETE http://127.0.0.1:8010/projects/API
{"key": "API", "status": "archived", "archived": true, ...}

# List archived projects
$ curl http://127.0.0.1:8010/projects/?archived=true
{"items": [{"key": "API", "status": "archived", ...}]}

# Restore a project
$ curl -X POST http://127.0.0.1:8010/projects/API/restore
{"key": "API", "status": "active", "archived": false, ...}

# Validation error — missing owner_email
$ curl -X POST http://127.0.0.1:8010/projects/ \
  -H "Content-Type: application/json" \
  -d '{"key": "BAD"}'

{"error": {"code": "FIELD_VALIDATION", "message": "Validation failed",
 "fields": {"owner_email": ["This field is required"]}}}

# Conflict — duplicate key
$ curl -X POST http://127.0.0.1:8010/projects/ \
  -H "Content-Type: application/json" \
  -d '{"key": "API", "name": "Duplicate", "owner_email": "x@y.com"}'

{"error": {"code": "CONFLICT", "message": "Project 'API' already exists", "domain": "HTTP"}}

# Not found
$ curl http://127.0.0.1:8010/projects/DOESNOTEXIST

{"error": {"code": "NOT_FOUND", "message": "Project 'DOESNOTEXIST' was not found", "domain": "HTTP"}}
```

---

## Step 9 — Add Dependency Injection

The current controller creates its own `ProjectsService`. For a real application, use DI to let the framework manage object lifecycles and scopes.

Register the service in the manifest:

```python title="modules/projects/manifest.py"
from aquilia import AppManifest
from aquilia.manifest import FaultHandlingConfig

manifest = AppManifest(
    name="projects",
    version="1.0.0",
    description="Project CRUD module",
    controllers=["modules.projects.controllers:ProjectsController"],
    services=["modules.projects.services:ProjectsService"],  # ← registered for DI
    models=[],
    base_path="modules.projects",
    tags=["projects"],
    faults=FaultHandlingConfig(default_domain="PROJECTS", strategy="propagate"),
)
```

Update the controller to use `Inject`:

```python title="modules/projects/controllers.py (updated)"
from aquilia import Controller, DELETE, GET, Inject, PATCH, POST, RequestCtx, Response

from .blueprints import ProjectCreateBlueprint, ProjectUpdateBlueprint
from .services import ProjectsService

class ProjectsController(Controller):
    prefix = "/"
    tags = ["projects"]

    def __init__(self, service: ProjectsService = Inject()):
        self.service = service

    # ... route handlers unchanged ...
```

Now Aquilia resolves `ProjectsService` from the DI container automatically. The `AutoWire` integration (enabled in `workspace.py`) discovers this dependency and verifies it at boot.

??? example "DI scopes in Aquilia"
    | Scope | Lifetime | How to declare |
    |---|---|---|
    | `singleton` | Once per process | `@service(scope="singleton")` or default |
    | `app` | Application lifespan | `@service(scope="app")` |
    | `request` | Per HTTP request | `@service(scope="request")` or `Inject()` in controller constructor |

    ```python
    from aquilia.di import service

    @service(scope="singleton")
    class ConfigService:
        def __init__(self):
            self.settings = load_config()

    @service(scope="request")
    class RequestLogger:
        def __init__(self, request_ctx: RequestCtx = Inject()):
            self.request_id = request_ctx.request_id
    ```

    Full DI documentation: [:octicons-arrow-right-24: Dependency Injection](../concepts/core-concepts.md)

---

## Step 10 — Write Tests

Aquilia's test framework provides `TestServer` and `TestClient` that boot a fully-wired application for integration testing:

```python title="modules/projects/tests/test_api.py"
import pytest
from aquilia.testing import TestClient, TestServer


@pytest.fixture
async def server():
    """Boot a test server with the project workspace."""
    async with TestServer(workspace_path=".") as srv:
        yield srv


@pytest.mark.asyncio
async def test_list_projects_returns_empty(server: TestServer):
    client = TestClient(server)
    response = await client.get("/projects/")
    assert response.status == 200
    data = response.json()
    assert data["items"] == []


@pytest.mark.asyncio
async def test_create_and_get_project(server: TestServer):
    client = TestClient(server)

    # Create
    response = await client.post("/projects/", json={
        "key": "TEST",
        "name": "Test Project",
        "owner_email": "test@example.com",
    })
    assert response.status == 201
    created = response.json()
    assert created["key"] == "TEST"
    assert created["name"] == "Test Project"

    # Get by key
    response = await client.get("/projects/TEST")
    assert response.status == 200
    assert response.json()["key"] == "TEST"


@pytest.mark.asyncio
async def test_create_duplicate_returns_conflict(server: TestServer):
    client = TestClient(server)
    payload = {"key": "DUP", "name": "Dup", "owner_email": "a@b.com"}

    await client.post("/projects/", json=payload)
    response = await client.post("/projects/", json=payload)

    assert response.status == 409
    assert response.json()["error"]["code"] == "CONFLICT"


@pytest.mark.asyncio
async def test_get_nonexistent_returns_not_found(server: TestServer):
    client = TestClient(server)
    response = await client.get("/projects/NOPE")
    assert response.status == 404
    assert response.json()["error"]["code"] == "NOT_FOUND"


@pytest.mark.asyncio
async def test_validation_rejects_invalid_email(server: TestServer):
    client = TestClient(server)
    response = await client.post("/projects/", json={
        "key": "VAL",
        "name": "Validation Test",
        "owner_email": "not-an-email",
    })
    assert response.status == 422
```

Run the tests:

```bash
$ aq test
============================= test session starts ==============================
modules/projects/tests/test_api.py ....                               [100%]
============================== 5 passed in 0.89s ===============================
```

---

## Project Structure Recap

After this walkthrough, the project looks like:

```
project-tracker/
├── workspace.py                          # Orchestration root
├── config/
│   └── __init__.py
├── .env
├── requirements.txt
├── runtime/                              # Created at runtime
│   └── projects.db                       # SQLite database
└── modules/
    └── projects/
        ├── __init__.py
        ├── manifest.py                   # Declares controllers, services, models
        ├── controllers.py                # HTTP endpoint handlers
        ├── services.py                   # Business logic + repository
        ├── blueprints.py                 # Request/response validation contracts
        ├── models.py                     # ORM model definitions (if using ORM)
        └── tests/
            └── test_api.py               # Integration tests
```

---

## Next Steps

Your project tracker API is complete. Here's where to go from here:

<div class="grid cards" markdown>

-   :material-shield-account:{ .lg .middle } **Add Authentication**

    ---

    Protect your endpoints with JWT, sessions, OAuth, MFA, or the clearance system.

    [:octicons-arrow-right-24: Authentication guide](../guides/authentication.md)

-   :material-database:{ .lg .middle } **Switch to the ORM**

    ---

    Replace the in-memory repository with `Model`, field types, queries, and migrations.

    [:octicons-arrow-right-24: ORM documentation](../reference/modules/models/index.md)

-   :material-layers:{ .lg .middle } **Add More Modules**

    ---

    Organize your growing codebase with multiple modules: orders, notifications, realtime.

    [:octicons-arrow-right-24: Multi-module example](../examples/multi-module.md)

-   :material-webhook:{ .lg .middle } **Add WebSockets**

    ---

    Stream real-time project updates to clients with `SocketController`.

    [:octicons-arrow-right-24: WebSocket guide](../reference/api/websockets.md)

-   :material-clock-fast:{ .lg .middle } **Add Background Tasks**

    ---

    Send welcome emails, clean up old data, and run scheduled jobs.

    [:octicons-arrow-right-24: Tasks documentation](../reference/modules/tasks/index.md)

-   :material-docker:{ .lg .middle } **Deploy**

    ---

    Generate Dockerfiles, Kubernetes manifests, or deploy to Render directly.

    [:octicons-arrow-right-24: Deployment guides](../deployment/docker.md)

</div>