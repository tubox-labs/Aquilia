from aquilia import Integration, Module, Workspace
from aquilia.integrations import AdminIntegration, AdminModules

workspace = (
    Workspace("admin-dashboard-app", version="1.0.0", description="Admin operations and permissions reference")
    .runtime(mode="dev", host="127.0.0.1", port=8061, reload=True)
    .module(Module("adminops", version="1.0.0").route_prefix("/adminops").tags("admin", "audit"))
    .integrate(AdminIntegration(site_title="Operations Admin", modules=AdminModules(audit=True, monitoring=True, testing=True)))
    .integrate(Integration.di(auto_wire=True, manifest_validation=True))
    .integrate(Integration.routing(strict_matching=True))
    .integrate(Integration.fault_handling(default_strategy="propagate"))
    .security(cors_enabled=True, csrf_protection=True, helmet_enabled=True)
)
