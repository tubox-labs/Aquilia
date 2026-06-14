# Versioning Module

> `aquilia.versioning` — API version management

The Versioning module provides API version management with multiple resolution strategies (URL path, header, query param, media type), sunset policies, version graphs, and version negotiation middleware.

## When to Use

Use the Versioning module when you need:

- Multiple API versions served simultaneously
- Gradual deprecation with sunset policies
- Version negotiation from Accept headers
- Version-specific route handlers
- Backward-compatible API changes

## Key Classes

| Class | Purpose |
|---|---|
| `ApiVersion` | Typed version identifier (e.g., `v1`, `2024-01`) |
| `VersionChannel` | Named version channel (stable, beta, canary) |
| `VersionConfig` | Versioning configuration |
| `VersionStrategy` | Version resolution strategy |
| `VersionMiddleware` | Middleware that resolves request version |
| `VersionGraph` | Directed graph of version relationships |
| `VersionNegotiator` | Client-server version negotiation |
| `SunsetPolicy` | Deprecation timeline for a version |
| `SunsetRegistry` | Registry of sunsetting versions |

## Version Resolvers

| Resolver | Example |
|---|---|
| `URLPathResolver` | `/v1/users/`, `/v2/users/` |
| `HeaderResolver` | `Accept-Version: v1` |
| `QueryParamResolver` | `?version=v2` |
| `MediaTypeResolver` | `Accept: application/vnd.myapp.v2+json` |
| `CompositeResolver` | Tries multiple resolvers in order |
| `ChannelResolver` | Resolves version channels (stable → specific version) |

## Quick Example

```python
from aquilia.versioning import version, ApiVersion, VersionConfig

class UsersController(Controller):
    prefix = "/users"

    @version(1)
    @GET("/")
    async def list_v1(self, ctx: RequestCtx):
        # Legacy: flat list
        return Response.json({"users": ["Alice", "Bob"]})

    @version(2)
    @GET("/")
    async def list_v2(self, ctx: RequestCtx):
        # V2: paginated with metadata
        return Response.json({
            "data": [{"name": "Alice"}, {"name": "Bob"}],
            "meta": {"total": 2, "page": 1},
        })

# Version-agnostic endpoint
version_neutral
@GET("/health")
async def health(self, ctx: RequestCtx):
    return Response.json({"status": "ok"})

# Version range
@version_range(1, 3)
@GET("/legacy-feature")
async def legacy(self, ctx: RequestCtx):
    return Response.json({"deprecated": True})
```

## Sunset Policy

```python
from aquilia.versioning import SunsetPolicy

policy = SunsetPolicy(
    version="v1",
    sunset_date="2026-12-31",
    deprecation_date="2026-06-01",
    message="Migrate to v2 before end of year",
)
```

## Import Path

```python
from aquilia.versioning import (
    ApiVersion,
    VersionChannel,
    VersionConfig,
    VersionStrategy,
    VersionMiddleware,
    VersionGraph,
    VersionNegotiator,
    SunsetPolicy,
    SunsetRegistry,
    HeaderResolver,
    URLPathResolver,
    QueryParamResolver,
    MediaTypeResolver,
    CompositeResolver,
    ChannelResolver,
    version,
    version_neutral,
    version_range,
    VERSION_NEUTRAL,
    VERSION_ANY,
)
```

## Related Modules

- [cli](../cli/index.md) — Version-aware route inspection
- [core/middleware](../core/middleware.md) — VersionMiddleware in the chain
- [integrations](../integrations/index.md) — `VersioningIntegration` config builder