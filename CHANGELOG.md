# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

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
