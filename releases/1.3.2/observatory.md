# Specula Observatory UI & Integration

The Specula Observatory is a built-in interactive dashboard served natively by Aquilia at `/specula`. It provides a CDN-free developer sandbox that works entirely offline, inline-cached, and features hot-reload awareness.

## Workspace Integration

Specula is registered at the workspace level inside `workspace.py`. You configure it using the `Integration.specula(...)` builder method or by importing and instantiating `SpeculaIntegration` directly:

```python
# workspace.py
from aquilia.workspace import Workspace
from aquilia.integrations import Integration, SpeculaIntegration

workspace = (
    Workspace("user-portal")
    
    # Style A: Fluent Integration helper
    .integrate(Integration.specula(
        title="User Portal API",
        version="1.4.0",
        ui_theme="dark"
    ))
    
    # Style B: Direct Instantiation (provides static checks and autocomplete)
    # .integrate(SpeculaIntegration(
    #     title="User Portal API",
    #     version="1.4.0",
    #     ui_theme="dark"
    # ))
)
```

---

## Configuration Reference (`SpeculaConfig`)

When you configure Specula, your parameters map to the `SpeculaConfig` dataclass. The primary settings available are:

| Parameter | Type | Default | Description |
| :--- | :--- | :--- | :--- |
| **Info / Branding** | | | |
| `title` | `str` | `"Aquilia API"` | Name of the API, visible in the UI header and spec exports. |
| `version` | `str` | `"1.0.0"` | The current API release version. |
| `description` | `str` | `""` | Detailed description of the API. |
| `ui_theme` | `str` | `"auto"` | `"auto"` (matches system preferences), `"light"`, or `"dark"`. |
| `ui_primary_color`| `str` | `"#22c55e"` | Hex code for branding the main interface buttons and tags. |
| **URL Paths** | | | |
| `ui_path` | `str` | `"/specula"` | Browser path to view the Observatory HTML dashboard. |
| `json_path` | `str` | `"/specula/spec.json"`| JSON endpoint serving the raw OpenAPI 3.1.0 spec. |
| `yaml_path` | `str` | `"/specula/spec.yaml"`| YAML endpoint serving the raw OpenAPI 3.1.0 spec. |
| `stream_path` | `str` | `"/specula/stream"`| SSE stream pushing route updates to the UI. |
| `mock_path` | `str` | `"/specula/mock"` | Endpoint path for the mock server router. |
| **Feature Toggles** | | | |
| `enabled` | `bool` | `True` | Master toggle to enable or disable Specula routes. |
| `include_internal`| `bool` | `False` | Whether routes matching `/_*` are included in the spec. |
| `detect_security` | `bool` | `True` | Scan route guards and decorators to construct security schemes. |
| `mock_server_enabled`| `bool` | `False` | Set `True` to enable schema-synthesized mock responses. |
| `spec_cache_ttl` | `int` | `60` | In-memory cache duration (in seconds) for compiled spec payloads. |

---

## Hot-Reloading SSE Stream (`/specula/stream`)

During development, Aquilia runs with file watchers. When you modify controller code, the worker process reloads. 

Specula exposes a native ASGI Server-Sent Events (SSE) stream endpoint at `/specula/stream`. When the dashboard is loaded in a browser, it subscribes to this stream. When a reload happens, the server pushes an invalidation event down the pipe:

```json
{"event": "update", "data": {"status": "invalidated", "version": "2.0.0"}}
```

The Observatory frontend listens to this event and immediately fetches the newly compiled specification and routes dynamically, refreshing the client view with zero hard refreshes.

---

## Production Security Locks

By default, the Specula Observatory is fully open. In production environments, you can lock access down to authenticated users with specific roles:

```python
workspace.integrate(Integration.specula(
    title="Corporate Core API",
    docs_auth_required=True,
    docs_roles=["admin", "ops-team"]
))
```

When `docs_auth_required` is enabled, the Specula controller inspects the request context using the configured `AuthMiddleware` pipeline. If the visitor lacks the required roles, they receive a `403 Forbidden` response.
