from aquilia import AppManifest
from aquilia.manifest import FaultHandlingConfig

manifest = AppManifest(
    name="catalog",
    version="1.0.0",
    description="Product catalog API module",
    tags=["catalog", "rest"],
    controllers=["modules.catalog.controllers:CatalogController"],
    services=["modules.catalog.services:CatalogService"],
    base_path="modules.catalog",
    faults=FaultHandlingConfig(default_domain="CATALOG", strategy="propagate"),
)

__all__ = ["manifest"]
