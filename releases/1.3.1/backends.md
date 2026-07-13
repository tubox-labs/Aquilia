# Pluggable Authentication Backends

In Aquilia v1.3.1, authentication is driven by **Backends**. A backend is a class that implements the `AuthBackend` protocol. It is responsible for inspecting a request's credentials and resolving them to an `Identity`.

## The `AuthBackend` Protocol

The `AuthBackend` protocol is a runtime checkable `Protocol` defined in `aquilia.auth.backends.base`:

```python
from typing import Any, Protocol, runtime_checkable
from aquilia.auth.core import Identity

@runtime_checkable
class AuthBackend(Protocol):
    def accepts(self, credentials: dict[str, Any]) -> bool:
        """Return True if the backend supports the provided credentials."""
        ...

    async def authenticate(self, credentials: dict[str, Any]) -> Identity | None:
        """Verify credentials and resolve them to an Identity."""
        ...
```

---

## Built-in Backends

Aquilia comes with four built-in backends:

### 1. `TokenBackend`
Validates JWT Bearer tokens extracted from the `Authorization: Bearer <token>` header. It validates the signature, check claims (e.g. expiration, audience), and checks if the token has been revoked via `TokenManager`.
* **Accepts**: `{"token": str}`

### 2. `SessionBackend`
Restores identity from an active session (cookie-based). It reads the `identity_id` from the session data and fetches the up-to-date user principal from the `IdentityStore`.
* **Accepts**: `{"session": Session}`

### 3. `PasswordBackend`
Authenticates a user via their username and raw password. It performs rate-limiting checks, retrieves the hashed password from the `CredentialStore`, and verifies it using the Argon2id/PBKDF2 `PasswordHasher`.
* **Accepts**: `{"username": str, "password": str}`

### 4. `ApiKeyBackend`
Validates custom API keys from either the `x-api-key` header or `Authorization: ApiKey <key>`. It queries the `CredentialStore` to resolve the associated identity.
* **Accepts**: `{"api_key": str}`

---

## Writing a Custom Backend

Custom backends are easy to write. For example, to write an LDAP or OAuth backend:

```python
from typing import Any
from aquilia.auth.backends import AuthBackend
from aquilia.auth.core import Identity, IdentityType, IdentityStatus

class LdapAuthBackend:
    def __init__(self, ldap_client: Any, identity_store: Any) -> None:
        self.ldap_client = ldap_client
        self.identity_store = identity_store

    def accepts(self, credentials: dict[str, Any]) -> bool:
        # This backend accepts LDAP-specific credentials
        return "username" in credentials and "password" in credentials and credentials.get("auth_type") == "ldap"

    async def authenticate(self, credentials: dict[str, Any]) -> Identity | None:
        username = credentials["username"]
        password = credentials["password"]
        
        # Verify against LDAP server
        if not await self.ldap_client.verify(username, password):
            return None
            
        # Resolve identity from the internal store or auto-provision
        identity = await self.identity_store.get_by_username(username)
        if not identity:
            identity = await self.identity_store.create(
                id=f"ldap_{username}",
                type=IdentityType.USER,
                attributes={"roles": ["staff"]},
                status=IdentityStatus.ACTIVE,
            )
        return identity
```

## Configuring Backends

Backends are registered in `workspace.py` using dotted paths, classes, or short names:

```python
class auth(AquilaConfig.Auth):
    secret_key = Secret(env="AQ_SECRET_KEY", default="change-me")
    backends = [
        "aquilia.auth.backends.TokenBackend",
        "my_project.auth.backends.LdapAuthBackend",
        "session",  # short name resolves to SessionBackend
    ]
```
