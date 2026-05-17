from aquilia.manifest import AppManifest

manifest = AppManifest(
    name="publicapi",
    version="1.0.0",
    description="Public API module with route-level version metadata and VersionStrategy service usage.",
    controllers=["modules.publicapi.controllers:PublicCatalogController"],
    services=["modules.publicapi.services:PublicCatalogService"],
    exports=["modules.publicapi.services:PublicCatalogService"],
    tags=["versioning", "public-api"],
)
