"""Add module to workspace command."""

from pathlib import Path

from ..generators import ModuleGenerator
from ..generators.workspace import WorkspaceGenerator
from ..utils.colors import _CHECK, dim, info


def _ensure_docker_files(workspace_root: Path, verbose: bool = False) -> None:
    """
    Ensure Dockerfile and docker-compose.yml exist in the workspace.

    Called automatically by ``aq add module`` to keep deployment
    files in sync with the workspace structure.  Only generates files
    that do not already exist -- existing files are never overwritten.
    """
    from ..generators.deployment import (
        ComposeGenerator,
        DockerfileGenerator,
        WorkspaceIntrospector,
    )

    wctx = WorkspaceIntrospector(workspace_root).introspect()

    docker_gen = DockerfileGenerator(wctx)
    compose_gen = ComposeGenerator(wctx)

    generated: list[str] = []

    dockerfile = workspace_root / "Dockerfile"
    if not dockerfile.exists():
        dockerfile.write_text(docker_gen.generate_dockerfile(), encoding="utf-8")
        generated.append("Dockerfile")

    dockerignore = workspace_root / ".dockerignore"
    if not dockerignore.exists():
        dockerignore.write_text(docker_gen.generate_dockerignore(), encoding="utf-8")
        generated.append(".dockerignore")

    compose_file = workspace_root / "docker-compose.yml"
    if not compose_file.exists():
        compose_file.write_text(compose_gen.generate_compose(include_monitoring=False), encoding="utf-8")
        generated.append("docker-compose.yml")

    if generated and verbose:
        info(f"  {_CHECK} Auto-generated deployment files: {', '.join(generated)}")


def add_module(
    name: str,
    depends_on: list[str],
    fault_domain: str | None = None,
    route_prefix: str | None = None,
    with_tests: bool = False,
    minimal: bool = False,
    no_docker: bool = False,
    verbose: bool = False,
) -> Path:
    """
    Add a new module to the workspace.

    When ``minimal=True``, generates only the essentials:
      - manifest.py (lean)
      - controllers.py (single GET endpoint)
      - __init__.py

    Args:
        name: Module name
        depends_on: List of module dependencies
        fault_domain: Custom fault domain
        route_prefix: Route prefix for the module
        with_tests: Generate test routes file
        minimal: Generate minimal module (no services/faults boilerplate)
        no_docker: Skip Docker file auto-generation
        verbose: Enable verbose output

    Returns:
        Path to created module
    """
    workspace_root = Path.cwd()
    workspace_file = workspace_root / "workspace.py"

    if not workspace_file.exists():
        from aquilia.faults.domains import ConfigMissingFault

        raise ConfigMissingFault(key="workspace.py")

    if verbose:
        info(f"Adding module '{name}'...")
        if depends_on:
            info(f"  Dependencies: {', '.join(depends_on)}")
        if fault_domain:
            info(f"  Fault domain: {fault_domain}")
        if route_prefix:
            info(f"  Route prefix: {route_prefix}")
        if with_tests:
            info("  With test routes: Yes")
        if minimal:
            info("  Minimal mode: enabled")

    # Check if modules directory exists
    modules_dir = workspace_root / "modules"
    if not modules_dir.exists():
        modules_dir.mkdir(parents=True, exist_ok=True)

    # Check if module already exists
    module_path = modules_dir / name
    if module_path.exists():
        from aquilia.faults.domains import ConfigInvalidFault

        raise ConfigInvalidFault(
            key="module.name",
            reason=f"Module '{name}' already exists",
        )

    # Parse existing workspace.py to find existing modules
    workspace_content = workspace_file.read_text(encoding="utf-8")
    existing_modules = []

    # Simple regex to find .module() calls -- match Module("name"...)
    import re

    module_pattern = r'Module\("([^"]+)"'
    existing_modules = re.findall(module_pattern, workspace_content)

    # Validate dependencies
    for dep in depends_on:
        if dep not in existing_modules:
            from aquilia.faults.domains import ConfigInvalidFault

            raise ConfigInvalidFault(
                key="module.depends_on",
                reason=f"Dependency '{dep}' not found in workspace",
            )

    # Generate module structure
    generator = ModuleGenerator(
        name=name,
        path=module_path,
        depends_on=depends_on,
        fault_domain=fault_domain or name.upper(),
        route_prefix=route_prefix or f"/{name}",
        with_tests=with_tests,
        minimal=minimal,
    )

    generator.generate()

    # Update workspace with the new module (don't regenerate everything)
    try:
        workspace_generator = WorkspaceGenerator(name=workspace_root.name, path=workspace_root)

        # Discover the new module
        discovered = workspace_generator._discover_modules()

        # Update workspace.py with discovered modules (preserves existing config)
        workspace_path = workspace_root / "workspace.py"
        workspace_generator.update_workspace_config(workspace_path, discovered)

        if verbose:
            info(f"{_CHECK} Updated workspace.py with auto-discovery")
    except Exception as e:
        if verbose:
            warning = __import__("aquilia.cli.utils.colors", fromlist=["warning"]).warning
            warning(f"  Could not regenerate workspace.py: {e}")
            info("  Module was created, but workspace.py may need manual update")

    if verbose:
        dim("\nGenerated structure:")
        dim(f"  modules/{name}/")
        dim("    manifest.py")
        dim("    controllers.py")
        if not minimal:
            dim("    services.py")
            dim("    faults.py")
        if with_tests:
            dim("    test_routes.py")
        dim("    __init__.py")

    # Auto-generate Docker/Compose files if they don't exist yet
    if not no_docker:
        try:
            _ensure_docker_files(workspace_root, verbose=verbose)
        except Exception:
            # Non-fatal -- deployment files are a convenience
            pass

    return module_path
