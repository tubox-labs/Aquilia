# Authentication And Authorization Edge Cases And Limitations

## Fault And Error Types

The following error-oriented classes are present in the implementation and should guide defensive usage.

| Type | Source | Meaning |
| --- | --- | --- |
| `AuthorizationRequiredFault` | `aquilia/auth/decorators.py` | Raised when authorization check fails. |
| `FaultHandlerMiddleware` | `aquilia/auth/integration/middleware.py` | Middleware for handling faults with FaultEngine. |

## Common Edge Cases

- Optional dependencies may change behavior. Check imports and constructor docs before enabling production features.
- In-memory stores, queues, caches, adapters, and registries are usually process-local. Use durable backends when state must survive restarts or scale across workers.
- Request-scoped data must not be cached globally. Use request state, DI request scopes, or explicit parameters.
- Decorators in Aquilia generally attach metadata at import time. Runtime behavior happens later during compilation, routing, middleware execution, or service startup.
- Many subsystems intentionally convert invalid states into typed faults. Catch the specific fault type when application code can recover.

## Source-Level Limits To Review

Review these files before changing behavior:

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
