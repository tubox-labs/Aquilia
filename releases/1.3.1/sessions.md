# Session Security, AuthManager & RateLimiting

Aquilia v1.3.1 introduces substantial security improvements to cookie-based and session-based authentication to prevent privilege escalation, alongside a refined `AuthManager` API and a standalone `RateLimiter` utility.

---

## 1. Session Serialization Hardening

In previous versions of Aquilia, the full set of user roles, scopes, and attributes was serialized and stored directly inside the session store database (or client-side cookie):

```python
# Old, insecure v1.3.0 implementation:
session["roles"] = identity.get_attribute("roles", [])
session["scopes"] = identity.get_attribute("scopes", [])
session["status"] = identity.status.value
```

This optimization meant that if an administrator modified a user's permissions, suspended their account, or deleted them, the changes **would not take effect** for requests authenticated via session cookies until their session expired.

In Aquilia v1.3.1, session serialization has been hardened. The `bind_identity` function only writes core identifiers:

```python
# Hardened v1.3.1 implementation:
session.mark_authenticated(AuthPrincipal.from_identity(identity))
session["identity_id"] = identity.id
if identity.tenant_id is not None:
    session["tenant_id"] = identity.tenant_id
```

Notice that **roles, scopes, and user attributes are no longer written to the session store**.

### Active Identity Resolution
* The `SessionBackend` captures the active session credentials.
* It extracts the `identity_id` (either from `session.principal` or from `session.data["identity_id"]`).
* It fetches a fresh `Identity` object directly from the `IdentityStore` on **every single request**.
* Authorization guards evaluate roles and scopes against this fresh database/cache state.

---

## 2. Shared Manager Types: `RateLimiter`

To protect brute-force paths (such as username/password login), Aquilia v1.3.1 introduces a standalone `RateLimiter` class in `aquilia.auth.manager_types` (and re-exported in `aquilia.auth.manager` for backward compatibility).

* **Constructor & Parameters**:
  ```python
  def __init__(
      self,
      max_attempts: int = 5,
      window_seconds: int = 900,
      lockout_duration: int = 3600,
  )
  ```
  Tracks failed authentication attempts per key (typically a username or IP address) within a sliding time window.
* **Core API Methods**:
  * `record_attempt(key: str) -> None`: Records a failed attempt. If attempts exceed `max_attempts` within the window, locks out the key.
  * `is_locked_out(key: str) -> bool`: Checks if the key is currently locked out.
  * `get_remaining_attempts(key: str) -> int`: Returns attempts left before lockout.
  * `reset(key: str) -> None`: Clears attempt history for the key on successful authentication.

---

## 3. `AuthManager` Refactored APIs

The `AuthManager` class (defined in `aquilia.auth.manager`) is the central coordinator for authentication operations. The following APIs were updated:

### Token Revocation
The token revocation API now supports access tokens by extracting the unique JWT identifier (`jti`) and blacklisting it:
* `async def revoke_token(self, token: str, token_type: str = "refresh") -> None`:
  * If `token_type == "refresh"`, revokes the refresh token directly.
  * If `token_type == "access"`, validates the access token, extracts the `jti` claim, and revokes it so subsequent validations reject it.

### Deprecated `logout()`
* **Signature**: `async def logout(self, identity_id=None, session_id=None, access_token=None, refresh_token=None) -> None`
* **Status**: **Deprecated** in favor of `sign_out()`. Raises a `DeprecationWarning` when called.

---

## 4. `SessionAuthBridge`

The `SessionAuthBridge` coordinates actions between `AuthManager` and `SessionEngine`:
* `create_auth_session(identity, request, token_claims=None)`: Resolves and binds authentication credentials to a new session.
* `rotate_on_privilege_escalation(session, response)`: Rotates the session ID (session fixation protection) after an escalating event (such as completing an MFA challenge).
* `logout(session, response)`: Destroys the current session.
* `logout_all_devices(identity_id)`: Revokes and purges all active session identifiers linked to a given identity ID across the session store.
