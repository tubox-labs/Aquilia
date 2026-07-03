---
title: "Content Negotiation Tutorial"
description: "Serving multiple response formats (JSON, XML, CSV) dynamically based on Accept headers or query params"
icon: lucide/shuffle
---In this tutorial, we will walk through how to build a flexible API endpoint in Aquilia that can serve the same product data as JSON, XML, or CSV. We will leverage Aquilia's built-in content negotiation system and extend it with a custom CSV renderer.

## Prerequisites

Before starting, ensure you have read the primary documentation on [Content Negotiation & Renderers](../controller/renderers.md) to understand how the [ContentNegotiator](../controller/renderers.md#L129) and [BaseRenderer](../controller/renderers.md#L50-L80) operate.

---

## Step 1: JSONRenderer + XMLRenderer on ProductsController

By default, Aquilia controllers use [JSONRenderer](../controller/renderers.md#L23) as the fallback. To support both JSON and XML on your controller, import and register both [JSONRenderer](../controller/renderers.md#L23) and [XMLRenderer](../controller/renderers.md#L24) in the controller's `renderer_classes` attribute.

Create your controller file with the following setup (modeled after the [Multi-format API Endpoint example](../controller/renderers.md#L316-L352)):

```python
from aquilia import Controller, GET
from aquilia.controller.renderers import JSONRenderer, XMLRenderer

class ProductsController(Controller):
    prefix = "/products"
    
    # Registering built-in renderers. Order determines default fallback (JSON)
    renderer_classes = [
        JSONRenderer(indent=2),
        XMLRenderer(root_tag="products", item_tag="product")
    ]
    
    @GET("/")
    async def list_products(self, ctx):
        # Return Python dict/list structures directly; Aquilia handles translation.
        return [
            {"id": 1, "name": "Widget", "price": 9.99},
            {"id": 2, "name": "Gadget", "price": 19.99},
        ]
```

!!! info
    The order of `renderer_classes` defines the priority list. If a client's `Accept` header contains `*/*` or is missing, the negotiator falls back to the first renderer in the list, which is [JSONRenderer](../controller/renderers.md#L23) in this setup (see [Negotiation Priority](../controller/renderers.md#L32-L48)).


---

## Step 2: Testing with Accept Header

With both renderers registered, the [ContentNegotiator](../controller/renderers.md#L129) evaluates incoming `Accept` headers to select the best match based on client preferences (quality factors).

### Test 1: Requesting XML
Send an HTTP request with the `Accept: application/xml` header (as detailed in [Quality Factor Negotiation](../controller/renderers.md#L403-L418)):

```bash
curl -H "Accept: application/xml" http://localhost:8000/products
```

**Response Content-Type:** `application/xml; charset=utf-8`

**Response Body:**
```xml
<?xml version="1.0" encoding="UTF-8"?>
<products>
  <product>
    <id>1</id>
    <name>Widget</name>
    <price>9.99</price>
  </product>
  <product>
    <id>2</id>
    <name>Gadget</name>
    <price>19.99</price>
  </product>
</products>
```

### Test 2: Requesting JSON (Default Fallback)
If no `Accept` header or a wildcard is sent:

```bash
curl http://localhost:8000/products
```

**Response Content-Type:** `application/json; charset=utf-8`

**Response Body:**
```json
[
  {
    "id": 1,
    "name": "Widget",
    "price": 9.99
  },
  {
    "id": 2,
    "name": "Gadget",
    "price": 19.99
  }
]
```

---

## Step 3: ?format=xml Query Parameter Override

Sometimes, browser clients or developers testing in a browser cannot easily manipulate the `Accept` headers. Aquilia provides a built-in query parameter override `?format=` which takes highest priority over headers (proven in [Negotiation Priority](../controller/renderers.md#L32-L48)).

For example, to explicitly request XML format via the URL query parameters:

```bash
curl http://localhost:8000/products?format=xml
```

The negotiator checks the value of `?format=` against each renderer's `format_suffix` (which is `"xml"` for [XMLRenderer](../controller/renderers.md#L24) and `"json"` for [JSONRenderer](../controller/renderers.md#L23)).

!!! warning
    If you pass an invalid format suffix like `?format=invalid`, the negotiator will bypass the parameter and fall back to evaluating the `Accept` header or using the default renderer.


---

## Step 4: Writing a Custom CSVRenderer

To support exporting data to CSV format, we can write a custom renderer by subclassing [BaseRenderer](../controller/renderers.md#L50-L80) and implementing the abstract `render` method (as shown in [Custom Renderer](../controller/renderers.md#L242-L282)).

Create `renderers.py` and write the custom class:

```python
import csv
from io import StringIO
from typing import Any
from aquilia.controller.renderers import BaseRenderer

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
        """Convert list of dicts to CSV string."""
        if not isinstance(data, list) or not data:
            return ""
            
        output = StringIO()
        # Extract headers from the keys of the first dictionary
        writer = csv.DictWriter(
            output,
            fieldnames=data[0].keys(),
            delimiter=self.delimiter
        )
        writer.writeheader()
        writer.writerows(data)
        return output.getvalue()
```

### Verification details:
- **media_type**: `"text/csv"` matches the standard MIME type.
- **format_suffix**: `"csv"` matches standard query params overrides (`?format=csv`).
- **render**: Signature conforms exactly to [BaseRenderer.render](../controller/renderers.md#L62-L71).

---

## Step 5: Registering CSVRenderer

We can register `CSVRenderer` at two levels: controller level (applying to all routes on the controller) and route level (applying only to a specific route via manual negotiation).

### Option A: Controller-Level Registration
Add the renderer class directly to the list of `renderer_classes` on the controller (see [Controller-level renderer_classes](../controller/renderers.md#L111-L130)):

```python
from aquilia import Controller, GET
from aquilia.controller.renderers import JSONRenderer, XMLRenderer
from .renderers import CSVRenderer

class ProductsController(Controller):
    prefix = "/products"
    renderer_classes = [
        JSONRenderer(indent=2),
        XMLRenderer(root_tag="products", item_tag="product"),
        CSVRenderer()  # Added CSV capability
    ]
    
    @GET("/")
    async def list_products(self, ctx):
        return [
            {"id": 1, "name": "Widget", "price": 9.99},
            {"id": 2, "name": "Gadget", "price": 19.99},
        ]
```

Test controller-level CSV selection:
```bash
curl -H "Accept: text/csv" http://localhost:8000/products
# OR
curl http://localhost:8000/products?format=csv
```

### Option B: Route-Level Registration & Manual Negotiation
If you only want specific endpoints to allow CSV downloads, keep the controller class clean and manually invoke [negotiate](../controller/renderers.md#L166-L201) (modeled after [Route-level Override](../controller/renderers.md#L131-L165)):

```python
from aquilia import Controller, GET
from aquilia.controller.renderers import JSONRenderer, XMLRenderer, negotiate
from .renderers import CSVRenderer

class ProductsController(Controller):
    prefix = "/products"
    renderer_classes = [JSONRenderer(), XMLRenderer()]  # Default renderers
    
    @GET("/")
    async def list_products(self, ctx):
        # Default JSON/XML negotiation
        return [
            {"id": 1, "name": "Widget", "price": 9.99},
            {"id": 2, "name": "Gadget", "price": 19.99},
        ]

    @GET("/export")
    async def export_products(self, ctx):
        """Dedicated route offering JSON, XML, and CSV exports."""
        products = [
            {"id": 1, "name": "Widget", "price": 9.99},
            {"id": 2, "name": "Gadget", "price": 19.99},
        ]
        
        # Manually negotiate using route-specific renderer list
        body, content_type, status = negotiate(
            products,
            ctx.request,
            renderers=[JSONRenderer(), XMLRenderer(), CSVRenderer()]
        )
        
        # Apply response details to ctx
        ctx.response.set_header("Content-Type", content_type)
        ctx.response.status = status
        return body
```

!!! info
    By invoking [negotiate](../controller/renderers.md#L166-L201) manually, the controller returns the pre-rendered string/bytes body directly. Be sure to set the `Content-Type` header from `content_type` so the client knows how to parse the result.

