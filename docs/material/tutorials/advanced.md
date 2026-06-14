# Advanced Tutorial: Patterns and Deep Customization

This tutorial covers advanced Aquilia patterns: custom middleware, multi-module workspaces with cross-module DI, API versioning with sunset policies, custom effects, admin dashboard customization, and MCP server setup.

## Scenario: Multi-tenant e-commerce platform

We'll build `shopcore` — a multi-tenant e-commerce backend with:

- 4 modules: `catalog`, `orders`, `tenants`, `analytics`
- Custom rate-limiting middleware
- API versioning with sunset of v1
- Custom database transaction effect
- Custom admin dashboard
- MCP server for AI-powered inventory queries

## Step 1: Custom middleware

`modules/common/middleware.py`:

```python
"""
Tenant isolation middleware — injects tenant_id into every request scope.
Rate limiting per tenant — applies quota per tenant, not globally.
"""
from __future__ import annotations
import time
from dataclasses import dataclass, field
from threading import RLock

from aquilia.middleware import Handler
from aquilia.request import Request
from aquilia.controller.base import RequestCtx
from aquilia.response import Response
from aquilia.faults.domains import ForbiddenFault, TooManyRequestsFault


class TenantMiddleware:

    def __init__(self, header_name: str = "X-Tenant-ID"):
        self.header_name = header_name

    async def __call__(self, request: Request, ctx: RequestCtx, next: Handler) -> Response:
        tenant_id = request.header(self.header_name) or request.query_params.get("tenant_id")

        if not tenant_id:
            raise ForbiddenFault(detail="Tenant ID is required. Provide X-Tenant-ID header.")

        ctx.state["tenant_id"] = tenant_id
        ctx._extra = ctx._extra or {}
        ctx._extra["tenant_id"] = tenant_id

        response = await next(request, ctx)
        return response


@dataclass
class TenantRateLimitMiddleware:
    """
    Rate limiter that maintains per-tenant counters.
    Uses a sliding window in memory.
    """

    max_requests: int = 100
    window_seconds: float = 60.0

    _counters: dict[str, list[float]] = field(default_factory=dict, repr=False, init=False)
    _lock: RLock = field(default_factory=RLock, repr=False, init=False)

    async def __call__(self, request: Request, ctx: RequestCtx, next: Handler) -> Response:
        tenant_id = ctx.state.get("tenant_id", "default")
        now = time.monotonic()

        with self._lock:
            timestamps = self._counters.get(tenant_id, [])
            cutoff = now - self.window_seconds
            timestamps = [t for t in timestamps if t > cutoff]
            self._counters[tenant_id] = timestamps

            if len(timestamps) >= self.max_requests:
                oldest = timestamps[0]
                retry_after = int(oldest + self.window_seconds - now)
                raise TooManyRequestsFault(
                    detail=f"Tenant rate limit exceeded",
                    retry_after=max(retry_after, 1),
                )

            timestamps.append(now)

        return await next(request, ctx)
```

Register in `modules/common/manifest.py`:

```python
from aquilia.manifest import AppManifest

manifest = AppManifest(
    name="common",
    version="0.1.0",
    middleware=[
        "modules.common.middleware:TenantMiddleware",
        "modules.common.middleware:TenantRateLimitMiddleware",
    ],
    exports=["modules.common.middleware:TenantMiddleware"],
)
```

## Step 2: Multi-module workspace with cross-module DI

`workspace.py`:

```python
from aquilia.workspace import Workspace, Module
from aquilia import AquilaConfig, Secret, Env
from aquilia.integrations import (
    DatabaseIntegration, AuthIntegration, CacheIntegration,
    TasksIntegration, StorageIntegration, OpenAPIIntegration,
    VersioningIntegration, AdminIntegration, AdminModules,
    AdminAudit, AdminMonitoring,
    CorsIntegration, RateLimitIntegration,
)

class BaseEnv(AquilaConfig):
    env = "dev"

    class server(AquilaConfig.Server):
        host = "0.0.0.0"
        port = 8000
        workers = 2

    class auth(AquilaConfig.Auth):
        secret_key = Secret(env="AQ_SECRET_KEY", required=True)

    class database(AquilaConfig.Database):
        url = "sqlite:///shopcore.db"
        auto_create = True

class ProdEnv(BaseEnv):
    env = "prod"

    class server(BaseEnv.server):
        workers = Env("WORKERS", default=4, cast=int)

    class database(BaseEnv.database):
        url = "postgresql://user:pass@host:5432/shopcore"
        pool_size = 20

workspace = (
    Workspace("shopcore", version="2.0.0")
    .runtime(mode="dev", port=8000)
    # Core modules
    .module(Module("common").route_prefix("/").tags("infra"))
    .module(Module("tenants").route_prefix("/api/tenants").tags("core"))
    # Business modules — each declares imports from others
    .module(
        Module("catalog", version="0.2.0")
        .route_prefix("/api/catalog")
        .depends_on("tenants", "common")
        .tags("core", "catalog")
    )
    .module(
        Module("orders", version="0.2.0")
        .route_prefix("/api/orders")
        .depends_on("catalog", "tenants")
        .tags("core", "orders")
    )
    .module(
        Module("analytics", version="0.1.0")
        .route_prefix("/api/analytics")
        .depends_on("orders", "catalog")
        .tags("reporting")
    )
    # Integrations
    .integrate(DatabaseIntegration(url="sqlite:///shopcore.db"))
    .integrate(CacheIntegration(backend="redis", redis_url="redis://localhost:6379/0"))
    .integrate(StorageIntegration(default="local", backends={
        "local": {"backend": "local", "root": "./uploads"},
        "product_images": {"backend": "s3", "bucket": "shopcore-images"},
    }))
    .integrate(VersioningIntegration(
        strategy="composite",
        versions=["1.0", "2.0"],
        default_version="2.0",
        channels={"stable": "2.0", "legacy": "1.0"},
        require_version=True,
        sunset_schedules={
            "1.0": {
                "sunset_date": "2027-01-01",
                "deprecation_date": "2026-07-01",
                "link": "https://docs.shopcore.com/migration-v2",
            },
        },
    ))
    .integrate(AdminIntegration(
        site_title="Shopcore Admin",
        modules=AdminModules(monitoring=True, audit=True),
        audit=AdminAudit(enabled=True, max_entries=100_000),
        monitoring=AdminMonitoring(
            enabled=True,
            metrics=["cpu", "memory", "disk", "network", "system"],
            refresh_interval=10,
        ),
    ))
    .integrate(CorsIntegration(allow_origins=["https://admin.shopcore.com"]))
    .integrate(RateLimitIntegration(limit=500, window=60, burst=100))
    .env_config(BaseEnv)
)
```

## Step 3: Cross-module service dependencies

`modules/catalog/manifest.py`:

```python
from aquilia.manifest import AppManifest

manifest = AppManifest(
    name="catalog",
    version="0.2.0",
    controllers=[
        "modules.catalog.controllers:ProductController",
    ],
    services=[
        "modules.catalog.services:ProductService",
        "modules.catalog.services:InventoryService",
    ],
    models=[
        "modules.catalog.models:Product",
        "modules.catalog.models:Category",
    ],
    exports=["ProductService", "InventoryService"],
    imports=["tenants"],  # Consume TenantService from tenants module
)
```

`modules/orders/manifest.py`:

```python
manifest = AppManifest(
    name="orders",
    version="0.2.0",
    controllers=[
        "modules.orders.controllers:OrderController",
    ],
    services=[
        "modules.orders.services:OrderService",
    ],
    models=[
        "modules.orders.models:Order",
        "modules.orders.models:OrderItem",
    ],
    exports=["OrderService"],
    imports=["catalog", "tenants"],  # Depend on catalog & tenants
)
```

`modules/orders/services.py`:

```python
from aquilia import Inject

class OrderService:

    def __init__(
        self,
        product_service = Inject(tag="catalog.ProductService"),
        tenant_service = Inject(tag="tenants.TenantService"),
    ):
        self.products = product_service
        self.tenants = tenant_service

    async def create_order(self, tenant_id: str, items: list[dict]) -> dict:
        # Verify tenant quota
        tenant = await self.tenants.get_tenant(tenant_id)

        # Verify inventory for each item
        for item in items:
            available = await self.products.check_inventory(item["product_id"])
            if available < item["quantity"]:
                raise ValueError(f"Insufficient inventory for {item['product_id']}")

        # Create order, reduce inventory, process payment...
        return {"status": "confirmed", "order_id": "ord_...", "items": items}
```

## Step 4: API versioning with sunset

`modules/catalog/controllers.py`:

```python
from aquilia import Controller, GET, POST, RequestCtx, Response, Inject
from aquilia.versioning import version, version_neutral, SunsetPolicy, VersionSunsetError
from aquilia.faults.domains import GoneFault

class ProductController(Controller):
    prefix = "/catalog"
    tags = ["catalog"]

    def __init__(self, product_service=Inject()):
        self.service = product_service

    # v1 route — deprecated with sunset
    @version("1.0")
    @GET("/products")
    async def list_products_v1(self, ctx: RequestCtx):
        # Old response format
        products = await self.service.list_all()
        return Response.json({"data": [p.to_dict_v1() for p in products]})

    # v2 route — current stable
    @version("2.0")
    @GET("/products")
    async def list_products_v2(self, ctx: RequestCtx):
        # New response format with pagination
        page = int(ctx.request.query_params.get("page", 1))
        per_page = int(ctx.request.query_params.get("per_page", 20))
        products, total = await self.service.list_paginated(page, per_page)
        return Response.json({
            "products": [p.to_dict_v2() for p in products],
            "meta": {"page": page, "per_page": per_page, "total": total},
        })

    # Version-neutral — works across all versions
    @version_neutral
    @GET("/health")
    async def health(self, ctx: RequestCtx):
        return Response.json({"status": "healthy"})

    @version("2.1")
    @GET("/products/{id:int}/recommendations")
    async def recommendations(self, ctx: RequestCtx, id: int):
        # New in 2.1: AI-powered recommendations
        recs = await self.service.get_recommendations(id)
        return Response.json({"recommendations": recs})
```

## Step 5: Custom effect for database transactions

`modules/common/effects.py`:

```python
"""
Custom DBTx effect that enforces per-tenant database isolation.
"""
from aquilia import Controller, GET, RequestCtx, Response
from aquilia.effects import Effect, EffectKind, EffectProvider
from aquilia.flow import requires, pipeline, FlowContext


class TenantDBTx(Effect):
    """Database transaction scoped to a tenant."""
    kind = EffectKind.TRANSACTION
    name = "tenant_dbtx"

    def __init__(self, tenant_id: str, timeout: float = 30.0):
        self.tenant_id = tenant_id
        self.timeout = timeout


class TenantDBTxProvider(EffectProvider):
    """Provider that sets the tenant context before a DB transaction."""

    async def begin(self, effect: TenantDBTx) -> dict:
        return {
            "tenant_id": effect.tenant_id,
            "started_at": "now",
        }

    async def commit(self, effect: TenantDBTx, context: dict):
        # Set tenant context before queries
        pass

    async def rollback(self, effect: TenantDBTx, context: dict, error: Exception):
        pass


# Usage in a flow pipeline
@requires(TenantDBTx("tenant:abc"))
async def my_query(flow: FlowContext):
    tenant_id = flow.effects["tenant_dbtx"].tenant_id
    # Query scoped to tenant...
```

## Step 6: Admin dashboard customization

`workspace.py` (extended):

```python
workspace.integrate(AdminIntegration(
    url_prefix="/admin",
    site_title="Shopcore Admin",
    site_header="Shopcore",
    theme="auto",  # Follows system preference
    list_per_page=50,
    modules=AdminModules(
        monitoring=True,
        audit=True,
        tasks=True,
        storage=True,
    ).with_(orm=True, config=True, permissions=True),
    audit=AdminAudit(
        enabled=True,
        max_entries=100_000,
        log_logins=True,
        log_views=True,
        log_searches=True,
        excluded_actions=["cache_warmup"],
    ),
    monitoring=AdminMonitoring(
        enabled=True,
        metrics=["cpu", "memory", "disk", "network", "process", "python", "system"],
        refresh_interval=10,
    ),
    sidebar=AdminSidebar(
        overview=True,
        data=True,
        system=True,
        infrastructure=True,
        security=True,
        models=True,
        devtools=False,
    ),
    security=AdminSecurity(
        csrf_enabled=True,
        rate_limit_max_attempts=5,
        password_min_length=12,
        progressive_lockout=True,
        session_fixation_protection=True,
    ),
))
```

## Step 7: MCP server for AI-powered inventory queries

Aquilia can host MCP (Model Context Protocol) servers alongside your main API. This lets AI coding assistants query your catalog.

`modules/catalog/mcp_server.py`:

```python
"""
MCP tool: AI agents can ask 'what products are in stock?'
or 'find laptops under €1000' and get real-time answers
from the live inventory.
"""
from aquilia import Inject
from .services import ProductService


async def mc_psearch_products(product_service: ProductService, query: str, max_price: float | None = None):
    """Search products by name/description, optionally filtering by price."""
    products = await product_service.search(query=query, max_price=max_price)
    return [
        {
            "id": p.id,
            "name": p.name,
            "price": p.price,
            "in_stock": p.stock_count > 0,
            "stock_count": p.stock_count,
        }
        for p in products
    ]


async def mcp_get_product(product_service: ProductService, id: int):
    """Get full product details by ID."""
    product = await product_service.get_by_id(id)
    if not product:
        return {"error": "not_found"}
    return {
        "id": product.id,
        "name": product.name,
        "description": product.description,
        "price": product.price,
        "currency": product.currency,
        "categories": [c.name for c in product.categories],
        "stock": product.stock_count,
        "warehouse_locations": product.warehouse_locations,
    }
```

`modules/catalog/controllers.py` (MCP endpoint):

```python
from aquilia import Controller, POST, RequestCtx, Response, Inject


class MCPController(Controller):
    """MCP server endpoint — consumed by AI coding assistants."""
    prefix = "/mcp"
    tags = ["mcp", "ai"]

    def __init__(self, product_service=Inject()):
        self.service = product_service

    @POST("/tools/list")
    async def list_tools(self, ctx: RequestCtx):
        """Return available MCP tools."""
        return Response.json({
            "tools": [
                {
                    "name": "search_products",
                    "description": "Search the product catalog by name or description, with optional price filter",
                    "inputSchema": {
                        "type": "object",
                        "properties": {
                            "query": {"type": "string", "description": "Search query"},
                            "max_price": {"type": "number"},
                        },
                        "required": ["query"],
                    },
                },
                {
                    "name": "get_product",
                    "description": "Get detailed product information by ID",
                    "inputSchema": {
                        "type": "object",
                        "properties": {
                            "id": {"type": "integer", "description": "Product ID"},
                        },
                        "required": ["id"],
                    },
                },
            ],
        })

    @POST("/tools/call")
    async def call_tool(self, ctx: RequestCtx):
        body = await ctx.request.json()
        tool_name = body.get("name")
        args = body.get("arguments", {})

        if tool_name == "search_products":
            from .mcp_server import mcp_search_products
            result = await mcp_search_products(self.service, **args)
            return Response.json({"content": [{"type": "text", "text": str(result)}]})

        elif tool_name == "get_product":
            from .mcp_server import mcp_get_product
            result = await mcp_get_product(self.service, **args)
            return Response.json({"content": [{"type": "text", "text": str(result)}]})

        return Response.json({"error": f"Unknown tool: {tool_name}"}, status=400)
```

## Step 8: Advanced testing patterns

```python
import pytest
from aquilia.testing import TestClient, override_settings
from aquilia.entrypoint import create_app


@pytest.fixture
async def app():
    app = create_app()
    yield app

@pytest.fixture
async def client(app):
    return TestClient(app)

@pytest.mark.asyncio
async def test_version_routing(client):
    """Test that v1 and v2 return different response formats."""
    # v1 response
    resp_v1 = await client.get(
        "/api/catalog/products",
        headers={"X-API-Version": "1.0"},
    )
    assert resp_v1.status == 200
    assert "data" in resp_v1.json()  # v1 format

    # v2 response
    resp_v2 = await client.get(
        "/api/catalog/products",
        headers={"X-API-Version": "2.0"},
    )
    assert resp_v2.status == 200
    assert "products" in resp_v2.json()  # v2 format
    assert "meta" in resp_v2.json()

@pytest.mark.asyncio
async def test_tenant_isolation(client):
    """Test that setting X-Tenant-ID works."""
    resp = await client.get(
        "/api/catalog/products",
        headers={"X-Tenant-ID": "tenant-abc", "X-API-Version": "2.0"},
    )
    assert resp.status == 200

@pytest.mark.asyncio
async def test_missing_tenant_returns_403(client):
    resp = await client.get(
        "/api/catalog/products",
        headers={"X-API-Version": "2.0"},
    )
    assert resp.status == 403

@pytest.mark.asyncio
async def test_rate_limit_per_tenant(client):
    """Test that per-tenant rate limiting works."""
    for _ in range(100):
        resp = await client.get(
            "/api/catalog/products",
            headers={"X-Tenant-ID": "tenant-test", "X-API-Version": "2.0"},
        )
        assert resp.status == 200

    # 101st request should be rate-limited
    resp = await client.get(
        "/api/catalog/products",
        headers={"X-Tenant-ID": "tenant-test", "X-API-Version": "2.0"},
    )
    assert resp.status == 429

@pytest.mark.asyncio
async def test_mcp_tools(client):
    """Test that MCP server lists and executes tools."""
    # List tools
    resp = await client.post("/api/mcp/tools/list")
    assert resp.status == 200
    assert len(resp.json()["tools"]) == 2

    # Call a tool
    resp = await client.post("/api/mcp/tools/call", json={
        "name": "search_products",
        "arguments": {"query": "laptop", "max_price": 1000},
    })
    assert resp.status == 200

@pytest.mark.asyncio
async def test_version_sunset_headers(client):
    """Test that deprecated version gets sunset headers."""
    resp = await client.get(
        "/api/catalog/products",
        headers={"X-API-Version": "1.0"},
    )
    assert "Sunset" in resp.headers or "Deprecation" in resp.headers
    assert resp.headers.get("X-API-Version") == "1.0"
```

## Summary

You've built an advanced multi-module platform with:

| Feature | Implementation |
|---------|---------------|
| Custom middleware | `TenantMiddleware`, `TenantRateLimitMiddleware` |
| Cross-module DI | `exports` / `imports` with `Inject(tag="...")` |
| API versioning | `@version`, `@version_neutral`, sunset schedules |
| Custom effects | `TenantDBTx` effect with provider |
| Admin customization | `AdminIntegration` with all sub-configs |
| MCP server | Tool listing and invocation for AI agents |
| Per-tenant rate limiting | Sliding window in middleware |
| Version-aware tests | Test multiple API versions with different headers |

The architecture is now:

```mermaid
graph TD
    subgraph "modules/"
        A[common] --> B[tenants]
        A --> C[catalog]
        B --> C
        B --> D[orders]
        C --> D
        D --> E[analytics]
    end
    F[Middleware Chain] --> G[TenantMiddleware]
    G --> H[TenantRateLimit]
    H --> I[VersioningMiddleware]
    I --> J[Controller Dispatch]
```