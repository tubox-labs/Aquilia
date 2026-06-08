<div align="center">
  <img src="https://github.com/tubox-labs/Aquilia/blob/master/assets/logo.png" alt="Aquilia Logo" width="200" />
  <h1>Aquilia</h1>
  <p><strong>The async-native, manifest-first Python web framework.</strong></p>

  [![Version](https://img.shields.io/badge/version-1.1.0-blue.svg)](https://aquilia.tubox.cloud)
  [![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
  [![Python](https://img.shields.io/badge/python-3.10%2B-blue.svg)](https://www.python.org/)
  [![Tests](https://img.shields.io/badge/tests-5085%20passing-brightgreen.svg)](#-testing)
</div>

---

**Aquilia** is an async-native, manifest-first Python web framework that auto-discovers modules, wires dependency injection, and generates infrastructure manifests — no routing glue code, no manual Dockerfiles.

## Features

- **Manifest-First Architecture** — Modules declare controllers, services, and middleware in `manifest.py`. Aquilia discovers and wires them automatically.
- **Auto-Discovery** — `PackageScanner` traverses your workspace, finds modules, and registers them without boilerplate.
- **Scoped Dependency Injection** — Hierarchical DI (`singleton`, `app`, `request` scopes) with annotation-driven providers.
- **Structured Fault System** — Every error is a typed `Fault` subclass with domain, severity, code, and recovery strategy. No raw exceptions.
- **Clearance System** — Declarative, multi-dimensional access control with access levels, entitlements, conditions, and tenant compartments.
- **API Versioning with Sunset** — Epoch-based versioning with channel promotion, multi-strategy resolution (URL, header, query, media type), and RFC 8594 sunset enforcement.
- **SSE Streaming** — First-class Server-Sent Events with `SSEResponse` and `SSEEvent` for real-time data and LLM token streaming.
- **OpenTelemetry** — Built-in distributed tracing via `OTelConfig` and ASGI instrumentation middleware.
- **Production Security** — HMAC-verified caches, path traversal protection, CSRF/CORS/CSP/HSTS guards, sandboxed Jinja2 templates.

## Installation

```bash
pip install aquilia
```

`jinja2` (templates) and `aiosqlite` (SQLite) are bundled in core — no extras needed to get started.

| Extra | What it adds |
|-------|-------------|
| `aquilia` | Core framework — controllers, DI, ORM, templates, filesystem, SQLite |
| `aquilia[auth]` | Argon2 hashing, JWT, OAuth, cryptography |
| `aquilia[postgres]` | asyncpg driver for PostgreSQL |
| `aquilia[redis]` | Redis cache & WebSocket backends |
| `aquilia[otel]` | OpenTelemetry API, SDK, OTLP exporter, ASGI instrumentation |
| `aquilia[mail]` | SMTP email provider |
| `aquilia[server]` | Gunicorn + Uvicorn workers for production |
| `aquilia[full]` | Everything above — auth, postgres, redis, otel, mail, server, multipart |

## Quick Start

Aquilia is workspace-first — scaffold projects through the `aq` CLI.

### 1 — Create a workspace

```bash
aq init workspace my-app
cd my-app
```

This generates `workspace.py`, `config/`, and a starter page serving `GET /` immediately.

### 2 — Add a module

```bash
aq add module users
```

Generates `modules/users/` with `manifest.py`, `controllers.py`, `services.py`, and `models.py`.

### 3 — Write a controller

```python
# modules/users/controllers.py
from aquilia import Controller, GET, POST, RequestCtx, Response
from aquilia.controller.validation import validate_body

class UsersController(Controller):
    prefix = "/users"
    tags  = ["users"]

    @GET("/")
    async def list_users(self, ctx: RequestCtx):
        return Response.json({"users": []})

    @POST("/")
    @validate_body(CreateUserBlueprint)
    async def create_user(self, ctx: RequestCtx, body: dict):
        return Response.json({"created": body}, status=201)
```

No manual route registration — controllers in a module's `manifest.py` are discovered and wired automatically.

### 4 — Run the development server

```bash
aq serve
```

Serves on `http://127.0.0.1:8000` with hot reload.

## CLI

| Command | Description |
|---------|-------------|
| `aq init workspace <name>` | Scaffold a new workspace |
| `aq add module <name>` | Add a module with manifest, controller, services, models |
| `aq serve` | Start development server with hot reload |
| `aq compile` | Compile manifests into a frozen artifact |
| `aq validate` | Validate manifests, routes, and DI graph |
| `aq inspect` | Inspect compiled routes, DI providers, and version graph |

## Code Examples

### Structured Faults

```python
from aquilia.faults import Fault, FaultDomain, Severity

class PaymentRequiredFault(Fault):
    def __init__(self, plan: str):
        super().__init__(
            code="PAYMENT_REQUIRED",
            message=f"Upgrade to {plan} to access this feature",
            domain=FaultDomain.SECURITY,
            severity=Severity.WARN,
            retryable=False,
            public=True,
        )

raise PaymentRequiredFault(plan="pro")
```

Or use built-in HTTP faults:

```python
from aquilia.faults import NotFoundFault, ForbiddenFault

raise NotFoundFault(detail="/api/users/999 does not exist")
raise ForbiddenFault(detail="Insufficient permissions")
```

### Clearance System — Declarative Access Control

```python
from aquilia import Controller, GET, POST, DELETE, RequestCtx
from aquilia.auth.clearance import Clearance, AccessLevel, grant, exempt, is_verified, is_owner_or_admin

class DocumentController(Controller):
    prefix = "/documents"
    clearance = Clearance(level=AccessLevel.AUTHENTICATED)

    @GET("/")
    @grant(level=AccessLevel.PUBLIC)
    async def list_public(self, ctx: RequestCtx):
        return {"docs": []}

    @POST("/")
    @grant(entitlements=["documents:write"], conditions=[is_verified])
    async def create(self, ctx: RequestCtx):
        ...

    @DELETE("/{doc_id}")
    @grant(level=AccessLevel.CONFIDENTIAL, conditions=[is_owner_or_admin])
    async def delete(self, ctx: RequestCtx, doc_id: str):
        ...
```

### SSE Streaming

```python
import asyncio
from aquilia import Controller, GET, RequestCtx
from aquilia.sse import SSEEvent, SSEResponse

class StreamController(Controller):
    prefix = "/stream"

    @GET("/events")
    async def live_events(self, ctx: RequestCtx):
        return SSEResponse(self._generate())

    async def _generate(self):
        for i in range(100):
            yield SSEEvent(data=f"event {i}", event="update", id=str(i))
            await asyncio.sleep(0.5)
```

### API Versioning with Sunset

```python
from aquilia import Controller, GET
from aquilia.versioning import version, SunsetPolicy, VERSION_NEUTRAL

class UsersV2Controller(Controller):
    prefix = "/users"
    version = "2.0"

    @GET("/")
    async def list_v2(self, ctx):
        ...

class UsersV1Controller(Controller):
    prefix = "/users"
    version = "1.0"
    sunset = SunsetPolicy(grace_period="180d", warn_header=True)

    @GET("/")
    async def list_v1(self, ctx):
        ...
```

## Architecture

The boot sequence: **Manifests → Aquilary → RuntimeRegistry → Controllers → ASGI**

| Subsystem | Purpose |
|-----------|---------|
| **Aquilary** | Core manifest registry, metadata, runtime wiring |
| **Controller** | Route decorators (`@GET`, `@POST`), OpenAPI generation, filtering, pagination |
| **DI** | Hierarchical dependency injection with singleton/app/request scopes |
| **Faults** | Structured error system with 14+ domains, typed HTTP faults |
| **Auth** | JWT/session auth, MFA, OAuth, RBAC/ABAC, clearance guards |
| **Flow** | Typed routing and composable request pipelines with effect scopes |
| **Models/ORM** | Async ORM with query builder, migrations, transactions |
| **Templates** | Sandboxed Jinja2 with bytecode caching and HMAC integrity |
| **Cache** | Multi-backend caching with decorators and middleware |
| **Storage** | Async file storage (local, S3, GCS, Azure, SFTP, memory) |
| **Tasks** | Background job system with priority queues and scheduling |
| **Mail** | Multi-provider email (SMTP, SES, SendGrid) |
| **SSE** | Server-Sent Events streaming (`SSEResponse`, `SSEEvent`) |
| **WebSockets** | Socket controllers with event/subscription/guard decorators |
| **Versioning** | Epoch-based API versioning with sunset lifecycle |
| **OTel** | OpenTelemetry distributed tracing middleware and configuration |
| **Admin** | Auto-detecting admin dashboard with audit logging |

## Testing

```bash
python -m pytest tests/ -v

python -m pytest tests/ --cov=aquilia --cov-report=html
```

## Learn More

- **Documentation**: [https://aquilia.tubox.cloud](https://aquilia.tubox.cloud)
- **Architecture Guide**: [https://aquilia.tubox.cloud/docs/architecture](https://aquilia.tubox.cloud/docs/architecture)
- **Quick Start**: [https://aquilia.tubox.cloud/docs/quickstart](https://aquilia.tubox.cloud/docs/quickstart)
- **Changelog**: [CHANGELOG.md](CHANGELOG.md)
- **Security**: [SECURITY.md](SECURITY.md)
- **Contributing**: [CONTRIBUTING.md](CONTRIBUTING.md)

---

<p align="center">Built with ❤️ by the Aquilia Team</p>