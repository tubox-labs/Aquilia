# Debugging Guide

Aquilia provides beautiful, information-rich debugging tools that help you diagnose errors in development. In production, debug output is automatically suppressed to prevent sensitive information leaks.

## Debug Page Renderer

The `DebugPageRenderer` (in `aquilia.debug.pages`) generates self-contained HTML pages with no external dependencies. All CSS, JavaScript, and SVG icons are inlined. The theme supports both dark and light modes with a persistent preference saved to `localStorage`.

### Rendering Pages

```python
from aquilia.debug import DebugPageRenderer

renderer = DebugPageRenderer()

# Exception page with traceback
html = renderer.render_exception(exception, request, aquilia_version="1.1.2")

# HTTP error page
html = renderer.render_http_error(404, "Not Found", "The page does not exist")

# Welcome page
html = renderer.render_welcome(aquilia_version="1.1.2", system_info={
    "python_version": "3.12.0",
    "platform": "macOS",
    "debug": True,
})
```

## Exception Pages (Development Mode)

When `debug=True` and `AQUILIA_ENV` is not `prod`/`production`/`staging`, browser clients receive beautiful React-style debug exception pages.

### Features

- **Full traceback** with source code context (7 lines above/below the error)
- **Syntax highlighting** — keywords, strings, comments, and numbers are color-coded
- **Collapsible stack frames** — each frame shows the function, file path, line number, and a badge indicating "App" vs "Lib" code
- **Local variables inspector** — per-frame locals displayed in a table
- **Request info panel** — headers, query params, path params (sensitive values redacted)
- **Copy traceback button** — copies the full Python traceback to clipboard
- **Dark/light theme toggle** with persistent preference

### Production Safety Guard

Even if `debug=True` was accidentally set, the debug page **refuses to render** in production environments. If `AQUILIA_ENV` is `production`, `prod`, or `staging`, the debug page replaces itself with a generic 500 error page:

```
Debug exception page was requested in a PRODUCTION environment.
Refusing to render sensitive debug information.
Set AQUILIA_ENV to 'development' to enable debug pages.
```

### Sensitive Data Redaction

Debug pages automatically redact sensitive data to prevent accidental exposure:

**Headers redacted:**
- `Authorization`
- `Cookie` / `Set-Cookie`
- `X-API-Key`
- `X-Auth-Token`
- `X-CSRF-Token`
- `Proxy-Authorization`
- `X-Forwarded-Access-Token`

**Local variables redacted by name:** Any variable containing `password`, `passwd`, `secret`, `token`, `api_key`, `apikey`, `access_key`, `private_key`, `credential`, `auth`, `ssn`, or `credit_card` in its name is replaced with `[REDACTED]`.

### Environment Detection

```python
from aquilia.debug.pages import _is_production_environment

# Checks AQUILIA_ENV or APP_ENV for "production", "prod", "staging"
if _is_production_environment():
    print("Debug pages suppressed")
```

## HTTP Error Pages

Styled error pages are rendered for all standard HTTP error codes. Each page includes:

- The status code as a colored badge
- A status icon
- Descriptive title and message
- A "Back Home" button
- Theme toggle

```python
from aquilia.debug import render_http_error_page

# 404 page
html = render_http_error_page(404, "Not Found", "The requested resource was not found.")

# 500 page
html = render_http_error_page(500, "Internal Server Error", "An unexpected error occurred.")
```

Error pages are available for: `400`, `401`, `403`, `404`, `405`, `500`, and all other standard status codes.

## Version Error Pages

API versioning errors get a dedicated page with version information:

```python
from aquilia.debug import render_version_error_page

html = render_version_error_page(
    status_code=400,
    error_code="UNSUPPORTED_API_VERSION",
    message="The requested API version is no longer supported",
    detail="Supported versions: v1, v2",
    metadata={"available_versions": ["v1", "v2"]},
    aquilia_version="1.1.2",
)
```

## Welcome Page

When no root route is defined, Aquilia serves a starter welcome page:

```python
from aquilia.debug import render_welcome_page

html = render_welcome_page(
    aquilia_version="1.1.2",
    system_info={
        "python_version": "3.12.0",
        "platform": "macOS",
        "debug": True,
    },
)
```

The welcome page features:

- An animated SVG gyroscope visual with the Aquilia logo
- System information (Python version, platform, debug mode)
- Quick-start command block (`aq add module users`)
- Feature cards highlighting framework capabilities
- Links to documentation and GitHub
- Dark/light theme toggle

---

## `aq doctor` — Workspace Diagnostics

The `aq doctor` command performs comprehensive health checks across every layer of the manifest-first architecture. It runs in 6 phases:

### Phase 1: Environment

```bash
aq doctor
```

Checks:

- Python version (requires >= 3.10)
- Aquilia installation and version
- Sub-package imports: `aquilia.manifest`, `aquilia.aquilary`, `aquilia.config`, `aquilia.server`, `aquilia.di`, `aquilia.faults`, `aquilia.controller`, `aquilia.effects`, `aquilia.blueprints`

### Phase 2: Workspace Structure

- Workspace config file presence (`workspace.py` or `aquilia.py`)
- `modules/` directory existence
- `AquilaConfig` inline configuration in workspace file

### Phase 3: Manifests

- Module discovery from `workspace.py`'s `Module("...")` declarations
- `manifest.py` file presence per module
- `__init__.py` existence warnings
- Controller reference validation — checks that referenced `modules.X.Y:ClassName` files exist
- Service reference validation
- Dependency consistency — cross-module `depends_on` must reference registered modules
- Recommended file warnings — `controllers.py`, `services.py`, `faults.py`

### Phase 4: Aquilary Pipeline

- **Registry validation**: Validates all loaded manifests through `RegistryValidator`
- **Dependency graph**: Builds `DependencyGraph`, checks for cycles, shows topological load order
- **Fingerprint**: Generates a registry fingerprint for change detection

### Phase 5: Integrations

Scans `workspace.py` content for configured integrations:

- Database (driver: SQLite, PostgreSQL, or MySQL)
- Sessions
- Cache
- Auth
- Templates
- Static files
- Security checks: CORS, CSRF protection, security headers, rate limiting

### Phase 6: Deployment

Checks for deployment artifacts:

- `Dockerfile`, `.dockerignore`, `docker-compose.yml`
- `k8s/` Kubernetes manifests
- `.env` file presence
- `.gitignore` presence

### Example Output

```
── Environment ──
  [ok] Python 3.12.3
  [ok] Aquilia 1.1.2 installed
  [ok] Manifest system
  [ok] Aquilary registry
  [ok] Config system

── Workspace ──
  [ok] Workspace file: workspace.py
  [ok] modules/ directory

── Manifests ──
  [ok] 3 module(s) registered: users, products, auth
  [ok] Module 'users' manifest loaded
  [ok] Module 'products' manifest loaded
  [ok] Module 'auth' manifest loaded

── Pipeline ──
  [ok] Registry validation passed
  [ok] No dependency cycles
  [ok] Load order: auth → users → products
  [ok] Registry fingerprint: a1b2c3d4e5f6

── Integrations ──
  [ok] Database configured
  [ok] Database driver: PostgreSQL
  [ok] Sessions configured
  [ok] Auth configured
  [ok] CORS enabled

── Deployment ──
  [ok] Dockerfile (Docker image build)
  [ok] .env file present

  [ok] All checks passed -- workspace is healthy
```

---

## Health Endpoint

Aquilia automatically registers a health check endpoint when the health subsystem is configured. The exact path depends on your configuration.

A typical health endpoint returns:

```json
{
  "status": "healthy",
  "version": "1.1.2",
  "uptime": 3600,
  "checks": {
    "database": "ok",
    "cache": "ok",
    "sessions": "ok"
  }
}
```

---

## `aq inspect` — Route and Component Inspection

The `aq inspect` command displays detailed information about your application:

```bash
# List all registered routes
aq inspect routes

# Show dependency graph
aq inspect deps

# Show DI container registrations
aq inspect di

# Show middleware stack
aq inspect middleware

# Show all manifests
aq inspect manifests
```

## `aq validate` — Configuration Validation

```bash
# Validate the workspace configuration
aq validate

# Validate with detailed output
aq validate --verbose

# Validate a specific manifest
aq validate --manifest users
```

---

## Diagnostic Logging

### Enabling Debug Logging

```python
import logging

# Framework debug logging
logging.getLogger("aquilia").setLevel(logging.DEBUG)

# Specific subsystem
logging.getLogger("aquilia.testing.server").setLevel(logging.DEBUG)
logging.getLogger("aquilia.controller.router").setLevel(logging.DEBUG)
logging.getLogger("aquilia.di").setLevel(logging.DEBUG)
```

### Common Logger Names

| Logger | Purpose |
|--------|---------|
| `aquilia.debug` | Debug page rendering |
| `aquilia.testing.server` | Test server lifecycle |
| `aquilia.testing.cases` | Test case execution |
| `aquilia.controller` | Route matching and dispatch |
| `aquilia.di` | Dependency resolution |
| `aquilia.faults` | Fault engine processing |
| `aquilia.aquilary` | Manifest registry operations |

---

## Common Debugging Scenarios

### Routes Not Matching

1. Run `aq inspect routes` to see all registered routes
2. Check controller `prefix` and decorator paths compose correctly
3. Verify HTTP method matches (GET vs POST)
4. Check module `route_prefix` in `workspace.py`

### DI Resolution Failures

1. Run `aq inspect di` to see all registered providers
2. Check that services are declared in `manifest.py` services list
3. Verify scope compatibility (singleton services can't depend on request-scoped services)
4. Check for circular dependencies with `aq inspect deps`

### Startup Failures

1. Run `aq doctor` for comprehensive diagnostics
2. Check `AQUILIA_ENV` is set correctly
3. Verify all module dependencies are registered
4. Check that `modules/` contains `__init__.py` files

### Middleware Issues

1. Run `aq inspect middleware` to see the stack order
2. Check that middleware classes are listed in `manifest.py`
3. Verify middleware `process()` / `process_response()` method signatures

### Database Connection Issues

1. Check the database URL in your config
2. Verify the driver dependency is installed (`pip install aquilia[postgres]`)
3. For SQLite, check file permissions on the database file
4. Run `aq doctor` to verify database configuration is detected