from aquilia import Module, Workspace
from aquilia.integrations import (
    AdminIntegration,
    AdminModules,
    CacheIntegration,
    ConsoleProvider,
    DiIntegration,
    FaultHandlingIntegration,
    MailIntegration,
    OpenAPIIntegration,
    RoutingIntegration,
    TemplatesIntegration,
    VersioningIntegration,
)
from aquilia.sessions import DEFAULT_USER_POLICY

workspace = (
    Workspace("aquilia-native-commerce", version="1.0.0", description="Complete Aquilia-native starter")
    .runtime(mode="dev", host="127.0.0.1", port=8050, reload=True)
    .module(Module("accounts", version="1.0.0").route_prefix("/accounts").tags("auth", "identity"))
    .module(Module("catalog", version="1.0.0").route_prefix("/catalog").tags("products"))
    .module(Module("orders", version="1.0.0").route_prefix("/orders").imports("accounts", "catalog").tags("orders"))
    .module(
        Module("notifications", version="1.0.0")
        .route_prefix("/notifications")
        .imports("accounts")
        .tags("mail", "tasks")
    )
    .module(
        Module("realtime", version="1.0.0").route_prefix("/realtime").imports("accounts", "orders").tags("websocket")
    )
    .module(Module("operations", version="1.0.0").route_prefix("/ops").tags("admin", "health"))
    .database(url="sqlite:///runtime/app.db", auto_create=True, auto_migrate=False)
    .tasks(num_workers=4, backend="memory", scheduler_tick=15.0)
    .storage(default="local", backends={"local": {"type": "local", "root": "var/uploads"}})
    .integrate(MailIntegration(default_from="noreply@example.test", providers=[ConsoleProvider(name="console")]))
    .integrate(TemplatesIntegration(search_paths=["templates"], cache="memory", sandbox=True))
    .integrate(OpenAPIIntegration(title="Aquilia Native Commerce", version="1.0.0", enabled=True))
    .integrate(VersioningIntegration(default_version="1.0", versions=["1.0"]))
    .integrate(
        AdminIntegration(
            site_title="Commerce Admin", modules=AdminModules(audit=True, monitoring=True, storage=True, tasks=True)
        )
    )
    .integrate(DiIntegration(auto_wire=True))
    .integrate(RoutingIntegration(strict_matching=True))
    .integrate(FaultHandlingIntegration(default_strategy="propagate"))
    .integrate(CacheIntegration(backend="memory", default_ttl=300))
    .i18n(default_locale="en", available_locales=["en", "es", "fr"])
    .sessions(policies=[DEFAULT_USER_POLICY])
    .security(cors_enabled=True, csrf_protection=False, helmet_enabled=True, rate_limiting=True)
    .telemetry(tracing_enabled=False, metrics_enabled=True, logging_enabled=True)
)
