from aquilia import AppManifest
from aquilia.manifest import FaultHandlingConfig

manifest = AppManifest(
    name="projects",
    version="1.0.0",
    description="Project CRUD module",
    controllers=["modules.projects.controllers:ProjectsController"],
    services=["modules.projects.services:ProjectsService"],
    models=["modules.projects.models:Project"],
    base_path="modules.projects",
    tags=["projects"],
    faults=FaultHandlingConfig(default_domain="PROJECTS", strategy="propagate"),
)

__all__ = ["manifest"]
