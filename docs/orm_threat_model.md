# Aquilia ORM — Threat Model

**Version**: 1.0.1 | Phase 9 Security Audit  
**Framework**: STRIDE (Spoofing, Tampering, Repudiation, Information Disclosure, DoS, EoP)

---

## 1. System Context

The Aquilia ORM sits between the application layer (controllers/views) and the
database layer (SQLite/PostgreSQL/MySQL/Oracle). It transforms high-level
Python API calls into parameterized SQL. The threat model considers an
adversary who can influence the ORM API through:

- HTTP request parameters (query strings, form data, JSON body)
- WebSocket messages
- File uploads containing serialized data
- Inter-service API calls

---

## 2. STRIDE Analysis

### 2.1 Spoofing (S)

| Threat | Vector | Likelihood | Impact | Mitigation |
|--------|--------|-----------|--------|------------|
| Model identity spoofing | Crafted `from_row()` data bypasses type checking | Low | Medium | Fields have `to_python()` type conversion |
| Registry pollution | `ModelRegistry.register()` accepts any class | Low | High | Only called by `ModelMeta.__new__()` |

### 2.2 Tampering (T) — **Highest Risk Category**

| Threat | Vector | Likelihood | Impact | Mitigation |
|--------|--------|-----------|--------|------------|
| **SQL Injection via filter keys** | `filter(**user_dict)` with crafted keys | **High** | **Critical** | **Fixed: `_SAFE_FIELD_RE` validation** |
| **SQL Injection via Func()** | User-controlled function names | Medium | Critical | **Fixed: `_SAFE_FUNC_RE` whitelist** |
| **SQL Injection via Cast()** | User-controlled type strings | Medium | Critical | **Fixed: `_SAFE_TYPE_RE` whitelist** |
| **SQL Injection via When()** | Raw string conditions | Medium | Critical | **Fixed: DDL guard + deprecation warning** |
| **LIKE wildcard manipulation** | `%` and `_` in filter values | **High** | High | **Fixed: `_escape_like()` helper** |
| Data tampering via bulk ops | `bulk_create()` skips validation | Medium | Medium | Documented; optional validate param |
| Transaction manipulation | `atomic(isolation=...)` injection | Low | High | **Fixed: whitelist validation** |

### 2.3 Repudiation (R)

| Threat | Vector | Likelihood | Impact | Mitigation |
|--------|--------|-----------|--------|------------|
| Unaudited data changes | `bulk_update()` skips signals | Medium | Medium | Documented in docstrings |
| Silent query modification | Signal handlers can silently fail | Low | Medium | Documented in L-01 |

### 2.4 Information Disclosure (I)

| Threat | Vector | Likelihood | Impact | Mitigation |
|--------|--------|-----------|--------|------------|
| **Data leakage via LIKE** | Wildcard injection in `contains` | **High** | High | **Fixed: `_escape_like()`** |
| Schema leakage via `explain()` | Query plans expose table structure | Low | Medium | `explain()` format whitelisted |
| Error message leakage | `QueryFault` metadata contains SQL | Medium | Medium | SQL truncated to 200 chars |
| `to_dict()` over-serialization | All fields serialized by default | Medium | Low | `exclude` parameter available |

### 2.5 Denial of Service (D)

| Threat | Vector | Likelihood | Impact | Mitigation |
|--------|--------|-----------|--------|------------|
| Unbounded query results | `all()` with no LIMIT | Medium | High | `iterator(chunk_size)` available |
| Large IN clauses | `in_bulk()` with huge lists | Medium | Medium | `batch_size=999` default |
| Deep subquery nesting | Nested `Subquery(Subquery(...))` | Low | Medium | No limit enforced |
| JOIN explosion | Excessive `select_related()` | Low | Medium | Manual control only |
| Regex DoS (ReDoS) | `Regex` lookup with evil patterns | Low | High | DB-level regex execution |

### 2.6 Elevation of Privilege (E)

| Threat | Vector | Likelihood | Impact | Mitigation |
|--------|--------|-----------|--------|------------|
| **DDL via RawSQL** | `RawSQL("DROP TABLE ...")` | Medium | **Critical** | **Fixed: raise instead of warn** |
| **DDL via Func()** | `Func("DROP TABLE users--", ...)` | Medium | Critical | **Fixed: `_SAFE_FUNC_RE`** |
| Schema modification via raw() | `Model.raw("ALTER TABLE ...")` | Low | High | DDL guard rejects ALTER/DROP |
| Privilege escalation via GRANT | SQL GRANT/REVOKE commands | Low | High | DDL guard rejects GRANT/REVOKE |

---

## 3. Attack Trees

### 3.1 SQL Injection Attack Tree

```
SQL Injection
├── Via Identifier Position (field names)
│   ├── filter(**user_dict)      → FIXED: _SAFE_FIELD_RE
│   ├── Model.get(**user_dict)   → FIXED: _SAFE_FIELD_RE
│   ├── values(*user_fields)     → FIXED: _SAFE_FIELD_RE
│   ├── group_by(*user_fields)   → FIXED: _SAFE_FIELD_RE
│   ├── only(*user_fields)       → FIXED: _SAFE_FIELD_RE
│   ├── defer(*user_fields)      → FIXED: _SAFE_FIELD_RE
│   └── Q.update(user_dict)      → FIXED: _SAFE_FIELD_RE
│
├── Via Expression System
│   ├── Func(user_string, ...)   → FIXED: _SAFE_FUNC_RE
│   ├── Cast(expr, user_string)  → FIXED: _SAFE_TYPE_RE
│   ├── When(condition=user_str) → FIXED: DDL guard + warning
│   ├── annotate(x=user_str)     → FIXED: Reject non-Expression
│   └── aggregate(x=user_str)    → FIXED: Reject non-Expression
│
├── Via LIKE Metacharacters
│   └── contains/starts/ends     → FIXED: _escape_like()
│
└── Via Raw SQL APIs
    ├── where(clause, ...)        → DDL guard (existing)
    ├── having(clause, ...)       → DDL guard (existing)
    ├── Model.raw(sql, ...)       → DDL guard (existing)
    └── RawSQL(sql, ...)          → FIXED: raise on DDL
```

### 3.2 Data Exfiltration Attack Tree

```
Data Exfiltration
├── Blind SQL Injection
│   ├── Via LIKE wildcards        → FIXED: _escape_like()
│   └── Via boolean conditions    → Mitigated by parameterization
│
├── Error-based leakage
│   └── QueryFault with SQL       → SQL truncated to 200 chars
│
├── Union-based injection
│   └── Via filter key injection  → FIXED: _SAFE_FIELD_RE
│
└── Out-of-band (OOB)
    └── Via Func("LOAD_FILE", ..) → FIXED: _SAFE_FUNC_RE
```

---

## 4. Risk Matrix

| Finding | Likelihood | Impact | Risk Level |
|---------|-----------|--------|------------|
| Filter key injection | High | Critical | **Extreme** |
| LIKE wildcard injection | High | High | **High** |
| Func() name injection | Medium | Critical | **High** |
| Cast() type injection | Medium | Critical | **High** |
| When() string injection | Medium | Critical | **High** |
| RawSQL DDL execution | Medium | Critical | **High** |
| Isolation level injection | Low | High | **Medium** |
| Unbounded queries | Medium | Medium | **Medium** |
| Bulk ops skip validation | Medium | Medium | **Medium** |

---

## 5. Residual Risk

After all fixes are applied, the following residual risks remain:

1. **Developer misuse of `where()`/`having()`**: These APIs intentionally
   accept raw SQL fragments. The DDL guard blocks destructive keywords, but
   developers can still construct injection-vulnerable conditions if they
   interpolate user values into the clause string instead of using `?` params.

2. **Model.raw()**: Intentionally executes arbitrary SQL (minus DDL). Cannot
   be fully restricted without removing the feature.

3. **Validation opt-in**: `save(validate=False)` is the default for
   performance. Invalid data can reach the database if developers don't
   call `full_clean()`.

4. **Query complexity DoS**: No configurable limits on JOIN depth, subquery
   nesting, or result set size. Recommended for future hardening.

---

*End of Threat Model*
