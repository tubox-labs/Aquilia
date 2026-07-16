# OpenAPI to Specula Migration Guide

Aquilia v1.3.2 deprecates and removes the old static OpenAPI/Swagger engine. This guide outlines how to migrate your configuration, imports, and endpoints.

---

## 1. Configuration & Integration Upgrades

The old `OpenAPIIntegration` has been replaced by `SpeculaIntegration`. In your `workspace.py`, update your registrations:

### Legacy Style (Removed)
```python
# Replaced by Specula
workspace.integrate(Integration.openapi(
    title="Store API",
    docs_path="/apidocs",
    swagger_ui_theme="dark"
))
```

### New Style (Active)
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

### Parameter Mapping Table

Use this reference table to map configuration options from legacy OpenAPI attributes to Specula attributes:

| Legacy OpenAPI Option | New Specula Option | Notes |
| :--- | :--- | :--- |
| `docs_path` | `ui_path` | Default changes from `/docs` to `/specula`. |
| `openapi_json_path` | `json_path` | Default changes from `/openapi.json` to `/specula/spec.json`. |
| `redoc_path` | (Removed) | ReDoc is deprecated. Use the unified Specula dashboard. |
| `swagger_ui_theme` | `ui_theme` | Values: `"auto"`, `"light"`, `"dark"`. |
| `swagger_ui_config` | (Removed) | Replaced by direct dashboard configuration. |

---

## 2. Replaced Imports & Engines

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

## 3. Redirects & Endpoint Updates

The automatic redirects mapping legacy paths are no longer registered. Update links:

* **Swagger UI Docs**: Old path `/docs` is replaced by `/specula`.
* **ReDoc Docs**: Old path `/redoc` is deprecated. Use the unified `/specula` dashboard.
* **JSON Specification**: Old path `/openapi.json` is replaced by `/specula/spec.json`.
* **YAML Specification**: Specula now supports rendering YAML natively at `/specula/spec.yaml`.
