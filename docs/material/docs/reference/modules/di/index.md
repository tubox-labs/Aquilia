# DI Module

> `aquilia.di` — Scoped dependency injection with hierarchical containers

The DI module provides a hierarchical dependency injection system with `singleton`, `app`, and `request` scopes. Providers resolve dependencies from class instances, factory functions, values, pools, aliases, and scoped containers.

## When to Use

Use the DI module when you need:

- Automatic dependency wiring for services and controllers
- Per-request isolation of stateful services
- Test-friendly dependency overriding
- Annotation-driven injection in controller methods

## Key Classes

| Class | Purpose |
|---|---|
| `Container` | DI container with scoped resolution |
| `Registry` | Provider registry (aliased as `DIRegistry` at top level) |
| `ClassProvider` | Creates instances from classes |
| `FactoryProvider` | Creates instances from factory functions |
| `ValueProvider` | Returns pre-created values |
| `PoolProvider` | Object pool with configurable size |
| `AliasProvider` | Maps one service name to another |
| `ScopedProvider` | Creates per-scope singleton instances |
| `RequestDAG` | Resolved dependency graph for a request |

## Decorators

| Decorator | Purpose |
|---|---|
| `@service` | Register a class as a DI service |
| `@factory` | Register a function as a DI factory |
| `@inject` | Inject dependencies into a function |
| `Inject` | Class-level injection marker |

## Quick Example

```python
from aquilia.di import Container, service, inject, Inject, Dep

# Register services
@service(scope="singleton")
class Database:
    async def execute(self, sql): ...

@service(scope="request")
class UsersService:
    db: Database = Inject()

    async def get_user(self, user_id: str):
        return await self.db.execute("SELECT * FROM users WHERE id = ?", user_id)

# Inject into controller method
@inject
async def handler(ctx, service: UsersService = Dep()):
    user = await service.get_user("42")
    return Response.json(user)
```

## Import Path

```python
from aquilia.di import (
    Container,
    Registry,
    ClassProvider,
    FactoryProvider,
    ValueProvider,
    Provider,
    service,
    factory,
    inject,
    Inject,
    Dep,
)
```

## Related Modules

- [core/server](../core/server.md) — DI container built during server bootstrap
- [core/manifest](../core/manifest.md) — Services declared in AppManifest
- [integrations](../integrations/index.md) — DiIntegration config builder