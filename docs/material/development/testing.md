# Testing Guide

Aquilia provides a comprehensive, batteries-included testing framework tightly integrated with every subsystem: server lifecycle, DI containers, faults, effects, cache, sessions, auth, controllers, middleware, WebSockets, and mail.

```python
from aquilia.testing import AquiliaTestCase, TestClient, TestServer, WebSocketTestClient

# All testing tools are available from the top-level aquilia.testing package
```

## Test Server

The `TestServer` wraps an `AquiliaServer` instance with test-mode defaults: memory stores, no external connections, and configurable subsystem toggles.

### Quick Start

```python
from aquilia.testing import TestServer, TestClient
from aquilia.manifest import AppManifest

# Define a manifest for testing
my_manifest = AppManifest(
    name="test_app",
    version="0.0.1-test",
    controllers=["modules.test.controllers:UsersController"],
    services=[],
)

# Using async context manager (recommended)
async with TestServer(manifests=[my_manifest]) as server:
    client = TestClient(server)
    resp = await client.get("/users")
    assert resp.status_code == 200

# Or manual start/stop
server = TestServer(manifests=[my_manifest])
await server.start()
# ... tests ...
await server.stop()
```

### Factory Shortcut

```python
from aquilia.testing import create_test_server

server = create_test_server(my_manifest, debug=True)
await server.start()
```

### Subsystem Toggles

Each subsystem is **off by default** for test isolation. Enable only what you need:

```python
server = TestServer(
    manifests=[my_manifest],
    debug=True,
    enable_cache=True,       # Boot the cache subsystem
    enable_sessions=True,    # Boot sessions
    enable_auth=True,        # Boot the auth subsystem
    enable_mail=True,        # Boot mail
    enable_templates=True,   # Boot templates
)
```

### Config Overrides

```python
server = TestServer(
    manifests=[my_manifest],
    config_overrides={
        "database": {"url": "sqlite:///:memory:"},
        "cache": {"backend": "memory"},
    },
)
```

### Accessor Properties

Inspect the running server's subsystems:

| Property | Returns |
|----------|---------|
| `server.app` | ASGI application callable |
| `server.config` | `TestConfig` instance |
| `server.di_container` | First DI container |
| `server.controller_router` | Route registry |
| `server.middleware_stack` | Middleware chain |
| `server.fault_engine` | Fault engine instance |
| `server.effect_registry` | Effect registry |
| `server.cache_service` | Cache service (if enabled) |
| `server.auth_manager` | Auth manager (if enabled) |
| `server.session_engine` | Session engine (if enabled) |
| `server.mail_provider` | Mail provider (if enabled) |
| `server.get_url("route_name", id="123")` | Reverse route URL |

---

## Test Client

The `TestClient` issues in-process ASGI requests without opening network sockets. It invokes the ASGI application directly and captures response events.

### Basic Usage

```python
async with TestServer(manifests=[m]) as server:
    client = TestClient(server)
    resp = await client.get("/api/users")
    print(resp.status_code)  # 200
    print(resp.json())       # {"users": [...]}
```

### HTTP Verbs

```python
resp = await client.get("/api/users")
resp = await client.post("/api/users", json={"name": "Alice"})
resp = await client.put("/api/users/1", json={"name": "Bob"})
resp = await client.patch("/api/users/1", json={"name": "Charlie"})
resp = await client.delete("/api/users/1")
resp = await client.head("/api/users")
resp = await client.options("/api/users")
```

### Request Options

```python
# Custom headers
resp = await client.get("/api/users", headers={"X-Custom": "value"})

# Query strings
resp = await client.get("/api/users", query_string="page=1&limit=10")

# Form data
resp = await client.post("/login", data={"username": "alice", "password": "s3cret"})

# Raw body
resp = await client.post("/webhook", body=b'{"event":"push"}')

# File uploads
resp = await client.post(
    "/upload",
    data={"description": "My photo"},
    files={"attachment": ("photo.jpg", b"binary-data", "image/jpeg")},
)
```

### Auth Helpers

```python
# Bearer token
client.set_bearer_token("eyJhbGciOi...")
resp = await client.get("/api/me")  # Authorization header auto-injected

# Clear auth
client.clear_auth()
```

### Redirect Following

```python
client = TestClient(server, follow_redirects=True)
resp = await client.get("/old-url")
# Automatically follows 3xx redirects (up to 20 hops)
print(client.history)  # List of redirect responses
```

### Cookie Management

The client maintains a cookie jar like a real browser:

```python
# Manual cookie
client.set_cookie("session_id", "abc123")

# Auto-captured from Set-Cookie headers
resp = await client.post("/login", json={"username": "alice"})
# client._cookies now contains any session cookies set by the server

client.clear_cookies()
```

### Response Object

The `TestResponse` provides convenient accessors:

```python
resp = await client.get("/api/users")

# Status
resp.status_code       # int: 200
resp.is_success        # bool: 200-299
resp.is_redirect       # bool: 300-399
resp.is_client_error   # bool: 400-499
resp.is_server_error   # bool: 500-599

# Body
resp.text              # str: decoded text
resp.json()            # parsed JSON
resp.body              # raw bytes

# Headers
resp.headers           # dict[str, str]
resp.content_type      # str: "application/json"
resp.content_length    # int | None
resp.header("location")  # Get specific header
resp.has_header("x-request-id")

# Timing
resp.elapsed           # float: milliseconds

# Redirect info
resp.location          # str | None: Location header
```

---

## WebSocket Test Client

The `WebSocketTestClient` simulates a WebSocket connection by feeding ASGI events directly into the application's `websocket` handler.

```python
from aquilia.testing import WebSocketTestClient

ws = WebSocketTestClient(server)

# Connect
await ws.connect("/ws/chat", headers=[("Authorization", "Bearer token")])

# Send
await ws.send_text("hello")
await ws.send_json({"type": "message", "text": "hi"})
await ws.send_bytes(b"\x00\x01\x02")

# Receive
msg = await ws.receive_text(timeout=5.0)
data = await ws.receive_json(timeout=5.0)
binary = await ws.receive_bytes(timeout=5.0)

# Check state
assert ws.is_connected

# Close
await ws.close(code=1000)

# Async context manager
async with WebSocketTestClient(server) as ws:
    await ws.connect("/ws/chat")
    await ws.send_text("hello")
    msg = await ws.receive_text()
```

---

## Test Case Classes

### AquiliaTestCase

Full-featured async test case with integrated server lifecycle. Boots a `TestServer` before each test and tears it down afterward.

```python
from aquilia.testing import AquiliaTestCase
from aquilia.manifest import AppManifest

users_manifest = AppManifest(
    name="users",
    version="1.0.0",
    controllers=["modules.users.controllers:UsersController"],
)

class TestUserAPI(AquiliaTestCase):
    manifests = [users_manifest]
    settings = {"debug": True}

    async def test_list_users(self):
        resp = await self.client.get("/users")
        self.assert_status(resp, 200)
        self.assert_json(resp)

    async def test_create_user(self):
        resp = await self.client.post("/users", json={"name": "Alice"})
        self.assert_status(resp, 201)

    async def test_get_url(self):
        url = self.get_url("users_detail", id="42")
        resp = await self.client.get(url)

    async def test_login(self):
        resp = await self.login(username="admin@test.com", password="password")
        self.assert_status(resp, 200)
```

**Class-level configuration attributes:**

| Attribute | Type | Default | Description |
|-----------|------|---------|-------------|
| `manifests` | `list[AppManifest]` | `[]` | Manifests to load |
| `settings` | `dict` | `{}` | Config overrides |
| `enable_cache` | `bool` | `False` | Boot cache subsystem |
| `enable_sessions` | `bool` | `False` | Boot sessions |
| `enable_auth` | `bool` | `False` | Boot auth subsystem |
| `enable_mail` | `bool` | `False` | Boot mail |
| `enable_templates` | `bool` | `False` | Boot templates |

**Convenience accessors:**

| Property | Returns |
|----------|---------|
| `self.server` | `TestServer` instance |
| `self.client` | `TestClient` instance |
| `self.di_container` | First DI container |
| `self.fault_engine` | Fault engine |
| `self.config` | `TestConfig` |
| `self.controller_router` | Route router |
| `self.cache_service` | Cache service (if enabled) |

### TransactionTestCase

Wraps each test in a database transaction that is rolled back after completion. Database state is never committed — tests are fully isolated.

```python
from aquilia.testing import TransactionTestCase

class TestProductCRUD(TransactionTestCase):
    manifests = [products_manifest]
    settings = {"database": {"url": "sqlite:///test.db", "auto_create": True}}

    async def test_create_product(self):
        resp = await self.client.post("/products", json={"name": "Widget"})
        self.assert_status(resp, 201)

    # After this test, the product is not actually persisted
```

### LiveServerTestCase

Starts a real ASGI server on a random port. Useful for end-to-end tests requiring a genuine TCP connection.

```python
from aquilia.testing import LiveServerTestCase

class TestE2E(LiveServerTestCase):
    manifests = [app_manifest]
    host = "127.0.0.1"
    port = 0  # Random port

    async def test_healthcheck(self):
        import httpx
        async with httpx.AsyncClient() as http:
            resp = await http.get(f"{self.live_server_url}/health")
            assert resp.status_code == 200

    async def test_browser_simulation(self):
        # Can be used with selenium, playwright, or any HTTP client
        print(self.live_server_url)  # http://127.0.0.1:54321
```

### SimpleTestCase

Test case that does NOT start a server. For pure unit tests needing only assertion helpers.

```python
from aquilia.testing import SimpleTestCase

class TestUtils(SimpleTestCase):
    def test_helper_function(self):
        result = my_pure_function(42)
        self.assertEqual(result, 84)
```

---

## Assertion Helpers

The `AquiliaAssertions` mixin provides over 50 assertion methods. All test case classes inherit them.

### Status Assertions

```python
self.assert_status(resp, 200)
self.assert_success(resp)           # 2xx
self.assert_created(resp)           # 201
self.assert_accepted(resp)          # 202
self.assert_no_content(resp)        # 204
self.assert_redirect(resp, location="/home")
self.assert_permanent_redirect(resp)
self.assert_bad_request(resp)       # 400
self.assert_unauthorized(resp)      # 401
self.assert_forbidden(resp)         # 403
self.assert_not_found(resp)         # 404
self.assert_method_not_allowed(resp)# 405
self.assert_conflict(resp)          # 409
self.assert_gone(resp)              # 410
self.assert_unprocessable(resp)     # 422
self.assert_too_many_requests(resp) # 429
self.assert_server_error(resp)      # 500
self.assert_service_unavailable(resp)# 503
```

### JSON Assertions

```python
self.assert_json(resp, expected={"key": "value"})
self.assert_json_contains(resp, {"name": "Alice", "active": True})
self.assert_json_key(resp, "data")
self.assert_json_path(resp, "data.users.0.name", "Alice")
self.assert_json_path(resp, "meta.total")  # Existence check
self.assert_json_list(resp, min_length=1)
self.assert_json_length(resp, 5)
self.assert_json_not_empty(resp)
```

### Header Assertions

```python
self.assert_header(resp, "content-type", "application/json")
self.assert_header_contains(resp, "content-type", "json")
self.assert_no_header(resp, "x-powered-by")
self.assert_content_length(resp, 42)
```

### Cookie Assertions

```python
self.assert_cookie(resp, "session_id")
self.assert_cookie_value(resp, "session_id", "abc123")
self.assert_no_cookie(resp, "session_id")
```

### Body Assertions

```python
self.assert_body_contains(resp, "Welcome")
self.assert_body_not_contains(resp, "error")
self.assert_body_empty(resp)
self.assert_html(resp)
self.assert_content_type(resp, "text/html")
```

### Fault Assertions

```python
# Assert a specific fault was captured
self.assert_fault_raised(engine, code="ROUTE_NOT_FOUND")
self.assert_fault_raised(engine, domain="routing")

# Assert no faults
self.assert_no_faults(engine)

# Assert fault count
self.assert_fault_count(engine, 3)

# Assert fault severity
self.assert_fault_severity(engine, FaultSeverity.ERROR, code="VALIDATION_FAILED")
```

### DI Assertions

```python
self.assert_registered(container, UserService)
self.assert_not_registered(container, DeprecatedService)
self.assert_resolves(container, UserService)
await self.assert_resolves_async(container, UserService)
```

### Effect Assertions

```python
self.assert_effect_acquired(provider)
self.assert_effect_acquired(provider, count=3)
self.assert_effect_released(provider)
```

### Cache Assertions

```python
await self.assert_cache_hit(cache, "user:1", expected={"name": "Alice"})
await self.assert_cache_miss(cache, "nonexistent")
```

### Mail Assertions

```python
self.assert_mail_count(outbox, 2)
self.assert_mail_to(outbox, "user@example.com")
self.assert_mail_from(outbox, "noreply@myapp.com")
```

---

## Pytest Fixtures

Import `aquilia_fixtures` in your `conftest.py` to register all fixtures:

```python
# tests/conftest.py
from aquilia.testing.fixtures import aquilia_fixtures

aquilia_fixtures()  # Registers all standard fixtures
```

### Available Fixtures

| Fixture | Type | Description |
|---------|------|-------------|
| `test_config` | sync | Blank `TestConfig` for unit tests |
| `fault_engine` | sync | `MockFaultEngine` for capturing faults |
| `effect_registry` | sync | `MockEffectRegistry` for stubbing effects |
| `cache_backend` | sync | `MockCacheBackend` (in-memory, zero-config) |
| `di_container` | sync | `TestContainer` with relaxed validation |
| `identity_factory` | sync | `TestIdentityFactory` for creating test identities |
| `mail_outbox` | sync | Clears/returns mail outbox per test |
| `test_request` | sync | Factory for creating test request objects |
| `test_scope` | sync | Factory for creating ASGI scopes |
| `test_server` | async | Booted `TestServer` (auto-shutdown) |
| `test_client` | async | `TestClient` wired to `test_server` |
| `ws_client` | async | `WebSocketTestClient` wired to `test_server` |
| `settings_override` | sync | Factory for `override_settings()` |

### Fixture Usage Examples

```python
# Async fixture usage
async def test_api(test_client):
    resp = await test_client.get("/health")
    assert resp.status_code == 200

async def test_websocket(ws_client):
    await ws_client.connect("/ws")
    await ws_client.send_text("ping")
    msg = await ws_client.receive_text()
    assert msg == "pong"

# Sync fixture usage
def test_di_registration(di_container):
    di_container.register_value("Database", FakeDatabase())
    db = di_container.resolve("Database")
    assert db is not None

def test_mail_sent(mail_outbox):
    # Your code sends mail
    assert len(mail_outbox) == 1
    assert mail_outbox[0].to == ["user@example.com"]
```

---

## Mocking Dependency Injection

### TestContainer

A `Container` subclass with test-friendly defaults:

```python
from aquilia.testing.di import TestContainer

container = TestContainer()

# Register values directly
container.register_value("Database", FakeDatabase())

# Register factories
container.register_factory("Client", lambda: FakeClient())

# Resolution tracking
user = container.resolve("Database")
print(container.resolution_log)  # ["Database"]

# Reset between tests
container.reset()
```

### Mock Provider

Replace a real service with a fixed-value mock:

```python
from aquilia.testing.di import mock_provider

container.register(mock_provider(UserRepo, FakeUserRepo(), scope="singleton"))
```

### Override Provider (Context Manager)

Temporarily replace a provider, restoring the original on exit:

```python
from aquilia.testing.di import override_provider

async with override_provider(container, UserRepo, FakeRepo()):
    user = await container.resolve_async(UserRepo)
    assert isinstance(user, FakeRepo)
# Original provider restored
```

### Spy Provider

Wrap an existing provider with a spy that tracks calls without changing behavior:

```python
from aquilia.testing.di import spy_provider

async with spy_provider(container, UserRepo) as spy:
    user = await container.resolve_async(UserRepo)
    assert spy.resolve_count == 1
```

### Factory Provider

Create a provider that calls a factory on each resolve:

```python
from aquilia.testing.di import factory_provider

container.register(factory_provider("counter", lambda: incrementing_counter()))
```

---

## Config Overrides

### override_settings Context Manager / Decorator

```python
from aquilia.testing import override_settings

# Context manager
with override_settings(debug=True, cache={"backend": "memory"}):
    resp = await client.get("/")

# Decorator
@override_settings(debug=True)
async def test_debug_mode():
    resp = await client.get("/")
    assert resp.status_code == 200
```

### TestConfig

```python
from aquilia.testing import TestConfig
from aquilia.config import ConfigLoader

loader = ConfigLoader()
loader.config_data = {"debug": False}
cfg = TestConfig(loader, debug=True, runtime={"mode": "test"})

assert cfg["debug"] is True
assert cfg.get("runtime.mode") == "test"
assert "debug" in cfg
```

---

## Running Tests via CLI

The `aq test` command sets `AQUILIA_ENV=test` and auto-discovers tests:

```bash
# Run all tests
aq test

# Specific path
aq test tests/test_users.py

# Pattern filter
aq test -k "test_create"

# Verbose with coverage
aq test -v --coverage

# Fail fast
aq test -x

# Marker filter
aq test -m "slow"

# Parallel (requires pytest-xdist)
aq test --parallel

# HTML coverage report
aq test --coverage-html

# Re-run only previously failed
aq test --last-failed
```

Test discovery looks in:
- `tests/` directory
- `modules/*/tests/` directories
- `modules/*/test_*.py` files

---

## E2E Testing with Docker

The project includes `docker-compose.test.yml` for E2E regression tests:

```yaml
# docker-compose.test.yml
services:
  redis-test:
    image: redis:7-alpine
    ports:
      - "6399:6379"
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 5s
      timeout: 3s
      retries: 3
    tmpfs:
      - /data

  test-runner:
    build:
      context: .
    depends_on:
      redis-test:
        condition: service_healthy
    environment:
      - AQUILIA_ENV=test
      - REDIS_URL=redis://redis-test:6379/0
      - PYTHONDONTWRITEBYTECODE=1
    command: python -m pytest tests/ -v --tb=short
```

```bash
docker compose -f docker-compose.test.yml up --build --abort-on-container-exit
```

---

## Best Practices

1. **Use `AquiliaTestCase` for integration tests** — it handles server lifecycle automatically.
2. **Use `SimpleTestCase` for pure unit tests** — no server overhead.
3. **Enable only needed subsystems** — keep `enable_cache=False` unless testing cache.
4. **Use `override_settings` for config variations** — cleaner than creating multiple manifests.
5. **Use `MockFaultEngine` for error path testing** — capture and assert on structured faults.
6. **Use `TransactionTestCase` for DB tests** — automatic rollback keeps tests isolated.
7. **Use `LiveServerTestCase` for external client testing** — when you need a real TCP port.
8. **Prefer `override_provider` over `mock_provider`** — it restores original state automatically.