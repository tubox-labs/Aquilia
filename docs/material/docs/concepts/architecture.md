# Architecture

Aquilia follows a **manifest-first, layered composition** architecture. The boot sequence progresses through five deterministic phases: manifests are discovered, metadata is compiled into the Aquilary registry, DI containers are built, controllers are routed, and finally an ASGI adapter bridges everything to the protocol layer.

## High-Level Architecture

```mermaid
flowchart TB
    subgraph User["User Project"]
        W[workspace.py]
        M1[modules/users/manifest.py]
        M2[modules/auth/manifest.py]
        M3[modules/orders/manifest.py]
    end

    subgraph Boot["Boot Sequence"]
        direction LR
        P1["Manifests"] --> P2["Aquilary"]
        P2 --> P3["RuntimeRegistry"]
        P3 --> P4["Controllers"]
        P4 --> P5["ASGI"]
    end

    subgraph Server["AquiliaServer"]
        AR[Aquilary Registry]
        RR[Runtime Registry]
        LC[Lifecycle Coordinator]
        MW[Middleware Stack]
        CR[Controller Router]
        CE[Controller Engine]
        FE[Fault Engine]
        ER[Effect Registry]
        HR[Health Registry]
    end

    subgraph Protocol["ASGI Layer"]
        ASGI[ASGIAdapter]
        HTTP[HTTP Handler]
        WS[WebSocket Handler]
        LS[Lifespan Handler]
    end

    W --> Boot
    M1 --> Boot
    M2 --> Boot
    M3 --> Boot

    P2 --> AR
    P3 --> RR
    P4 --> CR

    ASGI --> HTTP
    ASGI --> WS
    ASGI --> LS

    Server --> ASGI
```

## Boot Sequence in Detail

The five-phase boot sequence is the backbone of every Aquilia application:

```mermaid
sequenceDiagram
    participant Entry as entrypoint.py
    participant RT as AquiliaRuntime
    participant WS as workspace.py
    participant AL as Aquilary
    participant RR as RuntimeRegistry
    participant CR as ControllerRouter
    participant ASGI as ASGIAdapter

    Entry->>RT: from_workspace(root, mode)
    activate RT

    rect rgb(230, 240, 255)
        Note over RT,WS: Phase 1: Configure
        RT->>RT: configure()
        RT->>RT: Set AQUILIA_WORKSPACE, AQUILIA_ENV
        RT->>RT: Configure logging
        RT->>WS: Import workspace.py
        WS-->>RT: Workspace + Module configs
    end

    rect rgb(230, 255, 230)
        Note over RT,AL: Phase 2: Discover
        RT->>RT: discover()
        RT->>RT: Parse module declarations
        RT->>RT: Import modules/*/manifest.py
        RT->>AL: Load manifests
        AL-->>RT: AppManifest instances
    end

    rect rgb(255, 245, 230)
        Note over RT,RR: Phase 3: Bootstrap
        RT->>RT: bootstrap()
        RT->>RT: Construct AquiliaServer
        RT->>AL: Build Aquilary registry
        AL-->>RT: Validated registry
        RT->>RR: Build RuntimeRegistry
        RR-->>RT: DI containers + services
    end

    rect rgb(255, 230, 245)
        Note over RT,ASGI: Phase 4: Routes + ASGI
        RT->>CR: Compile controller routes
        CR-->>RT: Compiled routes
        RT->>ASGI: Create ASGIAdapter
        ASGI-->>RT: ASGI app
    end

    deactivate RT
```

### Phase 1: Configuration

`AquiliaRuntime.configure()` sets the workspace root in `sys.path`, resolves `AQUILIA_ENV` and `AQUILIA_WORKSPACE` environment variables, configures structured logging, verifies the existence of `workspace.py`, and loads configuration through `ConfigLoader`. The loader merges workspace structure, `.env` files, and `AQ_` prefixed environment variable overlays.

### Phase 2: Discovery

`AquiliaRuntime.discover()` imports `workspace.py`, extracts declared `Module` pointers, imports each `modules/<name>/manifest.py`, and performs dynamic module discovery for directories containing a `manifest.py`. Each manifest's `AppManifest` declares its controllers, services, middleware, models, task handlers, socket controllers, and fault handlers via dotted component references.

### Phase 3: Bootstrap — Aquilary Registry

`AquiliaServer` builds the **Aquilary registry** — the central metadata store. The registry validates manifest compatibility, resolves dependency ordering between modules, checks for route conflicts, and produces a `RuntimeRegistry` with compiled component metadata. A cryptographic fingerprint is generated for deterministic deployments.

### Phase 4: Dependency Injection

The `RuntimeRegistry` builds hierarchical **DI containers**: singleton scope (process-wide), app scope (per-module), and request scope (per-request). Service providers, factory functions, and value providers are registered with their lifecycle policies. Cross-module dependency imports/exports are enforced.

### Phase 5: Controller Routing

`ControllerRouter` compiles all controller route decorators into a segment trie: static routes use `O(1)` dict lookups per HTTP method, dynamic routes use `O(k)` trie traversal (where `k` is URL path depth), and complex patterns fall back to regex matching.

## Component Architecture

```mermaid
flowchart LR
    subgraph Workspace["Workspace Orchestration"]
        direction TB
        WCONF["Workspace<br/>Name, Version, Mode"]
        WMOD["Module<br/>route_prefix, depends_on, tags"]
        WINT["Integration<br/>Database, Cache, Storage, Mail"]
    end

    subgraph Manifest["Module Manifest"]
        direction TB
        MCTRL["Controllers"]
        MSVC["Services"]
        MMW["Middleware"]
        MMODEL["Models"]
        MSOCK["Socket Controllers"]
        MTASK["Background Tasks"]
        MFAULT["Fault Handlers"]
    end

    subgraph Registry["Aquilary Registry"]
        direction TB
        AVAL["Validator<br/>Dependencies, Routes, Config"]
        ALOAD["Loader<br/>Import manifests, Resolve refs"]
        AFINGER["Fingerprint<br/>Deterministic build hash"]
    end

    subgraph DI["Runtime Registry"]
        direction TB
        DID["DI Containers<br/>Singleton / App / Request"]
        DIPROV["Providers<br/>Class, Factory, Value, Pool"]
        DILIFE["Lifecycle Hooks<br/>startup / shutdown / dispose"]
    end

    subgraph Runtime["Request Runtime"]
        direction TB
        RRMW["Middleware Stack<br/>Global → App → Controller → Route"]
        RRCTRL["Controller Engine<br/>Execute compiled route"]
        RREFF["Effect System<br/>DB, Cache, HTTP, Queue, Storage"]
        RRFM["Fault Middleware<br/>Convert faults to HTTP responses"]
    end

    Workspace --> Manifest
    Manifest --> Registry
    Registry --> DI
    DI --> Runtime
```

## Request Lifecycle

```mermaid
flowchart TD
    R1["ASGIAdapter.__call__()"] --> R2{"Scope Type?"}

    R2 -->|http| R3["handle_http()"]
    R2 -->|websocket| R4["handle_websocket()"]
    R2 -->|lifespan| R5["handle_lifespan()"]

    R3 --> R6["Build/cache middleware chain"]
    R6 --> R7{"Is /_health?"}
    R7 -->|Yes| R8["Return engine metrics"]
    R7 -->|No| R9["Wrap ASGI scope → Request"]
    R9 --> R10["Pre-resolve API version (if active)"]
    R10 --> R11["ControllerRouter.match_sync()"]
    R11 --> R12{"Route found?"}
    R12 -->|No| R13["Return 404"]
    R12 -->|Yes| R14["Create request DI container"]
    R14 --> R15["Allocate RequestCtx (pooled)"]
    R15 --> R16["Execute middleware chain"]
    R16 --> R17["ControllerEngine.execute()"]
    R17 --> R18["Fault handling (if any)"]
    R18 --> R19["Response.send_asgi()"]
    R19 --> R20["Record metrics, release context"]
    R20 --> R21["Return"]

    R5 --> R22{"Lifespan event?"}
    R22 -->|startup| R23["AquiliaServer.startup()"]
    R22 -->|shutdown| R24["AquiliaServer.shutdown()"]
```

## Key Architectural Properties

| Property | Implementation |
|---|---|
| **Manifest-first** | No import-time side effects. All components declared in manifests, loaded on demand. |
| **Segmented routing** | Segment trie for `O(k)` dynamic route matching. Static routes use `O(1)` dict lookups. |
| **Pooled contexts** | `RequestCtx` uses a pre-allocated ring buffer pool, eliminating per-request allocations. |
| **Hierarchical DI** | Singleton → App → Request scopes with cycle detection and lazy resolution. |
| **Structured faults** | Every error is a `Fault` subclass with domain, code, severity, and recovery strategy. |
| **Effect awareness** | Handlers declare required capabilities. The runtime acquires and releases resources automatically. |
| **Deterministic builds** | Registry fingerprinting enables frozen deployments and integrity verification. |
| **Health tracking** | `HealthRegistry` monitors every subsystem with composable `HealthStatus` checks. |

## Directory Layout

```
my-project/
├── workspace.py              # Workspace + Module + Integration declarations
├── modules/
│   ├── users/
│   │   ├── manifest.py       # AppManifest: controllers, services, models
│   │   ├── controllers.py    # Controller classes
│   │   ├── services.py       # Business logic services
│   │   ├── models.py         # ORM models
│   │   └── blueprints.py     # Request/response Blueprints
│   ├── auth/
│   │   ├── manifest.py
│   │   ├── controllers.py
│   │   ├── guards.py
│   │   └── services.py
│   └── orders/
│       ├── manifest.py
│       ├── controllers.py
│       ├── services.py
│       └── models.py
├── templates/                # Jinja2 templates
├── migrations/               # Database migrations
├── .env                     # Environment variables
└── config/                   # Additional Python config (optional)
```

## Design Decisions

### Why Manifest-First?

Traditional Python frameworks often rely on import-time side effects (decorator registration, global route tables) that make testing, tooling, and introspection fragile. Aquilia's manifest-first design means:

- **No global state** — every piece of metadata is declared explicitly in `manifest.py`.
- **Tooling-friendly** — the `aq` CLI can inspect, validate, and freeze manifests without executing application code.
- **Test isolation** — test suites can construct `AquiliaServer` with a subset of manifests.
- **Deterministic deployment** — the registry fingerprint guarantees that what was tested is what gets deployed.

### Why Segment Trie Routing?

`ControllerRouter` uses a radix (segment) trie rather than regex iteration:

- Static paths (`/users`, `/users/profile`) use `O(1)` dict lookups.
- Dynamic paths (`/users/{id:int}`, `/posts/{slug}`) use `O(k)` trie traversal with inline type casting.
- Regex is only a fallback for patterns the trie cannot express (e.g., `/{filename}.{ext}`).

### Why Pooled RequestCtx?

Per-request heap allocation of context objects adds measurable overhead at scale. `_RequestCtxPool` pre-allocates a ring buffer of `RequestCtx` instances with `__slots__` for compact memory. `acquire()` resets fields in-place, eliminating allocations from the hot path.