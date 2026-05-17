# REST API Blueprint Starter

## Purpose

Product catalog API showing the standard Aquilia split: workspace routing, module manifest, controller transport code, service business logic, structured faults, and blueprint validation.

## Architecture

- `workspace.py` registers the `catalog` module at `/catalog` and enables DI, routing, fault handling, security headers, and telemetry.
- `modules/catalog/manifest.py` declares `CatalogController` and `CatalogService`.
- `blueprints.py` validates create/update payloads and rejects unknown fields.
- `services.py` keeps an in-memory catalog so the app runs without a database.

## Run

```bash
cd examples/rest_api_blueprint
python -m uvicorn runtime:app --reload --port 8000
```

Expected behavior: `GET /catalog/health` returns `{"module":"catalog","status":"ok",...}` and product routes operate on the in-memory catalog.

## Routes

| Method | Path | Purpose |
| --- | --- | --- |
| `GET` | `/catalog/products` | List products with `q`, `active`, `limit`, and `offset`. |
| `POST` | `/catalog/products` | Create product using `ProductCreateBlueprint`. |
| `GET` | `/catalog/products/<sku>` | Read one product. |
| `PATCH` | `/catalog/products/<sku>` | Partial update. |
| `DELETE` | `/catalog/products/<sku>` | Soft deactivate product. |
| `GET` | `/catalog/health` | Module health. |

## Test

```bash
python -m pytest examples/rest_api_blueprint -q
```

## Common Pitfalls

- Keep route prefix in `workspace.py`; keep controllers/services in `manifest.py`.
- `price_cents` must be non-negative.
- The service is process-local memory; use a database-backed service for production persistence.

## Extension Ideas

Add model-backed persistence, OpenAPI assertions, cache-aside reads, auth guards for writes, and versioned v2 product response shapes.

## Related APIs

`Workspace`, `Module`, `Integration.routing`, `AppManifest`, `Controller`, `GET`, `POST`, `PATCH`, `DELETE`, `Blueprint`, `Response`, `ConflictFault`, `NotFoundFault`.
