# Aquilia Controller System — Security Audit Report

**Date:** 2025-01-XX  
**Auditor:** GitHub Copilot (Phase 5)  
**Scope:** `aquilia/controller/` (12 files, ~5,000+ LOC), `aquilia/di/` raw exception audit  
**References:** OWASP REST Security Cheat Sheet, OWASP Error Handling Cheat Sheet, OWASP Input Validation Cheat Sheet, NestJS Guards/Interceptors/Filters patterns  
**Status:** 🔴 13 issues found — **3 Critical, 4 High, 4 Medium, 2 Low**

---

## Executive Summary

The controller subsystem provides a NestJS-inspired architecture with ExceptionFilters, Interceptors, Throttle, pipeline execution, content negotiation, and declarative parameter binding. While the architecture is well-designed, the audit found **13 security and correctness issues** across the controller engine, factory, base classes, and DI integration. Raw Python exceptions (`RuntimeError`, `ValueError`, `TypeError`, `TimeoutError`) are used throughout DI and controller layers instead of Aquilia's structured Fault mechanism, violating the framework's own observability design.

---

## Table of Contents

1. [Critical Issues](#critical-issues)
2. [High Issues](#high-issues)
3. [Medium Issues](#medium-issues)
4. [Low Issues](#low-issues)
5. [ExceptionFilter / Interceptor / Throttle Correctness](#component-correctness-audit)
6. [RequestCtx Dual-Class Analysis](#requestctx-dual-class-analysis)
7. [Raw Exception → Fault Migration Inventory](#fault-migration-inventory)
8. [OWASP Compliance Checklist](#owasp-compliance)

---

## Critical Issues

### SEC-CTRL-01: `_cast_value()` — Uncaught ValueError on Type Casting
- **File:** `aquilia/controller/engine.py:844-855`
- **Severity:** 🔴 CRITICAL
- **OWASP:** Input Validation (CWE-20)
- **Description:** `_cast_value()` calls `int(value)` and `float(value)` with no try/except. Malformed query parameters (e.g., `?page=abc`) cause an unhandled `ValueError` that propagates up as a 500 Internal Server Error instead of a 400 Bad Request.
- **Impact:** Information leakage via stack trace; Denial of Service via repeated malformed requests.
- **Fix:** Wrap casts in try/except, return 400-appropriate structured fault.

### SEC-CTRL-02: `_simple_resolve()` — Arbitrary Class Instantiation
- **File:** `aquilia/controller/factory.py:295-298`
- **Severity:** 🔴 CRITICAL
- **OWASP:** Injection (CWE-94)
- **Description:** When no container provider exists, `_simple_resolve()` falls back to `param_type()` — attempting to instantiate arbitrary classes. If an attacker can influence type annotations (e.g., via malicious plugins or misconfigured DI), this enables arbitrary object creation.
- **Impact:** Arbitrary code execution; uncontrolled side effects from constructing dangerous objects.
- **Fix:** Remove the `param_type()` fallback entirely; raise a structured `DIFault` instead.

### SEC-CTRL-03: `_to_response()` — Information Leakage via `str()` Fallback
- **File:** `aquilia/controller/engine.py:1257-1260`
- **Severity:** 🔴 CRITICAL
- **OWASP:** Error Handling — "Do not pass technical details to the client" (CWE-209)
- **Description:** The final else branch serializes unknown return types via `str(result)`. This can leak internal object representations, memory addresses, database connection strings, or other sensitive data embedded in `__repr__`.
- **Impact:** Information disclosure of internal framework/application state.
- **Fix:** Return a generic 500 response instead of `str()` serialization; log the object type server-side.

---

## High Issues

### SEC-CTRL-04: Throttle `_requests` Dict — Unbounded Memory Growth (DoS)
- **File:** `aquilia/controller/base.py:315`
- **Severity:** 🟠 HIGH
- **OWASP:** Denial of Service (CWE-400)
- **Description:** `Throttle._requests` is a `Dict[str, list]` that grows unbounded. Each unique client IP adds a new key that is never garbage-collected. An attacker cycling through IPs (e.g., via a botnet or IPv6 rotation) can cause memory exhaustion.
- **Impact:** Memory-based Denial of Service.
- **Fix:** Add max-keys limit + LRU eviction; implement periodic cleanup of expired entries.

### SEC-CTRL-05: `_get_interceptors()` — Route-Level Interceptors Silently Ignored
- **File:** `aquilia/controller/engine.py:1167-1177`
- **Severity:** 🟠 HIGH
- **Impact:** Feature broken — route-specific interceptors (declared via decorator kwargs) are never collected or executed. Only class-level `interceptors` list is returned. This means per-route security interceptors (e.g., logging, auth transformations) are silently skipped.
- **Fix:** Merge route-level interceptors from `route_metadata` with class-level interceptors.

### SEC-CTRL-06: `_apply_exception_filters()` — Silent Swallowing of Filter Errors
- **File:** `aquilia/controller/engine.py:1194-1200`
- **Severity:** 🟠 HIGH
- **Description:** If an `ExceptionFilter.catch()` method itself throws, the exception is caught by a bare `except Exception: pass`. The original exception and the filter's error are both lost.
- **Impact:** Security-critical errors (e.g., auth failures) can be silently swallowed; debugging becomes impossible.
- **Fix:** Log filter failures at ERROR level; emit fault event; continue to next filter.

### SEC-CTRL-07: Body Size Check — Only Validates Content-Length Header
- **File:** `aquilia/controller/engine.py:127-140`
- **Severity:** 🟠 HIGH
- **OWASP:** Request Entity Too Large (CWE-400)
- **Description:** The body size enforcement only checks the `Content-Length` header. Chunked Transfer Encoding (`Transfer-Encoding: chunked`) bypasses this check entirely, allowing unlimited body uploads.
- **Impact:** Memory exhaustion from oversized request bodies.
- **Fix:** Also enforce size limit when actually reading the body (streaming size guard).

---

## Medium Issues

### SEC-CTRL-08: Raw Exceptions Instead of Structured Faults
- **File:** Multiple files (see [Fault Migration Inventory](#fault-migration-inventory))
- **Severity:** 🟡 MEDIUM
- **Description:** 31 raw `raise` statements in `aquilia/di/` and 24 in `aquilia/controller/` use `RuntimeError`, `ValueError`, `TypeError`, `TimeoutError` instead of Aquilia's `Fault` hierarchy. This bypasses the FaultEngine's lifecycle (annotation, propagation, resolution, emission) and loses observability data.
- **Impact:** Inconsistent error handling; no fault events emitted for observability.
- **Fix:** Replace raw exceptions with domain-specific Faults where appropriate.

### SEC-CTRL-09: `_init_controller_lifecycle()` — Dummy Request with Bare Scope
- **File:** `aquilia/controller/engine.py:370-383`
- **Severity:** 🟡 MEDIUM
- **Description:** Creates a dummy `Request` with a minimal scope `{"type": "http", "method": "GET", "path": "/", ...}` for singleton startup hooks. This can confuse middleware or guards that expect valid scope entries (e.g., `root_path`, `server`, `app`).
- **Impact:** Subtle bugs in startup hooks; potential crashes in middleware.
- **Fix:** Use a dedicated startup context flag instead of fake request.

### SEC-CTRL-10: `_bind_parameters()` — Broad Exception Catching Masks Real Errors
- **File:** `aquilia/controller/engine.py:580-840`
- **Severity:** 🟡 MEDIUM
- **Description:** Both the `dep` and `di` resolution blocks catch `Exception` broadly and fall back to defaults when `not param.required`. This masks real DI resolution failures, configuration errors, and security exceptions.
- **Impact:** Silent failures in dependency injection; hard-to-debug production issues.
- **Fix:** Catch specific exception types; let security exceptions (Fault subclasses) always propagate.

### SEC-CTRL-11: `_extract_constructor_params()` — Silent Empty Return on Failure
- **File:** `aquilia/controller/metadata.py`
- **Severity:** 🟡 MEDIUM
- **Description:** If metadata extraction fails for any reason, an empty parameter list is returned silently. This means controllers with malformed type hints will appear to have no parameters, leading to missing DI injection.
- **Impact:** Silent loss of DI functionality; hard-to-diagnose runtime errors.
- **Fix:** Log warning on extraction failure; emit diagnostic fault.

---

## Low Issues

### SEC-CTRL-12: `patch_di_container()` — Dead Code, Never Called
- **File:** `aquilia/faults/integrations/di.py`
- **Severity:** 🟢 LOW
- **Description:** The `patch_di_container()` function exists and wraps Container methods to emit structured faults, but it is commented out at the bottom of the file and never called from any bootstrapping code.
- **Impact:** The entire DI fault integration is dead code; DI errors bypass fault engine.
- **Fix:** Integrate properly via the DI lifecycle or remove dead code.

### SEC-CTRL-13: `_execute_with_timeout()` — Raises Raw `TimeoutError`
- **File:** `aquilia/controller/engine.py:1227`
- **Severity:** 🟢 LOW
- **Description:** Raises `TimeoutError(f"Handler ... timed out after {timeout}s")` instead of `FlowCancelledFault(reason="timeout")`.
- **Impact:** Timeout errors bypass fault engine; inconsistent error type.
- **Fix:** Replace with `FlowCancelledFault`.

---

## Component Correctness Audit

### ExceptionFilter ✅ (with issues noted in SEC-CTRL-06)
- **Architecture:** Correct. Matches NestJS/Spring pattern — `catches` list for type filtering, `async catch()` for handling.
- **Issue:** Filter-level failures silently swallowed (SEC-CTRL-06).
- **Issue:** Only class-level filters checked; route-level not merged.

### Interceptor ✅ (with issues noted in SEC-CTRL-05)
- **Architecture:** Correct. `before()` for pre-processing (can short-circuit with Response), `after()` for post-processing (can transform result). Reverse order for `after()`.
- **Issue:** Route-level interceptors not collected (SEC-CTRL-05).
- **Note:** The before/after symmetry and reverse ordering are correctly implemented in `execute()`.

### Throttle ⚠️ (with issues noted in SEC-CTRL-04)
- **Architecture:** Correct sliding-window rate limiter. Uses `time.monotonic()` (good, not wall-clock). Client key extraction delegates to `request.client_ip()` with fallback.
- **Issue:** Unbounded memory growth (SEC-CTRL-04).
- **Issue:** `retry_after` always returns `self.window` — doesn't calculate actual remaining time for the client.
- **Note:** Route-level throttle correctly takes precedence over class-level in `_check_throttle()`.

---

## RequestCtx Dual-Class Analysis

### 1. `aquilia/controller/base.py::RequestCtx`
- **Purpose:** Full controller request context
- **Slots:** `request`, `identity`, `session`, `container`, `state`, `request_id`, `_extra`
- **Features:** Dynamic attribute escape hatch via `_extra` dict, body parsing delegators (`json()`, `body()`, `form()`, `multipart()`), request property delegation (`path`, `method`, `headers`, `query_params`)
- **Lifecycle:** Managed by `_RequestCtxPool` (max 256, lock-free acquire/release)
- **Used by:** `ControllerEngine.execute()`, all controller handlers

### 2. `aquilia/di/compat.py::RequestCtx`
- **Purpose:** Legacy DI compatibility wrapper
- **Slots:** None (regular class)
- **Features:** `get()` and `get_async()` methods wrapping `Container.resolve()`/`resolve_async()`
- **Lifecycle:** Managed via `ContextVar[Container]` per request
- **Used by:** Legacy code using pre-v1.0 DI API

### Analysis
These are **intentionally different** classes serving different layers:
- The controller `RequestCtx` is the **user-facing request context** (like Express `req` or Django `request`) enriched with identity, session, and DI container.
- The DI `RequestCtx` is a **backwards-compatibility shim** for code that used the old DI API pattern `RequestCtx.get(ServiceType)`.

**Recommendation:** They should NOT be merged. The DI `RequestCtx` should be deprecated in docs with a migration guide pointing to controller `RequestCtx`.

---

## Fault Migration Inventory

### DI Layer — 31 Raw Raises
| File | Line | Current Exception | Recommended Fault |
|------|------|-------------------|-------------------|
| `di/decorators.py` | 190 | `RuntimeError` | `DIResolutionFault` |
| `di/lifecycle.py` | 142 | `RuntimeError` | `SystemFault` |
| `di/graph.py` | 174 | `DependencyCycleError` | Keep (already structured) |
| `di/request_dag.py` | 102 | `RuntimeError` | `DIResolutionFault` |
| `di/request_dag.py` | 248 | `TypeError` | `DIResolutionFault` |
| `di/request_dag.py` | 270,284,304 | `ValueError` | `InputValidationFault` (new) |
| `di/request_dag.py` | 317 | `ValueError` | `InputValidationFault` |
| `di/cli.py` | 33,35,40 | `FileNotFoundError`/`ValueError` | Keep (CLI-specific, not runtime) |
| `di/providers.py` | 143 | `DIError` | Keep (already structured) |
| `di/providers.py` | 387 | `ValueError` | `DIResolutionFault` |
| `di/providers.py` | 433 | `TimeoutError` | `DIResolutionFault` |
| `di/providers.py` | 586 | `RuntimeError` | `DIResolutionFault` |
| `di/dep.py` | 187,200,236 | `ValueError` | `InputValidationFault` |
| `di/core.py` | 203 | `ValueError` | `DIResolutionFault` |
| `di/core.py` | 357,362 | `RuntimeError` | Keep (re-raise) |
| `di/core.py` | 626 | `ProviderNotFoundError` | Keep (already structured) |
| `di/core.py` | 882,916,985 | DI-specific | Keep (already structured) |

### Controller Layer — 24 Raw Raises
| File | Line | Current Exception | Recommended Fault |
|------|------|-------------------|-------------------|
| `controller/engine.py` | 1227 | `TimeoutError` | `FlowCancelledFault` |
| `controller/factory.py` | 293 | `TypeError` | `DIResolutionFault` |
| `controller/factory.py` | 368 | `ScopeViolationError` | `ScopeViolationFault` |
| `controller/base.py` | 74 | `AttributeError` | Keep (Python protocol) |
| `controller/base.py` | 240 | `NotImplementedError` | Keep (abstract method) |
| `controller/compiler.py` | 121,166 | `PatternSemanticError` | `PatternInvalidFault` |
| `controller/router.py` | 459 | `ValueError` | `RouteNotFoundFault` |
| `controller/renderers.py` | 148 | `NotImplementedError` | Keep (abstract) |
| `controller/renderers.py` | 349 | `RuntimeError` | `FlowFault` |
| `controller/filters.py` | 87,97,106 | `ValueError` | Keep (validation, correct) |
| `controller/decorators.py` | 257 | `ValueError` | Keep (config-time, correct) |
| `controller/pagination.py` | 122 | `NotImplementedError` | Keep (abstract) |

---

## OWASP Compliance

| OWASP Control | Status | Notes |
|---------------|--------|-------|
| Input Validation | ⚠️ | `_cast_value()` lacks error handling (SEC-CTRL-01) |
| Error Handling | ⚠️ | `str()` fallback leaks info (SEC-CTRL-03); filter errors swallowed (SEC-CTRL-06) |
| Rate Limiting | ⚠️ | Works but memory DoS vector (SEC-CTRL-04) |
| Request Size Limits | ⚠️ | Content-Length only, chunked bypass (SEC-CTRL-07) |
| Access Control | ✅ | Clearance system properly checked per request |
| Security Headers | ✅ | Response headers handled at middleware level |
| Content Type Validation | ✅ | Content negotiation system is robust |
| Audit Logging | ⚠️ | Exception filter failures not logged (SEC-CTRL-06) |

---

## Fixes Applied

All issues will be fixed in the same commit. See the git diff for implementation details.
