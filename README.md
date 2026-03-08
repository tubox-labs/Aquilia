<div align="center">
  <img src="https://github.com/tubox-labs/Aquilia/blob/master/assets/logo.png" alt="Aquilia Logo" width="200" />
  <h1>Aquilia</h1>
  <p><strong>The speed of a microframework. The reliability of an enterprise engine.</strong></p>

  [![Version](https://img.shields.io/badge/version-1.0.1b3-orange.svg)](https://aquilia.tubox.cloud)
  [![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
  [![Python](https://img.shields.io/badge/python-3.10%2B-blue.svg)](https://www.python.org/)
  [![Tests](https://img.shields.io/badge/tests-5085%20passing-brightgreen.svg)](#-testing)
</div>

---

**Aquilia** is a Manifest-First, async-native Python framework designed to bridge the gap between developer velocity and production-grade stability. It removes routing and deployment boilerplate, auto-generates infrastructure manifests (Docker/K8s), and comes with built-in MLOps capabilities.

## 🚀 Why Aquilia?

Current frameworks force a trade-off: use a microframework for speed but spend months on infrastructure, or use a "batteries-included" monolith that's hard to scale and deploy. Aquilia changes the game:

- **Manifest-First Architecture**: Your code defines its own infrastructure. No more manual Dockerfile or K8s YAML maintenance.
- **Scoped Dependency Injection**: Built-in, enterprise-grade DI that handles complex lifecycles and provides deep observability.
- **Async-Native Core**: Built for modern, high-concurrency workloads from the ground up.
- **Integrated MLOps**: Native support for artifact versioning, lineage tracking, and model deployment.
- **Structured Fault System**: First-class typed error handling with domains, severity, and recovery strategies — no raw exceptions.
- **Production Security**: HMAC-verified caches, path traversal protection, CSRF/CORS/CSP guards, and sandboxed templates out of the box.

## 📦 Installation

```bash
pip install aquilia
```

`jinja2` (templates + admin panel) and `aiosqlite` (default SQLite backend) are
**bundled in the core install** — no extras needed to get started.

| Extra | What it adds |
|-------|-------------|
| `aquilia[auth]` | Argon2 hashing, JWT, OAuth, cryptography |
| `aquilia[files]` | Async file I/O for static serving & uploads |
| `aquilia[multipart]` | Multipart form / file-upload parsing |
| `aquilia[redis]` | Redis cache & WebSocket adapter |
| `aquilia[mail]` | SMTP email provider |
| `aquilia[server]` | Gunicorn + Uvicorn workers for production |
| `aquilia[all]` | Everything above + MLOps stack |

## ⚡ Quick Start

Aquilia is a **workspace-first, batteries-included** framework. Projects are
scaffolded through the `aq` CLI — you don't write routing glue code by hand.

### 1 — Create a workspace

```bash
aq init workspace my-app          # full workspace (Dockerfile, config/, tests/, …)
cd my-app
```

This generates `workspace.py` (the workspace manifest), `config/base.yaml`,
and a starter page that serves `GET /` immediately.

### 2 — Add a module

```bash
aq add module users     # generates modules/users/{manifest,controllers,services,faults,models}.py
```

Each module has its own `manifest.py` that registers controllers, services,
middleware, and database config for that module only.

### 3 — Edit the generated controller

```python
# modules/users/controllers.py
from aquilia import Controller, GET, POST, RequestCtx, Response

class UsersController(Controller):
    prefix = "/users"
    tags  = ["users"]

    @GET("/")
    async def list_users(self, ctx: RequestCtx):
        return Response.json({"users": []})

    @POST("/")
    async def create_user(self, ctx: RequestCtx):
        body = await ctx.json()
        return Response.json({"created": body}, status=201)
```

### 4 — Run the development server

```bash
aq serve                # hot-reload dev server on http://127.0.0.1:8000
```

> **No manual route registration needed.** Controllers declared in a module's
> `manifest.py` are discovered and wired automatically.

## 🏛️ Core Pillars

### 1. The Manifest System
The `AppManifest` is the single source of truth for your application's requirements. It declares controllers, services, middleware, and database configurations. Aquilia uses this manifest to auto-generate:
- **Dockerfiles** tailored to your dependencies.
- **Kubernetes Manifests** for production-ready deployments.
- **OpenAPI Documentation** for your APIs.

### 2. Scoped Dependency Injection
Forget globals. Aquilia provides a hierarchical DI system:
- **Singleton**: Service lives for the app lifecycle.
- **App**: Scoped to the module level.
- **Request**: Fresh instance for every incoming HTTP request.

### 3. Structured Fault System
Aquilia treats errors as first-class data, not surprises:
- **Typed Faults**: Every error has a stable code, domain, severity, and recovery strategy.
- **12+ Domains**: CONFIG, REGISTRY, DI, ROUTING, FLOW, EFFECT, IO, SECURITY, SYSTEM, MODEL, CACHE, STORAGE, TASKS, TEMPLATE.
- **No Raw Exceptions**: All subsystems use `Fault` subclasses with metadata and serialization support.

### 4. Integrated MLOps
Aquilia treats machine learning as a first-class citizen:
- **Artifact Registry**: Version and track data/model assets.
- **Lineage Tracing**: Know exactly which code produced which model.
- **Shadow Deployments**: Test new models in production without affecting real traffic.

## 🛠️ Subsystems

Aquilia is composed of several deeply integrated subsystems:

| Subsystem | Description |
|-----------|-------------|
| **Aquilary** | Core registry and manifest loader |
| **Flow** | Typed routing and composable request pipelines |
| **Faults** | Structured error handling with 14 fault domains |
| **Auth** | JWT/session auth, MFA, OAuth, RBAC, guards |
| **DI** | Hierarchical dependency injection with lifecycle scopes |
| **Controller** | Aquilia-native controllers with filters, pagination, and typed routing |
| **Sessions** | Pluggable session backends (cookie, Redis, memory) |
| **Cache** | Multi-backend caching with middleware integration |
| **Storage** | Async file storage (local, S3, GCS, Azure, SFTP, memory) |
| **Tasks** | Background job system with priority queues and scheduling |
| **Templates** | Sandboxed Jinja2 with bytecode caching and HMAC integrity |
| **Models/ORM** | Async ORM with query builder, migrations, transactions |
| **Mail** | Multi-provider email (SMTP, SES, SendGrid) |
| **Admin** | Full-featured admin dashboard with audit logging |
| **MLOps** | Model registry, inference, monitoring, deployment |

## 🔒 Security

Aquilia takes security seriously across every subsystem:

- **Auth**: Argon2 password hashing, JWT with rotation, CSRF tokens, rate limiting
- **Templates**: Sandboxed Jinja2 execution, autoescape by default, HMAC-verified bytecode cache
- **Storage**: Path traversal protection, null byte rejection, path length limits
- **Tasks**: Registered-task-only execution (no arbitrary func_ref resolution)
- **Admin**: Role-based permissions, comprehensive audit logging, session security
- **ORM**: Parameterized queries, field name validation, SQL injection prevention

## 🧪 Testing

Run the full unit test suite (5,085 tests):

```bash
python -m pytest tests/ -v
```

Run with coverage:

```bash
python -m pytest tests/ --cov=aquilia --cov-report=html
```

## 🌐 Learn More

- **Documentation**: [https://aquilia.tubox.cloud](https://aquilia.tubox.cloud)
- **Architecture Guide**: [Architecture](https://aquilia.tubox.cloud/docs/architecture)
- **Quick Start**: [Get Started](https://aquilia.tubox.cloud/docs/quickstart)
- **Changelog**: [CHANGELOG.md](CHANGELOG.md)
- **Security**: [SECURITY.md](SECURITY.md)
- **Contributing**: [CONTRIBUTING.md](CONTRIBUTING.md)

---

<p align="center">Built with ❤️ by the Aquilia Team</p>
