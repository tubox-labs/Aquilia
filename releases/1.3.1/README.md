# Aquilia v1.3.1 Release Notes — "Backend Refactoring"

Aquilia v1.3.1 introduces a major rewrite of the authentication (`aquilia.auth`) and authorization subsystems. It moves away from rigid string-based strategies and hardcoded guard adapters in favor of a pluggable, class-based backend architecture, a unified permission engine, hardened session serialization, and token clock-skew tolerance.

## Table of Contents

1. [Pluggable Authentication Backends](backends.md)
   * The new `AuthBackend` protocol.
   * Built-in backends: `TokenBackend`, `SessionBackend`, `PasswordBackend`, `ApiKeyBackend`.
   * The `resolve_backend` helper and loading configuration.
2. [Unified Permission & Authorization Engine](guards.md#permissionengine)
   * Role DAG (Directed Acyclic Graph) inheritance.
   * Policy callables and scope checks.
   * Pluggable Flow Guards: `AuthGuard`, `RoleGuard`, `ScopeGuard`, `PolicyGuard`.
   * Context-First Decorators: `@authenticated`, `@roles_required`, `@scopes_required`, `@optional_auth`.
3. [Session Security Hardening](sessions.md)
   * Elimination of stale permission state in session cookies.
   * The lightweight `AuthPrincipal` serialization format.
   * Dynamic resolution of roles and scopes on every request.
4. [Migration Guide](migration.md)
   * Upgrading configuration settings from `strategies` to `backends`.
   * Replaced classes, decorators, and middleware.

---

## Key Refactoring Goals

1. **Pluggability**: Unify all authentication strategies (Bearer JWTs, Session cookies, Username/Password, API keys) under a single, reusable backend protocol.
2. **Dynamic Privileges**: Resolve permissions, roles, and scopes fresh from the database or cache on every request, preventing privilege escalation through stale session states.
3. **API Simplification**: Consolidate five parallel authorization subsystems (RBAC, ABAC, Clearance, Policy DSL, and custom adapters) into a single, cohesive `PermissionEngine`.
4. **Resiliency**: Handle clock drift in distributed clusters by introducing native clock-skew tolerance.
5. **DI Scope Performance**: Deprecate the class/object-based `ServiceScope` Enum in favor of high-performance raw string literals backed by `typing.Literal` to eliminate import-time namespace scanning and runtime attribute lookup overhead.

