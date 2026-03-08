# Aquilia Framework Integration Audit

**Phase 12 — Comprehensive Integration & Wiring Audit**
**Date**: 2025
**Framework Version**: 1.0.1
**Test Count**: 4,702 (all passing)

---

## Executive Summary

This audit examines the integration and wiring of all major Aquilia framework
subsystems. The framework demonstrates a well-structured, manifest-driven
architecture with clean separation of concerns. Three integration-level issues
were identified and resolved; all are correctness or efficiency improvements
rather than security vulnerabilities (those were addressed in Phases 1–11).

### Issues Found & Resolved

| # | Severity | Component | Issue | Status |
|---|----------|-----------|-------|--------|
| INT-01 | **Critical** | Middleware Ordering | CSRF middleware priority (10) runs BEFORE session middleware (15) despite comment saying it must run AFTER | ✅ Fixed |
| INT-02 | **Medium** | DI Container | Double `shutdown()` on request-scoped container (middleware + ASGI finally) | ✅ Fixed |
| INT-03 | **Low** | Controller Engine | `effect_registry` initialized as `None`, wired late during startup | ✅ Documented (by design) |

---

## 1. Architecture Overview

### 1.1 Bootstrap Flow

```
Workspace (config_builders.py)
  → AppManifest (per-module manifest.py)
    → Aquilary.from_manifests() (static validation)
      → AquilaryRegistry (validated metadata)
        → RuntimeRegistry.from_metadata() (lazy compilation)
          → AquiliaServer.__init__() (wiring)
            → ASGIAdapter (ASGI bridge)
```

### 1.2 Component Graph

```
AquiliaServer
├── ConfigLoader (config.py)
├── HealthRegistry (health.py)
├── FaultEngine (faults/)
├── Aquilary → AquilaryRegistry → RuntimeRegistry
│   ├── DI Containers (per-app)
│   ├── AppContexts (metadata)
│   └── Dependency Graph (topological order)
├── LifecycleCoordinator (lifecycle.py)
├── ControllerRouter (controller/router.py)
│   ├── Static routes: O(1) hash map
│   ├── Dynamic routes: O(k) segment trie
│   └── Regex fallback for complex patterns
├── ControllerEngine (controller/engine.py)
│   ├── ControllerFactory (DI-based instantiation)
│   ├── FlowPipeline (guard/transform/hook)
│   ├── Clearance evaluation
│   └── Throttle/Interceptor/Exception filter
├── MiddlewareStack (middleware.py)
│   ├── Priority-ordered chain (built once, cached)
│   ├── Scope-aware (global/app/controller/route)
│   └── Fast-path builder (skip observability MW)
├── ASGIAdapter (asgi.py)
│   ├── HTTP handler (cached middleware chain)
│   ├── WebSocket handler
│   ├── Lifespan handler
│   └── Built-in /_health endpoint
├── SessionEngine (sessions/)
├── AuthManager (auth/)
├── TemplateEngine (templates/)
├── MailService (mail/)
├── CacheService (cache/)
├── StorageRegistry (storage/)
├── I18nService (i18n/)
├── TaskManager (tasks/)
├── EffectRegistry (effects.py)
├── AquilaSockets (sockets/)
├── AdminController (admin/)
└── ErrorTracker (admin/error_tracker.py)
```

### 1.3 Subsystem Count

| Subsystem | Status | DI Registered | Middleware | Lifecycle |
|-----------|--------|---------------|------------|-----------|
| Core Server | ✅ | — | — | startup/shutdown |
| DI System | ✅ | — | request_scope_mw | per-request scope |
| Faults | ✅ | FaultEngine | FaultMiddleware | — |
| Controller | ✅ | — | — | per-request |
| Routing | ✅ | — | — | initialize() |
| Auth | ✅ | AuthManager + sub-components | AquilAuthMiddleware | — |
| Sessions | ✅ | SessionEngine | SessionMiddleware/Auth | — |
| Templates | ✅ | TemplateEngine + providers | TemplateMiddleware | — |
| Mail | ✅ | MailService + MailConfig | — | on_startup/on_shutdown |
| Cache | ✅ | CacheService + CacheBackend | CacheMiddleware (opt) | initialize/shutdown |
| Storage | ✅ | StorageRegistry | — | initialize_all/shutdown_all |
| I18n | ✅ | I18nService + I18nConfig | I18nMiddleware | — |
| Tasks | ✅ | TaskManager | — | start/stop |
| Effects | ✅ | EffectRegistry | — | initialize_all/finalize_all |
| WebSockets | ✅ | — | — | initialize/shutdown |
| Admin | ✅ | AdminSite (optional) | — | — |
| Health | ✅ | — | — | subsystem registration |
| Error Tracker | ✅ | — | — | FaultEngine listener |
| Security MW | ✅ | — | ProxyFix/HTTPS/Helmet/HSTS/CSP/CORS/CSRF/RateLimit | — |
| Static Files | ✅ | — | StaticMiddleware | — |
| Database/ORM | ✅ | AquiliaDatabase + ModelRegistry | — | connect/disconnect |

---

## 2. Issues Found

### INT-01: CSRF Middleware Priority Ordering (Critical)

**Location**: `server.py:797-799`

**Problem**: The CSRF middleware has priority 10 but the comment states:
```
# Must run AFTER session middleware (priority 15) so session is available
```

In the middleware stack, lower priority numbers execute first (outermost).
Priority 10 (CSRF) runs BEFORE priority 15 (session/auth), meaning the
session is NOT yet available when CSRF middleware executes.

**Impact**: CSRF token validation that depends on session state will fail
silently or see `None` session, potentially bypassing protection or causing
spurious 403 errors.

**Fix**: Changed CSRF priority from 10 → 20 (after session/auth at 15).

### INT-02: Double DI Container Shutdown (Medium)

**Location**: `server.py:215-226` (request_scope_mw) + `asgi.py:340-346` (handle_http finally)

**Problem**: Both the `request_scope_mw` middleware and the ASGI adapter's
`handle_http` method call `di_container.shutdown()`. While the Container's
shutdown is idempotent (guarded by `_shutdown_called`), the double call is:
1. Wasteful — extra async call + attribute check on every request
2. Confusing — two owners of the same resource's lifecycle

**Fix**: Removed the shutdown call from the ASGI adapter's finally block,
since the middleware is the proper owner of the DI lifecycle. Added a
comment explaining the delegation.

### INT-03: ControllerEngine effect_registry Late Binding (Low)

**Location**: `server.py:163` + `server.py:3107-3113`

**Problem**: `effect_registry=None` is passed during `__init__`, only wired
during `startup()` step 3.5. Any code that accesses `controller_engine.effect_registry`
before startup completes will see `None`.

**Assessment**: This is by-design temporal coupling — effects require async
initialization which can only happen during the async startup phase. The
controller engine is never invoked before startup completes (the ASGI
adapter calls `server.startup()` during lifespan). No fix needed.

---

## 3. Middleware Priority Layout (After Fixes)

| Priority | Middleware | Purpose |
|----------|-----------|---------|
| 1 | ExceptionMiddleware | Catch-all error handler |
| 2 | FaultMiddleware | Fault engine integration |
| 3 | ProxyFixMiddleware | Trusted proxy resolution |
| 4 | HTTPSRedirectMiddleware | Force HTTPS |
| 5 | request_scope_mw | DI container lifecycle |
| 6 | StaticMiddleware | Serve static files |
| 7 | SecurityHeadersMiddleware | Helmet headers |
| 8 | HSTSMiddleware | HSTS enforcement |
| 9 | CSPMiddleware | Content Security Policy |
| 10 | RequestIdMiddleware | Request correlation |
| 11 | CORSMiddleware | Cross-origin support |
| 12 | RateLimitMiddleware | Rate limiting |
| 15 | SessionMiddleware / AquilAuthMiddleware | Session + Auth |
| **20** | **CSRFMiddleware** | **CSRF protection (FIXED)** |
| 24 | I18nMiddleware | Locale resolution |
| 25 | TemplateMiddleware | Template context |
| 26 | CacheMiddleware | HTTP response cache |
| 50 | User-configurable | Custom middleware |

---

## 4. Verification

All 4,702 tests pass after integration fixes.
