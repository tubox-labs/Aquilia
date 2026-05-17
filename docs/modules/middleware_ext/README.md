# Extended Middleware Documentation

This directory is the professional documentation set for `middleware_ext`. It is implementation-driven and aligned with the current source files under `aquilia/middleware_ext`.

## What This Covers

Production middleware implementations for security, CORS, CSP, CSRF, HSTS, HTTPS redirects, proxy headers, sessions, static files, request scopes, logging, rate limiting, and effects.

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

- `architecture.md`: Runtime architecture and module boundaries
- `configuration.md`: Configuration entry points, datatypes, and precedence
- `api-reference.md`: Classes, methods, functions, constants, and data fields extracted from source
- `integration-guide.md`: How to wire the module into a real Aquilia application
- `cli-reference.md`: Command line surface and operational commands
- `edge-cases-and-limitations.md`: Known edge cases and implementation limits
- `troubleshooting.md`: Common failures and diagnosis steps
- `examples.md`: Code examples and usage patterns

## Public Surface Snapshot

- Python files: 8
- Public classes: 22
- Configuration or dataclass-like types: 1
- Public functions: 7
- Constants detected: 2

## Fast Start

```python
from aquilia.middleware_ext import EffectMiddleware, FlowContextMiddleware, CombinedLogFormatter, DevLogFormatter, StructuredLogFormatter, EnhancedLoggingMiddleware

# The imported symbols above are public exports from this module.
# See api-reference.md for constructor signatures, methods, and data fields.
```

## Read Next

Start with `architecture.md` if you are learning how the subsystem fits into runtime boot. Use `api-reference.md` when you need exact methods, datatypes, and class fields. Use `examples.md` for copyable patterns that match the current code.
