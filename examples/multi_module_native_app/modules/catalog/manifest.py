from aquilia import AppManifest
from aquilia.manifest import FaultHandlingConfig

manifest = AppManifest(
    name="catalog",
    version="1.0.0",
    description="Product catalog module",
    controllers=["modules.catalog.controllers:CatalogController"],
    services=["modules.catalog.services:CatalogService"],
    exports=["modules.catalog.services:CatalogService"],
    base_path="modules.catalog",
    tags=["catalog"],
    faults=FaultHandlingConfig(default_domain="CATALOG", strategy="propagate"),
)

__all__ = ["manifest"]
