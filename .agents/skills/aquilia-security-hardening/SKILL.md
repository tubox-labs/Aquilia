---
name: aquilia-security-hardening
description: "Apply Aquilia security hardening across auth, sessions, middleware, storage/filesystem, templates, cache signing, admin, ORM, provider credentials, CSRF/CORS/CSP/HSTS, rate limiting, path validation, and secret handling. Use when security-sensitive framework behavior is involved."
---

# Aquilia Security Hardening

## Purpose
Make security-sensitive Aquilia changes using implemented hardening primitives instead of generic advice.

## Trigger Conditions
Use for authentication secrets, password policy, token binding, CSRF/CORS/CSP/HSTS, sessions/cookies, admin access, path traversal, storage roots, template sandboxing, cache signing, SQL injection prevention, provider credentials, or production hardening.

## Inputs
- Threat surface, environment, config values, affected subsystem, and acceptable compatibility tradeoffs.
- Whether app is dev/test/prod and whether public clients need browser access.

## Execution Flow
1. Identify the subsystem: auth/session, middleware, template, storage/filesystem, ORM/database, cache, admin, provider, or deployment.
2. Use implemented hardening classes such as `CSRFProtection`, `SecurityHeaders`, `TokenBinder`, security middleware, storage/filesystem validators, template sandboxing, and password policy.
3. Keep secrets in `Secret`/env-backed config or provider credential stores.
4. Validate behavior with focused tests and existing security tests.
5. Document any deliberately relaxed dev settings separately from production settings.

## Constraints
- Do not turn off CSRF/CORS/CSP/session cookie protections without stating the risk and scope.
- Do not log raw secrets, tokens, passwords, provider credentials, or full PII identifiers.
- Do not bypass ORM/query parameterization or path validators for user input.

## Implementation Anchors
`aquilia/auth/hardening.py`, `aquilia/middleware_ext/security.py`, `aquilia/filesystem/_security.py`, `aquilia/storage/base.py`, `aquilia/templates/security.py`, `aquilia/signing.py`, `aquilia/providers/render/store.py`, `tests/test_*security*.py`, `SECURITY.md`.

## Examples
- Require `Secret(env="AQ_SECRET_KEY", required=True)` in production config.
- Add CSP and HSTS middleware for browser-facing apps.
- Sanitize uploaded filenames before writing through storage/filesystem APIs.

## Failure Handling
If hardening breaks a client, isolate which middleware/header/policy changed and adjust narrowly. If credentials are already leaked, rotate them; do not just redact code. If tests need relaxed security, scope the override to test settings only.
