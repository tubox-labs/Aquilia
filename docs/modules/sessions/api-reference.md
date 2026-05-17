# Sessions API Reference

This page is generated from the current Python source using the AST. It lists public classes, public methods, public module-level functions, constants, exports, and source files.

## Source Inventory

| File | Lines | Classes | Functions | Purpose |
| --- | ---: | ---: | ---: | --- |
| `aquilia/sessions/__init__.py` | 144 | 0 | 0 | AquilaSessions - Production-grade session management for Aquilia. |
| `aquilia/sessions/core.py` | 602 | 5 | 0 | AquilaSessions - Core types. |
| `aquilia/sessions/decorators.py` | 442 | 4 | 2 | Unique Session Decorators for Aquilia. |
| `aquilia/sessions/engine.py` | 407 | 1 | 0 | AquilaSessions - Session Engine. |
| `aquilia/sessions/faults.py` | 320 | 16 | 0 | AquilaSessions - Fault definitions. |
| `aquilia/sessions/policy.py` | 456 | 5 | 0 | AquilaSessions - Policy types. |
| `aquilia/sessions/state.py` | 189 | 4 | 0 | Typed Session State for Aquilia. |
| `aquilia/sessions/store.py` | 309 | 3 | 0 | AquilaSessions - Session storage abstraction. |
| `aquilia/sessions/transport.py` | 290 | 3 | 1 | AquilaSessions - Transport adapters. |

## Public Exports

`ADMIN_POLICY`, `API_TOKEN_POLICY`, `CartState`, `ConcurrencyPolicy`, `CookieTransport`, `DEFAULT_USER_POLICY`, `EPHEMERAL_POLICY`, `Field`, `FileStore`, `HeaderTransport`, `MemoryStore`, `PersistencePolicy`, `Session`, `SessionAbsoluteTimeoutFault`, `SessionConcurrencyViolationFault`, `SessionContext`, `SessionEngine`, `SessionExpiredFault`, `SessionFault`, `SessionFingerprintMismatchFault`, `SessionFlag`, `SessionForgeryAttemptFault`, `SessionGuard`, `SessionHijackAttemptFault`, `SessionID`, `SessionIdleTimeoutFault`, `SessionInvalidFault`, `SessionLockedFault`, `SessionNotFoundFault`, `SessionPolicy`, `SessionPolicyBuilder`, `SessionPolicyViolationFault`, `SessionPrincipal`, `SessionRequiredFault`, `SessionRotationFailedFault`, `SessionScope`, `SessionState`, `SessionStore`, `SessionStoreCorruptedFault`, `SessionStoreUnavailableFault`, `SessionTransport`, `SessionTransportFault`, `TransportPolicy`, `UserPreferencesState`, `create_transport`, `requires`, `session`, `stateful`

## Public Class Summary

| Class | Source | Bases | Summary |
| --- | --- | --- | --- |
| `SessionID` | `aquilia/sessions/core.py` | object | Opaque session identifier with cryptographic randomness. |
| `SessionScope` | `aquilia/sessions/core.py` | str, Enum |  |
| `SessionFlag` | `aquilia/sessions/core.py` | str, Enum |  |
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
| `FileStore` | `aquilia/sessions/store.py` | object | File-based session storage for debugging and development. NOT suitable for production. |
| `SessionTransport` | `aquilia/sessions/transport.py` | Protocol | Abstract transport interface for session ID delivery. |
| `CookieTransport` | `aquilia/sessions/transport.py` | object | Cookie-based session transport. |
| `HeaderTransport` | `aquilia/sessions/transport.py` | object | Header-based session transport for APIs and mobile apps. |

## Public Function Summary

| Function | Source | Signature | Summary |
| --- | --- | --- | --- |
| `stateful` | `aquilia/sessions/decorators.py` | `def stateful(func: F)` | Shorthand decorator for stateful sessions. |
| `requires` | `aquilia/sessions/decorators.py` | `def requires(*guards: SessionGuard)` | Decorator to require multiple session guards. |
| `create_transport` | `aquilia/sessions/transport.py` | `def create_transport(policy: TransportPolicy)` | Create transport adapter from policy. |

## Constants And Module Flags

| Name | Source | Value or Type |
| --- | --- | --- |
| `F` | `aquilia/sessions/decorators.py` | `TypeVar('F', bound=Callable[..., Any])` |
| `DEFAULT_USER_POLICY` | `aquilia/sessions/policy.py` | `SessionPolicy(name='user_default', ttl=timedelta(days=7), idle_timeout=timedelta(minutes=30), rotate_on_use=False, rotate_on_privilege_change=True, persistence=PersistencePolicy(enabled=True, store_name='default'), concurrency=ConcurrencyPolicy(max_sessions_per_principal=5, behavior_on_limit='evict_oldest'), transport=TransportPolicy(adapter='cookie'), scope='user')` |
| `API_TOKEN_POLICY` | `aquilia/sessions/policy.py` | `SessionPolicy(name='api_token', ttl=timedelta(hours=1), idle_timeout=None, rotate_on_use=False, rotate_on_privilege_change=False, persistence=PersistencePolicy(enabled=True, store_name='default'), concurrency=ConcurrencyPolicy(max_sessions_per_principal=None), transport=TransportPolicy(adapter='header', header_name='X-API-Token'), scope='user')` |
| `EPHEMERAL_POLICY` | `aquilia/sessions/policy.py` | `SessionPolicy(name='ephemeral', ttl=None, idle_timeout=None, rotate_on_use=False, rotate_on_privilege_change=False, persistence=PersistencePolicy(enabled=False), concurrency=ConcurrencyPolicy(max_sessions_per_principal=None), transport=TransportPolicy(adapter='cookie'), scope='request')` |
| `ADMIN_POLICY` | `aquilia/sessions/policy.py` | `SessionPolicy(name='admin', ttl=timedelta(hours=8), idle_timeout=timedelta(minutes=15), absolute_timeout=timedelta(hours=12), rotate_on_use=True, rotate_on_privilege_change=True, fingerprint_binding=True, persistence=PersistencePolicy(enabled=True, store_name='default'), concurrency=ConcurrencyPolicy(max_sessions_per_principal=1, behavior_on_limit='evict_all'), transport=TransportPolicy(adapter='cookie', cookie_samesite='strict'), scope='user')` |
| `T` | `aquilia/sessions/state.py` | `TypeVar('T', bound='SessionState')` |

## Detailed Classes And Methods

### `SessionID`

- Source: `aquilia/sessions/core.py`
- Bases: `object`
- Summary: Opaque session identifier with cryptographic randomness.

Fields and class attributes:

| Name | Type | Default / Value |
| --- | --- | --- |
| `ENTROPY_BYTES` | `` | `32` |
| `PREFIX` | `` | `'sess_'` |

Methods:

| Method | Signature | Summary |
| --- | --- | --- |
| `from_string` | `def from_string(cls, encoded: str)` |  |
| `raw` | `def raw(self)` |  |
| `fingerprint` | `def fingerprint(self)` | Privacy-safe fingerprint for logging. |

### `SessionScope`

- Source: `aquilia/sessions/core.py`
- Bases: `str, Enum`

Fields and class attributes:

| Name | Type | Default / Value |
| --- | --- | --- |
| `REQUEST` | `` | `'request'` |
| `CONNECTION` | `` | `'connection'` |
| `USER` | `` | `'user'` |
| `DEVICE` | `` | `'device'` |

Methods:

| Method | Signature | Summary |
| --- | --- | --- |
| `requires_persistence` | `def requires_persistence(self)` |  |
| `is_ephemeral` | `def is_ephemeral(self)` |  |

### `SessionFlag`

- Source: `aquilia/sessions/core.py`
- Bases: `str, Enum`

Fields and class attributes:

| Name | Type | Default / Value |
| --- | --- | --- |
| `AUTHENTICATED` | `` | `'authenticated'` |
| `EPHEMERAL` | `` | `'ephemeral'` |
| `ROTATABLE` | `` | `'rotatable'` |
| `RENEWABLE` | `` | `'renewable'` |
| `READ_ONLY` | `` | `'read_only'` |
| `LOCKED` | `` | `'locked'` |

### `SessionPrincipal`

- Source: `aquilia/sessions/core.py`
- Bases: `object`
- Summary: Represents who the session belongs to.
- Decorators: `dataclass`

Fields and class attributes:

| Name | Type | Default / Value |
| --- | --- | --- |
| `kind` | `Literal['user', 'service', 'device', 'anonymous']` | `` |
| `id` | `str` | `` |
| `attributes` | `dict[str, Any]` | `field(default_factory=dict)` |

Methods:

| Method | Signature | Summary |
| --- | --- | --- |
| `is_user` | `def is_user(self)` |  |
| `is_service` | `def is_service(self)` |  |
| `is_device` | `def is_device(self)` |  |
| `is_anonymous` | `def is_anonymous(self)` |  |
| `has_attribute` | `def has_attribute(self, key: str)` |  |
| `get_attribute` | `def get_attribute(self, key: str, default: Any=None)` |  |
| `set_attribute` | `def set_attribute(self, key: str, value: Any)` |  |
| `remove_attribute` | `def remove_attribute(self, key: str)` |  |

### `Session`

- Source: `aquilia/sessions/core.py`
- Bases: `object`
- Summary: Core session object - explicit state container with lifecycle.
- Decorators: `dataclass`

Fields and class attributes:

| Name | Type | Default / Value |
| --- | --- | --- |
| `id` | `SessionID` | `` |
| `principal` | `SessionPrincipal \| None` | `None` |
| `data` | `dict[str, Any]` | `field(default_factory=dict)` |
| `created_at` | `datetime` | `field(default_factory=lambda: datetime.now(timezone.utc))` |
| `last_accessed_at` | `datetime` | `field(default_factory=lambda: datetime.now(timezone.utc))` |
| `expires_at` | `datetime \| None` | `None` |
| `scope` | `SessionScope` | `SessionScope.USER` |
| `flags` | `set[SessionFlag]` | `field(default_factory=set)` |
| `version` | `int` | `0` |
| `MAX_DATA_KEYS` | `` | `256` |

Methods:

| Method | Signature | Summary |
| --- | --- | --- |
| `get` | `def get(self, key: str, default: Any=None)` |  |
| `set` | `def set(self, key: str, value: Any)` |  |
| `delete` | `def delete(self, key: str)` |  |
| `clear_data` | `def clear_data(self)` |  |
| `is_expired` | `def is_expired(self, now: datetime \| None=None)` |  |
| `idle_duration` | `def idle_duration(self, now: datetime \| None=None)` |  |
| `age` | `def age(self, now: datetime \| None=None)` | Total session age since creation. |
| `touch` | `def touch(self, now: datetime \| None=None)` |  |
| `extend_expiry` | `def extend_expiry(self, ttl: timedelta, now: datetime \| None=None)` |  |
| `mark_authenticated` | `def mark_authenticated(self, principal: SessionPrincipal)` |  |
| `clear_authentication` | `def clear_authentication(self)` |  |
| `is_authenticated` | `def is_authenticated(self)` |  |
| `is_anonymous` | `def is_anonymous(self)` |  |
| `is_dirty` | `def is_dirty(self)` |  |
| `mark_clean` | `def mark_clean(self)` |  |
| `mark_dirty` | `def mark_dirty(self)` |  |
| `is_ephemeral` | `def is_ephemeral(self)` |  |
| `is_read_only` | `def is_read_only(self)` |  |
| `is_locked` | `def is_locked(self)` |  |
| `bind_fingerprint` | `def bind_fingerprint(self, ip: str \| None=None, user_agent: str \| None=None)` | Bind session to client properties for hijack detection. |
| `verify_fingerprint` | `def verify_fingerprint(self, ip: str \| None=None, user_agent: str \| None=None)` | Verify client fingerprint matches. Returns True if unset. |
| `to_dict` | `def to_dict(self)` |  |
| `from_dict` | `def from_dict(cls, data: dict[str, Any])` |  |

### `SessionRequiredFault`

- Source: `aquilia/sessions/decorators.py`
- Bases: `Fault`
- Summary: Raised when session is required but missing.

### `SessionDecorators`

- Source: `aquilia/sessions/decorators.py`
- Bases: `object`
- Summary: Namespace for session decorators.

Methods:

| Method | Signature | Summary |
| --- | --- | --- |
| `require` | `def require(authenticated: bool=False, **kwargs)` | Require session with specific properties. |
| `ensure` | `def ensure()` | Ensure session exists (create if missing). |
| `optional` | `def optional()` | Session is optional. The handler will receive Session \| None. |

### `SessionContextManager`

- Source: `aquilia/sessions/decorators.py`
- Bases: `object`
- Summary: Context manager for scoped session access.

Methods:

| Method | Signature | Summary |
| --- | --- | --- |
| `authenticated` | `async def authenticated(ctx)` | Context manager for authenticated sessions. |
| `ensure` | `async def ensure(ctx)` | Context manager that ensures session exists. |
| `transactional` | `async def transactional(ctx)` | Transactional session context with rollback on exception. |

### `SessionGuard`

- Source: `aquilia/sessions/decorators.py`
- Bases: `object`
- Summary: Advanced session guards for complex authorization logic.

Methods:

| Method | Signature | Summary |
| --- | --- | --- |
| `check` | `async def check(self, session: Session)` |  |

### `SessionEngine`

- Source: `aquilia/sessions/engine.py`
- Bases: `object`
- Summary: Session lifecycle orchestrator.

Methods:

| Method | Signature | Summary |
| --- | --- | --- |
| `resolve` | `async def resolve(self, request: Request, container: Container \| None=None)` | Resolve session for request (Phase 1-4). |
| `commit` | `async def commit(self, session: Session, response: Response, privilege_changed: bool=False)` | Commit session changes (Phase 6-7: Commit, Emission). |
| `destroy` | `async def destroy(self, session: Session, response: Response)` | Destroy session (logout). |
| `check_concurrency` | `async def check_concurrency(self, session: Session)` | Check concurrency limits for session's principal. |
| `refresh` | `async def refresh(self, session: Session, now: datetime \| None=None)` | Refresh session expiry (extend TTL). |
| `on_event` | `def on_event(self, handler: callable)` | Register event handler for observability. |
| `cleanup_expired` | `async def cleanup_expired(self)` | Remove expired sessions from store. |
| `shutdown` | `async def shutdown(self)` | Gracefully shutdown engine. |

### `SessionFault`

- Source: `aquilia/sessions/faults.py`
- Bases: `Fault`
- Summary: Base class for session-related faults.

### `SessionExpiredFault`

- Source: `aquilia/sessions/faults.py`
- Bases: `SessionFault`
- Summary: Session has expired (TTL exceeded).

Fields and class attributes:

| Name | Type | Default / Value |
| --- | --- | --- |
| `code` | `` | `'SESSION_EXPIRED'` |
| `message` | `` | `'Session has expired'` |
| `public` | `` | `True` |
| `retryable` | `` | `False` |

### `SessionIdleTimeoutFault`

- Source: `aquilia/sessions/faults.py`
- Bases: `SessionFault`
- Summary: Session idle timeout exceeded.

Fields and class attributes:

| Name | Type | Default / Value |
| --- | --- | --- |
| `code` | `` | `'SESSION_IDLE_TIMEOUT'` |
| `message` | `` | `'Session idle timeout exceeded'` |
| `public` | `` | `True` |
| `retryable` | `` | `False` |

### `SessionAbsoluteTimeoutFault`

- Source: `aquilia/sessions/faults.py`
- Bases: `SessionFault`
- Summary: Session absolute timeout exceeded (OWASP requirement).

Fields and class attributes:

| Name | Type | Default / Value |
| --- | --- | --- |
| `code` | `` | `'SESSION_ABSOLUTE_TIMEOUT'` |
| `message` | `` | `'Session absolute timeout exceeded'` |
| `public` | `` | `True` |
| `retryable` | `` | `False` |

### `SessionInvalidFault`

- Source: `aquilia/sessions/faults.py`
- Bases: `SessionFault`
- Summary: Session ID is invalid or malformed.

Fields and class attributes:

| Name | Type | Default / Value |
| --- | --- | --- |
| `code` | `` | `'SESSION_INVALID'` |
| `message` | `` | `'Invalid session identifier'` |
| `public` | `` | `True` |
| `retryable` | `` | `False` |

### `SessionNotFoundFault`

- Source: `aquilia/sessions/faults.py`
- Bases: `SessionFault`
- Summary: Session ID not found in store.

Fields and class attributes:

| Name | Type | Default / Value |
| --- | --- | --- |
| `code` | `` | `'SESSION_NOT_FOUND'` |
| `message` | `` | `'Session not found'` |
| `public` | `` | `True` |
| `retryable` | `` | `False` |

### `SessionPolicyViolationFault`

- Source: `aquilia/sessions/faults.py`
- Bases: `SessionFault`
- Summary: Session violates policy constraints.

Fields and class attributes:

| Name | Type | Default / Value |
| --- | --- | --- |
| `code` | `` | `'SESSION_POLICY_VIOLATION'` |
| `message` | `` | `'Session violates policy constraints'` |
| `public` | `` | `False` |
| `retryable` | `` | `False` |

### `SessionConcurrencyViolationFault`

- Source: `aquilia/sessions/faults.py`
- Bases: `SessionFault`
- Summary: Too many concurrent sessions for principal.

Fields and class attributes:

| Name | Type | Default / Value |
| --- | --- | --- |
| `code` | `` | `'SESSION_CONCURRENCY_VIOLATION'` |
| `message` | `` | `'Too many concurrent sessions'` |
| `public` | `` | `True` |
| `retryable` | `` | `False` |

### `SessionLockedFault`

- Source: `aquilia/sessions/faults.py`
- Bases: `SessionFault`
- Summary: Session is locked by another operation. Retry after lock is released.

Fields and class attributes:

| Name | Type | Default / Value |
| --- | --- | --- |
| `code` | `` | `'SESSION_LOCKED'` |
| `message` | `` | `'Session is locked'` |
| `public` | `` | `False` |
| `retryable` | `` | `True` |

### `SessionStoreUnavailableFault`

- Source: `aquilia/sessions/faults.py`
- Bases: `SessionFault`
- Summary: Session store is unavailable. Transient error - retry may succeed.

Fields and class attributes:

| Name | Type | Default / Value |
| --- | --- | --- |
| `code` | `` | `'SESSION_STORE_UNAVAILABLE'` |
| `message` | `` | `'Session storage unavailable'` |
| `public` | `` | `False` |
| `retryable` | `` | `True` |

### `SessionStoreCorruptedFault`

- Source: `aquilia/sessions/faults.py`
- Bases: `SessionFault`
- Summary: Session data in store is corrupted.

Fields and class attributes:

| Name | Type | Default / Value |
| --- | --- | --- |
| `code` | `` | `'SESSION_STORE_CORRUPTED'` |
| `message` | `` | `'Session data corrupted'` |
| `public` | `` | `False` |
| `retryable` | `` | `False` |

### `SessionRotationFailedFault`

- Source: `aquilia/sessions/faults.py`
- Bases: `SessionFault`
- Summary: Session ID rotation failed. Session may be in inconsistent state.

Fields and class attributes:

| Name | Type | Default / Value |
| --- | --- | --- |
| `code` | `` | `'SESSION_ROTATION_FAILED'` |
| `message` | `` | `'Session rotation failed'` |
| `public` | `` | `False` |
| `retryable` | `` | `True` |

### `SessionTransportFault`

- Source: `aquilia/sessions/faults.py`
- Bases: `SessionFault`
- Summary: Error extracting or injecting session via transport.

Fields and class attributes:

| Name | Type | Default / Value |
| --- | --- | --- |
| `code` | `` | `'SESSION_TRANSPORT_ERROR'` |
| `message` | `` | `'Session transport error'` |
| `public` | `` | `False` |
| `retryable` | `` | `False` |

### `SessionForgeryAttemptFault`

- Source: `aquilia/sessions/faults.py`
- Bases: `SessionFault`
- Summary: Suspected session forgery or tampering. Security event.

Fields and class attributes:

| Name | Type | Default / Value |
| --- | --- | --- |
| `code` | `` | `'SESSION_FORGERY_ATTEMPT'` |
| `message` | `` | `'Suspected session forgery'` |
| `public` | `` | `False` |
| `retryable` | `` | `False` |

### `SessionHijackAttemptFault`

- Source: `aquilia/sessions/faults.py`
- Bases: `SessionFault`
- Summary: Suspected session hijacking (IP/User-Agent mismatch).

Fields and class attributes:

| Name | Type | Default / Value |
| --- | --- | --- |
| `code` | `` | `'SESSION_HIJACK_ATTEMPT'` |
| `message` | `` | `'Suspected session hijacking'` |
| `public` | `` | `False` |
| `retryable` | `` | `False` |

### `SessionFingerprintMismatchFault`

- Source: `aquilia/sessions/faults.py`
- Bases: `SessionFault`
- Summary: Session fingerprint does not match client (OWASP hijack detection).

Fields and class attributes:

| Name | Type | Default / Value |
| --- | --- | --- |
| `code` | `` | `'SESSION_FINGERPRINT_MISMATCH'` |
| `message` | `` | `'Session fingerprint mismatch - possible hijack'` |
| `public` | `` | `False` |
| `retryable` | `` | `False` |

### `PersistencePolicy`

- Source: `aquilia/sessions/policy.py`
- Bases: `object`
- Summary: Controls how sessions persist to storage.
- Decorators: `dataclass`

Fields and class attributes:

| Name | Type | Default / Value |
| --- | --- | --- |
| `enabled` | `bool` | `True` |
| `store_name` | `str` | `'default'` |
| `write_through` | `bool` | `True` |
| `compress` | `bool` | `False` |

### `ConcurrencyPolicy`

- Source: `aquilia/sessions/policy.py`
- Bases: `object`
- Summary: Controls concurrent session limits per principal.
- Decorators: `dataclass`

Fields and class attributes:

| Name | Type | Default / Value |
| --- | --- | --- |
| `max_sessions_per_principal` | `int \| None` | `None` |
| `behavior_on_limit` | `Literal['reject', 'evict_oldest', 'evict_all']` | `'evict_oldest'` |

Methods:

| Method | Signature | Summary |
| --- | --- | --- |
| `violated` | `def violated(self, principal: SessionPrincipal, active_count: int)` |  |
| `should_reject` | `def should_reject(self)` |  |
| `should_evict_oldest` | `def should_evict_oldest(self)` |  |
| `should_evict_all` | `def should_evict_all(self)` |  |

### `TransportPolicy`

- Source: `aquilia/sessions/policy.py`
- Bases: `object`
- Summary: Controls how sessions travel across network.
- Decorators: `dataclass`

Fields and class attributes:

| Name | Type | Default / Value |
| --- | --- | --- |
| `adapter` | `Literal['cookie', 'header', 'token']` | `'cookie'` |
| `cookie_name` | `str` | `'aquilia_session'` |
| `cookie_httponly` | `bool` | `True` |
| `cookie_secure` | `bool` | `True` |
| `cookie_samesite` | `Literal['strict', 'lax', 'none']` | `'lax'` |
| `cookie_path` | `str` | `'/'` |
| `cookie_domain` | `str \| None` | `None` |
| `header_name` | `str` | `'X-Session-ID'` |

### `SessionPolicy`

- Source: `aquilia/sessions/policy.py`
- Bases: `object`
- Summary: Master policy that defines how sessions behave.
- Decorators: `dataclass`

Fields and class attributes:

| Name | Type | Default / Value |
| --- | --- | --- |
| `name` | `str` | `` |
| `ttl` | `timedelta \| None` | `None` |
| `idle_timeout` | `timedelta \| None` | `None` |
| `absolute_timeout` | `timedelta \| None` | `None` |
| `rotate_on_use` | `bool` | `False` |
| `rotate_on_privilege_change` | `bool` | `True` |
| `fingerprint_binding` | `bool` | `False` |
| `persistence` | `PersistencePolicy` | `dc_field(default=None)` |
| `concurrency` | `ConcurrencyPolicy` | `dc_field(default=None)` |
| `transport` | `TransportPolicy` | `dc_field(default=None)` |
| `scope` | `str` | `'user'` |

Methods:

| Method | Signature | Summary |
| --- | --- | --- |
| `should_rotate` | `def should_rotate(self, session: Session, privilege_changed: bool=False)` |  |
| `calculate_expiry` | `def calculate_expiry(self, now: datetime \| None=None)` |  |
| `is_valid` | `def is_valid(self, session: Session, now: datetime \| None=None)` | Validate session against policy. |
| `should_persist` | `def should_persist(self, session: Session)` |  |
| `requires_store` | `def requires_store(self)` |  |
| `from_dict` | `def from_dict(cls, name: str, config: dict)` | Create policy from configuration dictionary. |
| `for_web_users` | `def for_web_users(cls)` |  |
| `for_api_tokens` | `def for_api_tokens(cls)` |  |
| `for_mobile_users` | `def for_mobile_users(cls)` |  |
| `for_admin_users` | `def for_admin_users(cls)` |  |

### `SessionPolicyBuilder`

- Source: `aquilia/sessions/policy.py`
- Bases: `object`
- Summary: Fluent builder for SessionPolicy with unique Aquilia syntax.

Methods:

| Method | Signature | Summary |
| --- | --- | --- |
| `named` | `def named(self, name: str)` |  |
| `lasting` | `def lasting(self, days: int=None, hours: int=None, minutes: int=None)` |  |
| `idle_timeout` | `def idle_timeout(self, hours: int=None, minutes: int=None, days: int=None)` |  |
| `no_idle_timeout` | `def no_idle_timeout(self)` |  |
| `absolute_timeout` | `def absolute_timeout(self, hours: int=None, minutes: int=None, days: int=None)` | Set absolute timeout (OWASP: max total session lifetime). |
| `with_fingerprint_binding` | `def with_fingerprint_binding(self)` | Enable OWASP session-to-client fingerprint binding. |
| `rotating_on_auth` | `def rotating_on_auth(self)` |  |
| `rotating_on_use` | `def rotating_on_use(self)` |  |
| `scoped_to` | `def scoped_to(self, scope: str)` |  |
| `max_concurrent` | `def max_concurrent(self, limit: int)` |  |
| `unlimited_concurrent` | `def unlimited_concurrent(self)` |  |
| `with_smart_defaults` | `def with_smart_defaults(self)` |  |
| `web_defaults` | `def web_defaults(self)` |  |
| `api_defaults` | `def api_defaults(self)` |  |
| `mobile_defaults` | `def mobile_defaults(self)` |  |
| `admin_defaults` | `def admin_defaults(self)` | Enhanced security defaults for admin users with fingerprint binding. |
| `build` | `def build(self)` |  |

### `Field`

- Source: `aquilia/sessions/state.py`
- Bases: `object`
- Summary: Field descriptor for SessionState.

### `SessionState`

- Source: `aquilia/sessions/state.py`
- Bases: `object`
- Summary: Base class for typed session state.

Methods:

| Method | Signature | Summary |
| --- | --- | --- |
| `get` | `def get(self, key: str, default: Any=None)` | Get state value with default. |
| `to_dict` | `def to_dict(self)` | Convert state to dictionary. |

### `CartState`

- Source: `aquilia/sessions/state.py`
- Bases: `SessionState`
- Summary: Shopping cart session state.

Fields and class attributes:

| Name | Type | Default / Value |
| --- | --- | --- |
| `items` | `list` | `Field(default_factory=list)` |
| `total` | `float` | `Field(default=0.0)` |
| `currency` | `str` | `Field(default='USD')` |

### `UserPreferencesState`

- Source: `aquilia/sessions/state.py`
- Bases: `SessionState`
- Summary: User preferences session state.

Fields and class attributes:

| Name | Type | Default / Value |
| --- | --- | --- |
| `theme` | `str` | `Field(default='light')` |
| `language` | `str` | `Field(default='en')` |
| `notifications` | `bool` | `Field(default=True)` |
| `timezone` | `str` | `Field(default='UTC')` |

### `SessionStore`

- Source: `aquilia/sessions/store.py`
- Bases: `Protocol`
- Summary: Abstract session storage interface.

Methods:

| Method | Signature | Summary |
| --- | --- | --- |
| `load` | `async def load(self, session_id: SessionID)` |  |
| `save` | `async def save(self, session: Session)` |  |
| `delete` | `async def delete(self, session_id: SessionID)` |  |
| `exists` | `async def exists(self, session_id: SessionID)` |  |
| `list_by_principal` | `async def list_by_principal(self, principal_id: str)` |  |
| `count_by_principal` | `async def count_by_principal(self, principal_id: str)` |  |
| `cleanup_expired` | `async def cleanup_expired(self)` |  |
| `shutdown` | `async def shutdown(self)` |  |

### `MemoryStore`

- Source: `aquilia/sessions/store.py`
- Bases: `object`
- Summary: In-memory session storage for development and testing.

Methods:

| Method | Signature | Summary |
| --- | --- | --- |
| `load` | `async def load(self, session_id: SessionID)` |  |
| `save` | `async def save(self, session: Session)` |  |
| `delete` | `async def delete(self, session_id: SessionID)` |  |
| `exists` | `async def exists(self, session_id: SessionID)` |  |
| `list_by_principal` | `async def list_by_principal(self, principal_id: str)` |  |
| `count_by_principal` | `async def count_by_principal(self, principal_id: str)` |  |
| `cleanup_expired` | `async def cleanup_expired(self)` |  |
| `shutdown` | `async def shutdown(self)` |  |
| `get_stats` | `def get_stats(self)` |  |
| `web_optimized` | `def web_optimized(cls)` |  |
| `api_optimized` | `def api_optimized(cls)` |  |
| `development_focused` | `def development_focused(cls)` |  |
| `high_throughput` | `def high_throughput(cls)` |  |

### `FileStore`

- Source: `aquilia/sessions/store.py`
- Bases: `object`
- Summary: File-based session storage for debugging and development. NOT suitable for production.

Methods:

| Method | Signature | Summary |
| --- | --- | --- |
| `load` | `async def load(self, session_id: SessionID)` |  |
| `save` | `async def save(self, session: Session)` |  |
| `delete` | `async def delete(self, session_id: SessionID)` |  |
| `exists` | `async def exists(self, session_id: SessionID)` |  |
| `list_by_principal` | `async def list_by_principal(self, principal_id: str)` |  |
| `count_by_principal` | `async def count_by_principal(self, principal_id: str)` |  |
| `cleanup_expired` | `async def cleanup_expired(self)` |  |
| `shutdown` | `async def shutdown(self)` |  |
| `get_stats` | `def get_stats(self)` |  |

### `SessionTransport`

- Source: `aquilia/sessions/transport.py`
- Bases: `Protocol`
- Summary: Abstract transport interface for session ID delivery.

Methods:

| Method | Signature | Summary |
| --- | --- | --- |
| `extract` | `def extract(self, request: Request)` |  |
| `inject` | `def inject(self, response: Response, session: Session)` |  |
| `clear` | `def clear(self, response: Response)` |  |

### `CookieTransport`

- Source: `aquilia/sessions/transport.py`
- Bases: `object`
- Summary: Cookie-based session transport.

Methods:

| Method | Signature | Summary |
| --- | --- | --- |
| `extract` | `def extract(self, request: Request)` | Extract session ID from cookie. |
| `inject` | `def inject(self, response: Response, session: Session)` | Inject session ID as cookie via response.set_cookie(). |
| `clear` | `def clear(self, response: Response)` | Clear session cookie (logout). |
| `for_web_browsers` | `def for_web_browsers(cls)` |  |
| `for_spa_applications` | `def for_spa_applications(cls)` |  |
| `for_mobile_webviews` | `def for_mobile_webviews(cls)` |  |
| `with_aquilia_defaults` | `def with_aquilia_defaults(cls)` |  |

### `HeaderTransport`

- Source: `aquilia/sessions/transport.py`
- Bases: `object`
- Summary: Header-based session transport for APIs and mobile apps.

Methods:

| Method | Signature | Summary |
| --- | --- | --- |
| `extract` | `def extract(self, request: Request)` |  |
| `inject` | `def inject(self, response: Response, session: Session)` |  |
| `clear` | `def clear(self, response: Response)` |  |
| `for_rest_apis` | `def for_rest_apis(cls)` |  |
| `for_graphql_apis` | `def for_graphql_apis(cls)` |  |
| `for_mobile_apis` | `def for_mobile_apis(cls)` |  |
| `for_microservices` | `def for_microservices(cls)` |  |
| `with_aquilia_defaults` | `def with_aquilia_defaults(cls)` |  |
