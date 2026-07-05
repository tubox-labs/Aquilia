"""
Aquilia configuration — everything in one place.

For workspace structure:
    from aquilia.config import Workspace, Module, Integration

For environment config:
    from aquilia.config import AquilaConfig, Env, Secret

For runtime config reading (subsystems only):
    from aquilia.config import ConfigLoader
"""

from aquilia.integrations.integration import Integration
from aquilia.pyconfig import AquilaConfig, Env, Secret, section
from aquilia.workspace import Module, Workspace

from ._loader import Config, ConfigLoader

__all__ = [
    "Workspace",
    "Module",
    "Integration",
    "AquilaConfig",
    "Env",
    "Secret",
    "section",
    "Config",
    "ConfigLoader",
]
