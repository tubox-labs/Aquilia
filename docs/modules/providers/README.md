# Providers Documentation

This directory is the professional documentation set for `providers`. It is implementation-driven and aligned with the current source files under `aquilia/providers`.

## What This Covers

Deployment provider clients and data types, currently centered on Render deployment configuration, API client behavior, deployer orchestration, and credential storage.

## Source Files Read

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

## Document Map

- `architecture.md`: Runtime architecture and module boundaries
- `configuration.md`: Configuration entry points, datatypes, and precedence
- `api-reference.md`: Classes, methods, functions, constants, and data fields extracted from source
- `integration-guide.md`: How to wire the module into a real Aquilia application
- `cli-reference.md`: Command line surface and operational commands
- `edge-cases-and-limitations.md`: Known edge cases and implementation limits
- `troubleshooting.md`: Common failures and diagnosis steps
- `examples.md`: Code examples and usage patterns

## Public Surface Snapshot

- Python files: 11
- Public classes: 72
- Configuration or dataclass-like types: 42
- Public functions: 0
- Constants detected: 33

## Fast Start

```python
from aquilia.providers import RenderClient, DeployResult, RenderDeployer, RenderCredentialStore

# The imported symbols above are public exports from this module.
# See api-reference.md for constructor signatures, methods, and data fields.
```

## Read Next

Start with `architecture.md` if you are learning how the subsystem fits into runtime boot. Use `api-reference.md` when you need exact methods, datatypes, and class fields. Use `examples.md` for copyable patterns that match the current code.
