# Versioned Public API App

## Purpose

Shows header-based API versioning, route-level version decorators, version-neutral routes, and service-side version resolution.

## Architecture

- `workspace.py` wires `VersioningIntegration`.
- `PublicCatalogController` uses `@version` and `@version_neutral`.
- `PublicCatalogService` uses `VersionConfig` and `VersionStrategy` with a fake request for deterministic tests.

## Setup

```bash
python -m pip install -e ".[dev]"
python -m pytest examples/versioned_public_api_app -q
```

## Run

```bash
cd examples/versioned_public_api_app
python -m uvicorn runtime:app --reload --port 8066
```

## Expected Behavior

`X-API-Version: 2.0` returns a richer catalog payload while unversioned requests use the configured default version.

## Common Pitfalls

- Version decorators store metadata; runtime negotiation is handled by the versioning integration and middleware.
- Header names are normalized to lowercase by many request implementations.

## Extension Ideas

Add sunset policy, channel routing, media type negotiation, and migration docs for deprecated versions.

## Related APIs

`VersionConfig`, `VersionStrategy`, `ApiVersion`, `@version`, `@version_neutral`, `VersioningIntegration`.
