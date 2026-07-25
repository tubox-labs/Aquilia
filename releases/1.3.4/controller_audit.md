# Controller System Audit Fixes

This document details the fixes applied to the `ControllerEngine`, `AuthManager`, and routing subsystems in Aquilia v1.3.4, addressing issues identified in sections §6.1–§8 of the architectural audit report.

## §6.1 Lifecycle Hook Bypass (CRITICAL)

**Previous Behavior:**
The `ControllerEngine` utilized a fast-path execution model for routes classified as "simple" (routes with only path parameters, and no pipeline, contract, or filter requirements). However, this fast-path silently skipped the `on_request` and `on_response` controller lifecycle hooks. If a controller overrode these hooks but contained a simple route, the hooks were never executed for that specific route.

**Root Cause:**
The `is_simple` classification logic only checked the route's immediate metadata and ignored whether the parent controller had overridden the lifecycle methods.

**Fix:**
The `is_simple` check now interrogates the `_has_lifecycle_hooks` cache on the controller class. Routes belonging to controllers that implement custom `on_request` or `on_response` methods are safely disqualified from the fast-path, ensuring the hooks execute unconditionally.

**User Impact:**
If you relied on `on_request` or `on_response` for logging, context setup, or teardown on simple routes, these will now correctly execute. No code changes are required.

## §6.2 Unintended Token Generation (SECURITY)

**Previous Behavior:**
The `authenticate_password()` method in `AuthManager` automatically generated and issued both JWT access and refresh tokens upon successful authentication, even when the application only required session-based authentication.

**Fix:**
An `issue_tokens: bool = True` parameter was added to `authenticate_password()`. Correspondingly, an `issue_tokens` field was added to `SignInProvisionPolicy`.

**User Impact & Migration:**
If your application uses session-only authentication, you can now safely skip JWT generation:
```python
# Pass issue_tokens=False to prevent JWT generation
identity = await auth_manager.authenticate_password(username, password, issue_tokens=False)
```
Identity resolution remains fully functional.

## §6.3 Forward-Reference Type Resolution (BUG)

**Previous Behavior:**
In `metadata.py`, `_extract_method_params()` classified the injected request context by performing a naive substring match (`"Request" in param_type`). This inadvertently caused valid domain types containing the word "Request" (e.g., `RequestLog`, `PasswordResetRequest`) to be incorrectly classified and silently dropped from payload parameter binding.

**Fix:**
The classification logic now performs an exact string match (`param_type == x or param_type.endswith(f".{x}")`). Additionally, when `get_type_hints()` fails due to unresolvable forward references, the system gracefully falls back to inspecting `__annotations__`.

## §6.4 Dynamic Segment Route Conflict False Positives (BUG)

**Previous Behavior:**
The `ControllerCompiler` raised false-positive `RouteConflictError`s when two controllers registered dynamic segments at the exact same path position, even if their type castors differed (e.g., `/<id:int>` vs `/<slug:str>`).

**Fix:**
`_routes_conflict()` has been updated to compare type castors. Distinct type castors at the same path position no longer trigger a conflict, enabling safe routing to different handlers based on type.

## §5.2 Pipeline vs Clearance Documentation (DOCS/ARCH)

The `Controller` class docstring has been updated to explicitly define the decision rules and execution order between request pipelines and access clearance.

## §5.3 Class-Level Cache Contamination (ARCH)

**Previous Behavior:**
`ControllerEngine` and `ControllerFactory` maintained `id()`-keyed class-level caches (`_simple_route_cache`, `_clearance_cache`, `_has_lifecycle_hooks`, `_ctor_info_cache`). Because object `id()`s can be reused by the Python runtime after garbage collection, these caches could serve stale entries to newly allocated objects.

**Fix:**
Added `clear_caches()` classmethods to both classes, providing a deterministic mechanism to flush all caches and prevent ID-reuse contamination across tests and application reloads.

## §7 / §11.11 Router `url_for()` Performance (PERF)

**Previous Behavior:**
`url_for()` in `ControllerRouter` performed an O(n·m) linear scan across all registered routes to find a name match.

**Fix:**
During initialization, the router now builds a `_name_index` dictionary mapping handler names directly to their compiled routes. `url_for()` lookups are now O(1).
