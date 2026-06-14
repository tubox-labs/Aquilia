# Beginner Tutorial: Building a Simple REST API

In this tutorial, you'll build a complete REST API for a task management app using Aquilia. You'll learn workspace setup, module creation, controller routing, blueprint validation, and testing.

## Prerequisites

```bash
pip install aquilia
```

Ensure Python 3.10+ is installed.

## Step 1: Create a workspace

```bash
aq init tasks_app
```

This creates the project structure:

```
tasks_app/
├── workspace.py          # Workspace orchestration
├── modules/
│   └── tasks/
│       ├── manifest.py   # Module declarations
│       ├── controllers/  # Controller classes
│       ├── services/     # Business logic
│       └── blueprints/   # Validation schemas
├── .env                  # Environment variables
└── requirements.txt
```

## Step 2: Configure the workspace

Edit `workspace.py`:

```python
from aquilia.workspace import Workspace, Module
from aquilia import AquilaConfig, Env, Secret

# ── Environment config ──────────────────────────────────────────
class BaseEnv(AquilaConfig):
    env = "dev"

    class server(AquilaConfig.Server):
        host = "127.0.0.1"
        port = 8000
        reload = True

class DevEnv(BaseEnv):
    env = "dev"

# ── Workspace definition ────────────────────────────────────────
workspace = (
    Workspace("tasks_app", version="0.1.0")
    .runtime(mode="dev", port=8000, reload=True)
    .module(
        Module("tasks", version="0.1.0")
        .route_prefix("/api/tasks")
        .tags("core")
    )
    .env_config(BaseEnv)
)
```

## Step 3: Create the module manifest

`modules/tasks/manifest.py`:

```python
from aquilia.manifest import AppManifest

manifest = AppManifest(
    name="tasks",
    version="0.1.0",
    description="Task management module",
    controllers=[
        "modules.tasks.controllers:TasksController",
    ],
    services=[
        "modules.tasks.services:TaskService",
    ],
)
```

## Step 4: Build the task service

`modules/tasks/services.py`:

```python
from __future__ import annotations
from typing import Any

class TaskService:

    def __init__(self):
        self._tasks: dict[int, dict[str, Any]] = {}
        self._next_id = 1

    async def list_tasks(self, status: str | None = None) -> list[dict[str, Any]]:
        tasks = list(self._tasks.values())
        if status:
            tasks = [t for t in tasks if t["status"] == status]
        return sorted(tasks, key=lambda t: t["id"])

    async def get_task(self, task_id: int) -> dict[str, Any] | None:
        return self._tasks.get(task_id)

    async def create_task(self, data: dict[str, Any]) -> dict[str, Any]:
        task = {
            "id": self._next_id,
            "title": data["title"],
            "description": data.get("description", ""),
            "status": "pending",
        }
        self._tasks[self._next_id] = task
        self._next_id += 1
        return task

    async def update_task(self, task_id: int, data: dict[str, Any]) -> dict[str, Any] | None:
        task = self._tasks.get(task_id)
        if not task:
            return None
        task["title"] = data.get("title", task["title"])
        task["description"] = data.get("description", task["description"])
        task["status"] = data.get("status", task["status"])
        return task

    async def delete_task(self, task_id: int) -> bool:
        if task_id in self._tasks:
            del self._tasks[task_id]
            return True
        return False
```

## Step 5: Create a Blueprint for validation

Blueprints declare the shape of request/response data with type-safe facets.

`modules/tasks/blueprints.py`:

```python
from aquilia.blueprints import Blueprint, TextFacet, ChoiceFacet, ReadOnly

class CreateTaskBlueprint(Blueprint):
    title = TextFacet(min_length=1, max_length=200)
    description = TextFacet(max_length=2000, required=False)

class UpdateTaskBlueprint(Blueprint):
    title = TextFacet(min_length=1, max_length=200, required=False)
    description = TextFacet(max_length=2000, required=False)
    status = ChoiceFacet(choices=["pending", "in_progress", "done"], required=False)

class TaskResponse(Blueprint):
    id = ReadOnly()
    title = TextFacet()
    description = TextFacet()
    status = TextFacet()
```

## Step 6: Build the controller

`modules/tasks/controllers.py`:

```python
from __future__ import annotations

from aquilia import Controller, GET, POST, PUT, DELETE, RequestCtx, Response, Inject
from aquilia.controller.validation import validate_body
from aquilia.faults.domains import NotFoundFault

from .blueprints import CreateTaskBlueprint, UpdateTaskBlueprint
from .services import TaskService


class TasksController(Controller):
    prefix = "/api/tasks"
    tags = ["tasks"]

    def __init__(self, task_service: TaskService = Inject()):
        self.service = task_service

    @GET("/")
    async def list_tasks(self, ctx: RequestCtx):
        status = ctx.request.query_params.get("status")
        tasks = await self.service.list_tasks(status=status)
        return Response.json({"tasks": tasks})

    @GET("/{id:int}")
    async def get_task(self, ctx: RequestCtx, id: int):
        task = await self.service.get_task(id)
        if task is None:
            raise NotFoundFault(detail=f"Task {id} not found")
        return Response.json(task)

    @POST("/")
    @validate_body(CreateTaskBlueprint)
    async def create_task(self, ctx: RequestCtx, body: dict):
        task = await self.service.create_task(body)
        return Response.json(task, status=201)

    @PUT("/{id:int}")
    @validate_body(UpdateTaskBlueprint)
    async def update_task(self, ctx: RequestCtx, id: int, body: dict):
        task = await self.service.update_task(id, body)
        if task is None:
            raise NotFoundFault(detail=f"Task {id} not found")
        return Response.json(task)

    @DELETE("/{id:int}")
    async def delete_task(self, ctx: RequestCtx, id: int):
        deleted = await self.service.delete_task(id)
        if not deleted:
            raise NotFoundFault(detail=f"Task {id} not found")
        return Response.json({"deleted": True})
```

Key points:
- `Controller.prefix` sets the URL base for all routes.
- `@GET("/")` maps `GET /api/tasks/`.
- `{id:int}` ensures the path parameter is an integer.
- `@validate_body(CreateTaskBlueprint)` validates and injects `body: dict`.
- `NotFoundFault` is a first-class HTTP fault (404) with a descriptive detail.

## Step 7: Test with TestClient

`tests/test_tasks.py`:

```python
import pytest
from aquilia.testing import TestClient
from aquilia.entrypoint import create_app

@pytest.fixture
async def client():
    app = create_app()  # Reads workspace.py from current directory
    client = TestClient(app)
    yield client

@pytest.mark.asyncio
async def test_create_task(client):
    response = await client.post(
        "/api/tasks/",
        json={"title": "Learn Aquilia", "description": "Read the docs"},
    )
    assert response.status == 201
    data = response.json()
    assert data["title"] == "Learn Aquilia"
    assert data["status"] == "pending"
    assert "id" in data

@pytest.mark.asyncio
async def test_list_tasks(client):
    # Create a task first
    await client.post("/api/tasks/", json={"title": "Task 1"})
    await client.post("/api/tasks/", json={"title": "Task 2"})

    response = await client.get("/api/tasks/")
    assert response.status == 200
    data = response.json()
    assert len(data["tasks"]) == 2

@pytest.mark.asyncio
async def test_get_task_not_found(client):
    response = await client.get("/api/tasks/999")
    assert response.status == 404
    error = response.json()
    assert error["error"]["code"] == "HTTP_404"

@pytest.mark.asyncio
async def test_validation_error(client):
    response = await client.post("/api/tasks/", json={"title": ""})
    assert response.status == 422  # Blueprint validation returns 422

@pytest.mark.asyncio
async def test_update_task(client):
    create_resp = await client.post("/api/tasks/", json={"title": "Old title"})
    task_id = create_resp.json()["id"]

    response = await client.put(
        f"/api/tasks/{task_id}",
        json={"title": "New title", "status": "done"},
    )
    assert response.status == 200
    assert response.json()["title"] == "New title"
    assert response.json()["status"] == "done"

@pytest.mark.asyncio
async def test_delete_task(client):
    create_resp = await client.post("/api/tasks/", json={"title": "Delete me"})
    task_id = create_resp.json()["id"]

    response = await client.delete(f"/api/tasks/{task_id}")
    assert response.status == 200

    # Verify it's gone
    response = await client.get(f"/api/tasks/{task_id}")
    assert response.status == 404
```

Run the tests:

```bash
pytest tests/ -v
```

## Step 8: Run the server

```bash
aq serve
```

Test it with curl:

```bash
# Create a task
curl -X POST http://127.0.0.1:8000/api/tasks/ \
  -H "Content-Type: application/json" \
  -d '{"title": "My first task", "description": "Hello Aquilia"}'

# List tasks
curl http://127.0.0.1:8000/api/tasks/

# Filter by status
curl "http://127.0.0.1:8000/api/tasks/?status=pending"

# Get a task
curl http://127.0.0.1:8000/api/tasks/1

# Update a task
curl -X PUT http://127.0.0.1:8000/api/tasks/1 \
  -H "Content-Type: application/json" \
  -d '{"status": "done"}'

# Delete a task
curl -X DELETE http://127.0.0.1:8000/api/tasks/1
```

## Summary

You've built a complete REST API with:

| Concept | Implementation |
|---------|---------------|
| Workspace | `Workspace` + `Module` in `workspace.py` |
| Module manifest | `AppManifest` in `manifest.py` |
| Business logic | `TaskService` with DI |
| Routing | `@GET`, `@POST`, `@PUT`, `@DELETE` decorators |
| Validation | Blueprint classes with `@validate_body` |
| Error handling | `NotFoundFault` → 404, Blueprint validation → 422 |
| Testing | `TestClient` with pytest-asyncio |
| Serving | `aq serve` |