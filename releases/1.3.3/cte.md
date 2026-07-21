# CTEs — Common Table Expressions — Aquilia v1.3.3

CTEs let you name a subquery and reference it one or more times in the main
query. They improve readability, enable query composition, and on some
databases allow the optimiser to materialise intermediate results.

```sql
WITH active_users AS (
    SELECT * FROM "users" WHERE ("is_active" = ?)
)
SELECT * FROM "users" WHERE ...
```

---

## API

### `Q.cte(name) → CTE`

Creates a named CTE from the queryset. Does **not** execute anything.

```python
active_cte = User.objects.filter(is_active=True).cte("active_users")
```

### `Q.with_cte(*ctes) → Q`

Registers one or more CTEs into the query's `WITH` clause. Chainable.

```python
result = await (
    User.objects
    .with_cte(active_cte)
    .filter(role="admin")
    .all()
)
```

Generated SQL:
```sql
WITH "active_users" AS (SELECT * FROM "users" WHERE ("is_active" = ?))
SELECT * FROM "users" WHERE ("role" = ?)
```

Parameters: `[True, "admin"]` — CTE params always come first.

---

## CTE Objects

### `CTE(name, queryset)`

Returned by `Q.cte(name)`. Carries the name and the compiled inner queryset.

```python
from aquilia.models.cte import CTE

# Manual construction (rare; usually use Q.cte())
cte = CTE(name="large_orders", queryset=Order.objects.filter(amount__gt=1000))
```

### `CTECol(cte_name, column)`

An `Expression` that renders as `"cte_name"."column"`. Used to reference CTE
output columns inside other queries or annotations.

```python
from aquilia.models.cte import CTECol

# Reference the 'id' column of the 'active_users' CTE
col = CTECol("active_users", "id")
col.as_sql("sqlite")  # → ('"active_users"."id"', [])
```

### `CTEReference`

Used inside `recursive_cte()` lambdas. See [Recursive CTE docs](recursive_cte.md).

---

## Multiple CTEs

Chain `.with_cte()` calls or pass multiple CTEs in one call:

```python
large_orders_cte = Order.objects.filter(amount__gt=1000).cte("large_orders")
active_users_cte = User.objects.filter(is_active=True).cte("active_users")

result = await (
    User.objects
    .with_cte(active_users_cte, large_orders_cte)
    .all()
)
```

Generated SQL:
```sql
WITH
  "active_users" AS (SELECT * FROM "users" WHERE ("is_active" = ?)),
  "large_orders" AS (SELECT * FROM "orders" WHERE ("amount" > ?))
SELECT * FROM "users"
```

---

## Practical Examples

### Rank-filtered results using CTE

```python
from aquilia.models import Window
from aquilia.models.window import Rank

# Build ranked subquery as CTE
ranked_cte = (
    Product.objects
    .annotate(rank=Window(Rank(), partition_by=["category"], order_by="-revenue"))
    .cte("ranked_products")
)

# Select only top-3 per category from CTE
# (filter happens in Python since window annotations can't be filtered directly in WHERE)
products = await Product.objects.with_cte(ranked_cte).all()
top3 = [p for p in products if p.rank <= 3]
```

### Analytics pipeline with multiple CTEs

```python
monthly_revenue_cte = (
    Sale.objects
    .annotate(month=RawSQL("strftime('%Y-%m', created_at)"))
    .group_by("month")
    .annotate(total=Sum("amount"))
    .cte("monthly_revenue")
)

high_months_cte = (
    Sale.objects
    .filter(total__gt=10000)
    .cte("high_months")
)

result = await (
    Sale.objects
    .with_cte(monthly_revenue_cte, high_months_cte)
    .all()
)
```

---

## CTE Parameter Ordering

Bind parameters from CTEs are always prepended before annotation parameters
and WHERE parameters in the final parameter list. This ensures correct
positional binding regardless of where CTEs appear visually in the SQL.

```
Final params = cte_params + annotation_params + where_params + having_params
```

---

## Backend Compatibility

| Feature | SQLite | PostgreSQL | MySQL |
|---|---|---|---|
| Non-recursive CTEs | ≥ 3.8.3 | ≥ 8.4 | ≥ 8.0 |
| Multiple CTEs | ≥ 3.8.3 | ≥ 8.4 | ≥ 8.0 |
