# Sessions API Reference

This page is extracted from the current Python source. It includes public classes, methods, functions, constants, dataclass-like fields, decorators, and notable attributes.

## Public Class Summary

| Name | Source | Bases | Purpose |
| --- | --- | --- | --- |
| `SessionID` | `aquilia/sessions/core.py` | object | Opaque session identifier with cryptographic randomness. |
| `SessionScope` | `aquilia/sessions/core.py` | str, Enum | Public class. |
| `SessionFlag` | `aquilia/sessions/core.py` | str, Enum | Public class. |
| `SessionPrincipal` | `aquilia/sessions/core.py` | object | Represents who the session belongs to. |
| `Session` | `aquilia/sessions/core.py` | object | Core session object - explicit state container with lifecycle. |
| `SessionRequiredFault` | `aquilia/sessions/decorators.py` | Fault | Raised when session is required but missing. |
| `SessionDecorators` | `aquilia/sessions/decorators.py` | object | Namespace for session decorators. |
| `SessionContextManager` | `aquilia/sessions/decorators.py` | object | Context manager for scoped session access. |
| `SessionGuard` | `aquilia/sessions/decorators.py` | object | Advanced session guards for complex authorization logic. |
| `SessionEngine` | `aquilia/sessions/engine.py` | object | Session lifecycle orchestrator. |
| `SessionFault` | `aquilia/sessions/faults.py` | Fault | Base class for session-related faults. |
| `SessionExpiredFault` | `aquilia/sessions/faults.py` | SessionFault | Session has expired (TTL exceeded). |
| `SessionIdleTimeoutFault` | `aquilia/sessions/faults.py` | SessionFault | Session idle timeout exceeded. |
| `SessionAbsoluteTimeoutFault` | `aquilia/sessions/faults.py` | SessionFault | Session absolute timeout exceeded (OWASP requirement). |
| `SessionInvalidFault` | `aquilia/sessions/faults.py` | SessionFault | Session ID is invalid or malformed. |
| `SessionNotFoundFault` | `aquilia/sessions/faults.py` | SessionFault | Session ID not found in store. |
| `SessionPolicyViolationFault` | `aquilia/sessions/faults.py` | SessionFault | Session violates policy constraints. |
| `SessionConcurrencyViolationFault` | `aquilia/sessions/faults.py` | SessionFault | Too many concurrent sessions for principal. |
| `SessionLockedFault` | `aquilia/sessions/faults.py` | SessionFault | Session is locked by another operation. Retry after lock is released. |
| `SessionStoreUnavailableFault` | `aquilia/sessions/faults.py` | SessionFault | Session store is unavailable. Transient error - retry may succeed. |
| `SessionStoreCorruptedFault` | `aquilia/sessions/faults.py` | SessionFault | Session data in store is corrupted. |
| `SessionRotationFailedFault` | `aquilia/sessions/faults.py` | SessionFault | Session ID rotation failed. Session may be in inconsistent state. |
| `SessionTransportFault` | `aquilia/sessions/faults.py` | SessionFault | Error extracting or injecting session via transport. |
| `SessionForgeryAttemptFault` | `aquilia/sessions/faults.py` | SessionFault | Suspected session forgery or tampering. Security event. |
| `SessionHijackAttemptFault` | `aquilia/sessions/faults.py` | SessionFault | Suspected session hijacking (IP/User-Agent mismatch). |
| `SessionFingerprintMismatchFault` | `aquilia/sessions/faults.py` | SessionFault | Session fingerprint does not match client (OWASP hijack detection). |
| `PersistencePolicy` | `aquilia/sessions/policy.py` | object | Controls how sessions persist to storage. |
| `ConcurrencyPolicy` | `aquilia/sessions/policy.py` | object | Controls concurrent session limits per principal. |
| `TransportPolicy` | `aquilia/sessions/policy.py` | object | Controls how sessions travel across network. |
| `SessionPolicy` | `aquilia/sessions/policy.py` | object | Master policy that defines how sessions behave. |
| `SessionPolicyBuilder` | `aquilia/sessions/policy.py` | object | Fluent builder for SessionPolicy with unique Aquilia syntax. |
| `Field` | `aquilia/sessions/state.py` | object | Field descriptor for SessionState. |
| `SessionState` | `aquilia/sessions/state.py` | object | Base class for typed session state. |
| `CartState` | `aquilia/sessions/state.py` | SessionState | Shopping cart session state. |
| `UserPreferencesState` | `aquilia/sessions/state.py` | SessionState | User preferences session state. |
| `SessionStore` | `aquilia/sessions/store.py` | Protocol | Abstract session storage interface. |
| `MemoryStore` | `aquilia/sessions/store.py` | object | In-memory session storage for development and testing. |
| `FileStore` | `aquilia/sessions/store.py` | object | File-based session storage for debugging and development. |
| `SessionTransport` | `aquilia/sessions/transport.py` | Protocol | Abstract transport interface for session ID delivery. |
| `CookieTransport` | `aquilia/sessions/transport.py` | object | Cookie-based session transport. |
| `HeaderTransport` | `aquilia/sessions/transport.py` | object | Header-based session transport for APIs and mobile apps. |

## Public Function Summary

| Name | Source | Signature | Purpose |
| --- | --- | --- | --- |
| `stateful` | `aquilia/sessions/decorators.py` | `def stateful(func: F) -> F` | Shorthand decorator for stateful sessions. |
| `requires` | `aquilia/sessions/decorators.py` | `def requires(*guards: SessionGuard)` | Decorator to require multiple session guards. |
| `create_transport` | `aquilia/sessions/transport.py` | `def create_transport(policy: TransportPolicy) -> CookieTransport &#124; HeaderTransport` | Create transport adapter from policy. |

## Constants

| Name | Source | Value or type |
| --- | --- | --- |
| `F` | `aquilia/sessions/decorators.py` | `TypeVar('F', bound=Callable[..., Any])` |
| `DEFAULT_USER_POLICY` | `aquilia/sessions/policy.py` | `SessionPolicy(name='user_default', ttl=timedelta(days=7), idle_timeout=timedelta(minutes=30), rotate_on_use=False, rotate_on_privilege_change=True, persistence=` |
| `API_TOKEN_POLICY` | `aquilia/sessions/policy.py` | `SessionPolicy(name='api_token', ttl=timedelta(hours=1), idle_timeout=None, rotate_on_use=False, rotate_on_privilege_change=False, persistence=PersistencePolicy(` |
| `EPHEMERAL_POLICY` | `aquilia/sessions/policy.py` | `SessionPolicy(name='ephemeral', ttl=None, idle_timeout=None, rotate_on_use=False, rotate_on_privilege_change=False, persistence=PersistencePolicy(enabled=False)` |
| `ADMIN_POLICY` | `aquilia/sessions/policy.py` | `SessionPolicy(name='admin', ttl=timedelta(hours=8), idle_timeout=timedelta(minutes=15), absolute_timeout=timedelta(hours=12), rotate_on_use=True, rotate_on_priv` |
| `T` | `aquilia/sessions/state.py` | `TypeVar('T', bound='SessionState')` |

## Detailed Classes And Methods

### Class: `SessionID`

- Source: `aquilia/sessions/core.py`
- Bases: `object`
- Summary: Opaque session identifier with cryptographic randomness.

Attributes and fields:

| Name | Type | Default |
| --- | --- | --- |
| `ENTROPY_BYTES` |  | `32` |
| `PREFIX` |  | `'sess_'` |

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `from_string` | `def from_string(cls, encoded: str) -> SessionID` | classmethod | Method. |
| `raw` | `def raw(self) -> bytes` | property | Method. |
| `fingerprint` | `def fingerprint(self) -> str` |  | Privacy-safe fingerprint for logging. |

### Class: `SessionScope`

- Source: `aquilia/sessions/core.py`
- Bases: `str, Enum`

Attributes and fields:

| Name | Type | Default |
| --- | --- | --- |
| `REQUEST` |  | `'request'` |
| `CONNECTION` |  | `'connection'` |
| `USER` |  | `'user'` |
| `DEVICE` |  | `'device'` |

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `requires_persistence` | `def requires_persistence(self) -> bool` |  | Method. |
| `is_ephemeral` | `def is_ephemeral(self) -> bool` |  | Method. |

### Class: `SessionFlag`

- Source: `aquilia/sessions/core.py`
- Bases: `str, Enum`

Attributes and fields:

| Name | Type | Default |
| --- | --- | --- |
| `AUTHENTICATED` |  | `'authenticated'` |
| `EPHEMERAL` |  | `'ephemeral'` |
| `ROTATABLE` |  | `'rotatable'` |
| `RENEWABLE` |  | `'renewable'` |
| `READ_ONLY` |  | `'read_only'` |
| `LOCKED` |  | `'locked'` |

### Class: `SessionPrincipal`

- Source: `aquilia/sessions/core.py`
- Bases: `object`
- Decorators: `dataclass`
- Summary: Represents who the session belongs to.

Attributes and fields:

| Name | Type | Default |
| --- | --- | --- |
| `kind` | `Literal['user', 'service', 'device', 'anonymous']` |  |
| `id` | `str` |  |
| `attributes` | `dict[str, Any]` | `field(default_factory=dict)` |

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `is_user` | `def is_user(self) -> bool` |  | Method. |
| `is_service` | `def is_service(self) -> bool` |  | Method. |
| `is_device` | `def is_device(self) -> bool` |  | Method. |
| `is_anonymous` | `def is_anonymous(self) -> bool` |  | Method. |
| `has_attribute` | `def has_attribute(self, key: str) -> bool` |  | Method. |
| `get_attribute` | `def get_attribute(self, key: str, default: Any = None) -> Any` |  | Method. |
| `set_attribute` | `def set_attribute(self, key: str, value: Any) -> None` |  | Method. |
| `remove_attribute` | `def remove_attribute(self, key: str) -> None` |  | Method. |

### Class: `Session`

- Source: `aquilia/sessions/core.py`
- Bases: `object`
- Decorators: `dataclass`
- Summary: Core session object - explicit state container with lifecycle.

Attributes and fields:

| Name | Type | Default |
| --- | --- | --- |
| `id` | `SessionID` |  |
| `principal` | `SessionPrincipal &#124; None` | `None` |
| `data` | `dict[str, Any]` | `field(default_factory=dict)` |
| `created_at` | `datetime` | `field(default_factory=lambda: datetime.now(timezone.utc))` |
| `last_accessed_at` | `datetime` | `field(default_factory=lambda: datetime.now(timezone.utc))` |
| `expires_at` | `datetime &#124; None` | `None` |
| `scope` | `SessionScope` | `SessionScope.USER` |
| `flags` | `set[SessionFlag]` | `field(default_factory=set)` |
| `version` | `int` | `0` |
| `MAX_DATA_KEYS` |  | `256` |

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `get` | `def get(self, key: str, default: Any = None) -> Any` |  | Method. |
| `set` | `def set(self, key: str, value: Any) -> None` |  | Method. |
| `delete` | `def delete(self, key: str) -> None` |  | Method. |
| `clear_data` | `def clear_data(self) -> None` |  | Method. |
| `is_expired` | `def is_expired(self, now: datetime &#124; None = None) -> bool` |  | Method. |
| `idle_duration` | `def idle_duration(self, now: datetime &#124; None = None) -> timedelta` |  | Method. |
| `age` | `def age(self, now: datetime &#124; None = None) -> timedelta` |  | Total session age since creation. |
| `touch` | `def touch(self, now: datetime &#124; None = None) -> None` |  | Method. |
| `extend_expiry` | `def extend_expiry(self, ttl: timedelta, now: datetime &#124; None = None) -> None` |  | Method. |
| `mark_authenticated` | `def mark_authenticated(self, principal: SessionPrincipal) -> None` |  | Method. |
| `clear_authentication` | `def clear_authentication(self) -> None` |  | Method. |
| `is_authenticated` | `def is_authenticated(self) -> bool` | property | Method. |
| `is_anonymous` | `def is_anonymous(self) -> bool` | property | Method. |
| `is_dirty` | `def is_dirty(self) -> bool` | property | Method. |
| `mark_clean` | `def mark_clean(self) -> None` |  | Method. |
| `mark_dirty` | `def mark_dirty(self) -> None` |  | Method. |
| `is_ephemeral` | `def is_ephemeral(self) -> bool` | property | Method. |
| `is_read_only` | `def is_read_only(self) -> bool` | property | Method. |
| `is_locked` | `def is_locked(self) -> bool` | property | Method. |
| `bind_fingerprint` | `def bind_fingerprint(self, ip: str &#124; None = None, user_agent: str &#124; None = None) -> None` |  | Bind session to client properties for hijack detection. |
| `verify_fingerprint` | `def verify_fingerprint(self, ip: str &#124; None = None, user_agent: str &#124; None = None) -> bool` |  | Verify client fingerprint matches. Returns True if unset. |
| `to_dict` | `def to_dict(self) -> dict[str, Any]` |  | Method. |
| `from_dict` | `def from_dict(cls, data: dict[str, Any]) -> Session` | classmethod | Method. |

### Class: `SessionRequiredFault`

- Source: `aquilia/sessions/decorators.py`
- Bases: `Fault`
- Summary: Raised when session is required but missing.

### Class: `SessionDecorators`

- Source: `aquilia/sessions/decorators.py`
- Bases: `object`
- Summary: Namespace for session decorators.

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `require` | `def require(authenticated: bool = False, **kwargs) -> Callable[[F], F]` | staticmethod | Require session with specific properties. |
| `ensure` | `def ensure() -> Callable[[F], F]` | staticmethod | Ensure session exists (create if missing). |
| `optional` | `def optional() -> Callable[[F], F]` &#124; staticmethod | Session is optional. The handler will receive Session | None. |

### Class: `SessionContextManager`

- Source: `aquilia/sessions/decorators.py`
- Bases: `object`
- Summary: Context manager for scoped session access.

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `authenticated` | `async def authenticated(ctx)` | staticmethod, asynccontextmanager | Context manager for authenticated sessions. |
| `ensure` | `async def ensure(ctx)` | staticmethod, asynccontextmanager | Context manager that ensures session exists. |
| `transactional` | `async def transactional(ctx)` | staticmethod, asynccontextmanager | Transactional session context with rollback on exception. |

### Class: `SessionGuard`

- Source: `aquilia/sessions/decorators.py`
- Bases: `object`
- Summary: Advanced session guards for complex authorization logic.

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `check` | `async def check(self, session: Session) -> bool` |  | Method. |

### Class: `SessionEngine`

- Source: `aquilia/sessions/engine.py`
- Bases: `object`
- Summary: Session lifecycle orchestrator.

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `resolve` | `async def resolve(self, request: Request, container: Container &#124; None = None) -> Session` |  | Resolve session for request (Phase 1-4). |
| `commit` | `async def commit(self, session: Session, response: Response, privilege_changed: bool = False) -> None` |  | Commit session changes (Phase 6-7: Commit, Emission). |
| `destroy` | `async def destroy(self, session: Session, response: Response) -> None` |  | Destroy session (logout). |
| `check_concurrency` | `async def check_concurrency(self, session: Session) -> None` |  | Check concurrency limits for session's principal. |
| `refresh` | `async def refresh(self, session: Session, now: datetime &#124; None = None) -> None` |  | Refresh session expiry (extend TTL). |
| `on_event` | `def on_event(self, handler: callable) -> None` |  | Register event handler for observability. |
| `cleanup_expired` | `async def cleanup_expired(self) -> int` |  | Remove expired sessions from store. |
| `shutdown` | `async def shutdown(self) -> None` |  | Gracefully shutdown engine. |

### Class: `SessionFault`

- Source: `aquilia/sessions/faults.py`
- Bases: `Fault`
- Summary: Base class for session-related faults.

Attributes and fields:

| Name | Type | Default |
| --- | --- | --- |
| `domain` |  | `FaultDomain.SECURITY` |

### Class: `SessionExpiredFault`

- Source: `aquilia/sessions/faults.py`
- Bases: `SessionFault`
- Summary: Session has expired (TTL exceeded).

Attributes and fields:

| Name | Type | Default |
| --- | --- | --- |
| `code` |  | `'SESSION_EXPIRED'` |
| `message` |  | `'Session has expired'` |
| `severity` |  | `Severity.WARN` |
| `public` |  | `True` |
| `retryable` |  | `False` |

### Class: `SessionIdleTimeoutFault`

- Source: `aquilia/sessions/faults.py`
- Bases: `SessionFault`
- Summary: Session idle timeout exceeded.

Attributes and fields:

| Name | Type | Default |
| --- | --- | --- |
| `code` |  | `'SESSION_IDLE_TIMEOUT'` |
| `message` |  | `'Session idle timeout exceeded'` |
| `severity` |  | `Severity.WARN` |
| `public` |  | `True` |
| `retryable` |  | `False` |

### Class: `SessionAbsoluteTimeoutFault`

- Source: `aquilia/sessions/faults.py`
- Bases: `SessionFault`
- Summary: Session absolute timeout exceeded (OWASP requirement).

Attributes and fields:

| Name | Type | Default |
| --- | --- | --- |
| `code` |  | `'SESSION_ABSOLUTE_TIMEOUT'` |
| `message` |  | `'Session absolute timeout exceeded'` |
| `severity` |  | `Severity.WARN` |
| `public` |  | `True` |
| `retryable` |  | `False` |

### Class: `SessionInvalidFault`

- Source: `aquilia/sessions/faults.py`
- Bases: `SessionFault`
- Summary: Session ID is invalid or malformed.

Attributes and fields:

| Name | Type | Default |
| --- | --- | --- |
| `code` |  | `'SESSION_INVALID'` |
| `message` |  | `'Invalid session identifier'` |
| `severity` |  | `Severity.ERROR` |
| `public` |  | `True` |
| `retryable` |  | `False` |

### Class: `SessionNotFoundFault`

- Source: `aquilia/sessions/faults.py`
- Bases: `SessionFault`
- Summary: Session ID not found in store.

Attributes and fields:

| Name | Type | Default |
| --- | --- | --- |
| `code` |  | `'SESSION_NOT_FOUND'` |
| `message` |  | `'Session not found'` |
| `severity` |  | `Severity.WARN` |
| `public` |  | `True` |
| `retryable` |  | `False` |

### Class: `SessionPolicyViolationFault`

- Source: `aquilia/sessions/faults.py`
- Bases: `SessionFault`
- Summary: Session violates policy constraints.

Attributes and fields:

| Name | Type | Default |
| --- | --- | --- |
| `code` |  | `'SESSION_POLICY_VIOLATION'` |
| `message` |  | `'Session violates policy constraints'` |
| `severity` |  | `Severity.ERROR` |
| `public` |  | `False` |
| `retryable` |  | `False` |

### Class: `SessionConcurrencyViolationFault`

- Source: `aquilia/sessions/faults.py`
- Bases: `SessionFault`
- Summary: Too many concurrent sessions for principal.

Attributes and fields:

| Name | Type | Default |
| --- | --- | --- |
| `code` |  | `'SESSION_CONCURRENCY_VIOLATION'` |
| `message` |  | `'Too many concurrent sessions'` |
| `severity` |  | `Severity.ERROR` |
| `public` |  | `True` |
| `retryable` |  | `False` |

### Class: `SessionLockedFault`

- Source: `aquilia/sessions/faults.py`
- Bases: `SessionFault`
- Summary: Session is locked by another operation. Retry after lock is released.

Attributes and fields:

| Name | Type | Default |
| --- | --- | --- |
| `code` |  | `'SESSION_LOCKED'` |
| `message` |  | `'Session is locked'` |
| `severity` |  | `Severity.WARN` |
| `public` |  | `False` |
| `retryable` |  | `True` |

### Class: `SessionStoreUnavailableFault`

- Source: `aquilia/sessions/faults.py`
- Bases: `SessionFault`
- Summary: Session store is unavailable. Transient error - retry may succeed.

Attributes and fields:

| Name | Type | Default |
| --- | --- | --- |
| `code` |  | `'SESSION_STORE_UNAVAILABLE'` |
| `message` |  | `'Session storage unavailable'` |
| `severity` |  | `Severity.ERROR` |
| `public` |  | `False` |
| `retryable` |  | `True` |

### Class: `SessionStoreCorruptedFault`

- Source: `aquilia/sessions/faults.py`
- Bases: `SessionFault`
- Summary: Session data in store is corrupted.

Attributes and fields:

| Name | Type | Default |
| --- | --- | --- |
| `code` |  | `'SESSION_STORE_CORRUPTED'` |
| `message` |  | `'Session data corrupted'` |
| `severity` |  | `Severity.ERROR` |
| `public` |  | `False` |
| `retryable` |  | `False` |

### Class: `SessionRotationFailedFault`

- Source: `aquilia/sessions/faults.py`
- Bases: `SessionFault`
- Summary: Session ID rotation failed. Session may be in inconsistent state.

Attributes and fields:

| Name | Type | Default |
| --- | --- | --- |
| `code` |  | `'SESSION_ROTATION_FAILED'` |
| `message` |  | `'Session rotation failed'` |
| `severity` |  | `Severity.ERROR` |
| `public` |  | `False` |
| `retryable` |  | `True` |

### Class: `SessionTransportFault`

- Source: `aquilia/sessions/faults.py`
- Bases: `SessionFault`
- Summary: Error extracting or injecting session via transport.

Attributes and fields:

| Name | Type | Default |
| --- | --- | --- |
| `code` |  | `'SESSION_TRANSPORT_ERROR'` |
| `message` |  | `'Session transport error'` |
| `severity` |  | `Severity.WARN` |
| `public` |  | `False` |
| `retryable` |  | `False` |

### Class: `SessionForgeryAttemptFault`

- Source: `aquilia/sessions/faults.py`
- Bases: `SessionFault`
- Summary: Suspected session forgery or tampering. Security event.

Attributes and fields:

| Name | Type | Default |
| --- | --- | --- |
| `code` |  | `'SESSION_FORGERY_ATTEMPT'` |
| `message` |  | `'Suspected session forgery'` |
| `severity` |  | `Severity.ERROR` |
| `public` |  | `False` |
| `retryable` |  | `False` |

### Class: `SessionHijackAttemptFault`

- Source: `aquilia/sessions/faults.py`
- Bases: `SessionFault`
- Summary: Suspected session hijacking (IP/User-Agent mismatch).

Attributes and fields:

| Name | Type | Default |
| --- | --- | --- |
| `code` |  | `'SESSION_HIJACK_ATTEMPT'` |
| `message` |  | `'Suspected session hijacking'` |
| `severity` |  | `Severity.ERROR` |
| `public` |  | `False` |
| `retryable` |  | `False` |

### Class: `SessionFingerprintMismatchFault`

- Source: `aquilia/sessions/faults.py`
- Bases: `SessionFault`
- Summary: Session fingerprint does not match client (OWASP hijack detection).

Attributes and fields:

| Name | Type | Default |
| --- | --- | --- |
| `code` |  | `'SESSION_FINGERPRINT_MISMATCH'` |
| `message` |  | `'Session fingerprint mismatch - possible hijack'` |
| `severity` |  | `Severity.ERROR` |
| `public` |  | `False` |
| `retryable` |  | `False` |

### Class: `PersistencePolicy`

- Source: `aquilia/sessions/policy.py`
- Bases: `object`
- Decorators: `dataclass`
- Summary: Controls how sessions persist to storage.

Attributes and fields:

| Name | Type | Default |
| --- | --- | --- |
| `enabled` | `bool` | `True` |
| `store_name` | `str` | `'default'` |
| `write_through` | `bool` | `True` |
| `compress` | `bool` | `False` |

### Class: `ConcurrencyPolicy`

- Source: `aquilia/sessions/policy.py`
- Bases: `object`
- Decorators: `dataclass`
- Summary: Controls concurrent session limits per principal.

Attributes and fields:

| Name | Type | Default |
| --- | --- | --- |
| `max_sessions_per_principal` | `int &#124; None` | `None` |
| `behavior_on_limit` | `Literal['reject', 'evict_oldest', 'evict_all']` | `'evict_oldest'` |

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `violated` | `def violated(self, principal: SessionPrincipal, active_count: int) -> bool` |  | Method. |
| `should_reject` | `def should_reject(self) -> bool` |  | Method. |
| `should_evict_oldest` | `def should_evict_oldest(self) -> bool` |  | Method. |
| `should_evict_all` | `def should_evict_all(self) -> bool` |  | Method. |

### Class: `TransportPolicy`

- Source: `aquilia/sessions/policy.py`
- Bases: `object`
- Decorators: `dataclass`
- Summary: Controls how sessions travel across network.

Attributes and fields:

| Name | Type | Default |
| --- | --- | --- |
| `adapter` | `Literal['cookie', 'header', 'token']` | `'cookie'` |
| `cookie_name` | `str` | `'aquilia_session'` |
| `cookie_httponly` | `bool` | `True` |
| `cookie_secure` | `bool` | `True` |
| `cookie_samesite` | `Literal['strict', 'lax', 'none']` | `'lax'` |
| `cookie_path` | `str` | `'/'` |
| `cookie_domain` | `str &#124; None` | `None` |
| `header_name` | `str` | `'X-Session-ID'` |

### Class: `SessionPolicy`

- Source: `aquilia/sessions/policy.py`
- Bases: `object`
- Decorators: `dataclass`
- Summary: Master policy that defines how sessions behave.

Attributes and fields:

| Name | Type | Default |
| --- | --- | --- |
| `name` | `str` |  |
| `ttl` | `timedelta &#124; None` | `None` |
| `idle_timeout` | `timedelta &#124; None` | `None` |
| `absolute_timeout` | `timedelta &#124; None` | `None` |
| `rotate_on_use` | `bool` | `False` |
| `rotate_on_privilege_change` | `bool` | `True` |
| `fingerprint_binding` | `bool` | `False` |
| `persistence` | `PersistencePolicy` | `dc_field(default=None)` |
| `concurrency` | `ConcurrencyPolicy` | `dc_field(default=None)` |
| `transport` | `TransportPolicy` | `dc_field(default=None)` |
| `scope` | `str` | `'user'` |

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `should_rotate` | `def should_rotate(self, session: Session, privilege_changed: bool = False) -> bool` |  | Method. |
| `calculate_expiry` | `def calculate_expiry(self, now: datetime &#124; None = None) -> datetime &#124; None` |  | Method. |
| `is_valid` | `def is_valid(self, session: Session, now: datetime &#124; None = None) -> tuple[bool, str]` |  | Validate session against policy. |
| `should_persist` | `def should_persist(self, session: Session) -> bool` |  | Method. |
| `requires_store` | `def requires_store(self) -> bool` |  | Method. |
| `from_dict` | `def from_dict(cls, name: str, config: dict) -> SessionPolicy` | classmethod | Create policy from configuration dictionary. |
| `for_web_users` | `def for_web_users(cls) -> SessionPolicyBuilder` | classmethod | Method. |
| `for_api_tokens` | `def for_api_tokens(cls) -> SessionPolicyBuilder` | classmethod | Method. |
| `for_mobile_users` | `def for_mobile_users(cls) -> SessionPolicyBuilder` | classmethod | Method. |
| `for_admin_users` | `def for_admin_users(cls) -> SessionPolicyBuilder` | classmethod | Method. |

### Class: `SessionPolicyBuilder`

- Source: `aquilia/sessions/policy.py`
- Bases: `object`
- Summary: Fluent builder for SessionPolicy with unique Aquilia syntax.

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `named` | `def named(self, name: str) -> SessionPolicyBuilder` |  | Method. |
| `lasting` | `def lasting(self, days: int = None, hours: int = None, minutes: int = None) -> SessionPolicyBuilder` |  | Method. |
| `idle_timeout` | `def idle_timeout(self, hours: int = None, minutes: int = None, days: int = None) -> SessionPolicyBuilder` |  | Method. |
| `no_idle_timeout` | `def no_idle_timeout(self) -> SessionPolicyBuilder` |  | Method. |
| `absolute_timeout` | `def absolute_timeout(self, hours: int = None, minutes: int = None, days: int = None) -> SessionPolicyBuilder` |  | Set absolute timeout (OWASP: max total session lifetime). |
| `with_fingerprint_binding` | `def with_fingerprint_binding(self) -> SessionPolicyBuilder` |  | Enable OWASP session-to-client fingerprint binding. |
| `rotating_on_auth` | `def rotating_on_auth(self) -> SessionPolicyBuilder` |  | Method. |
| `rotating_on_use` | `def rotating_on_use(self) -> SessionPolicyBuilder` |  | Method. |
| `scoped_to` | `def scoped_to(self, scope: str) -> SessionPolicyBuilder` |  | Method. |
| `max_concurrent` | `def max_concurrent(self, limit: int) -> SessionPolicyBuilder` |  | Method. |
| `unlimited_concurrent` | `def unlimited_concurrent(self) -> SessionPolicyBuilder` |  | Method. |
| `with_smart_defaults` | `def with_smart_defaults(self) -> SessionPolicyBuilder` |  | Method. |
| `web_defaults` | `def web_defaults(self) -> SessionPolicyBuilder` |  | Method. |
| `api_defaults` | `def api_defaults(self) -> SessionPolicyBuilder` |  | Method. |
| `mobile_defaults` | `def mobile_defaults(self) -> SessionPolicyBuilder` |  | Method. |
| `admin_defaults` | `def admin_defaults(self) -> SessionPolicyBuilder` |  | Enhanced security defaults for admin users with fingerprint binding. |
| `build` | `def build(self) -> SessionPolicy` |  | Method. |

### Class: `Field`

- Source: `aquilia/sessions/state.py`
- Bases: `object`
- Summary: Field descriptor for SessionState.

### Class: `SessionState`

- Source: `aquilia/sessions/state.py`
- Bases: `object`
- Summary: Base class for typed session state.

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `get` | `def get(self, key: str, default: Any = None) -> Any` |  | Get state value with default. |
| `to_dict` | `def to_dict(self) -> dict[str, Any]` |  | Convert state to dictionary. |

### Class: `CartState`

- Source: `aquilia/sessions/state.py`
- Bases: `SessionState`
- Summary: Shopping cart session state.

Attributes and fields:

| Name | Type | Default |
| --- | --- | --- |
| `items` | `list` | `Field(default_factory=list)` |
| `total` | `float` | `Field(default=0.0)` |
| `currency` | `str` | `Field(default='USD')` |

### Class: `UserPreferencesState`

- Source: `aquilia/sessions/state.py`
- Bases: `SessionState`
- Summary: User preferences session state.

Attributes and fields:

| Name | Type | Default |
| --- | --- | --- |
| `theme` | `str` | `Field(default='light')` |
| `language` | `str` | `Field(default='en')` |
| `notifications` | `bool` | `Field(default=True)` |
| `timezone` | `str` | `Field(default='UTC')` |

### Class: `SessionStore`

- Source: `aquilia/sessions/store.py`
- Bases: `Protocol`
- Summary: Abstract session storage interface.

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `load` | `async def load(self, session_id: SessionID) -> Session &#124; None` |  | Method. |
| `save` | `async def save(self, session: Session) -> None` |  | Method. |
| `delete` | `async def delete(self, session_id: SessionID) -> None` |  | Method. |
| `exists` | `async def exists(self, session_id: SessionID) -> bool` |  | Method. |
| `list_by_principal` | `async def list_by_principal(self, principal_id: str) -> list[Session]` |  | Method. |
| `count_by_principal` | `async def count_by_principal(self, principal_id: str) -> int` |  | Method. |
| `cleanup_expired` | `async def cleanup_expired(self) -> int` |  | Method. |
| `shutdown` | `async def shutdown(self) -> None` |  | Method. |

### Class: `MemoryStore`

- Source: `aquilia/sessions/store.py`
- Bases: `object`
- Summary: In-memory session storage for development and testing.

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `load` | `async def load(self, session_id: SessionID) -> Session &#124; None` |  | Method. |
| `save` | `async def save(self, session: Session) -> None` |  | Method. |
| `delete` | `async def delete(self, session_id: SessionID) -> None` |  | Method. |
| `exists` | `async def exists(self, session_id: SessionID) -> bool` |  | Method. |
| `list_by_principal` | `async def list_by_principal(self, principal_id: str) -> list[Session]` |  | Method. |
| `count_by_principal` | `async def count_by_principal(self, principal_id: str) -> int` |  | Method. |
| `cleanup_expired` | `async def cleanup_expired(self) -> int` |  | Method. |
| `shutdown` | `async def shutdown(self) -> None` |  | Method. |
| `get_stats` | `def get_stats(self) -> dict[str, Any]` |  | Method. |
| `web_optimized` | `def web_optimized(cls) -> MemoryStore` | classmethod | Method. |
| `api_optimized` | `def api_optimized(cls) -> MemoryStore` | classmethod | Method. |
| `development_focused` | `def development_focused(cls) -> MemoryStore` | classmethod | Method. |
| `high_throughput` | `def high_throughput(cls) -> MemoryStore` | classmethod | Method. |

### Class: `FileStore`

- Source: `aquilia/sessions/store.py`
- Bases: `object`
- Summary: File-based session storage for debugging and development.

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `load` | `async def load(self, session_id: SessionID) -> Session &#124; None` |  | Method. |
| `save` | `async def save(self, session: Session) -> None` |  | Method. |
| `delete` | `async def delete(self, session_id: SessionID) -> None` |  | Method. |
| `exists` | `async def exists(self, session_id: SessionID) -> bool` |  | Method. |
| `list_by_principal` | `async def list_by_principal(self, principal_id: str) -> list[Session]` |  | Method. |
| `count_by_principal` | `async def count_by_principal(self, principal_id: str) -> int` |  | Method. |
| `cleanup_expired` | `async def cleanup_expired(self) -> int` |  | Method. |
| `shutdown` | `async def shutdown(self) -> None` |  | Method. |
| `get_stats` | `def get_stats(self) -> dict[str, Any]` |  | Method. |

### Class: `SessionTransport`

- Source: `aquilia/sessions/transport.py`
- Bases: `Protocol`
- Summary: Abstract transport interface for session ID delivery.

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `extract` | `def extract(self, request: Request) -> str &#124; None` |  | Method. |
| `inject` | `def inject(self, response: Response, session: Session) -> None` |  | Method. |
| `clear` | `def clear(self, response: Response) -> None` |  | Method. |

### Class: `CookieTransport`

- Source: `aquilia/sessions/transport.py`
- Bases: `object`
- Summary: Cookie-based session transport.

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `extract` | `def extract(self, request: Request) -> str &#124; None` |  | Extract session ID from cookie. |
| `inject` | `def inject(self, response: Response, session: Session) -> None` |  | Inject session ID as cookie via response.set_cookie(). |
| `clear` | `def clear(self, response: Response) -> None` |  | Clear session cookie (logout). |
| `for_web_browsers` | `def for_web_browsers(cls) -> CookieTransport` | classmethod | Method. |
| `for_spa_applications` | `def for_spa_applications(cls) -> CookieTransport` | classmethod | Method. |
| `for_mobile_webviews` | `def for_mobile_webviews(cls) -> CookieTransport` | classmethod | Method. |
| `with_aquilia_defaults` | `def with_aquilia_defaults(cls) -> CookieTransport` | classmethod | Method. |

### Class: `HeaderTransport`

- Source: `aquilia/sessions/transport.py`
- Bases: `object`
- Summary: Header-based session transport for APIs and mobile apps.

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `extract` | `def extract(self, request: Request) -> str &#124; None` |  | Method. |
| `inject` | `def inject(self, response: Response, session: Session) -> None` |  | Method. |
| `clear` | `def clear(self, response: Response) -> None` |  | Method. |
| `for_rest_apis` | `def for_rest_apis(cls) -> HeaderTransport` | classmethod | Method. |
| `for_graphql_apis` | `def for_graphql_apis(cls) -> HeaderTransport` | classmethod | Method. |
| `for_mobile_apis` | `def for_mobile_apis(cls) -> HeaderTransport` | classmethod | Method. |
| `for_microservices` | `def for_microservices(cls) -> HeaderTransport` | classmethod | Method. |
| `with_aquilia_defaults` | `def with_aquilia_defaults(cls) -> HeaderTransport` | classmethod | Method. |

## Functions

| Name | Source | Signature | Purpose |
| --- | --- | --- | --- |
| `stateful` | `aquilia/sessions/decorators.py` | `def stateful(func: F) -> F` | Shorthand decorator for stateful sessions. |
| `requires` | `aquilia/sessions/decorators.py` | `def requires(*guards: SessionGuard)` | Decorator to require multiple session guards. |
| `create_transport` | `aquilia/sessions/transport.py` | `def create_transport(policy: TransportPolicy) -> CookieTransport &#124; HeaderTransport` | Create transport adapter from policy. |

## Constants

| Name | Source | Value or type |
| --- | --- | --- |
| `F` | `aquilia/sessions/decorators.py` | `TypeVar('F', bound=Callable[..., Any])` |
| `DEFAULT_USER_POLICY` | `aquilia/sessions/policy.py` | `SessionPolicy(name='user_default', ttl=timedelta(days=7), idle_timeout=timedelta(minutes=30), rotate_on_use=False, rotate_on_privilege_change=True, persistence=` |
| `API_TOKEN_POLICY` | `aquilia/sessions/policy.py` | `SessionPolicy(name='api_token', ttl=timedelta(hours=1), idle_timeout=None, rotate_on_use=False, rotate_on_privilege_change=False, persistence=PersistencePolicy(` |
| `EPHEMERAL_POLICY` | `aquilia/sessions/policy.py` | `SessionPolicy(name='ephemeral', ttl=None, idle_timeout=None, rotate_on_use=False, rotate_on_privilege_change=False, persistence=PersistencePolicy(enabled=False)` |
| `ADMIN_POLICY` | `aquilia/sessions/policy.py` | `SessionPolicy(name='admin', ttl=timedelta(hours=8), idle_timeout=timedelta(minutes=15), absolute_timeout=timedelta(hours=12), rotate_on_use=True, rotate_on_priv` |
| `T` | `aquilia/sessions/state.py` | `TypeVar('T', bound='SessionState')` |
