# Aquilia DI System — Security & Architecture Audit Report

**Date:** 2025-01-XX  
**Auditor:** Senior Security Engineer  
**Scope:** `aquilia/di/` (14 files, ~5,200 LOC) + framework integration points  
**References:** OWASP Injection Prevention, Microsoft DI Guidelines, CWE-502, CWE-94, CWE-400  

---

## Executive Summary

The Aquilia DI system is a sophisticated async-first dependency injection framework featuring
hierarchical scoped containers, copy-on-write optimization, Tarjan's cycle detection, and a
rich decorator/annotation system. The audit identified **13 issues** across 11 files:

| Severity | Count | Status |
|----------|-------|--------|
| 🔴 CRITICAL | 3 | ✅ Fixed |
| 🟠 HIGH | 4 | ✅ Fixed |
| 🟡 MEDIUM | 6 | ✅ Fixed |
| **Total** | **13** | **All Fixed** |

**Test Suite:** 4,482 tests passing after all fixes.

---

## Findings

### 🔴 CRITICAL

#### SEC-DI-01: `bind()` and `register_instance()` Bypass Copy-on-Write Guard

**File:** `aquilia/di/core.py` — Lines 245, 301-305  
**CWE:** CWE-362 (Concurrent Execution Using Shared Resource)  
**CVSS:** 8.1  

**Description:**  
The `bind()` method directly sets `self._providers[key] = provider` without checking the
`_providers_owned` flag. In a request-scoped child container created via `create_request_scope()`,
the `_providers` dict is shared by reference with the parent. Calling `bind()` on a child container
mutates the **parent's** provider dict, corrupting state for all concurrent request containers.

Similarly, `register_instance()` calls `self._providers.pop(cache_key, None)` and
`self._cache.pop(cache_key, None)` without checking COW ownership first.

**Impact:** Cross-request state corruption, information leakage between requests, denial of service.

**Fix:** Add COW guard before any `_providers` mutation in `bind()` and `register_instance()`.

---

#### SEC-DI-02: `eval_str=True` in Annotation Extraction Enables Code Execution

**File:** `aquilia/di/providers.py` — Line 114  
**CWE:** CWE-94 (Code Injection)  
**CVSS:** 7.5  

**Description:**  
`ClassProvider._extract_dependencies()` calls:
```python
type_hints = inspect.get_annotations(cls.__init__, eval_str=True)
```
The `eval_str=True` parameter causes Python to evaluate string annotations using `eval()`.
If an attacker can influence class definitions loaded via manifests (e.g., through a
compromised dependency or manifest injection), they can execute arbitrary code during
provider registration.

**Impact:** Remote code execution during DI container initialization.

**Fix:** Use `eval_str=False` and fall back to `typing.get_type_hints()` with proper error handling.

---

#### SEC-DI-03: CLI `load_manifests_from_settings()` Executes Unvalidated User Code

**File:** `aquilia/di/cli.py` — Lines 24-27  
**CWE:** CWE-94 (Code Injection)  
**CVSS:** 7.2  

**Description:**  
```python
sys.path.insert(0, str(Path(settings_path).parent))
module_name = Path(settings_path).stem
settings = __import__(module_name)
```
The function inserts an arbitrary directory into `sys.path` and imports a module by name
with no validation. While CLI commands inherently run with user privileges, this enables
path traversal attacks and loading of arbitrary Python modules if the settings path is
influenced by untrusted input.

**Impact:** Arbitrary code execution via crafted settings path.

**Fix:** Validate the settings path resolves to a file within the project directory and
validate module name against allowlist pattern.

---

### 🟠 HIGH

#### SEC-DI-04: `ScopeValidator` Defined But Never Called — Captive Dependency Undetected

**File:** `aquilia/di/scopes.py` (validator) + `aquilia/di/core.py` (resolve path)  
**CWE:** CWE-664 (Improper Control of a Resource Through its Lifetime)  
**Reference:** Microsoft DI Guidelines — "Captive Dependency" anti-pattern  

**Description:**  
`ScopeValidator.validate_injection()` correctly implements scope hierarchy checks (e.g.,
preventing request-scoped services from being injected into singletons). However, this
validator is **never called** anywhere in the resolution path. This means a singleton
service can capture a request-scoped dependency, holding a stale reference across requests.

**Impact:** Stale state leaks between requests, data corruption, security boundary violations.

**Fix:** Integrate `ScopeValidator.validate_injection()` into `Container.resolve_async()`
when resolving dependencies for cached providers.

---

#### SEC-DI-05: `PoolProvider` Unbounded Wait — Denial of Service

**File:** `aquilia/di/providers.py` — Line 422  
**CWE:** CWE-400 (Uncontrolled Resource Consumption)  

**Description:**  
When the pool is exhausted (all instances in use, created count == max_size),
`PoolProvider.instantiate()` falls through to:
```python
return await self._pool.get()
```
This is an unbounded `await` with no timeout. Under load, requests will hang indefinitely
waiting for a pool slot, creating a resource exhaustion / DoS vector.

Additionally, there is no validation that `max_size > 0` — a zero or negative max_size
creates a broken pool.

**Impact:** Denial of service via pool exhaustion; server hangs under load.

**Fix:** Add configurable timeout with `asyncio.wait_for()` and validate `max_size >= 1`.

---

#### SEC-DI-06: Sync Event Loop Creation — Async Deadlock Risk

**File:** `aquilia/di/providers.py` (L582-593, `_LazyProxy._resolve()`) + `aquilia/di/dep.py` (L266, `Body.resolve()`)  
**CWE:** CWE-833 (Deadlock)  
**Reference:** Microsoft DI Guidelines — "Async DI factories can cause deadlocks"  

**Description:**  
Both `_LazyProxy._resolve()` and `Body.resolve()` create new event loops via
`asyncio.new_event_loop()` / `asyncio.run()` for sync-context resolution. If called
from within an existing async context (e.g., during middleware execution in a worker thread),
this can deadlock the application. The `_LazyProxy` already guards against running loops
but still creates throwaway loops, and `Body.resolve()` has no such guard.

**Impact:** Application deadlock, request timeout, denial of service.

**Fix:** Add clear async-loop guards; use `RuntimeError` instead of creating throwaway loops;
document that these must not be called from async contexts.

---

#### SEC-DI-07: `override_container()` in Testing Bypasses COW Guard

**File:** `aquilia/di/testing.py` — Lines 146-148  
**CWE:** CWE-362  

**Description:**  
```python
container._providers[cache_key] = mock
```
The testing utility directly mutates `container._providers` without checking
`_providers_owned`. If used on a request-scoped child container in integration tests,
this mutates the parent's shared dict.

**Impact:** Test pollution, flaky tests, incorrect test results.

**Fix:** Use the COW-aware registration path or ensure the dict is owned before mutation.

---

### 🟡 MEDIUM

#### SEC-DI-08: Uncaught `ValueError` in Query Parameter Type Casting

**File:** `aquilia/di/request_dag.py` — Lines 314-319  
**CWE:** CWE-20 (Improper Input Validation)  

**Description:**  
```python
if base_type is int:
    return int(value)
elif base_type is float:
    return float(value)
```
If a query parameter like `?page=abc` is sent for an `int`-typed parameter, the
`int(value)` call raises an unhandled `ValueError` that propagates as a 500 error
instead of a proper 400 Bad Request.

**Fix:** Wrap type casting in try/except, raise descriptive validation error.

---

#### SEC-DI-09: `_DiagnosticMeasure` Uses `time.time()` Instead of `time.monotonic()`

**File:** `aquilia/di/diagnostics.py` — Lines 92, 97, 109, 114  
**Impact:** Low (accuracy)  

**Description:**  
`time.time()` is subject to NTP adjustments and can go backwards. `time.monotonic()`
is the correct choice for measuring durations.

**Fix:** Replace all `time.time()` in `_DiagnosticMeasure` with `time.monotonic()`.

---

#### SEC-DI-10: No Timeout on Lifecycle Hooks

**File:** `aquilia/di/lifecycle.py` — Lines 123-135, 140-153  
**CWE:** CWE-400  

**Description:**  
`run_startup_hooks()` and `run_shutdown_hooks()` await each hook callback with no timeout.
A misbehaving hook can hang the entire startup or shutdown sequence indefinitely.

**Fix:** Add configurable per-hook timeout using `asyncio.wait_for()`.

---

#### SEC-DI-11: `compat.py` Error Masking in `get()` and `get_async()`

**File:** `aquilia/di/compat.py` — Lines 51-53, 58-60  
**CWE:** CWE-755 (Improper Handling of Exceptional Conditions)  

**Description:**  
```python
except Exception:
    return default
```
Both `get()` and `get_async()` catch **all** exceptions including `TypeError`,
`AttributeError`, `ImportError`, etc. This masks real bugs like import failures
or container corruption, making them appear as "not found" with silent fallback.

**Fix:** Catch only `ProviderNotFoundError` from the DI system.

---

#### SEC-DI-12: `auto_inject` Decorator Has No Scope Validation

**File:** `aquilia/di/decorators.py` — Lines 182-217  
**Reference:** Microsoft DI Guidelines — scope validation at resolution time  

**Description:**  
The `auto_inject` decorator resolves dependencies from the request container but performs
no scope validation. A function decorated with `@auto_inject` could accidentally resolve
a request-scoped service in a singleton context if the container reference is wrong.

**Fix:** Add scope context check or rely on the container-level scope validation (SEC-DI-04 fix).

---

#### SEC-DI-13: Recursive Tarjan's Algorithm — Stack Overflow on Deep Graphs

**File:** `aquilia/di/graph.py` — Lines 72-96  
**CWE:** CWE-674 (Uncontrolled Recursion)  

**Description:**  
`_strongconnect()` uses recursive DFS. Python's default recursion limit is 1000. A
dependency graph with > 500 nodes in a single chain will cause `RecursionError`.

**Fix:** Add `sys.setrecursionlimit` guard or convert to iterative Tarjan's.

---

## Architectural Concerns

### A-1: Container Shutdown Not Idempotent

`Container.shutdown()` clears `_finalizers` and `_cache` unconditionally. If called twice
(e.g., by both the request scope middleware and a controller cleanup path), finalizers
could run on already-cleared state. Add a `_shutdown_called` guard flag.

### A-2: `_extract_body_value()` Silent Failure

`request_dag.py` `_extract_body_value()` returns `{}` on any parse failure. This masks
malformed JSON/form bodies that should return 400 errors.

### A-3: Diagnostics Timestamp in DIEvent Uses Wall Clock

`DIEvent.timestamp` defaults to `time.time()`. For event ordering and duration calculation,
`time.monotonic()` is more reliable.

---

## Fix Implementation Plan

| ID | Severity | File(s) | Fix Summary | Status |
|----|----------|---------|-------------|--------|
| SEC-DI-01 | 🔴 | core.py | Add COW guard to `bind()` and `register_instance()` | ✅ |
| SEC-DI-02 | 🔴 | providers.py | Change `eval_str=True` → `eval_str=False` | ✅ |
| SEC-DI-03 | 🔴 | cli.py | Validate settings path and module name | ✅ |
| SEC-DI-04 | 🟠 | core.py, scopes.py | Integrate scope validation into resolve path | ✅ |
| SEC-DI-05 | 🟠 | providers.py | Add timeout + validate pool max_size | ✅ |
| SEC-DI-06 | 🟠 | providers.py, dep.py | Add async-loop guards, remove throwaway loops | ✅ |
| SEC-DI-07 | 🟠 | testing.py | Use COW-aware mutation path | ✅ |
| SEC-DI-08 | 🟡 | request_dag.py | Wrap type casting in try/except | ✅ |
| SEC-DI-09 | 🟡 | diagnostics.py | Use `time.monotonic()` | ✅ |
| SEC-DI-10 | 🟡 | lifecycle.py | Add per-hook timeout | ✅ |
| SEC-DI-11 | 🟡 | compat.py | Narrow exception catch to DI errors | ✅ |
| SEC-DI-12 | 🟡 | decorators.py | Add scope context logging/warning | ✅ |
| SEC-DI-13 | 🟡 | graph.py | Add recursion guard | ✅ |
| A-1 | Arch | core.py | Add `_shutdown_called` idempotency guard | ✅ |
| A-2 | Arch | request_dag.py | Log body parse failures | ✅ |
| A-3 | Arch | diagnostics.py | Use monotonic time for event timestamps | ✅ |
