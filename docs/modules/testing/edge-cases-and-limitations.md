# Testing Edge Cases And Limitations

## Fault And Error Types

The following error-oriented classes are present in the implementation and should guide defensive usage.

| Type | Source | Meaning |
| --- | --- | --- |
| `CapturedFault` | `aquilia/testing/faults.py` | A fault captured by :class:`MockFaultEngine`. |
| `MockFaultEngine` | `aquilia/testing/faults.py` | Drop-in replacement for :class:`~aquilia.faults.engine.FaultEngine` |

## Common Edge Cases

- Optional dependencies may change behavior. Check imports and constructor docs before enabling production features.
- In-memory stores, queues, caches, adapters, and registries are usually process-local. Use durable backends when state must survive restarts or scale across workers.
- Request-scoped data must not be cached globally. Use request state, DI request scopes, or explicit parameters.
- Decorators in Aquilia generally attach metadata at import time. Runtime behavior happens later during compilation, routing, middleware execution, or service startup.
- Many subsystems intentionally convert invalid states into typed faults. Catch the specific fault type when application code can recover.

## Source-Level Limits To Review

Review these files before changing behavior:

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
