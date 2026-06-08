from aquilia import Module, Workspace
from aquilia.integrations import DiIntegration, RoutingIntegration

workspace = (
    Workspace("chat-sockets", version="1.0.0", description="WebSocket starter application")
    .runtime(mode="dev", port=8030, reload=True)
    .module(Module("chat", version="1.0.0").route_prefix("/chat").tags("websocket", "chat"))
    .integrate(DiIntegration(auto_wire=True))
    .integrate(RoutingIntegration(strict_matching=True))
    .security(cors_enabled=True, helmet_enabled=True)
)