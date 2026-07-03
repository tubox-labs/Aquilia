---
title: "Pagination"
description: "Pagination strategies"
icon: lucide/list-ordered
---## Overview

Aquilia provides three built-in pagination strategies for handling large datasets efficiently (lines 1-13):

- **PageNumberPagination** — Classic page-based navigation using `?page=2&page_size=20`
- **LimitOffsetPagination** — SQL-style pagination using `?limit=20&offset=40`
- **CursorPagination** — Keyset-based pagination using opaque cursor tokens `?cursor=<opaque>` for constant-time page jumps

All pagination backends work seamlessly with both ORM QuerySets and plain Python lists (line 14). Each paginator implements query optimization for ORM queries, using `.count()` and `.offset().limit()` to avoid fetching entire datasets into memory.

## PageNumberPagination

Classic page-number pagination that's intuitive for users and easy to bookmark (lines 166-301).

### Query Parameters

- `page` — Page number (default: 1)
- `page_size` — Items per page (default: 20)

### Configuration

```python
class PageNumberPagination(BasePagination):
    page_size: int = 20              # Default items per page
    max_page_size: int = 1000        # Maximum allowed page size
    page_param: str = "page"         # Query param name for page number
    page_size_param: str = "page_size"  # Query param name for page size
```

**Lines 182-186**: Default configuration attributes. You can customize these at the class level or via constructor:

```python
# Custom pagination class
class LargePagePagination(PageNumberPagination):
    page_size = 100
    max_page_size = 500

# Or instantiate with custom values
paginator = PageNumberPagination(page_size=50, max_page_size=200)
```

### Response Envelope

**Lines 169-181**: PageNumberPagination returns a comprehensive response envelope:

```json
{
    "count": 1200,
    "total_pages": 60,
    "page": 2,
    "page_size": 20,
    "next": "http://host/items/?page=3&page_size=20",
    "previous": "http://host/items/?page=1&page_size=20",
    "results": [...]
}
```

- `count` — Total number of items across all pages
- `total_pages` — Total number of pages
- `page` — Current page number
- `page_size` — Items per page
- `next` / `previous` — Fully-qualified URLs for navigation (null if unavailable)
- `results` — Array of items for the current page

### QuerySet Optimization

**Lines 253-301**: For ORM QuerySets, PageNumberPagination uses optimized queries instead of loading all records:

```python
async def paginate_queryset(self, queryset, request):
    # Uses .count() for total, then .offset().limit() for the page
    total = await queryset.count()
    total_pages = max(1, math.ceil(total / size))
    offset = (page - 1) * size
    items = await queryset.offset(offset).limit(size).all()
```

This avoids loading 1,000,000 records just to return 20 items.

## LimitOffsetPagination

SQL-style pagination using limit and offset parameters (lines 304-414).

### Query Parameters

- `limit` — Maximum items to return (default: 20)
- `offset` — Number of items to skip (default: 0)

### Configuration

```python
class LimitOffsetPagination(BasePagination):
    default_limit: int = 20      # Default page size
    max_limit: int = 1000        # Maximum allowed limit
    limit_param: str = "limit"   # Query param name for limit
    offset_param: str = "offset" # Query param name for offset
```

**Lines 319-323**: Configure defaults at the class level or via constructor.

### Response Envelope

**Lines 307-318**: Returns a simpler envelope without page numbers:

```json
{
    "count": 1200,
    "limit": 20,
    "offset": 40,
    "next": "http://host/items/?limit=20&offset=60",
    "previous": "http://host/items/?limit=20&offset=20",
    "results": [...]
}
```

**Lines 345-376**: Navigation links adjust offset automatically:
- `next` — Advances offset by `limit` (offset 40 → 60)
- `previous` — Moves back by `limit`, clamped to 0 (offset 40 → 20)

### QuerySet Optimization

**Lines 378-414**: Like PageNumberPagination, uses `.count()` and `.offset().limit()` for efficient ORM pagination.

## CursorPagination

Cursor-based (keyset) pagination for very large datasets with constant-time page jumps regardless of size (lines 417-633).

### Query Parameters

- `cursor` — Opaque base64-encoded token pointing to the last item's ordering key
- `page_size` — Items per page (default: 20)

### Configuration

```python
class CursorPagination(BasePagination):
    page_size: int = 20
    max_page_size: int = 1000
    cursor_param: str = "cursor"
    page_size_param: str = "page_size"
    ordering: str = "-id"  # Keyset field (descending ID by default)
```

**Lines 447-452**: The `ordering` field determines which column is used for keyset navigation. Use `-` prefix for descending order.

### Response Envelope

**Lines 429-437**: Returns only navigation links and results (no count, since that would require scanning the entire table):

```json
{
    "next": "http://host/items/?cursor=abc...",
    "previous": "http://host/items/?cursor=xyz...",
    "results": [...]
}
```

### Cursor Generation and Security

**Lines 459-499**: Cursors are HMAC-SHA256 signed to prevent tampering:

```python
def _encode_cursor(self, data: dict[str, Any]) -> str:
    """Encode cursor data with HMAC-SHA256 signature."""
    payload = json.dumps(data, default=str).encode("utf-8")
    sig = hmac.new(self._get_cursor_secret(), payload, hashlib.sha256).digest()
    payload_b64 = base64.urlsafe_b64encode(payload).decode("utf-8").rstrip("=")
    sig_b64 = base64.urlsafe_b64encode(sig).decode("utf-8").rstrip("=")
    return f"{payload_b64}.{sig_b64}"
```

Cursor format: `<base64-payload>.<base64-signature>`

**Lines 463-477**: The HMAC secret is sourced from `AQUILIA_CURSOR_SECRET` environment variable. If not set, an ephemeral per-process key is generated (cursors won't survive restarts):

```python
secret = os.environ.get("AQUILIA_CURSOR_SECRET", "")
if not secret:
    if not hasattr(CursorPagination, "_ephemeral_secret"):
        CursorPagination._ephemeral_secret = os.urandom(32).hex()
        _cursor_logger.warning(
            "AQUILIA_CURSOR_SECRET not set; using ephemeral key. "
            "Cursors will not survive process restarts."
        )
```

**Set `AQUILIA_CURSOR_SECRET` in production** for cursor stability across deployments.

### Keyset Mechanics

**Lines 558-615**: CursorPagination uses WHERE clauses on the ordering field instead of OFFSET, enabling constant-time pagination:

```python
# For "next" on descending order (-id):
qs = qs.filter(**{f"{field_name}__lt": cursor_value})

# For "previous" on descending order:
qs = qs.filter(**{f"{field_name}__gt": cursor_value})
```

This means page 1000 is just as fast as page 1, unlike OFFSET-based pagination which scans and skips rows.

## NoPagination

**Lines 148-157**: Passthrough pagination that returns all results in a standard envelope:

```python
class NoPagination(BasePagination):
    """Passthrough — no pagination applied."""
    
    def paginate_list(self, data: list[Any], request: Any) -> dict[str, Any]:
        return {
            "count": len(data),
            "next": None,
            "previous": None,
            "results": data,
        }
```

Useful for small datasets or when you want consistent response envelopes without actual pagination.

## Declarative Usage

The recommended way to enable pagination is via the `pagination_class` parameter on route decorators (lines 16-24):

```python
from aquilia import Controller, GET
from aquilia.controller.pagination import PageNumberPagination

class ProductsController(Controller):
    prefix = "/products"

    @GET("/", pagination_class=PageNumberPagination)
    async def list_products(self, ctx):
        return await Product.objects.all()  # Framework paginates automatically
```

When `pagination_class` is set:
1. The framework detects if the handler returns a QuerySet or list
2. Calls `paginator.paginate_queryset()` (async) or `paginator.paginate_list()` automatically
3. Returns the paginated envelope as JSON

You can also use custom pagination instances:

```python
@GET("/bulk", pagination_class=PageNumberPagination(page_size=100))
async def bulk_list(self, ctx):
    return await Product.objects.all()
```

## Explicit Usage

For fine-grained control, instantiate a paginator and call `.paginate_list()` or `.paginate_queryset()` manually (lines 26-29):

```python
from aquilia.controller.pagination import PageNumberPagination

class ProductsController(Controller):
    @GET("/products")
    async def list_products(self, ctx):
        products = await Product.objects.all()
        
        paginator = PageNumberPagination(page_size=25)
        page = paginator.paginate_list(products, ctx.request)
        
        # page == {"count": 1200, "next": "...", "previous": "...", "results": [...]}
        return page
```

**Lines 115-126** (BasePagination interface):
- `.paginate_list(data: list, request)` → Paginate in-memory lists
- `.paginate_queryset(queryset, request)` → Paginate ORM QuerySets (async)

## QuerySet vs List Support

**Lines 127-141**: All paginators implement both `paginate_list` and `paginate_queryset`:

```python
class BasePagination:
    def paginate_list(self, data: list[Any], request: Any) -> dict[str, Any]:
        """Paginate an in-memory list."""
        raise NotImplementedError

    async def paginate_queryset(self, queryset: Any, request: Any) -> dict[str, Any]:
        """Paginate an ORM queryset."""
        # Default: fetch all and delegate to paginate_list
        items = await queryset.all()
        serialized = [item.to_dict() if hasattr(item, "to_dict") else item for item in items]
        return self.paginate_list(serialized, request)
```

- **List support**: All paginators work with plain Python lists immediately
- **QuerySet support**: PageNumberPagination, LimitOffsetPagination, and CursorPagination override `paginate_queryset()` with optimized queries
- **Serialization**: Models with `.to_dict()` are automatically converted; others are passed through

## Custom Pagination

Create custom pagination strategies by subclassing `BasePagination` (lines 108-141):

```python
from aquilia.controller.pagination import BasePagination

class HeaderPagination(BasePagination):
    """Pagination using X-Page and X-Page-Size headers."""
    
    def paginate_list(self, data: list, request) -> dict:
        # Parse headers
        page = int(request.headers.get("X-Page", 1))
        size = int(request.headers.get("X-Page-Size", 20))
        
        # Slice data
        start = (page - 1) * size
        results = data[start:start + size]
        
        # Return envelope (you control the structure)
        return {
            "results": results,
            "page": page,
            "total": len(data)
        }
```

**Required method**: `paginate_list(data, request) -> dict`

**Optional method**: `paginate_queryset(queryset, request)` for ORM optimization (async)

Use your custom paginator declaratively:

```python
@GET("/items", pagination_class=HeaderPagination)
async def list_items(self, ctx):
    return await Item.objects.all()
```

## Code Examples

### Page-Number Pagination (Default)

```python
from aquilia import Controller, GET
from aquilia.controller.pagination import PageNumberPagination

class UsersController(Controller):
    prefix = "/users"
    
    @GET("/", pagination_class=PageNumberPagination)
    async def list_users(self, ctx):
        return await User.objects.all()

# GET /users?page=2&page_size=50
# Returns:
# {
#   "count": 1200,
#   "total_pages": 24,
#   "page": 2,
#   "page_size": 50,
#   "next": "http://localhost/users?page=3&page_size=50",
#   "previous": "http://localhost/users?page=1&page_size=50",
#   "results": [...]
# }
```

### Limit-Offset Pagination

```python
from aquilia.controller.pagination import LimitOffsetPagination

class OrdersController(Controller):
    @GET("/orders", pagination_class=LimitOffsetPagination)
    async def list_orders(self, ctx):
        return await Order.objects.filter(status="shipped")

# GET /orders?limit=20&offset=40
# Returns:
# {
#   "count": 500,
#   "limit": 20,
#   "offset": 40,
#   "next": "http://localhost/orders?limit=20&offset=60",
#   "previous": "http://localhost/orders?limit=20&offset=20",
#   "results": [...]
# }
```

### Cursor Pagination for Large Datasets

```python
from aquilia.controller.pagination import CursorPagination

class LogsController(Controller):
    @GET("/logs", pagination_class=CursorPagination(ordering="-created_at"))
    async def list_logs(self, ctx):
        return await Log.objects.all()

# GET /logs?cursor=<opaque>&page_size=100
# Returns:
# {
#   "next": "http://localhost/logs?cursor=eyJ2Ij...",
#   "previous": "http://localhost/logs?cursor=eyJ2Ij...",
#   "results": [...]
# }
```

**Lines 447-452**: Set `ordering` to control the keyset field. Use `-` prefix for descending (newest first).

### Custom Page Size per Route

```python
class ProductsController(Controller):
    # Small pages for thumbnails
    @GET("/thumbnails", pagination_class=PageNumberPagination(page_size=50))
    async def thumbnails(self, ctx):
        return await Product.objects.all()
    
    # Large pages for exports
    @GET("/export", pagination_class=PageNumberPagination(page_size=500, max_page_size=1000))
    async def export(self, ctx):
        return await Product.objects.all()
```

### Manual Pagination with Filters

```python
from aquilia.controller.pagination import PageNumberPagination

class SearchController(Controller):
    @GET("/search")
    async def search(self, ctx):
        query = ctx.request.query_params.get("q", "")
        
        # Apply filters
        results = await Product.objects.filter(name__icontains=query).all()
        
        # Paginate manually
        paginator = PageNumberPagination(page_size=20)
        return paginator.paginate_list(results, ctx.request)
```

### No Pagination (Return All)

```python
from aquilia.controller.pagination import NoPagination

class MetadataController(Controller):
    @GET("/categories", pagination_class=NoPagination)
    async def categories(self, ctx):
        return await Category.objects.all()

# Returns:
# {
#   "count": 15,
#   "next": null,
#   "previous": null,
#   "results": [...]  # All 15 items
# }
```

### Pagination with Plain Lists

```python
class StaticController(Controller):
    @GET("/features", pagination_class=PageNumberPagination)
    async def features(self, ctx):
        # No ORM — return a plain list
        features = [
            {"name": "Fast", "description": "..."},
            {"name": "Secure", "description": "..."},
            # ... 100 items
        ]
        return features  # Framework paginates automatically

# GET /features?page=1&page_size=10
# Works identically to QuerySet pagination
```

---

**Source Evidence**: All line references cite `/Users/kuroyami/TuboxLabProject/aquilia_docs/aquilia/controller/pagination.py`
