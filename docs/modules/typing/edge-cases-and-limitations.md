# Typing Contracts Edge Cases And Limitations

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

- `aquilia/typing/__init__.py`: Implementation file.
- `aquilia/typing/asgi.py`: Implementation file.
- `aquilia/typing/common.py`: Implementation file.
- `aquilia/typing/config.py`: Configuration type definitions for Aquilia.
- `aquilia/typing/container.py`: Implementation file.
- `aquilia/typing/controller.py`: Implementation file.
- `aquilia/typing/effects.py`: Implementation file.
- `aquilia/typing/manifest.py`: Implementation file.
- `aquilia/typing/middleware.py`: Implementation file.
- `aquilia/typing/request_state.py`: Implementation file.
