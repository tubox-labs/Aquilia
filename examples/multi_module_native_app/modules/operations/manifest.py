from aquilia import AppManifest
from aquilia.manifest import FaultHandlingConfig

manifest = AppManifest(
    name="operations",
    version="1.0.0",
    description="Operations and health module",
    controllers=["modules.operations.controllers:OperationsController"],
    services=["modules.operations.services:OperationsService"],
    base_path="modules.operations",
    tags=["operations"],
    faults=FaultHandlingConfig(default_domain="OPERATIONS", strategy="propagate"),
)

__all__ = ["manifest"]
