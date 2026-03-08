# Aquilia ORM System Audit Report

**Auditor**: GitHub Copilot (Claude Opus 4.6)
**Date**: Phase 8 — ORM & Data Layer Audit
**Scope**: `aquilia/models/` (30+ files, ~12,000 LOC), `aquilia/db/` (engine, backends), `aquilia/faults/domains.py`
**References**: OWASP Query Parameterization Cheat Sheet, OWASP Database Security Cheat Sheet, OWASP SQL Injection Prevention Cheat Sheet

---

## Executive Summary

The Aquilia ORM is a well-architected, async-first data layer with metaclass-driven models, chainable querysets, signal system, and multi-dialect SQL generation. However, the audit identified **28 issues** spanning security, fault integration, consistency, and legacy code. The legacy AMDL (Aquilia Model Definition Language) system is slated for full deprecation per project requirements.

| Severity | Count | Description |
|----------|-------|-------------|
| 🔴 CRITICAL | 4 | SQL injection vectors, missing fault integration |
| 🟠 HIGH | 9 | Inconsistent error handling, missing validations |
| 🟡 MEDIUM | 9 | Code quality, missing features, integration gaps |
| 🔵 LOW | 6 | Documentation, deprecation, naming |

---

## Issues Found

### 🔴 CRITICAL Issues

#### C-01: `FieldValidationError` Not Integrated with Fault System
- **File**: `aquilia/models/fields_module.py` (line 21)
- **Problem**: `FieldValidationError` is a plain `ValueError` subclass, completely disconnected from the Aquilia Fault mechanism. Every field validation (40+ field types) raises this non-Fault exception, bypassing fault pipelines, logging, and error formatting.
- **Best Practice**: All domain errors should flow through the unified fault system (OWASP Error Handling).
- **Fix**: Create `FieldValidationFault` in `faults/domains.py` inheriting from `ModelFault`. Make `FieldValidationError` inherit from it for backward compat.
- **Status**: ✅ Fixed

#### C-02: `ProtectedError` / `RestrictedError` Not Integrated with Fault System
- **File**: `aquilia/models/deletion.py` (lines 224-240)
- **Problem**: `ProtectedError` and `RestrictedError` are plain `Exception` subclasses, not Faults. When a PROTECT/RESTRICT on_delete fires, these bypass the entire fault pipeline.
- **Fix**: Make them inherit from `ModelFault` while keeping backward compat.
- **Status**: ✅ Fixed

#### C-03: `having()` Accepts Raw SQL String — Potential Injection
- **File**: `aquilia/models/query.py` (line 608)
- **Problem**: `having(clause, *args)` accepts a raw SQL string. While args are parameterized, the clause itself is interpolated directly into SQL. A malicious clause string could inject SQL. No field name validation like `order()` has.
- **Fix**: Add `_SAFE_HAVING_RE` validation for HAVING clauses that don't use bind params.
- **Status**: ✅ Fixed

#### C-04: `where()` Raw SQL Method Lacks Input Validation
- **File**: `aquilia/models/query.py` (around line 375)
- **Problem**: `Q.where(clause, *args)` passes raw SQL directly. While it uses parameterized values, the clause string itself is not validated. Combined with user-controlled input, this is an injection vector.
- **Fix**: Add deprecation warning and documentation noting this is for internal/advanced use only. Add basic SQL keyword injection guard.
- **Status**: ✅ Fixed

### 🟠 HIGH Issues

#### H-01: `Model.get()` Returns None vs `latest()`/`earliest()` Raise Fault — Inconsistent
- **File**: `aquilia/models/base.py` (line ~250)
- **Problem**: `Model.get()` silently returns `None` when not found, while `latest()`, `earliest()`, and `one()` raise `ModelNotFoundFault`. This inconsistency confuses developers.
- **Fix**: `Model.get()` should raise `ModelNotFoundFault` when pk is explicitly provided and not found. Add `get_or_none()` for the None-returning pattern.
- **Status**: ✅ Fixed

#### H-02: `registry.py` Uses `RuntimeError` Instead of Fault System
- **File**: `aquilia/models/registry.py` (multiple locations)
- **Problem**: `ModelRegistry.register()`, `check_constraints()`, and other methods raise `RuntimeError` instead of `ModelRegistrationFault`, `SchemaFault`, etc.
- **Fix**: Replace `RuntimeError` with appropriate Fault subclasses.
- **Status**: ✅ Fixed

#### H-03: `refresh()` Uses `ValueError` Instead of Fault System
- **File**: `aquilia/models/base.py` (lines 958-982)
- **Problem**: `refresh()` raises plain `ValueError` for unsaved instances and when instances no longer exist. Should use `QueryFault` / `ModelNotFoundFault`.
- **Fix**: Replace with appropriate Faults.
- **Status**: ✅ Fixed

#### H-04: `base.py` `related()` Raises `AttributeError` Instead of Fault
- **File**: `aquilia/models/base.py` (line ~1091)
- **Problem**: `related()` raises `AttributeError` for missing relations instead of a proper Fault.
- **Fix**: Raise `QueryFault` with descriptive message.
- **Status**: ✅ Fixed

#### H-05: `attach()`/`detach()` Raise `AttributeError` Instead of Fault
- **File**: `aquilia/models/base.py` (lines ~1105, ~1135)
- **Problem**: M2M `attach()` and `detach()` raise plain `AttributeError`.
- **Fix**: Raise `QueryFault` with descriptive message.
- **Status**: ✅ Fixed

#### H-06: `Q.delete()` Does Not Fire `pre_delete`/`post_delete` Signals
- **File**: `aquilia/models/query.py` (line ~1340)
- **Problem**: Bulk `Q.delete()` executes raw DELETE SQL without firing per-instance signals. This means cascade handlers, audit logs, and cache invalidation connected via signals are silently bypassed.
- **Fix**: Document this limitation clearly. For critical paths, users should iterate and call `delete_instance()`.
- **Status**: 📝 Documented

#### H-07: `Q.update()` Does Not Fire `pre_save`/`post_save` Signals
- **File**: `aquilia/models/query.py` (line ~1310)
- **Problem**: Bulk `Q.update()` bypasses signals. Same concern as H-06.
- **Fix**: Document limitation.
- **Status**: 📝 Documented

#### H-08: Missing `FieldValidationFault` in `faults/domains.py`
- **File**: `aquilia/faults/domains.py`
- **Problem**: No `FieldValidationFault` class exists for field-level validation errors.
- **Fix**: Add `FieldValidationFault(ModelFault)` with field name and reason.
- **Status**: ✅ Fixed

#### H-09: `DatabaseNotReadyError(SystemExit)` in `startup_guard.py` Not a Fault
- **File**: `aquilia/models/startup_guard.py` (line 40)
- **Problem**: `DatabaseNotReadyError` inherits from `SystemExit`, not the Fault system. While this is intentional for process exit, it should also be a Fault for logging/auditing.
- **Fix**: Make it inherit from both `SystemExit` and `SchemaFault`.
- **Status**: ✅ Fixed

### 🟡 MEDIUM Issues

#### M-01: AMDL System Not Deprecated
- **Files**: `parser.py`, `ast_nodes.py`, `runtime.py`, `__init__old.py`, `migrations.py`
- **Problem**: The old AMDL system (parser, AST nodes, runtime proxy) is still importable and not marked as deprecated. Per project requirements, AMDL must be fully deprecated.
- **Fix**: Add deprecation warnings to all AMDL entry points.
- **Status**: ✅ Fixed

#### M-02: `__init__old.py` Still Importable
- **File**: `aquilia/models/__init__old.py`
- **Problem**: Old AMDL public API file still exists and is importable.
- **Fix**: Add module-level deprecation warning.
- **Status**: ✅ Fixed

#### M-03: `order()` Meta Ordering Doesn't Validate Field Names
- **File**: `aquilia/models/query.py` (lines 920-930)
- **Problem**: Default ordering from `Meta.ordering` is interpolated into SQL without `_SAFE_FIELD_RE` validation.
- **Fix**: Apply same field name validation as explicit `order()` calls.
- **Status**: ✅ Fixed

#### M-04: `in_bulk()` No SQL Injection Guard on Placeholders
- **File**: `aquilia/models/query.py` (lines 1405-1415)
- **Problem**: While `in_bulk()` uses parameterized queries, it doesn't limit the size of `id_list`, allowing potential DoS via extremely large IN clauses.
- **Fix**: Add configurable max batch size with chunking.
- **Status**: ✅ Fixed

#### M-05: Missing `select_for_update` SQLite Warning Not a Fault
- **File**: `aquilia/models/query.py` (line 944)
- **Problem**: `select_for_update()` on SQLite logs a warning but silently continues. The developer may not realize their locking has no effect.
- **Fix**: Raise `QueryFault` on SQLite instead of silent warning.
- **Status**: ✅ Fixed

#### M-06: `Model.raw()` Lacks SQL Keyword Guard
- **File**: `aquilia/models/base.py` (line ~740)
- **Problem**: `raw()` accepts arbitrary SQL strings. While this is intentional for power users, there's no guard against destructive operations (DROP, ALTER, DELETE without WHERE).
- **Fix**: Add a basic guard against common destructive patterns when not explicitly opted in.
- **Status**: ✅ Fixed

#### M-07: `explain()` Format Parameter Not Validated
- **File**: `aquilia/models/query.py` (line ~1505)
- **Problem**: The `format` parameter in `explain()` is interpolated into SQL without validation.
- **Fix**: Whitelist allowed format values.
- **Status**: ✅ Fixed

#### M-08: `transactions.py` Savepoint Names Not Validated Against Injection
- **File**: `aquilia/models/transactions.py` (line ~210)
- **Problem**: Savepoint IDs are generated from `uuid.uuid4().hex[:12]` which is safe, but `savepoint()`, `rollback_to_savepoint()`, and `release_savepoint()` accept arbitrary strings from callers.
- **Fix**: Validate savepoint IDs against `_SP_NAME_RE` from `db/engine.py`.
- **Status**: ✅ Fixed

#### M-09: `to_dict()` Missing `datetime.timezone` Serialization
- **File**: `aquilia/models/base.py` (line ~1200)
- **Problem**: `_serialize_value()` doesn't handle `Enum` types, which are common in models using `TextChoices`/`IntegerChoices`.
- **Fix**: Add Enum serialization support.
- **Status**: ✅ Fixed

### 🔵 LOW Issues

#### L-01: `signal.send()` Swallows Exceptions Silently
- **File**: `aquilia/models/signals.py` (line ~210)
- **Problem**: Signal `send()` catches exceptions and logs them but doesn't re-raise. This means critical signal handlers (e.g., audit logging) can fail silently.
- **Fix**: Already has `robust_send()` for this pattern. Document the difference.
- **Status**: 📝 Documented

#### L-02: `_clone()` Copies Lists Unconditionally for Non-Empty
- **File**: `aquilia/models/query.py` (line ~838)
- **Problem**: Already optimized with copy-on-write. No action needed.
- **Status**: ✅ No Fix Needed

#### L-03: `ManyToManyField.junction_table_name()` Naming Convention
- **File**: `aquilia/models/fields_module.py`
- **Problem**: Junction table naming uses `{source}_{attr_name}` which could collide with regular table names.
- **Fix**: Document naming convention. No code change needed.
- **Status**: 📝 Documented

#### L-04: Missing `__repr__` on `Options` Class
- **File**: `aquilia/models/options.py` (line ~150)
- **Problem**: `Options.__repr__` only shows table_name. Should include key metadata.
- **Fix**: Enhance repr.
- **Status**: ✅ Fixed

#### L-05: `runtime.py` Still Imports AMDL AST Nodes
- **File**: `aquilia/models/runtime.py`
- **Problem**: The AMDL runtime module is still active and uses `ast_nodes`. Part of AMDL deprecation.
- **Fix**: Add deprecation warning to `runtime.py`.
- **Status**: ✅ Fixed

#### L-06: `ORM_AUDIT.md` Placeholder Exists in Root
- **File**: `ORM_AUDIT.md`
- **Problem**: An audit placeholder file exists at root. Should be replaced with this comprehensive report.
- **Fix**: This report supersedes it.
- **Status**: ✅ Fixed

---

## Architecture Assessment

### Strengths
1. **Parameterized SQL everywhere**: All SQL builders use `?` placeholders — excellent OWASP compliance
2. **Immutable QuerySets**: `Q._clone()` ensures chainable operations are side-effect free
3. **Signal system**: Comprehensive lifecycle hooks (pre/post save/delete, m2m_changed)
4. **Multi-dialect support**: SQLite, PostgreSQL, MySQL, Oracle DDL/DML generation
5. **Dirty field tracking**: Minimal UPDATE statements via `_snapshot_original()`
6. **Topological sort for FK creation**: `ModelRegistry.create_tables()` uses Kahn's algorithm
7. **N+1 prevention**: `select_related()` (JOINs) and `prefetch_related()` (batch queries)
8. **Expression system**: F(), Value(), Case/When, Subquery, aggregates — rich and composable
9. **DSL migration system**: Clean, declarative migration operations

### Weaknesses Addressed
1. FieldValidationError disconnected from Fault system → Fixed
2. Inconsistent None/raise behavior for not-found → Fixed
3. Raw SQL methods lacking guards → Fixed
4. AMDL system not deprecated → Fixed
5. Multiple Exception subclasses not using Faults → Fixed

---

## AMDL Deprecation Plan

Per project requirements, the AMDL (Aquilia Model Definition Language) system is **fully deprecated**:

| File | Action | Status |
|------|--------|--------|
| `parser.py` | Module-level deprecation warning | ✅ Done |
| `ast_nodes.py` | Module-level deprecation warning | ✅ Done |
| `runtime.py` | Module-level deprecation warning | ✅ Done |
| `__init__old.py` | Module-level deprecation warning | ✅ Done |

The new Python-native Model class system (`base.py`, `fields_module.py`, `metaclass.py`) is the canonical and only supported approach.

---

## Test Results

All **4,482 tests** pass after fixes. No regressions introduced.

```
$ cd /Users/kuroyami/PyProjects/Aquilia && ./env/bin/python -m pytest tests/ -q --tb=short
4482 passed
```
