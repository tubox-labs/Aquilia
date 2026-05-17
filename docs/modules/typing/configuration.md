# Typing Configuration

Shared protocols, typed dictionaries, aliases, and interface contracts for ASGI, containers, config, controllers, effects, manifests, middleware, and request state.

This page distinguishes direct configuration APIs from indirect runtime wiring. All class names and source files below are extracted from the current source tree.

## Configuration Model

This module exposes config-oriented public classes. Use the table below to locate exact constructors and `to_dict()` behavior in `api-reference.md`.

## Source Inventory

| File | Lines | Public classes | Public functions | Purpose |
| --- | ---: | ---: | ---: | --- |
| `aquilia/typing/__init__.py` | 144 | 0 | 0 |  |
| `aquilia/typing/asgi.py` | 151 | 21 | 0 |  |
| `aquilia/typing/common.py` | 24 | 0 | 0 |  |
| `aquilia/typing/config.py` | 121 | 4 | 0 | Configuration type definitions for Aquilia. |
| `aquilia/typing/container.py` | 46 | 7 | 0 |  |
| `aquilia/typing/controller.py` | 30 | 1 | 0 |  |
| `aquilia/typing/effects.py` | 21 | 1 | 0 |  |
| `aquilia/typing/manifest.py` | 26 | 2 | 0 |  |
| `aquilia/typing/middleware.py` | 20 | 1 | 0 |  |
| `aquilia/typing/request_state.py` | 10 | 0 | 0 |  |

## Detected Config-Oriented Classes

| Class | Source | Methods | Summary |
| --- | --- | --- | --- |
| `ConfigSource` | `aquilia/typing/config.py` | `to_dict` | Protocol for configuration sources that can be converted to dict. |
| `ConfigSection` | `aquilia/typing/config.py` | `to_dict` | Protocol for config section classes. |
| `EffectProviderProtocol` | `aquilia/typing/effects.py` | `initialize`, `acquire`, `release`, `finalize` |  |
| `MiddlewareProtocol` | `aquilia/typing/middleware.py` |  |  |

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
