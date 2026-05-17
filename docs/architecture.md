# Aquilia Architecture

Aquilia is a manifest-first, async-native Python framework. The implementation splits responsibilities across workspace configuration, module manifests, registry compilation, DI setup, controller routing, middleware, ASGI adaptation, and optional subsystems.

## Runtime Path

1. `workspace.py` declares a `Workspace` with `Module` pointers and `Integration` objects.
2. Each module exposes `modules/<name>/manifest.py` with an `AppManifest` that lists controllers, services, models, socket controllers, middleware, tasks, faults, templates, and metadata.
3. `AquiliaRuntime.configure()` inserts the workspace root into `sys.path`, sets `AQUILIA_ENV` and `AQUILIA_WORKSPACE`, configures logging, and loads config through `ConfigLoader`.
4. `AquiliaRuntime.discover()` extracts workspace/module names, imports module manifests, performs dynamic module discovery, rebuilds the apps namespace, and loads workspace module configuration.
5. `AquiliaRuntime.bootstrap()` constructs `AquiliaServer` with manifests, config, registry mode, and workspace module metadata.
6. `AquiliaServer` builds the Aquilary registry, runtime registry, DI containers, lifecycle coordinator, middleware stack, socket runtime, controller compiler/router/engine, and optional subsystem services.
7. `ASGIAdapter` receives HTTP, WebSocket, and lifespan scopes.
8. HTTP requests are matched by `ControllerRouter`, wrapped by middleware, executed by `ControllerEngine`, and serialized by `Response`.
9. Lifespan startup loads controllers, admin routes, OpenAPI docs, models, lifecycle hooks, effects, cache, storage, mail, tasks, health state, and optional subsystems.

## Workspace Versus Module Manifest

`Workspace` is orchestration: runtime mode, modules, integrations, sessions, security, telemetry, database, MLOps, and env config. `Module` in `workspace.py` is a pointer with route prefix, dependencies, tags, lifecycle, and optional module database override.

`AppManifest` is module internals: controllers, services, socket controllers, models, serializers, guards, pipes, interceptors, middleware, sessions, templates, fault handlers, background tasks, features, imports/exports, and discovery settings.

## HTTP Request Flow

1. `ASGIAdapter.handle_http()` builds the middleware chain once and caches it.
2. The built-in `/_health` endpoint is served before the normal middleware path and only supports GET/HEAD.
3. `Request` wraps the ASGI scope and receive callable.
4. API version inputs are pre-resolved for URL-path matching when versioning is active.
5. `ControllerRouter.match_sync()` selects a route; HEAD can fall back to GET and strip the response body.
6. The adapter creates a request-scoped DI container and pooled controller `RequestCtx`.
7. Middleware descriptors execute in scope/priority order.
8. The final handler calls `ControllerEngine.execute()` with the compiled route, request, path params, and request container.
9. Fault middleware and exception handling convert faults/exceptions to structured JSON or HTML error pages.
10. `Response.send_asgi()` emits ASGI response events.

## Built-In Runtime Behavior

- `/_health` returns engine metrics and subsystem health, with no-store and security headers.
- OpenAPI routes are registered at `/openapi.json`, `/docs`, and `/redoc` when docs are enabled.
- Admin routes are injected into the controller router when `Integration.admin(...)` is configured.
- Static `assets/` can be auto-mounted under `/static` for admin assets when needed.
- Dev/test/local modes can force session cookies to insecure mode so browser sessions work on plain HTTP.
- Optional subsystem startup failures for mail, cache, tasks, storage, and effects are logged as non-fatal where the implementation catches them.

## Module Documentation

Use [module-index.md](module-index.md) for every module and [runtime-lifecycle.md](runtime-lifecycle.md) for phase-by-phase details.
