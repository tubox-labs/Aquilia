from aquilia import Integration, Module, Workspace
from aquilia.integrations import MLOpsIntegration

workspace = (
    Workspace("mlops-model-registry-app", version="1.0.0", description="MLOps registry and rollout reference")
    .runtime(mode="dev", host="127.0.0.1", port=8071, reload=True)
    .module(Module("mlopsdemo", version="1.0.0").route_prefix("/mlops").tags("mlops"))
    .integrate(MLOpsIntegration(enabled=True, registry_db="runtime/models.db", storage_backend="filesystem"))
    .integrate(Integration.di(auto_wire=True))
)
