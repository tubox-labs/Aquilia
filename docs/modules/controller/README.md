# Controllers Documentation

This directory is the professional documentation set for `controller`. It is implementation-driven and aligned with the current source files under `aquilia/controller`.

## What This Covers

The HTTP controller system with route decorators, compiler, router, factory, engine, filters, pagination, renderers, throttles, interceptors, exception filters, and OpenAPI generation.

## Source Files Read

- `aquilia/controller/__init__.py`: Aquilia Controller System
- `aquilia/controller/base.py`: Controller Base Class
- `aquilia/controller/compiler.py`: Controller Compiler - Compiles controllers to patterns and routes.
- `aquilia/controller/decorators.py`: Controller Method Decorators
- `aquilia/controller/engine.py`: Controller Engine - Executes controller methods with full integration.
- `aquilia/controller/factory.py`: Controller Factory
- `aquilia/controller/filters.py`: Aquilia Filter System -- declarative filtering, searching, and ordering.
- `aquilia/controller/metadata.py`: Controller Metadata Extraction
- `aquilia/controller/openapi.py`: OpenAPI 3.1.0 Generation for Aquilia Controllers.
- `aquilia/controller/pagination.py`: Aquilia Pagination System -- declarative pagination backends.
- `aquilia/controller/renderers.py`: Aquilia Content Negotiation & Renderer System.
- `aquilia/controller/router.py`: Controller Router - Pattern-based router for controllers.

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

- Python files: 12
- Public classes: 48
- Configuration or dataclass-like types: 8
- Public functions: 10
- Constants detected: 17

## Fast Start

```python
from aquilia import Controller, GET, POST, RequestCtx, Response

class UsersController(Controller):
    prefix = "/"
    tags = ["users"]

    @GET("/")
    async def list_users(self, ctx: RequestCtx):
        return Response.json({"items": []})

    @POST("/", status_code=201)
    async def create_user(self, ctx: RequestCtx):
        payload = await ctx.json()
        return Response.json({"created": payload}, status=201)
```

## Read Next

Start with `architecture.md` if you are learning how the subsystem fits into runtime boot. Use `api-reference.md` when you need exact methods, datatypes, and class fields. Use `examples.md` for copyable patterns that match the current code.
