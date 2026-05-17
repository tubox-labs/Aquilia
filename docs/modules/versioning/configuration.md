# Versioning Configuration

API version parsing, resolvers, decorators, negotiation, graph, sunset policy/enforcement, middleware, and route registration integration.

This page distinguishes direct configuration APIs from indirect runtime wiring. All class names and source files below are extracted from the current source tree.

## Configuration Model

This module exposes config-oriented public classes. Use the table below to locate exact constructors and `to_dict()` behavior in `api-reference.md`.

## Source Inventory

| File | Lines | Public classes | Public functions | Purpose |
| --- | ---: | ---: | ---: | --- |
| `aquilia/versioning/__init__.py` | 181 | 0 | 0 | Aquilia Versioning System — Epoch-Based API Versioning |
| `aquilia/versioning/core.py` | 290 | 3 | 0 | Aquilia Versioning — Core Types |
| `aquilia/versioning/decorators.py` | 138 | 0 | 3 | Aquilia Versioning — Route-Level Decorators |
| `aquilia/versioning/errors.py` | 144 | 6 | 0 | Aquilia Versioning — Version Errors |
| `aquilia/versioning/graph.py` | 261 | 2 | 0 | Aquilia Versioning — Version Graph |
| `aquilia/versioning/middleware.py` | 223 | 1 | 0 | Aquilia Versioning — Version Middleware |
| `aquilia/versioning/negotiation.py` | 193 | 2 | 0 | Aquilia Versioning — Version Negotiation |
| `aquilia/versioning/parser.py` | 137 | 2 | 0 | Aquilia Versioning — Version Parser |
| `aquilia/versioning/resolvers.py` | 486 | 8 | 0 | Aquilia Versioning — Version Resolvers |
| `aquilia/versioning/strategy.py` | 500 | 2 | 0 | Aquilia Versioning — Version Strategy |
| `aquilia/versioning/sunset.py` | 291 | 4 | 0 | Aquilia Versioning — Sunset Lifecycle |

## Detected Config-Oriented Classes

| Class | Source | Methods | Summary |
| --- | --- | --- | --- |
| `VersionMiddleware` | `aquilia/versioning/middleware.py` |  | Middleware that resolves API version for every request. |
| `VersionConfig` | `aquilia/versioning/strategy.py` | `to_dict` | Complete versioning configuration. |
| `SunsetPolicy` | `aquilia/versioning/sunset.py` | `to_dict` | Global sunset policy configuration. |

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
