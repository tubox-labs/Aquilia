from aquilia.manifest import AppManifest

manifest = AppManifest(
    name="inventory",
    version="1.0.0",
    description="Inventory module using Aquilia native SqliteService and pool transactions.",
    controllers=["modules.inventory.controllers:InventoryController"],
    services=["modules.inventory.services:InventorySqliteService"],
    exports=["modules.inventory.services:InventorySqliteService"],
    tags=["sqlite", "database", "transactions"],
)
