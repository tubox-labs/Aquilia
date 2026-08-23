# Bug Fixes & Security Hardening in v1.4.0

Aquilia v1.4.0 consolidates seven beta cycles of bug fixes, security hardening, and reliability improvements.

---

## Critical Bug Fixes

1. **Top-Level IDE Autocomplete & Type Resolution (`aquilia/__init__.py`)**
   * Fixed missing static exports in the main package barrel by adding structured `if TYPE_CHECKING:` imports for all 594 public exports and synchronizing `__all__`, enabling full autocomplete, parameter hints, and Go-to-Definition across all IDEs with zero runtime import cost.

2. **Controller Sync/Async Dispatch Integrity (`ControllerEngine._safe_call`)**
   * Eliminated bound-method ID reuse from coroutine classification, resolving intermittent `TypeError: 'dict' object can't be awaited` when handlers returned dictionaries.
   * Synchronous decorators returning coroutines are now correctly awaited.

3. **Metaclass Computed Field Inheritance (`aquilia.contracts`)**
   * Fixed `@computed` methods being erroneously demoted to required `TextFacet` input fields when a subclass redeclared the field as a type annotation or bound an ORM model with a matching column name.

4. **Database Migration Workspace Module Loading (`aq db migrate`)**
   * Fixed migration deserialization failures when generated fields reference workspace enums (e.g. `EnumField(enum_class="modules.users.models.UserStatus")`). The loader now automatically discovers the owning workspace root and adds it to `sys.path`.

5. **HTTP Rate Limiting Correctness**
   * Fixed `NameError` causing rate-limited requests to return HTTP `500 Internal Server Error` instead of `429 Too Many Requests`.
   * Fixed per-user identity rate limits running before authentication by moving identity rule evaluation to priority `16` (after `AuthMiddleware` at `15`).

6. **WebSocket Parameterized Route Matching**
   * Fixed `@Socket("/chat/:room")` failing to match dynamic path parameters due to an un-awaited coroutine swallowed by an exception handler.

7. **Garbage Collection Leak in `RequestContext`**
   * Implemented custom `tp_traverse` and `tp_clear` on native C++ `RequestContext` objects so cycles attached to `ctx.state` are visible to Python's garbage collector, preventing 1 leaked context per request.

8. **Nanobind Router Memory Leaks**
   * Added `ControllerRouter.clear()` and `ASGIAdapter.shutdown()` to explicitly release native C++ nanobind Router handles during ASGI lifespan shutdown, eliminating leak warnings on process exit.

9. **Deterministic CLI Exit Codes**
   * Fixed `aq doctor` and `aq validate` returning exit code `0` on broken workspaces and missing databases. They now return exit code `1` (`FAILED`) or `3` (`CONFIG`).

10. **Subsystem Boot Timeout Enforcement**
    * Wrapped `BaseSubsystem.initialize()` in `asyncio.wait_for()`, preventing unreachable dependencies from hanging the server boot indefinitely.

11. **Admin Lifecycle & Rate Limiter Sweeps**
    * Fixed dormant admin startup/shutdown hooks.
    * Fixed `AdminRateLimiter.force_cleanup()` sweeps failing on hosts with uptime under 1 hour due to monotonic clock interval comparisons against 0.

---

## Security Hardening

* **JSON Depth Protection:** Replaced recursive JSON depth validation with iterative stack traversal, eliminating server crashes (process termination) from hostile deeply-nested payloads.
* **WebSocket Frame Size Limiting:** Added `_MAX_FRAME_SIZE` (16 MiB) frame size bounds in the devplatform transport before memory allocation.
* **EQL Grammar Validation:** `parse_eql()` compiles string filters into validated `VF` AST trees, preventing raw, unvalidated filter strings from reaching the underlying vector engine.
* **Python 3.14 Annotation Introspection:** Preserved `CastFault` security exceptions during deferred annotation evaluation, ensuring ReDoS-vulnerable patterns fail at definition time.
* **UDS Socket Permissions:** UNIX domain sockets created by the development server are automatically permissions-locked with `chmod 0o600` (owner-only).
