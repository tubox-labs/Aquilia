# Auth App Starter

## Purpose

Authentication starter with registration, login, token issuance, a protected profile endpoint, and an admin-only route.

## Architecture

- `workspace.py` enables DI, sessions, routing, fault handling, and security middleware.
- `AccountsService` wires `MemoryIdentityStore`, `MemoryCredentialStore`, `MemoryTokenStore`, `PasswordHasher`, `TokenManager`, and `AuthManager`.
- `AccountsController` exposes registration, login, `@authenticated` profile access, and an `AdminGuard` route.

## Run

```bash
cd examples/auth_app
python -m uvicorn runtime:app --reload --port 8020
```

Expected behavior: registration creates an in-memory identity, login returns access/refresh tokens, and protected routes require auth middleware state.

## Test

```bash
python -m pytest examples/auth_app -q
```

## Common Pitfalls

- Memory stores reset on process restart.
- The signing key is a development value and must come from environment-backed config in production.
- Protected routes depend on auth/session middleware at runtime, not only service-level token issuance.

## Extension Ideas

Use durable identity stores, add MFA, add OAuth clients, configure token rotation, and add role-specific route tests.

## Related APIs

`AuthManager`, `Identity`, `IdentityType`, `PasswordCredential`, `PasswordHasher`, `TokenManager`, `KeyRing`, `SessionPolicy`, `authenticated`, `AdminGuard`.
