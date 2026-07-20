# Migration Guide: v1.3.1 to v1.3.2

Aquilia v1.3.2 introduces **Specula** (replacing the legacy OpenAPI generator) and rewrites the dependency-injection subsystem while keeping public core APIs backward compatible. This guide covers the deprecations, configuration changes, and migration steps for both subsystems.

---

## Part A: OpenAPI to Specula Migration

Aquilia v1.3.2 deprecates and removes the old static OpenAPI/Swagger engine.

### 1. Configuration & Integration Upgrades

The old `OpenAPIIntegration` has been replaced by `SpeculaIntegration`. In your `workspace.py`, update your registrations:

#### Legacy Style (Removed)
```python
# Replaced by Specula
workspace.integrate(Integration.openapi(
    title="Store API",
    docs_path="/apidocs",
    swagger_ui_theme="dark"
))
```

#### New Style (Active)
```python
from aquilia.integrations import SpeculaIntegration

# Option A: Direct class registration
workspace.integrate(SpeculaIntegration(
    title="Store API",
    ui_path="/apidocs",
    ui_theme="dark"
))

# Option B: Fluent helper
# workspace.integrate(Integration.specula(
#     title="Store API",
#     ui_path="/apidocs",
#     ui_theme="dark"
# ))
```

#### Parameter Mapping Table

| Legacy OpenAPI Option | New Specula Option | Notes |
| :--- | :--- | :--- |
| `docs_path` | `ui_path` | Default changes from `/docs` to `/specula`. |
| `openapi_json_path` | `json_path` | Default changes from `/openapi.json` to `/specula/spec.json`. |
| `redoc_path` | (Removed) | ReDoc is deprecated. Use the unified Specula dashboard. |
| `swagger_ui_theme` | `ui_theme` | Values: `"auto"`, `"light"`, `"dark"`. |
| `swagger_ui_config` | (Removed) | Replaced by direct dashboard configuration. |

---

### 2. Replaced Imports & Engines

If you manually generated specs, update your imports and instantiation:

```python
# --- Legacy Imports (Removed) ---
# from aquilia.controller.openapi import OpenAPIConfig, OpenAPIGenerator
# config = OpenAPIConfig(title="API")
# spec = OpenAPIGenerator(config=config).generate(router)

# --- New Imports (Active) ---
from aquilia.specula.config import SpeculaConfig
from aquilia.specula.schema.builder import SpeculaBuilder

config = SpeculaConfig(title="API")
spec = SpeculaBuilder(config=config).build(router)
```

---

### 3. Redirects & Endpoint Updates

The automatic redirects mapping legacy paths are no longer registered. Update links:

* **Swagger UI Docs**: Old path `/docs` is replaced by `/specula`.
* **ReDoc Docs**: Old path `/redoc` is deprecated. Use the unified `/specula` dashboard.
* **JSON Specification**: Old path `/openapi.json` is replaced by `/specula/spec.json`.
* **YAML Specification**: Specula now supports rendering YAML natively at `/specula/spec.yaml`.

---

## Part B: Dependency Injection Subsystem Migration

### 4. Move DI Flags into the `di` Config Block

The DI subsystem previously read loose environment flags (e.g. strict-scope enforcement) via `os.environ`. These are replaced by the typed `DISettings` object, configured through a `di` block in `workspace.py`.

#### Before (v1.3.1) — environment flags

```bash
export AQUILIA_DI_STRICT_SCOPES=1
```

#### After (v1.3.2) — typed config

```python
from aquilia import AquilaConfig

class ProdEnv(BaseEnv):
    class di(AquilaConfig.DI):
        scope_enforcement   = "raise"   # was AQUILIA_DI_STRICT_SCOPES=1
        parallel_resolution = True
        strict_service_registration = True
```

Invalid values now fail fast at boot with `DIConfigFault` instead of being silently ignored.

---

### 5. `ServiceScope` Enum — Deprecated

The `ServiceScope` Enum is deprecated in favor of plain string literals. Accessing any member (`ServiceScope.SINGLETON`) or calling the Enum emits a `DeprecationWarning` and will be removed in a future version.

#### Before:

```python
from aquilia.di import ServiceScope

@service(scope=ServiceScope.SINGLETON)
class Config: ...
```

#### After:

```python
@service(scope="singleton")   # canonical type hint: ServiceScopeLiteral
class Config: ...
```

Replace `ServiceScope.SINGLETON` → `"singleton"`, `.APP` → `"app"`, `.REQUEST` → `"request"`, `.TRANSIENT` → `"transient"`, `.POOLED` → `"pooled"`, `.EPHEMERAL` → `"ephemeral"`. String literals skip import-time namespace scanning and runtime attribute lookups.

---

### 6. `clear_request_container()` — Deprecated

`clear_request_container()` is nesting-unsafe (it hard-resets the request container to `None`) and now emits a `DeprecationWarning`. `set_request_container()` and `RequestCtx.set_current()` now return a `Token`.

#### Before:

```python
from aquilia.di import set_request_container, clear_request_container

set_request_container(container)
try:
    ...
finally:
    clear_request_container()
```

#### After:

```python
from aquilia.di import set_request_container, reset_request_container, request_container_scope

# Option A — capture and reset the token (nesting-safe)
token = set_request_container(container)
try:
    ...
finally:
    reset_request_container(token)

# Option B — the context manager (preferred)
with request_container_scope(container):
    ...
```

---

### 7. `ModuleContainer` — Removed

`ModuleContainer` has been removed. Cross-app resolution now uses link-based `Container.add_dependency_link()` instead of nested module containers. This is wired automatically by the runtime from each manifest's `depends_on` — no code change is required unless you instantiated `ModuleContainer` directly.

If you declared cross-app dependencies, ensure they are listed in `depends_on`:

```python
manifest = AppManifest(
    name="billing",
    depends_on=["auth"],   # makes auth-owned providers resolvable in billing
    services=["modules.billing.services:InvoiceService"],
)
```

An undeclared cross-app dependency raises `CrossAppDependencyError` at boot.

---

### 8. Behavioral Changes to Note

These require no code change but alter runtime behavior:

* **Unified engine** — inline `Dep()` dependencies and constructor-injected services now share one deduplicated resolution graph. `RequestDAG` remains as a thin shim over `container.resolve_dep()`; its public API is unchanged.
* **Diagnostics are opt-in** — resolution events (`RESOLUTION_START/SUCCESS/FAILURE`) are emitted only when `diagnostics_enabled` is on. Turn it on in `DevEnv` to trace resolution.
* **Provider shadowing** — a child container may now shadow a provider inherited from its parent. Only a genuine local re-registration of the same token+tag raises `PROVIDER_ALREADY_REGISTERED`.
* **Structured faults** — the DI layer raises `DIFault` subclasses (with stable codes) rather than bare `ValueError`s. If you catch DI errors, catch `DIError` (or a specific subclass) instead of `ValueError`.
* **Sync resolution in a running loop** — `Container.resolve()` and lazy proxies raise `DIResolutionFault` if called from inside a running event loop. In async code, always `await resolve_async()`.

---

### 9. New APIs Worth Adopting

| API | Use it for |
|---|---|
| `DISettings` / `configure_di` | Typed, validated container configuration. |
| `intercept()` / `ProviderInterceptor` | Around-advice on provider instantiation (timing, tracing). |
| `DIPlugin` / `register_plugin` | Auto-registering providers and registry-build hooks. |
| `@service(when=...)` / `@conditional` | Environment/feature-gated provider registration. |
| `Container.replace_provider` | Production-safe atomic provider hot-swap. |
| `Container.create_child` | Per-tenant / multi-level hierarchical containers. |
