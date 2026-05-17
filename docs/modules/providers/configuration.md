# Providers Configuration

Cloud provider clients and deployment tooling, currently focused on the Render provider and encrypted credential store.

This page distinguishes direct configuration APIs from indirect runtime wiring. All class names and source files below are extracted from the current source tree.

## Configuration Model

This module exposes config-oriented public classes. Use the table below to locate exact constructors and `to_dict()` behavior in `api-reference.md`.

## Source Inventory

| File | Lines | Public classes | Public functions | Purpose |
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
| `aquilia/providers/render_backup_phase10/store.py` | 344 | 1 | 0 | Render Credential Store — Crous-Encrypted Token Persistence. |
| `aquilia/providers/render_backup_phase10/types.py` | 384 | 11 | 0 | Render API Type Definitions. |

## Detected Config-Oriented Classes

| Class | Source | Methods | Summary |
| --- | --- | --- | --- |
| `RenderNotificationSettings` | `aquilia/providers/render/types.py` |  | Notification settings for a service. |
| `RenderDeployConfig` | `aquilia/providers/render/types.py` | `to_service_payload`, `to_update_payload`, `from_workspace_context` | Complete deployment configuration for ``aq deploy render``. |
| `RenderDeployConfig` | `aquilia/providers/render_backup_phase10/types.py` | `to_service_payload`, `to_update_payload`, `from_workspace_context` | Complete deployment configuration for ``aq deploy render``. |

## Runtime Wiring Paths

- `workspace.py` defines workspace-level structure with `Workspace`, `Module`, and `Integration` builders.
- `modules/<name>/manifest.py` defines module internals with `AppManifest`.
- `ConfigLoader.get(...)` resolves dotted configuration paths at runtime.
- `AquiliaServer` consumes resolved config during middleware and subsystem setup.
- Subsystems with optional providers only require optional dependencies when their backend/provider is configured.

## Verification Checklist

1. Run `aq validate` to verify manifests.
2. Run `aq inspect config` to inspect resolved configuration.
3. Run `aq doctor` for workspace and integration diagnostics.
4. For server-only wiring, start via `aq run` and check startup logs plus `GET /_health`.

## Related Pages

- `api-reference.md` for exact class fields, methods, constants, and signatures.
- `integration-guide.md` for the workspace/manifest wiring pattern.
- `edge-cases-and-limitations.md` for fallback and compatibility behavior.
