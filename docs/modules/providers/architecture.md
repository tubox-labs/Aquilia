# Providers Architecture

## Runtime Role

Deployment provider clients and data types, currently centered on Render deployment configuration, API client behavior, deployer orchestration, and credential storage.

The implementation is split across 11 Python files. The module boundary is visible in the file inventory below and the API reference is generated from the same source files.

## Primary Source Files

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

## Internal Dependency Shape

The table below is derived from import statements in the module. It shows which top-level packages this module depends on most often.

| Imported package | Import count |
| --- | --- |
| `__future__` | 8 |
| `typing` | 8 |
| `aquilia` | 6 |
| `logging` | 6 |
| `time` | 6 |
| `types` | 6 |
| `urllib` | 6 |
| `client` | 4 |
| `dataclasses` | 4 |
| `json` | 4 |
| `pathlib` | 4 |
| `collections` | 2 |
| `contextlib` | 2 |
| `deployer` | 2 |
| `enum` | 2 |
| `hashlib` | 2 |
| `hmac` | 2 |
| `os` | 2 |
| `platform` | 2 |
| `secrets` | 2 |
| `ssl` | 2 |
| `store` | 2 |
| `struct` | 2 |
| `subprocess` | 2 |
| `ctypes` | 1 |
| `datetime` | 1 |
| `sys` | 1 |

## Data And Control Flow

1. Configuration or direct construction creates the public service objects, controllers, providers, or helpers for this module.
2. Runtime code imports the registered classes from manifests, workspace integrations, middleware stacks, or direct application code.
3. Public methods perform validation and convert invalid states into typed Aquilia faults where the implementation defines fault classes.
4. Integration points return Python data structures, `Response` objects, provider results, jobs, sessions, connections, or model instances depending on the subsystem.

## Boundary Rules

- Keep application-specific business decisions outside framework classes unless the class is explicitly a service or controller owned by your app.
- Prefer the public exports and typed configuration dataclasses shown in `api-reference.md`.
- When a module supplies both a low-level primitive and a high-level service, use the service in application code and keep primitives for tests, providers, or advanced integrations.
