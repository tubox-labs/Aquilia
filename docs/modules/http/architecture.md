# HTTP Client Architecture

## Runtime Role

The outbound async HTTP client with transport selection, sessions, requests, responses, retry policy, auth schemes, cookies, middleware, interceptors, multipart, and streaming.

The implementation is split across 17 Python files. The module boundary is visible in the file inventory below and the API reference is generated from the same source files.

## Primary Source Files

- `aquilia/http/__init__.py`: AquilaHTTP - Async HTTP Client for Aquilia.
- `aquilia/http/_transport.py`: HTTP Transport Layer
- `aquilia/http/auth.py`: AquilaHTTP - Authentication Interceptors.
- `aquilia/http/client.py`: AquilaHTTP - Async HTTP Client.
- `aquilia/http/config.py`: AquilaHTTP - Configuration.
- `aquilia/http/cookies.py`: AquilaHTTP - Cookie Jar.
- `aquilia/http/faults.py`: AquilaHTTP - Fault Classes.
- `aquilia/http/integration.py`: AquilaHTTP - Framework Integration.
- `aquilia/http/interceptors.py`: AquilaHTTP - Interceptors.
- `aquilia/http/middleware.py`: AquilaHTTP - Middleware.
- `aquilia/http/multipart.py`: AquilaHTTP - Multipart Form Data.
- `aquilia/http/pool.py`: AquilaHTTP - Connection Pool.
- `aquilia/http/request.py`: AquilaHTTP - HTTP Client Request.
- `aquilia/http/response.py`: AquilaHTTP - HTTP Client Response.
- `aquilia/http/retry.py`: AquilaHTTP - Retry Strategies.
- `aquilia/http/session.py`: AquilaHTTP - HTTP Session.
- `aquilia/http/streaming.py`: AquilaHTTP - Streaming Support.

## Internal Dependency Shape

The table below is derived from import statements in the module. It shows which top-level packages this module depends on most often.

| Imported package | Import count |
| --- | --- |
| `__future__` | 16 |
| `typing` | 14 |
| `collections` | 11 |
| `dataclasses` | 11 |
| `logging` | 10 |
| `config` | 8 |
| `request` | 8 |
| `response` | 8 |
| `faults` | 6 |
| `time` | 6 |
| `abc` | 5 |
| `asyncio` | 4 |
| `interceptors` | 4 |
| `urllib` | 4 |
| `_transport` | 3 |
| `cookies` | 3 |
| `middleware` | 3 |
| `base64` | 2 |
| `client` | 2 |
| `enum` | 2 |
| `http` | 2 |
| `json` | 2 |
| `multipart` | 2 |
| `pathlib` | 2 |
| `session` | 2 |
| `ssl` | 2 |
| `aquilia` | 1 |
| `auth` | 1 |
| `datetime` | 1 |
| `gzip` | 1 |

## Data And Control Flow

1. Configuration or direct construction creates the public service objects, controllers, providers, or helpers for this module.
2. Runtime code imports the registered classes from manifests, workspace integrations, middleware stacks, or direct application code.
3. Public methods perform validation and convert invalid states into typed Aquilia faults where the implementation defines fault classes.
4. Integration points return Python data structures, `Response` objects, provider results, jobs, sessions, connections, or model instances depending on the subsystem.

## Boundary Rules

- Keep application-specific business decisions outside framework classes unless the class is explicitly a service or controller owned by your app.
- Prefer the public exports and typed configuration dataclasses shown in `api-reference.md`.
- When a module supplies both a low-level primitive and a high-level service, use the service in application code and keep primitives for tests, providers, or advanced integrations.
