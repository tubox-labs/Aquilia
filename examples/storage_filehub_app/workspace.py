from aquilia import Module, Workspace
from aquilia.integrations import DiIntegration, StorageIntegration

workspace = (
    Workspace("storage-filehub-app", version="1.0.0", description="Multi-backend storage file hub")
    .runtime(mode="dev", host="127.0.0.1", port=8063, reload=True)
    .module(Module("files", version="1.0.0").route_prefix("/files").tags("storage"))
    .integrate(
        StorageIntegration(
            default="documents",
            backends={
                "documents": {"backend": "memory", "max_size": 1048576},
                "quarantine": {"backend": "memory", "max_size": 262144},
            },
        )
    )
    .integrate(DiIntegration(auto_wire=True))
)
