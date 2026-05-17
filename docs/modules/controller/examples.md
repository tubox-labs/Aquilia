# Controller Examples

Controller base class, route decorators, compiler, router, execution engine, renderers, filters, pagination, and OpenAPI generation.

Examples here use public symbols and checked patterns from the repository. When a module has no safe standalone constructor example, the example focuses on importing and wiring the actual source-backed API.

## Source-Backed Import Examples

```python
from aquilia.controller.base import RequestCtx
from aquilia.controller.base import ExceptionFilter
from aquilia.controller.compiler import CompiledRoute
from aquilia.controller.compiler import CompiledController
from aquilia.controller.decorators import RouteDecorator
from aquilia.controller.decorators import GET
```

## Workspace/Manifest Wiring Example

```python
from aquilia import AppManifest, Integration, Module, Workspace

workspace = (
    Workspace("example", version="1.0.0")
    .runtime(mode="dev", port=8000)
    .module(Module("example").route_prefix("/example"))
    .integrate(Integration.di(auto_wire=True))
)

manifest = AppManifest(
    name="example",
    version="1.0.0",
    controllers=["modules.example.controllers:ExampleController"],
    services=["modules.example.services:ExampleService"],
)
```

## Controller Pattern From Checked Examples

```python
from aquilia import Controller, GET, POST, RequestCtx, Response

class ProjectsController(Controller):
    prefix = "/"

    @GET("/")
    async def list_projects(self, ctx: RequestCtx):
        return Response.json({"items": []})

    @POST("/", status_code=201)
    async def create_project(self, ctx: RequestCtx):
        body = await ctx.json()
        return Response.json(body, status=201)
```

## Verification

- Run `python -m aquilia.cli.__main__ --help` to confirm CLI availability.
- Run `aq validate` in a workspace to validate manifest paths.
- Run related tests under `tests/` or `examples/*/tests/` for executable behavior.
