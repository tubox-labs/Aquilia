# Aquilia — Developer Guide

> Everything you need to understand, run, extend, and debug the Aquilia framework.

---

## Table of Contents

1. [Prerequisites](#1-prerequisites)
2. [Repository Setup](#2-repository-setup)
3. [Project Structure](#3-project-structure)
4. [Running the Framework](#4-running-the-framework)
5. [How Aquilia Works](#5-how-aquilia-works)
6. [Creating a Module](#6-creating-a-module)
7. [Working with Controllers](#7-working-with-controllers)
8. [Working with Models](#8-working-with-models)
9. [Dependency Injection](#9-dependency-injection)
10. [Configuration](#10-configuration)
11. [Testing](#11-testing)
12. [Debugging](#12-debugging)
13. [Common Tasks](#13-common-tasks)
14. [Architecture Reference](#14-architecture-reference)

---

## 1. Prerequisites

| Requirement | Version |
|-------------|---------|
| Python | ≥ 3.10 |
| pip | Latest |
| Git | Latest |
| SQLite | Built-in (default DB) |
| Node.js | ≥ 18 (only for aqdocx frontend) |

Optional for specific features:
- **PostgreSQL** — for asyncpg backend
- **MySQL** — for aiomysql backend
- **Redis** — for cache/session/socket backends
- **Docker** — for containerized development

---

## 2. Repository Setup

### Clone and Install

```bash
git clone https://github.com/axiomchronicles/Aquilia.git
cd Aquilia

# Create virtual environment
python -m venv env
source env/bin/activate

# Install in development mode with all extras
pip install -e ".[all]"

# Or install with specific extras
pip install -e ".[dev,testing,auth,db,templates]"
```

### Available Extras

| Extra | Packages |
|-------|----------|
| `templates` | jinja2 |
| `auth` | cryptography, argon2-cffi |
| `db` | aiosqlite |
| `files` | aiofiles |
| `multipart` | python-multipart |
| `redis` | aioredis |
| `mail` | aiosmtplib |
| `mail-ses` | aiobotocore |
| `mail-sendgrid` | httpx |
| `server` | uvicorn |
| `mlops` | numpy |
| `testing` | pytest, pytest-asyncio, coverage |
| `dev` | black, ruff, mypy, pytest, aiosqlite |
| `full` | all production extras |
| `all` | full + dev + testing |

### Verify Installation

```bash
# Check CLI
aq --version

# Run tests
pytest tests/ -x -v

# Check for lint errors
ruff check aquilia/
```

---

## 3. Project Structure

```
Aquilia/
├── aquilia/                 # Framework source code (~106,500 lines)
│   ├── __init__.py          # Public API exports
│   ├── server.py            # AqServer — central orchestrator
│   ├── request.py           # AqRequest — ASGI request wrapper
│   ├── response.py          # AqResponse — HTTP response builder
│   ├── config_builders.py   # Fluent configuration API
│   └── <20+ subsystem dirs> # See docs/Codebase-Structure.md
│
├── tests/                   # Test suite
├── myapp/                   # Example application
├── benchmark/               # Performance benchmarks
├── docs/                    # Documentation
├── aqdocx/                  # Documentation site (Vue.js)
└── .claude/                 # AI agent configurations
```

---

## 4. Running the Framework

### Using the CLI

```bash
# Initialize a new project
aq init myproject

# Run development server
aq run

# Run with hot reload
aq serve --reload

# Run with specific host/port
aq serve --host 0.0.0.0 --port 8080
```

### Using the Example App

```bash
cd myapp

# Install dependencies
pip install -r requirements.txt

# Run the starter app
python starter.py
```

### Using Docker

```bash
# Build image
docker build -t aquilia .

# Run with compose (includes PostgreSQL)
docker compose up
```

---

## 5. How Aquilia Works

### 5.1 The Big Picture

Aquilia is an **async Python ASGI web framework** with a **manifest-driven modular architecture**. Every feature is organized into modules declared via `manifest.yaml` files. The framework:

1. **Discovers** modules via AST scanning (no code execution)
2. **Validates** module manifests
3. **Resolves** dependencies using Tarjan's algorithm
4. **Registers** providers in a DI container
5. **Compiles** URL patterns into an optimized router
6. **Builds** a middleware chain
7. **Serves** requests through a 12-phase executor

### 5.2 Request Lifecycle

```
HTTP Request
  → Uvicorn (ASGI server)
  → ProtocolHandler (engine.py)
  → ASGIAdapter (asgi.py)
  → Middleware chain (CORS → CSRF → Auth → RateLimit → Cache)
  → Router.match() (controller/router.py)
  → 12-phase Executor (controller/executor.py)
    → Guards → Param binding → Body parse → Validate → DI resolve → Handler → Serialize → Hooks
  → Middleware chain (reverse)
  → HTTP Response
```

### 5.3 Key Concepts

| Concept | Description | Key File |
|---------|-------------|----------|
| **Module** | Self-contained feature unit with manifest | `manifest.py` |
| **Controller** | Route handler class | `controller/base.py` |
| **Blueprint** | Data serialization schema | `blueprints/core.py` |
| **Effect** | Typed resource lifecycle (acquire/release) | `effects.py` |
| **Flow** | Guard → Transform → Handler → Hook pipeline | `flow.py` |
| **Provider** | DI-managed service instance | `di/providers.py` |
| **Fault** | Structured error with severity and code | `faults/engine.py` |

---

## 6. Creating a Module

### 6.1 Module Structure

```
modules/
  users/
    manifest.yaml
    controllers/
      user_controller.py
    models/
      user.py
    services/
      user_service.py
    blueprints/
      user_blueprint.py
```

### 6.2 Manifest File

```yaml
# modules/users/manifest.yaml
name: users
version: "1.0.0"
description: User management module

providers:
  - import_path: modules.users.services.user_service.UserService
    scope: singleton

controllers:
  - import_path: modules.users.controllers.user_controller.UserController

models:
  - import_path: modules.users.models.user.User

depends_on:
  - auth  # This module requires the auth module
```

### 6.3 Generate via CLI

```bash
aq init module users
```

---

## 7. Working with Controllers

### 7.1 Basic Controller

```python
from aquilia import BaseController, route, get, post, AqRequest, AqResponse

class UserController(BaseController):
    prefix = "/api/users"

    @get("/")
    async def list_users(self, request: AqRequest) -> AqResponse:
        users = await User.objects.all()
        return AqResponse.json({"users": users})

    @get("/{id:int}")
    async def get_user(self, request: AqRequest, id: int) -> AqResponse:
        user = await User.objects.get(id=id)
        return AqResponse.json(user)

    @post("/")
    async def create_user(self, request: AqRequest) -> AqResponse:
        data = await request.json()
        user = await User.objects.create(**data)
        return AqResponse.json(user, status=201)
```

### 7.2 With Guards and DI

```python
from aquilia import BaseController, get, post, Guard
from aquilia.auth import AuthGuard, RoleGuard

class UserController(BaseController):
    prefix = "/api/users"

    def __init__(self, user_service: UserService):
        self.user_service = user_service  # Injected by DI

    @get("/", guards=[AuthGuard()])
    async def list_users(self, request: AqRequest) -> AqResponse:
        users = await self.user_service.list_all()
        return AqResponse.json(users)

    @post("/", guards=[AuthGuard(), RoleGuard("admin")])
    async def create_user(self, request: AqRequest) -> AqResponse:
        data = await request.json()
        user = await self.user_service.create(data)
        return AqResponse.json(user, status=201)
```

### 7.3 URL Patterns

| Pattern | Example | Matches |
|---------|---------|---------|
| `/users` | Static | Exact match |
| `/users/{id}` | Parameterized | `/users/42` |
| `/users/{id:int}` | Typed | `/users/42` (int only) |
| `/users/{slug:str}` | String | `/users/john-doe` |
| `/users/{uuid:uuid}` | UUID | `/users/550e8400-...` |
| `/files/{path:path}` | Path | `/files/a/b/c.txt` |

---

## 8. Working with Models

### 8.1 Define a Model

```python
from aquilia.models import Model, CharField, IntegerField, ForeignKey, DateTimeField

class User(Model):
    class Meta:
        table_name = "users"

    name = CharField(max_length=100)
    email = CharField(max_length=255, unique=True)
    age = IntegerField(null=True)
    created_at = DateTimeField(auto_now_add=True)
```

### 8.2 QuerySet API

```python
# Create
user = await User.objects.create(name="Alice", email="alice@example.com")

# Read
user = await User.objects.get(id=1)
users = await User.objects.filter(age__gte=18).order_by("-created_at").limit(10)
exists = await User.objects.filter(email="alice@example.com").exists()
count = await User.objects.count()

# Update
user.name = "Bob"
await user.save()

# Delete
await user.delete()

# Aggregation
from aquilia.models import Avg, Count
stats = await User.objects.aggregate(avg_age=Avg("age"), total=Count("id"))

# Select related (eager loading)
posts = await Post.objects.select_related("author").filter(published=True)
```

### 8.3 Migrations

```bash
# Generate migration
aq migrate generate --name add_users_table

# Run migrations
aq migrate run

# Show migration status
aq migrate status

# Rollback last migration
aq migrate rollback
```

---

## 9. Dependency Injection

### 9.1 Register Providers

```python
# In manifest.yaml
providers:
  - import_path: modules.users.services.UserService
    scope: singleton

# Or programmatically
container.add_singleton(UserService)
container.add_transient(NotificationService)
container.add_factory(lambda: DatabaseSession(), scope="request")
container.add_value("API_KEY", "secret-key-123")
```

### 9.2 Inject Dependencies

```python
class UserService:
    def __init__(self, db: DatabaseEngine, cache: CacheManager):
        # Both injected automatically by the DI container
        self.db = db
        self.cache = cache
```

### 9.3 Scopes

| Scope | Lifetime | Use Case |
|-------|----------|----------|
| SINGLETON | App lifetime | Database engine, cache manager |
| APPLICATION | App lifetime | Configuration, registries |
| REQUEST | Single HTTP request | Request-specific state |
| SESSION | User session | User preferences |
| TRANSIENT | Created every resolution | Lightweight, stateless services |
| THREAD | Thread lifetime | Thread-local state |

---

## 10. Configuration

### 10.1 Fluent Builder API

```python
from aquilia import AqServer
from aquilia.config_builders import (
    DatabaseConfig, CacheConfig, AuthConfig, MailConfig
)

server = AqServer()

# Database
server.configure(
    DatabaseConfig()
        .backend("postgresql")
        .host("localhost")
        .port(5432)
        .database("myapp")
        .user("admin")
        .password("secret")
        .pool_size(20)
        .build()
)

# Cache
server.configure(
    CacheConfig()
        .backend("redis")
        .url("redis://localhost:6379")
        .default_ttl(300)
        .build()
)

# Auth
server.configure(
    AuthConfig()
        .secret_key("your-secret-key")
        .token_algorithm("ES256")
        .token_expiry(3600)
        .enable_mfa(True)
        .build()
)
```

### 10.2 YAML Configuration

```yaml
# config/app.yaml
app:
  name: MyApp
  debug: false

database:
  backend: postgresql
  host: localhost
  port: 5432

cache:
  backend: redis
  url: redis://localhost:6379

auth:
  secret_key: ${SECRET_KEY}  # Environment variable
  token_expiry: 3600
```

---

## 11. Testing

### 11.1 Setup

```python
# tests/conftest.py
import pytest
from aquilia.testing import AqTestClient, create_test_app

@pytest.fixture
async def app():
    app = create_test_app()
    yield app

@pytest.fixture
async def client(app):
    async with AqTestClient(app) as client:
        yield client
```

### 11.2 Write Tests

```python
import pytest
from aquilia.testing import AqTestCase

class TestUserAPI(AqTestCase):

    async def test_create_user(self, client):
        response = await client.post("/api/users", json={
            "name": "Alice",
            "email": "alice@example.com"
        })
        assert response.status_code == 201
        assert response.json["name"] == "Alice"

    async def test_create_user_invalid_email(self, client):
        response = await client.post("/api/users", json={
            "name": "Alice",
            "email": "not-an-email"
        })
        assert response.status_code == 422

    async def test_get_user_unauthenticated(self, client):
        response = await client.get("/api/users/1")
        assert response.status_code == 401
```

### 11.3 Run Tests

```bash
# Run all tests
pytest tests/ -v

# Run specific test file
pytest tests/test_auth_system.py -v

# Run with coverage
pytest tests/ --cov=aquilia --cov-report=html

# Run only fast tests
pytest tests/ -m "not slow" -v
```

---

## 12. Debugging

### 12.1 Enable Debug Mode

```python
server = AqServer(debug=True)
```

This enables:
- Detailed exception pages with stack traces
- Debug toolbar on HTML responses
- Verbose logging
- Auto-reload on file changes

### 12.2 Common Issues

| Issue | Cause | Fix |
|-------|-------|-----|
| `ProviderNotFound` | Service not registered | Add to manifest.yaml providers |
| `CircularDependencyError` | Two providers depend on each other | Break cycle with factory or interface |
| `RouteConflict` | Duplicate route patterns | Check controller prefixes |
| `DatabaseNotConfigured` | Missing DB config | Call `server.configure(DatabaseConfig()...)` |
| `TemplateNotFound` | Wrong template directory | Check template search paths |
| Import errors | Missing optional dependency | Install the right extra: `pip install -e ".[auth]"` |

### 12.3 Logging

```python
import logging

# See all framework activity
logging.getLogger("aquilia").setLevel(logging.DEBUG)

# See only database queries
logging.getLogger("aquilia.db").setLevel(logging.DEBUG)

# See auth decisions
logging.getLogger("aquilia.auth").setLevel(logging.DEBUG)
```

---

## 13. Common Tasks

### Add a new API endpoint

1. Create controller in `modules/<name>/controllers/`
2. Register in `manifest.yaml` under `controllers`
3. Add guards for auth if needed
4. Add blueprint for validation/serialization
5. Write tests

### Add a database table

1. Define model in `modules/<name>/models/`
2. Register in `manifest.yaml` under `models`
3. Generate migration: `aq migrate generate --name add_<table>`
4. Run migration: `aq migrate run`

### Add a background task

1. Define task function in `modules/<name>/tasks/`
2. Register in task queue
3. Add scheduling (cron or interval) if recurring

### Add authentication to an endpoint

```python
from aquilia.auth import AuthGuard, RoleGuard, ClearanceGuard

@get("/secret", guards=[
    AuthGuard(),                    # Must be logged in
    RoleGuard("admin"),             # Must have admin role
    ClearanceGuard("CONFIDENTIAL")  # Must have CONFIDENTIAL clearance
])
async def secret_endpoint(self, request):
    ...
```

### Add caching to an endpoint

```python
from aquilia.cache import cached

@get("/expensive")
@cached(ttl=300, key="expensive:{request.query.page}")
async def expensive_endpoint(self, request):
    ...
```

---

## 14. Architecture Reference

For deeper understanding, see:

| Document | Contents |
|----------|----------|
| [Architecture.md](Architecture.md) | High-level architecture overview |
| [System-Design.md](System-Design.md) | Design patterns and decisions |
| [Codebase-Structure.md](Codebase-Structure.md) | File-by-file inventory |
| [Data-Flow.md](Data-Flow.md) | Request/response data flow |
| [API-Architecture.md](API-Architecture.md) | Controller, router, OpenAPI |
| [Database-Design.md](Database-Design.md) | ORM, migrations, backends |
| [Background-Jobs.md](Background-Jobs.md) | Task queue, scheduling |
| [Security-Audit.md](Security-Audit.md) | Vulnerability assessment |
| [Observability.md](Observability.md) | Logging, monitoring, health |
| [Codebase-Knowledge-Graph.md](Codebase-Knowledge-Graph.md) | Module dependency map |
