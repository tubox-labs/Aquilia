# Testing Documentation

This directory is the professional documentation set for `testing`. It is implementation-driven and aligned with the current source files under `aquilia/testing`.

## What This Covers

Testing helpers for requests, responses, test clients, WebSocket clients, live servers, DI overrides, auth factories, cache and mail mixins, effects, assertions, and captured faults.

## Source Files Read

- `aquilia/testing/__init__.py`: Aquilia Testing Framework.
- `aquilia/testing/assertions.py`: Aquilia Testing - Custom Assertion Helpers.
- `aquilia/testing/auth.py`: Aquilia Testing - Auth & Identity Helpers.
- `aquilia/testing/cache.py`: Aquilia Testing - Cache Testing Utilities.
- `aquilia/testing/cases.py`: Aquilia Testing - Test Case Base Classes.
- `aquilia/testing/client.py`: Aquilia Testing - HTTP & WebSocket Test Client.
- `aquilia/testing/config.py`: Aquilia Testing - Config Override Utilities.
- `aquilia/testing/di.py`: Aquilia Testing - DI Container Testing Utilities.
- `aquilia/testing/effects.py`: Aquilia Testing - Effect System Testing Utilities.
- `aquilia/testing/faults.py`: Aquilia Testing - Fault Testing Utilities.
- `aquilia/testing/fixtures.py`: Aquilia Testing - Pytest Fixtures.
- `aquilia/testing/mail.py`: Aquilia Testing - Mail Testing Utilities.
- `aquilia/testing/server.py`: Aquilia Testing - TestServer Factory.
- `aquilia/testing/utils.py`: Aquilia Testing - Request/Response Utility Factories.

## Document Map

- `architecture.md`: Runtime architecture and module boundaries
- `configuration.md`: Configuration entry points, datatypes, and precedence
- `api-reference.md`: Classes, methods, functions, constants, and data fields extracted from source
- `integration-guide.md`: How to wire the module into a real Aquilia application
- `cli-reference.md`: Command line surface and operational commands
- `edge-cases-and-limitations.md`: Known edge cases and implementation limits
- `troubleshooting.md`: Common failures and diagnosis steps
- `examples.md`: Code examples and usage patterns

## Public Surface Snapshot

- Python files: 14
- Public classes: 25
- Configuration or dataclass-like types: 4
- Public functions: 30
- Constants detected: 2

## Fast Start

```python
from aquilia.testing import make_test_request, TestClient

request = make_test_request(method="GET", path="/health")
client = TestClient(app)
response = await client.get("/health")
assert response.status_code == 200
```

## Read Next

Start with `architecture.md` if you are learning how the subsystem fits into runtime boot. Use `api-reference.md` when you need exact methods, datatypes, and class fields. Use `examples.md` for copyable patterns that match the current code.
