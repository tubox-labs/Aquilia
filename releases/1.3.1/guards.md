# Unified Authorization, Guards & Decorators

Aquilia v1.3.1 consolidates authentication checks and authorization strategies into a unified API.

---

## 1. Unified `PermissionEngine`

The `PermissionEngine` (defined in `aquilia.auth.permissions`) is the central engine for evaluating roles, scopes, and policies. It replaces five separate historical systems and runs check assertions that raise appropriate exceptions on denial.

### Core API & Capabilities

* **DAG Role Hierarchies**: Define roles that inherit permissions and access from other roles.
  ```python
  engine = PermissionEngine()
  engine.define_role("editor", permissions=["posts:edit"])
  engine.define_role("admin", inherits=["editor"], permissions=["users:delete"])
  
  # admin implies editor
  assert engine.role_implies("admin", "editor") is True
  ```
* **Dynamic Policies**: Register arbitrary policy callables that evaluate access against a user and resource.
  ```python
  engine.register_policy(
      "can_edit_post",
      lambda identity, post: identity.id == post.author_id or identity.has_role("admin")
  )
  ```
* **Assertive Checks**:
  * `check_role(identity, role)`: Raises `AUTHZ_INSUFFICIENT_ROLE` if role is not met.
  * `check_scope(identity, scope)`: Raises `AUTHZ_INSUFFICIENT_SCOPE` if scope is absent.
  * `check_policy(key, identity, resource=None)`: Raises `AUTHZ_POLICY_DENIED` if policy returns `False`.

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
