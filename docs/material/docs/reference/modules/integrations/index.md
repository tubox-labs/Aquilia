# Integrations Module

> `aquilia.integrations` — Typed integration configuration builders

The Integrations module provides typed dataclass configuration builders for every Aquilia subsystem. Each integration encapsulates the settings needed to wire a subsystem into the application, replacing the legacy `Integration` pattern.

## When to Use

Use the Integrations module when you need:

- Configuring subsystems in `workspace.py`
- Type-safe configuration for database, cache, storage, mail, templates
- Declarative middleware chain configuration
- Enabling optional features (CORS, CSP, rate limiting, etc.)

## Key Integration Builders

| Integration | Configures |
|---|---|
| `DatabaseIntegration` | Database backend, connection pool |
| `AuthIntegration` | Authentication settings |
| `SessionIntegration` | Session store, transport, policy |
| `CacheIntegration` | Cache backend, TTL, policies |
| `TasksIntegration` | Task backend, worker count |
| `StorageIntegration` | Storage backends and configs |
| `MailIntegration` | Mail provider, from address |
| `TemplatesIntegration` | Template directory, caching |
| `AdminIntegration` | Admin dashboard settings |
| `OpenAPIIntegration` | API documentation config |
| `CorsIntegration` | CORS origins, headers |
| `CspIntegration` | Content-Security-Policy |
| `CsrfIntegration` | CSRF token settings |
| `RateLimitIntegration` | Rate limit rules |
| `DiIntegration` | DI auto-wiring |
| `RoutingIntegration` | Route matching options |
| `FaultHandlingIntegration` | Fault recovery strategies |
| `I18nIntegration` | Locale settings |
| `VersioningIntegration` | API version defaults |
| `LoggingIntegration` | Log level, format |
| `StaticFilesIntegration` | Static file serving |
| `PatternsIntegration` | Retry, circuit breaker |
| `SerializersIntegration` | JSON encoder config |
| `RegistryIntegration` | Registry mode |

## Quick Example

```python
# workspace.py
from aquilia import Module, Workspace
from aquilia.integrations import (
    DatabaseIntegration, CacheIntegration, MailIntegration,
    CorsIntegration, SessionIntegration,
)

workspace = Workspace("my-api")
workspace.integrate(
    DatabaseIntegration(
        url="sqlite:///app.db",
        pool_size=5,
    )
)
workspace.integrate(
    CacheIntegration(
        backend="redis",
        redis_url="redis://localhost:6379",
        default_ttl=300,
    )
)
workspace.integrate(
    CorsIntegration(
        origins=["http://localhost:3000"],
        methods=["GET", "POST", "PUT", "DELETE"],
    )
)
workspace.integrate(
    MailIntegration(
        provider="smtp",
        smtp_host="smtp.example.com",
        default_from="noreply@example.com",
    )
)
```

## Import Path

```python
from aquilia.integrations import (
    DatabaseIntegration,
    AuthIntegration,
    SessionIntegration,
    CacheIntegration,
    TasksIntegration,
    StorageIntegration,
    MailIntegration,
    TemplatesIntegration,
    AdminIntegration,
    OpenAPIIntegration,
    CorsIntegration,
    CspIntegration,
    CsrfIntegration,
    RateLimitIntegration,
    DiIntegration,
    RoutingIntegration,
    FaultHandlingIntegration,
    I18nIntegration,
    VersioningIntegration,
    LoggingIntegration,
    StaticFilesIntegration,
    PatternsIntegration,
    SerializersIntegration,
    RegistryIntegration,
)
```

## Related Modules

- [core/server](../core/server.md) — Integrations are consumed during server boot
- [core/manifest](../core/manifest.md) — Integrations complement manifest declarations
- [cache](../cache/index.md) — Cache configuration via `CacheIntegration`
- [storage](../storage/index.md) — Storage configuration via `StorageIntegration`