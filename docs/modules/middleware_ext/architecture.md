# Extended Middleware Architecture

## Runtime Role

Production middleware implementations for security, CORS, CSP, CSRF, HSTS, HTTPS redirects, proxy headers, sessions, static files, request scopes, logging, rate limiting, and effects.

The implementation is split across 8 Python files. The module boundary is visible in the file inventory below and the API reference is generated from the same source files.

## Primary Source Files

- `aquilia/middleware_ext/__init__.py`: Extended middleware components for Aquilia framework.
- `aquilia/middleware_ext/effect_middleware.py`: Effect Middleware -- Per-request effect lifecycle management.
- `aquilia/middleware_ext/logging.py`: Enhanced Logging Middleware - Structured access logging.
- `aquilia/middleware_ext/rate_limit.py`: Rate Limiting Middleware - Production-grade request rate limiting.
- `aquilia/middleware_ext/request_scope.py`: Request Scope Middleware - Creates request-scoped DI container per request.
- `aquilia/middleware_ext/security.py`: Security Middleware Suite - Production-grade HTTP security middleware.
- `aquilia/middleware_ext/session_middleware.py`: Session Middleware - Integrates SessionEngine with request lifecycle.
- `aquilia/middleware_ext/static.py`: Static File Middleware - Production-grade static asset serving.

## Internal Dependency Shape

The table below is derived from import statements in the module. It shows which top-level packages this module depends on most often.

| Imported package | Import count |
| --- | --- |
| `aquilia` | 15 |
| `collections` | 7 |
| `typing` | 7 |
| `__future__` | 5 |
| `logging` | 4 |
| `contextlib` | 2 |
| `datetime` | 2 |
| `time` | 2 |
| `effect_middleware` | 1 |
| `email` | 1 |
| `hashlib` | 1 |
| `ipaddress` | 1 |
| `math` | 1 |
| `mimetypes` | 1 |
| `os` | 1 |
| `pathlib` | 1 |
| `rate_limit` | 1 |
| `re` | 1 |
| `request_scope` | 1 |
| `secrets` | 1 |
| `security` | 1 |
| `session_middleware` | 1 |
| `static` | 1 |

## Data And Control Flow

1. Configuration or direct construction creates the public service objects, controllers, providers, or helpers for this module.
2. Runtime code imports the registered classes from manifests, workspace integrations, middleware stacks, or direct application code.
3. Public methods perform validation and convert invalid states into typed Aquilia faults where the implementation defines fault classes.
4. Integration points return Python data structures, `Response` objects, provider results, jobs, sessions, connections, or model instances depending on the subsystem.

## Boundary Rules

- Keep application-specific business decisions outside framework classes unless the class is explicitly a service or controller owned by your app.
- Prefer the public exports and typed configuration dataclasses shown in `api-reference.md`.
- When a module supplies both a low-level primitive and a high-level service, use the service in application code and keep primitives for tests, providers, or advanced integrations.
