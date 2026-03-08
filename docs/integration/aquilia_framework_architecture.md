# Aquilia Framework Architecture

**Phase 12 — Integration Audit**
**Aquilia v1.0.1**

---

## 1. High-Level Architecture

Aquilia is an async-first Python ASGI framework following a manifest-driven
architecture. It combines ideas from NestJS (controller-based routing, DI),
Effect-TS (typed effects, layers), Django (ORM, admin), and Express (middleware)
into a cohesive Python-native design.

### 1.1 Core Design Principles

1. **Manifest-First** — Module internals live in `manifest.py`; workspace.py
   orchestrates modules without knowing their internals.
2. **Static-then-Runtime** — Manifests are validated statically (Aquilary),
   then compiled to a runtime registry. This enables deployment gating via
   registry fingerprints.
3. **Scope-Isolated DI** — App-scoped containers inherit to request-scoped
   children via copy-on-write. No global mutable state.
4. **Effect-Aware Handlers** — Side effects (DB, cache, queue) are declared
   via `@requires()`, acquired/released automatically by FlowPipeline.
5. **Fault-Centric Errors** — All errors are `Fault` objects with domain,
   code, metadata. Raw exceptions are caught at the boundary.

### 1.2 Layer Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    ASGI Protocol Layer                    │
│                    (ASGIAdapter)                          │
├─────────────────────────────────────────────────────────┤
│                    Middleware Layer                       │
│  FaultMW → Scope → Security → Session → CSRF → I18n → … │
├─────────────────────────────────────────────────────────┤
│                    Controller Layer                       │
│  Router → Engine → Factory → FlowPipeline → Handler      │
├─────────────────────────────────────────────────────────┤
│                    Service Layer                          │
│  DI Container → Services → Effects → Providers           │
├─────────────────────────────────────────────────────────┤
│                    Data Layer                             │
│  Models → QueryBuilder → Migrations → Database           │
├─────────────────────────────────────────────────────────┤
│                    Infrastructure Layer                   │
│  Mail → Cache → Storage → Tasks → Sockets                │
└─────────────────────────────────────────────────────────┘
```

---

## 2. Module System

### 2.1 Module Structure (Convention)

```
modules/<name>/
├── manifest.py          # AppManifest (source of truth)
├── controllers.py       # Controller classes
├── services.py          # Service classes (DI-injectable)
├── models/
│   ├── __init__.py      # Model classes
│   └── *.amdl           # Legacy AMDL model definitions
├── blueprints.py        # Request/response schemas
├── tasks.py             # Background job definitions
├── static/              # Module-scoped static files
├── templates/           # Module-scoped templates
└── tests/               # Module-scoped tests
```

### 2.2 Module Lifecycle

```
manifest.py (static declaration)
  → Aquilary.from_manifests() (validation + dependency graph)
    → topological sort (dependency order)
      → RuntimeRegistry (DI containers per module)
        → autodiscovery (scan for controllers/services)
          → LifecycleCoordinator.startup() (on_startup hooks)
            → Module ready
```

### 2.3 Module Encapsulation (v2)

Modules can declare `imports` and `exports`:
- **imports**: Which modules this module depends on (provides access to their exports)
- **exports**: Which services/components are exposed to importers

This enables NestJS-style module encapsulation while keeping the Python
convention of explicit imports.

---

## 3. DI System Architecture

### 3.1 Container Hierarchy

```
Root Container (scope="app")
├── Per-App Container (scope="app", one per module)
│   ├── App-scoped providers (singletons per module)
│   └── create_request_scope()
│        └── Request Container (scope="request")
│            ├── Copy-on-write provider inheritance
│            ├── Request-scoped instances
│            └── Automatic shutdown on request end
```

### 3.2 Provider Types

| Provider | Lifecycle | Use Case |
|----------|-----------|----------|
| `ClassProvider` | Per-resolve or cached | Service classes |
| `FactoryProvider` | Per-resolve | Dynamic creation |
| `ValueProvider` | Singleton | Pre-built instances |

### 3.3 Resolution Strategy

```python
# Annotation-driven (preferred)
class UserController(Controller):
    def __init__(self, service: Annotated[UserService, Dep()]):
        self.service = service

# Type-hint based (auto-resolve)
class UserController(Controller):
    def __init__(self, service: UserService):
        self.service = service
```

Resolution order:
1. Check cache (O(1))
2. Lookup provider by token (O(1))
3. Walk parent chain if not found
4. Raise `ProviderNotFoundError` if terminal

---

## 4. Controller Architecture

### 4.1 Controller Pipeline

```
Request
  → ControllerRouter.match_sync()        # Route matching
    → ControllerEngine.execute()          # Orchestration
      → ControllerFactory.create()        # DI instantiation
        → FlowPipeline (class-level)      # Guards/transforms
          → FlowPipeline (method-level)   # Per-route guards
            → Clearance evaluation        # Declarative ACL
              → Parameter binding         # Path/query/body
                → Interceptors (before)   # Pre-hooks
                  → Handler execution     # User code
                → Interceptors (after)    # Post-hooks
              → Exception filters         # Error handling
            → Response conversion         # Normalize to Response
```

### 4.2 FlowPipeline Integration

The FlowPipeline (inspired by Effect-TS) provides a composable pipeline
of nodes:

| Node Type | Purpose | Example |
|-----------|---------|---------|
| `guard` | Accept/reject request | `@require_auth` |
| `transform` | Modify request/context | Input validation |
| `handler` | Process request | Business logic |
| `hook` | Side effects | Logging, analytics |

Effects declared via `@requires(DBTx['write'])` are automatically acquired
before pipeline execution and released after.

---

## 5. Fault System Architecture

### 5.1 Fault Hierarchy

```
Fault (base)
├── ModelFault
│   ├── AMDLParseFault
│   ├── ModelNotFoundFault
│   ├── QueryFault
│   └── DatabaseConnectionFault
├── AuthFault
│   ├── AdminAuthenticationFault
│   └── AdminAuthorizationFault
├── SessionFault
│   ├── SessionExpiredFault
│   └── SessionInvalidFault
├── CacheFault
│   ├── CacheMissFault
│   └── CacheConnectionFault
├── BlueprintFault
│   ├── CastFault
│   └── SealFault
└── ConfigInvalidFault
```

### 5.2 Fault Processing Pipeline

```
Exception raised
  → FaultMiddleware catches
    → Convert to Fault if needed
      → FaultEngine.process(fault, app)
        → Per-app handler (if registered)
        → Global handlers
        → ErrorTracker.capture() (for admin dashboard)
        → Observer callbacks
      → Response with fault details
```

---

## 6. Comparison with Modern Frameworks

| Feature | Aquilia | NestJS | FastAPI | Django |
|---------|---------|--------|---------|--------|
| DI System | ✅ Full container + scopes | ✅ Full | ❌ Depends | ❌ None |
| Type-safe routing | ✅ Pattern compiler | ✅ Decorators | ✅ Type hints | ❌ regex |
| Effect system | ✅ Typed effects | ❌ | ❌ | ❌ |
| FlowPipeline | ✅ Guard/transform/hook | ✅ Pipes/guards | ❌ | ❌ |
| ORM | ✅ Pure Python + AMDL | ❌ (TypeORM) | ❌ (SQLAlchemy) | ✅ Django ORM |
| Admin panel | ✅ Auto-generated | ❌ | ❌ | ✅ Django Admin |
| WebSockets | ✅ Controller-based | ✅ Gateways | ✅ | ❌ (channels) |
| Background tasks | ✅ Built-in TaskManager | ❌ (Bull) | ❌ (Celery) | ❌ (Celery) |
| Mail system | ✅ Built-in AquilaMail | ❌ (Nodemailer) | ❌ | ✅ django.mail |
| Session system | ✅ Policy-based | ✅ (express-session) | ❌ | ✅ |
| Middleware | ✅ Priority-ordered | ✅ | ✅ | ✅ |
| Config system | ✅ Fluent Python builders | ✅ ConfigModule | ✅ Settings | ✅ settings.py |
| Blueprint/Schema | ✅ Bidirectional Facets | ✅ DTOs | ✅ Pydantic | ✅ Serializers |
| Clearance/ACL | ✅ Declarative grants | ✅ CASL | ❌ | ✅ Permissions |
| i18n | ✅ Built-in | ✅ (i18next) | ❌ | ✅ |

Aquilia's unique differentiators:
- **Manifest-First Architecture** — Static validation before runtime
- **Effect System** — Typed side-effect management inspired by Effect-TS
- **Blueprint Facets** — Bidirectional model↔world contracts with casting
- **Clearance System** — Declarative access control with `@grant`/`@exempt`
- **AMDL** — Domain-specific language for model definitions (legacy)
