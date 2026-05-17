# Http Documentation

Native async HTTP client, request/response builders, sessions, retry policies, auth interceptors, cookies, middleware, streaming, and transport.

## Coverage Snapshot

- Source files: 17
- Source lines: 8549
- Public classes: 100
- Public module functions: 23
- Constants/module flags: 12
- Public exports in `__all__`: 122

## Source Files Read

- `aquilia/http/__init__.py`: AquilaHTTP — Async HTTP Client for Aquilia.
- `aquilia/http/_transport.py`: HTTP Transport Layer
- `aquilia/http/auth.py`: AquilaHTTP — Authentication Interceptors.
- `aquilia/http/client.py`: AquilaHTTP — Async HTTP Client.
- `aquilia/http/config.py`: AquilaHTTP — Configuration.
- `aquilia/http/cookies.py`: AquilaHTTP — Cookie Jar.
- `aquilia/http/faults.py`: AquilaHTTP — Fault Classes.
- `aquilia/http/integration.py`: AquilaHTTP — Framework Integration.
- `aquilia/http/interceptors.py`: AquilaHTTP — Interceptors.
- `aquilia/http/middleware.py`: AquilaHTTP — Middleware.
- `aquilia/http/multipart.py`: AquilaHTTP — Multipart Form Data.
- `aquilia/http/pool.py`: AquilaHTTP — Connection Pool.
- `aquilia/http/request.py`: AquilaHTTP — HTTP Client Request.
- `aquilia/http/response.py`: AquilaHTTP — HTTP Client Response.
- `aquilia/http/retry.py`: AquilaHTTP — Retry Strategies.
- `aquilia/http/session.py`: AquilaHTTP — HTTP Session.
- `aquilia/http/streaming.py`: AquilaHTTP — Streaming Support.

## Document Map

- `architecture.md`: module boundaries, dependencies, lifecycle, and extension points.
- `configuration.md`: configuration classes, builders, server wiring, and precedence.
- `api-reference.md`: source-extracted classes, methods, functions, constants, exports, and signatures.
- `integration-guide.md`: how to wire the module into an Aquilia app.
- `cli-reference.md`: mounted `aq` commands for this module, if any.
- `examples.md`: usage examples derived from source and checked example apps.
- `edge-cases-and-limitations.md`: implementation limits and compatibility behavior.
- `troubleshooting.md`: diagnostic commands and common failure patterns.
