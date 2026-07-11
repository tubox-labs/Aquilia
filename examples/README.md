# Aquilia Examples

This directory is the practical reference for Aquilia. The examples follow the architecture implemented by the framework:

- `workspace.py` configures runtime, module pointers, integrations, security, sessions, storage, tasks, telemetry, and database settings.
- `modules/<name>/manifest.py` declares module internals through `AppManifest`.
- Controllers use Aquilia decorators such as `@GET`, `@POST`, `@Socket`, `@Event`, and delegate behavior to services.
- `runtime.py` exposes the ASGI `app` by bootstrapping `AquiliaRuntime`.
- Tests are executable from the repository root with `python -m pytest examples -q`.

## Setup

From the repository root:

```bash
python -m pip install -e ".[dev]"
python -m pytest examples -q
```

Run an app starter:

```bash
cd examples/rest_api_contract
python -m uvicorn runtime:app --reload --port 8000
```

Run the subsystem reference suite:

```bash
python -m examples.reference_suite.run_all
```

## App Starters

| Directory | Purpose | Primary APIs |
| --- | --- | --- |
| `rest_api_contract` | Product catalog REST API with validation, search, pagination-style parameters, and soft deletion. | `Workspace`, `Module`, `AppManifest`, `Controller`, `Response`, `Contract`, faults |
| `crud_app` | Project tracker CRUD workflow with a model declaration and repository-style service boundary. | Models, contracts, controllers, database config |
| `auth_app` | Registration, password verification, token issuance, protected profile route, and admin guard route. | `AuthManager`, identity stores, `PasswordHasher`, `TokenManager`, guards |
| `websocket_app` | Chat rooms, connect/disconnect hooks, subscriptions, acknowledgements, and presence inspection. | `SocketController`, `@Socket`, `@Event`, `@Subscribe`, `Connection` |
| `background_jobs` | Controller-triggered jobs, queue metadata, retries, scheduled cleanup, and job status. | `TaskManager`, `@task`, `Priority`, schedules |
| `multi_module_native_app` | Full commerce-shaped workspace composing HTTP, auth, sessions, cache, storage, mail, i18n, tasks, sockets, templates, OpenAPI, versioning, and admin config. | Multi-module manifests, imports/exports, integrations |
| `admin_dashboard_app` | Admin model registration, role permissions, audit-style service events, and dashboard metrics. | `AdminIntegration`, `ModelAdmin`, `@register`, admin permissions |
| `cache_http_edge_app` | Cache-aside HTTP gateway using memory cache and mock transport. | `CacheService`, `MemoryBackend`, `AsyncHTTPClient`, `MockTransport` |
| `storage_filehub_app` | Multi-backend file hub with metadata, tenant paths, and health checks. | `StorageRegistry`, `MemoryStorage`, `MemoryConfig` |
| `mail_notifications_app` | Welcome notification pipeline delivered through the file mail provider. | `EmailMessage`, `MailEnvelope`, `FileProvider` |
| `i18n_content_app` | Localized content, locale negotiation, fallback, and pluralization. | `I18nService`, `I18nConfig`, `MemoryCatalog` |
| `versioned_public_api_app` | Header-versioned API payloads and route version metadata. | `VersionConfig`, `VersionStrategy`, `@version`, `@version_neutral` |
| `sqlite_inventory_app` | Native SQLite pool lifecycle, parameterized queries, and transactions. | `SqliteService`, `SqlitePoolConfig`, `ConnectionPool` |
| `templates_portal_app` | Server-rendered portal with sandboxed templates, filters, globals, and streaming. | `TemplateEngine`, `TemplateLoader`, `TemplateConfig` |
| `middleware_security_app` | Security policy modeling for rate limits, API keys, and CSP. | `RateLimitRule`, `CSPPolicy`, security integrations |
| `artifacts_release_app` | Release artifact creation, integrity checks, signing, and promotion provenance. | `ArtifactBuilder`, `MemoryArtifactStore`, `aquilia.signing` |
| `mlops_model_registry_app` | MLOps model metadata registration, local inference, rollout state, and plugin inventory. | `AquiliaModel`, `ModelRegistry`, `RolloutEngine`, `PluginHost` |
| `provider_render_deploy_app` | Render provider dry-run deployment payload planning. | `RenderIntegration`, `RenderDeployConfig`, `DeployResult` |

## Subsystem References

`reference_suite` contains runnable examples for APIs that are not naturally visible in one app starter: DI, cache, storage, filesystem, sqlite, templates, mail providers, artifacts, signing, versioning, HTTP mock transport, patterns, and fault handling.

## CLI Workflows

See `CLI_WORKFLOWS.md` for command examples derived from `aquilia/cli/__main__.py` and command modules.

## Coverage Reports

- `COVERAGE_REPORT.md` records the pre-implementation audit and missing coverage.
- `MODULE_COVERAGE.md` maps source modules to examples and extension ideas.

## Common Pitfalls

- Run app-local commands from the app directory because `AquiliaRuntime` discovers `workspace.py` and `modules/` relative to the workspace root.
- Prefer `python -m uvicorn runtime:app` or `aq run` inside a starter.
- Keep workspace-level component pointers in `workspace.py`; declare controllers, services, sockets, models, middleware, and tasks in each module's `manifest.py`.
- Memory stores are intentional for local executability. Replace them with configured providers for durable production behavior.
- Provider, cloud, and MLOps examples use dry-run, memory, local, or file-backed execution unless credentials are explicitly required by the real workflow.
