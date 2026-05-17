# Aquilia Examples Coverage Report

Generated after auditing `aquilia/`, `aquilia/cli/`, `tests/`, and the existing `examples/` tree.

## Framework Architecture Findings

Aquilia is a workspace-first framework. Runtime startup is not based on handwritten route tables; it flows through `RuntimeConfig`, `AquiliaRuntime.configure().discover().bootstrap()`, `AquiliaServer`, Aquilary manifest loading, `RuntimeRegistry`, controller compilation, middleware setup, and the ASGI adapter.

The canonical project structure is:

- `workspace.py` owns workspace metadata, runtime options, module pointers, integration configuration, sessions, security, storage, tasks, database, telemetry, and i18n.
- `modules/<name>/manifest.py` owns `AppManifest` declarations for controllers, services, socket controllers, models, middleware, faults, templates, tasks, imports, and exports.
- `runtime.py` exports an ASGI `app` from `AquiliaRuntime`.
- The `aq` CLI is the public orchestration surface for scaffolding, validation, run/serve, discovery, manifests, database/model commands, cache/mail/i18n/admin/ws commands, artifacts, providers, deployment generation, tests, and MLOps commands.

## Existing Example Inventory

| Example | Current Coverage | Audit Result |
| --- | --- | --- |
| `rest_api_blueprint` | Controller, service, blueprint validation, manifest, workspace runtime | Good app-level REST starter, but README is minimal and no root-level pytest support. |
| `crud_app` | CRUD service, model class, blueprints, controller, database config | Good local starter, but persistence is intentionally in-memory and database/model CLI workflows are not demonstrated. |
| `auth_app` | Auth stores, password hashing, token issuance, protected routes | Useful but narrow; lacks auth config patterns, failure cases, and root-level pytest support. |
| `websocket_app` | Socket decorators, rooms, acknowledgements, presence | Useful socket starter; no generated client workflow or adapter variation. |
| `background_jobs` | `@task`, `TaskManager`, queues, scheduled task metadata | Useful task starter; no lifecycle startup pattern or persistent backend variation. |
| `multi_module_native_app` | Multi-module composition with integrations | Strong app-level reference, but documentation does not explain extension points in enough detail. |

## Verified Behavior

- Running `python -m pytest tests -q` inside each individual example app succeeds.
- Running `python -m pytest examples -q` from the repository root fails because tests import the top-level `modules` package and all starters use the same package name.
- Existing examples rely on real Aquilia APIs and are not pseudo-code.

## Missing Coverage

The current examples do not sufficiently cover:

- Runtime phase access and `AquiliaRuntime.from_workspace`.
- Python-native configuration with `AquilaConfig`, `Env`, and `.env_config()`.
- Low-level `ConfigLoader` behavior.
- DI providers, request scopes, and lifecycle cleanup.
- Middleware authoring and configured middleware chains.
- Cache service, decorators, and backend behavior.
- Storage registry and memory/local storage APIs.
- Native filesystem APIs.
- Native sqlite pool and transaction APIs.
- Mail provider APIs.
- Template engine APIs.
- Artifacts builder, memory store, filesystem store, and reader APIs.
- Signing APIs.
- Versioning resolvers and decorators.
- Fault engine and structured fault handling.
- Blueprints beyond app-level request DTOs.
- Patterns compiler/matcher.
- Request/response/data structure helpers.
- HTTP client APIs and mock transport patterns.
- CLI examples for every major command group.
- Deployment generator workflows.
- Admin setup/check/user CLI workflows.
- Provider and Render workflows.
- MLOps command workflows.
- Root-level executable test support for the examples directory.

## Implementation Plan

1. Preserve the six existing app starters, but make their tests root-runnable with package-qualified imports.
2. Add package markers where needed so `examples.<app>.modules...` imports are unambiguous.
3. Expand `examples/README.md` into the ecosystem index with setup, execution, CLI workflows, and module coverage.
4. Add a `reference_suite` with executable scripts and tests for subsystem-level APIs that are not naturally covered by app starters.
5. Add focused CLI workflow documentation using actual command names, flags, and behavior from `aquilia/cli/__main__.py` and command modules.
6. Validate with `python -m pytest examples -q` and targeted reference-suite execution.
