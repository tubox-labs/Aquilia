"""Code generators for workspace and modules."""

from aquilia.cli.generators.controller import generate_controller
from aquilia.cli.generators.deployment import (
    CIGenerator,
    ComposeGenerator,
    DockerfileGenerator,
    EnvGenerator,
    GrafanaGenerator,
    KubernetesGenerator,
    MakefileGenerator,
    NginxGenerator,
    PrometheusGenerator,
    WorkspaceIntrospector,
)
from aquilia.cli.generators.module import ModuleGenerator
from aquilia.cli.generators.workspace import WorkspaceGenerator

__all__ = [
    "WorkspaceGenerator",
    "ModuleGenerator",
    "generate_controller",
    # Deployment generators
    "WorkspaceIntrospector",
    "DockerfileGenerator",
    "ComposeGenerator",
    "KubernetesGenerator",
    "NginxGenerator",
    "CIGenerator",
    "PrometheusGenerator",
    "GrafanaGenerator",
    "EnvGenerator",
    "MakefileGenerator",
]
