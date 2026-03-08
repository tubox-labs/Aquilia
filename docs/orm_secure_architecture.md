# Aquilia ORM — Secure Architecture Design

**Version**: 1.0.1 | Phase 9 Security Audit  

---

## 1. Architecture Principles

The Aquilia ORM security architecture follows the **Defense in Depth** strategy
with multiple independent validation layers:

```
Layer 1: API Boundary Validation
    ↓  (field name regex, type whitelist, DDL guard)
Layer 2: Expression System Type Safety
    ↓  (Expression objects enforce parameterization)
Layer 3: SQL Builder Parameterization
    ↓  (all values use ? placeholders)
Layer 4: Database Engine Abstraction
    ↓  (adapter translates ? to backend's param style)
Layer 5: Database Driver Prepared Statements
    ↓  (aiosqlite/asyncpg/aiomysql bind parameters)
Layer 6: Database Server Enforcement
    (RBAC, constraints, triggers)
```

---

## 2. Security-Hardened Component Design

### 2.1 Query Builder (`Q` class)

**Pre-Phase 9**: Only `order()` validated field names with `_SAFE_FIELD_RE`.

**Post-Phase 9**: Every method that accepts field/column names validates them:

| Method | Validation | Guard |
|--------|-----------|-------|
| `filter(**kwargs)` | `_SAFE_FIELD_RE` on keys | `QueryFault` |
| `exclude(**kwargs)` | `_SAFE_FIELD_RE` on keys | `QueryFault` |
| `order(*fields)` | `_SAFE_FIELD_RE` | ✅ Already existed |
| `group_by(*fields)` | `_SAFE_FIELD_RE` | `QueryFault` |
| `only(*fields)` | `_SAFE_FIELD_RE` | `QueryFault` |
| `defer(*fields)` | `_SAFE_FIELD_RE` | `QueryFault` |
| `values(*fields)` | `_SAFE_FIELD_RE` | `QueryFault` |
| `update(**kwargs)` | `_SAFE_FIELD_RE` on keys | `QueryFault` |
| `where(clause)` | `_DANGEROUS_KEYWORDS_RE` | `QueryFault` |
| `having(clause)` | `_DANGEROUS_KEYWORDS_RE` | `QueryFault` |

### 2.2 Expression System

**Pre-Phase 9**: Expressions accepted arbitrary strings for function names,
type names, and conditions.

**Post-Phase 9**:

| Expression | Validation | Pattern |
|-----------|-----------|---------|
| `F(name)` | `_SAFE_FIELD_RE` | Quoted identifier |
| `Value(val)` | None needed | Parameterized `?` |
| `Func(name, ...)` | `_SAFE_FUNC_RE` | Alphanumeric + underscore |
| `Cast(expr, type)` | `_SAFE_TYPE_RE` | SQL type pattern whitelist |
| `When(cond=str)` | DDL guard + deprecation | Warns for raw strings |
| `RawSQL(sql)` | `_DANGEROUS_RE` | Raises `QueryFault` on DDL |

### 2.3 SQL Builder Layer

The `sql_builder.py` module was already secure:

- All DML builders (`InsertBuilder`, `UpdateBuilder`, `DeleteBuilder`) use
  `?` placeholders for values
- DDL builders (`CreateTableBuilder`, `AlterTableBuilder`) accept raw
  column definitions but are only called from framework-internal code
- `_is_raw()` helper determines quoting behavior

### 2.4 Database Engine Layer

The `db/engine.py` module provides:

- **Savepoint name sanitization**: `_SP_NAME_RE` regex validation
- **Query timing**: All queries are timed and recorded for admin inspector
- **Fault wrapping**: All exceptions are caught and re-raised as typed faults
- **SQL truncation**: Error metadata contains only first 200 chars of SQL

---

## 3. Validation Architecture

### 3.1 Identifier Validation Regex

```python
_SAFE_FIELD_RE = re.compile(r'^[a-zA-Z_][a-zA-Z0-9_]*$')
```

This regex ensures identifiers:
- Start with a letter or underscore
- Contain only letters, digits, and underscores
- Cannot contain quotes, spaces, semicolons, or any SQL-significant characters

### 3.2 Function Name Validation

```python
_SAFE_FUNC_RE = re.compile(r'^[A-Z_][A-Z0-9_]*$', re.IGNORECASE)
```

### 3.3 SQL Type Validation

```python
_SAFE_TYPE_RE = re.compile(
    r'^[A-Z][A-Z0-9_ ]*(?:\([0-9]+(?:,[0-9]+)?\))?$', re.IGNORECASE
)
```

Allows: `INTEGER`, `VARCHAR(255)`, `DECIMAL(10,2)`, `DOUBLE PRECISION`  
Rejects: `INTEGER); DROP TABLE users--`, `VARCHAR'; GRANT ALL--`

### 3.4 LIKE Escape Function

```python
def _escape_like(value: str) -> str:
    return value.replace('\\', '\\\\').replace('%', '\\%').replace('_', '\\_')
```

Applied to all `Contains`, `StartsWith`, and `EndsWith` lookups.
The SQL clause includes `ESCAPE '\'` to define the escape character.

---

## 4. Fault Pipeline Integration

All security violations flow through the Aquilia Fault Pipeline:

```
Security Violation Detected
    ↓
QueryFault(
    model="User",
    operation="filter",
    reason="Invalid field name: 'id\" OR 1=1 --'"
)
    ↓
AquiliaFault base class
    ↓
Fault handlers (logging, metrics, error response formatting)
    ↓
HTTP 400/500 response (no SQL leakage)
```

---

## 5. Security Invariants

The following invariants are maintained across the entire ORM:

1. **No user-controlled string ever appears unquoted in SQL** — All
   identifiers are wrapped in double-quotes after validation.

2. **No user-controlled value ever appears un-parameterized in SQL** — All
   values use `?` placeholders bound at execution time.

3. **All identifier positions are validated** — Field names, column names,
   function names, and type names pass through appropriate regex validators.

4. **DDL keywords are blocked in all raw-SQL entry points** — `where()`,
   `having()`, `raw()`, `RawSQL` all have DDL-keyword guards.

5. **LIKE metacharacters are escaped** — `%` and `_` in user values cannot
   act as wildcards.

6. **Transaction isolation levels are whitelisted** — Only standard SQL
   isolation levels are accepted.

---

*End of Secure Architecture Design*
