from aquilia import Module, Workspace
from aquilia.integrations import DiIntegration, TemplatesIntegration

workspace = (
    Workspace("templates-portal-app", version="1.0.0", description="Server-rendered customer portal")
    .runtime(mode="dev", host="127.0.0.1", port=8068, reload=True)
    .module(Module("portal", version="1.0.0").route_prefix("/portal").tags("templates"))
    .integrate(TemplatesIntegration(search_paths=["templates"], cache="memory", sandbox=True))
    .integrate(DiIntegration(auto_wire=True))
)
