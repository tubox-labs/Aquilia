from aquilia.manifest import AppManifest

manifest = AppManifest(
    name="content",
    version="1.0.0",
    description="Localized content module using I18nService and MemoryCatalog.",
    controllers=["modules.content.controllers:ContentController"],
    services=["modules.content.services:ContentLocalizationService"],
    exports=["modules.content.services:ContentLocalizationService"],
    tags=["i18n", "content"],
)
