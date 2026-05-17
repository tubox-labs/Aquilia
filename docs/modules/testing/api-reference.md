# Testing API Reference

This page is generated from the current Python source using the AST. It lists public classes, public methods, public module-level functions, constants, exports, and source files.

## Source Inventory

| File | Lines | Classes | Functions | Purpose |
| --- | ---: | ---: | ---: | --- |
| `aquilia/testing/__init__.py` | 117 | 0 | 0 | Aquilia Testing Framework. |
| `aquilia/testing/assertions.py` | 442 | 1 | 0 | Aquilia Testing - Custom Assertion Helpers. |
| `aquilia/testing/auth.py` | 290 | 3 | 0 | Aquilia Testing - Auth & Identity Helpers. |
| `aquilia/testing/cache.py` | 221 | 2 | 0 | Aquilia Testing - Cache Testing Utilities. |
| `aquilia/testing/cases.py` | 274 | 4 | 0 | Aquilia Testing - Test Case Base Classes. |
| `aquilia/testing/client.py` | 606 | 3 | 0 | Aquilia Testing - HTTP & WebSocket Test Client. |
| `aquilia/testing/config.py` | 299 | 2 | 2 | Aquilia Testing - Config Override Utilities. |
| `aquilia/testing/di.py` | 290 | 1 | 4 | Aquilia Testing - DI Container Testing Utilities. |
| `aquilia/testing/effects.py` | 258 | 4 | 0 | Aquilia Testing - Effect System Testing Utilities. |
| `aquilia/testing/faults.py` | 167 | 2 | 0 | Aquilia Testing - Fault Testing Utilities. |
| `aquilia/testing/fixtures.py` | 212 | 0 | 14 | Aquilia Testing - Pytest Fixtures. |
| `aquilia/testing/mail.py` | 168 | 2 | 3 | Aquilia Testing - Mail Testing Utilities. |
| `aquilia/testing/server.py` | 267 | 1 | 1 | Aquilia Testing - TestServer Factory. |
| `aquilia/testing/utils.py` | 263 | 0 | 6 | Aquilia Testing - Request/Response Utility Factories. |

## Public Exports

`AquiliaAssertions`, `AquiliaTestCase`, `AuthTestMixin`, `CacheTestMixin`, `CapturedFault`, `CapturedMail`, `EffectCall`, `IdentityBuilder`, `LiveServerTestCase`, `MailTestMixin`, `MockCacheBackend`, `MockEffectProvider`, `MockEffectRegistry`, `MockFaultEngine`, `SimpleTestCase`, `TestClient`, `TestConfig`, `TestContainer`, `TestIdentityFactory`, `TestServer`, `TransactionTestCase`, `WebSocketTestClient`, `aquilia_fixtures`, `create_test_server`, `factory_provider`, `make_test_receive`, `make_test_request`, `make_test_response`, `make_test_scope`, `make_test_ws_scope`, `make_upload_file`, `mock_provider`, `override_provider`, `override_settings`, `spy_provider`

## Public Class Summary

| Class | Source | Bases | Summary |
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
| `MockFaultEngine` | `aquilia/testing/faults.py` | object | Drop-in replacement for :class:`~aquilia.faults.engine.FaultEngine` that captures faults instead of dispatching them. |
| `CapturedMail` | `aquilia/testing/mail.py` | object | A mail message captured during testing. |
| `MailTestMixin` | `aquilia/testing/mail.py` | object | Mixin providing mail assertion helpers. |
| `TestServer` | `aquilia/testing/server.py` | object | Lightweight test server wrapping :class:`AquiliaServer`. |

## Public Function Summary

| Function | Source | Signature | Summary |
| --- | --- | --- | --- |
| `set_active_config` | `aquilia/testing/config.py` | `def set_active_config(cfg: ConfigLoader)` | Register the config loader used by the running test server. |
| `get_active_config` | `aquilia/testing/config.py` | `def get_active_config()` | Return the active config loader. |
| `mock_provider` | `aquilia/testing/di.py` | `def mock_provider(token: type[T] \| str, value: T, scope: str='singleton')` | Create a mock DI provider that always returns *value*. |
| `factory_provider` | `aquilia/testing/di.py` | `def factory_provider(token: type[T] \| str, factory: Callable[..., T], scope: str='transient')` | Create a factory DI provider that calls *factory* on each resolve. |
| `override_provider` | `aquilia/testing/di.py` | `async def override_provider(container: Container, token: type[T] \| str, mock_value: T, *, tag: str \| None=None)` | Temporarily override a provider in a container. |
| `spy_provider` | `aquilia/testing/di.py` | `async def spy_provider(container: Container, token: type[T] \| str, *, tag: str \| None=None)` | Wrap an existing provider with a spy that tracks calls. |
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
| `get_outbox` | `aquilia/testing/mail.py` | `def get_outbox()` | Return the global mail outbox. |
| `clear_outbox` | `aquilia/testing/mail.py` | `def clear_outbox()` | Clear the global mail outbox. |
| `capture_mail` | `aquilia/testing/mail.py` | `def capture_mail(to: list[str], subject: str, body: str='', **kwargs: Any)` | Add a message to the outbox (called by the test mail provider). |
| `create_test_server` | `aquilia/testing/server.py` | `def create_test_server(*manifests: AppManifest, config_overrides: dict[str, Any] \| None=None, **kwargs: Any)` | Shortcut to create a :class:`TestServer`. |
| `make_test_scope` | `aquilia/testing/utils.py` | `def make_test_scope(method: str='GET', path: str='/', query_string: str='', headers: list[tuple] \| None=None, scheme: str='http', client: tuple \| None=None, server: tuple \| None=None, root_path: str='', http_version: str='1.1', scope_type: str='http')` | Build a minimal ASGI HTTP scope for testing. |
| `make_test_receive` | `aquilia/testing/utils.py` | `def make_test_receive(body: bytes=b'', *, chunks: list[bytes] \| None=None)` | Create an ASGI receive callable. |
| `make_test_request` | `aquilia/testing/utils.py` | `def make_test_request(method: str='GET', path: str='/', query_string: str='', headers: list[tuple] \| None=None, body: bytes=b'', scheme: str='http', client: tuple \| None=None, json: Any=None, form_data: dict[str, str] \| None=None, **kwargs: Any)` | Build a full :class:`~aquilia.request.Request` for testing. |
| `make_test_response` | `aquilia/testing/utils.py` | `def make_test_response(content: bytes \| str \| dict \| list=b'', status: int=200, headers: dict[str, str] \| None=None, media_type: str \| None=None)` | Build a :class:`~aquilia.response.Response` for assertion helpers. |
| `make_test_ws_scope` | `aquilia/testing/utils.py` | `def make_test_ws_scope(path: str='/ws', headers: list[tuple] \| None=None, subprotocols: list[str] \| None=None, query_string: str='', client: tuple \| None=None, server: tuple \| None=None)` | Build an ASGI WebSocket scope for testing. |
| `make_upload_file` | `aquilia/testing/utils.py` | `def make_upload_file(filename: str, content: bytes \| str, content_type: str='application/octet-stream')` | Create a file tuple suitable for :class:`TestClient` upload. |

## Constants And Module Flags

| Name | Source | Value or Type |
| --- | --- | --- |
| `_SENTINEL` | `aquilia/testing/config.py` | `object()` |
| `T` | `aquilia/testing/di.py` | `TypeVar('T')` |

## Detailed Classes And Methods

### `AquiliaAssertions`

- Source: `aquilia/testing/assertions.py`
- Bases: `object`
- Summary: Mixin class providing Aquilia-specific assertion methods.

Methods:

| Method | Signature | Summary |
| --- | --- | --- |
| `assert_status` | `def assert_status(self, response, expected: int, msg: str='')` | Assert HTTP status code. |
| `assert_status_in_range` | `def assert_status_in_range(self, response, low: int, high: int, msg: str='')` | Assert status code is within [low, high) range. |
| `assert_success` | `def assert_success(self, response, msg: str='')` | Assert 2xx status. |
| `assert_created` | `def assert_created(self, response, msg: str='')` | Assert 201 Created. |
| `assert_accepted` | `def assert_accepted(self, response, msg: str='')` | Assert 202 Accepted. |
| `assert_no_content` | `def assert_no_content(self, response, msg: str='')` | Assert 204 No Content. |
| `assert_redirect` | `def assert_redirect(self, response, location: str \| None=None, msg: str='')` | Assert 3xx redirect, optionally checking Location header. |
| `assert_permanent_redirect` | `def assert_permanent_redirect(self, response, location: str \| None=None, msg: str='')` | Assert 301 Moved Permanently. |
| `assert_bad_request` | `def assert_bad_request(self, response, msg: str='')` | Assert 400. |
| `assert_unauthorized` | `def assert_unauthorized(self, response, msg: str='')` | Assert 401. |
| `assert_forbidden` | `def assert_forbidden(self, response, msg: str='')` | Assert 403. |
| `assert_not_found` | `def assert_not_found(self, response, msg: str='')` | Assert 404. |
| `assert_method_not_allowed` | `def assert_method_not_allowed(self, response, msg: str='')` | Assert 405 Method Not Allowed. |
| `assert_conflict` | `def assert_conflict(self, response, msg: str='')` | Assert 409 Conflict. |
| `assert_gone` | `def assert_gone(self, response, msg: str='')` | Assert 410 Gone. |
| `assert_unprocessable` | `def assert_unprocessable(self, response, msg: str='')` | Assert 422 Unprocessable Entity. |
| `assert_too_many_requests` | `def assert_too_many_requests(self, response, msg: str='')` | Assert 429 Too Many Requests. |
| `assert_server_error` | `def assert_server_error(self, response, msg: str='')` | Assert 500 Internal Server Error. |
| `assert_service_unavailable` | `def assert_service_unavailable(self, response, msg: str='')` | Assert 503 Service Unavailable. |
| `assert_json` | `def assert_json(self, response, expected: Any=None, msg: str='')` | Assert response is JSON, optionally matching expected value. |
| `assert_json_contains` | `def assert_json_contains(self, response, subset: dict[str, Any], msg: str='')` | Assert JSON body contains all keys/values from *subset*. |
| `assert_json_key` | `def assert_json_key(self, response, key: str, msg: str='')` | Assert JSON body contains a specific key. |
| `assert_json_path` | `def assert_json_path(self, response, path: str, expected: Any=_sentinel, msg: str='')` | Assert a deeply nested JSON value using dot-notation. |
| `assert_json_list` | `def assert_json_list(self, response, min_length: int \| None=None, msg: str='')` | Assert JSON body is a list, optionally with minimum length. |
| `assert_json_length` | `def assert_json_length(self, response, expected: int, msg: str='')` | Assert JSON list/dict has exactly *expected* items/keys. |
| `assert_json_not_empty` | `def assert_json_not_empty(self, response, msg: str='')` | Assert JSON body is non-empty (non-null, non-empty list/dict). |
| `assert_html` | `def assert_html(self, response, msg: str='')` | Assert response is HTML. |
| `assert_content_type` | `def assert_content_type(self, response, expected: str, msg: str='')` | Assert exact content type. |
| `assert_header` | `def assert_header(self, response, name: str, value: str \| None=None, msg: str='')` | Assert response header exists (and optionally matches value). |
| `assert_header_contains` | `def assert_header_contains(self, response, name: str, substring: str, msg: str='')` | Assert response header value contains a substring. |
| `assert_no_header` | `def assert_no_header(self, response, name: str, msg: str='')` | Assert response header does NOT exist. |
| `assert_content_length` | `def assert_content_length(self, response, expected: int \| None=None, msg: str='')` | Assert Content-Length header exists (and optionally matches). |
| `assert_cookie` | `def assert_cookie(self, response, name: str, msg: str='')` | Assert Set-Cookie header contains the named cookie. |
| `assert_cookie_value` | `def assert_cookie_value(self, response, name: str, expected: str, msg: str='')` | Assert a cookie's value in Set-Cookie header. |
| `assert_no_cookie` | `def assert_no_cookie(self, response, name: str, msg: str='')` | Assert Set-Cookie does NOT contain the named cookie. |
| `assert_body_contains` | `def assert_body_contains(self, response, text: str, msg: str='')` | Assert text body contains substring. |
| `assert_body_not_contains` | `def assert_body_not_contains(self, response, text: str, msg: str='')` | Assert text body does NOT contain substring. |
| `assert_body_empty` | `def assert_body_empty(self, response, msg: str='')` | Assert response body is empty. |
| `assert_fault_raised` | `def assert_fault_raised(self, fault_engine_or_captured: Any, code: str \| None=None, domain: str \| None=None, msg: str='')` | Assert that a fault was emitted / captured. |
| `assert_no_faults` | `def assert_no_faults(self, fault_engine_or_captured: Any, msg: str='')` | Assert no faults were captured. |
| `assert_fault_count` | `def assert_fault_count(self, fault_engine_or_captured: Any, expected: int, msg: str='')` | Assert exact number of faults captured. |
| `assert_fault_severity` | `def assert_fault_severity(self, fault_engine_or_captured: Any, severity: Any, code: str \| None=None, msg: str='')` | Assert fault(s) have the expected severity. |
| `assert_registered` | `def assert_registered(self, container, token: Any, msg: str='')` | Assert a service is registered in the DI container. |
| `assert_not_registered` | `def assert_not_registered(self, container, token: Any, msg: str='')` | Assert a service is NOT registered in the DI container. |
| `assert_resolves` | `def assert_resolves(self, container, token: Any, msg: str='')` | Assert a service resolves successfully (sync). |
| `assert_resolves_async` | `async def assert_resolves_async(self, container, token: Any, msg: str='')` | Assert a service resolves successfully (async). |
| `assert_effect_acquired` | `def assert_effect_acquired(self, provider: Any, count: int \| None=None, msg: str='')` | Assert an effect provider's acquire was called. |
| `assert_effect_released` | `def assert_effect_released(self, provider: Any, count: int \| None=None, msg: str='')` | Assert an effect provider's release was called. |
| `assert_cache_hit` | `async def assert_cache_hit(self, cache: Any, key: str, expected: Any=_sentinel, msg: str='')` | Assert a cache key exists (and optionally matches value). |
| `assert_cache_miss` | `async def assert_cache_miss(self, cache: Any, key: str, msg: str='')` | Assert a cache key does NOT exist. |
| `assert_mail_count` | `def assert_mail_count(self, outbox: Any, expected: int, msg: str='')` | Assert exact number of messages in the mail outbox. |
| `assert_mail_to` | `def assert_mail_to(self, outbox: Any, address: str, msg: str='')` | Assert at least one message was sent to *address*. |
| `assert_mail_from` | `def assert_mail_from(self, outbox: Any, address: str, msg: str='')` | Assert at least one message was sent from *address*. |

### `TestIdentityFactory`

- Source: `aquilia/testing/auth.py`
- Bases: `object`
- Summary: Factory for creating test identities with sensible defaults.

Methods:

| Method | Signature | Summary |
| --- | --- | --- |
| `user` | `def user(cls, id: str \| None=None, email: str \| None=None, name: str \| None=None, roles: list[str] \| None=None, scopes: list[str] \| None=None, status: IdentityStatus=IdentityStatus.ACTIVE, tenant_id: str \| None=None, **extra_attrs: Any)` | Create a regular user identity. |
| `admin` | `def admin(cls, id: str \| None=None, **kw)` | Create an admin identity. |
| `service` | `def service(cls, id: str \| None=None, scopes: list[str] \| None=None, **kw)` | Create a service/API-key identity. |
| `anonymous` | `def anonymous(cls)` | Create an anonymous (unauthenticated) identity. |
| `suspended` | `def suspended(cls, id: str \| None=None, **kw)` | Create a suspended user identity. |
| `build` | `def build(cls, id: str \| None=None)` | Start building an identity with the fluent API. |

### `IdentityBuilder`

- Source: `aquilia/testing/auth.py`
- Bases: `object`
- Summary: Fluent builder for constructing test identities.

Methods:

| Method | Signature | Summary |
| --- | --- | --- |
| `with_roles` | `def with_roles(self, *roles: str)` |  |
| `with_scopes` | `def with_scopes(self, *scopes: str)` |  |
| `with_email` | `def with_email(self, email: str)` |  |
| `with_name` | `def with_name(self, name: str)` |  |
| `with_tenant` | `def with_tenant(self, tenant_id: str)` |  |
| `with_status` | `def with_status(self, status: IdentityStatus)` |  |
| `with_type` | `def with_type(self, type: IdentityType)` |  |
| `with_attr` | `def with_attr(self, key: str, value: Any)` |  |
| `as_service` | `def as_service(self)` |  |
| `as_suspended` | `def as_suspended(self)` |  |
| `create` | `def create(self)` | Build and return the Identity. |

### `AuthTestMixin`

- Source: `aquilia/testing/auth.py`
- Bases: `object`
- Summary: Mixin providing authentication helpers for test cases.

Methods:

| Method | Signature | Summary |
| --- | --- | --- |
| `force_login` | `def force_login(self, identity: Identity)` | Bypass the normal auth flow and inject an identity into the test client so subsequent requests appear authenticated. |
| `force_logout` | `def force_logout(self)` | Remove any forced authentication. |
| `current_identity` | `def current_identity(self)` | Return the currently forced identity (or None). |
| `is_authenticated` | `def is_authenticated(self)` | Check if a test identity is currently forced. |
| `authenticate_as` | `async def authenticate_as(self, identity: Identity)` | Authenticate by injecting the identity into the DI container. |
| `login_as_admin` | `def login_as_admin(self, id: str \| None=None, **kw)` | Convenience: create admin identity and force login. |
| `login_as_user` | `def login_as_user(self, id: str \| None=None, **kw)` | Convenience: create user identity and force login. |

### `MockCacheBackend`

- Source: `aquilia/testing/cache.py`
- Bases: `object`
- Summary: In-memory cache backend for testing with TTL tracking.

Methods:

| Method | Signature | Summary |
| --- | --- | --- |
| `get_ttl` | `def get_ttl(self, key: str)` | Return remaining TTL in seconds, or None if no TTL set. |
| `connect` | `async def connect(self)` |  |
| `disconnect` | `async def disconnect(self)` |  |
| `get` | `async def get(self, key: str)` |  |
| `set` | `async def set(self, key: str, value: Any, ttl: int \| None=None)` |  |
| `get_or_set` | `async def get_or_set(self, key: str, default: Any, ttl: int \| None=None)` | Get existing value or set & return default. |
| `delete` | `async def delete(self, key: str)` |  |
| `exists` | `async def exists(self, key: str)` |  |
| `clear` | `async def clear(self)` |  |
| `keys` | `async def keys(self, pattern: str='*')` |  |
| `increment` | `async def increment(self, key: str, delta: int=1)` | Increment a numeric cache value. |
| `decrement` | `async def decrement(self, key: str, delta: int=1)` | Decrement a numeric cache value. |
| `mget` | `async def mget(self, *keys: str)` | Get multiple values at once. |
| `mset` | `async def mset(self, mapping: dict[str, Any], ttl: int \| None=None)` | Set multiple values at once. |
| `health_check` | `async def health_check(self)` |  |
| `store` | `def store(self)` | Direct access to the underlying store for assertions. |
| `size` | `def size(self)` | Number of keys currently in the store. |
| `reset` | `def reset(self)` | Clear store, TTLs, and counters. |

### `CacheTestMixin`

- Source: `aquilia/testing/cache.py`
- Bases: `object`
- Summary: Mixin providing cache-specific test helpers.

Methods:

| Method | Signature | Summary |
| --- | --- | --- |
| `assert_cached` | `async def assert_cached(self, key: str, msg: str='')` | Assert a key is present in the cache. |
| `assert_not_cached` | `async def assert_not_cached(self, key: str, msg: str='')` | Assert a key is NOT present in the cache. |
| `assert_cache_value` | `async def assert_cache_value(self, key: str, expected: Any, msg: str='')` | Assert a cached key equals an expected value. |
| `assert_cache_count` | `async def assert_cache_count(self, expected: int, pattern: str='*', msg: str='')` | Assert the number of keys in the cache. |
| `populate_cache` | `async def populate_cache(self, data: dict[str, Any], ttl: int \| None=None)` | Bulk-populate cache entries. |
| `flush_cache` | `async def flush_cache(self)` | Clear the entire cache. |

### `SimpleTestCase`

- Source: `aquilia/testing/cases.py`
- Bases: `unittest.TestCase, AquiliaAssertions`
- Summary: Test case that does NOT start a server.

### `AquiliaTestCase`

- Source: `aquilia/testing/cases.py`
- Bases: `unittest.IsolatedAsyncioTestCase, AquiliaAssertions`
- Summary: Full-featured async test case with integrated server lifecycle.

Fields and class attributes:

| Name | Type | Default / Value |
| --- | --- | --- |
| `manifests` | `list[AppManifest]` | `[]` |
| `settings` | `dict[str, Any]` | `{}` |
| `enable_cache` | `bool` | `False` |
| `enable_sessions` | `bool` | `False` |
| `enable_auth` | `bool` | `False` |
| `enable_mail` | `bool` | `False` |
| `enable_templates` | `bool` | `False` |
| `server` | `TestServer` | `` |
| `client` | `TestClient` | `` |

Methods:

| Method | Signature | Summary |
| --- | --- | --- |
| `asyncSetUp` | `async def asyncSetUp(self)` | Boot the test server and create a client. |
| `asyncTearDown` | `async def asyncTearDown(self)` | Shutdown the test server. |
| `di_container` | `def di_container(self)` |  |
| `fault_engine` | `def fault_engine(self)` |  |
| `config` | `def config(self)` |  |
| `controller_router` | `def controller_router(self)` |  |
| `effect_registry` | `def effect_registry(self)` |  |
| `cache_service` | `def cache_service(self)` |  |
| `get_url` | `def get_url(self, route_name: str, **params: str)` | Reverse a named route to its URL. |
| `login` | `async def login(self, username: str='test@test.com', password: str='password')` | Convenience login helper. |

### `TransactionTestCase`

- Source: `aquilia/testing/cases.py`
- Bases: `AquiliaTestCase`
- Summary: Test case that wraps each test in a database transaction.

Methods:

| Method | Signature | Summary |
| --- | --- | --- |
| `asyncSetUp` | `async def asyncSetUp(self)` |  |
| `asyncTearDown` | `async def asyncTearDown(self)` |  |

### `LiveServerTestCase`

- Source: `aquilia/testing/cases.py`
- Bases: `AquiliaTestCase`
- Summary: Test case that starts a real ASGI server on a random port.

Fields and class attributes:

| Name | Type | Default / Value |
| --- | --- | --- |
| `host` | `str` | `'127.0.0.1'` |
| `port` | `int` | `0` |
| `live_server_url` | `str` | `''` |

Methods:

| Method | Signature | Summary |
| --- | --- | --- |
| `asyncSetUp` | `async def asyncSetUp(self)` |  |
| `asyncTearDown` | `async def asyncTearDown(self)` |  |

### `TestResponse`

- Source: `aquilia/testing/client.py`
- Bases: `object`
- Summary: Wrapper around captured ASGI response events.

Methods:

| Method | Signature | Summary |
| --- | --- | --- |
| `text` | `def text(self)` | Body decoded as text. |
| `json` | `def json(self)` | Parse body as JSON. |
| `is_success` | `def is_success(self)` |  |
| `is_redirect` | `def is_redirect(self)` |  |
| `is_client_error` | `def is_client_error(self)` |  |
| `is_server_error` | `def is_server_error(self)` |  |
| `content_length` | `def content_length(self)` | Return Content-Length as int, or None. |
| `location` | `def location(self)` | Return Location header (useful for redirects). |
| `header` | `def header(self, name: str, default: str \| None=None)` |  |
| `has_header` | `def has_header(self, name: str)` | Check if header exists. |

### `TestClient`

- Source: `aquilia/testing/client.py`
- Bases: `object`
- Summary: In-process ASGI test client for Aquilia.

Fields and class attributes:

| Name | Type | Default / Value |
| --- | --- | --- |
| `MAX_REDIRECTS` | `` | `20` |

Methods:

| Method | Signature | Summary |
| --- | --- | --- |
| `set_bearer_token` | `def set_bearer_token(self, token: str)` | Set Authorization: Bearer <token> header for all requests. |
| `clear_auth` | `def clear_auth(self)` | Remove Authorization header. |
| `history` | `def history(self)` | Redirect chain history from the last request. |
| `get` | `async def get(self, path: str, **kw)` |  |
| `post` | `async def post(self, path: str, json: Any=None, data: dict[str, str] \| None=None, body: bytes=b'', files: dict[str, Any] \| None=None, **kw)` |  |
| `put` | `async def put(self, path: str, json: Any=None, body: bytes=b'', files: dict[str, Any] \| None=None, **kw)` |  |
| `patch` | `async def patch(self, path: str, json: Any=None, body: bytes=b'', files: dict[str, Any] \| None=None, **kw)` |  |
| `delete` | `async def delete(self, path: str, **kw)` |  |
| `head` | `async def head(self, path: str, **kw)` |  |
| `options` | `async def options(self, path: str, **kw)` |  |
| `set_cookie` | `def set_cookie(self, name: str, value: str)` |  |
| `delete_cookie` | `def delete_cookie(self, name: str)` | Remove a specific cookie. |
| `clear_cookies` | `def clear_cookies(self)` |  |
| `cookies` | `def cookies(self)` | Read-only view of the cookie jar. |

### `WebSocketTestClient`

- Source: `aquilia/testing/client.py`
- Bases: `object`
- Summary: In-process WebSocket test client.

Methods:

| Method | Signature | Summary |
| --- | --- | --- |
| `connect` | `async def connect(self, path: str='/ws', headers: list[tuple] \| None=None, subprotocols: list[str] \| None=None)` | Initiate WebSocket handshake. |
| `send_text` | `async def send_text(self, text: str)` |  |
| `send_json` | `async def send_json(self, data: Any)` |  |
| `send_bytes` | `async def send_bytes(self, data: bytes)` |  |
| `receive` | `async def receive(self, timeout: float=5.0)` |  |
| `receive_text` | `async def receive_text(self, timeout: float=5.0)` |  |
| `receive_json` | `async def receive_json(self, timeout: float=5.0)` |  |
| `receive_bytes` | `async def receive_bytes(self, timeout: float=5.0)` | Receive binary data from the WebSocket. |
| `is_connected` | `def is_connected(self)` | Whether the WebSocket is currently connected. |
| `close` | `async def close(self, code: int=1000)` |  |

### `TestConfig`

- Source: `aquilia/testing/config.py`
- Bases: `object`
- Summary: Lightweight config wrapper for test overrides.

Methods:

| Method | Signature | Summary |
| --- | --- | --- |
| `get` | `def get(self, key: str, default: Any=None)` | Retrieve a config value using dot-notation. |
| `set` | `def set(self, key: str, value: Any)` | Set a config value using dot-notation (mutates overrides). |
| `has` | `def has(self, key: str)` | Check if a config key exists. |
| `keys` | `def keys(self)` | Return top-level config keys. |
| `config_data` | `def config_data(self)` | Return merged config dict (compatible with ConfigLoader). |
| `to_dict` | `def to_dict(self)` | Return merged config as a plain dictionary. |
| `get_cache_config` | `def get_cache_config(self)` |  |
| `get_session_config` | `def get_session_config(self)` |  |
| `get_auth_config` | `def get_auth_config(self)` |  |
| `get_mail_config` | `def get_mail_config(self)` |  |
| `get_template_config` | `def get_template_config(self)` |  |

### `override_settings`

- Source: `aquilia/testing/config.py`
- Bases: `object`
- Summary: Temporarily override Aquilia config values.

### `TestContainer`

- Source: `aquilia/testing/di.py`
- Bases: `Container`
- Summary: A :class:`Container` subclass tailored for testing.

Methods:

| Method | Signature | Summary |
| --- | --- | --- |
| `register` | `def register(self, provider: Provider, tag: str \| None=None)` | Register, silently overwriting duplicates. |
| `register_value` | `def register_value(self, token: type \| str, value: Any, scope: str='singleton', tag: str \| None=None)` | Shortcut: register a fixed value provider. |
| `register_factory` | `def register_factory(self, token: type \| str, factory: Callable[..., Any], scope: str='transient', tag: str \| None=None)` | Shortcut: register a factory provider. |
| `resolve` | `def resolve(self, token, *, tag=None, optional=False)` |  |
| `reset` | `def reset(self)` | Clear cache and resolution log. |

### `EffectCall`

- Source: `aquilia/testing/effects.py`
- Bases: `object`
- Summary: Record of an acquire or release call on a MockEffectProvider.
- Decorators: `dataclass`

Fields and class attributes:

| Name | Type | Default / Value |
| --- | --- | --- |
| `action` | `str` | `` |
| `mode` | `str \| None` | `None` |
| `resource` | `Any` | `None` |
| `success` | `bool \| None` | `None` |
| `timestamp` | `float` | `0.0` |

### `MockEffectProvider`

- Source: `aquilia/testing/effects.py`
- Bases: `EffectProvider`
- Summary: Stub provider that returns configurable values.

Methods:

| Method | Signature | Summary |
| --- | --- | --- |
| `initialize` | `async def initialize(self)` |  |
| `acquire` | `async def acquire(self, mode: str \| None=None)` |  |
| `release` | `async def release(self, resource: Any, success: bool=True)` |  |
| `finalize` | `async def finalize(self)` |  |
| `last_acquired_mode` | `def last_acquired_mode(self)` | Return the mode from the last acquire call. |
| `reset` | `def reset(self)` | Reset all tracking counters. |

### `MockEffectRegistry`

- Source: `aquilia/testing/effects.py`
- Bases: `EffectRegistry`
- Summary: Test-friendly :class:`EffectRegistry` that auto-stubs missing effects.

Methods:

| Method | Signature | Summary |
| --- | --- | --- |
| `register_mock` | `def register_mock(self, effect_name: str, return_value: Any=None, **kw)` | Register a mock provider for the given effect name. |
| `get_provider` | `def get_provider(self, effect_name: str)` | Return the provider – auto-creating a mock if not registered. |
| `get_mock` | `def get_mock(self, effect_name: str)` | Retrieve the underlying mock (or ``None``). |
| `reset_all` | `def reset_all(self)` | Reset tracking on all mock providers. |

### `MockFlowContext`

- Source: `aquilia/testing/effects.py`
- Bases: `object`
- Summary: Test-friendly FlowContext for testing pipeline nodes and handlers.

Methods:

| Method | Signature | Summary |
| --- | --- | --- |
| `from_registry` | `def from_registry(registry: MockEffectRegistry, *, request: Any=None, container: Any=None, identity: Any=None, session: Any=None, state: dict[str, Any] \| None=None)` | Create a FlowContext with pre-acquired mock effects. |
| `create` | `def create(*, effects: dict[str, Any] \| None=None, request: Any=None, container: Any=None, identity: Any=None, session: Any=None, state: dict[str, Any] \| None=None)` | Create a FlowContext with manually specified effect values. |

### `CapturedFault`

- Source: `aquilia/testing/faults.py`
- Bases: `object`
- Summary: A fault captured by :class:`MockFaultEngine`.
- Decorators: `dataclass`

Fields and class attributes:

| Name | Type | Default / Value |
| --- | --- | --- |
| `fault` | `Fault` | `` |
| `domain` | `str \| None` | `None` |
| `app_name` | `str \| None` | `None` |
| `handler_name` | `str \| None` | `None` |
| `timestamp` | `float` | `0.0` |

Methods:

| Method | Signature | Summary |
| --- | --- | --- |
| `code` | `def code(self)` |  |
| `message` | `def message(self)` |  |
| `severity` | `def severity(self)` |  |

### `MockFaultEngine`

- Source: `aquilia/testing/faults.py`
- Bases: `object`
- Summary: Drop-in replacement for :class:`~aquilia.faults.engine.FaultEngine` that captures faults instead of dispatching them.

Methods:

| Method | Signature | Summary |
| --- | --- | --- |
| `emit` | `def emit(self, fault: Fault, *, app_name: str \| None=None, handler_name: str \| None=None, **context: Any)` | Capture a fault emission. |
| `raise_fault` | `def raise_fault(self, fault: Fault, **kw)` | Alias used by some subsystems. |
| `register_app` | `def register_app(self, app_name: str, handler: Any=None)` |  |
| `register_handler` | `def register_handler(self, domain: str, handler: Any)` |  |
| `has_fault` | `def has_fault(self, code: str)` | Check if a fault with the given code was captured. |
| `get_faults` | `def get_faults(self, code: str \| None=None, domain: str \| None=None, severity: Severity \| None=None)` | Filter captured faults by code, domain, and/or severity. |
| `fault_codes` | `def fault_codes(self)` |  |
| `fault_count` | `def fault_count(self)` |  |
| `last_fault` | `def last_fault(self)` | Return the most recently captured fault, or ``None``. |
| `last_fault_code` | `def last_fault_code(self)` | Return the code of the most recently captured fault. |
| `has_fault_with_severity` | `def has_fault_with_severity(self, severity: Severity)` | Check if any fault with given severity was captured. |
| `reset` | `def reset(self)` | Clear all captured faults. |

### `CapturedMail`

- Source: `aquilia/testing/mail.py`
- Bases: `object`
- Summary: A mail message captured during testing.
- Decorators: `dataclass`

Fields and class attributes:

| Name | Type | Default / Value |
| --- | --- | --- |
| `to` | `list[str]` | `` |
| `subject` | `str` | `` |
| `body` | `str` | `''` |
| `html_body` | `str` | `''` |
| `from_email` | `str` | `''` |
| `cc` | `list[str]` | `field(default_factory=list)` |
| `bcc` | `list[str]` | `field(default_factory=list)` |
| `reply_to` | `str \| None` | `None` |
| `attachments` | `list[dict[str, Any]]` | `field(default_factory=list)` |
| `headers` | `dict[str, str]` | `field(default_factory=dict)` |
| `provider` | `str` | `''` |
| `template_name` | `str \| None` | `None` |

### `MailTestMixin`

- Source: `aquilia/testing/mail.py`
- Bases: `object`
- Summary: Mixin providing mail assertion helpers.

Methods:

| Method | Signature | Summary |
| --- | --- | --- |
| `setUp` | `def setUp(self)` |  |
| `mail_outbox` | `def mail_outbox(self)` | All captured mail messages. |
| `latest_mail` | `def latest_mail(self)` | Return the most recently sent mail, or None. |
| `get_mail_for` | `def get_mail_for(self, address: str)` | Return all mail sent to a specific address. |
| `assert_mail_sent` | `def assert_mail_sent(self, to: str \| None=None, count: int \| None=None, msg: str='')` | Assert that mail was sent. |
| `assert_no_mail_sent` | `def assert_no_mail_sent(self, msg: str='')` | Assert that no mail was sent. |
| `assert_mail_count` | `def assert_mail_count(self, expected: int, msg: str='')` | Assert exact number of messages in the outbox. |
| `assert_mail_to` | `def assert_mail_to(self, address: str, msg: str='')` | Assert at least one message was sent to *address*. |
| `assert_mail_from` | `def assert_mail_from(self, address: str, msg: str='')` | Assert at least one message was sent from *address*. |
| `assert_mail_subject_contains` | `def assert_mail_subject_contains(self, text: str, msg: str='')` | Assert at least one message has a subject containing *text*. |
| `assert_mail_body_contains` | `def assert_mail_body_contains(self, text: str, msg: str='')` | Assert at least one message has body containing *text*. |
| `assert_mail_has_attachment` | `def assert_mail_has_attachment(self, filename: str \| None=None, msg: str='')` | Assert at least one message has an attachment. |
| `assert_mail_cc` | `def assert_mail_cc(self, address: str, msg: str='')` | Assert at least one message has *address* in CC. |
| `assert_mail_bcc` | `def assert_mail_bcc(self, address: str, msg: str='')` | Assert at least one message has *address* in BCC. |

### `TestServer`

- Source: `aquilia/testing/server.py`
- Bases: `object`
- Summary: Lightweight test server wrapping :class:`AquiliaServer`.

Methods:

| Method | Signature | Summary |
| --- | --- | --- |
| `start` | `async def start(self)` | Boot the server (idempotent). |
| `stop` | `async def stop(self)` | Shutdown the server (idempotent). |
| `server` | `def server(self)` |  |
| `app` | `def app(self)` | ASGI application. |
| `config` | `def config(self)` |  |
| `is_running` | `def is_running(self)` | Whether the server is currently started. |
| `fault_engine` | `def fault_engine(self)` |  |
| `di_container` | `def di_container(self)` | Return the first available DI container. |
| `controller_router` | `def controller_router(self)` |  |
| `middleware_stack` | `def middleware_stack(self)` |  |
| `effect_registry` | `def effect_registry(self)` |  |
| `cache_service` | `def cache_service(self)` |  |
| `session_engine` | `def session_engine(self)` |  |
| `auth_manager` | `def auth_manager(self)` |  |
| `mail_provider` | `def mail_provider(self)` |  |
| `reload` | `async def reload(self)` | Restart the server (stop + start). |
| `get_url` | `def get_url(self, route_name: str, **params: str)` | Reverse a named route to its URL. |
