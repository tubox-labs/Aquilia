from aquilia.manifest import AppManifest

manifest = AppManifest(
    name="mlopsdemo",
    version="1.0.0",
    description="MLOps module using model registry, AquiliaModel, rollout engine, and plugin host.",
    controllers=["modules.mlopsdemo.controllers:MLOpsDemoController"],
    services=["modules.mlopsdemo.services:MLOpsRegistryService"],
    exports=["modules.mlopsdemo.services:MLOpsRegistryService"],
    tags=["mlops", "model-registry", "rollout", "plugins"],
)
