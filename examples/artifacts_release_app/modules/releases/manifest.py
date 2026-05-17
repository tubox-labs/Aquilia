from aquilia.manifest import AppManifest

manifest = AppManifest(
    name="releases",
    version="1.0.0",
    description="Release module using artifacts, integrity checks, in-memory store, and signing helpers.",
    controllers=["modules.releases.controllers:ReleaseController"],
    services=["modules.releases.services:ReleaseArtifactService"],
    exports=["modules.releases.services:ReleaseArtifactService"],
    tags=["artifacts", "signing", "release"],
)
