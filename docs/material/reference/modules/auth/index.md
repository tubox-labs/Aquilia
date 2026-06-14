# Auth Module

> `aquilia.auth` — Complete authentication and authorization system

The Auth module provides JWT, session, OAuth2, and MFA authentication plus RBAC/ABAC authorization, clearance-based access control, audit trails, and flow guards.

## When to Use

Use the Auth module when you need:

- User authentication (JWT tokens, sessions, OAuth2)
- Role-based (RBAC) or attribute-based (ABAC) authorization
- Multi-factor authentication (MFA)
- Declarative access control with the Clearance system
- Audit trails for security events
- Flow guards for per-route authorization

## Key Classes

| Class | Purpose |
|---|---|
| `AuthManager` | Central authentication orchestrator |
| `Identity` | Authenticated user identity |
| `TokenManager` | JWT token creation and verification |
| `PasswordHasher` | Secure password hashing (Argon2/bcrypt) |
| `AuthzEngine` | Authorization engine base |
| `RBACEngine` | Role-based access control |
| `ABACEngine` | Attribute-based access control |
| `ClearanceEngine` | Declarative multi-dimensional authorization |
| `MFAManager` | Multi-factor authentication |
| `OAuth2Manager` | OAuth2 / OIDC integration |
| `AuditTrail` | Security event audit logging |
| `FlowGuard` | Per-route authorization guard |
| `KeyRing` | Cryptographic key management |

## Quick Example

```python
from aquilia.auth import AuthManager, Identity
from aquilia import authenticated

auth = AuthManager()

# Authenticate
identity: Identity = await auth.authenticate(email="user@example.com", password="...")

# Issue token
token = auth.token_manager.create_access_token(identity)

# Protect a controller
class SecureController(Controller):
    @GET("/profile")
    @authenticated
    async def profile(self, ctx: RequestCtx):
        return Response.json({"user": ctx.identity.email})
```

## Import Path

```python
from aquilia.auth import (
    AuthManager,
    Identity,
    TokenManager,
    PasswordHasher,
    AuthzEngine,
    RBACEngine,
    ABACEngine,
    ClearanceEngine,
    AuditTrail,
    FlowGuard,
    KeyRing,
    authenticated,
    AdminGuard,
    VerifiedEmailGuard,
)
```

## Related Modules

- [sessions](../sessions/index.md) — Session-based authentication
- [middleware_ext](../middleware_ext/index.md) — Security middleware (CORS, CSRF, CSP)
- [core/flow](../core/flow.md) — Flow guards for per-route authorization
- [admin](../admin/index.md) — Admin authentication and roles