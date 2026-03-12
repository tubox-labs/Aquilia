"""
Aquilia MLOps Model Orchestrator.

Sits between the API layer and the execution engine.
Manages model identity, versioning, routing, lifecycle,
and lazy loading without knowing about HTTP.
"""

from .loader import ModelLoader
from .orchestrator import ModelOrchestrator
from .registry import ModelEntry, ModelRegistry
from .router import VersionRouter
from .versioning import VersionManager

__all__ = [
    "ModelRegistry",
    "ModelEntry",
    "VersionManager",
    "VersionRouter",
    "ModelLoader",
    "ModelOrchestrator",
]
