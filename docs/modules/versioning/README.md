# versioning Module

## Purpose

Epoch and semantic API versioning. Use this module for route version decorators, version negotiation, URL, query, header, media type, and channel resolvers, sunset policy, graph validation, and middleware.

## Source Coverage

- Python files: 11
- Public classes: 30
- Dataclasses: 5
- Enums: 3
- Public functions: 3

## How It Fits In Aquilia

1. Import the package from `aquilia.versioning` or its concrete submodules.
2. Configure it through workspace integrations, manifests, or direct service construction depending on the subsystem.
3. Keep business logic outside transport and framework glue so the subsystem stays testable.

## Practical Guidance

- Prefer typed configuration objects and framework helpers over ad hoc dictionaries when they exist.
- Use the tests in `tests/` as behavioral examples when changing this subsystem.

## Public Classes

| Name | Source | Role |
| --- | --- | --- |
| `VersionStatus` | `aquilia/versioning/core.py` | Version lifecycle status. |
| `VersionChannel` | `aquilia/versioning/core.py` | Named release channels. |
| `ApiVersion` | `aquilia/versioning/core.py` | Immutable API version value object. |
| `VersionError` | `aquilia/versioning/errors.py` | Base class for all versioning errors. |
| `InvalidVersionError` | `aquilia/versioning/errors.py` | Raised when a version string cannot be parsed. |
| `UnsupportedVersionError` | `aquilia/versioning/errors.py` | Raised when a valid version is not in the supported set. |
| `VersionSunsetError` | `aquilia/versioning/errors.py` | Raised when a version has been sunset (permanently retired). |
| `MissingVersionError` | `aquilia/versioning/errors.py` | Raised when no version is present and no default is configured. |
| `VersionNegotiationError` | `aquilia/versioning/errors.py` | Raised when version negotiation fails. |
| `VersionNode` | `aquilia/versioning/graph.py` | A node in the version graph. |
| `VersionGraph` | `aquilia/versioning/graph.py` | Compile-time version relationship graph. |
| `VersionMiddleware` | `aquilia/versioning/middleware.py` | Middleware that resolves API version for every request. |
| `NegotiationMode` | `aquilia/versioning/negotiation.py` | Version negotiation mode. |
| `VersionNegotiator` | `aquilia/versioning/negotiation.py` | Version negotiation engine. |
| `VersionParser` | `aquilia/versioning/parser.py` | Abstract version parser protocol. |
| `SemanticVersionParser` | `aquilia/versioning/parser.py` | Default version parser supporting semantic and epoch formats. |
| `BaseVersionResolver` | `aquilia/versioning/resolvers.py` | Abstract base class for version resolvers. |
| `URLPathResolver` | `aquilia/versioning/resolvers.py` | Extract version from URL path segment. |
| `HeaderResolver` | `aquilia/versioning/resolvers.py` | Extract version from a custom HTTP header. |
| `QueryParamResolver` | `aquilia/versioning/resolvers.py` | Extract version from query parameter. |
| `MediaTypeResolver` | `aquilia/versioning/resolvers.py` | Extract version from Accept header media type parameter. |
| `ChannelResolver` | `aquilia/versioning/resolvers.py` | Resolve version via named channels (unique to Aquilia). |
| `CompositeResolver` | `aquilia/versioning/resolvers.py` | Combine multiple resolvers with priority fallback. |
| `CustomResolver` | `aquilia/versioning/resolvers.py` | User-defined version resolver. |
| `VersionConfig` | `aquilia/versioning/strategy.py` | Complete versioning configuration. |
| `VersionStrategy` | `aquilia/versioning/strategy.py` | Central versioning orchestrator. |
| `SunsetPolicy` | `aquilia/versioning/sunset.py` | Global sunset policy configuration. |
| `SunsetEntry` | `aquilia/versioning/sunset.py` | Per-version sunset schedule entry. |
| `SunsetRegistry` | `aquilia/versioning/sunset.py` | Registry of sunset schedules. |
| `SunsetEnforcer` | `aquilia/versioning/sunset.py` | Enforces sunset policies at request time. |

## Public Functions

| Name | Source | Role |
| --- | --- | --- |
| `version` | `aquilia/versioning/decorators.py` | Bind a specific version (or list of versions) to a route. |
| `version_neutral` | `aquilia/versioning/decorators.py` | Mark a route as version-neutral. |
| `version_range` | `aquilia/versioning/decorators.py` | Bind a version range to a route. |

## Implementation Map

| File | What To Look For |
| --- | --- |
| `aquilia/versioning/__init__.py` | Aquilia Versioning System - Epoch-Based API Versioning |
| `aquilia/versioning/core.py` | Aquilia Versioning - Core Types |
| `aquilia/versioning/decorators.py` | Aquilia Versioning - Route-Level Decorators |
| `aquilia/versioning/errors.py` | Aquilia Versioning - Version Errors |
| `aquilia/versioning/graph.py` | Aquilia Versioning - Version Graph |
| `aquilia/versioning/middleware.py` | Aquilia Versioning - Version Middleware |
| `aquilia/versioning/negotiation.py` | Aquilia Versioning - Version Negotiation |
| `aquilia/versioning/parser.py` | Aquilia Versioning - Version Parser |
| `aquilia/versioning/resolvers.py` | Aquilia Versioning - Version Resolvers |
| `aquilia/versioning/strategy.py` | Aquilia Versioning - Version Strategy |
| `aquilia/versioning/sunset.py` | Aquilia Versioning - Sunset Lifecycle |

## Testing Pointers

Search `tests/` for `versioning` to find behavior-level examples. The test suite is especially useful for edge cases because many modules expose lightweight public APIs but enforce important security and lifecycle behavior internally.
