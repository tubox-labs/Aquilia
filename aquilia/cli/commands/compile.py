"""Manifest compilation command.

Uses the Aquilia Build Pipeline to:
1. Discover and validate workspace modules
2. Run static checks (syntax, imports, routes)
3. Compile manifests to Crous binary artifacts
4. Bundle everything into a single verified output
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
    Compile manifests to artifacts using the build pipeline.

    Args:
        output_dir: Output directory for artifacts
        watch: Watch for changes and recompile
        verbose: Enable verbose output
        mode: Build mode ("dev" or "prod")
        check_only: Only run checks, don't emit artifacts

    Returns:
        List of generated artifact paths
    """
    workspace_root = Path.cwd()
    workspace_config = workspace_root / "workspace.py"

    if not workspace_config.exists():
        from aquilia.faults.domains import ConfigMissingFault

        raise ConfigMissingFault(key="workspace.py")

    output = Path(output_dir) if output_dir else workspace_root / "build"
    output.mkdir(parents=True, exist_ok=True)

    from aquilia.build import AquiliaBuildPipeline

    result = AquiliaBuildPipeline.build(
        workspace_root=str(workspace_root),
        mode=mode,
        verbose=verbose,
        output_dir=str(output),
        check_only=check_only,
    )

    if not result.success:
        print("\n  Compilation FAILED\n")
        for err in result.errors:
            print(f"  {err}")
        return []

    if verbose:
        print(f"  {result.summary()}")

    # Return paths of generated artifacts
    crous_files = sorted(output.glob("*.crous"))
    return [str(f.relative_to(workspace_root)) for f in crous_files]
