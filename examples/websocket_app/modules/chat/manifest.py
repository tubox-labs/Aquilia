from aquilia import AppManifest
from aquilia.manifest import FaultHandlingConfig

manifest = AppManifest(
    name="chat",
    version="1.0.0",
    description="Chat HTTP and WebSocket module",
    controllers=["modules.chat.controllers:ChatController"],
    socket_controllers=["modules.chat.sockets:ChatSocket"],
    services=["modules.chat.services:ChatPresenceService"],
    base_path="modules.chat",
    tags=["chat", "sockets"],
    faults=FaultHandlingConfig(default_domain="CHAT", strategy="propagate"),
)

__all__ = ["manifest"]
