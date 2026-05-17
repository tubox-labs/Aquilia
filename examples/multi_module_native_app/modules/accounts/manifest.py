from aquilia import AppManifest
from aquilia.manifest import FaultHandlingConfig

manifest = AppManifest(
    name="accounts",
    version="1.0.0",
    description="Identity and account API",
    controllers=["modules.accounts.controllers:AccountsController"],
    services=["modules.accounts.services:AccountsService"],
    exports=["modules.accounts.services:AccountsService"],
    base_path="modules.accounts",
    tags=["accounts"],
    faults=FaultHandlingConfig(default_domain="ACCOUNTS", strategy="propagate"),
)

__all__ = ["manifest"]
