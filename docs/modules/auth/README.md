# Authentication And Authorization Documentation

This directory is the professional documentation set for `auth`. It is implementation-driven and aligned with the current source files under `aquilia/auth`.

## What This Covers

The identity, credential, token, authorization, guard, audit, OAuth, MFA, CSRF, and clearance subsystem.

## Source Files Read

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

## Document Map

- `architecture.md`: Runtime architecture and module boundaries
- `configuration.md`: Configuration entry points, datatypes, and precedence
- `api-reference.md`: Classes, methods, functions, constants, and data fields extracted from source
- `integration-guide.md`: How to wire the module into a real Aquilia application
- `cli-reference.md`: Command line surface and operational commands
- `edge-cases-and-limitations.md`: Known edge cases and implementation limits
- `troubleshooting.md`: Common failures and diagnosis steps
- `examples.md`: Code examples and usage patterns

## Public Surface Snapshot

- Python files: 24
- Public classes: 164
- Configuration or dataclass-like types: 28
- Public functions: 61
- Constants detected: 8

## Fast Start

```python
from aquilia.auth.core import Identity, IdentityType, PasswordCredential
from aquilia.auth.hashing import PasswordHasher
from aquilia.auth.manager import AuthManager
from aquilia.auth.stores import MemoryCredentialStore, MemoryIdentityStore, MemoryTokenStore
from aquilia.auth.tokens import KeyDescriptor, KeyRing, TokenManager

identity_store = MemoryIdentityStore()
credential_store = MemoryCredentialStore()
token_store = MemoryTokenStore()
key = KeyDescriptor.generate(kid="dev", algorithm="HS256", secret="replace-me")
manager = AuthManager(
    token_manager=TokenManager(KeyRing(keys=[key]), token_store),
    identity_store=identity_store,
    credential_store=credential_store,
    password_hasher=PasswordHasher(),
)
```

## Read Next

Start with `architecture.md` if you are learning how the subsystem fits into runtime boot. Use `api-reference.md` when you need exact methods, datatypes, and class fields. Use `examples.md` for copyable patterns that match the current code.
