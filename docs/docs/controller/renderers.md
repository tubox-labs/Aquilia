---
title: "Content Negotiation & Renderers"
description: "Multi-format response rendering"
icon: lucide/file-code
---## Overview

Aquilia provides automatic content negotiation through a pluggable renderer system that transforms your Python data structures into multiple response formats. The framework selects the appropriate renderer based on client preferences expressed via the `Accept` header or explicit `?format=` query parameters (lines 1-32).

The renderer system enables your API to serve the same data in JSON, XML, YAML, HTML, plain text, or binary MessagePack format without duplicating controller logic.

**Key Features:**
- Quality-weighted Accept header parsing
- Format override via query parameters
- Extensible renderer architecture
- Built-in renderers for common formats
- Automatic charset handling

## Built-in Renderers Table

| Renderer | Media Type | Format Suffix | Charset | Dependencies |
|----------|------------|---------------|---------|--------------|
| **JSONRenderer** | `application/json` | `json` | `utf-8` | None (stdlib) |
| **XMLRenderer** | `application/xml` | `xml` | `utf-8` | None (stdlib) |
| **YAMLRenderer** | `application/x-yaml` | `yaml` | `utf-8` | Optional: `pyyaml` |
| **PlainTextRenderer** | `text/plain` | `text` | `utf-8` | None (stdlib) |
| **HTMLRenderer** | `text/html` | `html` | `utf-8` | None (stdlib) |
| **MessagePackRenderer** | `application/msgpack` | `msgpack` | None (binary) | Required: `msgpack` |

All renderers are defined in lines 43-294, with JSONRenderer serving as the default (lines 141-163).

## Negotiation Priority

The content negotiation engine resolves the output format in this order (lines 314-363):

1. **Explicit `?format=` query parameter** — Matches against renderer `format_suffix`
   ```
   GET /api/products?format=xml
   ```

2. **Accept header negotiation** — Uses quality factors and wildcard matching
   ```
   Accept: application/json;q=0.9, text/html;q=0.8
   ```

3. **First renderer in the list** — Falls back to the default renderer

This three-tier priority ensures clients can explicitly request formats while still respecting standard HTTP content negotiation (lines 307-313).

## BaseRenderer API

All renderers inherit from `BaseRenderer` (lines 118-138), which defines the contract:

```python
class BaseRenderer:
    """Abstract renderer."""
    
    media_type: str = "application/octet-stream"
    format_suffix: str = ""  # e.g., "json", "xml"
    charset: str | None = "utf-8"
    
    def render(
        self,
        data: Any,
        *,
        request: Any = None,
        response_status: int = 200,
        response_headers: dict[str, str] | None = None,
    ) -> str | bytes:
        """Render data to the target format."""
        raise NotImplementedError
```

**Required Attributes:**
- `media_type` — MIME type for Content-Type header
- `format_suffix` — Short identifier for `?format=` parameter
- `charset` — Character encoding (or `None` for binary)

**Required Method:**
- `render()` — Converts Python data to string or bytes

## Accept Header Parsing

The `_parse_accept()` function (lines 51-83) implements RFC-compliant Accept header parsing with quality factor support:

```python
def _parse_accept(header: str) -> list[tuple[str, float]]:
    """
    Parse an Accept header into (media_type, quality) sorted by quality.
    
    Examples:
        _parse_accept("application/json")
        # → [("application/json", 1.0)]
        
        _parse_accept("text/html, application/json;q=0.9, */*;q=0.1")
        # → [("text/html", 1.0), ("application/json", 0.9), ("*/*", 0.1)]
    """
```

**Features:**
- Extracts quality factors from `q=` parameters (lines 69-74)
- Defaults to `q=1.0` when unspecified (line 67)
- Sorts entries by quality descending (line 77)
- Returns `[("*/*", 1.0)]` for empty/missing headers (line 54)

The `_media_matches()` helper (lines 86-96) supports wildcard matching:
- `*/*` matches any renderer
- `application/*` matches any `application/` media type
- Exact match for specific types

## Controller-level renderer_classes

Set `renderer_classes` on your controller to define available renderers (lines 18-27 in docstring):

```python
from aquilia import Controller, GET
from aquilia.controller.renderers import JSONRenderer, XMLRenderer, YAMLRenderer

class ProductsController(Controller):
    prefix = "/products"
    renderer_classes = [JSONRenderer(), XMLRenderer(), YAMLRenderer()]
    
    @GET("/")
    async def list_products(self, ctx):
        products = await self.product_service.get_all()
        return products  # Automatic negotiation
```

When you return data directly, Aquilia's response pipeline uses the `ContentNegotiator` (lines 299-363) to select and invoke the appropriate renderer.

## Route-level Override

Override renderers for specific routes by configuring the route decorator or manually invoking the negotiation:

```python
from aquilia import Controller, GET
from aquilia.controller.renderers import PlainTextRenderer, HTMLRenderer

class ReportController(Controller):
    prefix = "/reports"
    renderer_classes = [JSONRenderer()]  # Default for all routes
    
    @GET("/summary")
    async def summary(self, ctx):
        # This route uses controller-level renderers
        return {"summary": "data"}
    
    @GET("/export")
    async def export(self, ctx):
        # Manual override for this specific route
        from aquilia.controller.renderers import negotiate
        
        data = await self.generate_report()
        body, content_type, status = negotiate(
            data,
            ctx.request,
            renderers=[PlainTextRenderer(), HTMLRenderer()]
        )
        
        ctx.response.set_header("Content-Type", content_type)
        return body
```

Route-level control is achieved by calling `negotiate()` directly (lines 374-394).

## negotiate() Function

The `negotiate()` convenience function provides one-shot content negotiation (lines 374-394):

```python
def negotiate(
    data: Any,
    request: Any,
    *,
    renderers: Sequence[BaseRenderer] | None = None,
    status: int = 200,
    headers: dict[str, str] | None = None,
) -> tuple[str | bytes, str, int]:
    """
    One-shot content negotiation.
    
    Returns (rendered_body, content_type, status_code).
    """
```

**Parameters:**
- `data` — Python object to render
- `request` — Request object with Accept header and query params
- `renderers` — Optional list of renderers (defaults to `[JSONRenderer()]`)
- `status` — HTTP status code (default: 200)
- `headers` — Additional response headers

**Returns:**
- Tuple of `(body, content_type, status_code)`

**Implementation Details:**
- Creates a `ContentNegotiator` instance (line 385)
- Selects renderer via `select_renderer()` (line 386)
- Invokes `render()` with context (lines 388-393)
- Appends charset to Content-Type if applicable (lines 395-397)

## MessagePackRenderer

The `MessagePackRenderer` (lines 277-294) provides binary serialization for high-performance APIs:

```python
class MessagePackRenderer(BaseRenderer):
    """Render data as MessagePack binary (requires msgpack)."""
    
    media_type = "application/msgpack"
    format_suffix = "msgpack"
    charset = None  # binary
```

**Installation:**
```bash
pip install msgpack
```

**Usage:**
```python
from aquilia.controller.renderers import MessagePackRenderer, JSONRenderer

class DataController(Controller):
    renderer_classes = [JSONRenderer(), MessagePackRenderer()]
    
    @GET("/bulk")
    async def bulk_data(self, ctx):
        # Client requesting with Accept: application/msgpack
        # will receive binary MessagePack response
        return {"records": [...]}  # Large dataset
```

**Behavior:**
- Returns raw `bytes` instead of string (line 284)
- Uses `msgpack.packb()` with `use_bin_type=True` (line 284)
- Falls back to `str()` serialization for non-packable types (line 284)
- Raises `ConfigMissingFault` if `msgpack` is not installed (lines 286-290)

The renderer sets `charset = None` (line 281) to indicate binary content.

## Custom Renderer

Create custom renderers by subclassing `BaseRenderer` and implementing the contract:

```python
from aquilia.controller.renderers import BaseRenderer
import csv
from io import StringIO

class CSVRenderer(BaseRenderer):
    """Render list-of-dicts as CSV."""
    
    media_type = "text/csv"
    format_suffix = "csv"
    charset = "utf-8"
    
    def __init__(self, *, delimiter: str = ","):
        self.delimiter = delimiter
    
    def render(
        self,
        data: Any,
        *,
        request: Any = None,
        response_status: int = 200,
        response_headers: dict[str, str] | None = None,
    ) -> str:
        """Convert list of dicts to CSV."""
        if not isinstance(data, list) or not data:
            return ""
        
        output = StringIO()
        writer = csv.DictWriter(
            output,
            fieldnames=data[0].keys(),
            delimiter=self.delimiter
        )
        writer.writeheader()
        writer.writerows(data)
        return output.getvalue()
```

**Register your custom renderer:**

```python
from aquilia import Controller, GET

class ExportController(Controller):
    renderer_classes = [
        JSONRenderer(),
        XMLRenderer(),
        CSVRenderer(),  # Custom renderer
    ]
    
    @GET("/users")
    async def export_users(self, ctx):
        users = await self.user_service.get_all()
        return [u.to_dict() for u in users]
```

**Client requests:**
```bash
# Get JSON
curl -H "Accept: application/json" http://api/users

# Get CSV
curl -H "Accept: text/csv" http://api/users

# Explicit format override
curl http://api/users?format=csv
```

## Code Examples

### Multi-format API Endpoint

```python
from aquilia import Controller, GET
from aquilia.controller.renderers import (
    JSONRenderer,
    XMLRenderer,
    YAMLRenderer,
    PlainTextRenderer,
)

class ProductsController(Controller):
    prefix = "/api/products"
    renderer_classes = [
        JSONRenderer(indent=2),  # Pretty JSON
        XMLRenderer(root_tag="products", item_tag="product"),
        YAMLRenderer(),
        PlainTextRenderer(),
    ]
    
    @GET("/")
    async def list_products(self, ctx):
        """Return products in client's preferred format."""
        products = await self.db.fetch_all("SELECT * FROM products")
        return [dict(row) for row in products]
    
    @GET("/{id}")
    async def get_product(self, ctx, id: int):
        """Single product with negotiation."""
        product = await self.db.fetch_one(
            "SELECT * FROM products WHERE id = ?", id
        )
        if not product:
            ctx.response.status = 404
            return {"error": "Product not found"}
        return dict(product)
```

**Client requests:**
```bash
# JSON (default)
curl http://localhost:8000/api/products

# XML via Accept header
curl -H "Accept: application/xml" http://localhost:8000/api/products

# YAML via format parameter
curl http://localhost:8000/api/products?format=yaml

# Plain text fallback
curl -H "Accept: text/plain" http://localhost:8000/api/products/1
```

### Manual Negotiation with Custom Headers

```python
from aquilia import Controller, GET
from aquilia.controller.renderers import negotiate, JSONRenderer, XMLRenderer

class ReportsController(Controller):
    prefix = "/reports"
    
    @GET("/monthly")
    async def monthly_report(self, ctx):
        """Generate report with custom negotiation."""
        report_data = await self.generate_monthly_report()
        
        # Manual negotiation with custom renderers
        body, content_type, status = negotiate(
            report_data,
            ctx.request,
            renderers=[
                JSONRenderer(indent=4, ensure_ascii=False),
                XMLRenderer(root_tag="report", item_tag="entry"),
            ],
            status=200,
            headers={"X-Report-Generated": "2026-07-02"},
        )
        
        # Apply to response
        ctx.response.set_header("Content-Type", content_type)
        ctx.response.set_header("X-Report-Generated", "2026-07-02")
        ctx.response.status = status
        
        return body
```

### Quality Factor Negotiation

```python
# Client sends:
Accept: application/xml;q=0.8, application/json;q=1.0, text/html;q=0.5

# Parsed by _parse_accept() (lines 51-83):
# [("application/json", 1.0), ("application/xml", 0.8), ("text/html", 0.5)]

# ContentNegotiator.select_renderer() (lines 320-363):
# 1. No ?format= parameter
# 2. Iterate parsed accepts by quality descending
# 3. Match application/json → select JSONRenderer
# 4. Return (JSONRenderer(), "application/json")
```

### Conditional Renderer Selection

```python
from aquilia import Controller, GET
from aquilia.controller.renderers import (
    JSONRenderer,
    HTMLRenderer,
    PlainTextRenderer,
)

class DocsController(Controller):
    prefix = "/docs"
    
    @GET("/spec")
    async def api_spec(self, ctx):
        """Return API spec in appropriate format."""
        spec = self.load_openapi_spec()
        
        # Check if request is from browser
        accept = ctx.request.header("Accept") or ""
        is_browser = "text/html" in accept
        
        if is_browser:
            # Render HTML documentation
            renderers = [HTMLRenderer(), JSONRenderer()]
        else:
            # API clients get JSON/text
            renderers = [JSONRenderer(), PlainTextRenderer()]
        
        from aquilia.controller.renderers import negotiate
        body, content_type, _ = negotiate(spec, ctx.request, renderers=renderers)
        
        ctx.response.set_header("Content-Type", content_type)
        return body
```

### XML Renderer Customization

The `XMLRenderer` (lines 170-227) converts Python dicts and lists to XML with configurable tag names:

```python
from aquilia.controller.renderers import XMLRenderer

# Default tags
renderer = XMLRenderer()  # root_tag="response", item_tag="item"

# Custom tags for domain models
renderer = XMLRenderer(root_tag="catalog", item_tag="product")

# Example output:
data = {
    "products": [
        {"id": 1, "name": "Widget", "price": 9.99},
        {"id": 2, "name": "Gadget", "price": 19.99},
    ]
}

# Renders as (lines 187-227):
# <?xml version="1.0" encoding="UTF-8"?>
# <catalog>
#   <products>
#     <product>
#       <id>1</id>
#       <name>Widget</name>
#       <price>9.99</price>
#     </product>
#     <product>
#       <id>2</id>
#       <name>Gadget</name>
#       <price>19.99</price>
#     </product>
#   </products>
# </catalog>
```

**XML tag sanitization** (lines 230-236):
- Replaces invalid characters with underscores
- Prepends underscore if tag starts with digit
- Ensures valid XML element names

### YAML Renderer with Fallback

The `YAMLRenderer` (lines 239-274) provides graceful degradation:

```python
from aquilia.controller.renderers import YAMLRenderer

# Prefers PyYAML if installed (lines 246-251)
renderer = YAMLRenderer()

# Falls back to simple formatter if PyYAML missing (lines 253-274)
# Provides basic YAML structure without full spec compliance
```

**Example with fallback:**
```python
data = {"name": "Product", "tags": ["new", "featured"], "price": 29.99}

# With PyYAML:
# name: Product
# tags:
#   - new
#   - featured
# price: 29.99

# Without PyYAML (simple fallback):
# name: Product
# tags:
# - new
# - featured
# price: 29.99
```

---

**Implementation Evidence:**
- Overview: lines 1-32 (module docstring)
- Built-in renderers: lines 43-294
- Negotiation priority: lines 307-313, 320-363
- BaseRenderer: lines 118-138
- Accept parsing: lines 51-96
- ContentNegotiator: lines 299-363
- negotiate() function: lines 374-394
- MessagePackRenderer: lines 277-294
- Custom renderers: BaseRenderer contract lines 118-138
