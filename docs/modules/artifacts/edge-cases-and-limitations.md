# Artifacts Edge Cases And Limitations

## Fault And Error Types

The following error-oriented classes are present in the implementation and should guide defensive usage.

| Type | Source | Meaning |
| --- | --- | --- |
| None detected |  |  |

## Common Edge Cases

- Optional dependencies may change behavior. Check imports and constructor docs before enabling production features.
- In-memory stores, queues, caches, adapters, and registries are usually process-local. Use durable backends when state must survive restarts or scale across workers.
- Request-scoped data must not be cached globally. Use request state, DI request scopes, or explicit parameters.
- Decorators in Aquilia generally attach metadata at import time. Runtime behavior happens later during compilation, routing, middleware execution, or service startup.
- Many subsystems intentionally convert invalid states into typed faults. Catch the specific fault type when application code can recover.

## Source-Level Limits To Review

Review these files before changing behavior:

- `aquilia/artifacts/__init__.py`: Aquilia Artifacts -- Unified artifact system for the framework.
- `aquilia/artifacts/builder.py`: Artifact Builder -- fluent API for constructing artifacts.
- `aquilia/artifacts/core.py`: Artifact Core -- the foundational types for Aquilia's artifact system.
- `aquilia/artifacts/kinds.py`: Typed Artifact Kinds -- convenience subclasses with kind-specific helpers.
- `aquilia/artifacts/reader.py`: Artifact Reader -- load, inspect, verify, and query artifacts.
- `aquilia/artifacts/store.py`: Artifact Store -- pluggable storage backends for artifacts.
