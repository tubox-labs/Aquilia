# Backend Compatibility — Aquilia v1.3.3

## Window Functions

| Function | SQLite | PostgreSQL | MySQL | MariaDB |
|---|---|---|---|---|
| `RANK()` | ≥ 3.25 | ≥ 8.4 | ≥ 8.0 | ≥ 10.2 |
| `DENSE_RANK()` | ≥ 3.25 | ≥ 8.4 | ≥ 8.0 | ≥ 10.2 |
| `ROW_NUMBER()` | ≥ 3.25 | ≥ 8.4 | ≥ 8.0 | ≥ 10.2 |
| `NTILE(n)` | ≥ 3.25 | ≥ 8.4 | ≥ 8.0 | ≥ 10.2 |
| `LAG(expr, n, default)` | ≥ 3.25 | ≥ 8.4 | ≥ 8.0 | ≥ 10.2 |
| `LEAD(expr, n, default)` | ≥ 3.25 | ≥ 8.4 | ≥ 8.0 | ≥ 10.2 |
| `FIRST_VALUE(expr)` | ≥ 3.25 | ≥ 8.4 | ≥ 8.0 | ≥ 10.2 |
| `LAST_VALUE(expr)` | ≥ 3.25 | ≥ 8.4 | ≥ 8.0 | ≥ 10.2 |
| `NTH_VALUE(expr, n)` | ≥ 3.25 | ≥ 11 | ≥ 8.0.2 | ≥ 10.6 |
| Aggregate windows (SUM/AVG etc.) | ≥ 3.25 | ≥ 8.4 | ≥ 8.0 | ≥ 10.2 |
| `ROWS BETWEEN` frame | ≥ 3.25 | ≥ 8.4 | ≥ 8.0 | ≥ 10.2 |
| `RANGE BETWEEN` frame | ≥ 3.25 | ≥ 8.4 | ≥ 8.0 | ≥ 10.2 |
| `GROUPS BETWEEN` frame | ≥ 3.28 | ≥ 11 | ✗ | ✗ |

> **SQLite note**: Check your SQLite version with `SELECT sqlite_version()`.
> macOS ships SQLite ≥ 3.39 as of macOS 12. The system SQLite on older macOS
> may be < 3.25 — in that case, install a modern SQLite via Homebrew.

## CTEs

| Feature | SQLite | PostgreSQL | MySQL | MariaDB |
|---|---|---|---|---|
| Non-recursive CTE | ≥ 3.8.3 | ≥ 8.4 | ≥ 8.0 | ≥ 10.2 |
| Multiple CTEs in one query | ≥ 3.8.3 | ≥ 8.4 | ≥ 8.0 | ≥ 10.2 |
| Recursive CTE | ≥ 3.8.3 | ≥ 8.4 | ≥ 8.0 | ≥ 10.2 |
| `UNION ALL` in recursive | ≥ 3.8.3 | ≥ 8.4 | ≥ 8.0 | ≥ 10.2 |
| `UNION` dedup in recursive | ≥ 3.8.3 | ≥ 8.4 | ≥ 8.0 | ≥ 10.2 |
| CTE in UPDATE/DELETE | ✗ | ≥ 9.1 | ✗ | ≥ 10.6 |
| Materialisation hints | ✗ | ≥ 12 | ✗ | ✗ |

> **MySQL note**: MySQL 8.0 added CTE support. MySQL 5.7 and older do not
> support CTEs. If you target MySQL 5.7, avoid `with_cte()` and
> `recursive_cte()`.

## ORM Bug Fixes

| Fix | Affected versions | Fixed in |
|---|---|---|
| `UUIDField(auto=True)` NULL insert | All prior | 1.3.3 |
| Transaction depth `WeakValueDictionary` leak | All prior | 1.3.3 |

## Checking Your SQLite Version

```python
import sqlite3
print(sqlite3.sqlite_version)  # e.g., "3.45.1"
```

Minimum supported: SQLite **3.8.3** for CTEs, **3.25** for window functions.

## Checking Your PostgreSQL Version

```sql
SELECT version();
```

## Capability Detection at Runtime

Aquilia does not currently expose a runtime capability matrix API. If you
need to guard production code against unsupported backends, check the dialect:

```python
db = get_database()
dialect = db.driver  # "sqlite" | "postgresql" | "mysql"

if dialect == "mysql":
    # MySQL < 8.0 does not support CTEs
    pass  # add your own version check here
```

A first-class `backend.supports_window_functions` / `backend.supports_cte`
capability flag API is planned for a future release.
