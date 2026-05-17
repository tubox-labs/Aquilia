# Extended Middleware Edge Cases And Limitations

## Fault And Error Types

The following error-oriented classes are present in the implementation and should guide defensive usage.

| Type | Source | Meaning |
| --- | --- | --- |
| `CSRFError` | `aquilia/middleware_ext/security.py` | CSRF validation fault -- raised when CSRF protection detects a violation. |

## Common Edge Cases

- Optional dependencies may change behavior. Check imports and constructor docs before enabling production features.
- In-memory stores, queues, caches, adapters, and registries are usually process-local. Use durable backends when state must survive restarts or scale across workers.
- Request-scoped data must not be cached globally. Use request state, DI request scopes, or explicit parameters.
- Decorators in Aquilia generally attach metadata at import time. Runtime behavior happens later during compilation, routing, middleware execution, or service startup.
- Many subsystems intentionally convert invalid states into typed faults. Catch the specific fault type when application code can recover.

## Source-Level Limits To Review

Review these files before changing behavior:

- `aquilia/middleware_ext/__init__.py`: Extended middleware components for Aquilia framework.
- `aquilia/middleware_ext/effect_middleware.py`: Effect Middleware -- Per-request effect lifecycle management.
- `aquilia/middleware_ext/logging.py`: Enhanced Logging Middleware - Structured access logging.
- `aquilia/middleware_ext/rate_limit.py`: Rate Limiting Middleware - Production-grade request rate limiting.
- `aquilia/middleware_ext/request_scope.py`: Request Scope Middleware - Creates request-scoped DI container per request.
- `aquilia/middleware_ext/security.py`: Security Middleware Suite - Production-grade HTTP security middleware.
- `aquilia/middleware_ext/session_middleware.py`: Session Middleware - Integrates SessionEngine with request lifecycle.
- `aquilia/middleware_ext/static.py`: Static File Middleware - Production-grade static asset serving.
