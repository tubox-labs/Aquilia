# Testing Architecture

## Runtime Role

Testing helpers for requests, responses, test clients, WebSocket clients, live servers, DI overrides, auth factories, cache and mail mixins, effects, assertions, and captured faults.

The implementation is split across 14 Python files. The module boundary is visible in the file inventory below and the API reference is generated from the same source files.

## Primary Source Files

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

## Internal Dependency Shape

The table below is derived from import statements in the module. It shows which top-level packages this module depends on most often.

| Imported package | Import count |
| --- | --- |
| `__future__` | 13 |
| `aquilia` | 13 |
| `typing` | 12 |
| `collections` | 4 |
| `client` | 3 |
| `config` | 3 |
| `dataclasses` | 3 |
| `server` | 3 |
| `time` | 3 |
| `utils` | 3 |
| `assertions` | 2 |
| `asyncio` | 2 |
| `auth` | 2 |
| `cache` | 2 |
| `contextlib` | 2 |
| `di` | 2 |
| `effects` | 2 |
| `faults` | 2 |
| `json` | 2 |
| `logging` | 2 |
| `mail` | 2 |
| `cases` | 1 |
| `copy` | 1 |
| `fixtures` | 1 |
| `functools` | 1 |
| `pytest` | 1 |
| `unittest` | 1 |

## Data And Control Flow

1. Configuration or direct construction creates the public service objects, controllers, providers, or helpers for this module.
2. Runtime code imports the registered classes from manifests, workspace integrations, middleware stacks, or direct application code.
3. Public methods perform validation and convert invalid states into typed Aquilia faults where the implementation defines fault classes.
4. Integration points return Python data structures, `Response` objects, provider results, jobs, sessions, connections, or model instances depending on the subsystem.

## Boundary Rules

- Keep application-specific business decisions outside framework classes unless the class is explicitly a service or controller owned by your app.
- Prefer the public exports and typed configuration dataclasses shown in `api-reference.md`.
- When a module supplies both a low-level primitive and a high-level service, use the service in application code and keep primitives for tests, providers, or advanced integrations.
