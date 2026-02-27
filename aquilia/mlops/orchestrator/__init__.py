"""
Aquilia MLOps Model Orchestrator.

Sits between the API layer and the execution engine.
Manages model identity, versioning, routing, lifecycle,
and lazy loading without knowing about HTTP.
"""

from .registry import ModelRegistry, ModelEntry
from .versioning import VersionManager
from .router import VersionRouter
from .loader import ModelLoader
from .orchestrator import ModelOrchestrator

__all__ = [
    "ModelRegistry",
    "ModelEntry",
    "VersionManager",
    "VersionRouter",
    "ModelLoader",
    "ModelOrchestrator",
]
