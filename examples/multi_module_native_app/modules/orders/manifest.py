from aquilia import AppManifest
from aquilia.manifest import FaultHandlingConfig

manifest = AppManifest(
    name="orders",
    version="1.0.0",
    description="Order checkout module",
    controllers=["modules.orders.controllers:OrdersController"],
    services=["modules.orders.services:OrdersService"],
    imports=["accounts", "catalog"],
    exports=["modules.orders.services:OrdersService"],
    base_path="modules.orders",
    tags=["orders"],
    faults=FaultHandlingConfig(default_domain="ORDERS", strategy="propagate"),
)

__all__ = ["manifest"]
