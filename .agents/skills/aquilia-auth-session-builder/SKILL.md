---
name: aquilia-auth-session-builder
description: "Build Aquilia authentication and session workflows. Use for AuthManager, tokens, password hashing/policy, guards, clearance, OAuth, MFA, session policies/stores/transports, auth middleware, and protected controllers."
---

# Aquilia Auth Session Builder

## Purpose
Configure and implement Aquilia auth/session flows using the actual auth and session subsystems.

## Trigger Conditions
Use for login/session identity, JWT/token config, password hashing, RBAC/ABAC, clearance decorators, route guards, OAuth2/PKCE, MFA, session stores/transports, or auth middleware behavior.

## Inputs
- Auth settings: secret key, algorithm, issuer, audience, token TTLs, password policy.
- Session policies: TTL, idle timeout, persistence, cookie/header transport, store.
- Controller protection requirements: roles, scopes, permissions, clearance conditions.

## Execution Flow
1. Enable sessions with `Workspace.sessions(...)`; auth forces sessions on in server middleware setup.
2. Configure auth through `Integration.auth(...)`, `AuthConfig`, or workspace security settings as appropriate.
3. Use decorators/guards from `aquilia.auth.decorators`, `aquilia.auth.guards`, and clearance helpers for controller protection.
4. Use `AuthManager`, `TokenManager`, `PasswordHasher`, stores, and session bridge through DI where possible.
5. Test protected routes with `aquilia.testing.TestClient` bearer token or session cookie helpers.

## Constraints
- Do not use insecure default secrets; `AuthConfig.secret_key` must be set explicitly for real auth.
- Cookie security settings depend on environment; do not turn off httponly casually.
- Clearance and auth decorators should return structured auth faults or challenge responses, not raw exceptions.

## Implementation Anchors
`aquilia/auth/*.py`, `aquilia/auth/integration/*.py`, `aquilia/sessions/*.py`, `aquilia/middleware_ext/session_middleware.py`, `tests/test_auth_system.py`, `tests/test_sessions_system.py`, `examples/auth_app/`.

## Examples
- Protect a route with `@authenticated` or `@requires(AdminGuard())`.
- Add `DEFAULT_USER_POLICY` to workspace sessions.
- Implement a clearance rule with `@grant(level=AccessLevel.WRITE, conditions=[is_owner_or_admin])`.

## Failure Handling
If auth is enabled but sessions fail, inspect session engine creation first. Token errors should map to auth faults. Password validation failures come from `PasswordPolicy`; return user-safe messages only.
