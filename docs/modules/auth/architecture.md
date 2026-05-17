# Authentication And Authorization Architecture

## Runtime Role

The identity, credential, token, authorization, guard, audit, OAuth, MFA, CSRF, and clearance subsystem.

The implementation is split across 24 Python files. The module boundary is visible in the file inventory below and the API reference is generated from the same source files.

## Primary Source Files

- `aquilia/auth/__init__.py`: AquilAuth - Authentication & Authorization System
- `aquilia/auth/audit.py`: AquilAuth - Security Audit Trail
- `aquilia/auth/authz.py`: AquilAuth - Authorization Engine
- `aquilia/auth/clearance.py`: Aquilia Clearance System -- Unique declarative access control.
- `aquilia/auth/core.py`: AquilAuth - Core Types
- `aquilia/auth/crous.py`: AquilAuth - Crous Artifacts
- `aquilia/auth/decorators.py`: AquilAuth - Authentication Decorators and Guards.
- `aquilia/auth/faults.py`: AquilAuth - Authentication/Authorization Faults
- `aquilia/auth/guards.py`: AquilAuth - Guards and Flow Integration
- `aquilia/auth/hardening.py`: AquilAuth - Security Hardening Utilities
- `aquilia/auth/hashing.py`: AquilAuth - Password Hashing
- `aquilia/auth/integration/__init__.py`: AquilAuth - Integration package.
- `aquilia/auth/integration/aquila_sessions.py`: AquilAuth - Aquilia Sessions Integration
- `aquilia/auth/integration/di_providers.py`: AquilAuth - DI Providers
- `aquilia/auth/integration/flow_guards.py`: AquilAuth - Flow & Controller Guards (Deep Integration)
- `aquilia/auth/integration/middleware.py`: AquilAuth - Unified Middleware
- `aquilia/auth/integration/runtime_context.py`: AquilAuth runtime context bridge.
- `aquilia/auth/integration/sessions.py`: AquilAuth - Session Integration
- `aquilia/auth/manager.py`: AquilAuth - Authentication Manager
- `aquilia/auth/mfa.py`: AquilAuth - MFA Providers
- `aquilia/auth/oauth.py`: AquilAuth - OAuth2/OIDC Flows
- `aquilia/auth/policy/__init__.py`: AquilAuth - Policy DSL Module
- `aquilia/auth/stores.py`: AquilAuth - Credential and Token Stores
- `aquilia/auth/tokens.py`: AquilAuth - Token Management

## Internal Dependency Shape

The table below is derived from import statements in the module. It shows which top-level packages this module depends on most often.

| Imported package | Import count |
| --- | --- |
| `aquilia` | 23 |
| `typing` | 21 |
| `__future__` | 20 |
| `dataclasses` | 11 |
| `faults` | 11 |
| `datetime` | 9 |
| `collections` | 8 |
| `core` | 8 |
| `secrets` | 8 |
| `hashlib` | 7 |
| `enum` | 6 |
| `logging` | 5 |
| `manager` | 5 |
| `time` | 5 |
| `tokens` | 5 |
| `authz` | 4 |
| `base64` | 4 |
| `hmac` | 4 |
| `json` | 4 |
| `stores` | 4 |
| `aquila_sessions` | 3 |
| `hashing` | 3 |
| `functools` | 2 |
| `inspect` | 2 |
| `mfa` | 2 |
| `oauth` | 2 |
| `os` | 2 |
| `asyncio` | 1 |
| `audit` | 1 |
| `clearance` | 1 |

## Data And Control Flow

1. Configuration or direct construction creates the public service objects, controllers, providers, or helpers for this module.
2. Runtime code imports the registered classes from manifests, workspace integrations, middleware stacks, or direct application code.
3. Public methods perform validation and convert invalid states into typed Aquilia faults where the implementation defines fault classes.
4. Integration points return Python data structures, `Response` objects, provider results, jobs, sessions, connections, or model instances depending on the subsystem.

## Boundary Rules

- Keep application-specific business decisions outside framework classes unless the class is explicitly a service or controller owned by your app.
- Prefer the public exports and typed configuration dataclasses shown in `api-reference.md`.
- When a module supplies both a low-level primitive and a high-level service, use the service in application code and keep primitives for tests, providers, or advanced integrations.
