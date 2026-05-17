# Faults Configuration

Structured fault taxonomy, domains, handlers, middleware, response mapping, and subsystem patch integrations.

This page distinguishes direct configuration APIs from indirect runtime wiring. All class names and source files below are extracted from the current source tree.

## Configuration Model

This module exposes config-oriented public classes. Use the table below to locate exact constructors and `to_dict()` behavior in `api-reference.md`.

## Source Inventory

| File | Lines | Public classes | Public functions | Purpose |
| --- | ---: | ---: | ---: | --- |
| `aquilia/faults/__init__.py` | 292 | 0 | 0 | AquilaFaults - Production-grade fault handling system. |
| `aquilia/faults/core.py` | 490 | 8 | 0 | AquilaFaults - Core types and fault taxonomy. |
| `aquilia/faults/default_handlers.py` | 535 | 8 | 0 | AquilaFaults - Default Handlers. |
| `aquilia/faults/domains.py` | 1540 | 92 | 1 | AquilaFaults - Domain-specific fault types. |
| `aquilia/faults/engine.py` | 499 | 2 | 2 | AquilaFaults - Fault Engine. |
| `aquilia/faults/handlers.py` | 193 | 3 | 0 | AquilaFaults - Fault handlers. |
| `aquilia/faults/integrations/__init__.py` | 130 | 0 | 2 | AquilaFaults - Subsystem Integrations. |
| `aquilia/faults/integrations/di.py` | 185 | 3 | 2 | AquilaFaults - DI Integration. |
| `aquilia/faults/integrations/flow.py` | 355 | 3 | 7 | AquilaFaults - Flow Engine Integration. |
| `aquilia/faults/integrations/models.py` | 223 | 1 | 4 | AquilaFaults - Model/Database Integration. |
| `aquilia/faults/integrations/registry.py` | 148 | 4 | 2 | AquilaFaults - Registry Integration. |
| `aquilia/faults/integrations/routing.py` | 211 | 3 | 3 | AquilaFaults - Routing Integration. |

## Detected Config-Oriented Classes

| Class | Source | Methods | Summary |
| --- | --- | --- | --- |
| `ConfigFault` | `aquilia/faults/domains.py` |  | Base class for configuration faults. |
| `ConfigMissingFault` | `aquilia/faults/domains.py` |  | Required configuration is missing. |
| `ConfigInvalidFault` | `aquilia/faults/domains.py` |  | Configuration value is invalid. |
| `ProviderNotFoundFault` | `aquilia/faults/domains.py` |  | DI provider not found. |
| `MiddlewareFault` | `aquilia/faults/domains.py` |  | Middleware execution failed. |
| `ProviderFault` | `aquilia/faults/domains.py` |  | Base class for cloud provider integration faults. |
| `ProviderAPIFault` | `aquilia/faults/domains.py` |  | Cloud provider API returned an error response. |
| `ProviderAuthFault` | `aquilia/faults/domains.py` |  | Cloud provider authentication failure (401/403). |
| `ProviderRateLimitFault` | `aquilia/faults/domains.py` |  | Cloud provider rate limit exceeded (429). |
| `ProviderTokenFault` | `aquilia/faults/domains.py` |  | Provider API token is missing, invalid, or expired. |
| `ProviderCredentialFault` | `aquilia/faults/domains.py` |  | Credential storage or retrieval failure. |
| `ProviderConnectionFault` | `aquilia/faults/domains.py` |  | Network connection to provider API failed. |
| `DeployConfigFault` | `aquilia/faults/domains.py` |  | Deployment configuration is invalid or incomplete. |
| `FaultMiddleware` | `aquilia/faults/engine.py` |  | Middleware that bridges the FaultEngine with the request/response lifecycle. |
| `ProviderRegistrationFault` | `aquilia/faults/integrations/di.py` |  | Provider registration failed. |
| `MiddlewareChainFault` | `aquilia/faults/integrations/flow.py` |  | Middleware chain execution failed. |

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
