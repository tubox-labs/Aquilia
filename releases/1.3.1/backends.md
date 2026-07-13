# Pluggable Authentication Backends

In Aquilia v1.3.1, the authentication workflow is decomposed into single-responsibility **Backends**. A backend is a class that conforms to the `AuthBackend` protocol. It is responsible for accepting a credential dictionary and resolving it to an `Identity`.

## The `AuthBackend` Protocol

The `AuthBackend` protocol is defined in `aquilia.auth.backends.base` using Python's structural subtyping (`typing.Protocol`):

```python
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
```

---

## Built-in Backends

Aquilia provides four native backends to cover standard flows:

### 1. `TokenBackend`
Validates JWT Bearer tokens. It verifies signatures, checks `exp` and `nbf` claims (with clock-skew tolerance), and validates token revocation via `TokenManager`.
* **Accepted Credentials**: `{"token": str}`
* **Constructor**:
  ```python
  def __init__(self, token_manager: TokenManager, identity_store: IdentityStore)
  ```

### 2. `SessionBackend`
Restores identity from a cookie-backed session. It looks up the `identity_id` from the session data or from `session.principal`, and fetches the corresponding active identity.
* **Accepted Credentials**: `{"session": Session}`
* **Constructor**:
  ```python
  def __init__(self, identity_store: IdentityStore)
  ```

### 3. `PasswordBackend`
Authenticates user login credentials. It checks for IP/username brute-force lockouts, resolves usernames or email addresses to an identity, compares password hashes, handles password re-hashing when algorithm parameters upgrade, and checks for multi-factor authentication (MFA) requirements.
* **Accepted Credentials**: `{"username": str, "password": str}`
* **Constructor**:
  ```python
  def __init__(
      self,
      identity_store: IdentityStore,
      credential_store: CredentialStore,
      password_hasher: PasswordHasher,
      rate_limiter: RateLimiter | None = None,
      login_attributes: tuple[str, ...] = ("email", "username", "login"),
  )
  ```

### 4. `ApiKeyBackend`
Authenticates API requests via an opaque API key. It hashes the incoming key using `HMAC-SHA256` for lookup, checks expiration and revocation status, and verifies that the key carries the required scopes if requested.
* **Accepted Credentials**: `{"api_key": str, "required_scopes": list[str] | None}`
* **Constructor**:
  ```python
  def __init__(self, credential_store: CredentialStore, identity_store: IdentityStore)
  ```

---

## The Backend Resolver

To simplify instantiation, the `resolve_backend` function maps string identifiers, class references, or dotted import paths to their instantiated backends:

```python
def resolve_backend(b: Any, auth_manager: Any) -> Any:
    """Resolve a backend reference (instance, class, short name, or dotted path)
    into an instantiated backend object.
    """
    ...
```

It maps:
* Short names: `"token"` (TokenBackend), `"session"` (SessionBackend), `"password"` (PasswordBackend), `"api_key"` (ApiKeyBackend).
* Class references: `TokenBackend`, `SessionBackend`, `PasswordBackend`, `ApiKeyBackend`.
* Dotted paths: `"my_app.auth.backends.CustomBackend"`.

### Example Configuration in `workspace.py`

```python
class auth(AquilaConfig.Auth):
    secret_key = Secret(env="AQ_SECRET_KEY", default="change-me")
    backends = [
        "aquilia.auth.backends.TokenBackend",
        "aquilia.auth.backends.SessionBackend",
        "my_project.auth.CustomBackendClass",  # Dotted class path
    ]
```
