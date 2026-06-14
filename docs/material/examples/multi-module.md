# Multi-Module Native App

The Multi-Module Native App is the most comprehensive example — a production-shaped
commerce workspace demonstrating how six Aquilia modules compose in a single runtime
with typed integrations for every major subsystem.

---

## What It Demonstrates

- Six modules composing in one workspace: `accounts`, `catalog`, `orders`, `notifications`, `realtime`, `operations`
- Cross-module imports and exports via `Module.imports` and `AppManifest.exports`
- Typed integration dataclasses from `aquilia.integrations`
- Database (`sqlite://`), tasks (`memory`, 4 workers), storage (`local`), mail (`ConsoleProvider`), templates (`memory`, sandboxed)
- OpenAPI generation, versioning, admin, DI, routing, fault handling, cache, i18n, sessions, security, and telemetry
- Socket controllers with room fanout
- Task-backed mail notification workflows
- Thin controllers, stateful services, module boundary discipline

## Key Files

| File | Purpose |
| ---- | ------- |
| `workspace.py` | Orchestrates 6 modules with 15+ integrations |
| `modules/accounts/` | Registration, login, profile - same patterns as the Auth example |
| `modules/catalog/` | Product catalog with blueprint validation |
| `modules/orders/` | Order creation/status — imports `accounts` and `catalog` |
| `modules/notifications/` | Task-backed welcome emails — imports `accounts` |
| `modules/realtime/` | Socket controller for order events — imports `accounts` and `orders` |
| `modules/operations/` | Health, admin, and operational endpoints |
| `templates/` | Jinja2 templates for mail and admin |
| `locales/` | I18n catalog files for `en`, `es`, `fr` |

## Module Dependency Graph

```
accounts ──┐
           ├──→ orders ──→ realtime
catalog ───┘       │
                   └──→ notifications
```

Declared in workspace.py:

```python
workspace.module(Module("accounts", version="1.0.0").route_prefix("/accounts"))
workspace.module(Module("catalog", version="1.0.0").route_prefix("/catalog"))
workspace.module(Module("orders", version="1.0.0").route_prefix("/orders").imports("accounts", "catalog"))
workspace.module(Module("notifications", version="1.0.0").route_prefix("/notifications").imports("accounts"))
workspace.module(Module("realtime", version="1.0.0").route_prefix("/realtime").imports("accounts", "orders"))
workspace.module(Module("operations", version="1.0.0").route_prefix("/ops"))
```

## Full Workspace Configuration

```python
from aquilia import Module, Workspace
from aquilia.integrations import AdminIntegration, AdminModules, CacheIntegration, ConsoleProvider, DiIntegration, FaultHandlingIntegration, MailIntegration, OpenAPIIntegration, RoutingIntegration, TemplatesIntegration, VersioningIntegration
from aquilia.sessions import DEFAULT_USER_POLICY

workspace = (
    Workspace("aquilia-native-commerce", version="1.0.0")
    .runtime(mode="dev", host="127.0.0.1", port=8050, reload=True)
    .module(Module("accounts", version="1.0.0").route_prefix("/accounts").tags("auth", "identity"))
    .module(Module("catalog", version="1.0.0").route_prefix("/catalog").tags("products"))
    .module(Module("orders", version="1.0.0").route_prefix("/orders").imports("accounts", "catalog"))
    .module(Module("notifications", version="1.0.0").route_prefix("/notifications").imports("accounts"))
    .module(Module("realtime", version="1.0.0").route_prefix("/realtime").imports("accounts", "orders"))
    .module(Module("operations", version="1.0.0").route_prefix("/ops").tags("admin", "health"))
    .database(url="sqlite:///runtime/app.db", auto_create=True, auto_migrate=False)
    .tasks(num_workers=4, backend="memory", scheduler_tick=15.0)
    .storage(default="local", backends={"local": {"type": "local", "root": "var/uploads"}})
    .integrate(MailIntegration(default_from="noreply@example.test", providers=[ConsoleProvider(name="console")]))
    .integrate(TemplatesIntegration(search_paths=["templates"], cache="memory", sandbox=True))
    .integrate(OpenAPIIntegration(title="Aquilia Native Commerce", version="1.0.0", enabled=True))
    .integrate(VersioningIntegration(default_version="1.0", versions=["1.0"]))
    .integrate(AdminIntegration(site_title="Commerce Admin", modules=AdminModules(audit=True, monitoring=True, storage=True, tasks=True)))
    .integrate(DiIntegration(auto_wire=True))
    .integrate(RoutingIntegration(strict_matching=True))
    .integrate(FaultHandlingIntegration(default_strategy="propagate"))
    .integrate(CacheIntegration(backend="memory", default_ttl=300))
    .i18n(default_locale="en", available_locales=["en", "es", "fr"])
    .sessions(policies=[DEFAULT_USER_POLICY])
    .security(cors_enabled=True, csrf_protection=False, helmet_enabled=True, rate_limiting=True)
    .telemetry(tracing_enabled=False, metrics_enabled=True, logging_enabled=True)
)
```

## Integration Summary

| Integration | Configuration | Effect |
| ----------- | ------------- | ------ |
| `DatabaseIntegration` | `url="sqlite:///runtime/app.db"` | SQLite pool available to all modules |
| `TasksIntegration` | `num_workers=4, backend="memory"` | Background job processing |
| `StorageIntegration` | `default="local", backends={...}` | File storage with local root |
| `MailIntegration` | `ConsoleProvider(name="console")` | Mail writes to console instead of sending |
| `TemplatesIntegration` | `search_paths=["templates"]` | Sandboxed Jinja2 from `templates/` |
| `OpenAPIIntegration` | `enabled=True` | OpenAPI spec at `/openapi.json` |
| `VersioningIntegration` | `default_version="1.0"` | API versioning via `X-API-Version` |
| `AdminIntegration` | `AdminModules(audit=True, ...)` | Admin dashboard with audit/monitoring/storage/tasks |
| `DiIntegration` | `auto_wire=True` | Automatic dependency injection |
| `RoutingIntegration` | `strict_matching=True` | Exact route matching |
| `FaultHandlingIntegration` | `default_strategy="propagate"` | Structured fault propagation |
| `CacheIntegration` | `backend="memory"` | In-memory cache with 300s TTL |
| `.i18n()` | `locales=["en","es","fr"]` | Localization support |
| `.sessions()` | `DEFAULT_USER_POLICY` | Session management |
| `.security()` | `cors/helmet/rate_limiting` | Security middleware |
| `.telemetry()` | `metrics/logging enabled` | Observability |

## Cross-Module Imports

The `orders` module imports `accounts` (for identity lookups) and `catalog` (for product
lookups). This is declared in two places:

**workspace.py** — declares the dependency:
```python
Module("orders", ...).imports("accounts", "catalog")
```

**manifest.py** — exports the types that are available to importers:
```python
manifest = AppManifest(
    name="accounts",
    exports=["Account"],
    ...
)
```

## Running

```bash
cd examples/multi_module_native_app
python -m uvicorn runtime:app --reload --port 8050
```

```bash
# Health check
curl http://127.0.0.1:8050/ops/health

# List products
curl http://127.0.0.1:8050/catalog/products

# OpenAPI spec
curl http://127.0.0.1:8050/openapi.json

# Run tests
python -m pytest examples/multi_module_native_app -q
```

## What You'll Learn

- How to orchestrate multiple modules in a single workspace
- How to declare cross-module dependencies with `Module.imports`
- How to configure all major integrations in one workspace
- How to use typed integration dataclasses from `aquilia.integrations`
- How module boundaries enforce clean code organization
- How to use `AppManifest.exports` to control public module APIs

---

## Provider Render Deploy

The Render deploy example in `examples/provider_render_deploy_app/` demonstrates
provider/deployment configuration using Render dataclasses and dry-run planning
without contacting the Render API:

```python
from aquilia.integrations import RenderIntegration

workspace.integrate(RenderIntegration(service_name="my-app", plan="starter", region="oregon"))
```

The `RenderDeploymentPlanner` service converts integration config into `RenderDeployConfig`
and returns the exact service payload shape consumed by the Render deployer and CLI workflows.

```bash
cd examples/provider_render_deploy_app
python -m uvicorn runtime:app --reload --port 8072
curl -X POST http://127.0.0.1:8072/deployments/render/dry-run
```