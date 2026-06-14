# Versioned Public API

The Versioned Public API example demonstrates header-based API versioning with route-level
version decorators, version-neutral routes, and service-side version resolution.

---

## What It Demonstrates

- `VersioningIntegration` with `VersionConfig` and `VersionStrategy`
- `@version("1.0")` and `@version("2.0")` decorators for route versioning
- `@version_neutral` for routes that apply to all versions
- Service-side version resolution via `VersionConfig` and `VersionStrategy`
- Default version fallback when no version header is present
- Version-specific response shapes within the same controller

## Key Files

| File | Purpose |
| ---- | ------- |
| `workspace.py` | Enables `VersioningIntegration` with header strategy |
| `modules/publicapi/manifest.py` | Declares `PublicCatalogController` and `PublicCatalogService` |
| `modules/publicapi/controllers.py` | Version-specific and version-neutral routes |
| `modules/publicapi/services.py` | `PublicCatalogService` with version-aware data shaping |

## Workspace Configuration

```python
from aquilia.integrations import DiIntegration, VersioningIntegration

workspace = (
    Workspace("versioned-public-api-app", version="1.0.0")
    .runtime(mode="dev", host="127.0.0.1", port=8066, reload=True)
    .module(Module("publicapi", version="1.0.0").route_prefix("/public"))
    .integrate(VersioningIntegration(
        default_version="1.0",
        versions=["1.0", "2.0"],
        strategy="header",
    ))
    .integrate(DiIntegration(auto_wire=True))
)
```

| Setting | Purpose |
| ------- | ------- |
| `default_version` | Version used when no header is present |
| `versions` | Supported API versions |
| `strategy` | Version resolution strategy: `"header"`, `"query"`, `"path"`, `"media_type"` |

## Version-Aware Controller

Routes are versioned with decorators. Unversioned routes apply to all versions:

```python
from aquilia.versioning import version, version_neutral

class PublicCatalogController(Controller):
    prefix = "/"
    tags = ["catalog"]

    @GET("/products")
    @version_neutral
    async def product_count(self, ctx: RequestCtx):
        return Response.json({"count": await self.service.count_products()})

    @GET("/catalog")
    @version("1.0")
    async def catalog_v1(self, ctx: RequestCtx):
        return Response.json(await self.service.get_catalog(version="1.0"))

    @GET("/catalog")
    @version("2.0")
    async def catalog_v2(self, ctx: RequestCtx):
        return Response.json(await self.service.get_catalog(version="2.0"))
```

The routing system dispatches to the correct handler based on the `X-API-Version` header:

- No header → uses `default_version` (`1.0`) → dispatches to `catalog_v1`
- `X-API-Version: 1.0` → dispatches to `catalog_v1`
- `X-API-Version: 2.0` → dispatches to `catalog_v2`
- `/products` (version-neutral) → always dispatches to `product_count`

## Version-Aware Service

The service can also be version-aware for data transformations:

```python
class PublicCatalogService:
    async def get_catalog(self, version: str = "1.0") -> dict:
        products = await self._list_products()
        if version == "2.0":
            return {
                "version": "2.0",
                "catalog": [
                    {
                        "id": p["sku"],
                        "display_name": p["name"],
                        "pricing": {
                            "amount": p["price_cents"] / 100,
                            "currency": "USD",
                        },
                        "metadata": {"tags": p.get("tags", [])},
                    }
                    for p in products
                ],
            }
        # Version 1.0 shape (default)
        return {
            "version": "1.0",
            "products": [
                {"sku": p["sku"], "name": p["name"], "price_cents": p["price_cents"]}
                for p in products
            ],
        }
```

## Version Resolution Strategies

| Strategy | Example | Header / Source |
| -------- | ------- | --------------- |
| **header** | `X-API-Version: 2.0` | HTTP header (default) |
| **query** | `?version=2.0` | Query parameter |
| **path** | `/v2/products` | URL path segment |
| **media_type** | `Accept: application/vnd.api.v2+json` | Content negotiation |

## Running

```bash
cd examples/versioned_public_api_app
python -m uvicorn runtime:app --reload --port 8066
```

```bash
# Version 1.0 (default — no header)
curl http://127.0.0.1:8066/public/catalog

# Version 2.0 (explicit header)
curl http://127.0.0.1:8066/public/catalog \
  -H "X-API-Version: 2.0"

# Version-neutral route
curl http://127.0.0.1:8066/public/products

# Run tests
python -m pytest examples/versioned_public_api_app -q
```

## What You'll Learn

- How to configure `VersioningIntegration` with supported versions and strategy
- How to use `@version()`, `@version_neutral` decorators on controller routes
- How header-based version negotiation resolves the correct handler
- How to implement version-specific response shapes in services
- How to use `VersionConfig` and `VersionStrategy` for service-side version resolution