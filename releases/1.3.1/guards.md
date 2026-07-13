# Flow Guards & Context-First Decorators

Aquilia v1.3.1 standardizes endpoint protection using a unified Guard protocol and a set of clean, context-first decorators.

## Unified `Guard` Protocol

A guard is a class that implements `check(ctx)`. If access is denied, it raises a structured auth fault; otherwise, it returns `None` (success).

```python
class Guard(Protocol):
    def check(self, ctx: Any) -> None:
        """Evaluate the guard condition and raise a fault on denial."""
        ...
```

Guards are stateless, meaning they can be declared as class references or pre-instantiated. They integrate directly with `FlowPipeline`:

```python
from aquilia.auth.guards import AuthGuard, RoleGuard
from aquilia.flow import FlowPipeline

pipeline = FlowPipeline("admin_request")
pipeline.guard(AuthGuard)              # Class reference
pipeline.guard(RoleGuard("admin"))      # Pre-instantiated with parameters
```

---

## Context-First Decorators

In controllers, you can protect handlers using decorators. These decorators inspect the incoming `RequestCtx` (or argument list) to resolve the identity, and execute the matching guard checks.

### 1. `@authenticated`
Requires that the incoming request is authenticated (either via a valid token or an active session).

```python
from aquilia import Controller, GET, RequestCtx, Response, authenticated

class ProfileController(Controller):
    @GET("/me")
    @authenticated
    async def show_profile(self, ctx: RequestCtx) -> Response:
        # Injected identity is accessible via ctx.identity
        return Response.json(ctx.identity.to_dict())
```

### 2. `@roles_required`
Requires that the authenticated identity holds the specified roles. Supports checking against role inheritance when a `PermissionEngine` is registered.

```python
from aquilia import Controller, POST, RequestCtx, Response, roles_required

class SettingsController(Controller):
    @POST("/admin/settings")
    @roles_required("superadmin", "administrator", require_all=False)
    async def update_settings(self, ctx: RequestCtx) -> Response:
        return Response.json({"status": "updated"})
```

### 3. `@scopes_required`
Enforces OAuth2/API key scopes.

```python
from aquilia import Controller, GET, RequestCtx, Response, scopes_required

class ReportsController(Controller):
    @GET("/reports/financial")
    @scopes_required("reports:read")
    async def download_report(self, ctx: RequestCtx) -> Response:
        return Response.json({"data": []})
```

### 4. `@optional_auth`
Attempts to authenticate the request but does *not* reject it if authentication fails. Ideal for public endpoints that customize output when a logged-in user is detected.

```python
from aquilia import Controller, GET, RequestCtx, Response, optional_auth

class FeedController(Controller):
    @GET("/feed")
    @optional_auth
    async def get_feed(self, ctx: RequestCtx) -> Response:
        if ctx.identity:
            return Response.json(await self.get_personalized_feed(ctx.identity))
        return Response.json(await self.get_public_feed())
```

---

## The `@requires` Decorator

For complex scenarios where you need to compose multiple guards in a specific order, use the `@requires` decorator. It accepts both guard classes and instances:

```python
from aquilia.auth.guards import AuthGuard, RoleGuard, ScopeGuard, requires

@requires(AuthGuard, RoleGuard("editor"), ScopeGuard("publish"))
async def publish_article(ctx: RequestCtx) -> Response:
    ...
```
Guards are evaluated in the order they are passed, and the first fault raised stops execution.
