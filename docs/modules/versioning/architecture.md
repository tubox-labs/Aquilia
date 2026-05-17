# Versioning Architecture

API version parsing, resolvers, decorators, negotiation, graph, sunset policy/enforcement, middleware, and route registration integration.

## Source Boundaries

| File | Lines | Classes | Functions | Purpose |
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

## Internal Shape

`versioning` has 11 Python files, 30 public classes, 3 public module-level functions, and 6 constants or module flags detected by AST.

## Runtime Responsibilities

- No mounted `aq` command group maps directly to this module; it is used through Python APIs, manifests, workspace integrations, or server startup wiring.

## Internal Imports

| Import | Count |
| --- | ---: |
| `.core` | 7 |
| `.errors` | 5 |
| `.graph` | 2 |
| `.negotiation` | 2 |
| `.parser` | 2 |
| `.resolvers` | 2 |
| `.strategy` | 2 |
| `.sunset` | 2 |
| `..faults` | 1 |
| `.decorators` | 1 |
| `.middleware` | 1 |

## External And Stdlib Imports

| Import root | Count |
| --- | ---: |
| `__future__` | 10 |
| `typing` | 9 |
| `dataclasses` | 4 |
| `datetime` | 3 |
| `abc` | 2 |
| `collections` | 2 |
| `enum` | 2 |
| `re` | 2 |
| `functools` | 1 |
| `logging` | 1 |

## Lifecycle And Extension Points

| Extension Type | Source | Role |
| --- | --- | --- |
| `VersionMiddleware` | `aquilia/versioning/middleware.py` | Middleware that resolves API version for every request. |
| `VersionConfig` | `aquilia/versioning/strategy.py` | Complete versioning configuration. |
| `SunsetPolicy` | `aquilia/versioning/sunset.py` | Global sunset policy configuration. |
| `SunsetRegistry` | `aquilia/versioning/sunset.py` | Registry of sunset schedules. |

## Error Handling

Fault/error classes defined here:

`VersionError`, `InvalidVersionError`, `UnsupportedVersionError`, `VersionSunsetError`, `MissingVersionError`, `VersionNegotiationError`
