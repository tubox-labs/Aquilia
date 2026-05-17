# Providers Architecture

Cloud provider clients and deployment tooling, currently focused on the Render provider and encrypted credential store.

## Source Boundaries

| File | Lines | Classes | Functions | Purpose |
| --- | ---: | ---: | ---: | --- |
| `aquilia/providers/__init__.py` | 21 | 0 | 0 | Aquilia Cloud Providers — Pluggable PaaS/IaaS Deployment Backends. |
| `aquilia/providers/render/__init__.py` | 153 | 0 | 0 | Aquilia Render Provider — Comprehensive PaaS Deployment v2. |
| `aquilia/providers/render/client.py` | 1406 | 1 | 0 | Render REST API Client — Comprehensive v2. |
| `aquilia/providers/render/deployer.py` | 661 | 2 | 0 | Render Deployment Orchestrator — Enhanced v2. |
| `aquilia/providers/render/store.py` | 752 | 1 | 0 | Render Credential Store — Military-Grade Encrypted Token Persistence. |
| `aquilia/providers/render/types.py` | 993 | 53 | 0 | Render API Type Definitions — Comprehensive v2. |
| `aquilia/providers/render_backup_phase10/__init__.py` | 53 | 0 | 0 | Aquilia Render Provider — One-command PaaS deployment. |
| `aquilia/providers/render_backup_phase10/client.py` | 571 | 1 | 0 | Render REST API Client. |
| `aquilia/providers/render_backup_phase10/deployer.py` | 544 | 2 | 0 | Render Deployment Orchestrator. |
| `aquilia/providers/render_backup_phase10/store.py` | 344 | 1 | 0 | Render Credential Store — Surp-Encrypted Token Persistence. |
| `aquilia/providers/render_backup_phase10/types.py` | 384 | 11 | 0 | Render API Type Definitions. |

## Internal Shape

`providers` has 11 Python files, 72 public classes, 0 public module-level functions, and 42 constants or module flags detected by AST.

## Runtime Responsibilities

- This module has `aq` command coverage documented in `cli-reference.md`; 16 commands map to this subsystem.

## Internal Imports

| Import | Count |
| --- | ---: |
| `.types` | 6 |
| `aquilia.faults.domains` | 6 |
| `.client` | 4 |
| `.deployer` | 2 |
| `.store` | 2 |

## External And Stdlib Imports

| Import root | Count |
| --- | ---: |
| `__future__` | 8 |
| `typing` | 8 |
| `logging` | 6 |
| `time` | 6 |
| `urllib` | 6 |
| `dataclasses` | 4 |
| `json` | 4 |
| `pathlib` | 4 |
| `collections` | 2 |
| `contextlib` | 2 |
| `enum` | 2 |
| `hashlib` | 2 |
| `hmac` | 2 |
| `os` | 2 |
| `platform` | 2 |
| `secrets` | 2 |
| `ssl` | 2 |
| `struct` | 2 |
| `subprocess` | 2 |
| `ctypes` | 1 |
| `datetime` | 1 |
| `sys` | 1 |

## Lifecycle And Extension Points

| Extension Type | Source | Role |
| --- | --- | --- |
| `RenderCredentialStore` | `aquilia/providers/render/store.py` | Military-grade, file-based credential store for Render API tokens. |
| `RenderRegistryCredential` | `aquilia/providers/render/types.py` | Private container registry credential. |
| `RenderDeployConfig` | `aquilia/providers/render/types.py` | Complete deployment configuration for ``aq deploy render``. |
| `RenderCredentialStore` | `aquilia/providers/render_backup_phase10/store.py` | Secure, file-based credential store for Render API tokens. |
| `RenderDeployConfig` | `aquilia/providers/render_backup_phase10/types.py` | Complete deployment configuration for ``aq deploy render``. |

## Error Handling

This module does not define public `Fault` or `Error` classes in its own files. Errors are usually raised through shared `aquilia.faults` domains or consuming subsystems.
