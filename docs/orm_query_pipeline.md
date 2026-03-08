# Aquilia ORM — Query Pipeline Documentation

**Version**: 1.0.1 | Phase 9 Security Audit  

---

## 1. Pipeline Overview

Every ORM query follows a deterministic pipeline from Python API call to
database execution. This document traces the complete pipeline with security
annotations at each stage.

---

## 2. Complete Query Lifecycle

### Stage 1: API Entry

```python
users = await User.objects.filter(name__contains="alice", active=True).order("-created_at").all()
```

**Security checkpoints**:
- `Manager.__get__()` — blocks instance access (descriptor protocol)
- `Manager.filter()` → `Q.filter(**kwargs)` — entry point

### Stage 2: Filter Clause Construction

```python
Q.filter(**kwargs)  →  _build_filter_clause(key, value)  for each key/value pair
```

**Data flow for `name__contains="alice"`**:
1. `key = "name__contains"`, `value = "alice"`
2. `key.rsplit("__", 1)` → `field = "name"`, `op = "contains"`
3. **Security: `_SAFE_FIELD_RE.match(field)`** — validates field name ✅
4. `resolve_lookup("name", "contains", "alice")` → `Contains("name", "alice")`
5. `Contains.as_sql()` → `('"name" LIKE ? ESCAPE \'\\\'', ['%alice%'])`
6. **Security: `_escape_like(value)`** — escapes `%` and `_` ✅
7. Clause and params stored in `Q._wheres` and `Q._params`

**Data flow for `active=True`**:
1. No `__` in key → exact match
2. **Security: `_SAFE_FIELD_RE.match("active")`** ✅
3. `resolve_lookup("active", "exact", True)` → `Exact("active", True)`
4. `Exact.as_sql()` → `('"active" = ?', [True])`

### Stage 3: Query Chain Assembly

```python
Q.order("-created_at")
```

1. Field = `"created_at"` (after stripping `-`)
2. **Security: `_SAFE_FIELD_RE.match("created_at")`** ✅
3. Direction = DESC (from `-` prefix)
4. Stored as `'"created_at" DESC'` in `Q._order_clauses`

### Stage 4: SQL Generation (`_build_select`)

```python
Q._build_select() → (sql, params)
```

Assembly order:
1. **SELECT columns** — `"users".*` (or explicit column list)
2. **FROM table** — `FROM "users"` (table name from model class)
3. **JOINs** — if `select_related()` was called
4. **WHERE** — concatenate all `_wheres` with `AND`
5. **GROUP BY** — if `group_by()` was called
6. **HAVING** — if `having()` was called
7. **ORDER BY** — from `_order_clauses`
8. **LIMIT/OFFSET** — if set
9. **FOR UPDATE** — if `select_for_update()` was called

Result:
```sql
SELECT "users".* FROM "users"
WHERE ("name" LIKE ? ESCAPE '\') AND ("active" = ?)
ORDER BY "created_at" DESC
```
Params: `['%alice%', True]`

### Stage 5: Execution

```python
rows = await self._db.fetch_all(sql, params)
```

1. `AquiliaDatabase.ensure_connected()` — verify connection
2. `self._adapter.fetch_all(sql, params)` — delegate to backend
3. Backend translates `?` to native param style:
   - SQLite: `?` (native)
   - PostgreSQL: `$1`, `$2`, ... (asyncpg)
   - MySQL: `%s` (aiomysql)
4. Prepared statement execution with bound parameters
5. Result timing recorded for admin QueryInspector

### Stage 6: Hydration

```python
instances = [self._model_cls.from_row(row) for row in rows]
```

1. `Model.from_row(row_dict)` — uses `_col_to_attr` mapping
2. For each column: `field.to_python(raw_value)` — type conversion
3. Snapshot original values for dirty tracking
4. Return list of model instances

---

## 3. Expression Pipeline

When expressions are used in queries, they follow a parallel pipeline:

```python
await Product.objects.annotate(
    discounted=F("price") * Value(0.9)
).filter(discounted__gt=10).all()
```

**Expression resolution**:
1. `F("price")` → `as_sql()` → `('"price"', [])`
2. `Value(0.9)` → `as_sql()` → `('?', [0.9])`
3. `F("price") * Value(0.9)` → `CombinedExpression(F, *, Value)`
4. `CombinedExpression.as_sql()` → `('("price" * ?)', [0.9])`

**In `_build_select()`**:
```sql
SELECT "products".*, ("price" * ?) AS "discounted" FROM "products"
WHERE (("price" * ?) > ?)
```
Params: `[0.9, 0.9, 10]`

---

## 4. Aggregate Pipeline

```python
result = await Product.objects.aggregate(
    total=Sum("price"),
    count=Count("id"),
)
```

1. `Sum("price")` → `Aggregate(F("price"))` → `as_sql()` → `('SUM("price")', [])`
2. `Count("id")` → `Aggregate(F("id"))` → `as_sql()` → `('COUNT("id")', [])`
3. Assembly: `SELECT SUM("price") AS "total", COUNT("id") AS "count" FROM "products"`
4. Execute → returns single-row dict

---

## 5. Write Pipeline

### INSERT (Model.create / save)

```python
user = await User.create(name="Alice", email="alice@test.com")
```

1. `cls(**data)` → create in-memory instance
2. `pre_save.send()` → fire pre-save signals
3. Pre-save hooks: `auto_now_add`, default values
4. `full_clean()` → field validation
5. `field.to_db(value, dialect)` → DB-format conversion
6. `InsertBuilder(table).from_dict(data)` → parameterized INSERT
7. `db.execute(sql, params)` → execute
8. Set `lastrowid` on instance
9. `post_save.send()` → fire post-save signals

### UPDATE (Q.update / save)

```python
await User.objects.filter(pk=1).update(name="Bob")
```

1. Build SET clause: `'"name" = ?'` with `["Bob"]`
2. **Security: Validate column keys with `_SAFE_FIELD_RE`** ✅
3. Build WHERE from `_wheres`: `'"id" = ?'` with `[1]`
4. Assembly: `UPDATE "users" SET "name" = ? WHERE ("id" = ?)`
5. `db.execute(sql, params)` → execute
6. Return `cursor.rowcount`

### DELETE (Q.delete / delete_instance)

```python
await user.delete_instance()
```

1. `pre_delete.send()` → fire pre-delete signals
2. Handle reverse FK on_delete (CASCADE/SET_NULL/PROTECT)
3. `DeleteBuilder(table).where(...)` → parameterized DELETE
4. `db.execute(sql, params)` → execute
5. `post_delete.send()` → fire post-delete signals
6. Return `cursor.rowcount`

---

## 6. Security Checkpoint Summary

| Pipeline Stage | Checkpoint | Type |
|---------------|-----------|------|
| Filter entry | `_SAFE_FIELD_RE` on field names | Regex validation |
| Lookup resolution | Parameterized `?` for all values | Parameterization |
| LIKE values | `_escape_like()` for `%`/`_` | Metachar escape |
| Expression resolution | `_SAFE_FUNC_RE` / `_SAFE_TYPE_RE` | Regex validation |
| SQL assembly | All identifiers quoted with `"` | Identifier quoting |
| SQL execution | Backend param binding (`?` → `$N`/`%s`) | Prepared statements |
| Error handling | SQL truncated in fault metadata | Info leak prevention |
| Raw SQL entry | DDL keyword guard | Keyword blocklist |

---

*End of Query Pipeline Documentation*
