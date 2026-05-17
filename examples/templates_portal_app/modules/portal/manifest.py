from aquilia.manifest import AppManifest, TemplateConfig

manifest = AppManifest(
    name="portal",
    version="1.0.0",
    description="Template-rendered portal module using TemplateEngine and TemplateLoader.",
    controllers=["modules.portal.controllers:PortalController"],
    services=["modules.portal.services:PortalRenderService"],
    templates=TemplateConfig(enabled=True, search_paths=["templates"], cache="memory", sandbox=True),
    exports=["modules.portal.services:PortalRenderService"],
    tags=["templates", "portal"],
)
