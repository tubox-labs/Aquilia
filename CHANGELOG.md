# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.1.1] — 2026-06-09 — "Sea Serpent"

### Removed
- Removed `aquilia/config_builders.py` — the 5420-line god-file has been deleted.

### Changed
- Extracted `Workspace`, `Module`, and supporting dataclasses (`RuntimeConfig`,
  `ModuleConfig`, `AuthConfig`) into a clean `aquilia/workspace.py` module.
- `Workspace.integrate()` accepts `aquilia.integrations.*` typed dataclasses
  directly via the `IntegrationConfig` protocol (already partially supported).
- `Workspace.i18n()`, `Workspace.tasks()`, and `Workspace.storage()` convenience
  methods now use `I18nIntegration`, `TasksIntegration`, and `StorageIntegration`
  typed dataclasses internally instead of the legacy `Integration.*` static methods.
- Moved the legacy `Integration` class to `aquilia/integrations/_legacy.py`
  for backward compatibility.  Existing code using `Integration.mail(...)`,
  `Integration.admin(...)`, etc. continues to work.
- Updated all example workspace files to use typed integration dataclasses
  from `aquilia.integrations` instead of the `Integration` static API.
- Updated all test imports to use `aquilia.workspace` and
  `aquilia.integrations` directly.

### Fixed
- **Thread safety**: Replaced `bool` flag `_dotenv_lock` with `threading.RLock()`
  in `pyconfig.py` — two threads loading dotenv simultaneously no longer corrupt
  `os.environ`.
- **I18n default values**: Fixed broken `dataclasses.field()` usage on plain
  class attributes in `AquilaConfig.I18n` (replaced with plain lists).
- **Catalog format consistency**: `ConfigLoader.get_i18n_config()` now defaults to
  `"json"` (was `"surp"`), matching `AquilaConfig.I18n.catalog_format`.
- **`for_env()` recursion**: `AquilaConfig.for_env()` now recursively searches all
  subclass depths (was limited to 2 levels).
- **Step numbering**: Renumbered `ConfigLoader.load()` steps to remove the gap
  (Step 4 → Step 3, Step 4.5 → Step 4).
- **Config boilerplate**: Added `ConfigLoader.get_subsystem_config()` generic method;
  10 of 12 subsystem config getters are now thin wrappers, cutting boilerplate by ~80%.
- **Config package**: Created `aquilia/config/` package as a canonical re-export hub.
  `from aquilia.config import Workspace, Module, AquilaConfig, Env, Secret` works.
- **pyproject.toml**: Removed `psutil>=7.2.2` from core dependencies (now optional).
  Removed empty `templates`, `db`, and `files` extras. Fixed stale MLOps comment.

## [1.1.0] — 2026-06-08 — "Black Pearl"

### Removed
- Removed aquilia/mlops/ in its entirety
- Removed duplicate aquilia/aquilia_mcp/ package (canonical is aquilia.mcp)
- Removed AMDL DSL: parser, AST nodes, __init__old.py, AMDLParseFault
- Removed aquilia/patterns/lsp/ Language Server Protocol server

### Changed
- URL pattern documentation: guillemet delimiters replaced with brace syntax {id:int}
- Moved ruff from dependencies to [dev] optional extra
- Moved asyncpg from dependencies to new [postgres] optional extra
- Fixed broken GitHub URLs (axiomchronicles → tubox-labs)

### Added
- aquilia/sse/ — Server-Sent Events: SSEEvent, SSEResponse, json/text stream helpers
- aquilia/otel/ — OpenTelemetry: OTelConfig, OTelMiddleware, no-op fallback
- aquilia/controller/validation.py — @validate_body(BlueprintClass) decorator
- aquilia/sqlite/_config.py — SqlitePoolConfig with full parameter surface
- New [postgres] optional extra (asyncpg)
- New [otel] optional extra (opentelemetry-*)

### Fixed
- aiosqlite removed as framework dependency; only available via [sqlite-compat]

## [1.0.5] — 2026-06-04 — "Jolly Roger"

### Added
- Added a production-grade, source-backed Aquilia MCP server under `aquilia.mcp` with JSON-RPC stdio support, tool/resource/prompt registries, persistent repository indexing, installer helpers, and canonical `python -m aquilia.mcp` entrypoints.
- Added MCP tools and prompts for framework API discovery, bootstrap/runtime explanation, workspace and module scaffolding guidance, manifest-plan validation, integration recommendations, deprecation guarding, CLI discovery, example lookup, and agent prompt generation.
- Added practical MCP documentation and bootstrap configs for Claude, Codex, and Gemini CLI under `docs/mcp/` and `examples/mcp_bootstrap/`.

### Changed
- Replaced the Crous/Crousr binary serialization stack with Surp across runtime request and response helpers, compiled artifacts, Aquilary registry loading, admin audit persistence, i18n catalogs, model snapshots, WebSocket artifacts, template cache metadata, analytics cache, provider credential stores, and CLI workflows.
- Renamed public binary payload helpers and decorators from Crous terminology to Surp terminology, including `Request.surp()`, `Response.surp()`, `requires_surp`, `SurpCatalog`, and related availability helpers.
- Updated generated artifact extensions and documentation from `.crous` to `.surp` while preserving JSON fallback paths where the framework already supported them.
- Updated package dependencies to install `surp` instead of `crousr` and `crous-native`.
- Allowed `aq i18n init --format surp` to create Surp-backed starter catalogs.
- Rewired `aq mcp` commands to the canonical `aquilia.mcp` package while preserving the existing `aquilia.mcp` compatibility surface.

### Removed
- Removed Crous-specific imports, native backend probing, API names, file extensions, and request/response tests.

### Security
- Hardened MCP resource access and diagnostics with read-only defaults, path traversal and null-byte rejection, binary-file guards, bounded stdio frames, strict tool input validation, and secret redaction in doctor output.

### Tests
- Added Surp request/response coverage and updated admin, i18n, provider, regression, and security tests for the new Surp-backed behavior.
- Added MCP protocol, stdio transport, indexer/search, tool, prompt, installer, CLI, and end-to-end stdio session coverage for the canonical package.
- Verified the migration with bytecode compilation, focused Surp/i18n/provider tests, stale-reference scans, and a full test run with only the sandbox-local loopback test requiring an isolated permissioned rerun.
- Verified MCP changes with focused MCP tests, Ruff checks, bytecode compilation, index generation, and a full test suite run.

### Tooling
- Began tracking the repository-local `.agents/` skill definitions and stopped ignoring local agent skill metadata.
- Added `aq mcp` workflows for serving, index building, doctor diagnostics, agent installation, tool and prompt listing, and source-backed query testing.

## [1.0.4] — 2026-05-17

### Removed
- Removed the React-style `aquilia/build` package and the `aq build` command.
- Removed automatic build-gating from `aq run`, `aq serve`, and `aq deploy`; runtime and deploy generation now use native workspace loading and live introspection.
- Removed the Admin Build page, `/admin/build/` route, sidebar/search links, and `AdminModules.build` configuration surface.

### Changed
- `aq compile` now writes explicit artifacts through `WorkspaceCompiler` without depending on a build pipeline.
- `aq freeze` now creates an integrity snapshot for generated artifacts under `artifacts/`.
- Deployment Makefile generation now calls `python -m aquilia.cli compile`.

### Fixed
- Isolated independent SQLite `:memory:` pools while preserving shared state across connections within the same pool.

### Documentation
- Updated CLI, deployment, admin, release, and getting-started docs to reflect the native Python runtime structure.

## [1.0.1] — 2026-03-08

### Added — Comprehensive Framework Audit (Phases 1–15)

#### Core & Server (Phases 1–6)
- Full security audit of `aquilia/server.py`, `aquilia/engine.py`, `aquilia/flow.py`, `aquilia/middleware.py`
- Hardened `aquilia/request.py` and `aquilia/response.py` against header injection and content-type attacks
- Hardened `aquilia/asgi.py` ASGI lifecycle handling

#### Dependency Injection (Phase 7)
- Security audit of `aquilia/di/` — scope isolation, cycle detection, provider resolution
- Fixed potential DI graph leaks across request boundaries

#### Auth System (Phase 8)
- Comprehensive audit of `aquilia/auth/` — JWT, session, MFA, OAuth, RBAC
- Hardened token lifecycle, password hashing (Argon2), CSRF protection
- Fixed clearance level escalation edge cases in `aquilia/auth/clearance.py`

#### Controller System (Phase 9)
- Audit of `aquilia/controller/` — routing, filters, pagination, factory
- Secured filter/pagination against injection and overflow attacks

#### Sessions (Phase 10)
- Audit of `aquilia/sessions/` — store, transport, engine
- Hardened session fixation protection and cookie security flags

#### Blueprints (Phase 11)
- Audit of `aquilia/blueprints/` — annotations, facets, core, integration
- Secured blueprint registration against namespace collisions

#### ORM & Models (Phase 12)
- Comprehensive audit of `aquilia/models/` — query builder, fields, transactions, migrations
- Parameterized all raw SQL paths, field name validation, safe deletion cascades
- Protected against SQL injection in expression engine and lookup system

#### Admin Module (Phase 13)
- Deep security audit of `aquilia/admin/` — controller, site, registry, permissions, inlines, templates
- Created `aquilia/admin/security.py` with CSRF, rate-limiting, input validation, audit logging
- Role-based permission enforcement across all admin endpoints

#### Admin Fault Migration & Subsystem Integration (Phase 14)
- Replaced all raw exceptions in `aquilia/admin/` with structured `Fault` subclasses
- Created `aquilia/admin/faults.py` with `ADMIN_DOMAIN` and 7 fault classes
- Created `aquilia/admin/subsystems.py` integrating cache/effects/tasks/flow/lifecycle
- Added admin-specific config builders to `aquilia/config_builders.py`

#### Tasks, Storage & Templates — Fault Migration & Security (Phase 15)
- **Tasks**: Created `aquilia/tasks/faults.py` with `TASKS_DOMAIN`, `TaskScheduleFault`, `TaskNotBoundFault`, `TaskEnqueueFault`, `TaskResolutionFault`
- **Storage**: Converted `StorageError` hierarchy to inherit from `Fault` with `STORAGE_DOMAIN`; added `StorageIOFault`, `StorageConfigFault`
- **Templates**: Created `aquilia/templates/faults.py` with `TEMPLATE_DOMAIN`, `TemplateEngineUnavailableFault`, `TemplateCacheIntegrityFault`
- **Fault core**: Registered 3 new standard domains — `STORAGE`, `TASKS`, `TEMPLATE` on `FaultDomain`

### Security Fixes
- **CRITICAL**: Eliminated unsafe `pickle.load()` deserialization in `templates/bytecode_cache.py` and `templates/manager.py` — replaced with HMAC-verified JSON (SHA-256)
- **HIGH**: Hardened `storage/base.py._normalize_path()` — rejects null bytes (`\x00`), `..` traversal segments, paths >1024 chars
- **HIGH**: Task `func_ref` resolution in `tasks/engine.py` now only resolves via the registered `@task` registry (allowlist), preventing arbitrary code execution
- **MEDIUM**: Added deprecation warning to regex-based `sanitize_html()` in `templates/security.py`
- **MEDIUM**: ORM parameterized queries and field name validation against SQL injection
- **MEDIUM**: Session fixation protection and secure cookie flags
- **LOW**: Auth token rotation hardening, CSRF double-submit validation

### Changed
- `aquilia/faults/core.py` — added `FaultDomain.STORAGE`, `FaultDomain.TASKS`, `FaultDomain.TEMPLATE` standard domains
- `aquilia/storage/base.py` — `StorageError` now inherits from `Fault` (was `Exception`)
- `aquilia/storage/__init__.py` — exports `StorageIOFault`, `StorageConfigFault`, `STORAGE_DOMAIN`
- `aquilia/tasks/__init__.py` — exports all task fault classes
- `aquilia/templates/__init__.py` — exports all template fault classes
- Bytecode cache schema version bumped from `1.0` to `1.1` (JSON+HMAC format)

### Tests
- **5,085 total tests passing** (up from baseline), 0 failures
- `tests/test_phase14_faults_subsystems.py` — 118 tests (admin faults + subsystem integration)
- `tests/test_phase15_faults_security.py` — 120 tests (fault migration + security audit)
- `tests/test_admin_security.py` — admin security regression tests
- `tests/test_blueprint_security.py` — blueprint security tests
- `tests/test_orm_security.py` — ORM injection and security tests
- `tests/test_session_security.py` — session security tests
- `tests/test_integration_wiring.py` — cross-subsystem integration tests
- Updated existing tests to expect new `Fault` types instead of raw exceptions

## [1.0.0] - Initial Release

### Added
- Manifest-First Architecture implementation (`AppManifest`)
- Scoped Dependency Injection framework targeting Singleton, App, and Request contexts.
- Async-Native core using Uvicorn and ASGI specifications.
- Foundation for Integrated MLOps (Artifact Registry, Lineage Tracing, Shadow Deployments).
- Core subsystems: Flow (routing), Faults (error handling), and essential services.
