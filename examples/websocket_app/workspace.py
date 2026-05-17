from aquilia import Integration, Module, Workspace

workspace = (
    Workspace("chat-sockets", version="1.0.0", description="WebSocket starter application")
    .runtime(mode="dev", port=8030, reload=True)
    .module(Module("chat", version="1.0.0").route_prefix("/chat").tags("websocket", "chat"))
    .integrate(Integration.di(auto_wire=True, manifest_validation=True))
    .integrate(Integration.routing(strict_matching=True))
    .security(cors_enabled=True, helmet_enabled=True)
)
