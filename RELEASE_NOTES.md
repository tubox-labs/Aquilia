# Aquilia v1.4.1

Release date: 2026-09-14
Release Name: "Safe Harbor"

## Summary

Aquilia v1.4.1 is a hardening and repair release. It fixes the silent admin login redirect loop (sessions were only wired when framework auth was enabled), the admin security DI provider registration failure (`ValueProvider ... missing argument: 'token'`), and lands the framework's response to a 27-finding migration audit: two Critical migration defects (`ArrayField` serialization, UUID foreign keys typed as INTEGER), eight Major fixes (composite primary keys, atomic upserts, multi-value response headers, response body lifecycle, route `status_code`, bare `Annotated` facets, `depends_on`/`imports` parity, workspace-config preservation), and the full minor/observation tail — each independently reproduced, fixed, and covered by regression tests verified against live PostgreSQL and live HTTP.

## Key Changes

- **Admin**: session middleware + SessionEngine DI now gated on the session engine, not on `use_auth`; admin DI providers register correctly.
- **Migrations**: self-contained FK column types (`Reference.to_field`), `ArrayField` round-trips, wired `CompositePrimaryKey`, honest `--dry-run`, drift-free `aq db diff`.
- **ORM**: atomic `get_or_create`/`update_or_create` (100-writer stress verified), `create()` dirty-snapshot fix, FK `<attr>_id` accessors.
- **HTTP client**: multi-value headers preserved (`get_headers()`, `cookies`), response-owned connections (read-after-close works).
- **Contracts**: bare facet classes validate; `SealFault.errors` alias; contract faults map to 400; pluggable error renderer.
- **Behavioral changes to review on upgrade**: `AquilaConfig.Auth.enabled` now defaults to `False` (opt-in); contract validation faults return 400 (was 500); `NativeTransport._read_response_head` returns raw header lists.

## Verification

Complete suite 9488 passed / 0 failed; 87 new regression tests; live PostgreSQL (migration applies, zero false drift, concurrency stress), live loopback HTTP (multi `Set-Cookie`, read-after-close, reuse), admin login end-to-end (cookie issued, dashboard 200, guard intact).

Full documentation: [`releases/1.4.1/`](releases/1.4.1/README.md) · Audit report: [`docs/AQUILIA_MIGRATION_AUDIT.md`](docs/AQUILIA_MIGRATION_AUDIT.md) · Changelog: [`CHANGELOG.md`](CHANGELOG.md)

---

# Aquilia v1.3.0

Release date: 2026-07-11
Release Name: "Ironclad Anchor"

## Summary

Aquilia v1.3.0 is a stable release introducing the fluent Controller Attributes builder, renaming the Blueprint validation system to Contracts, and implementing native PyConfig & DotEnv configuration resolution. It also features transaction fixes (`atomic()`), ORM reverse relations updates (`RelatedManager`), and a comprehensive authentication & session forensic audit resolving several security issues and bugs.

## Changes

### Added
- **Attributes Builder**: Introduced the `Attributes()` fluent builder for declarative controller-level configuration (prefixes, pipelines, tags, instantiation modes, timeouts, exception filters, throttles, etc.) with slot optimizations and definition-time validation.
- **Native PyConfig & DotEnv Resolution**: Direct support for `Env` and `Secret` wrappers in integrations and provider builders.
- **Field & Ellipsis Improvements**: Enhanced `Field()` to support positional defaults and `...` ellipsis for required fields.
- **Effect Registry & Diagnostics**: Replaced generic exception with `EffectNotAcquiredFault` featuring rich diagnostic metadata, and added `_DeferredEffectRegistry` to resolve ASGI startup order dependency issues.
- **Atomic Transactions Enhancements**: `@atomic` as a decorator, read-only transaction support (`atomic(readonly=True)`), and Prisma-style interactive timeouts (`atomic(timeout=...)`).
- **ORM Reverse Relations & Sentinels**: Lazy `RelatedManager` chaining support (`Model.related_manager()`), `RelatedNotLoaded` sentinel to prevent wrong-type footguns, and cached reverse-accessor resolution.

### Changed
- **Contracts System Rename**: Renamed the entire validation and mapping subsystem from `Blueprint` to `Contract` across all modules, test suites, and documentation.
- **Descriptor-based FKs**: Converted `ForeignKey` and `OneToOneField` to generic descriptors for improved IDE autocomplete and static type safety.

### Fixed
- **Authentication & Session Forensic Audit**:
  - Validated API key non-active statuses (suspended/expired).
  - Resolved `CredentialStore` protocol/implementation mismatches.
  - Fixed `RequireSessionAuthGuard`, `RequirePolicyGuard`, and `RequirePermissionGuard` bugs.
  - Implemented real RBAC checks in template `can()` helper.
  - Omitted symmetric HMAC keys from JWKS-style `KeyDescriptor.to_dict()` serialization.
  - Prevented loss of `roles` and `tenant_id` claims during refresh token rotation.
  - Implemented state context propagation in `set_identity()`.
  - Added session rotation commit concurrency safety checks.
  - Enforced client secret validation in OAuth2 confidential client flow and re-checked PKCE in code grant.
  - Ensured secure locking in `MemoryStore` and `FileStore`.
- **Security & Validation Errors**:
  - Confined local storage paths in `LocalStorage.listdir()` using normalization and root confinement.
  - Prevented silent bypass of class-level pipelines on `@exempt` routes.
  - Resolved unhandled exceptions by mapping all framework errors to structured `Fault` sub-classes.
- **Database & Transactions**:
  - Replaced SQL text driving in `Atomic` with connection-bound `begin`/`commit`/`rollback` calls.
  - Enabled isolation level routing for Postgres and MySQL adapters.
