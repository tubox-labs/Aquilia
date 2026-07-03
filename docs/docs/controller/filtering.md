---
title: "Filtering, Search & Ordering"
description: "Filter, search, and order querysets"
icon: lucide/filter
---## Overview

Aquilia's filter system provides declarative filtering, searching, and ordering for your API endpoints. The system automatically parses query parameters and applies them to both ORM querysets and in-memory lists (lines 1-30).

Key features:

- **FilterSet**: Declarative field-based filtering with 20+ lookup types
- **SearchFilter**: Multi-field text search via `?search=<term>`
- **OrderingFilter**: Dynamic ordering via `?ordering=<field>`
- **Custom backends**: Implement `BaseFilterBackend` for full control
- **ReDoS prevention**: Built-in regex safety guards
- **Auto-application**: Filters apply automatically when configured on routes

```python
from aquilia import Controller, GET, FilterSet, SearchFilter, OrderingFilter

class ProductFilter(FilterSet):
    class Meta:
        fields = {
            "category": ["exact"],
            "price": ["gte", "lte", "range"],
            "is_active": ["exact"],
            "name": ["icontains"],
        }

class ProductsController(Controller):
    prefix = "/products"
    
    @GET("/", filterset_class=ProductFilter,
         search_fields=["name", "description"],
         ordering_fields=["price", "created_at", "name"])
    async def list_products(self, ctx):
        products = await Product.objects.all()
        return products  # engine auto-applies filter → search → order
```

## FilterSet (declarative field filtering, lookup types)

`FilterSet` provides declarative field-based filtering with support for 20+ lookup operators (lines 289-369). Define a class with a `Meta` inner class specifying which fields and lookups to enable.

### Supported Lookup Types

The system supports extensive lookup operators (lines 98-122):

| Lookup | Description | Example Query |
|--------|-------------|---------------|
| `exact` | Exact match (default) | `?status=active` |
| `iexact` | Case-insensitive exact match | `?name__iexact=john` |
| `contains` | Substring match (case-sensitive) | `?title__contains=Python` |
| `icontains` | Substring match (case-insensitive) | `?title__icontains=python` |
| `startswith` | Starts with | `?code__startswith=PRD` |
| `istartswith` | Starts with (case-insensitive) | `?code__istartswith=prd` |
| `endswith` | Ends with | `?email__endswith=@example.com` |
| `iendswith` | Ends with (case-insensitive) | `?email__iendswith=@EXAMPLE.COM` |
| `gt` | Greater than | `?price__gt=100` |
| `gte` | Greater than or equal | `?price__gte=100` |
| `lt` | Less than | `?price__lt=500` |
| `lte` | Less than or equal | `?price__lte=500` |
| `in` | In list (comma-separated) | `?status__in=active,pending` |
| `range` | Between two values | `?price__range=100,500` |
| `isnull` | Is null (true/false) | `?deleted_at__isnull=false` |
| `regex` | Regex match | `?sku__regex=^[A-Z]{3}` |
| `iregex` | Regex match (case-insensitive) | `?sku__iregex=^[a-z]{3}` |
| `ne` | Not equal | `?status__ne=deleted` |
| `date` | Date portion of datetime | `?created_at__date=2024-01-15` |
| `year` | Year of date/datetime | `?created_at__year=2024` |
| `month` | Month of date/datetime | `?created_at__month=12` |
| `day` | Day of date/datetime | `?created_at__day=25` |

### Basic Usage

```python
class ProductFilter(FilterSet):
    class Meta:
        fields = {
            "category": ["exact", "in"],
            "price": ["gte", "lte", "range"],
            "is_active": ["exact"],
            "name": ["icontains"],
            "created_at": ["date", "year", "month"],
        }

# In your controller
@GET("/products", filterset_class=ProductFilter)
async def list_products(self, ctx):
    products = await Product.objects.all()
    return products
```

Query examples:
```
GET /products?category=electronics
GET /products?price__gte=100&price__lte=500
GET /products?name__icontains=laptop
GET /products?category__in=electronics,books
GET /products?created_at__year=2024
```

### Custom Filter Methods

Define `filter_<field>` methods to override default behavior (lines 340-352):

```python
class ProductFilter(FilterSet):
    class Meta:
        fields = {"category": ["exact"], "price": ["gte", "lte"]}
    
    def filter_category(self, value: str) -> dict:
        """Map 'sale' to special clause"""
        if value == "sale":
            return {"discount__gt": 0}
        return {"category": value}
    
    def filter_price(self, value: str) -> dict:
        """Custom price logic"""
        price = float(value)
        if price == 0:
            return {"is_free": True}
        return {"price": price}
```

### Value Coercion

Query string values are automatically coerced to appropriate Python types (lines 127-159):

- **Numeric**: `"123"` → `123`, `"12.5"` → `12.5`
- **Boolean**: `"true"`, `"false"`, `"1"`, `"0"`, `"yes"`, `"no"`, `"on"`
- **Dates**: ISO 8601 formats (`YYYY-MM-DD`, `YYYY-MM-DDTHH:MM:SS`)
- **Lists**: Comma-separated for `in` and `range` lookups

### Manual Usage

Use FilterSet outside the auto-application system (lines 370-387):

```python
# Parse query params
fs = ProductFilter(request=request)
clauses = fs.parse()  # {"category": "electronics", "price__gte": 100}

# Apply to queryset
filtered = await fs.filter_queryset(Product.objects.all())

# Apply to in-memory list
data = [{"name": "Book", "price": 20}, {"name": "Pen", "price": 5}]
filtered = fs.filter_list(data)
```

## filterset_fields Shorthand

For simple exact-match filtering, use `filterset_fields` instead of creating a FilterSet class (lines 490-510):

```python
# List form - exact match only
@GET("/products", filterset_fields=["status", "category", "is_active"])
async def list_products(self, ctx):
    products = await Product.objects.all()
    return products
```

Query: `GET /products?status=active&category=electronics`

For multiple lookups per field, use dict form:

```python
# Dict form - specify lookups
@GET("/products", filterset_fields={
    "status": ["exact", "in"],
    "price": ["gte", "lte", "range"],
    "name": ["icontains"],
})
async def list_products(self, ctx):
    products = await Product.objects.all()
    return products
```

Query: `GET /products?price__gte=100&name__icontains=laptop`

The engine creates an ad-hoc FilterSet class internally (lines 497-503).

## SearchFilter (search param, search_fields)

`SearchFilter` enables multi-field text search via a single `?search=` query parameter (lines 431-467).

### Configuration

```python
@GET("/products", search_fields=["name", "description", "sku"])
async def list_products(self, ctx):
    products = await Product.objects.all()
    return products
```

Query: `GET /products?search=laptop`

### Behavior

- **ORM mode**: Builds an OR chain with `icontains` lookups (lines 452-461)
- **List mode**: Case-insensitive substring match across all search fields (lines 443-449)
- An item matches if **any** search field contains the search term

### Custom Search Parameter

Change the query parameter name (line 438):

```python
class CustomSearchFilter(SearchFilter):
    search_param = "q"  # Use ?q= instead of ?search=

@GET("/products", filter_backends=[CustomSearchFilter()], 
     search_fields=["name", "description"])
async def list_products(self, ctx):
    products = await Product.objects.all()
    return products
```

Query: `GET /products?q=laptop`

### ORM Implementation

For ORM querysets, SearchFilter builds a Q-node OR chain (lines 452-461):

```python
# For search_fields=["name", "description"] and search="laptop"
# Generates: name__icontains="laptop" | description__icontains="laptop"
nodes = [QNode(**{f"{f}__icontains": term}) for f in search_fields]
combined = nodes[0]
for n in nodes[1:]:
    combined = combined | n
return queryset.apply_q(combined)
```

### In-Memory Implementation

For lists, uses case-insensitive substring matching (lines 271-283):

```python
def apply_search_to_list(
    data: list[Any],
    search_term: str,
    search_fields: list[str],
) -> list[Any]:
    """An item passes if **any** search field contains search_term"""
    term_lower = search_term.lower()
    return [
        item for item in data 
        if any(term_lower in str(_get_nested(item, f) or "").lower() 
               for f in search_fields)
    ]
```

## OrderingFilter (ordering param, minus-prefix)

`OrderingFilter` enables dynamic field ordering via `?ordering=` query parameter (lines 470-515).

### Configuration

```python
@GET("/products", ordering_fields=["price", "created_at", "name"])
async def list_products(self, ctx):
    products = await Product.objects.all()
    return products
```

### Query Syntax

```
GET /products?ordering=price          # Ascending by price
GET /products?ordering=-price         # Descending by price (minus prefix)
GET /products?ordering=-price,name    # Multiple fields: desc price, then asc name
```

### Security: Field Whitelisting

Only fields in `ordering_fields` are allowed (lines 491-497). This prevents arbitrary field access:

```python
def _get_ordering(self, request, *, ordering_fields=None):
    raw = request.query_params.get(self.ordering_param, "").strip()
    requested = [f.strip() for f in raw.split(",") if f.strip()]
    if not ordering_fields:
        return requested
    # Whitelist check
    allowed = set(ordering_fields)
    return [f for f in requested if f.lstrip("-") in allowed]
```

### Custom Ordering Parameter

```python
class CustomOrderingFilter(OrderingFilter):
    ordering_param = "sort"  # Use ?sort= instead of ?ordering=

@GET("/products", filter_backends=[CustomOrderingFilter()],
     ordering_fields=["price", "name"])
async def list_products(self, ctx):
    products = await Product.objects.all()
    return products
```

Query: `GET /products?sort=-price,name`

### In-Memory Implementation

For lists, uses a custom comparator (lines 286-315):

```python
def apply_ordering_to_list(data: list[Any], ordering: list[str]) -> list[Any]:
    """Sort by one or more fields. Prefix '-' for descending."""
    def _compare(a: Any, b: Any) -> int:
        for field_spec in ordering:
            desc = field_spec.startswith("-")
            field_name = field_spec.lstrip("-")
            va = _get_nested(a, field_name)
            vb = _get_nested(b, field_name)
            # Handle None values
            if va is None and vb is None:
                continue
            if va is None:
                return 1 if not desc else -1
            if vb is None:
                return -1 if not desc else 1
            if va < vb:
                return 1 if desc else -1
            if va > vb:
                return -1 if desc else 1
        return 0
    return sorted(data, key=functools.cmp_to_key(_compare))
```

## BaseFilterBackend (custom backends)

Create custom filter backends by subclassing `BaseFilterBackend` (lines 403-428):

```python
class BaseFilterBackend:
    """Abstract base for pluggable filter backends."""
    
    def filter_data(self, data: list[Any], request: Any, **options: Any) -> list[Any]:
        """Filter an in-memory list. Return the filtered list."""
        return data
    
    async def filter_queryset(self, queryset: Any, request: Any, **options: Any) -> Any:
        """Filter an ORM queryset. Return the filtered queryset."""
        return queryset
```

### Custom Backend Example

```python
class TenantFilter(BaseFilterBackend):
    """Filter by tenant from authenticated user"""
    
    async def filter_queryset(self, queryset: Any, request: Any, **options: Any) -> Any:
        user = request.state.user
        if not user.is_superuser:
            return queryset.filter(tenant_id=user.tenant_id)
        return queryset
    
    def filter_data(self, data: list[Any], request: Any, **options: Any) -> list[Any]:
        user = request.state.user
        if not user.is_superuser:
            return [item for item in data if item.get("tenant_id") == user.tenant_id]
        return data

# Use in controller
@GET("/products", filter_backends=[TenantFilter()])
async def list_products(self, ctx):
    products = await Product.objects.all()
    return products
```

### Combining Multiple Backends

Backends are applied in sequence:

```python
@GET("/products",
     filter_backends=[TenantFilter(), AuditFilter()],
     filterset_class=ProductFilter,
     search_fields=["name"],
     ordering_fields=["price"])
async def list_products(self, ctx):
    # Applied in order:
    # 1. TenantFilter
    # 2. AuditFilter  
    # 3. ProductFilter (filterset_class)
    # 4. SearchFilter (search_fields)
    # 5. OrderingFilter (ordering_fields)
    products = await Product.objects.all()
    return products
```

## ReDoS Prevention

The filter system includes built-in protection against Regular Expression Denial of Service (ReDoS) attacks (lines 40-96).

### Safety Mechanisms

1. **Length limit**: Regex patterns limited to 256 characters (line 47)
2. **Pattern detection**: Rejects dangerous constructs (lines 50-54):
   - `(a+)+` or `(a*)*` — nested quantifiers
   - `(a|a)+` — alternation amplifiers
   - `.+.+` — multiple greedy wildcards

3. **Syntax validation**: Catches invalid regex syntax (lines 69-75)

### Implementation

```python
_MAX_REGEX_LENGTH: int = 256

_DANGEROUS_REGEX_PATTERNS: tuple[re.Pattern, ...] = (
    re.compile(r"\(.*[\+\*].*\)[\+\*]"),  # (a+)+ or (a*)*
    re.compile(r"\(.*\|.*\)[\+\*]"),       # (a|a)+ alternation amplifier
    re.compile(r"\.[\+\*].*\.[\+\*]"),     # .+.+ nested quantifiers
)

def _safe_regex_compile(pattern: str, flags: int = 0) -> re.Pattern:
    """Compile with safety guards against ReDoS."""
    if len(pattern) > _MAX_REGEX_LENGTH:
        raise ConfigInvalidFault(
            key="filter.regex_pattern",
            reason=f"Regex pattern too long ({len(pattern)} chars, max {_MAX_REGEX_LENGTH})"
        )
    
    for dangerous in _DANGEROUS_REGEX_PATTERNS:
        if dangerous.search(pattern):
            raise ConfigInvalidFault(
                key="filter.regex_pattern",
                reason="Pattern contains constructs that may cause catastrophic backtracking"
            )
    
    return re.compile(pattern, flags)
```

### Usage

ReDoS protection is automatic for `regex` and `iregex` lookups (lines 218-223):

```python
# Safe - automatically validated
@GET("/products", filterset_fields={"sku": ["regex"]})
async def list_products(self, ctx):
    products = await Product.objects.all()
    return products

# Query: GET /products?sku__regex=^[A-Z]{3}  ✓ Safe
# Query: GET /products?sku__regex=(a+)+      ✗ Rejected
```

## Auto-Application

When you configure filters on a route decorator, the Controller engine automatically applies them to the returned data (lines 17-30, 477-527).

### How It Works

1. You return a queryset or list from your route handler
2. The engine detects filter configuration on the route
3. Filters apply in this order:
   - Custom `filter_backends`
   - `filterset_class` or `filterset_fields`
   - `search_fields` (SearchFilter)
   - `ordering_fields` (OrderingFilter)

### Example

```python
class ProductsController(Controller):
    @GET("/", 
         filterset_class=ProductFilter,
         search_fields=["name", "description"],
         ordering_fields=["price", "created_at"])
    async def list_products(self, ctx):
        # Just return the queryset - engine handles the rest
        return await Product.objects.all()
```

Equivalent to:

```python
async def list_products(self, ctx):
    qs = await Product.objects.all()
    
    # 1. Apply FilterSet
    if filterset_class:
        qs = await filterset_class(request=ctx.request).filter_queryset(qs)
    
    # 2. Apply SearchFilter
    if search_fields:
        qs = await SearchFilter().filter_queryset(qs, ctx.request, 
                                                   search_fields=search_fields)
    
    # 3. Apply OrderingFilter
    if ordering_fields:
        qs = await OrderingFilter().filter_queryset(qs, ctx.request,
                                                     ordering_fields=ordering_fields)
    
    return qs
```

### Disabling Auto-Application

Return data wrapped in a response object to bypass auto-filtering:

```python
from aquilia.response import JSONResponse

@GET("/", filterset_class=ProductFilter)
async def list_products(self, ctx):
    products = await Product.objects.all()
    # Return response object - no auto-filtering
    return JSONResponse({"products": products})
```

## Standalone Functions (filter_data, filter_queryset)

Use the standalone functions for manual filtering outside the Controller system (lines 477-568).

### filter_queryset (ORM)

Apply filters to an ORM queryset (lines 477-514):

```python
from aquilia.controller.filters import filter_queryset

async def get_filtered_products(request):
    qs = Product.objects.all()
    
    filtered = await filter_queryset(
        qs,
        request,
        filterset_class=ProductFilter,
        search_fields=["name", "description"],
        ordering_fields=["price", "created_at"],
    )
    
    return await filtered.all()
```

### filter_data (in-memory lists)

Apply filters to in-memory lists or dicts (lines 517-568):

```python
from aquilia.controller.filters import filter_data

def get_filtered_products(request):
    products = [
        {"name": "Laptop", "price": 1200, "category": "electronics"},
        {"name": "Book", "price": 20, "category": "books"},
        {"name": "Pen", "price": 5, "category": "stationery"},
    ]
    
    filtered = filter_data(
        products,
        request,
        filterset_fields={"category": ["exact"], "price": ["gte", "lte"]},
        search_fields=["name"],
        ordering_fields=["price", "name"],
    )
    
    return filtered
```

### Parameters

Both functions accept the same parameters:

- `filterset_class`: FilterSet class to use
- `filterset_fields`: Shorthand dict/list for ad-hoc filtering
- `search_fields`: List of fields for text search
- `ordering_fields`: List of fields allowed for ordering

### Ad-hoc FilterSet Creation

When using `filterset_fields`, an ad-hoc FilterSet is created internally (lines 497-503, 547-553):

```python
# If list/tuple, convert to dict with ["exact"]
if isinstance(filterset_fields, (list, tuple)):
    field_dict = {f: ["exact"] for f in filterset_fields}
else:
    field_dict = dict(filterset_fields)

# Create ad-hoc FilterSet class
_Meta = type("Meta", (), {"fields": field_dict})
adhoc = type("_AdhocFilter", (FilterSet,), {"Meta": _Meta})
fs = adhoc(request=request)
```

## Complete Example

Here's a comprehensive example combining all filter features:

```python
from aquilia import Controller, GET
from aquilia.controller.filters import FilterSet, BaseFilterBackend

# Custom filter backend
class TenantFilter(BaseFilterBackend):
    """Automatically filter by user's tenant"""
    
    async def filter_queryset(self, queryset: Any, request: Any, **options: Any) -> Any:
        user = request.state.user
        if not user.is_superuser:
            return queryset.filter(tenant_id=user.tenant_id)
        return queryset

# Declarative FilterSet
class ProductFilter(FilterSet):
    class Meta:
        fields = {
            "category": ["exact", "in"],
            "price": ["gte", "lte", "range"],
            "is_active": ["exact"],
            "name": ["icontains", "startswith"],
            "created_at": ["date", "year", "month", "gte", "lte"],
            "stock": ["gt", "gte", "lt", "lte"],
        }
    
    def filter_category(self, value: str) -> dict:
        """Map 'sale' category to discount filter"""
        if value == "sale":
            return {"discount__gt": 0, "is_active": True}
        if value == "new":
            return {"created_at__gte": datetime.now() - timedelta(days=30)}
        return {"category": value}

# Controller with all filter types
class ProductsController(Controller):
    prefix = "/api/products"
    
    @GET("/",
         filter_backends=[TenantFilter()],           # 1. Custom tenant filtering
         filterset_class=ProductFilter,              # 2. Declarative field filtering
         search_fields=["name", "description", "sku"],  # 3. Text search
         ordering_fields=["price", "created_at", "name", "stock"])  # 4. Ordering
    async def list_products(self, ctx):
        """
        List products with filtering, search, and ordering.
        
        Query examples:
            GET /api/products?category=electronics
            GET /api/products?price__gte=100&price__lte=500
            GET /api/products?name__icontains=laptop
            GET /api/products?category__in=electronics,books
            GET /api/products?is_active=true
            GET /api/products?created_at__year=2024
            GET /api/products?search=laptop
            GET /api/products?ordering=-price,name
            GET /api/products?category=sale&search=laptop&ordering=-price
        """
        products = await Product.objects.all()
        return products  # Engine auto-applies all filters
    
    @GET("/{product_id}")
    async def get_product(self, ctx, product_id: int):
        """Get single product - no filtering"""
        return await Product.objects.get(id=product_id)
    
    @GET("/simple", filterset_fields=["category", "is_active"])
    async def list_simple(self, ctx):
        """Simple filtering with shorthand syntax"""
        products = await Product.objects.all()
        return products
    
    @GET("/advanced", filterset_fields={
        "price": ["gte", "lte"],
        "stock": ["gt", "gte"],
        "category": ["exact", "in"],
    })
    async def list_advanced(self, ctx):
        """Advanced filtering without FilterSet class"""
        products = await Product.objects.all()
        return products

# Manual usage example
async def background_task(request):
    """Use filters outside controller routes"""
    from aquilia.controller.filters import filter_queryset
    
    qs = Product.objects.all()
    
    filtered = await filter_queryset(
        qs,
        request,
        filterset_class=ProductFilter,
        search_fields=["name", "description"],
        ordering_fields=["price"],
    )
    
    return await filtered.all()

# In-memory filtering example
def filter_local_data(request):
    """Filter in-memory data structures"""
    from aquilia.controller.filters import filter_data
    
    products = [
        {"name": "Laptop", "price": 1200, "category": "electronics", "stock": 5},
        {"name": "Book", "price": 20, "category": "books", "stock": 100},
        {"name": "Pen", "price": 5, "category": "stationery", "stock": 500},
    ]
    
    filtered = filter_data(
        products,
        request,
        filterset_fields={
            "category": ["exact"],
            "price": ["gte", "lte"],
            "stock": ["gt"],
        },
        search_fields=["name"],
        ordering_fields=["price", "stock"],
    )
    
    return filtered
```

### Query Examples

```bash
# Basic filtering
GET /api/products?category=electronics
GET /api/products?is_active=true

# Range filtering
GET /api/products?price__gte=100&price__lte=500
GET /api/products?created_at__year=2024&created_at__month=12

# Text search
GET /api/products?name__icontains=laptop
GET /api/products?name__startswith=Mac

# List filtering
GET /api/products?category__in=electronics,books,computers

# Search across multiple fields
GET /api/products?search=laptop

# Ordering
GET /api/products?ordering=price
GET /api/products?ordering=-price          # Descending
GET /api/products?ordering=-price,name     # Multiple fields

# Combined
GET /api/products?category=electronics&price__gte=500&search=laptop&ordering=-price

# Custom filter method
GET /api/products?category=sale            # Maps to discount__gt=0
GET /api/products?category=new             # Maps to created_at__gte=(30 days ago)

# Null checks
GET /api/products?deleted_at__isnull=true  # Not deleted
GET /api/products?deleted_at__isnull=false # Deleted items

# Date filtering
GET /api/products?created_at__date=2024-01-15
GET /api/products?created_at__gte=2024-01-01&created_at__lte=2024-12-31
```

### Response

All filters apply automatically, returning filtered, searched, and ordered results:

```json
[
  {
    "id": 42,
    "name": "MacBook Pro",
    "description": "High-performance laptop",
    "category": "electronics",
    "price": 1299.99,
    "stock": 5,
    "is_active": true,
    "created_at": "2024-12-15T10:30:00Z"
  },
  {
    "id": 23,
    "name": "Dell Laptop",
    "description": "Business laptop",
    "category": "electronics",
    "price": 899.99,
    "stock": 12,
    "is_active": true,
    "created_at": "2024-11-20T14:20:00Z"
  }
]
```

## Summary

- **FilterSet**: Declarative filtering with 20+ lookup types (lines 289-387)
- **filterset_fields**: Shorthand for simple filtering (lines 490-510)
- **SearchFilter**: Multi-field text search via `?search=` (lines 431-467)
- **OrderingFilter**: Dynamic ordering via `?ordering=` with minus-prefix (lines 470-515)
- **BaseFilterBackend**: Extensible base for custom backends (lines 403-428)
- **ReDoS Prevention**: Automatic regex safety (lines 40-96)
- **Auto-Application**: Filters apply automatically to route returns (lines 477-527)
- **Standalone Functions**: `filter_data()` and `filter_queryset()` for manual use (lines 477-568)

The system works seamlessly with both ORM querysets and in-memory lists, providing a consistent filtering API across your application.
