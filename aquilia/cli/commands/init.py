"""Workspace and module initialization commands."""

from pathlib import Path
from typing import Optional

from ..utils.colors import info, dim
from ..generators import WorkspaceGenerator, ModuleGenerator


def create_workspace(
    name: str,
    minimal: bool = False,
    template: Optional[str] = None,
    verbose: bool = False,
) -> Path:
    """
    Create a new Aquilia workspace.

    When ``minimal=True``, generates the absolute minimum needed to run:
      - workspace.py (lean config — no sessions, no security, no telemetry)
      - modules/ directory
      - config/base.yaml (minimal)
      - starter.py (welcome page)
    No Docker files, no artifacts dir, no README, no .gitignore.

    Args:
        name: Workspace name
        minimal: Create minimal setup without extras
        template: Template to use (api, service, monolith)
        verbose: Enable verbose output

    Returns:
        Path to created workspace
    """
    if verbose:
        info(f"Creating workspace '{name}'...")
        if template:
            info(f"  Using template: {template}")
        if minimal:
            info(f"  Minimal mode: enabled")

    workspace_path = Path.cwd() / name

    if workspace_path.exists():
        raise ValueError(f"Directory '{name}' already exists")

    generator = WorkspaceGenerator(
        name=name,
        path=workspace_path,
        minimal=minimal,
        template=template,
    )

    generator.generate()

    if verbose:
        dim("\nGenerated structure:")
        dim(f"  {name}/")
        dim(f"    workspace.py")
        dim(f"    starter.py")
        dim(f"    modules/")
        dim(f"    config/")
        dim(f"      base.yaml")
        if not minimal:
            dim(f"      dev.yaml")
            dim(f"      prod.yaml")
            dim(f"    artifacts/")
            dim(f"    runtime/")
            dim(f"    Dockerfile")
            dim(f"    docker-compose.yml")
            dim(f"    .gitignore")
            dim(f"    README.md")

    return workspace_path
