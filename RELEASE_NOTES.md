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
