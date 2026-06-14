# Aquilary Module

> `aquilia.aquilary` — Manifest-driven application registry

Aquilary is the core registry engine that reads module manifests, validates the component graph, resolves dependencies, and compiles the runtime structures needed by the rest of the framework.

## When to Use

Aquilary operates automatically during bootstrap. You interact with it when:

- Debugging module discovery issues
- Inspecting the dependency graph via `aq inspect`
- Writing custom registry validators
- Understanding frozen artifacts (which are serialized Aquilary state)

## Architecture

```
AppManifest → ManifestLoader → Aquilary → AquilaryRegistry → RuntimeRegistry
                                                                    │
                                                    ┌───────────────┼───────────────┐
                                                    │               │               │
                                              DependencyGraph  RouteCompiler  RegistryValidator
```

## Key Classes

| Class | Purpose |
|---|---|
| `Aquilary` | Top-level metadata container for the application |
| `AquilaryRegistry` | Validates and stores all module manifests |
| `RuntimeRegistry` | Compiles manifests into DI containers and routes |
| `ManifestLoader` | Loads and validates `manifest.py` files |
| `DependencyGraph` | Resolves provider/service dependency DAG |
| `RouteCompiler` | Compiles controller routes into a route table |
| `RegistryValidator` | Validates registry integrity (cycles, conflicts) |
| `FingerprintGenerator` | Creates content hashes for artifact integrity |
| `RegistryMode` | DEV, PROD, or TEST — controls validation strictness |

## Import Path

```python
from aquilia.aquilary import (
    Aquilary,
    AquilaryRegistry,
    RuntimeRegistry,
    RegistryMode,
    DependencyGraph,
    RouteCompiler,
    RegistryValidator,
    FingerprintGenerator,
)
```

## Related Modules

- [core/manifest](../core/manifest.md) — `AppManifest` feeds into Aquilary
- [core/server](../core/server.md) — How `AquiliaServer` builds the registry
- [artifacts](../artifacts/index.md) — Frozen snapshots of registry state
- [discovery](../discovery/index.md) — Auto-discovery feeds the registry