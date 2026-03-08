# Aquilia ORM — Attack Surface Map

**Version**: 1.0.1 | Phase 9 Security Audit  

---

## 1. Attack Surface Overview

The ORM's attack surface consists of every point where external data can
influence SQL generation. This document maps each entry point, traces the
data flow, identifies the trust boundary, and classifies the risk.

---

## 2. Entry Point Classification

### Tier 1 — Direct User Input (Highest Risk)

These entry points are commonly called with data originating from HTTP
requests, form submissions, or API payloads.

| Entry Point | File | Method Signature | Data Flow |
|-------------|------|-----------------|-----------|
| `filter(**kwargs)` | `query.py:416` | `filter(**kwargs)` → `_build_filter_clause(key, value)` | **Keys** → field names (quoted, unvalidated) → SQL WHERE. **Values** → parameterized `?` |
| `exclude(**kwargs)` | `query.py:443` | Same as filter, negated | Same flow, wrapped in `NOT (...)` |
| `where(clause, *args)` | `query.py:339` | Clause → raw SQL, args → params | DDL guard on clause; args are parameterized |
| `having(clause, *args)` | `query.py:498` | Clause → raw HAVING SQL | DDL guard when no params; args are parameterized |
| `Model.get(**filters)` | `base.py:437` | Filters → `WHERE "k" = ?` | **Keys** unvalidated → SQL; values parameterized |
| `Model.create(**data)` | `base.py:354` | Data → `InsertBuilder.from_dict()` | Keys become column names; values parameterized |
| `Q.update(**kwargs)` | `query.py:1300` | Keys → SET columns; values → params | Keys quoted but unvalidated |
| `values(*fields)` | `query.py:1343` | Fields → SELECT column list | Quoted but unvalidated |
| `order(*fields)` | `query.py:470` | Fields → ORDER BY | Validated with `_SAFE_FIELD_RE` ✅ |
| `group_by(*fields)` | `query.py:509` | Fields → GROUP BY | Quoted but unvalidated ⚠️ |
| `only(*fields)` | `query.py:548` | Fields → SELECT column list | Quoted but unvalidated ⚠️ |
| `defer(*fields)` | `query.py:556` | Fields → exclusion list | Quoted but unvalidated ⚠️ |

### Tier 2 — Developer-Controlled (Medium Risk)

These APIs are typically called with hardcoded values in application code,
but could be wrapped in ways that expose them to user input.

| Entry Point | File | Risk |
|-------------|------|------|
| `annotate(**expressions)` | `query.py:525` | Raw strings bypass Expression system |
| `aggregate(**expressions)` | `query.py:1418` | Same — raw strings go to SQL |
| `Func(function_name, *args)` | `expression.py:520` | Function name → raw SQL |
| `Cast(expr, output_type)` | `expression.py:549` | Type name → raw SQL |
| `When(condition=string)` | `expression.py:348` | String condition → raw SQL |
| `RawSQL(sql, params)` | `expression.py:200` | Full raw SQL with DDL warning only |
| `Model.raw(sql, params)` | `base.py:700` | DDL guard; params parameterized |
| `atomic(isolation=str)` | `transactions.py:108` | Isolation → `SET TRANSACTION` SQL |

### Tier 3 — Framework-Internal (Low Risk)

| Entry Point | File | Risk |
|-------------|------|------|
| `select_related(*fields)` | `query.py:564` | Resolved against model `_fields` |
| `prefetch_related(*lookups)` | `query.py:576` | Resolved against model fields |
| `select_for_update(**kwargs)` | `query.py:590` | Boolean flags only |
| `latest(field_name)` | `query.py:1258` | Delegates to `order()` (validated) |
| `earliest(field_name)` | `query.py:1275` | Delegates to `order()` (validated) |
| `explain(format=str)` | `query.py:1467` | Whitelisted formats ✅ |

---

## 3. Data Flow Diagrams

### 3.1 Filter Pipeline

```
User HTTP Request
    ↓
Controller/View extracts query params
    ↓
filter(**params)                    [query.py:416]
    ↓
_build_filter_clause(key, value)    [query.py:172]
    ├── key.rsplit("__", 1) → (field, op)
    │   ├── field → NOT validated ← ⚠️ ATTACK VECTOR
    │   └── op → resolved via lookup_registry
    └── value → passed to Lookup.as_sql()
         └── returns ('"field" LIKE ?', ["%value%"])
              └── All values parameterized ✅
                   ↓
Q._build_select()                   [query.py:800]
    ↓
AquiliaDatabase.fetch_all(sql, params)  [db/engine.py:405]
    ↓
DatabaseAdapter.fetch_all(sql, params)
    ↓
Backend driver (aiosqlite/asyncpg/aiomysql)
```

### 3.2 Expression Pipeline

```
Developer Code
    ↓
annotate(total=Func("SUM", F("price")))
    ↓
Func.as_sql(dialect)                [expression.py:540]
    ├── self.function → "SUM" → RAW into SQL ← ⚠️ ATTACK VECTOR
    └── self.args → F.as_sql() → '"price"' (quoted field)
         ↓
Q._build_select()
    ↓ annotation_params
AquiliaDatabase.execute()
```

### 3.3 Raw SQL Pipeline

```
Developer Code
    ↓
Model.raw("SELECT * FROM users WHERE age > ?", [18])
    ↓
_DDL_RE.search(sql)                [base.py:708]
    ├── Match → raise QueryFault ✅
    └── No match → proceed
         ↓
db.fetch_all(sql, params)
    ↓
Backend driver (parameterized)
```

---

## 4. Trust Boundaries

```
┌─────────────────────────────────────────────────┐
│  UNTRUSTED ZONE (HTTP, WebSocket, user input)   │
│                                                 │
│  form_data, query_params, JSON body,            │
│  URL path params, headers, cookies              │
└─────────────────────┬───────────────────────────┘
                      │
          ┌───────────▼───────────┐
          │  TRUST BOUNDARY #1    │
          │  View/Controller      │
          │  (should sanitize)    │
          └───────────┬───────────┘
                      │
┌─────────────────────▼───────────────────────────┐
│  SEMI-TRUSTED ZONE (ORM API)                    │
│                                                 │
│  filter(), where(), annotate(), Func(), Cast()  │
│  These APIs must defend against injection even   │
│  if the view layer fails to sanitize.           │
└─────────────────────┬───────────────────────────┘
                      │
          ┌───────────▼───────────┐
          │  TRUST BOUNDARY #2    │
          │  SQL Builder + Engine │
          │  (parameterized exec) │
          └───────────┬───────────┘
                      │
┌─────────────────────▼───────────────────────────┐
│  TRUSTED ZONE (Database Engine)                 │
│                                                 │
│  SQLite / PostgreSQL / MySQL / Oracle           │
│  Prepared statements with bound parameters      │
└─────────────────────────────────────────────────┘
```

---

## 5. Attack Vector Summary

| Vector | Entry Point | Parameterized? | Validated? | Status |
|--------|------------|----------------|------------|--------|
| Field name in filter key | `filter()` | N/A (identifier) | ❌ No | **FIX NEEDED** |
| Field name in get() key | `Model.get()` | N/A (identifier) | ❌ No | **FIX NEEDED** |
| Filter value | `filter()` | ✅ Yes | ✅ Lookups | Secure |
| WHERE clause | `where()` | ✅ Params | ⚠️ DDL guard | Acceptable |
| ORDER BY field | `order()` | N/A (identifier) | ✅ `_SAFE_FIELD_RE` | Secure |
| GROUP BY field | `group_by()` | N/A (identifier) | ❌ No | **FIX NEEDED** |
| HAVING clause | `having()` | ✅ Params | ⚠️ DDL guard | Acceptable |
| Column in values() | `values()` | N/A (identifier) | ❌ No | **FIX NEEDED** |
| Column in only()/defer() | `only()`/`defer()` | N/A (identifier) | ❌ No | **FIX NEEDED** |
| UPDATE key | `Q.update()` | N/A (identifier) | ❌ No | **FIX NEEDED** |
| Func name | `Func()` | N/A (identifier) | ❌ No | **FIX NEEDED** |
| Cast type | `Cast()` | N/A (identifier) | ❌ No | **FIX NEEDED** |
| When condition str | `When()` | ❌ No | ❌ No | **FIX NEEDED** |
| Annotation raw str | `annotate()` | ❌ No | ❌ No | **FIX NEEDED** |
| Aggregate raw str | `aggregate()` | ❌ No | ❌ No | **FIX NEEDED** |
| LIKE metacharacters | `contains/startswith` | ✅ Value param | ❌ No escape | **FIX NEEDED** |
| Isolation level | `atomic()` | ❌ No | ❌ No | **FIX NEEDED** |
| RawSQL DDL | `RawSQL()` | ✅ Params | ⚠️ Warning only | **FIX NEEDED** |

---

*End of Attack Surface Map*
