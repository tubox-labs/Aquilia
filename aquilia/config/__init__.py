"""
Aquilia configuration — unified access to config, workspace, and integrations.

Examples:
    Loading workspace components:
    ```python
    from aquilia.config import Workspace, Module
    ```

    Declaring custom environment variables and secrets:
    ```python
    from aquilia.config import AquilaConfig, Env, Secret
    ```

    Accessing the configuration loader subsystem:
    ```python
    from aquilia.config import ConfigLoader
    ```
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
