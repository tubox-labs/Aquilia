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
    *,
    include_docker: bool = True,
    include_readme: bool = True,
    include_makefile: bool = True,
    include_tests: bool = True,
    include_gitignore: bool = True,
    include_license: Optional[str] = None,
) -> Path:
    """
    Create a new Aquilia workspace.

    When ``minimal=True``, generates the absolute minimum needed to run:
      - workspace.py (structure + inline AquilaConfig env config)
      - modules/ directory
      - starter.py (welcome page)
    No Docker files, no artifacts dir, no README, no .gitignore.

    Args:
        name: Workspace name
        minimal: Create minimal setup without extras
        template: Template to use (api, service, monolith)
        verbose: Enable verbose output
        include_docker: Generate Dockerfile and docker-compose.yml
        include_readme: Generate README.md
        include_makefile: Generate Makefile
        include_tests: Generate tests/ directory
        include_gitignore: Generate .gitignore
        include_license: License type (MIT, Apache-2.0, BSD-3) or None

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
        from aquilia.faults.domains import ConfigInvalidFault
        raise ConfigInvalidFault(
            key="workspace.path",
            reason=f"Directory '{name}' already exists",
        )

    generator = WorkspaceGenerator(
        name=name,
        path=workspace_path,
        minimal=minimal,
        template=template,
        include_docker=include_docker,
        include_readme=include_readme,
        include_makefile=include_makefile,
        include_tests=include_tests,
        include_gitignore=include_gitignore,
        include_license=include_license,
    )

    generator.generate()

    if verbose:
        dim("\nGenerated structure:")
        dim(f"  {name}/")
        dim(f"    workspace.py")
        dim(f"    starter.py")
        dim(f"    modules/")
        if not minimal:
            dim(f"    artifacts/")
            dim(f"    runtime/")
            if include_docker:
                dim(f"    Dockerfile")
                dim(f"    docker-compose.yml")
            if include_gitignore:
                dim(f"    .gitignore")
            if include_readme:
                dim(f"    README.md")

    return workspace_path
