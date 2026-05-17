from aquilia import Integration, Module, Workspace

workspace = (
    Workspace("artifacts-release-app", version="1.0.0", description="Release artifact and signing workflow")
    .runtime(mode="dev", host="127.0.0.1", port=8070, reload=True)
    .module(Module("releases", version="1.0.0").route_prefix("/releases").tags("artifacts"))
    .integrate(Integration.di(auto_wire=True))
)
