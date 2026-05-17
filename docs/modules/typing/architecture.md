# Typing Architecture

Shared protocols, typed dictionaries, aliases, and interface contracts for ASGI, containers, config, controllers, effects, manifests, middleware, and request state.

## Source Boundaries

| File | Lines | Classes | Functions | Purpose |
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

## Internal Shape

`typing` has 10 Python files, 37 public classes, 0 public module-level functions, and 4 constants or module flags detected by AST.

## Runtime Responsibilities

- No mounted `aq` command group maps directly to this module; it is used through Python APIs, manifests, workspace integrations, or server startup wiring.

## Internal Imports

| Import | Count |
| --- | ---: |
| `.common` | 4 |
| `.asgi` | 1 |
| `.config` | 1 |
| `.container` | 1 |
| `.controller` | 1 |
| `.effects` | 1 |
| `.manifest` | 1 |
| `.middleware` | 1 |
| `.request_state` | 1 |

## External And Stdlib Imports

| Import root | Count |
| --- | ---: |
| `__future__` | 9 |
| `typing` | 9 |
| `collections` | 6 |
| `dataclasses` | 1 |
| `datetime` | 1 |
| `pathlib` | 1 |

## Lifecycle And Extension Points

| Extension Type | Source | Role |
| --- | --- | --- |
| `ConfigSource` | `aquilia/typing/config.py` | Protocol for configuration sources that can be converted to dict. |
| `ConfigSection` | `aquilia/typing/config.py` | Protocol for config section classes. |
| `ControllerRouteMatchLike` | `aquilia/typing/controller.py` |  |
| `EffectProviderProtocol` | `aquilia/typing/effects.py` |  |
| `MiddlewareProtocol` | `aquilia/typing/middleware.py` |  |

## Error Handling

This module does not define public `Fault` or `Error` classes in its own files. Errors are usually raised through shared `aquilia.faults` domains or consuming subsystems.
