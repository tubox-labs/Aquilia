# Session Security Hardening & Integration

Aquilia v1.3.1 introduces substantial security improvements to cookie-based and session-based authentication to prevent privilege escalation.

---

## 1. Stale Session Authorization Bypass

In previous versions of Aquilia, the full set of user roles, scopes, and attributes was serialized and stored directly inside the session store database (or client-side cookie):

```python
# Old, insecure v1.3.0 implementation:
session["roles"] = identity.get_attribute("roles", [])
session["scopes"] = identity.get_attribute("scopes", [])
session["status"] = identity.status.value
```

This optimization meant that if an administrator modified a user's permissions, suspended their account, or deleted them, the changes **would not take effect** for requests authenticated via session cookies until their session expired.

---

## 2. Stateless Serialization & Dynamic Resolution

In Aquilia v1.3.1, session serialization has been hardened. The `bind_identity` function only writes core identifiers:

```python
# Hardened v1.3.1 implementation:
session.mark_authenticated(AuthPrincipal.from_identity(identity))
session["identity_id"] = identity.id
if identity.tenant_id is not None:
    session["tenant_id"] = identity.tenant_id
```

### Identity Resolution Flow
1. The `SessionBackend` captures the active session credentials.
2. It extracts the `identity_id` (either from `session.principal` or from `session.data["identity_id"]`).
3. It fetches a fresh `Identity` object directly from the `IdentityStore` on **every single request**.
4. Authorization guards evaluate roles and scopes against this fresh database/cache state.

Any changes to user permissions or status are applied **instantly** on the user's next request.

---

## 3. The `AuthPrincipal` Class

The `AuthPrincipal` (defined in `aquilia.auth.integration.aquila_sessions`) represents the authenticated subject within the session context:

```python
class AuthPrincipal(SessionPrincipal):
    def __init__(
        self,
        identity_id: str,
        tenant_id: str | None = None,
        roles: list[str] | None = None,
        scopes: list[str] | None = None,
        mfa_verified: bool = False,
    )
```

It is serialized to session dictionaries as:
* `principal_id` (maps to `identity_id`)
* `tenant_id`
* `roles` (ephemeral)
* `scopes` (ephemeral)
* `mfa_verified` (indicates if MFA challenge was completed during this session)

---

## 4. Preconfigured Session Policies

Three preconfigured session policies are exposed out-of-the-box:

* **`user_session_policy`**: Default for browser-based user sessions. Configured with a 7-day TTL, 1-hour idle timeout, a limit of 5 concurrent sessions per user (evicting oldest), and secure HTTP-only cookies (`aquilia_auth`).
* **`api_session_policy`**: Default for API token sessions. Configured with a 1-hour TTL, no idle timeout, and header transport (`Authorization: Bearer`).
* **`device_session_policy`**: Default for mobile app sessions. Configured with a 90-day TTL, 30-day idle timeout, and custom header transport (`X-Device-Session`).

---

## 5. `SessionAuthBridge`

The `SessionAuthBridge` coordinates actions between `AuthManager` and `SessionEngine`:
* `create_auth_session(identity, request, token_claims=None)`: Resolves and binds authentication credentials to a new session.
* `rotate_on_privilege_escalation(session, response)`: Rotates the session ID (session fixation protection) after an escalating event (such as completing an MFA challenge).
* `logout(session, response)`: Destroys the current session.
* `logout_all_devices(identity_id)`: Revokes and purges all active session identifiers linked to a given identity ID across the session store.
