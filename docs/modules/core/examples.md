# Core Examples

Root framework runtime files: ASGI adapter, server, runtime bootstrap, config, pyconfig, request/response, middleware, lifecycle, signing, effects, dotenv, uploads, and data structures.

Examples here use public symbols and checked patterns from the repository. When a module has no safe standalone constructor example, the example focuses on importing and wiring the actual source-backed API.

## Source-Backed Import Examples

```python
from aquilia._datastructures import MultiDict
from aquilia._datastructures import Headers
from aquilia._datastructures import parse_date_header
from aquilia._uploads import UploadFile
from aquilia._uploads import FormData
from aquilia._uploads import create_upload_file_from_bytes
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
