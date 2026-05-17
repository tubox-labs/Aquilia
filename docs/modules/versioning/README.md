# Versioning Documentation

This directory is the professional documentation set for `versioning`. It is implementation-driven and aligned with the current source files under `aquilia/versioning`.

## What This Covers

The API versioning subsystem with decorators, parsers, semantic versions, negotiation, resolvers, middleware, sunset policies, and version graph checks.

## Source Files Read

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

- Python files: 11
- Public classes: 30
- Configuration or dataclass-like types: 5
- Public functions: 3
- Constants detected: 5

## Fast Start

```python
from aquilia.versioning import version, version_neutral
from aquilia import Controller, GET, RequestCtx, Response

class UsersController(Controller):
    @GET("/users", version="1.0")
    async def users_v1(self, ctx: RequestCtx):
        return Response.json({"version": "1.0"})

    @GET("/health")
    @version_neutral
    async def health(self, ctx: RequestCtx):
        return Response.json({"ok": True})
```

## Read Next

Start with `architecture.md` if you are learning how the subsystem fits into runtime boot. Use `api-reference.md` when you need exact methods, datatypes, and class fields. Use `examples.md` for copyable patterns that match the current code.
