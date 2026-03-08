# Security Policy

## Supported Versions

Currently, the following versions of Aquilia are supported with security updates. We recommend always running the latest version.

| Version | Supported          |
| ------- | ------------------ |
| 1.0.1   | :white_check_mark: |
| 1.0.0   | :warning: upgrade recommended |
| < 1.0   | :x:                |

## Security Audit Status

Aquilia v1.0.1 has undergone a comprehensive 15-phase security audit covering all subsystems:

| Subsystem | Status | Key Protections |
|-----------|--------|----------------|
| **Core/Server** | ✅ Audited | Header injection prevention, ASGI lifecycle hardening |
| **Auth** | ✅ Audited | Argon2 hashing, JWT rotation, CSRF double-submit, MFA, rate limiting |
| **DI** | ✅ Audited | Scope isolation, cycle detection, provider leak prevention |
| **Controller** | ✅ Audited | Filter/pagination injection protection |
| **Sessions** | ✅ Audited | Fixation protection, secure cookie flags, transport hardening |
| **Blueprints** | ✅ Audited | Namespace collision prevention, annotation validation |
| **ORM/Models** | ✅ Audited | Parameterized queries, field validation, SQL injection prevention |
| **Admin** | ✅ Audited | RBAC, audit logging, CSRF, rate-limiting, input sanitization |
| **Storage** | ✅ Audited | Path traversal blocking, null byte rejection, Fault-based errors |
| **Tasks** | ✅ Audited | Registered-task-only resolution, no arbitrary code execution |
| **Templates** | ✅ Audited | Sandboxed Jinja2, HMAC-verified bytecode cache, autoescape |
| **Faults** | ✅ Audited | 14 typed domains, no raw exceptions in any audited subsystem |

### Critical Fixes in v1.0.1

1. **Unsafe pickle deserialization** — `templates/bytecode_cache.py` and `templates/manager.py` previously used `pickle.load()` to deserialize cached template data from disk. This has been replaced with HMAC-verified JSON serialization (SHA-256 signature) to prevent arbitrary code execution via tampered cache files.

2. **Path traversal in storage** — `storage/base.py._normalize_path()` now rejects null bytes (`\x00`), `..` path segments after normalization, and paths exceeding 1024 characters.

3. **Arbitrary task execution** — `tasks/engine.py._execute_job()` previously resolved `func_ref` strings via `importlib`, potentially allowing arbitrary code execution if job metadata was tampered with. Resolution now only uses the registered `@task` decorator registry.

4. **SQL injection vectors** — ORM expression engine and lookup system now use parameterized queries throughout, with field name validation rejecting special characters.

## Reporting a Vulnerability

Security is a high priority for the Aquilia project and its community. If you discover a security vulnerability in Aquilia, please adhere to the following guidelines:

1. **Do NOT open a public issue.** This gives attackers an opportunity to exploit the vulnerability before an official patch is released.
2. Please send an email to the project maintainers outlining the vulnerability context and potential steps to reproduce.
3. We will acknowledge receipt of your vulnerability report as soon as possible and strive to send you regular updates about our progress.
4. Once the issue has been resolved and a new release is available, we will announce the fix publicly and give you credit for the discovery (unless you prefer to remain anonymous).

### Scope
This policy applies to all core components included in the `aquilia` distribution package. If the vulnerability affects a third-party module or dependency, you should report it directly to that upstream project, but notifying us is still appreciated so we can update our dependencies as well.

### Security-Related Dependencies

| Dependency | Purpose | Minimum Version |
|-----------|---------|----------------|
| `cryptography` | JWT, token signing | ≥42.0.0 |
| `argon2-cffi` | Password hashing | ≥23.1.0 |
| `jinja2` | Template sandboxing | ≥3.1.0 |
| `markupsafe` | XSS prevention (autoescape) | ≥2.1.0 |
