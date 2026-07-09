# Aquilary Module Registry

The Aquilary Registry is Aquilia's manifest-driven module discovery and dependency resolution engine. It manages module declarations, checks configuration namespaces, resolves dependencies topologically, indexes route structures, and generates secure cryptographic fingerprints to enable deterministic hot-reloads.

To prevent import-time side effects and keep development tooling fast, Aquilia separates registry instantiation into two distinct phases:

1. **Static Validation Phase** (`AquilaryRegistry`): Evaluates manifest declarations without importing controller or service code. It checks route conflicts, resolves dependency cycles, and computes the load order topologically.
2. **Lazy Compilation Phase** (`RuntimeRegistry`): Active only during live ASGI server bootstrapping. Performs runtime package scans, imports user code, compiles route trees, and builds Dependency Injection (DI) containers.

---

## Core Architecture & Execution Flow

```
[AppManifest Sources]
         │
         ▼
  [ManifestLoader]      ◄─── Phase 1: Reads declarations (safely, no imports)
         │
         ▼
 [RegistryValidator]    ◄─── Phase 1: Validates schemas & scans route templates
         │
         ▼
  [DependencyGraph]     ◄─── Phase 1: Detects cycle errors & sorts modules topologically
         │
         ▼
 [AquilaryRegistry]     ◄─── Phase 1: Produces RegistryFingerprint (frozen metadata)
         │
         ▼
 [RuntimeRegistry]      ◄─── Phase 2: Server bootstrap triggers lazy compilation
         │
         ▼
  [PackageScanner]      ◄─── Phase 2: Recursively scans module package files
         │
         ▼
  [RouteCompiler]       ◄─── Phase 2: Imports controllers, binds DI containers
```

---

## Phase 1: Static Validation Phase

The static phase reads metadata declarations from workspace module manifests and compiles them into a validated layout. No executable code is imported during this phase, meaning errors like syntax bugs or circular imports in your controllers do not crash CLI validation commands (`aq validate` / `aq inspect`).

### 1. Manifest Loader (`ManifestLoader`)
Loads manifest declarations from mixed sources. Sources can be:
* Direct Python class references.
* File paths to Python manifest files (`manifest.py`).
* Domain-Specific Language (DSL) configurations (`manifest.yaml` / `manifest.json`).

### 2. Registry Validator (`RegistryValidator`)
Validates the loaded manifests against configuration namespaces and checks for conflicts:
* **Duplicate App Check**: Assures that two modules do not share the same registry name.
* **Route Conflict Check**: Scans defined route templates to preemptively flag colliding path patterns.

### 3. Dependency Graph Resolver (`DependencyGraph`)
Constructs an internal directional graph mapping load order dependencies defined by `depends_on`/`imports` tags. It runs a cycle detection check and executes a topological sort to compute the final safe load sequence:
```python
# topological_sort computes the load order:
# For graph A -> B, A loads first, then B.
load_order = dep_graph.topological_sort()
```
If circular references are discovered, it aborts execution and raises a `DependencyCycleError`.

### 4. Cryptographic Fingerprinting (`RegistryFingerprint`)
Generates a SHA-256 hash representing the absolute configuration state:
* Hashes manifest properties, configuration namespaces, and file paths.
* Incorporates registry mode (`dev`, `prod`, `test`), app count, and route metadata.
* Used as a deployment gate. If the server is in `prod` mode and the running registry hash does not match the frozen metadata hash, the deployment is blocked.

---

## Phase 2: Lazy Compilation Phase

The compilation phase is initiated when the live ASGI web server bootstraps. This is where actual user modules are imported and instanced.

### 1. Auto-Discovery & Scanning (`PackageScanner`)
If `auto_discover` is enabled for a module, the `PackageScanner` scans the package directory (`modules.{module_name}`) recursively to identify components:
* **Controllers**: Identifies classes subclassing `Controller` or ending in `Controller`.
* **Services**: Scans for classes ending in `Service` or decorated with DI annotations.
* **Socket Controllers**: Scans for classes decorated with `@Socket`.
* **Background Tasks**: Imports `tasks.py` to trigger `@task` registration.
* **Models**: Scans the `models/` folder and registers SQL tables with the active database connection.

### 2. Dependency Injection Bindings
Instantiates and registers discovered services in request-scoped DI containers.

### 3. Route Compilation & Handler Wrapping
The `RouteCompiler` compiles route trees from the indexed controller metadata. It imports the target controllers and wraps each endpoint handler in a wrapper:
```python
# Binds request-scoped DI container to handler arguments
route.handler = wrap_handler(route.handler, container)
```

---

## Code Example: Registry Bootstrap

```python
from aquilia.aquilary import Aquilary
from aquilia.config import ConfigLoader

# 1. Load config
config = ConfigLoader.load("production.json")

# 2. Compile static phase registry
registry_meta = Aquilary.from_manifests(
    manifests=[
        "modules/auth/manifest.py",
        "modules/users/manifest.py",
        "modules/billing/manifest.py"
    ],
    config=config,
    mode="prod"
)

print(f"Registry fingerprint generated: {registry_meta.fingerprint}")

# 3. Export frozen manifest for reproducible deploys
registry_meta.export_manifest("dist/registry.json")

# 4. Bootstrap runtime compilation phase at server startup
runtime_registry = registry_meta.build_runtime()
runtime_registry.perform_autodiscovery()
runtime_registry.compile_routes()
```
