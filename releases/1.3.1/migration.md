# Migration Guide: v1.3.0 to v1.3.1

Aquilia v1.3.1 contains several changes to the authentication subsystem. Follow this guide to upgrade your project.

---

## 1. Update `workspace.py` Configuration

The `strategies` setting has been replaced by `backends`. Dotted paths to classes are preferred, but standard string shorthand is supported.

### Legacy Configuration (v1.3.0)
```python
class auth(AquilaConfig.Auth):
    secret_key = Secret(env="AQ_SECRET_KEY", default="change-me")
    strategies = ["token", "session"]
```

### New Configuration (v1.3.1)
```python
class auth(AquilaConfig.Auth):
    secret_key = Secret(env="AQ_SECRET_KEY", default="change-me")
    backends = [
        "aquilia.auth.backends.TokenBackend",
        "aquilia.auth.backends.SessionBackend",
    ]
```

---

## 2. Update Decorators & Guards

Legacy adapters like `flow_guards` and legacy decorators have been removed.

### Decorator Replacements

| Legacy (v1.3.0) | Refactored (v1.3.1) | Note |
|---|---|---|
| `@authenticated` | `@authenticated` | Retained (ctx-first) |
| `@optional_auth` | `@optional_auth` | Retained (ctx-first) |
| `@roles_required` | `@roles_required` | Retained (ctx-first) |
| `@scopes_required` | `@scopes_required` | Retained (ctx-first) |
| `AdminGuard` | `@roles_required("admin")` | Use `@roles_required` with admin role |
| `VerifiedEmailGuard` | Custom backend / decorator | Handle via custom backend validation |

### Decorator Examples

#### Before:
```python
from aquilia.auth import AdminGuard, VerifiedEmailGuard

@AdminGuard
async def admin_only(ctx):
    ...
```

#### After:
```python
from aquilia.auth import roles_required

@roles_required("admin")
async def admin_only(ctx):
    ...
```

---

## 3. Update Pipeline Guards

If you had flow pipelines defined in `manifest.py` or manually, update the guards from the legacy adapter classes to the new first-class guards.

#### Before:
```python
from aquilia.auth.integration.flow_guards import RequireAuthGuard, RequireRolesGuard

pipeline.guard(RequireAuthGuard())
pipeline.guard(RequireRolesGuard("admin"))
```

#### After:
```python
from aquilia.auth.guards import AuthGuard, RoleGuard

# Raw classes can be used if they don't require parameters
pipeline.guard(AuthGuard)
# Instantiated guards can still be passed
pipeline.guard(RoleGuard("admin"))
```

---

## 4. Remove `AuthConfig` Fluent Builder

If you were setting up custom authentication containers manually using `AuthConfig`, switch to standard dict configurations or define them directly using `AquilaConfig.Auth` subclasses.

#### Before:
```python
from aquilia.auth.integration.di_providers import AuthConfig

config = (
    AuthConfig()
    .rate_limit(max_attempts=3)
    .strategies(["token"])
    .build()
)
```

#### After:
```python
config = {
    "rate_limit": {
        "max_attempts": 3,
    },
    "security": {
        "backends": ["aquilia.auth.backends.TokenBackend"],
    }
}
```
Alternatively, let `ConfigLoader` load it from `workspace.py` natively.
