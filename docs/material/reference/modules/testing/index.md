# Testing Module

> `aquilia.testing` — Test utilities and clients

The Testing module provides a complete test framework with `TestServer`, `TestClient`, `WebSocketTestClient`, `AquiliaTestCase`, fixtures, mocks, and settings override utilities.

## When to Use

Use the Testing module when you need:

- Writing tests for controllers, services, and middleware
- Simulating HTTP requests without starting a real server
- Testing WebSocket connections
- Overriding DI providers and settings in tests
- Transaction-rollback between tests

## Key Classes

| Class | Purpose |
|---|---|
| `TestServer` | In-process test server |
| `TestClient` | Async HTTP test client |
| `WebSocketTestClient` | WebSocket test client |
| `AquiliaTestCase` | Base test case with fixtures |
| `SimpleTestCase` | No-database test case |
| `TransactionTestCase` | Transaction-reset test case |
| `LiveServerTestCase` | Real-server integration test |
| `create_test_server` | Factory for test server instances |
| `override_settings` | Context manager for settings override |

## Quick Example

```python
from aquilia.testing import TestClient, AquiliaTestCase
from aquilia import AppManifest

class TestUsersAPI(AquiliaTestCase):
    def setUp(self):
        self.client = TestClient(app=my_app)

    async def test_list_users(self):
        response = await self.client.get("/users/")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data["users"], list)

    async def test_create_user(self):
        response = await self.client.post(
            "/users/",
            json={"name": "Alice", "email": "alice@example.com"},
        )
        assert response.status_code == 201

    async def test_not_found(self):
        response = await self.client.get("/users/999")
        assert response.status_code == 404
```

## Installation

```bash
pip install aquilia[testing]
```

## Import Path

```python
from aquilia.testing import (
    TestClient,
    TestServer,
    WebSocketTestClient,
    AquiliaTestCase,
    SimpleTestCase,
    TransactionTestCase,
    LiveServerTestCase,
    create_test_server,
    override_settings,
)
```

## Related Modules

- [core/server](../core/server.md) — App instance for test client
- [di](../di/index.md) — Override providers in tests
- [sockets](../sockets/index.md) — WebSocket test client