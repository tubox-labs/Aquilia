"""
Aquilary CLI commands implementation for Click integration.
"""

import sys
import json
import importlib.util
from pathlib import Path
from typing import Any, List, Optional
import click

from aquilia.aquilary import (
    Aquilary,
    ManifestValidationError,
    DependencyGraph,
)
from aquilia.aquilary.core import RegistryMode


def ensure_sys_path():
    """Ensure current working directory is in sys.path for workspace imports."""
    import sys
    import os
    cwd = os.getcwd()
    if cwd not in sys.path:
        sys.path.insert(0, cwd)


def load_config(config_path: Optional[str]) -> Any:
    """Load config from Python file."""
    ensure_sys_path()
    if not config_path:
        return None

    path = Path(config_path)
    if not path.exists():
        click.secho(f"Error: Config file not found at '{config_path}'", fg="red", err=True)
        sys.exit(1)

    # 1. Try loading via ConfigLoader
    try:
        from aquilia.config import ConfigLoader
        return ConfigLoader.load(paths=[str(path)])
    except Exception:
        pass

    # 2. Fallback to manual Config class loading
    try:
        spec = importlib.util.spec_from_file_location("config", path)
        if spec is None or spec.loader is None:
            click.secho(f"Error: Cannot load config from '{config_path}'", fg="red", err=True)
            sys.exit(1)

        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)

        # Find Config class
        for name, obj in vars(module).items():
            if isinstance(obj, type) and name == "Config":
                return obj()

        click.secho(f"Error: No Config class found in '{config_path}'", fg="red", err=True)
        sys.exit(1)
    except Exception as e:
        click.secho(f"Error loading config: {e}", fg="red", err=True)
        sys.exit(1)


def run_validate(manifests: List[str], config_path: Optional[str], mode: str, autodiscover: bool) -> None:
    """Validate manifests."""
    click.echo(f"Validating manifests in mode: {mode}")
    if manifests:
        click.echo(f"   Manifests: {', '.join(manifests)}")
    else:
        click.echo("   Manifests: (auto-discovering)")

    config = load_config(config_path)

    try:
        registry = Aquilary.from_manifests(
            manifests=list(manifests),
            config=config,
            mode=mode,
            allow_fs_autodiscovery=autodiscover,
        )

        click.secho("\nValidation passed!", fg="green", bold=True)
        click.echo(f"   Apps: {len(registry.app_contexts)}")
        click.echo(f"   Fingerprint: {registry.fingerprint[:16]}...")

        click.echo("\nLoad Order:")
        for ctx in registry.app_contexts:
            deps = f" (→ {', '.join(ctx.depends_on)})" if ctx.depends_on else ""
            click.echo(f"   {ctx.load_order + 1}. {ctx.name} v{ctx.version}{deps}")

        # Show warnings if any
        warnings = registry._validation_report.get("warnings", [])
        if warnings:
            click.secho("\nWarnings:", fg="yellow", bold=True)
            for warning in warnings:
                click.secho(f"   - {warning}", fg="yellow")

    except ManifestValidationError as e:
        click.secho("\nValidation failed!", fg="red", bold=True)
        click.echo(f"\n{e}")
        sys.exit(1)
    except Exception as e:
        click.secho(f"\nUnexpected error: {e}", fg="red", err=True)
        sys.exit(1)


def run_inspect(manifests: List[str], config_path: Optional[str], mode: str, autodiscover: bool, json_path: Optional[str]) -> None:
    """Inspect registry diagnostics."""
    click.echo("Inspecting registry...")

    config = load_config(config_path)

    try:
        registry = Aquilary.from_manifests(
            manifests=list(manifests),
            config=config,
            mode=mode,
            allow_fs_autodiscovery=autodiscover,
        )

        diagnostics = registry.inspect()

        click.echo("\n" + "=" * 70)
        click.secho("Registry Diagnostics", bold=True)
        click.echo("=" * 70)

        click.echo("\nSummary:")
        click.echo(f"   Fingerprint: {diagnostics['fingerprint']}")
        click.echo(f"   Mode: {diagnostics['mode']}")
        click.echo(f"   App Count: {diagnostics['app_count']}")

        click.echo("\nApplications:")
        for app in diagnostics["apps"]:
            click.echo(f"\n   {app['name']} v{app['version']}")
            click.echo(f"      Load Order: {app['load_order']}")
            click.echo(f"      Controllers: {app['controllers']}")
            click.echo(f"      Services: {app['services']}")
            click.echo(f"      Dependencies: {', '.join(app['depends_on']) if app['depends_on'] else 'none'}")

        click.echo("\nDependency Graph:")
        for app_name, deps in diagnostics["dependency_graph"].items():
            deps_str = ", ".join(deps) if deps else "none"
            click.echo(f"   {app_name}: {deps_str}")

        if json_path:
            Path(json_path).write_text(json.dumps(diagnostics, indent=2), encoding="utf-8")
            click.secho(f"\nDiagnostics exported to: {json_path}", fg="green")

    except Exception as e:
        click.secho(f"Error during inspection: {e}", fg="red", err=True)
        sys.exit(1)


def run_freeze(manifests: List[str], config_path: Optional[str], output_path: str, autodiscover: bool) -> None:
    """Freeze registry for deployment."""
    click.echo("Freezing manifest...")

    config = load_config(config_path)

    try:
        registry = Aquilary.from_manifests(
            manifests=list(manifests),
            config=config,
            mode="prod",
            allow_fs_autodiscovery=autodiscover,
        )

        registry.export_manifest(output_path)

        click.secho("\nFrozen manifest exported!", fg="green", bold=True)
        click.echo(f"   Path: {output_path}")
        click.echo(f"   Fingerprint: {registry.fingerprint}")
        click.echo(f"   Apps: {len(registry.app_contexts)}")

        click.echo("\nApps included:")
        for ctx in registry.app_contexts:
            click.echo(f"   - {ctx.name} v{ctx.version}")

        click.echo("\nUsage in production:")
        click.echo(f"   1. Commit {output_path} to version control")
        click.echo(f"   2. Deploy with: aq aquilary run --frozen {output_path} --config {config_path or '<config_file>'}")
        click.echo(f"   3. Verify fingerprint matches: {registry.fingerprint}")

    except Exception as e:
        click.secho(f"Error freezing manifest: {e}", fg="red", err=True)
        sys.exit(1)


def run_graph(manifests: List[str], config_path: Optional[str], mode: str, output_path: Optional[str], autodiscover: bool) -> None:
    """Visualize dependency graph."""
    click.echo("Generating dependency graph...")

    config = load_config(config_path)

    try:
        registry = Aquilary.from_manifests(
            manifests=list(manifests),
            config=config,
            mode=mode,
            allow_fs_autodiscovery=autodiscover,
        )

        graph = DependencyGraph()
        for ctx in registry.app_contexts:
            graph.add_node(ctx.name, ctx.depends_on)

        dot = graph.to_dot()

        if output_path:
            out_path = Path(output_path)
            out_path.write_text(dot, encoding="utf-8")
            click.secho(f"\nGraph exported to: {output_path}", fg="green")
            click.echo("\nVisualize with:")
            click.echo(f"   dot -Tpng {output_path} -o {out_path.stem}.png")
            click.echo("   Or view at: https://dreampuf.github.io/GraphvizOnline/")
        else:
            click.echo(f"\n{dot}")

        layers = graph.get_layers()
        click.echo("\nParallel Loading Layers:")
        for i, layer in enumerate(layers, 1):
            click.echo(f"   Layer {i}: {', '.join(layer)}")

    except Exception as e:
        click.secho(f"Error generating graph: {e}", fg="red", err=True)
        sys.exit(1)


def run_app_registry(frozen_path: Optional[str], manifests: List[str], config_path: str, mode: str, autodiscover: bool) -> None:
    """Run application registry setup."""
    click.echo("Starting application...")

    config = load_config(config_path)

    try:
        if frozen_path:
            click.echo(f"   Loading from frozen manifest: {frozen_path}")
            registry = Aquilary.from_manifests(
                manifests=[],
                config=config,
                mode="prod",
                freeze_manifest_path=frozen_path,
            )
        else:
            click.echo("   Loading from manifests...")
            registry = Aquilary.from_manifests(
                manifests=list(manifests),
                config=config,
                mode=mode,
                allow_fs_autodiscovery=autodiscover,
            )

        click.echo(f"   Fingerprint: {registry.fingerprint}")
        click.echo(f"   Apps: {len(registry.app_contexts)}")

        click.echo("\nBuilding runtime...")
        runtime = registry.build_runtime()

        click.echo("   Compiling routes...")
        runtime.compile_routes()

        click.secho("\nRuntime ready!", fg="green", bold=True)
        click.echo("\nStartup sequence:")
        for ctx in registry.app_contexts:
            click.echo(f"   {ctx.load_order + 1}. Starting {ctx.name}...")
            if ctx.on_startup:
                try:
                    ctx.on_startup()
                except Exception as e:
                    click.secho(f"      Warning: Startup hook failed for {ctx.name}: {e}", fg="yellow")

    except Exception as e:
        click.secho(f"Error starting application: {e}", fg="red", err=True)
        sys.exit(1)
