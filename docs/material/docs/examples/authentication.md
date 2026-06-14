# Authentication

The Auth example demonstrates registration, login, password verification, JWT token
issuance, and guard-protected routes. It wires Aquilia's authentication subsystem
through memory-backed identity, credential, and token stores.

---

## What It Demonstrates

- `AuthManager` composition with identity, credential, and token stores
- `PasswordHasher` with Argon2 password hashing
- `TokenManager` issuing access and refresh JWTs
- `@authenticated` decorator for requiring valid auth state
- `AdminGuard` and `@requires()` for role-based access control
- `SessionPolicy` integration via workspace configuration
- Blueprint-validated registration and login payloads

## Key Files

| File | Purpose |
| ---- | ------- |
| `workspace.py` | Enables DI, sessions, routing, fault handling, and security middleware |
| `modules/accounts/manifest.py` | Declares `AccountsController` and `AccountsService` |
| `modules/accounts/controllers.py` | Register, login, protected profile, admin summary endpoints |
| `modules/accounts/blueprints.py` | `RegisterBlueprint` and `LoginBlueprint` with validation |
| `modules/accounts/services.py` | `AccountsService` wiring all auth components with memory stores |

## Controller with Guards

```python
from aquilia.auth import AdminGuard, authenticated
from aquilia.auth.decorators import requires

class AccountsController(Controller):
    prefix = "/"
    tags = ["accounts"]

    def __init__(self, service: AccountsService | None = None):
        self.service = service or AccountsService()

    @POST("/register", status_code=201)
    async def register(self, ctx: RequestCtx):
        blueprint = RegisterBlueprint(data=await ctx.json())
        await blueprint.is_sealed_async()
        return Response.json(await self.service.register(blueprint.validated_data), status=201)

    @POST("/login")
    async def login(self, ctx: RequestCtx):
        blueprint = LoginBlueprint(data=await ctx.json())
        await blueprint.is_sealed_async()
        return Response.json(await self.service.login(blueprint.validated_data))

    @GET("/me")
    @authenticated
    async def me(self, ctx: RequestCtx, user=None):
        identity = user or ctx.identity
        return Response.json({"identity": identity.to_dict() if hasattr(identity, "to_dict") else None})

    @GET("/admin/summary")
    @requires(AdminGuard())
    async def admin_summary(self, ctx: RequestCtx):
        return Response.json({"area": "admin", "status": "authorized"})
```

## Auth Service Composition

The `AccountsService` wires the complete auth dependency graph:

- `MemoryIdentityStore` — stores identity records (email, username, roles)
- `MemoryCredentialStore` — stores hashed passwords by identity ID
- `MemoryTokenStore` — stores issued tokens with expiry
- `PasswordHasher` — Argon2 hashing with salt generation
- `TokenManager` — JWT creation with `KeyRing` signing
- `AuthManager` — orchestrates registration, authentication, and token lifecycle

The `register()` flow creates an identity, hashes the password, stores both, and returns
the identity. The `login()` flow verifies credentials, issues an access/refresh token pair,
and returns both tokens.

## Running

```bash
cd examples/auth_app
python -m uvicorn runtime:app --reload --port 8020
```

Test the auth flow:

```bash
# Register a user
curl -X POST http://127.0.0.1:8020/accounts/register \
  -H "Content-Type: application/json" \
  -d '{"email":"user@example.com","username":"testuser","password":"s3cretP@ss"}'

# Login
curl -X POST http://127.0.0.1:8020/accounts/login \
  -H "Content-Type: application/json" \
  -d '{"email":"user@example.com","password":"s3cretP@ss"}'

# Access protected profile (use the access token from login response)
curl http://127.0.0.1:8020/accounts/me \
  -H "Authorization: Bearer <access_token>"

# Run tests
python -m pytest examples/auth_app -q
```

## What You'll Learn

- How to compose `AuthManager` with identity, credential, and token stores
- How to protect routes with `@authenticated` and `@requires(AdminGuard())`
- How to validate registration and login payloads with Blueprints
- How `SessionPolicy` integrates with the auth subsystem
- How access and refresh tokens work in the Aquilia auth model

---

## Middleware Security App

The middleware security example in `examples/middleware_security_app/` demonstrates
CORS, CSP, and rate limiting policy composition:

```python
from aquilia.integrations import CorsIntegration, CspIntegration, RateLimitIntegration

workspace.integrate(CorsIntegration(
    allow_origins=["https://app.example.test"],
    allow_credentials=True,
))
workspace.integrate(CspIntegration(policy={
    "default-src": ["'self'"],
    "frame-ancestors": ["'none'"],
}))
workspace.integrate(RateLimitIntegration(limit=60, window=60))
```

It shows how rate limit extractors key requests by IP address for public routes
and by `X-API-Key` header for API routes.

```bash
cd examples/middleware_security_app
python -m uvicorn runtime:app --reload --port 8069
python -m pytest examples/middleware_security_app -q
```