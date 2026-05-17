# Testing API Reference

This page is extracted from the current Python source. It includes public classes, methods, functions, constants, dataclass-like fields, decorators, and notable attributes.

## Public Class Summary

| Name | Source | Bases | Purpose |
| --- | --- | --- | --- |
| `AquiliaAssertions` | `aquilia/testing/assertions.py` | object | Mixin class providing Aquilia-specific assertion methods. |
| `TestIdentityFactory` | `aquilia/testing/auth.py` | object | Factory for creating test identities with sensible defaults. |
| `IdentityBuilder` | `aquilia/testing/auth.py` | object | Fluent builder for constructing test identities. |
| `AuthTestMixin` | `aquilia/testing/auth.py` | object | Mixin providing authentication helpers for test cases. |
| `MockCacheBackend` | `aquilia/testing/cache.py` | object | In-memory cache backend for testing with TTL tracking. |
| `CacheTestMixin` | `aquilia/testing/cache.py` | object | Mixin providing cache-specific test helpers. |
| `SimpleTestCase` | `aquilia/testing/cases.py` | unittest.TestCase, AquiliaAssertions | Test case that does NOT start a server. |
| `AquiliaTestCase` | `aquilia/testing/cases.py` | unittest.IsolatedAsyncioTestCase, AquiliaAssertions | Full-featured async test case with integrated server lifecycle. |
| `TransactionTestCase` | `aquilia/testing/cases.py` | AquiliaTestCase | Test case that wraps each test in a database transaction. |
| `LiveServerTestCase` | `aquilia/testing/cases.py` | AquiliaTestCase | Test case that starts a real ASGI server on a random port. |
| `TestResponse` | `aquilia/testing/client.py` | object | Wrapper around captured ASGI response events. |
| `TestClient` | `aquilia/testing/client.py` | object | In-process ASGI test client for Aquilia. |
| `WebSocketTestClient` | `aquilia/testing/client.py` | object | In-process WebSocket test client. |
| `TestConfig` | `aquilia/testing/config.py` | object | Lightweight config wrapper for test overrides. |
| `override_settings` | `aquilia/testing/config.py` | object | Temporarily override Aquilia config values. |
| `TestContainer` | `aquilia/testing/di.py` | Container | A :class:`Container` subclass tailored for testing. |
| `EffectCall` | `aquilia/testing/effects.py` | object | Record of an acquire or release call on a MockEffectProvider. |
| `MockEffectProvider` | `aquilia/testing/effects.py` | EffectProvider | Stub provider that returns configurable values. |
| `MockEffectRegistry` | `aquilia/testing/effects.py` | EffectRegistry | Test-friendly :class:`EffectRegistry` that auto-stubs missing effects. |
| `MockFlowContext` | `aquilia/testing/effects.py` | object | Test-friendly FlowContext for testing pipeline nodes and handlers. |
| `CapturedFault` | `aquilia/testing/faults.py` | object | A fault captured by :class:`MockFaultEngine`. |
| `MockFaultEngine` | `aquilia/testing/faults.py` | object | Drop-in replacement for :class:`~aquilia.faults.engine.FaultEngine` |
| `CapturedMail` | `aquilia/testing/mail.py` | object | A mail message captured during testing. |
| `MailTestMixin` | `aquilia/testing/mail.py` | object | Mixin providing mail assertion helpers. |
| `TestServer` | `aquilia/testing/server.py` | object | Lightweight test server wrapping :class:`AquiliaServer`. |

## Public Function Summary

| Name | Source | Signature | Purpose |
| --- | --- | --- | --- |
| `set_active_config` | `aquilia/testing/config.py` | `def set_active_config(cfg: ConfigLoader) -> None` | Register the config loader used by the running test server. |
| `get_active_config` | `aquilia/testing/config.py` | `def get_active_config() -> ConfigLoader &#124; None` | Return the active config loader. |
| `mock_provider` | `aquilia/testing/di.py` | `def mock_provider(token: type[T] &#124; str, value: T, scope: str = 'singleton') -> _MockProvider` | Create a mock DI provider that always returns *value*. |
| `factory_provider` | `aquilia/testing/di.py` | `def factory_provider(token: type[T] &#124; str, factory: Callable[..., T], scope: str = 'transient') -> _FactoryProvider` | Create a factory DI provider that calls *factory* on each resolve. |
| `override_provider` | `aquilia/testing/di.py` | `async def override_provider(container: Container, token: type[T] &#124; str, mock_value: T, *, tag: str &#124; None = None)` | Temporarily override a provider in a container. |
| `spy_provider` | `aquilia/testing/di.py` | `async def spy_provider(container: Container, token: type[T] &#124; str, *, tag: str &#124; None = None)` | Wrap an existing provider with a spy that tracks calls. |
| `aquilia_fixtures` | `aquilia/testing/fixtures.py` | `def aquilia_fixtures()` | Register Aquilia pytest fixtures. |
| `test_config` | `aquilia/testing/fixtures.py` | `def test_config()` | A blank :class:`TestConfig` for unit tests. |
| `fault_engine` | `aquilia/testing/fixtures.py` | `def fault_engine()` | A :class:`MockFaultEngine` for capturing faults. |
| `effect_registry` | `aquilia/testing/fixtures.py` | `def effect_registry()` | A :class:`MockEffectRegistry` for stubbing effects. |
| `cache_backend` | `aquilia/testing/fixtures.py` | `def cache_backend()` | A :class:`MockCacheBackend` (in-memory, zero-config). |
| `di_container` | `aquilia/testing/fixtures.py` | `def di_container()` | A :class:`TestContainer` with relaxed validation. |
| `identity_factory` | `aquilia/testing/fixtures.py` | `def identity_factory()` | A :class:`TestIdentityFactory` for creating test identities. |
| `mail_outbox` | `aquilia/testing/fixtures.py` | `def mail_outbox()` | Clear the mail outbox before the test and return it. |
| `test_request` | `aquilia/testing/fixtures.py` | `def test_request()` | Factory fixture -- call with kwargs to create test requests. |
| `test_scope` | `aquilia/testing/fixtures.py` | `def test_scope()` | Factory fixture -- call with kwargs to create ASGI scopes. |
| `test_server` | `aquilia/testing/fixtures.py` | `async def test_server()` | Async fixture providing a booted :class:`TestServer`. |
| `test_client` | `aquilia/testing/fixtures.py` | `async def test_client(test_server)` | Async fixture providing a :class:`TestClient` wired to a :class:`TestServer`. |
| `ws_client` | `aquilia/testing/fixtures.py` | `async def ws_client(test_server)` | Async fixture providing a :class:`WebSocketTestClient` wired to a :class:`TestServer`. |
| `settings_override` | `aquilia/testing/fixtures.py` | `def settings_override()` | Fixture factory for overriding settings. |
| `get_outbox` | `aquilia/testing/mail.py` | `def get_outbox() -> list[CapturedMail]` | Return the global mail outbox. |
| `clear_outbox` | `aquilia/testing/mail.py` | `def clear_outbox() -> None` | Clear the global mail outbox. |
| `capture_mail` | `aquilia/testing/mail.py` | `def capture_mail(to: list[str], subject: str, body: str = '', **kwargs: Any) -> CapturedMail` | Add a message to the outbox (called by the test mail provider). |
| `create_test_server` | `aquilia/testing/server.py` | `def create_test_server(*manifests: AppManifest, config_overrides: dict[str, Any] &#124; None = None, **kwargs: Any) -> TestServer` | Shortcut to create a :class:`TestServer`. |
| `make_test_scope` | `aquilia/testing/utils.py` | `def make_test_scope(method: str = 'GET', path: str = '/', query_string: str = '', headers: list[tuple] &#124; None = None, scheme: str = 'http', client: tuple &#124; None = None, server: tuple &#124; None = None, root_path: str = '', http_version: str = '1.1', scope_type: str = 'http') -> dict` | Build a minimal ASGI HTTP scope for testing. |
| `make_test_receive` | `aquilia/testing/utils.py` | `def make_test_receive(body: bytes = b'', *, chunks: list[bytes] &#124; None = None)` | Create an ASGI receive callable. |
| `make_test_request` | `aquilia/testing/utils.py` | `def make_test_request(method: str = 'GET', path: str = '/', query_string: str = '', headers: list[tuple] &#124; None = None, body: bytes = b'', scheme: str = 'http', client: tuple &#124; None = None, json: Any = None, form_data: dict[str, str] &#124; None = None, **kwargs: Any) -> Request` | Build a full :class:`~aquilia.request.Request` for testing. |
| `make_test_response` | `aquilia/testing/utils.py` | `def make_test_response(content: bytes &#124; str &#124; dict &#124; list = b'', status: int = 200, headers: dict[str, str] &#124; None = None, media_type: str &#124; None = None) -> Response` | Build a :class:`~aquilia.response.Response` for assertion helpers. |
| `make_test_ws_scope` | `aquilia/testing/utils.py` | `def make_test_ws_scope(path: str = '/ws', headers: list[tuple] &#124; None = None, subprotocols: list[str] &#124; None = None, query_string: str = '', client: tuple &#124; None = None, server: tuple &#124; None = None) -> dict` | Build an ASGI WebSocket scope for testing. |
| `make_upload_file` | `aquilia/testing/utils.py` | `def make_upload_file(filename: str, content: bytes &#124; str, content_type: str = 'application/octet-stream') -> tuple` | Create a file tuple suitable for :class:`TestClient` upload. |

## Constants

| Name | Source | Value or type |
| --- | --- | --- |
| `_SENTINEL` | `aquilia/testing/config.py` | `object()` |
| `T` | `aquilia/testing/di.py` | `TypeVar('T')` |

## Detailed Classes And Methods

### Class: `AquiliaAssertions`

- Source: `aquilia/testing/assertions.py`
- Bases: `object`
- Summary: Mixin class providing Aquilia-specific assertion methods.

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `assert_status` | `def assert_status(self, response, expected: int, msg: str = '')` |  | Assert HTTP status code. |
| `assert_status_in_range` | `def assert_status_in_range(self, response, low: int, high: int, msg: str = '')` |  | Assert status code is within [low, high) range. |
| `assert_success` | `def assert_success(self, response, msg: str = '')` |  | Assert 2xx status. |
| `assert_created` | `def assert_created(self, response, msg: str = '')` |  | Assert 201 Created. |
| `assert_accepted` | `def assert_accepted(self, response, msg: str = '')` |  | Assert 202 Accepted. |
| `assert_no_content` | `def assert_no_content(self, response, msg: str = '')` |  | Assert 204 No Content. |
| `assert_redirect` | `def assert_redirect(self, response, location: str &#124; None = None, msg: str = '')` |  | Assert 3xx redirect, optionally checking Location header. |
| `assert_permanent_redirect` | `def assert_permanent_redirect(self, response, location: str &#124; None = None, msg: str = '')` |  | Assert 301 Moved Permanently. |
| `assert_bad_request` | `def assert_bad_request(self, response, msg: str = '')` |  | Assert 400. |
| `assert_unauthorized` | `def assert_unauthorized(self, response, msg: str = '')` |  | Assert 401. |
| `assert_forbidden` | `def assert_forbidden(self, response, msg: str = '')` |  | Assert 403. |
| `assert_not_found` | `def assert_not_found(self, response, msg: str = '')` |  | Assert 404. |
| `assert_method_not_allowed` | `def assert_method_not_allowed(self, response, msg: str = '')` |  | Assert 405 Method Not Allowed. |
| `assert_conflict` | `def assert_conflict(self, response, msg: str = '')` |  | Assert 409 Conflict. |
| `assert_gone` | `def assert_gone(self, response, msg: str = '')` |  | Assert 410 Gone. |
| `assert_unprocessable` | `def assert_unprocessable(self, response, msg: str = '')` |  | Assert 422 Unprocessable Entity. |
| `assert_too_many_requests` | `def assert_too_many_requests(self, response, msg: str = '')` |  | Assert 429 Too Many Requests. |
| `assert_server_error` | `def assert_server_error(self, response, msg: str = '')` |  | Assert 500 Internal Server Error. |
| `assert_service_unavailable` | `def assert_service_unavailable(self, response, msg: str = '')` |  | Assert 503 Service Unavailable. |
| `assert_json` | `def assert_json(self, response, expected: Any = None, msg: str = '')` |  | Assert response is JSON, optionally matching expected value. |
| `assert_json_contains` | `def assert_json_contains(self, response, subset: dict[str, Any], msg: str = '')` |  | Assert JSON body contains all keys/values from *subset*. |
| `assert_json_key` | `def assert_json_key(self, response, key: str, msg: str = '')` |  | Assert JSON body contains a specific key. |
| `assert_json_path` | `def assert_json_path(self, response, path: str, expected: Any = _sentinel, msg: str = '')` |  | Assert a deeply nested JSON value using dot-notation. |
| `assert_json_list` | `def assert_json_list(self, response, min_length: int &#124; None = None, msg: str = '')` |  | Assert JSON body is a list, optionally with minimum length. |
| `assert_json_length` | `def assert_json_length(self, response, expected: int, msg: str = '')` |  | Assert JSON list/dict has exactly *expected* items/keys. |
| `assert_json_not_empty` | `def assert_json_not_empty(self, response, msg: str = '')` |  | Assert JSON body is non-empty (non-null, non-empty list/dict). |
| `assert_html` | `def assert_html(self, response, msg: str = '')` |  | Assert response is HTML. |
| `assert_content_type` | `def assert_content_type(self, response, expected: str, msg: str = '')` |  | Assert exact content type. |
| `assert_header` | `def assert_header(self, response, name: str, value: str &#124; None = None, msg: str = '')` |  | Assert response header exists (and optionally matches value). |
| `assert_header_contains` | `def assert_header_contains(self, response, name: str, substring: str, msg: str = '')` |  | Assert response header value contains a substring. |
| `assert_no_header` | `def assert_no_header(self, response, name: str, msg: str = '')` |  | Assert response header does NOT exist. |
| `assert_content_length` | `def assert_content_length(self, response, expected: int &#124; None = None, msg: str = '')` |  | Assert Content-Length header exists (and optionally matches). |
| `assert_cookie` | `def assert_cookie(self, response, name: str, msg: str = '')` |  | Assert Set-Cookie header contains the named cookie. |
| `assert_cookie_value` | `def assert_cookie_value(self, response, name: str, expected: str, msg: str = '')` |  | Assert a cookie's value in Set-Cookie header. |
| `assert_no_cookie` | `def assert_no_cookie(self, response, name: str, msg: str = '')` |  | Assert Set-Cookie does NOT contain the named cookie. |
| `assert_body_contains` | `def assert_body_contains(self, response, text: str, msg: str = '')` |  | Assert text body contains substring. |
| `assert_body_not_contains` | `def assert_body_not_contains(self, response, text: str, msg: str = '')` |  | Assert text body does NOT contain substring. |
| `assert_body_empty` | `def assert_body_empty(self, response, msg: str = '')` |  | Assert response body is empty. |
| `assert_fault_raised` | `def assert_fault_raised(self, fault_engine_or_captured: Any, code: str &#124; None = None, domain: str &#124; None = None, msg: str = '')` |  | Assert that a fault was emitted / captured. |
| `assert_no_faults` | `def assert_no_faults(self, fault_engine_or_captured: Any, msg: str = '')` |  | Assert no faults were captured. |
| `assert_fault_count` | `def assert_fault_count(self, fault_engine_or_captured: Any, expected: int, msg: str = '')` |  | Assert exact number of faults captured. |
| `assert_fault_severity` | `def assert_fault_severity(self, fault_engine_or_captured: Any, severity: Any, code: str &#124; None = None, msg: str = '')` |  | Assert fault(s) have the expected severity. |
| `assert_registered` | `def assert_registered(self, container, token: Any, msg: str = '')` |  | Assert a service is registered in the DI container. |
| `assert_not_registered` | `def assert_not_registered(self, container, token: Any, msg: str = '')` |  | Assert a service is NOT registered in the DI container. |
| `assert_resolves` | `def assert_resolves(self, container, token: Any, msg: str = '')` |  | Assert a service resolves successfully (sync). |
| `assert_resolves_async` | `async def assert_resolves_async(self, container, token: Any, msg: str = '')` |  | Assert a service resolves successfully (async). |
| `assert_effect_acquired` | `def assert_effect_acquired(self, provider: Any, count: int &#124; None = None, msg: str = '')` |  | Assert an effect provider's acquire was called. |
| `assert_effect_released` | `def assert_effect_released(self, provider: Any, count: int &#124; None = None, msg: str = '')` |  | Assert an effect provider's release was called. |
| `assert_cache_hit` | `async def assert_cache_hit(self, cache: Any, key: str, expected: Any = _sentinel, msg: str = '')` |  | Assert a cache key exists (and optionally matches value). |
| `assert_cache_miss` | `async def assert_cache_miss(self, cache: Any, key: str, msg: str = '')` |  | Assert a cache key does NOT exist. |
| `assert_mail_count` | `def assert_mail_count(self, outbox: Any, expected: int, msg: str = '')` |  | Assert exact number of messages in the mail outbox. |
| `assert_mail_to` | `def assert_mail_to(self, outbox: Any, address: str, msg: str = '')` |  | Assert at least one message was sent to *address*. |
| `assert_mail_from` | `def assert_mail_from(self, outbox: Any, address: str, msg: str = '')` |  | Assert at least one message was sent from *address*. |

### Class: `TestIdentityFactory`

- Source: `aquilia/testing/auth.py`
- Bases: `object`
- Summary: Factory for creating test identities with sensible defaults.

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `user` | `def user(cls, id: str &#124; None = None, email: str &#124; None = None, name: str &#124; None = None, roles: list[str] &#124; None = None, scopes: list[str] &#124; None = None, status: IdentityStatus = IdentityStatus.ACTIVE, tenant_id: str &#124; None = None, **extra_attrs: Any) -> Identity` | classmethod | Create a regular user identity. |
| `admin` | `def admin(cls, id: str &#124; None = None, **kw) -> Identity` | classmethod | Create an admin identity. |
| `service` | `def service(cls, id: str &#124; None = None, scopes: list[str] &#124; None = None, **kw) -> Identity` | classmethod | Create a service/API-key identity. |
| `anonymous` | `def anonymous(cls) -> Identity` | classmethod | Create an anonymous (unauthenticated) identity. |
| `suspended` | `def suspended(cls, id: str &#124; None = None, **kw) -> Identity` | classmethod | Create a suspended user identity. |
| `build` | `def build(cls, id: str &#124; None = None) -> IdentityBuilder` | classmethod | Start building an identity with the fluent API. |

### Class: `IdentityBuilder`

- Source: `aquilia/testing/auth.py`
- Bases: `object`
- Summary: Fluent builder for constructing test identities.

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `with_roles` | `def with_roles(self, *roles: str) -> IdentityBuilder` |  | Method. |
| `with_scopes` | `def with_scopes(self, *scopes: str) -> IdentityBuilder` |  | Method. |
| `with_email` | `def with_email(self, email: str) -> IdentityBuilder` |  | Method. |
| `with_name` | `def with_name(self, name: str) -> IdentityBuilder` |  | Method. |
| `with_tenant` | `def with_tenant(self, tenant_id: str) -> IdentityBuilder` |  | Method. |
| `with_status` | `def with_status(self, status: IdentityStatus) -> IdentityBuilder` |  | Method. |
| `with_type` | `def with_type(self, type: IdentityType) -> IdentityBuilder` |  | Method. |
| `with_attr` | `def with_attr(self, key: str, value: Any) -> IdentityBuilder` |  | Method. |
| `as_service` | `def as_service(self) -> IdentityBuilder` |  | Method. |
| `as_suspended` | `def as_suspended(self) -> IdentityBuilder` |  | Method. |
| `create` | `def create(self) -> Identity` |  | Build and return the Identity. |

### Class: `AuthTestMixin`

- Source: `aquilia/testing/auth.py`
- Bases: `object`
- Summary: Mixin providing authentication helpers for test cases.

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `force_login` | `def force_login(self, identity: Identity) -> None` |  | Bypass the normal auth flow and inject an identity into the |
| `force_logout` | `def force_logout(self) -> None` |  | Remove any forced authentication. |
| `current_identity` | `def current_identity(self) -> Identity &#124; None` | property | Return the currently forced identity (or None). |
| `is_authenticated` | `def is_authenticated(self) -> bool` | property | Check if a test identity is currently forced. |
| `authenticate_as` | `async def authenticate_as(self, identity: Identity) -> None` |  | Authenticate by injecting the identity into the DI container. |
| `login_as_admin` | `def login_as_admin(self, id: str &#124; None = None, **kw) -> Identity` |  | Convenience: create admin identity and force login. |
| `login_as_user` | `def login_as_user(self, id: str &#124; None = None, **kw) -> Identity` |  | Convenience: create user identity and force login. |

### Class: `MockCacheBackend`

- Source: `aquilia/testing/cache.py`
- Bases: `object`
- Summary: In-memory cache backend for testing with TTL tracking.

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `get_ttl` | `def get_ttl(self, key: str) -> float &#124; None` |  | Return remaining TTL in seconds, or None if no TTL set. |
| `connect` | `async def connect(self)` |  | Method. |
| `disconnect` | `async def disconnect(self)` |  | Method. |
| `get` | `async def get(self, key: str) -> Any &#124; None` |  | Method. |
| `set` | `async def set(self, key: str, value: Any, ttl: int &#124; None = None)` |  | Method. |
| `get_or_set` | `async def get_or_set(self, key: str, default: Any, ttl: int &#124; None = None) -> Any` |  | Get existing value or set & return default. |
| `delete` | `async def delete(self, key: str) -> bool` |  | Method. |
| `exists` | `async def exists(self, key: str) -> bool` |  | Method. |
| `clear` | `async def clear(self)` |  | Method. |
| `keys` | `async def keys(self, pattern: str = '*') -> list[str]` |  | Method. |
| `increment` | `async def increment(self, key: str, delta: int = 1) -> int` |  | Increment a numeric cache value. |
| `decrement` | `async def decrement(self, key: str, delta: int = 1) -> int` |  | Decrement a numeric cache value. |
| `mget` | `async def mget(self, *keys: str) -> list[Any &#124; None]` |  | Get multiple values at once. |
| `mset` | `async def mset(self, mapping: dict[str, Any], ttl: int &#124; None = None) -> None` |  | Set multiple values at once. |
| `health_check` | `async def health_check(self) -> bool` |  | Method. |
| `store` | `def store(self) -> dict[str, Any]` | property | Direct access to the underlying store for assertions. |
| `size` | `def size(self) -> int` | property | Number of keys currently in the store. |
| `reset` | `def reset(self)` |  | Clear store, TTLs, and counters. |

### Class: `CacheTestMixin`

- Source: `aquilia/testing/cache.py`
- Bases: `object`
- Summary: Mixin providing cache-specific test helpers.

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `assert_cached` | `async def assert_cached(self, key: str, msg: str = '')` |  | Assert a key is present in the cache. |
| `assert_not_cached` | `async def assert_not_cached(self, key: str, msg: str = '')` |  | Assert a key is NOT present in the cache. |
| `assert_cache_value` | `async def assert_cache_value(self, key: str, expected: Any, msg: str = '')` |  | Assert a cached key equals an expected value. |
| `assert_cache_count` | `async def assert_cache_count(self, expected: int, pattern: str = '*', msg: str = '')` |  | Assert the number of keys in the cache. |
| `populate_cache` | `async def populate_cache(self, data: dict[str, Any], ttl: int &#124; None = None)` |  | Bulk-populate cache entries. |
| `flush_cache` | `async def flush_cache(self)` |  | Clear the entire cache. |

### Class: `SimpleTestCase`

- Source: `aquilia/testing/cases.py`
- Bases: `unittest.TestCase, AquiliaAssertions`
- Summary: Test case that does NOT start a server.

### Class: `AquiliaTestCase`

- Source: `aquilia/testing/cases.py`
- Bases: `unittest.IsolatedAsyncioTestCase, AquiliaAssertions`
- Summary: Full-featured async test case with integrated server lifecycle.

Attributes and fields:

| Name | Type | Default |
| --- | --- | --- |
| `manifests` | `list[AppManifest]` | `[]` |
| `settings` | `dict[str, Any]` | `{}` |
| `enable_cache` | `bool` | `False` |
| `enable_sessions` | `bool` | `False` |
| `enable_auth` | `bool` | `False` |
| `enable_mail` | `bool` | `False` |
| `enable_templates` | `bool` | `False` |
| `server` | `TestServer` |  |
| `client` | `TestClient` |  |

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `asyncSetUp` | `async def asyncSetUp(self) -> None` |  | Boot the test server and create a client. |
| `asyncTearDown` | `async def asyncTearDown(self) -> None` |  | Shutdown the test server. |
| `di_container` | `def di_container(self)` | property | Method. |
| `fault_engine` | `def fault_engine(self)` | property | Method. |
| `config` | `def config(self)` | property | Method. |
| `controller_router` | `def controller_router(self)` | property | Method. |
| `effect_registry` | `def effect_registry(self)` | property | Method. |
| `cache_service` | `def cache_service(self)` | property | Method. |
| `get_url` | `def get_url(self, route_name: str, **params: str) -> str` |  | Reverse a named route to its URL. |
| `login` | `async def login(self, username: str = 'test@test.com', password: str = 'password') -> TestResponse` |  | Convenience login helper. |

### Class: `TransactionTestCase`

- Source: `aquilia/testing/cases.py`
- Bases: `AquiliaTestCase`
- Summary: Test case that wraps each test in a database transaction.

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `asyncSetUp` | `async def asyncSetUp(self) -> None` |  | Method. |
| `asyncTearDown` | `async def asyncTearDown(self) -> None` |  | Method. |

### Class: `LiveServerTestCase`

- Source: `aquilia/testing/cases.py`
- Bases: `AquiliaTestCase`
- Summary: Test case that starts a real ASGI server on a random port.

Attributes and fields:

| Name | Type | Default |
| --- | --- | --- |
| `host` | `str` | `'127.0.0.1'` |
| `port` | `int` | `0` |
| `live_server_url` | `str` | `''` |

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `asyncSetUp` | `async def asyncSetUp(self) -> None` |  | Method. |
| `asyncTearDown` | `async def asyncTearDown(self) -> None` |  | Method. |

### Class: `TestResponse`

- Source: `aquilia/testing/client.py`
- Bases: `object`
- Summary: Wrapper around captured ASGI response events.

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `text` | `def text(self) -> str` | property | Body decoded as text. |
| `json` | `def json(self) -> Any` |  | Parse body as JSON. |
| `is_success` | `def is_success(self) -> bool` | property | Method. |
| `is_redirect` | `def is_redirect(self) -> bool` | property | Method. |
| `is_client_error` | `def is_client_error(self) -> bool` | property | Method. |
| `is_server_error` | `def is_server_error(self) -> bool` | property | Method. |
| `content_length` | `def content_length(self) -> int &#124; None` | property | Return Content-Length as int, or None. |
| `location` | `def location(self) -> str &#124; None` | property | Return Location header (useful for redirects). |
| `header` | `def header(self, name: str, default: str &#124; None = None) -> str &#124; None` |  | Method. |
| `has_header` | `def has_header(self, name: str) -> bool` |  | Check if header exists. |

### Class: `TestClient`

- Source: `aquilia/testing/client.py`
- Bases: `object`
- Summary: In-process ASGI test client for Aquilia.

Attributes and fields:

| Name | Type | Default |
| --- | --- | --- |
| `MAX_REDIRECTS` |  | `20` |

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `set_bearer_token` | `def set_bearer_token(self, token: str) -> None` |  | Set Authorization: Bearer <token> header for all requests. |
| `clear_auth` | `def clear_auth(self) -> None` |  | Remove Authorization header. |
| `history` | `def history(self) -> list[TestResponse]` | property | Redirect chain history from the last request. |
| `get` | `async def get(self, path: str, **kw) -> TestResponse` |  | Method. |
| `post` | `async def post(self, path: str, json: Any = None, data: dict[str, str] &#124; None = None, body: bytes = b'', files: dict[str, Any] &#124; None = None, **kw) -> TestResponse` |  | Method. |
| `put` | `async def put(self, path: str, json: Any = None, body: bytes = b'', files: dict[str, Any] &#124; None = None, **kw) -> TestResponse` |  | Method. |
| `patch` | `async def patch(self, path: str, json: Any = None, body: bytes = b'', files: dict[str, Any] &#124; None = None, **kw) -> TestResponse` |  | Method. |
| `delete` | `async def delete(self, path: str, **kw) -> TestResponse` |  | Method. |
| `head` | `async def head(self, path: str, **kw) -> TestResponse` |  | Method. |
| `options` | `async def options(self, path: str, **kw) -> TestResponse` |  | Method. |
| `set_cookie` | `def set_cookie(self, name: str, value: str) -> None` |  | Method. |
| `delete_cookie` | `def delete_cookie(self, name: str) -> None` |  | Remove a specific cookie. |
| `clear_cookies` | `def clear_cookies(self) -> None` |  | Method. |
| `cookies` | `def cookies(self) -> dict[str, str]` | property | Read-only view of the cookie jar. |

### Class: `WebSocketTestClient`

- Source: `aquilia/testing/client.py`
- Bases: `object`
- Summary: In-process WebSocket test client.

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `connect` | `async def connect(self, path: str = '/ws', headers: list[tuple] &#124; None = None, subprotocols: list[str] &#124; None = None) -> None` |  | Initiate WebSocket handshake. |
| `send_text` | `async def send_text(self, text: str) -> None` |  | Method. |
| `send_json` | `async def send_json(self, data: Any) -> None` |  | Method. |
| `send_bytes` | `async def send_bytes(self, data: bytes) -> None` |  | Method. |
| `receive` | `async def receive(self, timeout: float = 5.0) -> dict` |  | Method. |
| `receive_text` | `async def receive_text(self, timeout: float = 5.0) -> str` |  | Method. |
| `receive_json` | `async def receive_json(self, timeout: float = 5.0) -> Any` |  | Method. |
| `receive_bytes` | `async def receive_bytes(self, timeout: float = 5.0) -> bytes` |  | Receive binary data from the WebSocket. |
| `is_connected` | `def is_connected(self) -> bool` | property | Whether the WebSocket is currently connected. |
| `close` | `async def close(self, code: int = 1000) -> None` |  | Method. |

### Class: `TestConfig`

- Source: `aquilia/testing/config.py`
- Bases: `object`
- Summary: Lightweight config wrapper for test overrides.

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `get` | `def get(self, key: str, default: Any = None) -> Any` |  | Retrieve a config value using dot-notation. |
| `set` | `def set(self, key: str, value: Any) -> None` |  | Set a config value using dot-notation (mutates overrides). |
| `has` | `def has(self, key: str) -> bool` |  | Check if a config key exists. |
| `keys` | `def keys(self) -> list` |  | Return top-level config keys. |
| `config_data` | `def config_data(self) -> dict` | property | Return merged config dict (compatible with ConfigLoader). |
| `to_dict` | `def to_dict(self) -> dict` |  | Return merged config as a plain dictionary. |
| `get_cache_config` | `def get_cache_config(self) -> dict` |  | Method. |
| `get_session_config` | `def get_session_config(self) -> dict` |  | Method. |
| `get_auth_config` | `def get_auth_config(self) -> dict` |  | Method. |
| `get_mail_config` | `def get_mail_config(self) -> dict` |  | Method. |
| `get_template_config` | `def get_template_config(self) -> dict` |  | Method. |

### Class: `override_settings`

- Source: `aquilia/testing/config.py`
- Bases: `object`
- Summary: Temporarily override Aquilia config values.

### Class: `TestContainer`

- Source: `aquilia/testing/di.py`
- Bases: `Container`
- Summary: A :class:`Container` subclass tailored for testing.

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `register` | `def register(self, provider: Provider, tag: str &#124; None = None)` |  | Register, silently overwriting duplicates. |
| `register_value` | `def register_value(self, token: type &#124; str, value: Any, scope: str = 'singleton', tag: str &#124; None = None) -> _MockProvider` |  | Shortcut: register a fixed value provider. |
| `register_factory` | `def register_factory(self, token: type &#124; str, factory: Callable[..., Any], scope: str = 'transient', tag: str &#124; None = None) -> _FactoryProvider` |  | Shortcut: register a factory provider. |
| `resolve` | `def resolve(self, token, *, tag = None, optional = False)` |  | Method. |
| `reset` | `def reset(self)` |  | Clear cache and resolution log. |

### Class: `EffectCall`

- Source: `aquilia/testing/effects.py`
- Bases: `object`
- Decorators: `dataclass`
- Summary: Record of an acquire or release call on a MockEffectProvider.

Attributes and fields:

| Name | Type | Default |
| --- | --- | --- |
| `action` | `str` |  |
| `mode` | `str &#124; None` | `None` |
| `resource` | `Any` | `None` |
| `success` | `bool &#124; None` | `None` |
| `timestamp` | `float` | `0.0` |

### Class: `MockEffectProvider`

- Source: `aquilia/testing/effects.py`
- Bases: `EffectProvider`
- Summary: Stub provider that returns configurable values.

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `initialize` | `async def initialize(self)` |  | Method. |
| `acquire` | `async def acquire(self, mode: str &#124; None = None) -> Any` |  | Method. |
| `release` | `async def release(self, resource: Any, success: bool = True)` |  | Method. |
| `finalize` | `async def finalize(self)` |  | Method. |
| `last_acquired_mode` | `def last_acquired_mode(self) -> str &#124; None` | property | Return the mode from the last acquire call. |
| `reset` | `def reset(self)` |  | Reset all tracking counters. |

### Class: `MockEffectRegistry`

- Source: `aquilia/testing/effects.py`
- Bases: `EffectRegistry`
- Summary: Test-friendly :class:`EffectRegistry` that auto-stubs missing effects.

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `register_mock` | `def register_mock(self, effect_name: str, return_value: Any = None, **kw) -> MockEffectProvider` |  | Register a mock provider for the given effect name. |
| `get_provider` | `def get_provider(self, effect_name: str) -> EffectProvider` |  | Return the provider - auto-creating a mock if not registered. |
| `get_mock` | `def get_mock(self, effect_name: str) -> MockEffectProvider &#124; None` |  | Retrieve the underlying mock (or ``None``). |
| `reset_all` | `def reset_all(self)` |  | Reset tracking on all mock providers. |

### Class: `MockFlowContext`

- Source: `aquilia/testing/effects.py`
- Bases: `object`
- Summary: Test-friendly FlowContext for testing pipeline nodes and handlers.

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `from_registry` | `def from_registry(registry: MockEffectRegistry, *, request: Any = None, container: Any = None, identity: Any = None, session: Any = None, state: dict[str, Any] &#124; None = None) -> Any` | staticmethod | Create a FlowContext with pre-acquired mock effects. |
| `create` | `def create(*, effects: dict[str, Any] &#124; None = None, request: Any = None, container: Any = None, identity: Any = None, session: Any = None, state: dict[str, Any] &#124; None = None) -> Any` | staticmethod | Create a FlowContext with manually specified effect values. |

### Class: `CapturedFault`

- Source: `aquilia/testing/faults.py`
- Bases: `object`
- Decorators: `dataclass`
- Summary: A fault captured by :class:`MockFaultEngine`.

Attributes and fields:

| Name | Type | Default |
| --- | --- | --- |
| `fault` | `Fault` |  |
| `domain` | `str &#124; None` | `None` |
| `app_name` | `str &#124; None` | `None` |
| `handler_name` | `str &#124; None` | `None` |
| `timestamp` | `float` | `0.0` |

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `code` | `def code(self) -> str` | property | Method. |
| `message` | `def message(self) -> str` | property | Method. |
| `severity` | `def severity(self) -> Severity &#124; None` | property | Method. |

### Class: `MockFaultEngine`

- Source: `aquilia/testing/faults.py`
- Bases: `object`
- Summary: Drop-in replacement for :class:`~aquilia.faults.engine.FaultEngine`

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `emit` | `def emit(self, fault: Fault, *, app_name: str &#124; None = None, handler_name: str &#124; None = None, **context: Any)` |  | Capture a fault emission. |
| `raise_fault` | `def raise_fault(self, fault: Fault, **kw)` |  | Alias used by some subsystems. |
| `register_app` | `def register_app(self, app_name: str, handler: Any = None)` |  | Method. |
| `register_handler` | `def register_handler(self, domain: str, handler: Any)` |  | Method. |
| `has_fault` | `def has_fault(self, code: str) -> bool` |  | Check if a fault with the given code was captured. |
| `get_faults` | `def get_faults(self, code: str &#124; None = None, domain: str &#124; None = None, severity: Severity &#124; None = None) -> list[CapturedFault]` |  | Filter captured faults by code, domain, and/or severity. |
| `fault_codes` | `def fault_codes(self) -> list[str]` | property | Method. |
| `fault_count` | `def fault_count(self) -> int` | property | Method. |
| `last_fault` | `def last_fault(self) -> CapturedFault &#124; None` | property | Return the most recently captured fault, or ``None``. |
| `last_fault_code` | `def last_fault_code(self) -> str &#124; None` | property | Return the code of the most recently captured fault. |
| `has_fault_with_severity` | `def has_fault_with_severity(self, severity: Severity) -> bool` |  | Check if any fault with given severity was captured. |
| `reset` | `def reset(self)` |  | Clear all captured faults. |

### Class: `CapturedMail`

- Source: `aquilia/testing/mail.py`
- Bases: `object`
- Decorators: `dataclass`
- Summary: A mail message captured during testing.

Attributes and fields:

| Name | Type | Default |
| --- | --- | --- |
| `to` | `list[str]` |  |
| `subject` | `str` |  |
| `body` | `str` | `''` |
| `html_body` | `str` | `''` |
| `from_email` | `str` | `''` |
| `cc` | `list[str]` | `field(default_factory=list)` |
| `bcc` | `list[str]` | `field(default_factory=list)` |
| `reply_to` | `str &#124; None` | `None` |
| `attachments` | `list[dict[str, Any]]` | `field(default_factory=list)` |
| `headers` | `dict[str, str]` | `field(default_factory=dict)` |
| `provider` | `str` | `''` |
| `template_name` | `str &#124; None` | `None` |

### Class: `MailTestMixin`

- Source: `aquilia/testing/mail.py`
- Bases: `object`
- Summary: Mixin providing mail assertion helpers.

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `setUp` | `def setUp(self) -> None` |  | Method. |
| `mail_outbox` | `def mail_outbox(self) -> list[CapturedMail]` | property | All captured mail messages. |
| `latest_mail` | `def latest_mail(self) -> CapturedMail &#124; None` | property | Return the most recently sent mail, or None. |
| `get_mail_for` | `def get_mail_for(self, address: str) -> list[CapturedMail]` |  | Return all mail sent to a specific address. |
| `assert_mail_sent` | `def assert_mail_sent(self, to: str &#124; None = None, count: int &#124; None = None, msg: str = '')` |  | Assert that mail was sent. |
| `assert_no_mail_sent` | `def assert_no_mail_sent(self, msg: str = '')` |  | Assert that no mail was sent. |
| `assert_mail_count` | `def assert_mail_count(self, expected: int, msg: str = '')` |  | Assert exact number of messages in the outbox. |
| `assert_mail_to` | `def assert_mail_to(self, address: str, msg: str = '')` |  | Assert at least one message was sent to *address*. |
| `assert_mail_from` | `def assert_mail_from(self, address: str, msg: str = '')` |  | Assert at least one message was sent from *address*. |
| `assert_mail_subject_contains` | `def assert_mail_subject_contains(self, text: str, msg: str = '')` |  | Assert at least one message has a subject containing *text*. |
| `assert_mail_body_contains` | `def assert_mail_body_contains(self, text: str, msg: str = '')` |  | Assert at least one message has body containing *text*. |
| `assert_mail_has_attachment` | `def assert_mail_has_attachment(self, filename: str &#124; None = None, msg: str = '')` |  | Assert at least one message has an attachment. |
| `assert_mail_cc` | `def assert_mail_cc(self, address: str, msg: str = '')` |  | Assert at least one message has *address* in CC. |
| `assert_mail_bcc` | `def assert_mail_bcc(self, address: str, msg: str = '')` |  | Assert at least one message has *address* in BCC. |

### Class: `TestServer`

- Source: `aquilia/testing/server.py`
- Bases: `object`
- Summary: Lightweight test server wrapping :class:`AquiliaServer`.

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `start` | `async def start(self) -> TestServer` |  | Boot the server (idempotent). |
| `stop` | `async def stop(self) -> None` |  | Shutdown the server (idempotent). |
| `server` | `def server(self) -> AquiliaServer` | property | Method. |
| `app` | `def app(self)` | property | ASGI application. |
| `config` | `def config(self) -> TestConfig` | property | Method. |
| `is_running` | `def is_running(self) -> bool` | property | Whether the server is currently started. |
| `fault_engine` | `def fault_engine(self)` | property | Method. |
| `di_container` | `def di_container(self)` | property | Return the first available DI container. |
| `controller_router` | `def controller_router(self)` | property | Method. |
| `middleware_stack` | `def middleware_stack(self)` | property | Method. |
| `effect_registry` | `def effect_registry(self)` | property | Method. |
| `cache_service` | `def cache_service(self)` | property | Method. |
| `session_engine` | `def session_engine(self)` | property | Method. |
| `auth_manager` | `def auth_manager(self)` | property | Method. |
| `mail_provider` | `def mail_provider(self)` | property | Method. |
| `reload` | `async def reload(self) -> TestServer` |  | Restart the server (stop + start). |
| `get_url` | `def get_url(self, route_name: str, **params: str) -> str` |  | Reverse a named route to its URL. |

## Functions

| Name | Source | Signature | Purpose |
| --- | --- | --- | --- |
| `set_active_config` | `aquilia/testing/config.py` | `def set_active_config(cfg: ConfigLoader) -> None` | Register the config loader used by the running test server. |
| `get_active_config` | `aquilia/testing/config.py` | `def get_active_config() -> ConfigLoader &#124; None` | Return the active config loader. |
| `mock_provider` | `aquilia/testing/di.py` | `def mock_provider(token: type[T] &#124; str, value: T, scope: str = 'singleton') -> _MockProvider` | Create a mock DI provider that always returns *value*. |
| `factory_provider` | `aquilia/testing/di.py` | `def factory_provider(token: type[T] &#124; str, factory: Callable[..., T], scope: str = 'transient') -> _FactoryProvider` | Create a factory DI provider that calls *factory* on each resolve. |
| `override_provider` | `aquilia/testing/di.py` | `async def override_provider(container: Container, token: type[T] &#124; str, mock_value: T, *, tag: str &#124; None = None)` | Temporarily override a provider in a container. |
| `spy_provider` | `aquilia/testing/di.py` | `async def spy_provider(container: Container, token: type[T] &#124; str, *, tag: str &#124; None = None)` | Wrap an existing provider with a spy that tracks calls. |
| `aquilia_fixtures` | `aquilia/testing/fixtures.py` | `def aquilia_fixtures()` | Register Aquilia pytest fixtures. |
| `test_config` | `aquilia/testing/fixtures.py` | `def test_config()` | A blank :class:`TestConfig` for unit tests. |
| `fault_engine` | `aquilia/testing/fixtures.py` | `def fault_engine()` | A :class:`MockFaultEngine` for capturing faults. |
| `effect_registry` | `aquilia/testing/fixtures.py` | `def effect_registry()` | A :class:`MockEffectRegistry` for stubbing effects. |
| `cache_backend` | `aquilia/testing/fixtures.py` | `def cache_backend()` | A :class:`MockCacheBackend` (in-memory, zero-config). |
| `di_container` | `aquilia/testing/fixtures.py` | `def di_container()` | A :class:`TestContainer` with relaxed validation. |
| `identity_factory` | `aquilia/testing/fixtures.py` | `def identity_factory()` | A :class:`TestIdentityFactory` for creating test identities. |
| `mail_outbox` | `aquilia/testing/fixtures.py` | `def mail_outbox()` | Clear the mail outbox before the test and return it. |
| `test_request` | `aquilia/testing/fixtures.py` | `def test_request()` | Factory fixture -- call with kwargs to create test requests. |
| `test_scope` | `aquilia/testing/fixtures.py` | `def test_scope()` | Factory fixture -- call with kwargs to create ASGI scopes. |
| `test_server` | `aquilia/testing/fixtures.py` | `async def test_server()` | Async fixture providing a booted :class:`TestServer`. |
| `test_client` | `aquilia/testing/fixtures.py` | `async def test_client(test_server)` | Async fixture providing a :class:`TestClient` wired to a :class:`TestServer`. |
| `ws_client` | `aquilia/testing/fixtures.py` | `async def ws_client(test_server)` | Async fixture providing a :class:`WebSocketTestClient` wired to a :class:`TestServer`. |
| `settings_override` | `aquilia/testing/fixtures.py` | `def settings_override()` | Fixture factory for overriding settings. |
| `get_outbox` | `aquilia/testing/mail.py` | `def get_outbox() -> list[CapturedMail]` | Return the global mail outbox. |
| `clear_outbox` | `aquilia/testing/mail.py` | `def clear_outbox() -> None` | Clear the global mail outbox. |
| `capture_mail` | `aquilia/testing/mail.py` | `def capture_mail(to: list[str], subject: str, body: str = '', **kwargs: Any) -> CapturedMail` | Add a message to the outbox (called by the test mail provider). |
| `create_test_server` | `aquilia/testing/server.py` | `def create_test_server(*manifests: AppManifest, config_overrides: dict[str, Any] &#124; None = None, **kwargs: Any) -> TestServer` | Shortcut to create a :class:`TestServer`. |
| `make_test_scope` | `aquilia/testing/utils.py` | `def make_test_scope(method: str = 'GET', path: str = '/', query_string: str = '', headers: list[tuple] &#124; None = None, scheme: str = 'http', client: tuple &#124; None = None, server: tuple &#124; None = None, root_path: str = '', http_version: str = '1.1', scope_type: str = 'http') -> dict` | Build a minimal ASGI HTTP scope for testing. |
| `make_test_receive` | `aquilia/testing/utils.py` | `def make_test_receive(body: bytes = b'', *, chunks: list[bytes] &#124; None = None)` | Create an ASGI receive callable. |
| `make_test_request` | `aquilia/testing/utils.py` | `def make_test_request(method: str = 'GET', path: str = '/', query_string: str = '', headers: list[tuple] &#124; None = None, body: bytes = b'', scheme: str = 'http', client: tuple &#124; None = None, json: Any = None, form_data: dict[str, str] &#124; None = None, **kwargs: Any) -> Request` | Build a full :class:`~aquilia.request.Request` for testing. |
| `make_test_response` | `aquilia/testing/utils.py` | `def make_test_response(content: bytes &#124; str &#124; dict &#124; list = b'', status: int = 200, headers: dict[str, str] &#124; None = None, media_type: str &#124; None = None) -> Response` | Build a :class:`~aquilia.response.Response` for assertion helpers. |
| `make_test_ws_scope` | `aquilia/testing/utils.py` | `def make_test_ws_scope(path: str = '/ws', headers: list[tuple] &#124; None = None, subprotocols: list[str] &#124; None = None, query_string: str = '', client: tuple &#124; None = None, server: tuple &#124; None = None) -> dict` | Build an ASGI WebSocket scope for testing. |
| `make_upload_file` | `aquilia/testing/utils.py` | `def make_upload_file(filename: str, content: bytes &#124; str, content_type: str = 'application/octet-stream') -> tuple` | Create a file tuple suitable for :class:`TestClient` upload. |

## Constants

| Name | Source | Value or type |
| --- | --- | --- |
| `_SENTINEL` | `aquilia/testing/config.py` | `object()` |
| `T` | `aquilia/testing/di.py` | `TypeVar('T')` |
