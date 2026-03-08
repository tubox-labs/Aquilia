# Component Wiring Analysis

**Phase 12 — Integration Audit**
**Aquilia v1.0.1**

---

## 1. Server → Subsystem Wiring Map

This document traces every wiring point from `AquiliaServer.__init__()` and
`AquiliaServer.startup()` to ensure all subsystems are properly connected.

### 1.1 `__init__()` Phase (Synchronous)

| Step | Action | Wired To |
|------|--------|----------|
| 1 | Create `HealthRegistry` | Server-level singleton |
| 2 | Create `FaultEngine` | Server-level singleton |
| 3 | Build `Aquilary.from_manifests()` | Produces `AquilaryRegistry` |
| 4 | Build `RuntimeRegistry.from_metadata()` | Creates DI containers per-app |
| 5 | Register `FaultEngine` in all DI containers | `ValueProvider(token=FaultEngine)` |
| 6 | Register `EffectRegistry` in all DI containers | `ValueProvider(token=EffectRegistry)` |
| 7 | Create `LifecycleCoordinator` | Takes `runtime` + `config` |
| 8 | Connect lifecycle fault observer | `coordinator.on_event()` |
| 9 | Create `ControllerRouter` | Empty, populated at startup |
| 10 | Create `MiddlewareStack` | Populated by `_setup_middleware()` |
| 11 | `_setup_middleware()` | See §1.2 below |
| 12 | `_get_base_container()` | First DI container or fallback |
| 13 | Create `ControllerFactory(app_container=base_container)` | DI-based instantiation |
| 14 | Create `ControllerEngine(factory, fault_engine)` | effect_registry=None (deferred) |
| 15 | Create `ControllerCompiler` | Stateless, pattern-based |
| 16 | Create `ASGIAdapter(router, engine, sockets, middleware, server)` | ASGI bridge |

### 1.2 `_setup_middleware()` Wiring

| Priority | Middleware | DI Registration | Notes |
|----------|-----------|-----------------|-------|
| 2 | `FaultMiddleware` | ✅ FaultEngine | Always registered |
| 5 | `request_scope_mw` | — | DI container lifecycle |
| 1/10 | Exception/RequestId | — | Legacy defaults (if no chain config) |
| 15 | `AquilAuthMiddleware` or `SessionMiddleware` | ✅ AuthManager/SessionEngine | Conditional |
| 25 | `TemplateMiddleware` | ✅ TemplateEngine | Conditional |
| — | Mail, Cache, Storage, I18n, Tasks, ErrorTracker | ✅ Each registered | Conditional |
| 3-12 | Security middleware | — | Conditional per config |
| — | AquilaSockets | — | WebSocket runtime |

### 1.3 DI Registration Summary

Every subsystem registers its primary service(s) in **all** DI containers:

```
for container in self.runtime.di_containers.values():
    container.register(ValueProvider(...))
```

| Token | Scope | Registered In |
|-------|-------|---------------|
| `FaultEngine` | app | `__init__` |
| `EffectRegistry` | app | `__init__` |
| `AuthManager` | app | `_setup_middleware` |
| `MemoryIdentityStore` | app | `_setup_middleware` (string token) |
| `MemoryCredentialStore` | app | `_setup_middleware` (string token) |
| `TokenManager` | app | `_setup_middleware` (string token) |
| `PasswordHasher` | app | `_setup_middleware` (string token) |
| `SessionEngine` | app | `_setup_middleware` |
| `TemplateEngine` | app | `_setup_middleware` (via providers) |
| `MailService` + `MailConfig` | app | `_setup_mail` (via di_providers) |
| `CacheService` + `CacheBackend` | app | `_setup_cache` (via di_providers) |
| `StorageRegistry` | app | `_setup_storage` |
| `I18nService` + `I18nConfig` | app | `_setup_i18n` (via di_providers) |
| `TaskManager` | app | `_setup_tasks` |
| `AquiliaDatabase` | app | `_register_amdl_models` |
| `ModelRegistry` | app | `_register_amdl_models` |

### 1.4 `startup()` Phase (Async)

| Step | Action | Wired To |
|------|--------|----------|
| 0 | `runtime.perform_autodiscovery()` | Scans modules/ for controllers/services |
| 1 | `_load_controllers()` | Compiles routes, validates conflicts |
| 1.1 | `_load_starter_controller()` | Debug-mode auto-load |
| 1.2 | `aquila_sockets.initialize()` | WebSocket runtime |
| 1.3 | `_load_socket_controllers()` | WebSocket route registration |
| 1.4 | `_register_fault_handlers()` | Per-app fault handlers |
| 1.5 | `_register_docs_routes()` | OpenAPI/Swagger/ReDoc |
| 1.6 | `_wire_admin_integration()` | Admin routes + services |
| 2 | `runtime.compile_routes()` | Final route compilation |
| 3 | `coordinator.startup()` | App lifecycle hooks |
| 3.1 | `_register_amdl_models()` | AMDL/Python model discovery + DB |
| 3.2 | `_mail_service.on_startup()` | Mail provider connections |
| 3.3 | `_task_manager.start()` | Background workers |
| 3.5 | `_register_effects()` + `effect_registry.initialize_all()` | Effect providers |
| 3.5b | Wire `effect_registry` → `controller_engine` | Late binding (by design) |
| 3.6 | `_cache_service.initialize()` | Cache backend connection |
| 3.7 | `_storage_registry.initialize_all()` | Storage backend initialization |
| 4 | Health registration | All subsystem statuses |

---

## 2. Request Lifecycle Wiring

### 2.1 Hot Path (handle_http)

```
ASGI __call__ → handle_http()
  1. Build middleware chain (once, cached)
  2. Fast-path: /_health → bypass middleware
  3. Create Request from ASGI scope
  4. Sync route matching (O(1) static / O(k) trie)
  5. HEAD auto-support fallback
  6. 405 Method Not Allowed detection
  7. Resolve DI container (app_name → runtime.di_containers)
  8. Create request-scoped container (create_request_scope)
  9. Acquire RequestCtx from pool
  10. Store controller_match in request.state
  11. Execute cached middleware chain
      → FaultMiddleware
      → request_scope_mw (stores DI refs, cleanup)
      → [Security middleware...]
      → SessionMiddleware/AuthMiddleware
      → CSRFMiddleware (AFTER session — FIXED)
      → [I18n, Template, Cache middleware...]
      → _final_handler
        → ControllerEngine.execute(route, request, params, container)
          → FlowPipeline (guards, transforms, hooks)
          → Controller method invocation
  12. Metrics tracking (request_started/finished)
  13. DI container cleanup (via request_scope_mw)
  14. HEAD body stripping
  15. Send ASGI response
```

### 2.2 DI Container Flow

```
App Container (scope="app")
  └── create_request_scope()
       └── Request Container (scope="request")
            ├── Inherits all app-scoped providers (copy-on-write)
            ├── Session registered via register_instance()
            ├── Identity registered via register_instance()
            └── shutdown() called by request_scope_mw
```

---

## 3. Cross-Cutting Concerns

### 3.1 Error Handling Chain

```
Exception in handler
  → ExceptionMiddleware (outermost) catches
    → FaultMiddleware transforms to Fault
      → FaultEngine.process() dispatches to handlers
        → ErrorTracker.capture() records for admin
          → Response with error details (JSON or debug HTML)
```

### 3.2 Effect Lifecycle (per-request)

```
@requires(DBTx['write'], Cache['user'])
async def create_user(self, ctx):
    ...

FlowPipeline detects @requires decorators
  → EffectScope.acquire_all() per declared effect
    → DBTxProvider.acquire('write') → transaction
    → CacheProvider.acquire('user') → cache handle
      → Handler executes with effects available
    → EffectScope.release_all(success=True/False)
      → DBTxProvider.release(tx, success) → commit/rollback
      → CacheProvider.release(cache, success)
```

### 3.3 Auth → Session Integration

```
AquilAuthMiddleware
  ├── SessionEngine.load(request) → Session
  ├── Session → Identity extraction (if bound)
  ├── Identity → request.state["identity"]
  ├── Session → request.state["session"]
  ├── Container.register_instance(Session, session)
  ├── Container.register_instance(Identity, identity)
  └── SessionEngine.save(response) → Set-Cookie
```

---

## 4. Wiring Verification Results

All 21 subsystems verified for correct wiring:
- ✅ DI registration in all containers
- ✅ Lifecycle hooks (startup/shutdown)
- ✅ Middleware chain ordering (fixed INT-01)
- ✅ Cross-subsystem references (FaultEngine → ErrorTracker, Effects → FlowPipeline)
- ✅ No dangling references or missing registrations
