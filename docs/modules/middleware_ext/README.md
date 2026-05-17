# Middleware_Ext Documentation

Extended production middleware for security, CORS/CSP/CSRF/HSTS, static files, rate limits, sessions, request scopes, effects, and logging.

## Coverage Snapshot

- Source files: 8
- Source lines: 3274
- Public classes: 22
- Public module functions: 7
- Constants/module flags: 7
- Public exports in `__all__`: 29

## Source Files Read

- `aquilia/middleware_ext/__init__.py`: Extended middleware components for Aquilia framework.
- `aquilia/middleware_ext/effect_middleware.py`: Effect Middleware -- Per-request effect lifecycle management.
- `aquilia/middleware_ext/logging.py`: Enhanced Logging Middleware - Structured access logging.
- `aquilia/middleware_ext/rate_limit.py`: Rate Limiting Middleware - Production-grade request rate limiting.
- `aquilia/middleware_ext/request_scope.py`: Request Scope Middleware - Creates request-scoped DI container per request.
- `aquilia/middleware_ext/security.py`: Security Middleware Suite - Production-grade HTTP security middleware.
- `aquilia/middleware_ext/session_middleware.py`: Session Middleware - Integrates SessionEngine with request lifecycle.
- `aquilia/middleware_ext/static.py`: Static File Middleware - Production-grade static asset serving.

## Document Map

- `architecture.md`: module boundaries, dependencies, lifecycle, and extension points.
- `configuration.md`: configuration classes, builders, server wiring, and precedence.
- `api-reference.md`: source-extracted classes, methods, functions, constants, exports, and signatures.
- `integration-guide.md`: how to wire the module into an Aquilia app.
- `cli-reference.md`: mounted `aq` commands for this module, if any.
- `examples.md`: usage examples derived from source and checked example apps.
- `edge-cases-and-limitations.md`: implementation limits and compatibility behavior.
- `troubleshooting.md`: diagnostic commands and common failure patterns.
