# Session Security Hardening

One of the most important security enhancements in Aquilia v1.3.1 is the hardening of session-based authentication.

## The Privilege Escalation Problem (Stale Sessions)

In older versions of the framework, when a user logged in, their full details (including roles, permissions, scopes, and attributes) were serialized and written directly into the session store:

```python
# Old, unsafe behavior in v1.3.0:
session["roles"] = identity.get_attribute("roles", [])
session["scopes"] = identity.get_attribute("scopes", [])
session["attributes"] = identity.attributes
```

While this saved database lookups, it introduced a critical vulnerability: **privilege changes were not dynamic**. If an administrator revoked a role or banned a user, the user would still retain their privileges until their session cookie expired (often days or weeks later), because the middleware read permissions directly from the cookie/session storage.

---

## The New Session Binding Lifecycle

In Aquilia v1.3.1, `bind_identity()` has been redesigned to only store core identifiers:

```python
# New, hardened behavior in v1.3.1:
session.mark_authenticated(AuthPrincipal.from_identity(identity))
session["identity_id"] = identity.id
if identity.tenant_id is not None:
    session["tenant_id"] = identity.tenant_id
```

Notice that **roles, scopes, and user attributes are no longer written to the session store**.

### Active Identity Resolution

When a request arrives:
1. `SessionBackend` reads the `identity_id` from the active session.
2. It queries the `IdentityStore` to resolve the fresh `Identity` object.
3. The resolved `Identity` object is attached to `ctx.identity`.
4. Role and scope checks (like `@roles_required`) are performed against this fresh object.

This ensures that:
* **Instant Revocation**: If a role is revoked or a user is deactivated in the database/cache, it takes effect on their very next HTTP request.
* **Single Source of Truth**: There is no divergence between active sessions and the database/cache identity state.
* **Minimal Cookie Size**: Session payloads are significantly smaller, saving bandwidth on every request.
