# Aquilia ORM — Deep Security Audit Report

**Version**: 1.0.1  
**Audit Date**: Phase 9  
**Auditor**: Senior Database Security Researcher  
**Scope**: `aquilia/models/`, `aquilia/db/engine.py`, `aquilia/faults/`  
**Baseline**: 4,482 tests passing, zero regressions  

---

## Executive Summary

The Aquilia ORM demonstrates a **strong security baseline** with consistent
parameterized query generation across all DML builders, a comprehensive lookup
registry that always produces `?` placeholders, and a fault-pipeline that
replaces bare exceptions with structured domain faults.  Phase 8 already
hardened DDL-keyword guards in `where()`, `having()`, `raw()`, and `RawSQL`.

This audit identifies **7 critical**, **9 high**, **6 medium**, and **4 low**
severity findings that remain in the codebase.  Each finding includes a
severity classification, affected file/line, proof-of-concept attack vector,
and recommended fix.

---

## 1. Methodology

| Technique | Description |
|-----------|-------------|
| **Static Analysis** | Line-by-line review of every SQL-emitting path in the ORM |
| **Threat Modeling** | STRIDE-based analysis of the query pipeline |
| **Attack Surface Mapping** | Enumeration of all entry points where user data reaches SQL |
| **Data Flow Tracing** | Tracing user input from `filter(**kwargs)` → `_build_filter_clause` → `Lookup.as_sql()` → `SQLBuilder` → `AquiliaDatabase.execute()` |
| **Differential Analysis** | Comparing ORM output against known-safe patterns (Django, SQLAlchemy) |

---

## 2. Files Audited (Complete List)

| File | Lines | Risk Level | Key Observations |
|------|-------|------------|-----------------|
| `query.py` | 1656 | **Critical** | Core query builder — filter, where, having, order, _build_select |
| `sql_builder.py` | 557 | Medium | Low-level SQL construction — consistently parameterized |
| `expression.py` | 898 | **Critical** | F(), RawSQL(), Func(), Cast(), When() — several raw-string-to-SQL paths |
| `fields/lookups.py` | 293 | Medium | Lookup registry — all produce parameterized SQL |
| `fields/validators.py` | 412 | Low | Validation library — comprehensive but opt-in |
| `fields_module.py` | 2245 | Medium | Field types — to_db()/to_python() conversions |
| `base.py` | 1433 | High | Model CRUD — get(), create(), save(), raw(), delete_instance() |
| `metaclass.py` | 165 | Low | Class construction — no SQL emission |
| `manager.py` | 482 | Low | Descriptor proxy — delegates to Q |
| `deletion.py` | 300 | Medium | On-delete handlers — parameterized |
| `registry.py` | 282 | Low | Model registry — no SQL injection surface |
| `transactions.py` | 352 | Medium | Savepoint name validation (already hardened) |
| `signals.py` | 370 | Low | Signal dispatch — no SQL |
| `aggregate.py` | 298 | Medium | Aggregate functions — delegate to Expression |
| `db/engine.py` | 626 | High | Database engine — query execution, savepoint sanitization |

---

## 3. Critical Findings (CVSS ≥ 9.0)

### C-01: `_build_filter_clause` Field Name Injection

**Severity**: CRITICAL (CVSS 9.8)  
**File**: `query.py:172-220`  
**Vector**: `filter(**user_controlled_dict)`  

**Description**:  
When `filter()` receives `**kwargs`, the dict keys become field names that are
quoted with `"` but **never validated** against `_SAFE_FIELD_RE`. An attacker
who controls the dict keys can inject arbitrary SQL into the field position:

```python
# Attacker controls form data that becomes filter kwargs
user_input = {"id\" OR 1=1 --": "anything"}
await User.objects.filter(**user_input)
# Generates: WHERE "id" OR 1=1 --" = ?
```

**Impact**: Full SQL injection — arbitrary data exfiltration, auth bypass.  
**Fix**: Validate all field names in `_build_filter_clause` with `_SAFE_FIELD_RE`.

### C-02: `Func()` Function Name Injection

**Severity**: CRITICAL (CVSS 9.1)  
**File**: `expression.py:520-546`  
**Vector**: `Func(user_input, F("field"))`  

**Description**:  
`Func.as_sql()` places `self.function` directly into the SQL string without
any validation. If the function name comes from user input:

```python
func_name = request.data["aggregate_func"]  # "SUM(1); DROP TABLE users--"
Func(func_name, F("price"))
# Generates: SUM(1); DROP TABLE users--(price)
```

**Impact**: Arbitrary SQL execution including DDL.  
**Fix**: Whitelist allowed function names or validate with `_SAFE_FIELD_RE`.

### C-03: `Cast()` Output Type Injection

**Severity**: CRITICAL (CVSS 9.1)  
**File**: `expression.py:549-575`  
**Vector**: `Cast(F("field"), user_input)`  

**Description**:  
`Cast.as_sql()` places `self.output_type` directly into SQL without validation:

```python
type_name = request.data["cast_type"]  # "INTEGER); DROP TABLE users--"
Cast(F("price"), type_name)
# Generates: CAST("price" AS INTEGER); DROP TABLE users--)
```

**Impact**: Arbitrary SQL execution.  
**Fix**: Whitelist allowed SQL type names.

### C-04: `When(condition=string)` Raw SQL Injection

**Severity**: CRITICAL (CVSS 9.1)  
**File**: `expression.py:348-400`  
**Vector**: `When(condition=user_string, then=Value(1))`  

**Description**:  
`When.as_sql()` checks `isinstance(self.condition, str)` and if true, uses the
string directly as `cond_sql` without any sanitization:

```python
When(condition=f"status = '{user_input}'", then=Value(1))
# If user_input = "x' OR 1=1 --"
# Generates: WHEN status = 'x' OR 1=1 --' THEN ?
```

**Impact**: SQL injection in CASE/WHEN expressions.  
**Fix**: Reject raw strings or apply DDL-keyword guard + parameterization warning.

### C-05: `Model.get(**filters)` Field Name Injection

**Severity**: CRITICAL (CVSS 9.1)  
**File**: `base.py:437-455`  
**Vector**: `await User.get(**user_dict)`  

**Description**:  
`Model.get()` builds WHERE clauses from filter keys using f-string interpolation:
```python
wheres = [f'"{k}" = ?' for k in filters]
```
The keys `k` are not validated. An attacker who controls the filter dict keys
can inject SQL through the quoted identifier position.

**Impact**: SQL injection in direct Model.get() calls.  
**Fix**: Validate filter keys against `_SAFE_FIELD_RE`.

### C-06: `aggregate()` Expression String Injection

**Severity**: CRITICAL (CVSS 8.5)  
**File**: `query.py:1418-1440`  
**Vector**: `aggregate(**{alias: user_string})`  

**Description**:  
In `Q.aggregate()`, when an expression is not an `Aggregate` or `Expression`
instance, it's placed directly into SQL:
```python
select_parts.append(f'{expr} AS "{alias}"')
```
If a raw string is passed as an aggregate expression, it goes into SQL unescaped.

**Impact**: SQL injection via aggregate expressions.  
**Fix**: Reject non-Expression values or wrap in `RawSQL` with DDL guard.

### C-07: Annotation String Injection in `_build_select()`

**Severity**: CRITICAL (CVSS 8.5)  
**File**: `query.py:854-878`  
**Vector**: `annotate(**{alias: raw_string})`  

**Description**:  
In `_build_select()`, when an annotation value is not an `Aggregate` or
`Expression`, it's interpolated directly:
```python
parts.append(f'{expr} AS "{alias}"')
```
A raw string annotation bypasses all parameterization.

**Impact**: SQL injection via annotation expressions.  
**Fix**: Reject non-Expression annotation values.

---

## 4. High Findings (CVSS 7.0–8.9)

### H-01: LIKE Wildcard Injection in Contains/StartsWith/EndsWith

**Severity**: HIGH (CVSS 7.5)  
**File**: `fields/lookups.py:60-140`  
**Vector**: `filter(name__contains=user_input)`  

**Description**:  
The `Contains`, `StartsWith`, and `EndsWith` lookups wrap user values with `%`:
```python
class Contains(Lookup):
    def as_sql(self):
        return f'"{self.field}" LIKE ?', [f"%{self.value}%"]
```
If `user_input` contains `%` or `_`, these LIKE metacharacters match
unintended rows. For example, `%` matches zero or more characters and
`_` matches exactly one character.

**Impact**: Data leakage — attacker can enumerate data patterns.  
**Fix**: Escape `%` and `_` in user values before wrapping.

### H-02: `RawSQL` Executes Despite DDL Warning

**Severity**: HIGH (CVSS 8.0)  
**File**: `expression.py:200-235`  

**Description**:  
`RawSQL` has a `_DANGEROUS_RE` guard that logs a warning for DDL keywords but
**still executes** the SQL. The warning-only approach provides no actual security.

**Impact**: DDL/DCL statements can be executed through RawSQL.  
**Fix**: Raise `QueryFault` instead of just warning.

### H-03: `Atomic.isolation` SQL Injection

**Severity**: HIGH (CVSS 7.5)  
**File**: `transactions.py:178-180`  
**Vector**: `atomic(isolation=user_input)`  

**Description**:  
The isolation level string is interpolated directly into SQL:
```python
await db.execute(f"SET TRANSACTION ISOLATION LEVEL {self._isolation}")
```
No whitelist validation is applied.

**Impact**: SQL injection via transaction isolation parameter.  
**Fix**: Whitelist allowed isolation levels.

### H-04: `values()` with Column List — No Field Validation

**Severity**: HIGH (CVSS 7.5)  
**File**: `query.py:1343-1363`  
**Vector**: `values("id\"; DROP TABLE users--")`  

**Description**:  
`Q.values(*fields)` passes field names to `_build_select(columns=col_list)`.
In `_build_select()`, column names from the `columns` parameter are quoted but
not validated:
```python
if isinstance(f, Expression):
    ...
else:
    col_parts.append(f'"{f}"')
```

**Impact**: SQL injection through column name position.  
**Fix**: Validate column names against `_SAFE_FIELD_RE`.

### H-05: `group_by()` Field Injection

**Severity**: HIGH (CVSS 7.5)  
**File**: `query.py:509-511, _build_select:949`  

**Description**:  
`group_by()` accepts field names without validation:
```python
def group_by(self, *fields):
    new = self._clone()
    new._group_by = list(fields)
    return new
```
In `_build_select()`:
```python
sql += " GROUP BY " + ", ".join(f'"{g}"' for g in self._group_by)
```
The fields are quoted but not validated with `_SAFE_FIELD_RE`.

**Impact**: SQL injection through GROUP BY field names.  
**Fix**: Validate field names with `_SAFE_FIELD_RE`.

### H-06: `only()`/`defer()` Field Injection

**Severity**: HIGH (CVSS 7.5)  
**File**: `query.py:548-560`  

**Description**:  
`only()` and `defer()` accept field names that flow to `_build_select()`:
```python
col = ", ".join(f'"{f}"' for f in self._only_fields)
```
No `_SAFE_FIELD_RE` validation.

**Impact**: SQL injection through field projection names.  
**Fix**: Validate field names with `_SAFE_FIELD_RE`.

### H-07: `select_related()`/`prefetch_related()` Field Injection

**Severity**: HIGH (CVSS 7.0)  
**File**: `query.py:891-940`  

**Description**:  
Field names in `select_related()` flow to JOIN construction:
```python
sql += f' LEFT JOIN "{rtable}" ON "{self._table}"."{fk_col}" = "{rtable}"."{rpk}"'
```
While these are resolved against `_fields`, the initial name is not validated.

**Impact**: Potential injection if relation names are user-controlled.  
**Fix**: Validate relation names against `_SAFE_FIELD_RE`.

### H-08: Validation Opt-in by Default

**Severity**: HIGH (CVSS 7.0)  
**File**: `base.py:730`  

**Description**:  
`Model.save(validate=False)` is the default. `Model.create()` calls
`full_clean()` but `save()` does not unless explicitly requested.
This means malformed data can bypass all field validators and reach the DB.

**Impact**: Data integrity violations, potential for stored XSS or logic bypass.  
**Recommendation**: Document prominently; consider validate=True default in v2.

### H-09: `_sql_default()` String Interpolation

**Severity**: HIGH (CVSS 7.0)  
**File**: `fields_module.py:275`  

**Description**:  
Default string values are interpolated directly:
```python
return f"'{self.default}'"
```
If a developer sets `default="'; DROP TABLE users--"` this goes into DDL.

**Impact**: DDL injection via field defaults (developer-controlled, not user).  
**Mitigation**: This is a developer-facing API, not user-facing. Document the risk.

---

## 5. Medium Findings

### M-01: `Q.update()` Key Injection
**File**: `query.py:1300-1325`  
Column names in `update(values=dict)` are quoted but not validated.  
**Fix**: Validate against `_SAFE_FIELD_RE`.

### M-02: No Query Complexity Limits
No configurable limits on JOIN depth, subquery nesting, or IN clause size
(beyond `in_bulk` batch_size). Malicious queries could cause DoS.  
**Fix**: Add configurable query complexity limits.

### M-03: `_is_raw()` Bypass in SQLBuilder
`sql_builder.py:_is_raw()` checks for `(`, `)`, `*`, ` `, `.` to decide
whether to quote a column reference. Crafted column names could bypass this.  
**Fix**: Tighten `_is_raw()` detection or always validate column names first.

### M-04: `explain()` Format Injection (Mitigated)
Already whitelisted in Phase 8. Confirmed secure. No action needed.

### M-05: Aggregate `filter_clause` Raw String
`Aggregate.__init__` accepts `filter_clause` as a raw string that goes
directly into `FILTER (WHERE ...)` SQL.  
**Fix**: Require Expression objects or add DDL guard.

### M-06: Bulk Operations Skip Validation
`bulk_create()` and `bulk_update()` skip `full_clean()` entirely.
**Fix**: Add optional `validate=True` parameter.

---

## 6. Low Findings

### L-01: Signal Handler Exception Swallowing
`Signal.send()` catches and logs handler exceptions but doesn't propagate.
A security-critical handler (e.g., audit logging) could silently fail.

### L-02: `from_row()` Accepts Unknown Columns
`Model.from_row()` silently ignores columns not in `_col_to_attr`.
Could mask data injection if extra columns are returned.

### L-03: `_serialize_value()` Enum Leakage
`to_dict()` serializes Enum values as their raw `.value`, which could
expose internal constants.

### L-04: WeakRef Cleanup Race in Signals
`_make_cleanup()` could race with `send()` in concurrent async contexts.

---

## 7. Summary of Recommendations

| Priority | Count | Action |
|----------|-------|--------|
| **Immediate** | 7 | Fix all Critical findings (C-01 through C-07) |
| **Next Sprint** | 9 | Fix all High findings (H-01 through H-09) |
| **Backlog** | 6 | Fix Medium findings |
| **Documentation** | 4 | Document Low findings |

All fixes are implemented as part of this Phase 9 audit. See companion
documents for detailed threat models, architecture designs, and fix
implementations.

---

*End of Security Audit Report*
