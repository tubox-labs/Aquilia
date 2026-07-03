---
title: "Filtering, Search & Pagination Tutorial"
description: "How to configure complex list endpoints with search, ordering, filter backends, and pagination"
icon: lucide/sliders
---# Add search, filter, and pagination to a list endpoint

This tutorial guides you through adding search, filtering, sorting, and pagination to an API list endpoint using Aquilia. You will learn how to configure these features both individually and combined into a single, high-performance route handler.

## Scenario: Product Catalog with 10,000 Products

Imagine you are building a product listing API. Your database has **10,000 products** spanning multiple categories, prices, and creation dates. 

Returning all 10,000 products in a single request would:
- Degrade database and network performance.
- Overwhelm client applications.
- Cause high memory usage on the server.

To solve this, we will implement filtering, search, ordering, and pagination step-by-step.

---

## Step 1: FilterSet with Price Range & Category Exact

`FilterSet` provides declarative field-based filtering. We will configure a `ProductFilter` that allows users to filter by category (exact match) and price (greater than or equal, less than or equal, or a range).

```python
from aquilia import FilterSet

class ProductFilter(FilterSet):
    class Meta:
        fields = {
            "category": ["exact"],
            "price": ["gte", "lte", "range"],
        }
```

### How It Works
- **Category Filter**: Matches the category exactly.
  Query: `GET /products?category=electronics`
- **Price Filters**: 
  - `price__gte=50` (Greater than or equal to 50)
  - `price__lte=150` (Less than or equal to 150)
  - `price__range=50,150` (Between 50 and 150, comma-separated list value)

> [!NOTE]
> According to the **[Filtering Documentation](../controller/filtering.md#L42-L135)**, Aquilia automatically coerces query string values into their correct Python types, such as converting comma-separated values to lists for `range` lookups and strings to floats for numeric queries.

---

## Step 2: Adding search_fields for Name + Description

Often, users need a free-text search across multiple fields instead of strict filters. Aquilia provides the `search_fields` parameter on the route decorator to enable case-insensitive text search.

We will configure search to look up keywords in the `name` and `description` fields:

```python
# Decorator configuration:
search_fields=["name", "description"]
```

### Behavior
- When a client sends `?search=wireless`, Aquilia builds an `OR` query under the hood:
  `name__icontains="wireless" | description__icontains="wireless"`
- An item is returned if the term matches **any** of the configured search fields.

> [!NOTE]
> As described in the **[SearchFilter documentation](../controller/filtering.md#L185-L254)**, text search handles both ORM querysets (building `QNode` OR chains) and in-memory lists (case-insensitive substring checks) seamlessly.

---

## Step 3: Configuring ordering_fields for Price & Created At

Users expect to sort lists by relevant columns like cheapest price or newest products. `OrderingFilter` enables dynamic field ordering based on the `?ordering` query parameter.

We will whitelist `price` and `created_at` for ordering:

```python
# Decorator configuration:
ordering_fields=["price", "created_at"]
```

### Query Syntax
- **Ascending**: `GET /products?ordering=price` (sorts cheapest first)
- **Descending**: `GET /products?ordering=-price` (sorts most expensive first, using the `-` prefix)
- **Multiple fields**: `GET /products?ordering=-created_at,price` (newest first, then by price ascending)

> [!IMPORTANT]
> As shown in the **[OrderingFilter security section](../controller/filtering.md#L277-L290)**, only fields present in `ordering_fields` are allowed. Arbitrary query fields are ignored to prevent database index abuse or exposure of hidden fields.

---

## Step 4: PageNumberPagination (page + page_size)

For a classic paginated interface (e.g., desktop search results with `[1] [2] [3] ... [Next]`), `PageNumberPagination` is the default approach.

We can define a custom pagination class:

```python
from aquilia.controller.pagination import PageNumberPagination

class ProductPageNumberPagination(PageNumberPagination):
    page_size = 20          # Default items per page
    max_page_size = 100     # Prevent clients requesting too many items
```

### Query Parameters
- `page` (default: `1`)
- `page_size` (default: `20`, client can increase it up to `100`)

### Response Envelope
The response is automatically wrapped in a structured metadata object (see **[PageNumberPagination Response Envelope](../controller/pagination.md#L47-L68)**):

```json
{
    "count": 10000,
    "total_pages": 500,
    "page": 1,
    "page_size": 20,
    "next": "http://host/products?page=2&page_size=20",
    "previous": null,
    "results": [...]
}
```

---

## Step 5: LimitOffsetPagination (limit + offset)

For developers preferred to SQL-style syntax (`LIMIT 20 OFFSET 40`), `LimitOffsetPagination` is ideal.

```python
from aquilia.controller.pagination import LimitOffsetPagination

class ProductLimitOffsetPagination(LimitOffsetPagination):
    default_limit = 20
    max_limit = 100
```

### Query Parameters
- `limit` (default: `20`)
- `offset` (default: `0`)

### Response Envelope
This envelope omits absolute page numbers but details exact slices (see **[LimitOffsetPagination Response Envelope](../controller/pagination.md#L106-L124)**):

```json
{
    "count": 10000,
    "limit": 20,
    "offset": 20,
    "next": "http://host/products?limit=20&offset=40",
    "previous": "http://host/products?limit=20&offset=0",
    "results": [...]
}
```

---

## Step 6: CursorPagination (Keyset for Infinite Scroll)

When dealing with a dynamic catalog of 10,000 products, offset-based pagination (Steps 4 & 5) suffers from two major limitations:
1. **Performance**: Large offsets (e.g. `OFFSET 9980`) require database engines to scan and discard rows, leading to slow response times.
2. **Duplicate Items**: If a new product is added to the database while a user is scrolling, items shift pages, causing duplicates to appear.

`CursorPagination` solves this by using keyset pagination: filtering queries by the unique ordering value (e.g. `WHERE id < last_seen_id`) instead of skipping rows.

```python
from aquilia.controller.pagination import CursorPagination

class ProductCursorPagination(CursorPagination):
    page_size = 20
    ordering = "-id"  # Keyset field (must be indexed, unique, and ordered)
```

### Query Parameters
- `cursor` — Opaque base64-encoded token pointing to the last item
- `page_size` (default: `20`)

### Response Envelope
This envelope does **not** include the total `count` (avoiding expensive table scans):

```json
{
    "next": "http://host/products?cursor=eyJ2IjogMSwgIm8iOiBbIi1pZCJdLCAicCI6IFsxMDBdfQ==",
    "previous": null,
    "results": [...]
}
```

> [!WARNING]
> According to the **[Cursor Pagination Security details](../controller/pagination.md#L163-L192)**, cursor tokens are HMAC-SHA256 signed. You **must** set the `AQUILIA_CURSOR_SECRET` environment variable in production. Otherwise, an ephemeral per-process secret is used, causing cursors to break whenever the application restarts or scaling events occur.

---

## Step 7: Combining Filtering, Search, Ordering & Pagination in One Route

Aquilia's routing engine handles the complexity of applying all of these backends in a structured, optimized pipeline. By providing these options on a single route, they apply in sequence:

1. **FilterSet** (Filters by category and price range)
2. **SearchFilter** (Narrows results containing search query)
3. **OrderingFilter** (Applies ordering specifications)
4. **Pagination** (Applies page limits and offsets/keysets to return the final slice)

Here is the complete implementation:

```python
from aquilia import Controller, GET
from aquilia.controller.filters import FilterSet
from aquilia.controller.pagination import PageNumberPagination

# 1. Declare the FilterSet
class ProductFilter(FilterSet):
    class Meta:
        fields = {
            "category": ["exact"],
            "price": ["gte", "lte", "range"],
        }

# 2. Declare the Pagination class
class ProductPagination(PageNumberPagination):
    page_size = 20
    max_page_size = 100

# 3. Create the Controller
class ProductsController(Controller):
    prefix = "/products"
    
    @GET(
        "/",
        filterset_class=ProductFilter,
        search_fields=["name", "description"],
        ordering_fields=["price", "created_at"],
        pagination_class=ProductPagination
    )
    async def list_products(self, ctx):
        """
        List products with full support for filters, search, sorting, and pagination.
        """
        # Simply return the queryset. The engine automatically compiles
        # and applies the database-optimized filtering, sorting, and pagination steps.
        return await Product.objects.all()
```

> [!TIP]
> As explained in **[Auto-Application](../controller/filtering.md#L456-L519)**, return the database query directly (like `await Product.objects.all()`). Returning a raw response object (such as `JSONResponse`) will bypass the auto-filtering engine.

---

## Step 8: Testing Query Parameters

You can test the endpoint using standard query parameters. Let's look at how the route behaves across different requests.

### 1. Basic Filtering
Filter the product catalog to only include items in the `electronics` category that cost between `$100` and `$500`:

```bash
GET /products?category=electronics&price__range=100,500
```
- **Filter Applied**: Category exact match + price between 100 and 500.
- **Result**: Page 1 of matching electronics, ordered by default database order.

### 2. Search, Sort, and Custom Page Size
Search for "wireless" products, sort them by price descending, and request 10 items:

```bash
GET /products?search=wireless&ordering=-price&page_size=10
```
- **Search Applied**: Looks for "wireless" in `name` or `description`.
- **Ordering Applied**: Descending price.
- **Pagination Applied**: Limits results to the first 10 items.

### 3. Combining All Parameters
Query for products in the `appliances` category with a price greater than `$50`, containing the term "smart", sorted by creation date descending, on page 2:

```bash
GET /products?category=appliances&price__gte=50&search=smart&ordering=-created_at&page=2
```

### Summary of Combined Query Parameters
The following table highlights the query parameters and their behavior:

| Query Parameter | Example | Strategy | Reference |
| :--- | :--- | :--- | :--- |
| `category` | `?category=electronics` | exact match filtering | [FilterSet Documentation](../controller/filtering.md#L75-L102) |
| `price__range` | `?price__range=10,100` | range filtering | [FilterSet Documentation](../controller/filtering.md#L46-L74) |
| `search` | `?search=term` | text search (any of fields) | [SearchFilter Documentation](../controller/filtering.md#L185-L205) |
| `ordering` | `?ordering=-price` | ascending or descending sort | [OrderingFilter Documentation](../controller/filtering.md#L256-L276) |
| `page` / `page_size` | `?page=2&page_size=10` | page-number pagination | [PageNumberPagination](../controller/pagination.md#L16-L84) |
| `limit` / `offset` | `?limit=10&offset=20` | limit-offset pagination | [LimitOffsetPagination](../controller/pagination.md#L85-L128) |
| `cursor` | `?cursor=opaque...` | keyset pagination | [CursorPagination](../controller/pagination.md#L129-L207) |
