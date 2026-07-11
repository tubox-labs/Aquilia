---
name: aquilia-controller-api-builder
description: "Build Aquilia HTTP APIs with Controller, RequestCtx, Response, route decorators, contracts, filters, pagination, renderers, OpenAPI metadata, and route debugging. Use for controller methods and request/response behavior."
---

# Aquilia Controller Api Builder

## Purpose
Implement Aquilia-native HTTP controllers that compile into `ControllerRouter` routes and execute through `ControllerEngine`.

## Trigger Conditions
Use for API endpoints, CRUD controllers, request parsing, response formatting, route decorators, OpenAPI metadata, filters, pagination, content negotiation, or controller route debugging.

## Inputs
- Controller class name, prefix, tags, HTTP methods, paths, and path parameter types.
- Request body and response shape.
- Optional request/response contracts, filters, search, ordering, pagination, renderers, throttles, timeouts, and version binding.

## Execution Flow
1. Subclass `Controller` and set `prefix` and `tags` when useful.
2. Use `@GET`, `@POST`, `@PUT`, `@PATCH`, `@DELETE`, `@HEAD`, `@OPTIONS`, or `@TRACE` with paths such as `/`, `/<key:str>`, or `/<id:int>`.
3. Accept `ctx: RequestCtx` for query/body/header/session/auth access.
4. Return `Response.json(...)` or a value convertible by `ControllerEngine._to_response()`.
5. Inject services through `__init__` type hints when they are registered in `AppManifest.services` or auto-discovered.

## Constraints
- Do not manually register routes in `workspace.py`.
- Keep handlers async unless there is a deliberate compatibility reason.
- `ASGIAdapter` handles HEAD fallback to GET when a GET route exists.

## Implementation Anchors
`aquilia/controller/decorators.py`, `aquilia/controller/base.py`, `aquilia/controller/compiler.py`, `aquilia/controller/router.py`, `aquilia/controller/engine.py`, `aquilia/response.py`, `examples/crud_app/modules/projects/controllers.py`.

## Examples
- Implement `GET /projects/<key:str>` returning `Response.json(await service.get_project(key))`.
- Add `@POST("/", status_code=201)` and validate `await ctx.json()` with a Contract.
- Bind a route with `version="2.0"` for version-aware matching.

## Failure Handling
A 404 means no route matched method/path/version. A 405 means path matched but method did not. DI errors usually come from unregistered constructor type hints. Use `aq inspect routes` and controller compiler metadata when available.
