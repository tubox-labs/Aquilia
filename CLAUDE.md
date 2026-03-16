# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Aquilia is an async-native, manifest-first Python web framework (Python 3.10+). It auto-discovers modules, wires DI, and generates infrastructure (Docker/K8s). The CLI is `aq`. Current version: `aquilia/_version.py`.

## Commands

```bash
# Install for development
pip install -e ".[dev]"
pip install -r requirements-dev.txt

# Run full test suite (~5,085 tests, pytest-asyncio in auto mode)
pytest tests/ -v --tb=short -q

# Run a single test
pytest tests/test_controller_system.py::TestMetadata::test_extract_controller_metadata -q

# Run tests with coverage
pytest tests/ --cov=aquilia --cov-report=term-missing

# Fail-fast test run
pytest tests/ -v -x

# Lint (CI authority — must pass before merge)
ruff check aquilia/ --output-format=github
ruff format --check aquilia/

# Auto-format
ruff format aquilia/

# Build distributables
python -m build && twine check dist/*

# Dev server (requires a workspace project)
aq serve
```

## Architecture

The boot sequence is: **Manifests → Aquilary → RuntimeRegistry → Controllers → ASGI**

1. **`workspace.py`** (user project root) — declares workspace orchestration via `Workspace`, `Module`, and integrations from `aquilia.config_builders`.
2. **`modules/*/manifest.py`** — each module's `AppManifest` declares its controllers, services, middleware, and models.
3. **`aquilia/entrypoint.py:create_app()`** — reads `workspace.py`, discovers module manifests via `importlib`, constructs `AquiliaServer`.
4. **`aquilia/server.py:AquiliaServer`** — builds `Aquilary` metadata from manifests, creates `RuntimeRegistry` (DI containers + service registration), compiles `ControllerRouter`, builds `MiddlewareStack`, and produces the ASGI app.
5. **`aquilia/asgi.py:ASGIAdapter`** — handles HTTP/WebSocket/lifespan protocols, performs sync route matching, creates request-scope DI containers and pooled `RequestCtx`, then executes the middleware + controller pipeline.

### Key Subsystem Locations

| Subsystem | Path | Purpose |
|-----------|------|---------|
| Aquilary | `aquilia/aquilary/` | Core manifest registry, metadata, runtime registry |
| Controllers | `aquilia/controller/` | Route decorators (`@GET`, `@POST`), router, OpenAPI generation |
| DI | `aquilia/di/` | Hierarchical dependency injection (singleton/app/request scopes) |
| Faults | `aquilia/faults/` | Structured error system — domains, engine, middleware |
| Flow | `aquilia/flow.py` | Typed routing and composable request pipelines |
| Auth | `aquilia/auth/` | JWT, sessions, OAuth, RBAC, guards, MFA |
| Models/ORM | `aquilia/models/`, `aquilia/db/` | Async ORM, query builder, migrations |
| Templates | `aquilia/templates/` | Sandboxed Jinja2 with bytecode caching |
| CLI | `aquilia/cli/` | `aq` command — init, add, serve, validate, inspect |
| MLOps | `aquilia/mlops/` | Model registry, inference, monitoring, deployment |
| Tasks | `aquilia/tasks/` | Background job system with priority queues |
| Storage | `aquilia/storage/` | Async file storage (local, S3, GCS, Azure, SFTP) |

### Controller Pattern

```python
from aquilia import Controller, GET, POST, RequestCtx, Response

class UsersController(Controller):
    prefix = "/users"
    tags = ["users"]

    @GET("/")
    async def list_users(self, ctx: RequestCtx):
        return Response.json({"users": []})
```

Controllers declared in a module's `manifest.py` are auto-discovered — no manual route registration.

## Critical Conventions

- **Structured faults, not raw exceptions.** All framework-domain errors must use `Fault` subclasses from `aquilia/faults/`. Never raise raw `ValueError`/`RuntimeError`/`TypeError`/`KeyError` for framework failures. Every fault needs a stable `code`, `message`, `domain`, and `severity`. See `aquilia/faults/domains.py` and examples in `aquilia/tasks/faults.py`, `aquilia/storage/base.py`, `aquilia/templates/faults.py`.

- **Manifest-first module boundaries.** `workspace.py` is orchestration metadata only. Component declarations (controllers, services, middleware) belong in `modules/*/manifest.py` via `AppManifest`. Avoid deprecated `Module.register_*` patterns.

- **DI scope discipline.** App and request lifecycles are explicit (`singleton`, `app`, `request`). Preserve scope semantics when adding providers.

- **Async-native.** Controllers and the entire request pipeline are async. Follow existing `Controller` + decorator style with `RequestCtx`.

- **Security invariants.** No `pickle.load()` on untrusted data. Always validate/normalize file paths (null bytes, `..` traversal). Use parameterized queries only. Templates use `SandboxedEnvironment` with autoescape. Background tasks resolve only from the registered task registry.

## Tooling Configuration

- **Ruff**: line-length 120, target Python 3.10. Rule sets: E, F, W, I, N, UP, B, SIM (with many specific ignores — see `pyproject.toml [tool.ruff.lint]`). `__init__.py` files allow F401 (re-exports).
- **pytest**: `asyncio_mode = "auto"`, test paths in `tests/`, files match `test_*.py`.
- **mypy**: Python 3.10, `warn_return_any = true`, `disallow_untyped_defs = false`.
- **CI**: Lint runs on Python 3.13. Tests run on Python 3.10–3.13 (Ubuntu), plus 3.13 on macOS and Windows. Lint must pass before tests run.

## Environment Variables

- `AQUILIA_WORKSPACE` — workspace root path (default: `/app`)
- `AQUILIA_ENV` — runtime mode: `dev`, `test`, or `prod` (default: `prod`)
