# Aquilia Documentation

This documentation is written from the current `aquilia/` source tree. It mirrors the framework modules instead of describing an idealized API. Each module directory explains the purpose of the package, the runtime flow, important public types, operational notes, and the implementation files that make up that area.

## How To Read This Documentation

1. Start with `architecture.md` to understand how workspace configuration, manifests, runtime bootstrapping, controllers, middleware, and responses fit together.
2. Use `module-index.md` when you need a fast map of the entire package surface.
3. Open `modules/<name>/README.md` for package-level detail.
4. Use `../examples/` for complete starter blueprints that combine the documented APIs into working project layouts.

## Framework Map

| Module | Role | Files | Public classes | Public functions |
| --- | --- | ---: | ---: | ---: |
| [admin](modules/admin/README.md) | Auto-detecting administration interface | 21 | 92 | 53 |
| [aquilary](modules/aquilary/README.md) | Manifest-driven registry and runtime graph | 10 | 29 | 9 |
| [artifacts](modules/artifacts/README.md) | Typed artifact envelopes and stores | 6 | 19 | 2 |
| [auth](modules/auth/README.md) | Authentication, authorization, clearance, token, and MFA system | 24 | 164 | 61 |
| [blueprints](modules/blueprints/README.md) | Model to world contracts | 9 | 41 | 10 |
| [cache](modules/cache/README.md) | Async cache abstraction with middleware integration | 14 | 27 | 10 |
| [cli](modules/cli/README.md) | Aquilia native command line tooling | 42 | 25 | 216 |
| [controller](modules/controller/README.md) | Controller, router, compiler, renderer, filter, pagination, and OpenAPI layer | 12 | 48 | 10 |
| [core](modules/core/README.md) | Core runtime and public package surface | 22 | 132 | 46 |
| [db](modules/db/README.md) | Database adapter configuration and engine facade | 9 | 15 | 4 |
| [debug](modules/debug/README.md) | Development error and welcome pages | 2 | 1 | 4 |
| [di](modules/di/README.md) | Scoped dependency injection container | 14 | 44 | 16 |
| [discovery](modules/discovery/README.md) | AST-based component discovery | 2 | 9 | 0 |
| [faults](modules/faults/README.md) | Structured error and recovery system | 12 | 127 | 23 |
| [filesystem](modules/filesystem/README.md) | Native async filesystem service | 14 | 25 | 22 |
| [http](modules/http/README.md) | Async HTTP client subsystem | 17 | 100 | 23 |
| [i18n](modules/i18n/README.md) | Internationalization and localization service | 11 | 28 | 26 |
| [integrations](modules/integrations/README.md) | Typed workspace integration configuration | 21 | 42 | 0 |
| [mail](modules/mail/README.md) | Async mail and provider abstraction | 14 | 41 | 9 |
| [middleware_ext](modules/middleware_ext/README.md) | Production middleware extensions | 8 | 22 | 7 |
| [mlops](modules/mlops/README.md) | Native model operations platform | 76 | 212 | 30 |
| [models](modules/models/README.md) | Pure Python async ORM and model compiler | 33 | 222 | 23 |
| [patterns](modules/patterns/README.md) | URL pattern grammar, compiler, and matcher | 21 | 35 | 18 |
| [providers](modules/providers/README.md) | Cloud provider deployment clients | 11 | 72 | 0 |
| [sessions](modules/sessions/README.md) | Session policies, stores, transports, and guards | 9 | 41 | 3 |
| [sockets](modules/sockets/README.md) | WebSocket controllers, runtime, guards, and adapters | 14 | 41 | 18 |
| [sqlite](modules/sqlite/README.md) | Native async SQLite support | 14 | 20 | 8 |
| [storage](modules/storage/README.md) | Async storage abstraction | 14 | 28 | 2 |
| [subsystems](modules/subsystems/README.md) | Subsystem initializer contracts | 3 | 4 | 0 |
| [tasks](modules/tasks/README.md) | Async background job system | 7 | 15 | 6 |
| [templates](modules/templates/README.md) | Sandboxed Jinja2 rendering subsystem | 15 | 32 | 35 |
| [testing](modules/testing/README.md) | Aquilia test utilities and fixtures | 14 | 25 | 30 |
| [typing](modules/typing/README.md) | Shared framework protocols and aliases | 10 | 37 | 0 |
| [utils](modules/utils/README.md) | Small shared utilities | 4 | 2 | 2 |
| [versioning](modules/versioning/README.md) | Epoch and semantic API versioning | 11 | 30 | 3 |

## Documentation Principles

These docs use the same split as the framework itself:

- `workspace.py` owns application structure, module pointers, and cross-cutting integrations.
- `modules/<name>/manifest.py` owns the internals of that module, including controllers, services, models, socket controllers, middleware, tasks, and fault settings.
- Controllers handle transport and request shape.
- Services hold business rules.
- Blueprints describe input and output contracts.
- Models describe persisted data.
- Integrations configure framework subsystems.

The examples follow that structure so new applications can grow without moving code later.
