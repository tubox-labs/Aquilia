from aquilia import Integration, Module, Workspace

workspace = (
    Workspace("templates-portal-app", version="1.0.0", description="Server-rendered customer portal")
    .runtime(mode="dev", host="127.0.0.1", port=8068, reload=True)
    .module(Module("portal", version="1.0.0").route_prefix("/portal").tags("templates"))
    .integrate(Integration.templates.source("templates").cached("memory").secure())
    .integrate(Integration.di(auto_wire=True))
)
