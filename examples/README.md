# Aquilia Examples

This directory is the practical reference for Aquilia. The examples follow the architecture implemented by the framework:

- `workspace.py` configures runtime, module pointers, integrations, security, sessions, storage, tasks, telemetry, and database settings.
- `modules/<name>/manifest.py` declares module internals through `AppManifest`.
- Controllers use Aquilia decorators such as `@GET`, `@POST`, `@Socket`, `@Event`, and delegate behavior to services.
- `runtime.py` exposes the ASGI `app` by bootstrapping `AquiliaRuntime`.
- Tests are executable from the repository root with `python -m pytest examples -q`.

## Setup

From the repository root:

```bash
python -m pip install -e ".[dev]"
python -m pytest examples -q
```

Run an app starter:

```bash
cd examples/rest_api_blueprint
python -m uvicorn runtime:app --reload --port 8000
```

Run the subsystem reference suite:

```bash
python -m examples.reference_suite.run_all
```

## App Starters

| Directory | Purpose | Primary APIs |
| --- | --- | --- |
| `rest_api_blueprint` | Product catalog REST API with validation, search, pagination-style parameters, and soft deletion. | `Workspace`, `Module`, `AppManifest`, `Controller`, `Response`, `Blueprint`, faults |
| `crud_app` | Project tracker CRUD workflow with a model declaration and repository-style service boundary. | Models, blueprints, controllers, database config |
| `auth_app` | Registration, password verification, token issuance, protected profile route, and admin guard route. | `AuthManager`, identity stores, `PasswordHasher`, `TokenManager`, guards |
| `websocket_app` | Chat rooms, connect/disconnect hooks, subscriptions, acknowledgements, and presence inspection. | `SocketController`, `@Socket`, `@Event`, `@Subscribe`, `Connection` |
| `background_jobs` | Controller-triggered jobs, queue metadata, retries, scheduled cleanup, and job status. | `TaskManager`, `@task`, `Priority`, schedules |
| `multi_module_native_app` | Full commerce-shaped workspace composing HTTP, auth, sessions, cache, storage, mail, i18n, tasks, sockets, templates, OpenAPI, versioning, and admin config. | Multi-module manifests, imports/exports, integrations |

## Subsystem References

`reference_suite` contains runnable examples for APIs that are not naturally visible in one app starter: DI, cache, storage, filesystem, sqlite, templates, mail providers, artifacts, signing, versioning, HTTP mock transport, patterns, and fault handling.

## CLI Workflows

See `CLI_WORKFLOWS.md` for command examples derived from `aquilia/cli/__main__.py` and command modules.

## Coverage Reports

- `COVERAGE_REPORT.md` records the pre-implementation audit and missing coverage.
- `MODULE_COVERAGE.md` maps source modules to examples and extension ideas.

## Common Pitfalls

- Run app-local commands from the app directory because `AquiliaRuntime` discovers `workspace.py` and `modules/` relative to the workspace root.
- Prefer `python -m uvicorn runtime:app` or `aq run` inside a starter.
- Keep workspace-level component pointers in `workspace.py`; declare controllers, services, sockets, models, middleware, and tasks in each module's `manifest.py`.
- Memory stores are intentional for local executability. Replace them with configured providers for durable production behavior.
