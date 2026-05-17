# Providers Documentation

Cloud provider clients and deployment tooling, currently focused on the Render provider and encrypted credential store.

## Coverage Snapshot

- Source files: 11
- Source lines: 5882
- Public classes: 72
- Public module functions: 0
- Constants/module flags: 42
- Public exports in `__all__`: 61

## Source Files Read

- `aquilia/providers/__init__.py`: Aquilia Cloud Providers — Pluggable PaaS/IaaS Deployment Backends.
- `aquilia/providers/render/__init__.py`: Aquilia Render Provider — Comprehensive PaaS Deployment v2.
- `aquilia/providers/render/client.py`: Render REST API Client — Comprehensive v2.
- `aquilia/providers/render/deployer.py`: Render Deployment Orchestrator — Enhanced v2.
- `aquilia/providers/render/store.py`: Render Credential Store — Military-Grade Encrypted Token Persistence.
- `aquilia/providers/render/types.py`: Render API Type Definitions — Comprehensive v2.
- `aquilia/providers/render_backup_phase10/__init__.py`: Aquilia Render Provider — One-command PaaS deployment.
- `aquilia/providers/render_backup_phase10/client.py`: Render REST API Client.
- `aquilia/providers/render_backup_phase10/deployer.py`: Render Deployment Orchestrator.
- `aquilia/providers/render_backup_phase10/store.py`: Render Credential Store — Surp-Encrypted Token Persistence.
- `aquilia/providers/render_backup_phase10/types.py`: Render API Type Definitions.

## Document Map

- `architecture.md`: module boundaries, dependencies, lifecycle, and extension points.
- `configuration.md`: configuration classes, builders, server wiring, and precedence.
- `api-reference.md`: source-extracted classes, methods, functions, constants, exports, and signatures.
- `integration-guide.md`: how to wire the module into an Aquilia app.
- `cli-reference.md`: mounted `aq` commands for this module, if any.
- `examples.md`: usage examples derived from source and checked example apps.
- `edge-cases-and-limitations.md`: implementation limits and compatibility behavior.
- `troubleshooting.md`: diagnostic commands and common failure patterns.
