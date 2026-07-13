# Unified Authorization, Middleware & Decorators

Aquilia v1.3.1 unifies identity resolution and request-scoped checks into a single middleware and permission engine.

---

## 1. Unified `PermissionEngine`

The `PermissionEngine` (defined in `aquilia.auth.permissions`) is the central engine for evaluating roles, scopes, and policies. It replaces five separate historical systems and runs check assertions that raise appropriate exceptions on denial.

### Core API Methods

* `define_role(role: str, *, permissions: list[str] | None = None, inherits: list[str] | None = None) -> None`: Declare a role and its transitively implied parents.
* `role_implies(role: str, target: str) -> bool`: Query the role DAG structure.
* `register_policy(key: str, policy: PolicyCallable) -> None`: Define a rule matching the signature `(identity, resource) -> bool`.
* `check_role(identity: Identity, role: str) -> None`: Asserts role ownership; raises `AUTHZ_INSUFFICIENT_ROLE` on failure.
* `check_scope(identity: Identity, scope: str) -> None`: Asserts scope ownership; raises `AUTHZ_INSUFFICIENT_SCOPE` on failure.
* `check_policy(key: str, identity: Identity, resource: Any = None) -> None`: Asserts policy assertion passes; raises `AUTHZ_POLICY_DENIED` on failure.
* `has_role(identity: Identity, role: str) -> bool`: Returns a boolean indicating role membership.
* `has_scope(identity: Identity, scope: str) -> bool`: Returns a boolean indicating scope membership.
* `evaluate_policy(key: str, identity: Identity, resource: Any = None) -> bool`: Returns a boolean indicating policy result.

---

## 2. Pluggable Flow Guards

Guards (defined in `aquilia.auth.guards`) evaluate context and raise exceptions on denial. They can be placed directly in request pipelines or used as raw classes (for zero-configuration defaults).

### `AuthGuard`
Verifies authentication status.
* **Optional Mode**: When `optional=True`, anonymous users are allowed.
* **Proactive Auth**: If the identity is not yet resolved, `AuthGuard` attempts to proactively extract and authenticate a Bearer token using DI container-resolved `AuthManager`.
* **Signature**: `AuthGuard(auth_manager=None, optional=False)`

### `RoleGuard`
Ensures the identity holds required roles.
* **Resolution**: Uses `PermissionEngine` if found in the DI container; otherwise, falls back to direct membership testing of `identity.get_attribute("roles", [])`.
* **Signature**: `RoleGuard(*roles, engine=None, require_all=True)`

### `ScopeGuard`
Ensures the identity holds required scopes.
* **Wildcards**: Supports the wildcard `"*"` scope.
* **Signature**: `ScopeGuard(*scopes, require_all=True)`

### `PolicyGuard`
Evaluates a policy registered in the permission engine.
* **Signature**: `PolicyGuard(key, engine, resource=None)`

---

## 3. Context-First Decorators

Decorators (defined in `aquilia.auth.decorators`) wrap handlers to execute guard checks and **inject parameters** into the handler's signature (e.g., `identity`, `user`, `session`, `principal`).

### `@authenticated`
Requires an authenticated identity.
* **Browser Redirection**: If a request is anonymous, has `redirect_if_html=True` or `login_url` configured, and accepts HTML, it performs a `303 Redirect` to the login page with a `next` query parameter.
* **Signature**:
  ```python
  def authenticated(
      func=None,
      *,
      login_url: str | None = None,
      redirect_if_html: bool = False,
      include_next: bool = True,
      next_param: str = "next",
      redirect_status: int = 303,
  )
  ```

### `@roles_required` / `@scopes_required`
Evaluates role or scope conditions before executing the controller action.
```python
@roles_required("admin", "editor", require_all=False)
async def delete_post(self, ctx: RequestCtx) -> Response:
    ...
```

### `@optional_auth`
Evaluates the proactive `AuthGuard(optional=True)` check. It injects the user if found but does not block anonymous traffic.

### `@requires`
Composes multiple guards (both classes and instances) sequentially:
```python
@requires(AuthGuard, RoleGuard("admin"))
async def admin_only_action(self, ctx: RequestCtx) -> Response:
    ...
```

---

## 4. Unified `AuthMiddleware`

The new unified `AuthMiddleware` (defined in `aquilia.auth.middleware`) coordinates credential resolution from backends on every incoming request.

* **Signatures & Parameters**:
  ```python
  def __init__(
      self,
      auth_manager: AuthManager,
      session_engine: SessionEngine | None = None,
      *,
      require_auth: bool = False,
      backends: list[AuthBackend] | None = None,
      logger: logging.Logger | None = None,
  )
  ```
* **Execution Flow**:
  1. **Phase 1: Session Resolution**: If `session_engine` is provided, resolves the session and binds it to `ctx.session` and `request.state["session"]`.
  2. **Phase 2: Credentials Extraction**: Extracts Bearer token, ApiKey, or Session from the request.
  3. **Phase 3: Backend Authentication**: Loops through pluggable `backends` (defaults to `TokenBackend` and `SessionBackend`). The first backend that accepts the credentials and returns an `Identity` completes the phase.
  4. **Phase 4: Requirement Enforcement**: If `require_auth=True` and no identity is resolved, returns a `401 Unauthorized` response immediately.
  5. **Phase 5: Propagation**: Propagates the resolved identity to `request.state["identity"]`, `request.state["authenticated"]`, and `ctx.identity`.
  6. **Phase 6: Downstream Execution**: Calls the next handler in the ASGI middleware chain.
  7. **Phase 7: Session Commitment**: Commits session modifications back to the storage adapter.
