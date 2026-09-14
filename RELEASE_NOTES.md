# Aquilia v1.4.1

Release date: 2026-09-15
Release Name: "Safe Harbor"

## Summary

Aquilia v1.4.1 is a hardening and repair release. It fixes the silent admin login redirect loop (sessions were only wired when framework auth was enabled), the admin security DI provider registration failure (`ValueProvider ... missing argument: 'token'`), lands the framework's response to a 27-finding migration audit (two Critical migration defects, eight Major fixes, and the full minor/observation tail), and — following a second, auth-focused gap analysis — **rebuilds the authentication & authorization architecture end-to-end**: one unified configuration model, an authenticate-then-enforce request pipeline, a route-level async guard pipeline with `@Public()`/`@UseGuards`, a Passport-style strategy registry with a stateless JWT mode, `@CurrentUser()` principal injection, refresh-token rotation with reuse detection, durable database stores, and exact 401 error contracts. Every fix was independently reproduced, fixed, and covered by regression tests verified against live PostgreSQL, live HTTP, and live Redis.

## Key Changes

- **Admin**: session middleware + SessionEngine DI now gated on the session engine, not on `use_auth`; admin DI providers register correctly.
- **Migrations**: self-contained FK column types (`Reference.to_field`), `ArrayField` round-trips, wired `CompositePrimaryKey`, honest `--dry-run`, drift-free `aq db diff`.
- **ORM**: atomic `get_or_create`/`update_or_create` (100-writer stress verified), `create()` dirty-snapshot fix, FK `<attr>_id` accessors.
- **HTTP client**: multi-value headers preserved (`get_headers()`, `cookies`), response-owned connections (read-after-close works).
- **Contracts**: bare facet classes validate; `SealFault.errors` alias; contract faults map to 400; pluggable error renderer.
- **Auth architecture rebuild**: `AuthSettings` single configuration model (the loader no longer injects a secret default that outranked operator configuration — AG-13 Critical); public-route token tolerance; async guards with `global_guards`/`@UseGuards`/`@Public()`; `jwt-stateless` strategy; `CurrentUser` principal injection; `extra_claims`; `collapse_token_errors`; refresh rotation with reuse detection (family revocation, atomic CAS, exactly-one-winner races); `Database*Store` durable stores; Redis session store; auth faults 401 + public + rendered through the app's `error_renderer`; fail-closed auth bootstrap outside dev/test. Full reference: [`docs/AUTH_ARCHITECTURE.md`](docs/AUTH_ARCHITECTURE.md); fix report: [`releases/1.4.1/auth_architecture.md`](releases/1.4.1/auth_architecture.md).
- **Behavioral changes to review on upgrade**: `AquilaConfig.Auth.enabled` defaults to `False` (opt-in); contract validation faults return 400 (was 500); `NativeTransport._read_response_head` returns raw header lists; **auth faults return 401 (was 403) with real messages in production; the auth audience default is unified to `["api"]` (re-issue tokens or pin the old value for one TTL window); `require_auth` raises a fault (rendered via `error_renderer`) instead of returning a hand-built 401 body**; see `docs/AUTH_ARCHITECTURE.md` §11 for the complete migration list.

## Verification

Complete suite 9646 passed / 0 failed; 238 new tests this release (87 audit regressions + 151 auth-rebuild adversarial tests); live PostgreSQL (migration applies, zero false drift, concurrency stress), live loopback HTTP (multi `Set-Cookie`, read-after-close, reuse), live Redis (Lua-CAS rotation races, session store TTLs), admin login end-to-end (cookie issued, dashboard 200, guard intact), and a 120-request mixed-traffic auth soak.

Full documentation: [`releases/1.4.1/`](releases/1.4.1/README.md) · Migration audit: [`docs/AQUILIA_MIGRATION_AUDIT.md`](docs/AQUILIA_MIGRATION_AUDIT.md) · Auth architecture: [`docs/AUTH_ARCHITECTURE.md`](docs/AUTH_ARCHITECTURE.md) · Changelog: [`CHANGELOG.md`](CHANGELOG.md)

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
