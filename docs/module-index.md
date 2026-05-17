# Aquilia Module Index

Every top-level package under `aquilia/` has a module documentation directory. Root framework files are grouped under `core`.

| Module | Role | Files | Lines | Classes | Functions | Constants | Docs |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| `core` | Root framework runtime files: ASGI adapter, server, runtime bootstrap, config, pyconfig, request/response, middleware, lifecycle, signing, effects, dotenv, uploads, and data structures. | 22 | 27322 | 132 | 46 | 63 | [README](modules/core/README.md) |
| `admin` | Built-in administration interface, audit log, permissions, dashboards, model CRUD, operational pages, and admin security. | 21 | 26075 | 92 | 53 | 22 | [README](modules/admin/README.md) |
| `aquilary` | Manifest registry, validation, dependency graph, route table compilation metadata, fingerprinting, and runtime registry construction. | 10 | 4676 | 29 | 9 | 1 | [README](modules/aquilary/README.md) |
| `artifacts` | Typed artifact envelopes, artifact kinds, integrity metadata, readers, builders, and memory/filesystem stores. | 6 | 1859 | 19 | 2 | 2 | [README](modules/artifacts/README.md) |
| `auth` | Authentication, authorization, identity stores, token management, guards, clearance rules, MFA, OAuth, and session integration. | 24 | 12774 | 164 | 61 | 19 | [README](modules/auth/README.md) |
| `blueprints` | Model-to-world contracts for request validation, response rendering, schema generation, facets, projections, and lenses. | 9 | 4728 | 41 | 10 | 15 | [README](modules/blueprints/README.md) |
| `cache` | Async cache abstraction with memory, Redis, composite, null backends, serializers, decorators, DI providers, and HTTP caching middleware. | 14 | 3813 | 27 | 10 | 5 | [README](modules/cache/README.md) |
| `cli` | The `aq` command line interface, workspace/module generators, deployment generators, diagnostics, validation, inspection, and subsystem commands. | 42 | 23184 | 25 | 216 | 54 | [README](modules/cli/README.md) |
| `controller` | Controller base class, route decorators, compiler, router, execution engine, renderers, filters, pagination, and OpenAPI generation. | 12 | 7813 | 48 | 10 | 21 | [README](modules/controller/README.md) |
| `db` | Async database engine facade, typed database configs, adapters for SQLite/Postgres/MySQL/Oracle, and schema introspection helpers. | 9 | 3266 | 15 | 4 | 16 | [README](modules/db/README.md) |
| `debug` | Development-mode welcome, HTTP error, version error, and exception pages. | 2 | 1300 | 1 | 4 | 6 | [README](modules/debug/README.md) |
| `di` | Scoped dependency injection container, providers, request DAG, decorators, lifecycle disposal, diagnostics, scopes, and testing utilities. | 14 | 4800 | 44 | 16 | 8 | [README](modules/di/README.md) |
| `discovery` | AST-based component discovery and manifest synchronization support. | 2 | 747 | 9 | 0 | 1 | [README](modules/discovery/README.md) |
| `faults` | Structured fault taxonomy, domains, handlers, middleware, response mapping, and subsystem patch integrations. | 12 | 4801 | 127 | 23 | 4 | [README](modules/faults/README.md) |
| `filesystem` | Native async filesystem API, file handles, directory operations, streaming, locks, temporary files, path security, metrics, and service facade. | 14 | 4317 | 25 | 22 | 20 | [README](modules/filesystem/README.md) |
| `http` | Native async HTTP client, request/response builders, sessions, retry policies, auth interceptors, cookies, middleware, streaming, and transport. | 17 | 8549 | 100 | 23 | 12 | [README](modules/http/README.md) |
| `i18n` | Internationalization service, locale negotiation, catalogs, formatting, plural rules, lazy strings, middleware, CLI helpers, and template integration. | 11 | 4190 | 28 | 26 | 12 | [README](modules/i18n/README.md) |
| `integrations` | Typed workspace integration configuration objects consumed by `Workspace.integrate(...)` and server setup. | 21 | 2978 | 42 | 0 | 4 | [README](modules/integrations/README.md) |
| `mail` | Async mail subsystem with message classes, config blueprints, providers, DI registration, templates, faults, and convenience send APIs. | 14 | 4599 | 41 | 9 | 14 | [README](modules/mail/README.md) |
| `middleware_ext` | Extended production middleware for security, CORS/CSP/CSRF/HSTS, static files, rate limits, sessions, request scopes, effects, and logging. | 8 | 3274 | 22 | 7 | 7 | [README](modules/middleware_ext/README.md) |
| `mlops` | Model operations platform: modelpacks, serving, registries, runtimes, orchestration, observability, rollout, optimization, plugins, scheduler, and security. | 76 | 15885 | 212 | 30 | 24 | [README](modules/mlops/README.md) |
| `models` | Pure-Python async ORM, fields, query builder, managers, SQL builders, migrations, schema snapshots, legacy AMDL parser/runtime, and transactions. | 33 | 17845 | 222 | 23 | 65 | [README](modules/models/README.md) |
| `patterns` | URL pattern grammar, parser, compiler, matcher, type/validator/transform registries, specificity scoring, OpenAPI conversion, diagnostics, autofix, and LSP metadata. | 21 | 3246 | 35 | 18 | 13 | [README](modules/patterns/README.md) |
| `providers` | Cloud provider clients and deployment tooling, currently focused on the Render provider and encrypted credential store. | 11 | 5882 | 72 | 0 | 42 | [README](modules/providers/README.md) |
| `sessions` | Session IDs, policies, stores, transports, engine, decorators, typed session state, and session faults. | 9 | 3159 | 41 | 3 | 9 | [README](modules/sessions/README.md) |
| `sockets` | WebSocket decorators, controllers, runtime, connection state, guards, middleware, message envelopes, compile metadata, and in-memory/Redis adapters. | 14 | 3687 | 41 | 18 | 3 | [README](modules/sockets/README.md) |
| `sqlite` | Native async SQLite compatibility layer, connection pool, transactions, cursors, rows, PRAGMAs, backup, metrics, and errors. | 14 | 2672 | 20 | 8 | 20 | [README](modules/sqlite/README.md) |
| `storage` | Async storage abstraction with local, memory, S3, GCS, Azure, SFTP, composite backends, registry, configs, effects, and lifecycle subsystem. | 14 | 3166 | 28 | 2 | 5 | [README](modules/storage/README.md) |
| `subsystems` | Subsystem initializer contracts and boot context abstractions for decomposing server setup. | 3 | 563 | 4 | 0 | 1 | [README](modules/subsystems/README.md) |
| `tasks` | Async background job manager, task decorator registry, jobs, schedules, memory backend, worker loops, retries, and faults. | 7 | 1802 | 15 | 6 | 2 | [README](modules/tasks/README.md) |
| `templates` | Jinja2 template engine, loaders, manager, middleware, bytecode cache, sandbox, DI providers, manifest/session/auth/i18n integration, and template CLI helpers. | 15 | 4409 | 32 | 35 | 3 | [README](modules/templates/README.md) |
| `testing` | Test client/server, test cases, fixtures, auth/cache/mail/fault/effect/DI test helpers, config overrides, and request factory utilities. | 14 | 3874 | 25 | 30 | 3 | [README](modules/testing/README.md) |
| `typing` | Shared protocols, typed dictionaries, aliases, and interface contracts for ASGI, containers, config, controllers, effects, manifests, middleware, and request state. | 10 | 593 | 37 | 0 | 4 | [README](modules/typing/README.md) |
| `utils` | Small shared helpers for URL joining, data objects, and package scanning. | 4 | 326 | 2 | 2 | 1 | [README](modules/utils/README.md) |
| `versioning` | API version parsing, resolvers, decorators, negotiation, graph, sunset policy/enforcement, middleware, and route registration integration. | 11 | 2844 | 30 | 3 | 6 | [README](modules/versioning/README.md) |
