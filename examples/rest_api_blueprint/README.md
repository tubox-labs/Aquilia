# REST API Blueprint Starter

This starter is a clean product catalog API. It shows the normal Aquilia split: workspace routing, module manifest registration, controller transport code, service business logic, and blueprint validation.

The service uses an in-memory store so the project starts without a database. The API shape is still production-friendly: resources have stable IDs, writes are validated through blueprints, list routes support filtering and search, and delete is implemented as a soft deactivate operation.

## Run

```bash
cd examples/rest_api_blueprint
aquilia serve
```

Or point an ASGI server at `runtime:app`.

## Routes

| Method | Path | Purpose |
| --- | --- | --- |
| `GET` | `/catalog/products` | List active products with optional `q`, `active`, `limit`, and `offset`. |
| `POST` | `/catalog/products` | Create a product from `ProductCreateBlueprint`. |
| `GET` | `/catalog/products/<sku>` | Read one product. |
| `PATCH` | `/catalog/products/<sku>` | Partial update through `ProductUpdateBlueprint`. |
| `DELETE` | `/catalog/products/<sku>` | Soft deactivate a product. |
| `GET` | `/catalog/health` | Module health response. |
