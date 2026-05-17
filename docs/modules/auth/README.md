# Auth Documentation

Authentication, authorization, identity stores, token management, guards, clearance rules, MFA, OAuth, and session integration.

## Coverage Snapshot

- Source files: 24
- Source lines: 12774
- Public classes: 164
- Public module functions: 61
- Constants/module flags: 19
- Public exports in `__all__`: 192

## Source Files Read

- `aquilia/auth/__init__.py`: AquilAuth - Authentication & Authorization System
- `aquilia/auth/audit.py`: AquilAuth - Security Audit Trail
- `aquilia/auth/authz.py`: AquilAuth - Authorization Engine
- `aquilia/auth/clearance.py`: Aquilia Clearance System -- Unique declarative access control.
- `aquilia/auth/core.py`: AquilAuth - Core Types
- `aquilia/auth/surp.py`: AquilAuth - Surp Artifacts
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

## Document Map

- `architecture.md`: module boundaries, dependencies, lifecycle, and extension points.
- `configuration.md`: configuration classes, builders, server wiring, and precedence.
- `api-reference.md`: source-extracted classes, methods, functions, constants, exports, and signatures.
- `integration-guide.md`: how to wire the module into an Aquilia app.
- `cli-reference.md`: mounted `aq` commands for this module, if any.
- `examples.md`: usage examples derived from source and checked example apps.
- `edge-cases-and-limitations.md`: implementation limits and compatibility behavior.
- `troubleshooting.md`: diagnostic commands and common failure patterns.
