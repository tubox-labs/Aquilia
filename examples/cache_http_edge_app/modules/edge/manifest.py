from aquilia.manifest import AppManifest

manifest = AppManifest(
    name="edge",
    version="1.0.0",
    description="Cache-aside HTTP edge module backed by Aquilia cache and native HTTP mock transport.",
    controllers=["modules.edge.controllers:EdgeController"],
    services=["modules.edge.services:EdgeGatewayService"],
    exports=["modules.edge.services:EdgeGatewayService"],
    tags=["cache", "http", "edge"],
)
