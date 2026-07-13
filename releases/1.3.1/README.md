# Aquilia v1.3.1 Release Notes — "Backend Refactoring"

Aquilia v1.3.1 introduces a major redesign of the authentication and authorization subsystems. By replacing the legacy string-based strategies with a pluggable, class-based backend architecture and hardening session serialization, this release provides a more secure, clean, and production-ready security foundation.

## Table of Contents

1. [Pluggable Authentication Backends](backends.md)
   * The new `AuthBackend` protocol.
   * Built-in backends (`TokenBackend`, `SessionBackend`, `PasswordBackend`, `ApiKeyBackend`).
   * Developing and registering custom backends.
2. [First-class Flow Guards & Context-First Decorators](guards.md)
   * Declaring guards as raw classes or instances.
   * Protect endpoints via `@authenticated`, `@roles_required`, and `@scopes_required`.
   * Advanced composition with `@requires`.
3. [Session Security Hardening](sessions.md)
   * The new session serialization format (preventing privilege escalation).
   * Live identity resolution on every request.
4. [Migration Guide](migration.md)
   * Moving from `strategies` configuration to `backends`.
   * Replaced class and function mappings.

---

## Why the Refactoring?

The legacy authentication subsystem relied on hardcoded string strategies and complex, nested flow-guard adapters. This design suffered from three main issues:
1. **Extensibility**: Adding custom authentication methods (such as OAuth2, LDAP, or WebAuthn) required modifying the middleware core or writing verbose adapters.
2. **Session Pollution**: Storing full user attributes (like roles and permissions) directly in session stores led to stale privilege bugs (where revoking a role did not take effect until the session expired).
3. **Elegance**: The routing pipeline used distinct decorator paradigms for session guards versus token guards, leading to fragmented APIs.

**Aquilia v1.3.1 solves these issues** by introducing unified, single-responsibility authentication backends and context-first decorators.
