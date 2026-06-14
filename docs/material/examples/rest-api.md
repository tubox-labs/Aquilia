# REST API Blueprint

The REST API example demonstrates a product catalog with blueprint validation,
search, pagination, and soft deletion. It showcases the standard Aquilia pattern:
workspace routing, module manifest, thin controllers, service business logic,
structured faults, and Blueprint request validation.

---

## What It Demonstrates

- `Workspace` and `Module` configuration with typed integrations
- `AppManifest` declaring controllers and services
- `Controller` subclasses with `@GET`, `@POST`, `@PATCH`, `@DELETE` decorators
- `Blueprint` subclasses for request validation with `Spec.extra_fields = "reject"`
- URL path parameters with type annotations (`<sku:str>`)
- Structured faults: `ConflictFault` and `NotFoundFault`
- In-memory service layer with search, filtering, and pagination
- Soft deletion via `active` field toggle

## Key Files

| File | Purpose |
| ---- | ------- |
| `workspace.py` | Registers the `catalog` module at `/catalog` with DI, routing, and fault handling integrations |
| `runtime.py` | Boots `AquiliaRuntime` and exposes the ASGI `app` |
| `modules/catalog/manifest.py` | Declares `CatalogController` and `CatalogService` in `AppManifest` |
| `modules/catalog/controllers.py` | HTTP endpoints — health, list, create, read, update, deactivate |
| `modules/catalog/blueprints.py` | `ProductCreateBlueprint` and `ProductUpdateBlueprint` with field validation |
| `modules/catalog/services.py` | `CatalogService` and `Product` dataclass with in-memory storage |

## Workspace Configuration

```python
from aquilia import Module, Workspace
from aquilia.integrations import DiIntegration, FaultHandlingIntegration, RoutingIntegration

workspace = (
    Workspace("catalog-api", version="1.0.0", description="Product catalog REST API starter")
    .runtime(mode="dev", host="127.0.0.1", port=8000, reload=True)
    .module(Module("catalog", version="1.0.0").route_prefix("/catalog").tags("catalog", "rest"))
    .integrate(DiIntegration(auto_wire=True))
    .integrate(RoutingIntegration(strict_matching=True))
    .integrate(FaultHandlingIntegration(default_strategy="propagate"))
    .security(cors_enabled=True, csrf_protection=False, helmet_enabled=True)
    .telemetry(metrics_enabled=True, logging_enabled=True)
)
```

## Controller Routes

```python
class CatalogController(Controller):
    prefix = "/"
    tags = ["catalog"]

    def __init__(self, service: CatalogService | None = None):
        self.service = service or CatalogService()

    @GET("/health")
    async def health(self, ctx: RequestCtx):
        return Response.json({"module": "catalog", "status": "ok", "path": ctx.path})

    @GET("/products")
    async def list_products(self, ctx: RequestCtx):
        active = None if (raw := ctx.query_param("active", "true")) == "all" else raw.lower() != "false"
        limit = min(int(ctx.query_param("limit", "50") or "50"), 100)
        offset = max(int(ctx.query_param("offset", "0") or "0"), 0)
        payload = await self.service.list_products(
            q=ctx.query_param("q"), active=active, limit=limit, offset=offset,
        )
        return Response.json(payload)

    @POST("/products", status_code=201)
    async def create_product(self, ctx: RequestCtx):
        blueprint = ProductCreateBlueprint(data=await ctx.json())
        await blueprint.is_sealed_async()
        product = await self.service.create_product(blueprint.validated_data)
        return Response.json(product, status=201)

    @GET("/products/<sku:str>")
    async def get_product(self, ctx: RequestCtx, sku: str):
        return Response.json(await self.service.get_product(sku))

    @PATCH("/products/<sku:str>")
    async def update_product(self, ctx: RequestCtx, sku: str):
        blueprint = ProductUpdateBlueprint(data=await ctx.json())
        await blueprint.is_sealed_async()
        return Response.json(await self.service.update_product(sku, blueprint.validated_data))

    @DELETE("/products/<sku:str>")
    async def delete_product(self, ctx: RequestCtx, sku: str):
        return Response.json(await self.service.deactivate_product(sku))
```

## Blueprint Validation

Blueprints validate and normalize request bodies before they reach the service layer:

```python
class ProductCreateBlueprint(Blueprint):
    sku: str
    name: str
    price_cents: int
    active: bool = True
    tags: list[str] = []

    class Spec:
        extra_fields = "reject"

    def seal_sku(self, data):
        sku = data.get("sku", "").strip().upper()
        if not sku:
            self.reject("sku", "SKU is required")
        data["sku"] = sku

    def seal_price_cents(self, data):
        if data.get("price_cents", 0) < 0:
            self.reject("price_cents", "Price must be zero or greater")
```

Key points:

- `Spec.extra_fields = "reject"` rejects unknown fields in the request body
- `seal_*` methods run during `is_sealed_async()` and can call `self.reject()` for validation errors
- The controller accesses `blueprint.validated_data` after sealing
- Blueprints raise validation faults that the fault middleware converts to HTTP 422 responses

## Structured Faults

The service layer raises `Fault` subclasses instead of raw exceptions:

```python
from aquilia.faults import ConflictFault, NotFoundFault

async def get_product(self, sku: str) -> dict[str, Any]:
    product = self._products.get(sku.upper())
    if product is None:
        raise NotFoundFault(detail=f"Product {sku!r} was not found")
    return product.to_dict()

async def create_product(self, data: dict[str, Any]) -> dict[str, Any]:
    sku = data["sku"].upper()
    if sku in self._products:
        raise ConflictFault(detail=f"Product {sku!r} already exists")
    product = Product(**data)
    self._products[sku] = product
    return product.to_dict()
```

## API Endpoints

| Method | Path | Purpose |
| ------ | ---- | ------- |
| `GET` | `/catalog/health` | Module health check |
| `GET` | `/catalog/products` | List products with `q`, `active`, `limit`, `offset` |
| `POST` | `/catalog/products` | Create a product (validates with `ProductCreateBlueprint`) |
| `GET` | `/catalog/products/<sku>` | Read a single product |
| `PATCH` | `/catalog/products/<sku>` | Partial update (validates with `ProductUpdateBlueprint`) |
| `DELETE` | `/catalog/products/<sku>` | Soft-deactivate a product (sets `active=False`) |

## Running

```bash
cd examples/rest_api_blueprint
python -m uvicorn runtime:app --reload --port 8000
```

Test the API:

```bash
# List all products
curl http://127.0.0.1:8000/catalog/products

# Search by keyword
curl "http://127.0.0.1:8000/catalog/products?q=starter"

# Create a product
curl -X POST http://127.0.0.1:8000/catalog/products \
  -H "Content-Type: application/json" \
  -d '{"sku":"AQ-MINI","name":"Aquilia Mini","price_cents":2900,"tags":["mini","compact"]}'

# Run tests
python -m pytest examples/rest_api_blueprint -q
```

## What You'll Learn

- How to structure an Aquilia application with workspace, module, manifest, controller, and service layers
- How to validate request bodies with Blueprint subclasses
- How to use URL path parameters with type annotations
- How to raise and handle structured faults
- How to implement search, filtering, and pagination in service methods
- How to implement soft deletion patterns

---

## CRUD App

The CRUD example in `examples/crud_app/` extends these patterns with model declarations
and repository-style services. It demonstrates:

- Project model declaration using `aquilia.models.Model`
- `AppManifest.models` for declaring persistent models
- Blueprint-based `key` normalization (uppercase)
- Soft archive and restore flows
- The same controller/service/manifest patterns as the REST API example

```bash
cd examples/crud_app
python -m uvicorn runtime:app --reload --port 8010
python -m pytest examples/crud_app -q
```