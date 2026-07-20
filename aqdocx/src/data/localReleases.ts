export const localReleases: Record<string, Record<string, string>> = {
  "1.3.1": {
    "README.md": `# Aquilia v1.3.1 Release Notes — "Backend Refactoring"

Aquilia v1.3.1 introduces a major rewrite of the authentication (\`aquilia.auth\`) and authorization subsystems. It moves away from rigid string-based strategies and hardcoded guard adapters in favor of a pluggable, class-based backend architecture, a unified permission engine, hardened session serialization, and token clock-skew tolerance.

## Table of Contents

1. [Pluggable Authentication Backends](backends.md)
   * The new \`AuthBackend\` protocol.
   * Built-in backends: \`TokenBackend\`, \`SessionBackend\`, \`PasswordBackend\`, \`ApiKeyBackend\`.
   * The \`resolve_backend\` helper and loading configuration.
2. [Unified Permission & Authorization Engine](guards.md#permissionengine)
   * Role DAG (Directed Acyclic Graph) inheritance.
   * Policy callables and scope checks.
   * Pluggable Flow Guards: \`AuthGuard\`, \`RoleGuard\`, \`ScopeGuard\`, \`PolicyGuard\`.
   * Context-First Decorators: \`@authenticated\`, \`@roles_required\`, \`@scopes_required\`, \`@optional_auth\`.
3. [Session Security Hardening](sessions.md)
   * Elimination of stale permission state in session cookies.
   * The lightweight \`AuthPrincipal\` serialization format.
   * Dynamic resolution of roles and scopes on every request.
4. [Migration Guide](migration.md)
   * Upgrading configuration settings from \`strategies\` to \`backends\`.
   * Replaced classes, decorators, and middleware.

---

## Key Refactoring Goals

1. **Pluggability**: Unify all authentication strategies (Bearer JWTs, Session cookies, Username/Password, API keys) under a single, reusable backend protocol.
2. **Dynamic Privileges**: Resolve permissions, roles, and scopes fresh from the database or cache on every request, preventing privilege escalation through stale session states.
3. **API Simplification**: Consolidate five parallel authorization subsystems (RBAC, ABAC, Clearance, Policy DSL, and custom adapters) into a single, cohesive \`PermissionEngine\`.
4. **Resiliency**: Handle clock drift in distributed clusters by introducing native clock-skew tolerance.
5. **DI Scope Performance**: Deprecate the class/object-based \`ServiceScope\` Enum in favor of high-performance raw string literals backed by \`typing.Literal\` to eliminate import-time namespace scanning and runtime attribute lookup overhead.`,

    "backends.md": `# Pluggable Authentication Backends

In Aquilia v1.3.1, the authentication workflow is decomposed into single-responsibility **Backends**. A backend is a class that conforms to the \`AuthBackend\` protocol. It is responsible for accepting a credential dictionary and resolving it to an \`Identity\`.

## The \`AuthBackend\` Protocol

The \`AuthBackend\` protocol is defined in \`aquilia.auth.backends.base\` using Python's structural subtyping (\`typing.Protocol\`):

\`\`\`python
from typing import Any, Protocol, runtime_checkable
from aquilia.auth.core import Identity

@runtime_checkable
class AuthBackend(Protocol):
    def accepts(self, credentials: dict[str, Any]) -> bool:
        """Return True if the backend supports the provided credentials."""
        ...

    async def authenticate(self, credentials: dict[str, Any]) -> Identity | None:
        """Verify credentials and resolve them to an Identity.
        
        May raise specific auth faults (e.g., AUTH_TOKEN_EXPIRED, AUTH_INVALID_CREDENTIALS).
        """
        ...
\`\`\`

---

## Built-in Backends

Aquilia provides four native backends to cover standard flows:

### 1. \`TokenBackend\`
Validates JWT Bearer tokens. It verifies signatures, checks \`exp\` and \`nbf\` claims (with clock-skew tolerance), and validates token revocation via \`TokenManager\`.
* **Accepted Credentials**: \`{"token": str}\`
* **Constructor**:
  \`\`\`python
  def __init__(self, token_manager: TokenManager, identity_store: IdentityStore)
  \`\`\`

### 2. \`SessionBackend\`
Restores identity from a cookie-backed session. It looks up the \`identity_id\` from the session data or from \`session.principal\`, and fetches the corresponding active identity.
* **Accepted Credentials**: \`{"session": Session}\`
* **Constructor**:
  \`\`\`python
  def __init__(self, identity_store: IdentityStore)
  \`\`\`

### 3. \`PasswordBackend\`
Authenticates user login credentials. It checks for IP/username brute-force lockouts, resolves usernames or email addresses to an identity, compares password hashes, handles password re-hashing when algorithm parameters upgrade, and checks for multi-factor authentication (MFA) requirements.
* **Accepted Credentials**: \`{"username": str, "password": str}\`
* **Constructor**:
  \`\`\`python
  def __init__(
      self,
      identity_store: IdentityStore,
      credential_store: CredentialStore,
      password_hasher: PasswordHasher,
      rate_limiter: RateLimiter | None = None,
      login_attributes: tuple[str, ...] = ("email", "username", "login"),
  )
  \`\`\`

### 4. \`ApiKeyBackend\`
Authenticates API requests via an opaque API key. It hashes the incoming key using \`HMAC-SHA256\` for lookup, checks expiration and revocation status, and verifies that the key carries the required scopes if requested.
* **Accepted Credentials**: \`{"api_key": str, "required_scopes": list[str] | None}\`
* **Constructor**:
  \`\`\`python
  def __init__(self, credential_store: CredentialStore, identity_store: IdentityStore)
  \`\`\`

---

## The Backend Resolver

To simplify instantiation, the \`resolve_backend\` function maps string identifiers, class references, or dotted import paths to their instantiated backends:

\`\`\`python
def resolve_backend(b: Any, auth_manager: Any) -> Any:
    """Resolve a backend reference (instance, class, short name, or dotted path)
    into an instantiated backend object.
    """
    ...
\`\`\`

It maps:
* Short names: \`"token"\` (TokenBackend), \`"session"\` (SessionBackend), \`"password"\` (PasswordBackend), \`"api_key"\` (ApiKeyBackend).
* Class references: \`TokenBackend\`, \`SessionBackend\`, \`PasswordBackend\`, \`ApiKeyBackend\`.
* Dotted paths: \`"my_app.auth.backends.CustomBackend"\`.

### Example Configuration in \`workspace.py\`

\`\`\`python
class auth(AquilaConfig.Auth):
    secret_key = Secret(env="AQ_SECRET_KEY", default="change-me")
    backends = [
        "aquilia.auth.backends.TokenBackend",
        "aquilia.auth.backends.SessionBackend",
        "my_project.auth.CustomBackendClass",  # Dotted class path
    ]
\`\`\``,

    "guards.md": `# Unified Authorization, Middleware & Decorators

Aquilia v1.3.1 unifies identity resolution and request-scoped checks into a single middleware and permission engine.

---

## 1. Unified \`PermissionEngine\`

The \`PermissionEngine\` (defined in \`aquilia.auth.permissions\`) is the central engine for evaluating roles, scopes, and policies. It replaces five separate historical systems and runs check assertions that raise appropriate exceptions on denial.

### Core API Methods

* \`define_role(role: str, *, permissions: list[str] | None = None, inherits: list[str] | None = None) -> None\`: Declare a role and its transitively implied parents.
* \`role_implies(role: str, target: str) -> bool\`: Query the role DAG structure.
* \`register_policy(key: str, policy: PolicyCallable) -> None\`: Define a rule matching the signature \`(identity, resource) -> bool\`.
* \`check_role(identity: Identity, role: str) -> None\`: Asserts role ownership; raises \`AUTHZ_INSUFFICIENT_ROLE\` on failure.
* \`check_scope(identity: Identity, scope: str) -> None\`: Asserts scope ownership; raises \`AUTHZ_INSUFFICIENT_SCOPE\` on failure.
* \`check_policy(key: str, identity: Identity, resource: Any = None) -> None\`: Asserts policy assertion passes; raises \`AUTHZ_POLICY_DENIED\` on failure.
* \`has_role(identity: Identity, role: str) -> bool\`: Returns a boolean indicating role membership.
* \`has_scope(identity: Identity, scope: str) -> bool\`: Returns a boolean indicating scope membership.
* \`evaluate_policy(key: str, identity: Identity, resource: Any = None) -> bool\`: Returns a boolean indicating policy result.

---

## 2. Pluggable Flow Guards

Guards (defined in \`aquilia.auth.guards\`) evaluate context and raise exceptions on denial. They can be placed directly in request pipelines or used as raw classes (for zero-configuration defaults).

### \`AuthGuard\`
Verifies authentication status.
* **Optional Mode**: When \`optional=True\`, anonymous users are allowed.
* **Proactive Auth**: If the identity is not yet resolved, \`AuthGuard\` attempts to proactively extract and authenticate a Bearer token using DI container-resolved \`AuthManager\`.
* **Signature**: \`AuthGuard(auth_manager=None, optional=False)\`

### \`RoleGuard\`
Ensures the identity holds required roles.
* **Resolution**: Uses \`PermissionEngine\` if found in the DI container; otherwise, falls back to direct membership testing of \`identity.get_attribute("roles", [])\`.
* **Signature**: \`RoleGuard(*roles, engine=None, require_all=True)\`

### \`ScopeGuard\`
Ensures the identity holds required scopes.
* **Wildcards**: Supports the wildcard \`"*"\` scope.
* **Signature**: \`ScopeGuard(*scopes, require_all=True)\`

### \`PolicyGuard\`
Evaluates a policy registered in the permission engine.
* **Signature**: \`PolicyGuard(key, engine, resource=None)\`

---

## 3. Context-First Decorators

Decorators (defined in \`aquilia.auth.decorators\`) wrap handlers to execute guard checks and **inject parameters** into the handler's signature (e.g., \`identity\`, \`user\`, \`session\`, \`principal\`).

### \`@authenticated\`
Requires an authenticated identity.
* **Browser Redirection**: If a request is anonymous, has \`redirect_if_html=True\` or \`login_url\` configured, and accepts HTML, it performs a \`303 Redirect\` to the login page with a \`next\` query parameter.
* **Signature**:
  \`\`\`python
  def authenticated(
      func=None,
      *,
      login_url: str | None = None,
      redirect_if_html: bool = False,
      include_next: bool = True,
      next_param: str = "next",
      redirect_status: int = 303,
  )
  \`\`\`

### \`@roles_required\` / \`@scopes_required\`
Evaluates role or scope conditions before executing the controller action.
\`\`\`python
@roles_required("admin", "editor", require_all=False)
async def delete_post(self, ctx: RequestCtx) -> Response:
    ...
\`\`\`

### \`@optional_auth\`
Evaluates the proactive \`AuthGuard(optional=True)\` check. It injects the user if found but does not block anonymous traffic.

### \`@requires\`
Composes multiple guards (both classes and instances) sequentially:
\`\`\`python
@requires(AuthGuard, RoleGuard("admin"))
async def admin_only_action(self, ctx: RequestCtx) -> Response:
    ...
\`\`\`

---

## 4. Unified \`AuthMiddleware\`

The new unified \`AuthMiddleware\` (defined in \`aquilia.auth.middleware\`) coordinates credential resolution from backends on every incoming request.

* **Signatures & Parameters**:
  \`\`\`python
  def __init__(
      self,
      auth_manager: AuthManager,
      session_engine: SessionEngine | None = None,
      *,
      require_auth: bool = False,
      backends: list[AuthBackend] | None = None,
      logger: logging.Logger | None = None,
  )
  \`\`\`
* **Execution Flow**:
  1. **Phase 1: Session Resolution**: If \`session_engine\` is provided, resolves the session and binds it to \`ctx.session\` and \`request.state["session"]\`.
  2. **Phase 2: Credentials Extraction**: Extracts Bearer token, ApiKey, or Session from the request.
  3. **Phase 3: Backend Authentication**: Loops through pluggable \`backends\` (defaults to \`TokenBackend\` and \`SessionBackend\`). The first backend that accepts the credentials and returns an \`Identity\` completes the phase.
  4. **Phase 4: Requirement Enforcement**: If \`require_auth=True\` and no identity is resolved, returns a \`401 Unauthorized\` response immediately.
  5. **Phase 5: Propagation**: Propagates the resolved identity to \`request.state["identity"]\`, \`request.state["authenticated"]\`, and \`ctx.identity\`.
  6. **Phase 6: Downstream Execution**: Calls the next handler in the ASGI middleware chain.
  7. **Phase 7: Session Commitment**: Commits session modifications back to the storage adapter.`,

    "migration.md": `# Migration Guide: v1.3.0 to v1.3.1

Aquilia v1.3.1 consolidates and standardizes authentication and authorization. Follow this guide to upgrade your project.

---

## 1. Upgrading Configuration

The string-based \`strategies\` setting has been removed. You must now configure the list of identity-resolution backends using the \`backends\` parameter. Additionally, the rate-limiting and MFA settings have been promoted to direct configuration parameters on \`AquilaConfig.Auth\`.

### Legacy Configuration (v1.3.0)
\`\`\`python
class auth(AquilaConfig.Auth):
    secret_key = Secret(env="AQ_SECRET_KEY", default="change-me")
    strategies = ["token", "session"]
\`\`\`

### Refactored Configuration (v1.3.1)
\`\`\`python
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
\`\`\`

---

## 2. Replaced & Removed Decorators

The legacy decorators \`AdminGuard\` and \`VerifiedEmailGuard\` have been removed.

* **\`AdminGuard\`**: Replace with \`@roles_required("admin")\`.
* **\`VerifiedEmailGuard\`**: Handle verification checks in your identity resolution backend (such as deactivating unverified users) or write a simple custom guard.

#### Before:
\`\`\`python
from aquilia.auth import AdminGuard

@AdminGuard
async def delete_item(ctx):
    ...
\`\`\`

#### After:
\`\`\`python
from aquilia.auth import roles_required

@roles_required("admin")
async def delete_item(ctx):
    ...
\`\`\`

---

## 3. Upgrading Flow Pipeline Guards

All legacy guard adapters (historically located in \`flow_guards.py\`) have been removed. Use the new first-class guards directly.

| Legacy Guard Class (v1.3.0) | Refactored Guard Class (v1.3.1) |
|---|---|
| \`RequireAuthGuard\` | \`AuthGuard\` |
| \`RequireRolesGuard\` | \`RoleGuard\` |
| \`RequireScopesGuard\` | \`ScopeGuard\` |
| \`RequirePolicyGuard\` | \`PolicyGuard\` |

### Pipeline Registration Example

#### Before:
\`\`\`python
from aquilia.auth.integration.flow_guards import RequireAuthGuard, RequireRolesGuard

pipeline.guard(RequireAuthGuard())
pipeline.guard(RequireRolesGuard("admin"))
\`\`\`

#### After:
\`\`\`python
from aquilia.auth.guards import AuthGuard, RoleGuard

# Raw classes can be passed if no parameters are required
pipeline.guard(AuthGuard)
pipeline.guard(RoleGuard("admin"))
\`\`\`

---

## 4. Upgrading Session Guards

The legacy \`SessionGuard\` class and \`@requires\` decorator in \`aquilia.sessions.decorators\` have been removed. Switch to the unified \`PermissionEngine\` and the unified \`@requires\` decorator.

#### Before:
\`\`\`python
from aquilia.sessions.decorators import SessionGuard, requires

class CustomSessionGuard(SessionGuard):
    async def check(self, session: Session) -> bool:
        return bool(session.data.get("special_user"))

@requires(CustomSessionGuard())
async def handler(ctx):
    ...
\`\`\`

#### After:
\`\`\`python
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
\`\`\`

---

## 5. Removing the Fluent \`AuthConfig\` Builder

If you set up custom authentication containers in testing or bootstrapping scripts using the \`AuthConfig\` builder, you must remove it. Configure integrations directly using dictionary payloads or the \`AquilaConfig.Auth\` classes.

#### Before:
\`\`\`python
from aquilia.auth.integration.di_providers import AuthConfig

config = (
    AuthConfig()
    .rate_limit(max_attempts=3)
    .strategies(["token"])
    .build()
)
\`\`\`

#### After:
\`\`\`python
config = {
    "rate_limit": {
        "max_attempts": 3,
    },
    "security": {
        "backends": ["aquilia.auth.backends.TokenBackend"],
    }
}
\`\`\`

---

## 6. Deprecated APIs & Relocations

* **\`AuthManager.logout()\`**: Deprecated in favor of \`AuthManager.sign_out()\`. Calling \`logout()\` now raises a \`DeprecationWarning\` but will invoke \`sign_out()\` internally for backward compatibility.
* **\`OptionalAuthMiddleware\`**: Deprecated in favor of \`AquilAuthMiddleware(require_auth=False)\` or the new \`AuthMiddleware\` class.
* **\`RateLimiter\` relocation**: The \`RateLimiter\` class has been moved from the \`manager\` module to \`aquilia.auth.manager_types\` to prevent circular imports. Update imports if you reference it directly.
* **\`ServiceScope\` Enum class**: Deprecated in favor of plain string literals (e.g., \`"singleton"\`, \`"app"\`, \`"request"\`, \`"transient"\`, \`"pooled"\`, \`"ephemeral"\`) paired with \`typing.Literal\` type hints (\`ServiceScopeLiteral\`). Using \`ServiceScope.SINGLETON\` or other members will now emit a \`DeprecationWarning\`.`,

    "sessions.md": `# Session Security, AuthManager & RateLimiting

Aquilia v1.3.1 introduces substantial security improvements to cookie-based and session-based authentication to prevent privilege escalation, alongside a refined \`AuthManager\` API and a standalone \`RateLimiter\` utility.

---

## 1. Session Serialization Hardening

In previous versions of Aquilia, the full set of user roles, scopes, and attributes was serialized and stored directly inside the session store database (or client-side cookie):

\`\`\`python
# Old, insecure v1.3.0 implementation:
session["roles"] = identity.get_attribute("roles", [])
session["scopes"] = identity.get_attribute("scopes", [])
session["status"] = identity.status.value
\`\`\`

This optimization meant that if an administrator modified a user's permissions, suspended their account, or deleted them, the changes **would not take effect** for requests authenticated via session cookies until their session expired.

In Aquilia v1.3.1, session serialization has been hardened. The \`bind_identity\` function only writes core identifiers:

\`\`\`python
# Hardened v1.3.1 implementation:
session.mark_authenticated(AuthPrincipal.from_identity(identity))
session["identity_id"] = identity.id
if identity.tenant_id is not None:
    session["tenant_id"] = identity.tenant_id
\`\`\`

Notice that **roles, scopes, and user attributes are no longer written to the session store**.

### Active Identity Resolution
* The \`SessionBackend\` captures the active session credentials.
* It extracts the \`identity_id\` (either from \`session.principal\` or from \`session.data["identity_id"]\`).
* It fetches a fresh \`Identity\` object directly from the \`IdentityStore\` on **every single request**.
* Authorization guards evaluate roles and scopes against this fresh database/cache state.

---

## 2. Shared Manager Types: \`RateLimiter\`

To protect brute-force paths (such as username/password login), Aquilia v1.3.1 introduces a standalone \`RateLimiter\` class in \`aquilia.auth.manager_types\` (and re-exported in \`aquilia.auth.manager\` for backward compatibility).

* **Constructor & Parameters**:
  \`\`\`python
  def __init__(
      self,
      max_attempts: int = 5,
      window_seconds: int = 900,
      lockout_duration: int = 3600,
  )
  \`\`\`
  Tracks failed authentication attempts per key (typically a username or IP address) within a sliding time window.
* **Core API Methods**:
  * \`record_attempt(key: str) -> None\`: Records a failed attempt. If attempts exceed \`max_attempts\` within the window, locks out the key.
  * \`is_locked_out(key: str) -> bool\`: Checks if the key is currently locked out.
  * \`get_remaining_attempts(key: str) -> int\`: Returns attempts left before lockout.
  * \`reset(key: str) -> None\`: Clears attempt history for the key on successful authentication.

---

## 3. \`AuthManager\` Refactored APIs

The \`AuthManager\` class (defined in \`aquilia.auth.manager\`) is the central coordinator for authentication operations. The following APIs were updated:

### Token Revocation
The token revocation API now supports access tokens by extracting the unique JWT identifier (\`jti\`) and blacklisting it:
* \`async def revoke_token(self, token: str, token_type: str = "refresh") -> None\`:
  * If \`token_type == "refresh"\`, revokes the refresh token directly.
  * If \`token_type == "access"\`, validates the access token, extracts the \`jti\` claim, and revokes it so subsequent validations reject it.

### Deprecated \`logout()\`
* **Signature**: \`async def logout(self, identity_id=None, session_id=None, access_token=None, refresh_token=None) -> None\`
* **Status**: **Deprecated** in favor of \`sign_out()\`. Raises a \`DeprecationWarning\` when called.

---

## 4. \`SessionAuthBridge\`

The \`SessionAuthBridge\` coordinates actions between \`AuthManager\` and \`SessionEngine\`:
* \`create_auth_session(identity, request, token_claims=None)\`: Resolves and binds authentication credentials to a new session.
* \`rotate_on_privilege_escalation(session, response)\`: Rotates the session ID (session fixation protection) after an escalating event (such as completing an MFA challenge).
* \`logout(session, response)\`: Destroys the current session.
* \`logout_all_devices(identity_id)\`: Revokes and purges all active session identifiers linked to a given identity ID across the session store.`
  }
};
