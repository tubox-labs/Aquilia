from aquilia import AppManifest
from aquilia.manifest import FaultHandlingConfig

manifest = AppManifest(
    name="realtime",
    version="1.0.0",
    description="Realtime order updates module",
    socket_controllers=["modules.realtime.sockets:OrderEventsSocket"],
    services=["modules.realtime.services:RealtimeService"],
    imports=["accounts", "orders"],
    base_path="modules.realtime",
    tags=["realtime", "sockets"],
    faults=FaultHandlingConfig(default_domain="REALTIME", strategy="propagate"),
)

__all__ = ["manifest"]
