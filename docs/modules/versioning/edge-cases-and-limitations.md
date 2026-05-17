# Versioning Edge Cases And Limitations

## Fault And Error Types

The following error-oriented classes are present in the implementation and should guide defensive usage.

| Type | Source | Meaning |
| --- | --- | --- |
| `VersionError` | `aquilia/versioning/errors.py` | Base class for all versioning errors. |
| `InvalidVersionError` | `aquilia/versioning/errors.py` | Raised when a version string cannot be parsed. |
| `UnsupportedVersionError` | `aquilia/versioning/errors.py` | Raised when a valid version is not in the supported set. |
| `VersionSunsetError` | `aquilia/versioning/errors.py` | Raised when a version has been sunset (permanently retired). |
| `MissingVersionError` | `aquilia/versioning/errors.py` | Raised when no version is present and no default is configured. |
| `VersionNegotiationError` | `aquilia/versioning/errors.py` | Raised when version negotiation fails. |

## Common Edge Cases

- Optional dependencies may change behavior. Check imports and constructor docs before enabling production features.
- In-memory stores, queues, caches, adapters, and registries are usually process-local. Use durable backends when state must survive restarts or scale across workers.
- Request-scoped data must not be cached globally. Use request state, DI request scopes, or explicit parameters.
- Decorators in Aquilia generally attach metadata at import time. Runtime behavior happens later during compilation, routing, middleware execution, or service startup.
- Many subsystems intentionally convert invalid states into typed faults. Catch the specific fault type when application code can recover.

## Source-Level Limits To Review

Review these files before changing behavior:

- `aquilia/versioning/__init__.py`: Aquilia Versioning System - Epoch-Based API Versioning
- `aquilia/versioning/core.py`: Aquilia Versioning - Core Types
- `aquilia/versioning/decorators.py`: Aquilia Versioning - Route-Level Decorators
- `aquilia/versioning/errors.py`: Aquilia Versioning - Version Errors
- `aquilia/versioning/graph.py`: Aquilia Versioning - Version Graph
- `aquilia/versioning/middleware.py`: Aquilia Versioning - Version Middleware
- `aquilia/versioning/negotiation.py`: Aquilia Versioning - Version Negotiation
- `aquilia/versioning/parser.py`: Aquilia Versioning - Version Parser
- `aquilia/versioning/resolvers.py`: Aquilia Versioning - Version Resolvers
- `aquilia/versioning/strategy.py`: Aquilia Versioning - Version Strategy
- `aquilia/versioning/sunset.py`: Aquilia Versioning - Sunset Lifecycle
