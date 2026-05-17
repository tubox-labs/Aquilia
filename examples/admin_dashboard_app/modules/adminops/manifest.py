from aquilia.manifest import AppManifest

manifest = AppManifest(
    name="adminops",
    version="1.0.0",
    description="Admin operations module with model admin registration and permission-aware service workflows.",
    controllers=["modules.adminops.controllers:AdminOpsController"],
    services=["modules.adminops.services:AdminOpsService"],
    models=["modules.adminops.models:SupportTicket"],
    imports=[],
    exports=["modules.adminops.services:AdminOpsService"],
    tags=["admin", "permissions", "audit"],
)
