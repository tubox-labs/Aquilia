from aquilia.manifest import AppManifest

manifest = AppManifest(
    name="files",
    version="1.0.0",
    description="File storage module using StorageRegistry and memory backends.",
    controllers=["modules.files.controllers:FileHubController"],
    services=["modules.files.services:FileHubService"],
    exports=["modules.files.services:FileHubService"],
    tags=["storage", "files"],
)
