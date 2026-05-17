# testing Module

## Purpose

Aquilia test utilities and fixtures. Use this module for test clients, live servers, request builders, auth builders, cache and mail mixins, DI provider overrides, captured faults, and WebSocket test clients.

## Source Coverage

- Python files: 14
- Public classes: 25
- Dataclasses: 3
- Enums: 0
- Public functions: 30

## How It Fits In Aquilia

1. Import the package from `aquilia.testing` or its concrete submodules.
2. Configure it through workspace integrations, manifests, or direct service construction depending on the subsystem.
3. Keep business logic outside transport and framework glue so the subsystem stays testable.

## Practical Guidance

- Prefer typed configuration objects and framework helpers over ad hoc dictionaries when they exist.
- Use the tests in `tests/` as behavioral examples when changing this subsystem.

## Public Classes

| Name | Source | Role |
| --- | --- | --- |
| `AquiliaAssertions` | `aquilia/testing/assertions.py` | Mixin class providing Aquilia-specific assertion methods. |
| `TestIdentityFactory` | `aquilia/testing/auth.py` | Factory for creating test identities with sensible defaults. |
| `IdentityBuilder` | `aquilia/testing/auth.py` | Fluent builder for constructing test identities. |
| `AuthTestMixin` | `aquilia/testing/auth.py` | Mixin providing authentication helpers for test cases. |
| `MockCacheBackend` | `aquilia/testing/cache.py` | In-memory cache backend for testing with TTL tracking. |
| `CacheTestMixin` | `aquilia/testing/cache.py` | Mixin providing cache-specific test helpers. |
| `SimpleTestCase` | `aquilia/testing/cases.py` | Test case that does NOT start a server. |
| `AquiliaTestCase` | `aquilia/testing/cases.py` | Full-featured async test case with integrated server lifecycle. |
| `TransactionTestCase` | `aquilia/testing/cases.py` | Test case that wraps each test in a database transaction. |
| `LiveServerTestCase` | `aquilia/testing/cases.py` | Test case that starts a real ASGI server on a random port. |
| `TestResponse` | `aquilia/testing/client.py` | Wrapper around captured ASGI response events. |
| `TestClient` | `aquilia/testing/client.py` | In-process ASGI test client for Aquilia. |
| `WebSocketTestClient` | `aquilia/testing/client.py` | In-process WebSocket test client. |
| `TestConfig` | `aquilia/testing/config.py` | Lightweight config wrapper for test overrides. |
| `override_settings` | `aquilia/testing/config.py` | Temporarily override Aquilia config values. |
| `TestContainer` | `aquilia/testing/di.py` | A :class:`Container` subclass tailored for testing. |
| `EffectCall` | `aquilia/testing/effects.py` | Record of an acquire or release call on a MockEffectProvider. |
| `MockEffectProvider` | `aquilia/testing/effects.py` | Stub provider that returns configurable values. |
| `MockEffectRegistry` | `aquilia/testing/effects.py` | Test-friendly :class:`EffectRegistry` that auto-stubs missing effects. |
| `MockFlowContext` | `aquilia/testing/effects.py` | Test-friendly FlowContext for testing pipeline nodes and handlers. |
| `CapturedFault` | `aquilia/testing/faults.py` | A fault captured by :class:`MockFaultEngine`. |
| `MockFaultEngine` | `aquilia/testing/faults.py` | Drop-in replacement for :class:`~aquilia.faults.engine.FaultEngine` |
| `CapturedMail` | `aquilia/testing/mail.py` | A mail message captured during testing. |
| `MailTestMixin` | `aquilia/testing/mail.py` | Mixin providing mail assertion helpers. |
| `TestServer` | `aquilia/testing/server.py` | Lightweight test server wrapping :class:`AquiliaServer`. |

## Public Functions

| Name | Source | Role |
| --- | --- | --- |
| `set_active_config` | `aquilia/testing/config.py` | Register the config loader used by the running test server. |
| `get_active_config` | `aquilia/testing/config.py` | Return the active config loader. |
| `mock_provider` | `aquilia/testing/di.py` | Create a mock DI provider that always returns *value*. |
| `factory_provider` | `aquilia/testing/di.py` | Create a factory DI provider that calls *factory* on each resolve. |
| `override_provider` | `aquilia/testing/di.py` | Temporarily override a provider in a container. |
| `spy_provider` | `aquilia/testing/di.py` | Wrap an existing provider with a spy that tracks calls. |
| `aquilia_fixtures` | `aquilia/testing/fixtures.py` | Register Aquilia pytest fixtures. |
| `test_config` | `aquilia/testing/fixtures.py` | A blank :class:`TestConfig` for unit tests. |
| `fault_engine` | `aquilia/testing/fixtures.py` | A :class:`MockFaultEngine` for capturing faults. |
| `effect_registry` | `aquilia/testing/fixtures.py` | A :class:`MockEffectRegistry` for stubbing effects. |
| `cache_backend` | `aquilia/testing/fixtures.py` | A :class:`MockCacheBackend` (in-memory, zero-config). |
| `di_container` | `aquilia/testing/fixtures.py` | A :class:`TestContainer` with relaxed validation. |
| `identity_factory` | `aquilia/testing/fixtures.py` | A :class:`TestIdentityFactory` for creating test identities. |
| `mail_outbox` | `aquilia/testing/fixtures.py` | Clear the mail outbox before the test and return it. |
| `test_request` | `aquilia/testing/fixtures.py` | Factory fixture -- call with kwargs to create test requests. |
| `test_scope` | `aquilia/testing/fixtures.py` | Factory fixture -- call with kwargs to create ASGI scopes. |
| `test_server` | `aquilia/testing/fixtures.py` | Async fixture providing a booted :class:`TestServer`. |
| `test_client` | `aquilia/testing/fixtures.py` | Async fixture providing a :class:`TestClient` wired to a :class:`TestServer`. |
| `ws_client` | `aquilia/testing/fixtures.py` | Async fixture providing a :class:`WebSocketTestClient` wired to a :class:`TestServer`. |
| `settings_override` | `aquilia/testing/fixtures.py` | Fixture factory for overriding settings. |
| `get_outbox` | `aquilia/testing/mail.py` | Return the global mail outbox. |
| `clear_outbox` | `aquilia/testing/mail.py` | Clear the global mail outbox. |
| `capture_mail` | `aquilia/testing/mail.py` | Add a message to the outbox (called by the test mail provider). |
| `create_test_server` | `aquilia/testing/server.py` | Shortcut to create a :class:`TestServer`. |
| `make_test_scope` | `aquilia/testing/utils.py` | Build a minimal ASGI HTTP scope for testing. |
| `make_test_receive` | `aquilia/testing/utils.py` | Create an ASGI receive callable. |
| `make_test_request` | `aquilia/testing/utils.py` | Build a full :class:`~aquilia.request.Request` for testing. |
| `make_test_response` | `aquilia/testing/utils.py` | Build a :class:`~aquilia.response.Response` for assertion helpers. |
| `make_test_ws_scope` | `aquilia/testing/utils.py` | Build an ASGI WebSocket scope for testing. |
| `make_upload_file` | `aquilia/testing/utils.py` | Create a file tuple suitable for :class:`TestClient` upload. |

## Implementation Map

| File | What To Look For |
| --- | --- |
| `aquilia/testing/__init__.py` | Aquilia Testing Framework. |
| `aquilia/testing/assertions.py` | Aquilia Testing - Custom Assertion Helpers. |
| `aquilia/testing/auth.py` | Aquilia Testing - Auth & Identity Helpers. |
| `aquilia/testing/cache.py` | Aquilia Testing - Cache Testing Utilities. |
| `aquilia/testing/cases.py` | Aquilia Testing - Test Case Base Classes. |
| `aquilia/testing/client.py` | Aquilia Testing - HTTP & WebSocket Test Client. |
| `aquilia/testing/config.py` | Aquilia Testing - Config Override Utilities. |
| `aquilia/testing/di.py` | Aquilia Testing - DI Container Testing Utilities. |
| `aquilia/testing/effects.py` | Aquilia Testing - Effect System Testing Utilities. |
| `aquilia/testing/faults.py` | Aquilia Testing - Fault Testing Utilities. |
| `aquilia/testing/fixtures.py` | Aquilia Testing - Pytest Fixtures. |
| `aquilia/testing/mail.py` | Aquilia Testing - Mail Testing Utilities. |
| `aquilia/testing/server.py` | Aquilia Testing - TestServer Factory. |
| `aquilia/testing/utils.py` | Aquilia Testing - Request/Response Utility Factories. |

## Testing Pointers

Search `tests/` for `testing` to find behavior-level examples. The test suite is especially useful for edge cases because many modules expose lightweight public APIs but enforce important security and lifecycle behavior internally.
