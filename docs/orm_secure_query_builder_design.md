# Aquilia ORM — Secure Query Builder Design

**Version**: 1.0.1 | Phase 9 Security Audit  

---

## 1. Design Philosophy

The Aquilia SQL builder system follows the **Secure by Default** principle:

1. **Parameterization is mandatory** — All DML builders use `?` placeholders.
   There is no opt-out.

2. **Identifiers are validated then quoted** — Every identifier passes through
   `_SAFE_FIELD_RE` validation before being wrapped in double-quotes.

3. **Raw SQL is guarded** — All raw-SQL entry points have DDL-keyword guards.

4. **Expressions are typed** — The Expression class hierarchy ensures that
   SQL fragments are composed safely through method dispatch, not string
   concatenation.

---

## 2. Builder Architecture

```
┌──────────────────────────────────┐
│          Q (QuerySet)            │
│  filter(), order(), annotate()   │
│  group_by(), having(), values()  │
└──────────────┬───────────────────┘
               │ _build_select()
               ▼
┌──────────────────────────────────┐
│      SQL Assembly Engine         │
│  Combines validated fragments    │
│  into final SQL + params         │
└──────────────┬───────────────────┘
               │
               ▼
┌──────────────────────────────────┐
│      SQL Builder Layer           │
│  InsertBuilder, UpdateBuilder,   │
│  DeleteBuilder, CreateTableBuilder│
│  All use ? parameterization      │
└──────────────┬───────────────────┘
               │
               ▼
┌──────────────────────────────────┐
│    AquiliaDatabase.execute()     │
│  Adapter translates ? → native   │
│  Prepared statement execution    │
└──────────────────────────────────┘
```

---

## 3. SQL Builder Internals

### 3.1 InsertBuilder

```python
class InsertBuilder:
    def from_dict(self, data: dict):
        for key, value in data.items():
            self._columns.append(f'"{key}"')
            self._placeholders.append("?")
            self._values.append(value)
        return self
    
    def build(self) -> Tuple[str, list]:
        cols = ", ".join(self._columns)
        placeholders = ", ".join(self._placeholders)
        sql = f'INSERT INTO "{self._table}" ({cols}) VALUES ({placeholders})'
        return sql, self._values
```

**Security**: Column names come from `field.column_name` (set by metaclass),
not from user input. Values always use `?`.

### 3.2 UpdateBuilder

```python
class UpdateBuilder:
    def set_dict(self, data: dict):
        for key, value in data.items():
            self._sets.append(f'"{key}" = ?')
            self._values.append(value)
        return self
```

**Security**: Column names from field definitions. Values parameterized.

### 3.3 DeleteBuilder

```python
class DeleteBuilder:
    def where(self, clause: str, *params):
        self._wheres.append(clause)
        self._params.extend(params)
        return self
```

**Security**: WHERE clauses from framework-internal code (not user input).
Parameters are bound.

---

## 4. Expression System Security Design

### 4.1 Type Hierarchy

```
Combinable (arithmetic operators)
    └── Expression (base: as_sql method)
        ├── F(name)                 → '"name"' (validated, quoted)
        ├── Value(val)              → '?' + [val] (parameterized)
        ├── RawSQL(sql, params)     → sql + params (DDL-guarded)
        ├── Col(table, col)         → '"table"."col"' (quoted)
        ├── Star()                  → '*'
        ├── CombinedExpression      → (lhs OP rhs) (recursive)
        ├── When/Case               → CASE WHEN (validated conditions)
        ├── Subquery                → (SELECT ...) (delegates to Q)
        ├── Exists                  → EXISTS (SELECT ...) (delegates to Q)
        ├── Func(name, *args)       → name(...) (name validated)
        ├── Cast(expr, type)        → CAST(... AS type) (type validated)
        ├── OrderBy(expr, dir)      → "expr" ASC/DESC
        └── Aggregate (Sum/Avg/etc) → FUNC("field") (inherits Func safety)
```

### 4.2 Security Invariants

1. **F()**: Field name validated with `_SAFE_FIELD_RE`, then quoted with `"`.
2. **Value()**: Always produces `?` with the value as a bound parameter.
3. **CombinedExpression**: Operator comes from `Combinable` constants only
   (`+`, `-`, `*`, `/`, `%`, `&`, `|`). Never user-controlled.
4. **Func()**: Function name validated with `_SAFE_FUNC_RE`.
5. **Cast()**: Type string validated with `_SAFE_TYPE_RE`.
6. **RawSQL()**: DDL-keyword guard raises `QueryFault` on dangerous patterns.
7. **Subquery/Exists**: Delegate to `Q._build_select()` which applies all
   the standard security checks.

---

## 5. Lookup System Security Design

### 5.1 Lookup Registry

All lookups produce parameterized SQL:

| Lookup | SQL Pattern | Parameterized |
|--------|------------|---------------|
| `exact` | `"field" = ?` | ✅ |
| `iexact` | `LOWER("field") = LOWER(?)` | ✅ |
| `contains` | `"field" LIKE ? ESCAPE '\'` | ✅ + escaped |
| `icontains` | `"field" LIKE ? ESCAPE '\'` (case-insensitive) | ✅ + escaped |
| `startswith` | `"field" LIKE ? ESCAPE '\'` | ✅ + escaped |
| `endswith` | `"field" LIKE ? ESCAPE '\'` | ✅ + escaped |
| `in` | `"field" IN (?, ?, ...)` | ✅ |
| `gt/gte/lt/lte` | `"field" > ?` | ✅ |
| `isnull` | `"field" IS NULL` / `IS NOT NULL` | ✅ (no value) |
| `range` | `"field" BETWEEN ? AND ?` | ✅ |
| `regex/iregex` | `"field" ~ ?` / `REGEXP ?` | ✅ |
| `date/year/month/day` | Extraction functions | ✅ |

### 5.2 LIKE Escape Chain

```
User value: "100% complete_"
    ↓ _escape_like()
Escaped: "100\% complete\_"
    ↓ Wrapped with %
Pattern: "%100\% complete\_%" 
    ↓ Parameterized
SQL: "field" LIKE ? ESCAPE '\'  →  params: ["%100\% complete\_%"]
```

---

## 6. Filter Clause Construction Security

### 6.1 `_build_filter_clause` Security Flow

```python
def _build_filter_clause(key: str, value: Any) -> Tuple[str, List[Any]]:
    # Step 1: Split on __ to get field and operation
    if "__" in key:
        field, op = key.rsplit("__", 1)
    else:
        field, op = key, "exact"
    
    # Step 2: VALIDATE field name ← NEW IN PHASE 9
    if not _SAFE_FIELD_RE.match(field):
        raise QueryFault(...)
    
    # Step 3: Resolve lookup from registry
    lookup = resolve_lookup(field, op, value)
    
    # Step 4: Lookup produces parameterized SQL
    return lookup.as_sql()
```

---

## 7. Annotation/Aggregate Security

### 7.1 Pre-Phase 9 (Vulnerable)

```python
# Raw strings went directly into SQL
.annotate(total="SUM(price)")  # Direct SQL injection!
```

### 7.2 Post-Phase 9 (Secure)

```python
# Raw strings are rejected — must use Expression objects
.annotate(total=Sum("price"))  # ✅ Safe
.annotate(total="SUM(price)")  # ❌ Raises QueryFault
```

---

*End of Secure Query Builder Design*
