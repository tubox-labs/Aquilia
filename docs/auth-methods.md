# Aquilia Auth Methods Reference

This document lists practical authentication and authorization methods available in Aquilia, from global configuration down to route-level behavior.

## 1. Global Auth Integration

Enable auth system wiring in workspace configuration so AuthManager and related dependencies are available.

Example in workspace.py:

```python
.integrate(Integration.auth(
    enabled=True,
    store_type="memory",
))
```

Notes:
- If auth integration is not enabled, guards like AuthGuard may fail with DI_RESOLUTION_FAILED for AuthManager.
- Sessions are typically used alongside auth integration.

## 2. Core Guard Methods (aquilia.auth.guards)

### AuthGuard

Constructor:

```python
AuthGuard(auth_manager: AuthManager | None = None, optional: bool = False)
```

Behavior:
- optional=False: unauthenticated request raises AUTH_REQUIRED.
- optional=True: request continues with identity set to None.
- If auth_manager is omitted, it is resolved from DI context/container.

Typical controller usage:

```python
class UsersController(Controller):
    pipeline = [AuthGuard]
```

### ApiKeyGuard

Constructor:

```python
ApiKeyGuard(auth_manager: AuthManager | None = None, required_scopes: list[str] | None = None)
```

Behavior:
- Authenticates using X-API-Key header.
- Supports optional required_scopes.
- Resolves auth_manager from DI when omitted.

### AuthzGuard

Constructor:

```python
AuthzGuard(
    authz_engine: AuthzEngine | None = None,
    resource_extractor: Callable[[dict[str, Any]], str] | None = None,
    action: str | None = None,
    required_scopes: list[str] | None = None,
    required_roles: list[str] | None = None,
    policy_id: str | None = None,
)
```

Behavior:
- Requires identity in context.
- Evaluates scopes, roles, and/or policy.

### ScopeGuard and RoleGuard

Constructors:

```python
ScopeGuard(required_scopes: list[str])
RoleGuard(required_roles: list[str])
```

Behavior:
- Lightweight scope-only or role-only checks.

## 3. Flow Guard Methods (aquilia.auth.integration.flow_guards)

These are useful when building Flow-style pipelines.

### RequireAuthGuard

```python
RequireAuthGuard(optional: bool = False)
```

- optional=False: requires identity.
- optional=True: allows anonymous access.

### RequireSessionAuthGuard

```python
RequireSessionAuthGuard(auth_manager: AuthManager | None = None)
```

- Validates session identity linkage.
- Resolves auth_manager from DI when omitted.

### RequireTokenAuthGuard

```python
RequireTokenAuthGuard(auth_manager: AuthManager | None = None)
```

- Validates Bearer token.
- Resolves auth_manager from DI when omitted.

### RequireApiKeyGuard

```python
RequireApiKeyGuard(
    auth_manager: AuthManager | None = None,
    required_scopes: list[str] | None = None,
)
```

- Validates API key authentication.
- Resolves auth_manager from DI when omitted.

### RequireScopesGuard / RequireRolesGuard / RequirePermissionGuard / RequirePolicyGuard

Behavior:
- Additional authorization-level checks for scopes, roles, permissions, or policy rules.

## 4. Controller-Level vs Route-Level Auth

### Class-level pipeline (applies to all endpoints in controller)

```python
class AuthController(Controller):
    pipeline = [AuthGuard]
```

### Route-level pipeline (applies only to one endpoint)

```python
@GET("/private", pipeline=[AuthGuard])
async def private(self, ctx: RequestCtx):
    ...
```

### Route-level override to bypass class-level guard

If class-level pipeline is guarded and one route should be public, provide route-level pipeline explicitly.

```python
@GET("/register", pipeline=[])
async def register_view(self, ctx: RequestCtx):
    ...
```

## 5. Optional Auth + Redirect Pattern

If you want a page to be accessible to anonymous users but still redirect authenticated users:

```python
class AuthenticationController(Controller):
    pipeline = [AuthGuard(optional=True)]

    @GET("/register")
    async def register_view(self, ctx: RequestCtx):
        if ctx.identity is None:
            return await self.render("index.html", request_ctx=ctx)
        return Response.redirect("/login")
```

## 6. Clearance Methods (aquilia.auth.clearance)

Clearance provides declarative access control.

### AccessLevel

Common levels:
- PUBLIC
- AUTHENTICATED
- INTERNAL
- CONFIDENTIAL
- RESTRICTED

### grant decorator

```python
@grant(level=AccessLevel.AUTHENTICATED, entitlements=[...], conditions=[...])
```

### exempt decorator

```python
@exempt
```

Use exempt to force public access for specific routes when class-level clearance exists.

## 7. Middleware-Level Auth

In auth integration middleware, require_auth controls global enforcement.

- require_auth=True: all requests require auth unless your app explicitly handles exceptions.
- require_auth=False: requests may be anonymous; downstream routes/guards decide.

## 8. Common Method Combinations

### Public page + protected APIs in one controller

Option A:
- Use class-level AuthGuard(optional=True).
- In each endpoint, branch on ctx.identity.

Option B:
- No class-level guard.
- Add route-level pipeline only on protected endpoints.

### Strictly protected controller with one public endpoint

- Keep class-level guard.
- Override specific endpoint with route-level pipeline=[].

## 9. Troubleshooting

### DI_RESOLUTION_FAILED for AuthManager

Cause:
- Auth integration/provider registration missing.

Fix:
- Ensure workspace config includes Integration.auth(enabled=True, ...).
- Ensure app is restarted after config changes.

### Unexpected auth requirement on a route

Cause:
- Class-level pipeline with AuthGuard affects all methods.

Fix:
- Move guard to route-level only, or override with route-level pipeline=[].

### Want browser redirect instead of JSON 401/403

Fix:
- Handle inside endpoint with Response.redirect.
- Or implement custom middleware/error handling to convert auth faults into redirects for HTML requests.

## 10. Quick Cheatsheet

- Guard all routes in controller: pipeline = [AuthGuard]
- Allow anonymous + optional identity: pipeline = [AuthGuard(optional=True)]
- Guard one route only: @GET(..., pipeline=[AuthGuard])
- Make one route public while class is guarded: @GET(..., pipeline=[])
- Redirect if unauthenticated: if ctx.identity is None: return Response.redirect("/login")
- Use declarative access rules: @grant(...) and @exempt
