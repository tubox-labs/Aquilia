# Aquilia Documentation

This documentation is generated from the current `aquilia/` source tree and the live `aq` Click command tree. It documents implemented behavior: source files, public APIs, configuration objects, runtime lifecycle, command arguments/options, extension points, examples, edge cases, and troubleshooting paths.

## Start Here

1. [Architecture](architecture.md) explains the framework boot path and request flow.
2. [Installation](installation.md) lists requirements, extras, and setup flow from `pyproject.toml`.
3. [Configuration](configuration.md) documents `Workspace`, `Module`, `Integration`, `AquilaConfig`, dotenv, and `AQ_` environment overlays.
4. [CLI Reference](cli-reference.md) is the complete mounted `aq` command reference.
5. [Runtime Lifecycle](runtime-lifecycle.md) traces ASGI startup, request execution, and shutdown.
6. [Developer Guide](developer-guide.md) covers modules, providers, middleware, hooks, services, tests, and extension points.
7. [Examples](examples.md) indexes checked examples under `examples/`.
8. [Coverage Report](documentation-coverage-report.md) records what was audited and rebuilt.

## Module Map

| Module | Role | Files | Classes | Functions | API | CLI |
| --- | --- | ---: | ---: | ---: | --- | --- |
| [core](modules/core/README.md) | Root framework runtime files: ASGI adapter, server, runtime bootstrap, config, pyconfig, request/response, middleware, lifecycle, signing, effects, dotenv, uploads, and data structures. | 22 | 132 | 46 | [API](modules/core/api-reference.md) | [CLI](modules/core/cli-reference.md) |
| [admin](modules/admin/README.md) | Built-in administration interface, audit log, permissions, dashboards, model CRUD, operational pages, and admin security. | 21 | 92 | 53 | [API](modules/admin/api-reference.md) | [CLI](modules/admin/cli-reference.md) |
| [aquilary](modules/aquilary/README.md) | Manifest registry, validation, dependency graph, route table compilation metadata, fingerprinting, and runtime registry construction. | 10 | 29 | 9 | [API](modules/aquilary/api-reference.md) | [CLI](modules/aquilary/cli-reference.md) |
| [artifacts](modules/artifacts/README.md) | Typed artifact envelopes, artifact kinds, integrity metadata, readers, builders, and memory/filesystem stores. | 6 | 19 | 2 | [API](modules/artifacts/api-reference.md) | [CLI](modules/artifacts/cli-reference.md) |
| [auth](modules/auth/README.md) | Authentication, authorization, identity stores, token management, guards, clearance rules, MFA, OAuth, and session integration. | 24 | 164 | 61 | [API](modules/auth/api-reference.md) | [CLI](modules/auth/cli-reference.md) |
| [blueprints](modules/blueprints/README.md) | Model-to-world contracts for request validation, response rendering, schema generation, facets, projections, and lenses. | 9 | 41 | 10 | [API](modules/blueprints/api-reference.md) | [CLI](modules/blueprints/cli-reference.md) |
| [cache](modules/cache/README.md) | Async cache abstraction with memory, Redis, composite, null backends, serializers, decorators, DI providers, and HTTP caching middleware. | 14 | 27 | 10 | [API](modules/cache/api-reference.md) | [CLI](modules/cache/cli-reference.md) |
| [cli](modules/cli/README.md) | The `aq` command line interface, workspace/module generators, deployment generators, diagnostics, validation, inspection, and subsystem commands. | 42 | 25 | 216 | [API](modules/cli/api-reference.md) | [CLI](modules/cli/cli-reference.md) |
| [controller](modules/controller/README.md) | Controller base class, route decorators, compiler, router, execution engine, renderers, filters, pagination, and OpenAPI generation. | 12 | 48 | 10 | [API](modules/controller/api-reference.md) | [CLI](modules/controller/cli-reference.md) |
| [db](modules/db/README.md) | Async database engine facade, typed database configs, adapters for SQLite/Postgres/MySQL/Oracle, and schema introspection helpers. | 9 | 15 | 4 | [API](modules/db/api-reference.md) | [CLI](modules/db/cli-reference.md) |
| [debug](modules/debug/README.md) | Development-mode welcome, HTTP error, version error, and exception pages. | 2 | 1 | 4 | [API](modules/debug/api-reference.md) | [CLI](modules/debug/cli-reference.md) |
| [di](modules/di/README.md) | Scoped dependency injection container, providers, request DAG, decorators, lifecycle disposal, diagnostics, scopes, and testing utilities. | 14 | 44 | 16 | [API](modules/di/api-reference.md) | [CLI](modules/di/cli-reference.md) |
| [discovery](modules/discovery/README.md) | AST-based component discovery and manifest synchronization support. | 2 | 9 | 0 | [API](modules/discovery/api-reference.md) | [CLI](modules/discovery/cli-reference.md) |
| [faults](modules/faults/README.md) | Structured fault taxonomy, domains, handlers, middleware, response mapping, and subsystem patch integrations. | 12 | 127 | 23 | [API](modules/faults/api-reference.md) | [CLI](modules/faults/cli-reference.md) |
| [filesystem](modules/filesystem/README.md) | Native async filesystem API, file handles, directory operations, streaming, locks, temporary files, path security, metrics, and service facade. | 14 | 25 | 22 | [API](modules/filesystem/api-reference.md) | [CLI](modules/filesystem/cli-reference.md) |
| [http](modules/http/README.md) | Native async HTTP client, request/response builders, sessions, retry policies, auth interceptors, cookies, middleware, streaming, and transport. | 17 | 100 | 23 | [API](modules/http/api-reference.md) | [CLI](modules/http/cli-reference.md) |
| [i18n](modules/i18n/README.md) | Internationalization service, locale negotiation, catalogs, formatting, plural rules, lazy strings, middleware, CLI helpers, and template integration. | 11 | 28 | 26 | [API](modules/i18n/api-reference.md) | [CLI](modules/i18n/cli-reference.md) |
| [integrations](modules/integrations/README.md) | Typed workspace integration configuration objects consumed by `Workspace.integrate(...)` and server setup. | 21 | 42 | 0 | [API](modules/integrations/api-reference.md) | [CLI](modules/integrations/cli-reference.md) |
| [mail](modules/mail/README.md) | Async mail subsystem with message classes, config blueprints, providers, DI registration, templates, faults, and convenience send APIs. | 14 | 41 | 9 | [API](modules/mail/api-reference.md) | [CLI](modules/mail/cli-reference.md) |
| [middleware_ext](modules/middleware_ext/README.md) | Extended production middleware for security, CORS/CSP/CSRF/HSTS, static files, rate limits, sessions, request scopes, effects, and logging. | 8 | 22 | 7 | [API](modules/middleware_ext/api-reference.md) | [CLI](modules/middleware_ext/cli-reference.md) |
| [mlops](modules/mlops/README.md) | Model operations platform: modelpacks, serving, registries, runtimes, orchestration, observability, rollout, optimization, plugins, scheduler, and security. | 76 | 212 | 30 | [API](modules/mlops/api-reference.md) | [CLI](modules/mlops/cli-reference.md) |
| [models](modules/models/README.md) | Pure-Python async ORM, fields, query builder, managers, SQL builders, migrations, schema snapshots, legacy AMDL parser/runtime, and transactions. | 33 | 222 | 23 | [API](modules/models/api-reference.md) | [CLI](modules/models/cli-reference.md) |
| [patterns](modules/patterns/README.md) | URL pattern grammar, parser, compiler, matcher, type/validator/transform registries, specificity scoring, OpenAPI conversion, diagnostics, autofix, and LSP metadata. | 21 | 35 | 18 | [API](modules/patterns/api-reference.md) | [CLI](modules/patterns/cli-reference.md) |
| [providers](modules/providers/README.md) | Cloud provider clients and deployment tooling, currently focused on the Render provider and encrypted credential store. | 11 | 72 | 0 | [API](modules/providers/api-reference.md) | [CLI](modules/providers/cli-reference.md) |
| [sessions](modules/sessions/README.md) | Session IDs, policies, stores, transports, engine, decorators, typed session state, and session faults. | 9 | 41 | 3 | [API](modules/sessions/api-reference.md) | [CLI](modules/sessions/cli-reference.md) |
| [sockets](modules/sockets/README.md) | WebSocket decorators, controllers, runtime, connection state, guards, middleware, message envelopes, compile metadata, and in-memory/Redis adapters. | 14 | 41 | 18 | [API](modules/sockets/api-reference.md) | [CLI](modules/sockets/cli-reference.md) |
| [sqlite](modules/sqlite/README.md) | Native async SQLite compatibility layer, connection pool, transactions, cursors, rows, PRAGMAs, backup, metrics, and errors. | 14 | 20 | 8 | [API](modules/sqlite/api-reference.md) | [CLI](modules/sqlite/cli-reference.md) |
| [storage](modules/storage/README.md) | Async storage abstraction with local, memory, S3, GCS, Azure, SFTP, composite backends, registry, configs, effects, and lifecycle subsystem. | 14 | 28 | 2 | [API](modules/storage/api-reference.md) | [CLI](modules/storage/cli-reference.md) |
| [subsystems](modules/subsystems/README.md) | Subsystem initializer contracts and boot context abstractions for decomposing server setup. | 3 | 4 | 0 | [API](modules/subsystems/api-reference.md) | [CLI](modules/subsystems/cli-reference.md) |
| [tasks](modules/tasks/README.md) | Async background job manager, task decorator registry, jobs, schedules, memory backend, worker loops, retries, and faults. | 7 | 15 | 6 | [API](modules/tasks/api-reference.md) | [CLI](modules/tasks/cli-reference.md) |
| [templates](modules/templates/README.md) | Jinja2 template engine, loaders, manager, middleware, bytecode cache, sandbox, DI providers, manifest/session/auth/i18n integration, and template CLI helpers. | 15 | 32 | 35 | [API](modules/templates/api-reference.md) | [CLI](modules/templates/cli-reference.md) |
| [testing](modules/testing/README.md) | Test client/server, test cases, fixtures, auth/cache/mail/fault/effect/DI test helpers, config overrides, and request factory utilities. | 14 | 25 | 30 | [API](modules/testing/api-reference.md) | [CLI](modules/testing/cli-reference.md) |
| [typing](modules/typing/README.md) | Shared protocols, typed dictionaries, aliases, and interface contracts for ASGI, containers, config, controllers, effects, manifests, middleware, and request state. | 10 | 37 | 0 | [API](modules/typing/api-reference.md) | [CLI](modules/typing/cli-reference.md) |
| [utils](modules/utils/README.md) | Small shared helpers for URL joining, data objects, and package scanning. | 4 | 2 | 2 | [API](modules/utils/api-reference.md) | [CLI](modules/utils/cli-reference.md) |
| [versioning](modules/versioning/README.md) | API version parsing, resolvers, decorators, negotiation, graph, sunset policy/enforcement, middleware, and route registration integration. | 11 | 30 | 3 | [API](modules/versioning/api-reference.md) | [CLI](modules/versioning/cli-reference.md) |
