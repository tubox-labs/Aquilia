# Changelog

All notable changes to the Aquilia framework. This project adheres to
[Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [1.1.2] — 2026-06-12 — Crimson Gale

### Bug Fixes

- Fixed `name 'Entry' is not defined` server crash caused by nested `@dataclass` scoping
  in `Integration.middleware.Entry`. Calls now use the fully-qualified path.

- Fixed generated workspace missing `Integration` import. Commit `ca37a5e` removed
  `Integration` from imports but the template body still used it. The import is now
  restored in both full and minimal templates.

- Fixed `.env` values never reflected in workspace config. Three related bugs:

    1. `Workspace.to_dict()` read `os.environ.get("AQ_ENV", "dev")` before dotenv was
       loaded, so `.env` values were invisible.
    2. `.env.example` appeared after `.env` in the search path and `merge_values.update()`
       clobbered real `.env` values with template defaults.
    3. `ConfigLoader._load_pyconfig_file()` had the same order-of-operations bug.

- Fixed `AQ_ENV`/`AQUILIA_ENV` environment variable inconsistency. `Workspace.to_dict()`
  only checked `AQ_ENV` but the runtime sets `AQUILIA_ENV`. Both are now checked with
  `AQUILIA_ENV` taking precedence.

- Removed template files (`.env.example`, `.env.defaults`, `.env.default`) from dotenv
  search paths. These are templates meant to be copied, not config sources.

- Fixed `.env.example` using wrong variable names (`AQUILIA_MODE`, `AQUILIA_HOST`,
  `SECRET_KEY` instead of `AQ_ENV`, `AQ_HOST`, `AQ_SECRET_KEY`).

---

## [1.1.1] — 2026-06-09 — Sea Serpent

### Removed

- Deleted `aquilia/config_builders.py` — the 5,420-line god-file has been extracted.

### Changed

- Extracted `Workspace`, `Module`, `RuntimeConfig`, `ModuleConfig`, and `AuthConfig`
  into a clean `aquilia/workspace.py` module from `config_builders.py`.

- `Workspace.integrate()` accepts `aquilia.integrations.*` typed dataclasses directly
  via the `IntegrationConfig` protocol.

- `Workspace.i18n()`, `Workspace.tasks()`, and `Workspace.storage()` convenience methods
  now use `I18nIntegration`, `TasksIntegration`, and `StorageIntegration` typed
  dataclasses internally instead of legacy `Integration.*` static methods.

- Moved legacy `Integration` class to `aquilia/integrations/_legacy.py` for backward
  compatibility. Existing code using `Integration.mail(...)`, `Integration.admin(...)`,
  etc. continues to work.

- Updated all example workspace files to use typed integration dataclasses from
  `aquilia.integrations` instead of the `Integration` static API.

- Updated all test imports to use `aquilia.workspace` and `aquilia.integrations` directly.

### Bug Fixes

- **Thread safety**: Replaced `bool` flag `_dotenv_lock` with `threading.RLock()` in
  `pyconfig.py` — concurrent dotenv loading no longer corrupts `os.environ`.

- **I18n default values**: Fixed broken `dataclasses.field()` usage on plain class
  attributes in `AquilaConfig.I18n` (replaced with plain lists).

- **Catalog format consistency**: `ConfigLoader.get_i18n_config()` now defaults to
  `"json"` (was `"surp"`), matching `AquilaConfig.I18n.catalog_format`.

- **`for_env()` recursion**: `AquilaConfig.for_env()` now recursively searches all
  subclass depths (was limited to 2 levels).

- **Config boilerplate**: Added `ConfigLoader.get_subsystem_config()` generic method;
  10 of 12 subsystem config getters are now thin wrappers, cutting boilerplate by ~80%.

- **Config package**: Created `aquilia/config/` package as a canonical re-export hub.
  `from aquilia.config import Workspace, Module, AquilaConfig, Env, Secret` works.

- **pyproject.toml**: Removed `psutil>=7.2.2` from core dependencies (now optional).
  Removed empty `templates`, `db`, and `files` extras. Fixed stale MLOps comment.

---

## [1.1.0] — 2026-06-08 — Black Pearl

### Removed

- Removed `aquilia/mlops/` in its entirety.
- Removed duplicate `aquilia/aquilia_mcp/` package (canonical is `aquilia.mcp`).
- Removed AMDL DSL: parser, AST nodes, `__init__old.py`, `AMDLParseFault`.
- Removed `aquilia/patterns/lsp/` Language Server Protocol server.

### Changed

- URL pattern documentation: guillemet delimiters replaced with brace syntax `{id:int}`.
- Moved `ruff` from dependencies to `[dev]` optional extra.
- Moved `asyncpg` from dependencies to new `[postgres]` optional extra.
- Fixed broken GitHub URLs (axiomchronicles → tubox-labs).

### Added

- `aquilia/sse/` — Server-Sent Events subsystem: `SSEEvent`, `SSEResponse`, json/text stream
  helpers. Supports long-lived event streams from controllers.

- `aquilia/otel/` — OpenTelemetry integration: `OTelConfig`, `OTelMiddleware`, no-op
  fallback when OpenTelemetry SDK is not installed. Available via `[otel]` extra.

- `aquilia/controller/validation.py` — `@validate_body(BlueprintClass)` decorator.
  Applies to controller methods; on success injects a validated `body: dict` kwarg;
  on failure returns HTTP 422 with structured errors.

- `aquilia/sqlite/_config.py` — `SqlitePoolConfig` with full parameter surface including
  pool size, timeout, journal mode, synchronous mode, and WAL settings.

- New `[postgres]` optional extra for async PostgreSQL support.

- New `[otel]` optional extra for OpenTelemetry distributed tracing.

### Bug Fixes

- Removed `aiosqlite` as a core framework dependency; now available only via
  `[sqlite-compat]` optional extra.

---

## [1.0.5] — 2026-06-04 — Jolly Roger

### Added

- Production-grade MCP server under `aquilia.mcp` with JSON-RPC stdio support,
  tool/resource/prompt registries, persistent repository indexing, installer helpers,
  and canonical `python -m aquilia.mcp` entrypoints.

- MCP tools and prompts for framework API discovery, bootstrap/runtime explanation,
  workspace and module scaffolding guidance, manifest-plan validation, integration
  recommendations, deprecation guarding, CLI discovery, example lookup, and agent
  prompt generation.

- Practical MCP documentation and bootstrap configs for Claude, Codex, and Gemini CLI
  under `docs/mcp/` and `examples/mcp_bootstrap/`.

### Changed

- Replaced Crous/Crousr binary serialization stack with **Surp** across runtime request
  and response helpers, compiled artifacts, Aquilary registry loading, admin audit
  persistence, i18n catalogs, model snapshots, WebSocket artifacts, template cache
  metadata, analytics cache, provider credential stores, and CLI workflows.

- Renamed public binary payload helpers and decorators from Crous terminology to Surp
  terminology: `Request.surp()`, `Response.surp()`, `requires_surp`, `SurpCatalog`.

- Updated generated artifact extensions and documentation from `.crous` to `.surp` while
  preserving JSON fallback paths.

- Updated package dependencies to install `surp` instead of `crousr` and `crous-native`.

- Allowed `aq i18n init --format surp` to create Surp-backed starter catalogs.

- Rewired `aq mcp` commands to the canonical `aquilia.mcp` package.

### Removed

- Removed Crous-specific imports, native backend probing, API names, file extensions,
  and request/response tests.

### Security

- Hardened MCP resource access and diagnostics with read-only defaults, path traversal
  and null-byte rejection, binary-file guards, bounded stdio frames, strict tool input
  validation, and secret redaction in doctor output.

### Testing

- Added Surp request/response coverage and updated admin, i18n, provider, regression,
  and security tests for Surp-backed behavior.
- Added MCP protocol, stdio transport, indexer/search, tool, prompt, installer, CLI,
  and end-to-end stdio session coverage.
- Verified migration with bytecode compilation, focused tests, and a full test suite run.

---

## [1.0.4] — 2026-05-17

### Removed

- Removed the React-style `aquilia/build` package and the `aq build` command.
- Removed automatic build-gating from `aq run`, `aq serve`, and `aq deploy`; runtime
  and deploy generation now use native workspace loading and live introspection.
- Removed the Admin Build page, `/admin/build/` route, sidebar/search links, and
  `AdminModules.build` configuration surface.

### Changed

- `aq compile` now writes explicit artifacts through `WorkspaceCompiler` without depending
  on a build pipeline.
- `aq freeze` now creates an integrity snapshot for generated artifacts under `artifacts/`.
- Deployment Makefile generation now calls `python -m aquilia.cli compile`.

### Bug Fixes

- Isolated independent SQLite `:memory:` pools while preserving shared state across
  connections within the same pool.

### Documentation

- Updated CLI, deployment, admin, release, and getting-started docs to reflect the
  native Python runtime structure.

---

## [1.0.1] — 2026-03-08 — Security Audit Release

### Comprehensive Framework Audit (Phases 1–15)

A 15-phase security and hardening audit covering every major subsystem of the framework.

#### Core & Server (Phases 1–6)

- Full security audit of `aquilia/server.py`, `aquilia/engine.py`, `aquilia/flow.py`,
  `aquilia/middleware.py`.
- Hardened `aquilia/request.py` and `aquilia/response.py` against header injection
  and content-type attacks.
- Hardened `aquilia/asgi.py` ASGI lifecycle handling.

#### Dependency Injection (Phase 7)

- Security audit of `aquilia/di/` — scope isolation, cycle detection, provider resolution.
- Fixed potential DI graph leaks across request boundaries.

#### Auth System (Phase 8)

- Comprehensive audit of `aquilia/auth/` — JWT, session, MFA, OAuth, RBAC.
- Hardened token lifecycle, password hashing (Argon2), CSRF protection.
- Fixed clearance level escalation edge cases in `aquilia/auth/clearance.py`.

#### Controller System (Phase 9)

- Audit of `aquilia/controller/` — routing, filters, pagination, factory.
- Secured filter/pagination against injection and overflow attacks.

#### Sessions (Phase 10)

- Audit of `aquilia/sessions/` — store, transport, engine.
- Hardened session fixation protection and cookie security flags.

#### Blueprints (Phase 11)

- Audit of `aquilia/blueprints/` — annotations, facets, core, integration.
- Secured blueprint registration against namespace collisions.

#### ORM & Models (Phase 12)

- Comprehensive audit of `aquilia/models/` — query builder, fields, transactions,
  migrations.
- Parameterized all raw SQL paths, field name validation, safe deletion cascades.
- Protected against SQL injection in expression engine and lookup system.

#### Admin Module (Phase 13)

- Deep security audit of `aquilia/admin/` — controller, site, registry, permissions,
  inlines, templates.
- Created `aquilia/admin/security.py` with CSRF, rate-limiting, input validation, and
  audit logging.
- Role-based permission enforcement across all admin endpoints.

#### Admin Fault Migration & Subsystem Integration (Phase 14)

- Replaced all raw exceptions in `aquilia/admin/` with structured `Fault` subclasses.
- Created `aquilia/admin/faults.py` with `ADMIN_DOMAIN` and 7 fault classes.
- Created `aquilia/admin/subsystems.py` integrating cache/effects/tasks/flow/lifecycle.

#### Tasks, Storage & Templates — Fault Migration & Security (Phase 15)

- **Tasks**: Created `aquilia/tasks/faults.py` with `TASKS_DOMAIN`, `TaskScheduleFault`,
  `TaskNotBoundFault`, `TaskEnqueueFault`, `TaskResolutionFault`.
- **Storage**: Converted `StorageError` hierarchy to inherit from `Fault` with
  `STORAGE_DOMAIN`; added `StorageIOFault`, `StorageConfigFault`.
- **Templates**: Created `aquilia/templates/faults.py` with `TEMPLATE_DOMAIN`,
  `TemplateEngineUnavailableFault`, `TemplateCacheIntegrityFault`.
- **Fault core**: Registered 3 new standard domains — `STORAGE`, `TASKS`, `TEMPLATE`.

### Security Fixes

| Severity | Issue | Fix |
| -------- | ----- | --- |
| CRITICAL | Unsafe `pickle.load()` deserialization in bytecode cache and template manager | Replaced with HMAC-verified JSON (SHA-256); schema version bumped from 1.0 to 1.1 |
| HIGH | Path traversal in storage path normalization | Rejects null bytes, `..` segments, paths >1024 chars |
| HIGH | Arbitrary code execution via task `func_ref` resolution | Task resolution now uses registered `@task` allowlist only |
| MEDIUM | Regex-based HTML sanitization bypass in templates | Added deprecation warning on `sanitize_html()` |
| MEDIUM | SQL injection in ORM expression engine and lookups | Full parameterization and field name validation |
| MEDIUM | Session fixation and insecure cookie defaults | Added session fixation protection and secure flags |
| LOW | Auth token rotation edge cases | Hardened rotation and CSRF double-submit validation |

### Testing

- 5,085 total tests passing, 0 failures.
- `tests/test_phase14_faults_subsystems.py` — 118 tests (admin faults + subsystem integration).
- `tests/test_phase15_faults_security.py` — 120 tests (fault migration + security audit).
- `tests/test_admin_security.py` — admin security regression tests.
- `tests/test_blueprint_security.py` — blueprint security tests.
- `tests/test_orm_security.py` — ORM injection and security tests.
- `tests/test_session_security.py` — session security tests.
- `tests/test_integration_wiring.py` — cross-subsystem integration tests.

---

## [1.0.0] — Initial Release

### Core Framework

- **Manifest-First Architecture**: `AppManifest` declares controllers, services, models,
  and middleware per module. Auto-discovery via `importlib` with `PackageScanner`.

- **Scoped Dependency Injection**: Hierarchical DI with singleton, app, and request scopes.
  `Inject` annotations, factory providers, lifecycle hooks, and `RuntimeRegistry`.

- **Async-Native Core**: Full async request pipeline built on Uvicorn and ASGI.
  `AquiliaServer` → `Aquilary` metadata → `ControllerRouter` → `ASGIAdapter`.

- **Controller System**: `Controller` base class with `@GET`, `@POST`, `@PATCH`, `@DELETE`,
  `@PUT` decorators. URL path parameters, query parameter extraction, `RequestCtx`
  injection, and `Response` helpers.

### Subsystems

- **Flow**: Typed routing and composable request pipelines with middleware chaining.
- **Faults**: Structured error system with `Fault` subclasses, `FaultDomain`,
  `FaultEngine`, and default fault handlers.
- **Auth**: JWT tokens, session management, password hashing (Argon2), OAuth clients,
  RBAC guards, MFA support, and clearance levels.
- **Models/ORM**: Async ORM with Model field declarations, query builder, transaction
  management, migration system (`makemigrations`, `migrate`, `sqlmigrate`, `inspectdb`).
- **Templates**: Sandboxed Jinja2 with bytecode caching, `TemplateEngine`,
  `TemplateLoader`, and custom filters/globals.
- **Storage**: Async file storage with backends for local, S3, GCS, Azure, and SFTP.
- **Tasks**: Background job system with priority queues, retries, cron scheduling,
  `TaskManager`, and `MemoryBackend`.
- **Mail**: Email message construction, envelope handling, and provider-based delivery.
- **Admin**: Model admin registration, role permissions, audit events, and dashboard.
- **CLI**: `aq` command with init, add, generate, validate, serve, compile, freeze,
  discover, deploy, and more.

### MLOps Foundation

- Artifact registry, lineage tracing, shadow deployments, and model packaging
  infrastructure (removed in 1.1.0).