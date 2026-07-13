# Migration Guide: v1.3.0 to v1.3.1

Aquilia v1.3.1 consolidates and standardizes authentication and authorization. Follow this guide to upgrade your project.

---

## 1. Upgrading Configuration

The string-based `strategies` setting has been removed. You must now configure the list of identity-resolution backends using the `backends` parameter. Additionally, the rate-limiting and MFA settings have been promoted to direct configuration parameters on `AquilaConfig.Auth`.

### Legacy Configuration (v1.3.0)
```python
class auth(AquilaConfig.Auth):
    secret_key = Secret(env="AQ_SECRET_KEY", default="change-me")
    strategies = ["token", "session"]
```

### Refactored Configuration (v1.3.1)
```python
class auth(AquilaConfig.Auth):
    secret_key = Secret(env="AQ_SECRET_KEY", default="change-me")
    backends = [
        "aquilia.auth.backends.TokenBackend",
        "aquilia.auth.backends.SessionBackend",
    ]
    # Store type: "memory" or "redis"
    store_type = "memory"
    
    # Rate Limiting configuration parameters
    rate_limit_max_attempts = 5
    rate_limit_window_seconds = 900
    rate_limit_lockout_seconds = 3600
    
    # MFA settings
    mfa_enabled = False
    mfa_required = False
    
    # Clock skew tolerance (in seconds) for JWT validations
    clock_skew_seconds = 5
    
    # Audit trail activation
    audit_enabled = True
```

---

## 2. Replaced & Removed Decorators

The legacy decorators `AdminGuard` and `VerifiedEmailGuard` have been removed.

* **`AdminGuard`**: Replace with `@roles_required("admin")`.
* **`VerifiedEmailGuard`**: Handle verification checks in your identity resolution backend (such as deactivating unverified users) or write a simple custom guard.

#### Before:
```python
from aquilia.auth import AdminGuard

@AdminGuard
async def delete_item(ctx):
    ...
```

#### After:
```python
from aquilia.auth import roles_required

@roles_required("admin")
async def delete_item(ctx):
    ...
```

---

## 3. Upgrading Flow Pipeline Guards

All legacy guard adapters (historically located in `flow_guards.py`) have been removed. Use the new first-class guards directly.

| Legacy Guard Class (v1.3.0) | Refactored Guard Class (v1.3.1) |
|---|---|
| `RequireAuthGuard` | `AuthGuard` |
| `RequireRolesGuard` | `RoleGuard` |
| `RequireScopesGuard` | `ScopeGuard` |
| `RequirePolicyGuard` | `PolicyGuard` |

### Pipeline Registration Example

#### Before:
```python
from aquilia.auth.integration.flow_guards import RequireAuthGuard, RequireRolesGuard

pipeline.guard(RequireAuthGuard())
pipeline.guard(RequireRolesGuard("admin"))
```

#### After:
```python
from aquilia.auth.guards import AuthGuard, RoleGuard

# Raw classes can be passed if no parameters are required
pipeline.guard(AuthGuard)
pipeline.guard(RoleGuard("admin"))
```

---

## 4. Upgrading Session Guards

The legacy `SessionGuard` class and `@requires` decorator in `aquilia.sessions.decorators` have been removed. Switch to the unified `PermissionEngine` and the unified `@requires` decorator.

#### Before:
```python
from aquilia.sessions.decorators import SessionGuard, requires

class CustomSessionGuard(SessionGuard):
    async def check(self, session: Session) -> bool:
        return bool(session.data.get("special_user"))

@requires(CustomSessionGuard())
async def handler(ctx):
    ...
```

#### After:
```python
from aquilia.auth.guards import requires

class CustomGuard:
    def check(self, ctx: Any) -> None:
        from aquilia.auth.faults import AUTHZ_POLICY_DENIED
        session = getattr(ctx, "session", None)
        if session is None or not session.data.get("special_user"):
            raise AUTHZ_POLICY_DENIED()

@requires(CustomGuard())
async def handler(ctx):
    ...
```

---

## 5. Removing the Fluent `AuthConfig` Builder

If you set up custom authentication containers in testing or bootstrapping scripts using the `AuthConfig` builder, you must remove it. Configure integrations directly using dictionary payloads or the `AquilaConfig.Auth` classes.

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

---

## 6. Deprecated APIs & Relocations

* **`AuthManager.logout()`**: Deprecated in favor of `AuthManager.sign_out()`. Calling `logout()` now raises a `DeprecationWarning` but will invoke `sign_out()` internally for backward compatibility.
* **`OptionalAuthMiddleware`**: Deprecated in favor of `AquilAuthMiddleware(require_auth=False)` or the new `AuthMiddleware` class.
* **`RateLimiter` relocation**: The `RateLimiter` class has been moved from the `manager` module to `aquilia.auth.manager_types` to prevent circular imports. Update imports if you reference it directly.
