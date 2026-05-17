# Providers Edge Cases And Limitations

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

- `aquilia/providers/__init__.py`: Aquilia Cloud Providers - Pluggable PaaS/IaaS Deployment Backends.
- `aquilia/providers/render/__init__.py`: Aquilia Render Provider - Comprehensive PaaS Deployment v2.
- `aquilia/providers/render/client.py`: Render REST API Client - Comprehensive v2.
- `aquilia/providers/render/deployer.py`: Render Deployment Orchestrator - Enhanced v2.
- `aquilia/providers/render/store.py`: Render Credential Store - Military-Grade Encrypted Token Persistence.
- `aquilia/providers/render/types.py`: Render API Type Definitions - Comprehensive v2.
- `aquilia/providers/render_backup_phase10/__init__.py`: Aquilia Render Provider - One-command PaaS deployment.
- `aquilia/providers/render_backup_phase10/client.py`: Render REST API Client.
- `aquilia/providers/render_backup_phase10/deployer.py`: Render Deployment Orchestrator.
- `aquilia/providers/render_backup_phase10/store.py`: Render Credential Store - Crous-Encrypted Token Persistence.
- `aquilia/providers/render_backup_phase10/types.py`: Render API Type Definitions.
