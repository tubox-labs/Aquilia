---
name: aquilia-di-service-builder
description: "Create and debug Aquilia dependency injection providers, services, factories, scopes, request scopes, lifecycle hooks, Inject annotations, and DI diagnostics. Use for service construction and provider resolution issues."
---

# Aquilia Di Service Builder

## Purpose
Register and resolve Aquilia services consistently through the scoped DI container.

## Trigger Conditions
Use when adding services, factories, provider bindings, constructor injection, request-scoped dependencies, lifecycle hooks, or debugging `ProviderNotFoundError`, scope warnings, or DI cycles.

## Inputs
- Service classes/factories and constructor type hints.
- Desired scope: `singleton`, `app`, `request`, `transient`, `pooled`, or `ephemeral`.
- Optional `Annotated[..., inject(...)]` token/tag/optional metadata.

## Execution Flow
1. Add service import paths to `AppManifest.services` or rely on auto-discovery for classes ending in `Service` or decorated with `@service`.
2. Use `@service(scope="app")`, `@factory(...)`, `@provides(...)`, and `inject(...)` where explicit DI metadata is needed.
3. Let `AquiliaServer` call `RuntimeRegistry._register_services()` before controller factory creation.
4. Resolve dependencies with `await container.resolve_async(Type)` in async code.
5. Use request scopes from `Container.create_request_scope()` for per-request values.

## Constraints
- Do not call sync `resolve()` from an async context; `Container` raises `DIResolutionFault`.
- Avoid captive dependencies: request/ephemeral providers resolved into singleton/app containers produce warnings.
- Manifest import paths are validated to block dangerous module imports.

## Implementation Anchors
`aquilia/di/core.py`, `aquilia/di/providers.py`, `aquilia/di/decorators.py`, `aquilia/di/diagnostics.py`, `aquilia/aquilary/core.py`, `tests/test_di_system.py`.

## Examples
- Register `modules.orders.services:OrdersService` and inject it into `OrdersController.__init__`.
- Use `Annotated[Repository, inject(tag="readonly")]` for tagged dependencies.
- Add `async_init`, `on_startup`, or `on_shutdown` to a service that owns resources.

## Failure Handling
For missing providers, inspect `manifest.services`, auto-discovery, and type hints. For cycles, inspect `ResolveCtx.stack` or DI diagnostics. If a string annotation fails to resolve, prefer real imported types or controlled `get_type_hints` compatible annotations.
