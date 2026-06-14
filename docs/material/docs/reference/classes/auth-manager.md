# AuthManager

## Overview

`AuthManager` is the central coordinator for all authentication operations. It orchestrates identity verification, password authentication, token issuance/refresh/revocation, session management, and rate limiting. It is designed to be DI-injectable and works with pluggable identity and credential stores.

```python
from aquilia.auth import AuthManager, AuthResult, Identity

auth = AuthManager(token_manager=token_mgr)
result = await auth.authenticate_password("alice@example.com", "s3cret")
```

---

## `AuthManager`

!!! abstract "`aquilia.auth.AuthManager`"

```python
class AuthManager:
    def __init__(
        self,
        token_manager: TokenManager,
        identity_store: IdentityStore | None = None,
        credential_store: CredentialStore | None = None,
        password_hasher: PasswordHasher | None = None,
        rate_limiter: RateLimiter | None = None,
        login_identifier_attributes: tuple[str, ...] | list[str] | None = None,
    ):
```

| Parameter | Type | Default | Description |
|---|---|---|---|
| `token_manager` | `TokenManager` | **Required** | JWT token manager |
| `identity_store` | `IdentityStore \| None` | `MemoryIdentityStore()` | Identity persistence |
| `credential_store` | `CredentialStore \| None` | `MemoryCredentialStore()` | Credential persistence |
| `password_hasher` | `PasswordHasher \| None` | `PasswordHasher()` | Password hashing engine |
| `rate_limiter` | `RateLimiter \| None` | `RateLimiter()` | Brute-force protection |
| `login_identifier_attributes` | `tuple/list \| None` | `("email", "username", "login", "identity_id")` | Fields used for identity lookup |

### Core Methods

```python
async def authenticate_password(
    self,
    username: str,
    password: str,
    scopes: SessionScope | str | list | tuple | set | None = None,
    session_id: str | None = None,
    client_metadata: dict[str, Any] | None = None,
) -> AuthResult:
    """Authenticate with username/password. Returns AuthResult with tokens.
    Raises: AUTH_INVALID_CREDENTIALS, AUTH_ACCOUNT_LOCKED, AUTH_ACCOUNT_SUSPENDED, AUTH_MFA_REQUIRED."""

async def authenticate_api_key(
    self,
    api_key: str,
    scopes: ... | None = None,
) -> AuthResult: ...

async def create_identity(
    self,
    identity_type: IdentityType = IdentityType.USER,
    attributes: dict[str, Any] | None = None,
    *,
    password: str | None = None,
    tenant_id: str | None = None,
) -> Identity: ...
```

### Token Management

```python
async def issue_tokens(
    self,
    identity: Identity,
    *,
    scopes: list[str] | None = None,
    session_id: str | None = None,
) -> AuthResult: ...

async def refresh_token(
    self,
    refresh_token: str,
) -> AuthResult: ...

async def validate_token(
    self,
    access_token: str,
) -> TokenClaims | None: ...

async def revoke_token(
    self,
    token: str,
    *,
    token_type: str = "access",
) -> bool: ...
```

### High-Level Session APIs

```python
async def sign_in(
    self,
    username: str,
    password: str,
    *,
    scopes: ... | None = None,
    session_id: str | None = None,
    identity_seed: Identity | None = None,
    client_metadata: dict[str, Any] | None = None,
    provision_policy: SignInProvisionPolicy | None = None,
) -> AuthResult:
    """Ergonomic request-aware login. Binds identity to runtime session."""

async def sign_out(
    self,
    *,
    scope: SessionScope = SessionScope.ALL,
) -> None:
    """Scoped logout: SESSION / IDENTITY / ALL."""

async def resume_identity(self) -> Identity | None:
    """Restore principal from token or session context."""
```

### Runtime State

```python
def current_session(self) -> Any | None:
    """Return current runtime session."""

def has_active_session(self) -> bool: ...

def current_identity_id(self) -> str | None:
    """Return identity_id from runtime session."""
```

---

## `Identity`

!!! abstract "`aquilia.auth.Identity`"
    Frozen dataclass

```python
@dataclass(frozen=True)
class Identity:
    id: str
    type: IdentityType
    attributes: dict[str, Any]       # email, name, roles, clearance, etc.
    status: IdentityStatus = IdentityStatus.ACTIVE
    tenant_id: str | None = None
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def get_attribute(self, key: str, default: Any = None) -> Any: ...
    def has_role(self, role: str) -> bool: ...
    def has_scope(self, scope: str) -> bool: ...
    def is_active(self) -> bool: ...
    def to_dict(self) -> dict[str, Any]: ...
    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Identity: ...
```

### `IdentityType`

```python
class IdentityType(str, Enum):
    USER = "user"
    SERVICE = "service"
    DEVICE = "device"
    ANONYMOUS = "anonymous"
```

### `IdentityStatus`

```python
class IdentityStatus(str, Enum):
    ACTIVE = "active"
    SUSPENDED = "suspended"
    DELETED = "deleted"
    PENDING = "pending"   # awaiting verification
```

---

## `PasswordHasher`

!!! abstract "`aquilia.auth.PasswordHasher`"

Multi-algorithm hashing with automatic algorithm detection from PHC-format hashes.

```python
class PasswordHasher:
    def __init__(
        self,
        algorithm: str | None = None,
        # Argon2
        time_cost: int = 2,
        memory_cost: int = 65536,
        parallelism: int = 4,
        hash_len: int = 32,
        salt_len: int = 16,
        # scrypt
        scrypt_n: int = 32768,
        scrypt_r: int = 8,
        scrypt_p: int = 1,
        scrypt_dklen: int = 32,
        # bcrypt
        bcrypt_rounds: int = 12,
        # PBKDF2
        pbkdf2_iterations: int = 600000,
        pbkdf2_sha512_iterations: int = 210000,
        pbkdf2_dklen: int = 32,
    ):

    def hash(self, password: str) -> str:
        """Hash a password. Returns PHC-format string."""

    def hash_password(self, password: str) -> str:
        """Alias for hash()."""

    def verify(self, hashed: str, password: str) -> bool:
        """Verify password against hash. Auto-detects algorithm."""

    def verify_password(self, hashed: str, password: str) -> bool:
        """Alias for verify()."""

    def validate_password(self, password: str) -> None:
        """Validate password strength/complexity."""

    def needs_rehash(self, hashed: str) -> bool:
        """Check if hash uses outdated parameters."""

    @classmethod
    def from_config(cls, config: HasherConfig) -> PasswordHasher: ...
```

### `HasherConfig`

```python
@dataclass
class HasherConfig:
    algorithm: str = "argon2id"
    time_cost: int = 2
    memory_cost: int = 65536       # KiB
    parallelism: int = 4
    hash_len: int = 32
    salt_len: int = 16
    scrypt_n: int = 32768
    scrypt_r: int = 8
    scrypt_p: int = 1
    scrypt_dklen: int = 32
    bcrypt_rounds: int = 12
    pbkdf2_iterations: int = 600000
    pbkdf2_sha512_iterations: int = 210000
    pbkdf2_dklen: int = 32

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> HasherConfig: ...
    def to_dict(self) -> dict[str, Any]: ...
```

### Supported Algorithms

| Algorithm | Dependency | Recommendation |
|---|---|---|
| `argon2id` | `pip install argon2-cffi` | **Best** — memory-hard, GPU-resistant, PHC winner |
| `scrypt` | stdlib `hashlib` (3.6+) | Good — memory-hard, zero-dep |
| `bcrypt` | `pip install bcrypt` | Good — time-tested |
| `pbkdf2_sha512` | stdlib `hashlib` | OK — NIST SP 800-132 |
| `pbkdf2_sha256` | stdlib `hashlib` | Legacy fallback |

---

## `TokenManager`

!!! abstract "`aquilia.auth.TokenManager`"

```python
class TokenManager:
    def __init__(
        self,
        secret_key: str,
        *,
        algorithm: str = "HS256",
        issuer: str = "aquilia",
        audience: str = "aquilia-app",
        access_token_ttl: timedelta = timedelta(minutes=60),
        refresh_token_ttl: timedelta = timedelta(days=30),
        key_ring: KeyRing | None = None,
        token_store: TokenStore | None = None,
    ):

    def create_access_token(
        self,
        identity_id: str,
        *,
        scopes: list[str] | None = None,
        extra_claims: dict[str, Any] | None = None,
    ) -> str: ...

    def create_refresh_token(
        self,
        identity_id: str,
        *,
        session_id: str | None = None,
    ) -> str: ...

    def validate(
        self,
        token: str,
        *,
        token_type: str = "access",
    ) -> TokenClaims | None: ...

    def decode(
        self,
        token: str,
        *,
        verify: bool = True,
    ) -> TokenClaims: ...

    async def revoke(
        self,
        token: str,
        *,
        token_type: str = "access",
    ) -> bool: ...

    async def revoke_all_for_identity(self, identity_id: str) -> int: ...
```

### `KeyAlgorithm` Enum

```python
class KeyAlgorithm(str, Enum):
    HS256 = "HS256"   # HMAC-SHA-256 (stdlib, default)
    HS384 = "HS384"
    HS512 = "HS512"
    RS256 = "RS256"   # RSA (requires cryptography)
    ES256 = "ES256"   # ECDSA P-256
    EdDSA = "EdDSA"   # Ed25519
```

### `KeyRing`

```python
class KeyRing:
    """Manages current + fallback signing keys for rotation."""
    def __init__(
        self,
        current_key: str,
        *,
        fallback_keys: list[str] | None = None,
    ):

    @property
    def active_keys(self) -> list[str]:
        """Current key first, then fallbacks."""
```

---

## `ClearanceEngine`

!!! abstract "`aquilia.auth.ClearanceEngine`"

Multi-dimensional, composable, declarative access control.

```python
class ClearanceEngine:
    def __init__(self): ...

    async def check(
        self,
        identity: Any,
        clearance: Clearance,
        request: Any,
        ctx: Any,
    ) -> bool: ...
```

### `Clearance`

```python
@dataclass
class Clearance:
    level: AccessLevel = AccessLevel.AUTHENTICATED
    entitlements: list[str] = field(default_factory=list)
    conditions: list[ClearanceCondition] = field(default_factory=list)
    compartment: str | None = None
```

### `AccessLevel`

```python
class AccessLevel(IntEnum):
    PUBLIC = 0           # No auth required
    AUTHENTICATED = 10   # Any authenticated identity
    INTERNAL = 20        # Internal/staff
    CONFIDENTIAL = 30    # Managers, leads
    RESTRICTED = 40      # Admins, security
```

### Built-in Conditions

```python
def is_verified(identity, request, ctx) -> bool:
    """Identity must have email_verified or ACTIVE status."""

def is_owner_or_admin(identity, request, ctx) -> bool:
    """Resource owner or has admin/superuser role."""

def within_quota(identity, request, ctx) -> bool:
    """Identity hasn't exceeded rate/resource quota."""

def is_same_tenant(identity, request, ctx) -> bool:
    """Identity tenant matches resource tenant."""

def during_hours(identity, request, ctx) -> bool:
    """Request is within allowed time window."""

def require_attribute(attr: str, values: list[str]) -> ClearanceCondition:
    """Identity must have attribute with given value."""

def ip_allowlist(allowed: list[str]) -> ClearanceCondition:
    """Client IP must be in allowlist."""
```

---

## Guards

### `@authenticated` Decorator

```python
def authenticated(
    handler=None,
    *,
    scopes: list[str] | None = None,
    require_verified: bool = False,
):
```

```python
@GET("/profile")
@authenticated(scopes=["profile:read"])
async def get_profile(self, ctx):
    ...
```

### `AdminGuard`

```python
class AdminGuard:
    def __init__(self, *, superuser_only: bool = False):
    async def __call__(self, request, ctx, next_handler) -> Response:
```

### `VerifiedEmailGuard`

```python
class VerifiedEmailGuard:
    async def __call__(self, request, ctx, next_handler) -> Response:
```

---

## `MFAManager`

!!! abstract "`aquilia.auth.MFAManager`"

```python
class MFAManager:
    def __init__(self, *,
                 issuer: str = "Aquilia",
                 totp_window: int = 1,
                 backup_codes_count: int = 8):

    def generate_totp_secret(self) -> str: ...
    def get_totp_uri(self, secret: str, identity_id: str) -> str: ...
    def verify_totp(self, secret: str, code: str) -> bool: ...
    def generate_backup_codes(self, identity_id: str) -> list[str]: ...
    async def enroll(self, identity_id: str) -> MFAEnrollment: ...
    async def verify(self, identity_id: str, code: str) -> bool: ...
    async def is_enrolled(self, identity_id: str) -> bool: ...
    async def disable(self, identity_id: str) -> None: ...
```

---

## `OAuth2Manager`

!!! abstract "`aquilia.auth.OAuth2Manager`"

```python
class OAuth2Manager:
    def __init__(
        self,
        *,
        providers: dict[str, OAuth2Provider] | None = None,
        callback_base_url: str = "",
    ):

    def register_provider(self, name: str, provider: OAuth2Provider) -> None: ...
    def get_authorization_url(self, provider_name: str, state: str | None = None) -> str: ...
    async def exchange_code(self, provider_name: str, code: str) -> OAuth2Token: ...
    async def get_user_info(self, provider_name: str, token: OAuth2Token) -> dict[str, Any]: ...
```

---

## `AuditTrail`

!!! abstract "`aquilia.auth.AuditTrail`"

```python
class AuditTrail:
    def __init__(self, *, store: AuditStore | None = None):

    async def record(
        self,
        event: str,
        *,
        identity_id: str | None = None,
        resource: str | None = None,
        action: str | None = None,
        outcome: str = "success",
        metadata: dict[str, Any] | None = None,
        request_id: str | None = None,
    ) -> None: ...

    async def query(
        self,
        *,
        identity_id: str | None = None,
        event: str | None = None,
        since: datetime | None = None,
        until: datetime | None = None,
        limit: int = 100,
    ) -> list[AuditRecord]: ...
```

---

## Stores (Protocols)

```python
class IdentityStore(Protocol):
    async def get(self, identity_id: str) -> Identity | None: ...
    async def get_by_attribute(self, attr: str, value: str) -> Identity | None: ...
    async def create(self, identity: Identity) -> Identity: ...
    async def update(self, identity_id: str, **changes) -> Identity: ...
    async def delete(self, identity_id: str) -> None: ...

class CredentialStore(Protocol):
    async def get_password(self, identity_id: str) -> PasswordCredential | None: ...
    async def set_password(self, identity_id: str, password_hash: str) -> PasswordCredential: ...
    async def get_api_key(self, key_hash: str) -> ApiKeyCredential | None: ...
    async def create_api_key(self, identity_id: str, name: str) -> ApiKeyCredential: ...
    async def revoke_api_key(self, key_id: str) -> None: ...
```

---

## Full Example

```python
from aquilia.auth import (
    AuthManager, Identity, IdentityType, IdentityStatus,
    PasswordHasher, TokenManager, AccessLevel, Clearance,
)
from aquilia.auth.clearance import grant, is_verified, is_owner_or_admin

# Setup
hasher = PasswordHasher(algorithm="argon2id", time_cost=3, memory_cost=131072)
token_mgr = TokenManager(
    secret_key=os.environ["SECRET_KEY"],
    algorithm="HS512",
    access_token_ttl=timedelta(minutes=30),
)
auth_mgr = AuthManager(
    token_manager=token_mgr,
    password_hasher=hasher,
)

# Sign up
identity = await auth_mgr.create_identity(
    type=IdentityType.USER,
    attributes={"email": "alice@example.com", "name": "Alice", "roles": ["user"]},
    password="sup3rs3cret!",
)

# Sign in
result = await auth_mgr.authenticate_password("alice@example.com", "sup3rs3cret!")
print(result.access_token)
print(result.refresh_token)
print(result.identity.to_dict())

# Token validation
claims = await auth_mgr.validate_token(result.access_token)
if claims:
    print(claims.identity_id, claims.scopes)

# Refresh
new_result = await auth_mgr.refresh_token(result.refresh_token)

# Controller with Clearance
class DocumentsController(Controller):
    prefix = "/documents"
    clearance = Clearance(
        level=AccessLevel.AUTHENTICATED,
        entitlements=["documents:read"],
    )

    @GET("/")
    @grant(level=AccessLevel.PUBLIC)
    async def list_public(self, ctx):
        ...

    @POST("/")
    @grant(
        entitlements=["documents:write"],
        conditions=[is_verified, within_quota],
    )
    async def create(self, ctx):
        ...

    @DELETE("/{doc_id}")
    @grant(
        level=AccessLevel.CONFIDENTIAL,
        conditions=[is_owner_or_admin],
    )
    async def delete(self, ctx, doc_id: str):
        ...
```