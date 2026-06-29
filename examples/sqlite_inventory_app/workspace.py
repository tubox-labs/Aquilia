from aquilia import Module, Workspace
from aquilia.integrations import DiIntegration

workspace = (
    Workspace("sqlite-inventory-app", version="1.0.0", description="Native SQLite pool inventory service")
    .runtime(mode="dev", host="127.0.0.1", port=8067, reload=True)
    .module(Module("inventory", version="1.0.0").route_prefix("/inventory").tags("sqlite", "database"))
    .database(url="sqlite:///runtime/inventory.db", auto_create=True, auto_migrate=False)
    .integrate(DiIntegration(auto_wire=True))
)
