# Examples

Aquilia ships with 18 runnable example applications that demonstrate every major
subsystem of the framework. Each example is self-contained: a `workspace.py`
declares the orchestration, module directories contain controllers/services/manifests,
and a `runtime.py` boots the ASGI server.

All examples run with a single `uvicorn` command and include pytest suites.

---

## Core API Patterns

| Example | Description |
| ------- | ----------- |
| [**REST API Blueprint**](rest-api.md) | Product catalog REST API with blueprint validation, search, pagination, and soft deletion. Demonstrates `Blueprint` sealing, `Controller` decorators, and structured faults. |
| [**CRUD App**](rest-api.md#crud-app) | Project tracker CRUD with model declaration and repository-style services. Demonstrates create/read/update/archive/restore flows with a production-shaped service boundary. |

## Authentication & Security

| Example | Description |
| ------- | ----------- |
| [**Auth App**](authentication.md) | Registration, login, password verification, JWT token issuance, and guard-protected routes. Demonstrates `AuthManager`, `@authenticated`, `AdminGuard`, and memory-backed identity stores. |
| [**Middleware Security App**](authentication.md#middleware-security-app) | Rate limits, API key extraction, and CSP policy composition. Demonstrates `RateLimitRule`, `CSPPolicy`, `CorsIntegration`, and layered middleware. |

## Real-time & Background Processing

| Example | Description |
| ------- | ----------- |
| [**WebSocket App**](websockets.md) | Chat rooms with connect/disconnect hooks, subscriptions, acknowledgements, and presence tracking. Demonstrates `SocketController`, `@OnConnect`, `@Subscribe`, `@Event`, and `@AckEvent`. |
| [**Background Jobs**](background-jobs.md) | Controller-triggered job dispatch, priority queues, retries, scheduled cleanup, and job status inspection. Demonstrates `@task`, `TaskManager`, `MemoryBackend`, and `every()` scheduler. |

## Administration & Infrastructure

| Example | Description |
| ------- | ----------- |
| [**Admin Dashboard**](admin-dashboard.md) | Admin model registration, role-based permission checks, audit events, and dashboard integration. Demonstrates `AdminIntegration`, `@register`, `ModelAdmin`, and `AdminModules`. |
| [**Cache HTTP Edge**](cache-http.md) | Cache-aside HTTP gateway with memory cache and mock transport. Demonstrates `CacheService`, `MemoryBackend`, `AsyncHTTPClient`, and cache invalidation. |
| [**Multi-Module Native App**](multi-module.md) | Full commerce workspace with auth, sessions, cache, storage, mail, i18n, tasks, WebSockets, templates, OpenAPI, versioning, and admin. Demonstrates cross-module imports/exports and typed integrations. |
| [**Provider Render Deploy**](multi-module.md#provider-render-deploy) | Render provider dry-run deployment. Demonstrates `RenderIntegration`, `RenderDeployConfig`, and payload shape generation for the Render API. |

## Content & Localization

| Example | Description |
| ------- | ----------- |
| [**Storage File Hub**](storage.md) | Multi-backend file hub with metadata, tenant partitioning, and SHA-256 digest tracking. Demonstrates `StorageRegistry`, `MemoryStorage`, and multi-alias configuration. |
| [**Mail Notifications**](mail.md) | Welcome notification pipeline with `EmailMessage` envelopes and file-based delivery. Demonstrates `MailIntegration`, `FileProvider`, and attachment handling. |
| [**I18n Content**](i18n.md) | Localized application copy, `Accept-Language` negotiation, fallback behavior, and plural-aware translations. Demonstrates `I18nService`, `MemoryCatalog`, and `negotiate_locale()`. |
| [**Versioned Public API**](versioning.md) | Header-based API versioning with route-level version decorators and version-neutral routes. Demonstrates `VersioningIntegration`, `@version`, and version-aware service resolution. |

## Data & Rendering

| Example | Description |
| ------- | ----------- |
| [**SQLite Inventory**](sqlite.md) | Native SQLite connection pool, parameterized queries, explicit `IMMEDIATE` transactions, and schema lifecycle. Demonstrates `SqliteService`, `ConnectionPool`, and `TransactionContext`. |
| **Templates Portal** | Server-rendered portal with sandboxed Jinja2 templates, custom globals, filters, and streaming. Demonstrates `TemplateEngine`, `TemplateLoader`, and `SandboxedEnvironment`. |
| **Artifacts Release** | Release artifact creation with integrity verification and signed release tokens. Demonstrates `ArtifactBuilder`, `MemoryArtifactStore`, `Artifact.verify()`, and `dumps()`/`loads()` signing. |
| **MLOps Model Registry** | Model metadata registration, local inference, progressive rollout state, and plugin host registration. Demonstrates `AquiliaModel`, `ModelRegistry`, `RolloutEngine`, and `PluginHost`. |

---

## Running an Example

Every example follows the same pattern:

```bash
cd examples/<example_name>
python -m uvicorn runtime:app --reload --port <port>
```

Each example README documents its specific port and expected behavior.

## Running Tests

```bash
python -m pytest examples/<example_name> -q
```

All examples include a `tests/` directory with full coverage. Tests use the same patterns
shown in the framework test suite: `TestServer`, `TestClient`, and direct service unit tests.

## Example Structure

Every example follows this layout:

```
example_name/
    workspace.py          # Workspace orchestration: modules, integrations, configuration
    runtime.py            # AquiliaRuntime bootstrap → ASGI app
    modules/
        <module>/
            __init__.py
            manifest.py   # AppManifest: controllers, services, models, tasks
            controllers.py
            services.py
            blueprints.py # Optional: request/response validation schemas
            models.py     # Optional: ORM model declarations
            tasks.py      # Optional: background task definitions
            sockets.py    # Optional: WebSocket controllers
    templates/            # Optional: Jinja2 templates
    locales/              # Optional: i18n catalog files
    tests/                # Pytest suites
```

## Production Readiness

These examples use in-memory stores, console/file providers, and development secrets
so they run with zero dependencies. For production deployment:

- Replace in-memory services with database/model-backed repositories
- Use Redis or database-backed cache, sessions, and task queues
- Configure SMTP/SES/SendGrid for mail delivery
- Use S3/GCS/Azure/SFTP for durable storage
- Set signing keys and secrets from environment variables
- Enable rate limiting, CSRF, and CSP security middleware