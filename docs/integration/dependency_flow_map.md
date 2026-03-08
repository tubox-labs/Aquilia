# Dependency Flow Map

**Phase 12 — Integration Audit**
**Aquilia v1.0.1**

---

## 1. Package Dependency Graph

```
aquilia/
├── config.py              → (no internal deps)
├── config_builders.py     → config, sessions, auth, db
├── _datastructures.py     → (no internal deps)
├── _uploads.py            → (no internal deps)
│
├── faults/                → (no internal deps — leaf)
│   ├── core.py            → (standalone)
│   ├── domains.py         → core
│   ├── engine.py          → core, domains
│   └── middleware.py       → core, engine, response
│
├── di/                    → faults
│   ├── core.py            → faults.domains (DIFault)
│   ├── providers.py       → core, faults.domains
│   ├── decorators.py      → core
│   ├── dep.py             → (standalone)
│   ├── request_dag.py     → core, providers
│   └── lifecycle.py       → (standalone)
│
├── patterns/              → (no internal deps — leaf)
│
├── request.py             → _datastructures, _uploads
├── response.py            → (no internal deps)
│
├── middleware.py           → request, response, faults
│
├── engine.py              → di
│
├── effects.py             → (standalone with DI integration)
├── flow.py                → effects, engine
│
├── controller/            → di, patterns, request, response, middleware, flow, effects
│   ├── base.py            → request, response, engine
│   ├── metadata.py        → (standalone)
│   ├── compiler.py        → metadata, patterns
│   ├── router.py          → compiler, patterns
│   ├── factory.py         → di
│   └── engine.py          → factory, compiler, flow, effects, faults
│
├── sessions/              → faults, di
│   ├── core.py            → faults
│   ├── transport.py       → faults
│   ├── store.py           → faults
│   ├── engine.py          → core, transport, store, faults
│   └── providers.py       → di, engine
│
├── auth/                  → sessions, faults, di
│   ├── core.py            → (standalone)
│   ├── manager.py         → core, stores, tokens, hashing
│   ├── tokens.py          → core
│   ├── hashing.py         → (standalone)
│   ├── authz.py           → core
│   ├── clearance.py       → core, authz
│   └── integration/       → sessions, di, middleware
│
├── blueprints/            → faults, di
│   ├── core.py            → faults
│   ├── facets.py          → faults
│   └── integration.py     → faults, di
│
├── models/                → faults, db
│   ├── base.py            → faults
│   ├── fields.py          → (standalone)
│   ├── query.py           → base, db
│   └── migrations.py      → base, db
│
├── db/                    → faults
│   └── engine.py          → faults
│
├── templates/             → middleware, config
├── mail/                  → di, faults
├── cache/                 → di, faults
├── storage/               → faults
├── i18n/                  → di, faults
├── tasks/                 → faults, effects
├── sockets/               → di, auth, sessions, controller
│
├── aquilary/              → di, discovery
│   ├── core.py            → (standalone registry types)
│   ├── loader.py          → manifest parsing
│   ├── validator.py       → manifest validation
│   ├── graph.py           → dependency resolution
│   ├── fingerprint.py     → hash generation
│   └── runtime.py         → di, discovery
│
├── lifecycle.py           → aquilary
├── health.py              → (standalone)
│
├── admin/                 → ALL subsystems (integration point)
│
├── asgi.py                → controller, middleware, engine, health
├── server.py              → ALL subsystems (orchestrator)
└── __init__.py            → ALL subsystems (public API)
```

---

## 2. Circular Dependency Analysis

### 2.1 Known Circular Chains

No true import-time circular dependencies exist. The framework uses several
strategies to avoid them:

1. **TYPE_CHECKING guards** — Forward references in type hints
2. **Lazy imports** — `from .module import X` inside functions, not at module level
3. **String tokens** — DI registration uses string keys to break type cycles

### 2.2 Potential Tight Coupling Points

| From | To | Coupling | Mitigation |
|------|----|----------|------------|
| `server.py` | `admin/controller.py` | Direct instantiation | Admin is optional; guarded by try/except ImportError |
| `controller/engine.py` | `flow.py` | Pipeline execution | FlowPipeline is optional; `None` check |
| `auth/integration/` | `sessions/` | Session ↔ Auth bridge | Clean interface via `SessionAuthBridge` |
| `asgi.py` | `server.py` | Back-reference | Necessary for lifespan; `server` is Optional |

---

## 3. Data Flow Diagram

### 3.1 Configuration Flow

```
workspace.py
  → Workspace(...).module(...).integrate(...)
    → config_builders.py builds ConfigLoader
      → server.py receives config
        → _setup_middleware() reads config sections
        → _setup_mail/cache/storage/i18n/tasks() read config
        → _create_session_engine() reads session config
        → _create_auth_manager() reads auth config
```

### 3.2 DI Registration Flow

```
AquiliaServer.__init__()
  → RuntimeRegistry creates DI containers (one per app)
    → server registers global singletons (FaultEngine, EffectRegistry)
    → _setup_middleware() registers auth/session services
    → _setup_mail/cache/storage/i18n/tasks() register subsystem services
    → startup() → _register_amdl_models() registers DB/ORM
```

### 3.3 Request Data Flow

```
ASGI scope/receive
  → Request (lazy parsing)
    → Route match → ControllerRouteMatch
      → DI container (request-scoped)
        → RequestCtx (pooled)
          → Middleware chain (state injection)
            → Controller (DI-resolved)
              → Handler method
                → Response
                  → ASGI send
```

---

## 4. Subsystem Initialization Order

The order of subsystem initialization during `__init__` and `startup()` is
carefully designed to respect dependencies:

### 4.1 __init__ Order

```
1. HealthRegistry          (no deps)
2. FaultEngine             (no deps)
3. Aquilary                (config)
4. RuntimeRegistry         (Aquilary)
5. DI Registration         (RuntimeRegistry)
6. LifecycleCoordinator    (RuntimeRegistry, config)
7. ControllerRouter        (no deps)
8. MiddlewareStack         (no deps)
9. _setup_middleware        (config, RuntimeRegistry, FaultEngine)
   a. FaultMiddleware      (FaultEngine)
   b. request_scope_mw     (RuntimeRegistry)
   c. Security middleware  (config)
   d. Session/Auth         (config → SessionEngine → AuthManager)
   e. Templates            (config, manifests)
   f. Mail/Cache/Storage/I18n/Tasks/ErrorTracker
   g. Security middleware  (config)
   h. WebSockets           (RuntimeRegistry, Auth, Sessions)
10. ControllerFactory      (DI container)
11. ControllerEngine       (Factory, FaultEngine)
12. ControllerCompiler     (no deps)
13. ASGIAdapter            (Router, Engine, Sockets, Middleware, Server)
```

### 4.2 startup() Order

```
1. Autodiscovery           (RuntimeRegistry)
2. Load controllers        (Compiler, Router)
3. Wire admin              (config, Router, admin subsystems)
4. Compile routes          (RuntimeRegistry)
5. Lifecycle hooks         (per-app, in topological order)
6. Register models/DB      (models/, db/)
7. Mail startup            (MailService)
8. Task manager start      (TaskManager)
9. Effects initialization  (EffectRegistry → ControllerEngine)
10. Cache initialization   (CacheService)
11. Storage initialization (StorageRegistry)
12. Health registration    (all subsystem statuses)
```

### 4.3 shutdown() Order (Reverse)

```
1. Lifecycle shutdown hooks (reverse topological order)
2. Mail shutdown
3. Task manager stop
4. Cache shutdown
5. Storage shutdown
6. DI container cleanup (all apps)
7. Effect finalization
8. WebSocket shutdown
9. Database disconnect
```
