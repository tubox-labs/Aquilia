# Aquilia Build & Deploy Architecture — V2 Design

> **Status**: Proposed  
> **Author**: Architecture Review  
> **Scope**: `aquilia/build/`, `aquilia/cli/commands/deploy_gen.py`, `aquilia/cli/generators/deployment.py`

---

## Table of Contents

1. [Executive Summary](#1-executive-summary)
2. [Current State Analysis](#2-current-state-analysis)
3. [Proposed Architecture](#3-proposed-architecture)
4. [Build System V2](#4-build-system-v2)
5. [Deploy System V2](#5-deploy-system-v2)
6. [Integration Points](#6-integration-points)
7. [Migration Path](#7-migration-path)

---

## 1. Executive Summary

The Aquilia build system compiles workspace modules into verified Crous binary
artifacts through a 6-phase pipeline. The deploy system generates production
infrastructure files (Docker, K8s, Compose, Nginx, CI/CD, monitoring) via
introspection and templating. Both systems work but have architectural gaps:
redundant validation paths, fragile regex discovery, no incremental builds,
and no formal contract between build → deploy.

This document proposes a unified Build-Deploy pipeline with clear phase
boundaries, a dependency graph, and a shared artifact manifest.

---

## 2. Current State Analysis

### 2.1 Build Pipeline (Today)

```
workspace.py + modules/*/manifest.py
          │
          ▼
┌─────────────────────────────────────────────────────┐
│  AquiliaBuildPipeline.execute()                      │
│                                                      │
│  Phase 1: Discovery     Regex-parse workspace.py     │
│              │          importlib.exec each manifest  │
│              ▼                                        │
│  Phase 2: Validation    RegistryValidator (manifests) │
│              │          + empty ConfigLoader()  ← BUG │
│              ▼                                        │
│  Phase 3: Static Check  ast.parse all .py files       │
│              │          + duplicate route check        │
│              ▼                                        │
│  Phase 4: Compilation   Dict payloads × 5 artifacts   │
│              │                                        │
│  Phase 5: Bundling      CrousBundler → .crous binary  │
│              │          SHA-256 per artifact           │
│              ▼                                        │
│  Phase 6: Fingerprint   Combined hash → BuildResult   │
└─────────────────────────────────────────────────────┘
          │
          ▼
     build/*.crous + bundle.crous + build_output.txt
```

### 2.2 Deploy Pipeline (Today)

```
aq deploy (interactive wizard / sub-commands)
          │
          ▼
┌─────────────────────────────────────────────────────┐
│  WorkspaceIntrospector.introspect()                  │
│    Regex-parse workspace.py, pyproject.toml,         │
│    config/prod.yaml, scan modules/                   │
│              │                                        │
│              ▼                                        │
│  9 Generators (independent, stateless):               │
│    Dockerfile, Compose, K8s, Nginx, CI,              │
│    Prometheus, Grafana, Env, Makefile                 │
│              │                                        │
│              ▼                                        │
│  Execution Helpers:                                   │
│    docker build, compose up, kubectl apply -k,       │
│    compose audit, monitoring up                      │
└─────────────────────────────────────────────────────┘
          │
          ▼
     Generated files written to workspace root
```

### 2.3 Identified Issues

| # | Category | Issue | Severity |
|---|----------|-------|----------|
| 1 | **Correctness** | `_phase_validation` creates empty `ConfigLoader()` — always triggers false-positive warning for config namespace | ✅ Fixed |
| 2 | **Redundancy** | Route conflict detection runs in both Phase 2 (validator) and Phase 3 (checker) | Medium |
| 3 | **Fragility** | Discovery uses regex, not AST — breaks on multiline, f-strings, variables | High |
| 4 | **Dead Code** | `BuildResolver` Strategy 2 reads `bundle.manifest.json` which is never written | Low |
| 5 | **Legacy** | Two compilation systems: `AquiliaBuildPipeline` (Crous) + `WorkspaceCompiler` (JSON) | Medium |
| 6 | **Missing** | No incremental build — full rebuild every time | Medium |
| 7 | **Missing** | No build-deploy contract — deploy re-introspects from scratch | High |
| 8 | **Missing** | No build cache or artifact registry | Medium |
| 9 | **Integrity** | Digest verification in resolver re-encodes and compares, unreliable due to dict ordering | Medium |
| 10 | **Silent** | Bundling swallows per-artifact errors with broad `except` | Medium |
| 11 | **Shadowing** | Two `deploy` groups registered (MLOps + deploy_gen) | Low |

---

## 3. Proposed Architecture

### 3.1 Layered Design

```
┌─────────────────────────────────────────────────────────────────┐
│                        CLI Layer                                 │
│   aq build    aq compile    aq deploy    aq serve    aq freeze   │
└────────┬──────────┬────────────┬────────────┬────────────┬──────┘
         │          │            │            │            │
         ▼          ▼            │            │            │
┌─────────────────────────┐     │            │            │
│   Build Orchestrator     │     │            │            │
│   (Phased Pipeline)      │     │            │            │
│                          │     │            │            │
│  ┌─────────────────────┐ │     │            │            │
│  │ Phase 1: Discovery   │ │     │            │            │
│  │   AST-based scanner  │ │     │            │            │
│  └──────────┬──────────┘ │     │            │            │
│  ┌──────────▼──────────┐ │     │            │            │
│  │ Phase 2: Validation  │ │     │            │            │
│  │   RegistryValidator  │ │     │            │            │
│  │   + Seeded Config    │ │     │            │            │
│  └──────────┬──────────┘ │     │            │            │
│  ┌──────────▼──────────┐ │     │            │            │
│  │ Phase 3: Analysis    │ │     │            │            │
│  │   StaticChecker      │ │     │            │            │
│  │   (no route dup)     │ │     │            │            │
│  └──────────┬──────────┘ │     │            │            │
│  ┌──────────▼──────────┐ │     │            │            │
│  │ Phase 4: Compile     │ │     │            │            │
│  │   Artifact payloads  │ │     │            │            │
│  └──────────┬──────────┘ │     │            │            │
│  ┌──────────▼──────────┐ │     │            │            │
│  │ Phase 5: Bundle      │ │     │            │            │
│  │   Crous binary       │ │     │            │            │
│  │   + BuildManifest    │ │     │            │            │
│  └──────────┬──────────┘ │     │            │            │
│             ▼            │     │            │            │
│       BuildResult        │     │            │            │
│       + BuildManifest    │─────┼────────────┼────────────┘
│         (shared contract)│     │            │
└─────────────────────────┘     │            │
              │                  │            │
              ▼                  ▼            ▼
┌─────────────────────────────────────────────────────┐
│              Deploy Orchestrator                     │
│                                                      │
│  Input: BuildManifest (from build) OR                │
│         WorkspaceIntrospector (standalone)            │
│                                                      │
│  ┌────────────────────────────────────────────────┐  │
│  │  DeployContext (unified)                        │  │
│  │    workspace_name, modules[], dependencies{},   │  │
│  │    features{}, server_config{}, fingerprint     │  │
│  └────────────────────┬───────────────────────────┘  │
│                       │                               │
│  ┌────────────────────▼───────────────────────────┐  │
│  │  Generators (stateless, context-driven)         │  │
│  │    Dockerfile · Compose · K8s · Nginx · CI      │  │
│  │    Prometheus · Grafana · Env · Makefile         │  │
│  └────────────────────┬───────────────────────────┘  │
│                       │                               │
│  ┌────────────────────▼───────────────────────────┐  │
│  │  Executor (optional)                            │  │
│  │    docker build · compose up · kubectl apply    │  │
│  │    health checks · rollback on failure          │  │
│  └────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────┘
```

### 3.2 Core Principles

1. **Single Source of Truth**: Build produces a `BuildManifest` that deploy consumes. No re-introspection.
2. **Phase Isolation**: Each build phase has one responsibility. No cross-phase side effects.
3. **Fail Fast, Fail Loud**: Errors propagate immediately. No silent swallowing.
4. **Deterministic**: Same inputs → same outputs → same fingerprint.
5. **Incremental Ready**: Each phase can detect "no change" and skip.
6. **Strict by Default**: Production mode treats all warnings as errors.

---

## 4. Build System V2

### 4.1 Phase Responsibilities (Refined)

| Phase | Name | Input | Output | Change from V1 |
|-------|------|-------|--------|-----------------|
| 1 | **Discovery** | `workspace.py`, `modules/*/manifest.py` | `WorkspaceGraph` | AST-based instead of regex |
| 2 | **Validation** | `WorkspaceGraph` + seeded `ConfigLoader` | `ValidationReport` | Config seeded with app namespaces |
| 3 | **Analysis** | `modules/**/*.py` | `CheckResult` | Remove redundant route check |
| 4 | **Compilation** | `WorkspaceGraph` | `CompiledArtifacts` | No change |
| 5 | **Bundling** | `CompiledArtifacts` | `BundleManifest` + `.crous` files | Error propagation, no silent skip |
| 6 | **Manifest** | `BundleManifest` | `BuildManifest` (JSON) | NEW: Written to `build/manifest.json` |

### 4.2 WorkspaceGraph (New Data Structure)

```python
@dataclass
class WorkspaceGraph:
    """Complete workspace metadata extracted during discovery."""
    name: str                              # Workspace name
    version: str                           # Workspace version
    description: str                       # Workspace description
    modules: Dict[str, ModuleNode]         # module_name → ModuleNode
    dependency_edges: List[Tuple[str,str]] # (from, to) dependency pairs
    config_path: Optional[Path]            # config/ directory if exists

@dataclass
class ModuleNode:
    """Single module's metadata from its manifest."""
    name: str
    version: str
    manifest_path: Path
    manifest_obj: Any                      # The loaded AppManifest
    controllers: List[str]                 # Import paths
    services: List[str]                    # Import paths
    route_prefix: str
    depends_on: List[str]
    fault_domain: str
```

### 4.3 BuildManifest (Build → Deploy Contract)

```python
@dataclass
class BuildManifest:
    """
    Build output manifest — the contract between build and deploy.
    
    Written to build/manifest.json after every successful build.
    Consumed by the deploy system to avoid re-introspection.
    """
    schema_version: str = "2.0"
    workspace_name: str = ""
    workspace_version: str = ""
    build_mode: str = "dev"
    build_fingerprint: str = ""
    build_timestamp: str = ""           # ISO 8601
    
    # Module inventory
    modules: List[ModuleManifestEntry]   # name, version, controllers, services
    
    # Detected features (for deploy generators)
    features: Dict[str, bool]           # db, cache, sessions, websockets, etc.
    
    # Server configuration
    server: ServerConfig                 # host, port, workers, etc.
    
    # Dependency graph
    dependency_graph: Dict[str, List[str]]  # module → depends_on[]
    
    # Artifacts
    artifacts: List[ArtifactEntry]      # name, kind, size, digest
    bundle_path: str                    # Relative path to bundle.crous
```

### 4.4 Discovery Phase: AST Migration

Replace regex-based discovery with `ast.parse`:

```python
def _discover_workspace_ast(self, ws_path: Path) -> WorkspaceGraph:
    """
    AST-based workspace discovery.
    
    Parses workspace.py as an AST and walks the tree for:
    - Workspace("name", version="x.y.z", ...) calls
    - Module("name") calls  
    - Integration.xyz() calls
    
    This is safe (no code execution) and handles:
    - Multi-line calls
    - Variable references (warns but continues)
    - Comments and decorators
    """
    tree = ast.parse(ws_path.read_text())
    
    for node in ast.walk(tree):
        if isinstance(node, ast.Call):
            func_name = _resolve_call_name(node)
            if func_name == "Workspace":
                # Extract name, version, description from args/kwargs
                ...
            elif func_name == "Module":
                # Extract module name from first positional arg
                ...
```

### 4.5 Incremental Build Support

```
build/
├── .build-cache/
│   ├── discovery.hash       # SHA-256 of workspace.py + all manifest.py
│   ├── sources.hash         # SHA-256 of all modules/**/*.py
│   └── config.hash          # SHA-256 of config/*.yaml
├── manifest.json            # BuildManifest (JSON)
├── bundle.crous             # Consolidated binary
├── *.crous                  # Per-artifact binaries
└── build_output.txt         # Timestamped log
```

**Skip logic per phase:**

| Phase | Skip Condition |
|-------|----------------|
| Discovery | `discovery.hash` unchanged |
| Validation | Discovery skipped AND no config changes |
| Analysis | `sources.hash` unchanged |
| Compilation | Discovery skipped (manifest data unchanged) |
| Bundling | Compilation skipped |
| Manifest | Bundling skipped |

---

## 5. Deploy System V2

### 5.1 DeployContext (Unified Input)

```python
@dataclass  
class DeployContext:
    """
    Everything generators need to produce deployment files.
    
    Can be populated from:
    1. BuildManifest (preferred — uses compiled build data)
    2. WorkspaceIntrospector (fallback — live scanning)
    """
    # Identity
    workspace_name: str
    workspace_version: str
    build_fingerprint: Optional[str]
    
    # Modules
    modules: List[str]
    module_count: int
    controller_count: int
    service_count: int
    
    # Ecosystem detection
    has_db: bool
    db_driver: str                       # "postgresql", "sqlite", "mysql"
    has_cache: bool
    has_sessions: bool
    has_websockets: bool
    has_mlops: bool
    has_mail: bool
    has_auth: bool
    has_templates: bool
    has_static: bool
    has_migrations: bool
    has_faults: bool
    has_effects: bool
    has_cors: bool
    has_csrf: bool
    has_tracing: bool
    has_metrics: bool
    
    # Server config
    python_version: str
    host: str
    port: int
    workers: int
    
    # Filesystem awareness
    has_dockerfile: bool
    has_k8s_dir: bool
    has_compose: bool
    has_nginx_conf: bool
    
    @classmethod
    def from_build_manifest(cls, manifest: BuildManifest) -> "DeployContext":
        """Create from a BuildManifest (post-build)."""
        ...
    
    @classmethod
    def from_introspection(cls, workspace_root: Path) -> "DeployContext":
        """Create from live workspace scanning (no build required)."""
        introspector = WorkspaceIntrospector(str(workspace_root))
        ctx = introspector.introspect()
        ...
```

### 5.2 Generator Interface

```python
class DeployGenerator(Protocol):
    """Protocol for all deployment generators."""
    
    name: str                            # "dockerfile", "compose", etc.
    description: str                     # Human-readable description
    output_files: List[str]              # Relative paths of generated files
    
    def generate(self, context: DeployContext, options: Dict) -> Dict[str, str]:
        """
        Generate deployment files.
        
        Returns:
            Dict of relative_path → file_content
        """
        ...
    
    def validate(self, context: DeployContext) -> List[str]:
        """
        Pre-flight validation.
        
        Returns list of warnings (empty = OK).
        """
        ...
```

### 5.3 Execution Engine

```python
class DeployExecutor:
    """
    Orchestrates post-generation execution steps.
    
    Responsibilities:
    - Pre-flight checks (command availability, cluster reachability)
    - Ordered execution with dependency awareness
    - Health checks after each step
    - Summary reporting with skip/pass/fail counts
    - Rollback hints on failure
    """
    
    steps: List[ExecutionStep] = [
        ExecutionStep("docker_build",  requires=["docker"],     depends_on=[]),
        ExecutionStep("compose_up",    requires=["docker"],     depends_on=["docker_build"]),
        ExecutionStep("k8s_apply",     requires=["kubectl"],    depends_on=["docker_build"]),
        ExecutionStep("monitoring_up", requires=["docker"],     depends_on=["compose_up"]),
        ExecutionStep("compose_audit", requires=["docker"],     depends_on=["compose_up"]),
    ]
```

### 5.4 Deploy File Structure

```
project/
├── Dockerfile                # Multi-stage, BuildKit-optimized
├── .dockerignore             # Auto-generated exclusions
├── docker-compose.yml        # Services + profiles (monitoring, proxy, mlops)
├── k8s/
│   ├── kustomization.yaml    # Kustomize overlay
│   ├── namespace.yaml
│   ├── deployment.yaml
│   ├── service.yaml
│   ├── ingress.yaml
│   ├── hpa.yaml
│   ├── pdb.yaml
│   ├── network-policy.yaml
│   ├── configmap.yaml
│   ├── secret.yaml
│   └── service-account.yaml
├── nginx/
│   └── nginx.conf            # Reverse proxy + security headers
├── .github/workflows/
│   └── ci.yml                # CI/CD pipeline
├── monitoring/
│   ├── prometheus.yml
│   └── grafana/
│       ├── datasources.yml
│       └── dashboards/
│           └── aquilia.json
├── .env.example              # Environment template
└── Makefile                  # Developer shortcuts
```

---

## 6. Integration Points

### 6.1 Build → Deploy Flow

```
aq build --mode=prod
    │
    ▼
build/manifest.json  ←── BuildManifest (JSON)
    │
    ▼
aq deploy
    │
    ├── Detects build/manifest.json exists
    │   → DeployContext.from_build_manifest()
    │   → Uses exact module list, features, fingerprint
    │
    ├── OR no manifest.json
    │   → DeployContext.from_introspection()
    │   → Live scan (current behavior)
    │
    ▼
Generate files with exact context
    │
    ▼
Execute (optional)
```

### 6.2 Build → Serve Flow

```
aq build --mode=prod
    │
    ▼
build/bundle.crous + build/manifest.json
    │
    ▼
aq serve --build=build/
    │
    ├── BuildResolver.resolve("build/")
    │   → Load bundle.crous
    │   → Verify fingerprint
    │
    ├── BuildResult.create_registry()
    │   → AquilaryRegistry (ready-to-use)
    │
    ▼
Server boots from compiled state (no manifest parsing)
```

### 6.3 Build → CI Flow

```
# CI Pipeline
aq build --mode=prod --check-only    # Validate only, no artifacts
    │
    ▼ (exit 0 = pass, exit 1 = fail)

aq build --mode=prod                  # Full build with fingerprint
    │
    ▼
aq freeze --sign                      # Immutable signed artifacts
    │
    ▼
aq deploy ci                          # Generate CI workflow file
```

---

## 7. Migration Path

### Phase 1: Immediate Fixes (Current Sprint)

- [x] Seed `ConfigLoader` with app namespaces in `_phase_validation()` 
- [x] Remove duplicate route conflict check from `StaticChecker`
- [x] Propagate bundling errors instead of silently skipping
- [x] Write `build/manifest.json` after successful build

### Phase 2: Discovery Hardening (Next Sprint)

- [x] Migrate workspace discovery from regex to `ast.parse`
- [x] Add AST-based feature detection as alternative to regex
- [x] Keep regex fallback for backward compat, prefer AST

### Phase 3: Build-Deploy Contract (Future)

- [x] Define `BuildManifest` dataclass
- [x] Deploy reads `BuildManifest` when available
- [x] `DeployContext.from_build_manifest()` implementation
- [x] Deprecate duplicate introspection when build exists

### Phase 4: Incremental Builds (Future)

- [x] Content-hash cache per phase
- [x] Skip phases when inputs unchanged
- [x] `--force` flag to bypass cache

### Phase 5: Legacy Cleanup (Future)

- [x] Remove `WorkspaceCompiler` (JSON legacy)
- [x] Remove `BuildResolver` Strategy 2 (dead code)
- [x] Consolidate Phase 6 (Fingerprint) into Phase 5 (Bundling)
- [x] Remove redundant MLOps deploy group or namespace it clearly

### Phase 6: Build-First Deploy (React/Vite/Next.js-style)

- [x] Build gate: `_ensure_production_build()` checks for `build/manifest.json` + `build/bundle.crous`
- [x] Staleness detection: `_is_build_stale()` compares source mtimes against build timestamp
- [x] Auto-build: prompt user to `aq build --mode=prod` before deploy (interactive + auto with `-y`)
- [x] `--skip-build-check` escape hatch for dev-mode / live introspection
- [x] Build gate enforced on all 9 subcommands + interactive wizard
- [x] Deploy context shows source (build manifest vs live introspection)
- [x] Comprehensive test suite (14 tests) for build gate logic

---

*This document is a living architecture reference. Update it as phases are implemented.*
