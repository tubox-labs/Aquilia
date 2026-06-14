# Architecture Overview

Aquilia is an async-native, manifest-first Python web framework. It auto-discovers modules, wires dependency injection, and generates infrastructure artefacts. This page describes the high-level architecture, layered design, and component relationships.

## Architectural Layers

Aquilia follows a clean layered architecture with four primary tiers:

```
┌──────────────────────────────────────────────────────────────────┐
│                    Presentation Layer                              │
│  ASGIAdapter │ MiddlewareStack │ Request/Response │ Templates     │
├──────────────────────────────────────────────────────────────────┤
│                    Application Layer                               │
│  Controllers │ Router │ Engine │ Versioning │ Fault Engine         │
├──────────────────────────────────────────────────────────────────┤
│                      Domain Layer                                  │
│  Auth │ Sessions │ Storage │ Tasks │ Cache │ Mail │ i18n           │
├──────────────────────────────────────────────────────────────────┤
│                  Infrastructure Layer                              │
│  DI │ Aquilary │ Manifest Loader │ Config │ DB/ORM │ Signing      │
└──────────────────────────────────────────────────────────────────┘
```

### Presentation Layer

The outermost layer responsible for HTTP protocol handling. The `ASGIAdapter` (`aquilia/asgi.py`) bridges the ASGI protocol to Aquilia's typed request/response system. It handles HTTP, WebSocket, and lifespan events. The `MiddlewareStack` (`aquilia/middleware.py`) provides composable, ordered middleware execution for cross-cutting concerns like authentication, CORS, CSRF, rate limiting, and static file serving.

### Application Layer

Contains the controller system — routing, execution, and API versioning. The `ControllerRouter` (`aquilia/controller/router.py`) performs path-to-handler matching with a two-tier strategy (O(1) static hash maps + O(k) segment tries for parameterised routes). The `ControllerEngine` (`aquilia/controller/engine.py`) orchestrates handler execution with full DI integration, lifecycle hooks, interceptors, and clearance enforcement.

### Domain Layer

Houses the framework's business capabilities as composable subsystems: authentication and authorisation (`aquilia/auth/`), session management (`aquilia/sessions/`), background task processing (`aquilia/tasks/`), file storage abstraction (`aquilia/storage/`), caching (`aquilia/cache/`), mail delivery (`aquilia/mail/`), and internationalisation (`aquilia/i18n/`). Each subsystem is independently configurable and can be enabled or disabled at the workspace level.

### Infrastructure Layer

Provides the foundation: hierarchical dependency injection (`aquilia/di/`), manifest discovery and validation (`aquilia/aquilary/`), configuration loading (`aquilia/config/`), the signing engine (`aquilia/signing.py`), and the ORM/database layer (`aquilia/models/`, `aquilia/db/`).

## Boot Sequence

The application lifecycle follows a deterministic pipeline:

```mermaid
sequenceDiagram
    participant EP as Entrypoint
    participant RT as AquiliaRuntime
    participant WS as workspace.py
    participant ML as ManifestLoader
    participant AQ as Aquilary
    participant RR as RuntimeRegistry
    participant SVR as AquiliaServer
    participant ASGI as ASGIAdapter

    EP->>RT: create_app()
    RT->>RT: Phase: CREATED
    RT->>RT: Phase: CONFIGURING
    RT->>WS: Load workspace.py via ConfigLoader
    WS-->>RT: Config data
    RT->>RT: Phase: DISCOVERING
    RT->>ML: Import modules/*/manifest.py
    ML-->>RT: Manifest list
    RT->>RT: Phase: BOOTSTRAPPING
    RT->>SVR: Construct AquiliaServer(manifests, config)
    SVR->>AQ: Aquilary.from_manifests()
    AQ-->>SVR: AquilaryRegistry
    SVR->>RR: RuntimeRegistry.from_metadata()
    RR->>RR: _register_services()
    SVR->>SVR: _setup_middleware()
    SVR->>SVR: Setup subsystems (cache, mail, storage, etc.)
    SVR->>ASGI: Create ASGIAdapter
    SVR-->>RT: Fully bootstrapped
    RT->>RT: Phase: READY

    Note over ASGI: ASGI lifespan.startup
    ASGI->>SVR: server.startup()
    SVR->>SVR: _load_controllers()
    SVR->>SVR: health_registry init
    SVR->>SVR: TaskManager start
    SVR-->>ASGI: Ready for traffic
    RT->>RT: Phase: RUNNING
```

## Component Diagram

```mermaid
graph TD
    subgraph External
        client[HTTP Client]
        ws[WebSocket Client]
    end

    subgraph ASGI["ASGI Boundary"]
        adapter[ASGIAdapter]
    end

    subgraph Middleware["Middleware Pipeline"]
        faults[FaultMiddleware<br/>priority: 2]
        proxy[ProxyFixMiddleware<br/>priority: 3]
        versioning[VersionMiddleware<br/>priority: 5]
        security[Security Headers / CSP<br/>priority: 7-10]
        cors[CORSMiddleware<br/>priority: 11]
        rate[RateLimitMiddleware<br/>priority: 12]
        auth[AuthMiddleware<br/>priority: 15]
        csrf[CSRFMiddleware<br/>priority: 20]
        i18n[I18nMiddleware<br/>priority: 24]
        templates[TemplateMiddleware<br/>priority: 25]
        cache[CacheMiddleware<br/>priority: 26]
    end

    subgraph Core["Core Application"]
        router[ControllerRouter]
        engine[ControllerEngine]
        factory[ControllerFactory]
        compiler[ControllerCompiler]
    end

    subgraph DI["Dependency Injection"]
        container[Container<br/>singleton / app / request]
    end

    subgraph Subsystems["Subsystems"]
        authman[AuthManager]
        sessions[SessionEngine]
        tasks[TaskManager]
        storage[StorageRegistry]
        cachesvc[CacheService]
        mail[MailService]
        i18nsvc[I18nService]
        template[TemplateEngine]
    end

    subgraph Infra["Infrastructure"]
        aquilary[AquilaryRegistry]
        runtime[RuntimeRegistry]
        config[ConfigLoader]
        signing[Signing Engine]
        db[Database / ORM]
    end

    client --> adapter
    ws --> adapter
    adapter --> faults
    faults --> proxy
    proxy --> versioning
    versioning --> auth
    auth --> cors
    cors --> rate
    rate --> csrf
    csrf --> i18n
    i18n --> templates
    templates --> cache
    cache --> router
    router --> engine
    engine --> factory
    factory --> container
    container --> Subsystems
    container --> Infra
```

## Key Design Principles

### Manifest-First Module Boundaries

Every module declares its controllers, services, middleware, and models through an `AppManifest` in `modules/<name>/manifest.py`. The `workspace.py` at the project root is orchestration metadata only — it declares which modules are active and configures integrations. This separation ensures clean module boundaries and enables tooling (CLI generators, validation, discovery).

### Structured Faults

All framework errors use `Fault` subclasses from `aquilia/faults/` with stable `code`, `message`, `domain`, and `severity` fields. The `FaultEngine` processes these faults through registered handlers, and the `FaultMiddleware` (always registered at priority 2) provides a safety net for unhandled exceptions. Raw Python exceptions are never raised for framework failures.

### DI Scope Discipline

Aquilia's DI system supports three scopes:

| Scope | Lifetime | Example |
|-------|----------|---------|
| `singleton` | Process lifetime | `TaskManager` instance |
| `app` | Application lifetime | `AuthManager`, `CacheService` |
| `request` | Single HTTP request | `RequestCtx`, per-request objects |

The `request` scope is created from the `app` container via `create_request_scope()` and is cleaned up after each request by the `request_scope_mw` middleware.

### Async-Native Pipeline

The entire request pipeline — from ASGI event reception through middleware execution, controller dispatch, and response generation — is fully asynchronous. Controllers and services use `async def`, and blocking operations (like gzip compression) are offloaded to thread pools.

## Directory Structure

```
project/
├── workspace.py              # Workspace orchestration
├── modules/                  # Application modules
│   ├── users/
│   │   ├── manifest.py       # AppManifest for the users module
│   │   ├── controllers.py    # Controller classes
│   │   ├── services.py       # Service classes
│   │   └── templates/        # Module-specific templates
│   └── admin/
│       ├── manifest.py
│       └── controllers.py
├── runtime/                  # Generated runtime artefacts (optional)
│   └── app.py
├── .env                      # Environment variables
└── Dockerfile                # Deployment configuration
```

## Environment Configuration

| Variable | Default | Description |
|----------|---------|-------------|
| `AQUILIA_WORKSPACE` | `/app` | Workspace root path |
| `AQUILIA_ENV` | `prod` | Runtime mode: `dev`, `test`, `prod` |
| `AQ_SECRET_KEY` | — | Signing secret for sessions/CSRF |
| `AQ_SERVER_WORKERS` | — | Number of uvicorn workers |
| `AQ_SERVER_PORT` | — | Listening port |

## Versioning and Compatibility

Aquilia supports API versioning through URL-prefix, header-based, query-parameter, and media-type strategies. The `VersionMiddleware` runs early in the pipeline (priority 5) and populates `request.state` with the resolved version. Routes can be bound to specific versions using `@version()` and `@version_range()` decorators, with automatic sunset enforcement via `SunsetPolicy`.