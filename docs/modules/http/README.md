# HTTP Client Documentation

This directory is the professional documentation set for `http`. It is implementation-driven and aligned with the current source files under `aquilia/http`.

## What This Covers

The outbound async HTTP client with transport selection, sessions, requests, responses, retry policy, auth schemes, cookies, middleware, interceptors, multipart, and streaming.

## Source Files Read

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

- Python files: 17
- Public classes: 100
- Configuration or dataclass-like types: 19
- Public functions: 23
- Constants detected: 11

## Fast Start

```python
from aquilia.http import AsyncHTTPClient, HTTPClientConfig, RetryConfig

client = AsyncHTTPClient(
    HTTPClientConfig(
        base_url="https://api.example.test",
        retry=RetryConfig(max_attempts=3),
    )
)
response = await client.get("/health")
data = await response.json()
await client.close()
```

## Read Next

Start with `architecture.md` if you are learning how the subsystem fits into runtime boot. Use `api-reference.md` when you need exact methods, datatypes, and class fields. Use `examples.md` for copyable patterns that match the current code.
