"""Manifest compilation command.

Compiles workspace and module manifests into the native artifact store.
This is an explicit inspection/development tool; runtime loads the
workspace directly.
"""

from pathlib import Path


def compile_workspace(
    output_dir: str | None = None,
    watch: bool = False,
    verbose: bool = False,
    mode: str = "dev",
    check_only: bool = False,
) -> list[str]:
    """
    Compile manifests to artifacts using the workspace compiler.

    Args:
        output_dir: Output directory for artifacts
        watch: Watch for changes and recompile
        verbose: Enable verbose output
        mode: Reserved for CLI compatibility.
        check_only: Validate workspace presence without emitting artifacts.

    Returns:
        List of generated artifact paths
    """
    workspace_root = Path.cwd()
    workspace_config = workspace_root / "workspace.py"

    if not workspace_config.exists():
        from aquilia.faults.domains import ConfigMissingFault

        raise ConfigMissingFault(key="workspace.py")

    output = Path(output_dir) if output_dir else workspace_root / "artifacts"
    output.mkdir(parents=True, exist_ok=True)

    if check_only:
        return []

    from aquilia.cli.compilers.workspace import WorkspaceCompiler

    compiler = WorkspaceCompiler(workspace_root=workspace_root, output_dir=output, verbose=verbose)
    artifact_paths = compiler.compile()
    if verbose:
        print(f"  Compiled {len(artifact_paths)} artifact(s)")

    return [str(f.relative_to(workspace_root)) for f in artifact_paths]
