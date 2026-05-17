# Aquilia Architecture

Aquilia is a manifest-first async Python framework. The repository shows a clear separation between application structure, module internals, runtime compilation, request handling, and subsystem wiring.

## The Big Picture

A normal application moves through this path:

1. `workspace.py` defines a `Workspace` with `Module` pointers and integrations.
2. Each application module exposes `modules/<name>/manifest.py` with an `AppManifest`.
3. `AquiliaRuntime` reads the workspace, discovers manifests, and creates an `AquiliaServer`.
4. `AquiliaServer` builds the Aquilary registry, runtime registry, DI containers, lifecycle coordinator, middleware stack, controller compiler, controller router, controller engine, and socket runtime.
5. `ASGIAdapter` receives HTTP, WebSocket, and lifespan scopes.
6. HTTP requests become `Request` objects and controller `RequestCtx` instances.
7. Middleware wraps the matched controller handler.
8. Handlers return `Response` objects or data that the controller engine can render.
9. Faults are converted into structured responses by the fault middleware and response mapping layer.

## Workspace Versus Module Manifest

The source tree consistently treats the workspace as an orchestration layer. A `Module` in `workspace.py` is a pointer with routing, tags, dependency metadata, and lifecycle hints. Component declarations belong in `AppManifest` inside the module directory.

This split matters because it lets teams own modules independently. A workspace can import modules, route them, and configure shared integrations without having to know the implementation details of each module.

## Runtime Phases

`AquiliaRuntime` has explicit phases: created, configuring, discovering, bootstrapping, ready, running, shutting down, stopped, and failed. The phase model keeps boot deterministic and makes it easier to identify whether a problem came from configuration, discovery, DI registration, route compilation, startup hooks, or request execution.

## Request Flow

HTTP requests flow through these pieces:

1. `ASGIAdapter.handle_http` creates a `Request` from the ASGI scope and receive function.
2. The adapter resolves versioning inputs when versioning is enabled.
3. The controller router matches method and path.
4. A pooled controller `RequestCtx` is acquired.
5. Middleware is executed in priority order.
6. `ControllerEngine.execute` creates or reuses controller instances through `ControllerFactory`, applies route metadata, and calls the handler.
7. `Response` serializes JSON, text, HTML, streaming content, files, SSE, cookies, redirects, and cache headers back to ASGI send events.

## Dependency Injection

The DI package provides providers, scopes, request DAGs, lifecycle disposal, diagnostics, and test registries. The server creates app containers from runtime metadata and request scopes per request. Controllers and services should depend on constructor parameters where possible, then use request state only for request-specific facts such as identity, session, tenant, or correlation data.

## Fault Model

Aquilia uses structured fault classes instead of raw exceptions for framework behavior. Faults carry domain, severity, metadata, recovery strategy, and response mapping information. This makes operational behavior inspectable and helps avoid leaking unsafe exception details in production responses.

## Controller Contracts

Controllers use decorators such as `GET`, `POST`, `PUT`, `PATCH`, `DELETE`, `WS`, and `route`. Decorators only attach metadata. Compilation happens later, after manifests and runtime registries are loaded. Route metadata supports OpenAPI summaries, descriptions, response models, request and response blueprints, filters, search, ordering, pagination, renderers, throttles, timeouts, and API versions.

## Blueprints

Blueprints are input and output contracts. They cast inbound data, seal it with validation, mold outbound objects, support projections, and can imprint data into model instances. They are not just serializers. They are framework primitives used by controllers, OpenAPI generation, and model-facing code.

## Background Work

The tasks subsystem defines async task descriptors through `@task`. `TaskManager` binds descriptors on startup, starts worker loops, handles retries, schedules periodic jobs, cleans old terminal jobs, and reports stats. The default memory backend is useful for development and tests. More durable deployments should use a backend that survives process restarts.

## WebSockets

Socket controllers use `Socket`, `OnConnect`, `OnDisconnect`, `Event`, `AckEvent`, `Subscribe`, and `Unsubscribe`. A socket connection has connection state, rooms, identity, session, DI container, and adapter access. The runtime can stream chunks from sync or async iterators and can send acknowledgements when requested.

## Operational Rule Of Thumb

Keep framework boundary code boring:

- Workspace config should be declarative.
- Manifests should point to components.
- Controllers should validate transport shape and call services.
- Services should own business rules.
- Background tasks should be idempotent where possible.
- WebSocket handlers should validate event payloads and avoid long blocking work.
- Faults should carry stable codes and actionable metadata.
