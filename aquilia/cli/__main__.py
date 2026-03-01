"""Aquilate CLI - Main Entry Point.

The `aq` command provides manifest-driven project orchestration.

Commands:
    init     - Create new workspace or module
    add      - Add module to workspace
    generate - Generate controllers and services
    validate - Static validation of manifests
    compile  - Compile manifests to artifacts
    run      - Development server with hot-reload
    serve    - Production server (immutable)
    freeze   - Generate immutable artifacts
    inspect  - Query compiled artifacts
    migrate  - Convert legacy Django-style projects
    doctor   - Diagnose workspace issues
    version  - Show version information
"""

import sys
from pathlib import Path
from typing import Optional

import click

from . import __version__, __cli_name__
from .utils.colors import (
    success, error, info, warning, dim, bold,
    banner, section, kv, rule, step, bullet, panel, table, next_steps,
    file_written, file_skipped, tree_item, badge, indent_echo, accent,
    _CHECK, _CROSS, _ARROW, _BULLET,
)

import re as _re

_DEFAULT_DB_URL = "sqlite:///db.sqlite3"

# ═══════════════════════════════════════════════════════════════════════════
# Workspace guard — block operational commands when no workspace.py present
# ═══════════════════════════════════════════════════════════════════════════

# Commands that do NOT require a workspace.py to exist:
_NO_WORKSPACE_REQUIRED = frozenset({
    "init", "version", "--version", "--help", "help", "doctor",
})


def _require_workspace(ctx: click.Context) -> None:
    """Abort if workspace.py is not found in the current directory.

    Allows a small set of commands (``init``, ``version``, ``doctor``)
    to run without a workspace.  Everything else requires the file.
    Also skips the check when ``--help`` is requested.
    """
    # Never block --help output
    if ctx.resilient_parsing or "--help" in (ctx.params or {}):
        return
    # Check sys.argv for --help (covers Click's eager help handling)
    import sys as _sys
    if "--help" in _sys.argv or "-h" in _sys.argv:
        return

    # Walk up the invocation chain to find the actual sub-command name
    parts: list[str] = []
    c: Optional[click.Context] = ctx
    while c is not None:
        if c.info_name and c.info_name not in ("cli", "aq"):
            parts.insert(0, c.info_name)
        c = c.parent
    top = parts[0] if parts else ""

    if top in _NO_WORKSPACE_REQUIRED:
        return

    # During Click's own --help processing, invoked_subcommand is set before
    # the sub-command callback fires.  At the root level when there's no
    # sub-command yet, skip the check.
    if not top:
        return

    workspace_file = Path("workspace.py")
    if not workspace_file.exists():
        click.echo()
        error(
            f"  {_CROSS} No workspace.py found in the current directory."
        )
        click.echo()
        info("  Run 'aq init workspace <name>' to create a new Aquilia workspace first.")
        click.echo()
        raise SystemExit(1)


def _detect_workspace_db_url() -> str:
    """Auto-detect the database URL from workspace.py in the current directory.

    Scans workspace.py for ``.database(url="...")`` or
    ``Integration.database(url="...")`` patterns and returns the first URL
    found.  Falls back to the framework default ``sqlite:///db.sqlite3``.
    """
    workspace_file = Path("workspace.py")
    if not workspace_file.exists():
        return _DEFAULT_DB_URL
    try:
        text = workspace_file.read_text()
        # Match .database(url="<url>") or .database(url='<url>')
        m = _re.search(r'\.database\(\s*url\s*=\s*["\']([^"\']+)["\']', text)
        if m:
            return m.group(1)
    except Exception:
        pass
    return _DEFAULT_DB_URL


# ═══════════════════════════════════════════════════════════════════════════
# Custom Click help formatter
# ═══════════════════════════════════════════════════════════════════════════


class AquiliaGroup(click.Group):
    """Click group subclass with branded help output."""

    # Command categories for grouped display
    _CATEGORIES = {
        "Scaffold": ["init", "add", "generate"],
        "Develop": ["run", "validate", "compile", "test", "discover", "doctor"],
        "Production": ["serve", "freeze"],
        "Database": ["db"],
        "Admin": ["admin"],
        "Inspect": ["inspect", "manifest", "analytics"],
        "Subsystems": ["ws", "cache", "mail"],
        "MLOps": ["pack", "model", "deploy", "observe", "export", "plugin", "lineage", "experiment"],
        "Deploy": ["deploy-gen", "artifact"],
        "Migration": ["migrate"],
    }

    def format_help(self, ctx: click.Context, formatter: click.HelpFormatter) -> None:
        """Override to add Aquilia branding to the top-level help."""
        # Only show the full banner for the root group
        if ctx.parent is None:
            banner("Aquilia", subtitle=f"v{__version__}  {_CHECK}  manifest-driven framework CLI")
            click.echo()

        super().format_help(ctx, formatter)

    def format_commands(
        self, ctx: click.Context, formatter: click.HelpFormatter
    ) -> None:
        """Format command listing with categorised groups."""
        commands_map = {}
        for subcommand in self.list_commands(ctx):
            cmd = self.get_command(ctx, subcommand)
            if cmd is None or cmd.hidden:
                continue
            help_text = cmd.get_short_help_str(limit=48)
            commands_map[subcommand] = help_text

        if not commands_map:
            return

        # Try categorised output for root group
        if ctx.parent is None:
            categorised: set[str] = set()
            max_len = max(len(c) for c in commands_map) + 2

            for cat_name, cat_cmds in self._CATEGORIES.items():
                matched = [(c, commands_map[c]) for c in cat_cmds if c in commands_map]
                if not matched:
                    continue
                with formatter.section(
                    click.style(cat_name, fg="cyan", bold=True)
                ):
                    for name, help_text in matched:
                        padded = name.ljust(max_len)
                        styled_name = click.style(padded, fg="green")
                        formatter.write(f"  {styled_name} {help_text}\n")
                        categorised.add(name)

            # Any uncategorised commands
            uncategorised = [(c, h) for c, h in commands_map.items() if c not in categorised]
            if uncategorised:
                with formatter.section(
                    click.style("Other", fg="cyan", bold=True)
                ):
                    for name, help_text in uncategorised:
                        padded = name.ljust(max_len)
                        styled_name = click.style(padded, fg="green")
                        formatter.write(f"  {styled_name} {help_text}\n")
        else:
            # Subgroups: simple listing
            with formatter.section(
                click.style("Commands", fg="cyan", bold=True)
            ):
                max_len = max(len(c) for c in commands_map) + 2
                for name, help_text in commands_map.items():
                    padded = name.ljust(max_len)
                    styled_name = click.style(padded, fg="green")
                    formatter.write(f"  {styled_name} {help_text}\n")


@click.group(cls=AquiliaGroup)
@click.version_option(version=__version__, prog_name=__cli_name__)
@click.option('--verbose', '-v', is_flag=True, help='Verbose output')
@click.option('--quiet', '-q', is_flag=True, help='Minimal output')
@click.pass_context
def cli(ctx, verbose: bool, quiet: bool):
    """Manifest-driven, artifact-first project orchestration.

    \b
    Quick start:
      aq init workspace my-api
      aq add module users
      aq validate
      aq compile
      aq run
    """
    ctx.ensure_object(dict)
    ctx.obj['verbose'] = verbose
    ctx.obj['quiet'] = quiet

    # Workspace guard — operational commands require workspace.py
    _require_workspace(ctx)


# ============================================================================
# Commands
# ============================================================================

@cli.group(cls=AquiliaGroup)
def init():
    """Initialize new workspace or module."""
    pass


@init.command('workspace')
@click.argument('name')
@click.option('--minimal', is_flag=True, help='Minimal setup (no examples)')
@click.option('--template', type=str, help='Use template (api, service, monolith)')
@click.pass_context
def init_workspace(ctx, name: str, minimal: bool, template: Optional[str]):
    """
    Create a new Aquilia workspace.
    
    Examples:
      aq init workspace my-api
      aq init workspace my-api --minimal
      aq init workspace my-api --template=api
    """
    from .commands.init import create_workspace
    
    try:
        workspace_path = create_workspace(
            name=name,
            minimal=minimal,
            template=template,
            verbose=ctx.obj['verbose'],
        )
        
        if not ctx.obj['quiet']:
            click.echo()
            banner("Aquilia", subtitle=f"Workspace created  {_CHECK}")
            click.echo()

            section("Project")
            kv("Name", name)
            kv("Location", str(workspace_path))
            if template:
                kv("Template", template)
            kv("Mode", "minimal" if minimal else "full")
            click.echo()

            section("Generated Files")
            tree_item("workspace.py", depth=0)
            tree_item("starter.py", depth=0)
            tree_item("config/", depth=0)
            tree_item("base.yaml", depth=1)
            if not minimal:
                tree_item("dev.yaml", depth=1)
                tree_item("prod.yaml", depth=1, last=True)
            else:
                tree_item("base.yaml", depth=1, last=True)
            tree_item(".env.example", depth=0)
            tree_item(".editorconfig", depth=0)
            tree_item(".gitignore", depth=0)
            tree_item("requirements.txt", depth=0)
            tree_item("tests/", depth=0)
            tree_item("conftest.py", depth=1)
            tree_item("test_smoke.py", depth=1, last=True)
            if not minimal:
                tree_item("Makefile", depth=0)
                tree_item("Dockerfile", depth=0)
                tree_item("docker-compose.yml", depth=0, last=True)
            click.echo()

            next_steps([
                f"cd {name}",
                "cp .env.example .env",
                "pip install -r requirements.txt",
                "aq add module <module_name>",
                "make run",
            ])
    
    except Exception as e:
        error(f"  {_CROSS} Failed to create workspace: {e}")
        sys.exit(1)


@cli.group(cls=AquiliaGroup)
def add():
    """Add module to workspace."""
    pass


@add.command('module')
@click.argument('name')
@click.option('--depends-on', multiple=True, help='Module dependencies')
@click.option('--fault-domain', type=str, help='Custom fault domain')
@click.option('--route-prefix', type=str, help='Route prefix (default: /name)')
@click.option('--with-tests', is_flag=True, help='Generate test routes')
@click.option('--minimal', is_flag=True, help='Generate minimal module (controller + manifest only)')
@click.option('--no-docker', is_flag=True, help='Skip auto-generating Docker files')
@click.pass_context
def add_module(ctx, name: str, depends_on: tuple, fault_domain: Optional[str], route_prefix: Optional[str], with_tests: bool, minimal: bool, no_docker: bool):
    """
    Add a new module to the workspace.
    
    By default also generates Dockerfile and docker-compose.yml if they
    don't exist yet.  Use --no-docker to skip.
    
    Examples:
      aq add module users
      aq add module users --minimal
      aq add module products --depends-on=users
      aq add module admin --fault-domain=ADMIN --route-prefix=/api/admin
      aq add module test --with-tests
      aq add module api --no-docker
    """
    from .commands.add import add_module as _add_module
    
    try:
        module_path = _add_module(
            name=name,
            depends_on=list(depends_on),
            fault_domain=fault_domain,
            route_prefix=route_prefix,
            with_tests=with_tests,
            minimal=minimal,
            no_docker=no_docker,
            verbose=ctx.obj['verbose'],
        )
        
        if not ctx.obj['quiet']:
            click.echo()
            success(f"  {_CHECK} Module '{name}' added successfully")
            click.echo()

            section("Module Details")
            kv("Name", name)
            kv("Location", f"modules/{name}/")
            kv("Route Prefix", route_prefix or f"/{name}")
            if depends_on:
                kv("Dependencies", ", ".join(depends_on))
            if fault_domain:
                kv("Fault Domain", fault_domain)
            kv("Type", "minimal" if minimal else "full")
            click.echo()

            section("Generated Files")
            tree_item("__init__.py", depth=0)
            tree_item("manifest.py", depth=0)
            tree_item("controllers.py", depth=0)
            if not minimal:
                tree_item("services.py", depth=0)
                tree_item("faults.py", depth=0)
                tree_item("models/", depth=0)
            if with_tests:
                tree_item("test_routes.py", depth=0, last=True)
            else:
                items = ["__init__.py", "manifest.py", "controllers.py"]
                if not minimal:
                    items.extend(["services.py", "faults.py", "models/"])
                # Mark last item
            click.echo()

            steps = [
                f"Edit modules/{name}/controllers.py",
            ]
            if not minimal:
                steps.append(f"Add services in modules/{name}/services.py")
            steps.extend(["aq run", "aq validate"])
            next_steps(steps)
    
    except Exception as e:
        error(f"  {_CROSS} Failed to add module: {e}")
        sys.exit(1)


@cli.group(cls=AquiliaGroup)
def generate():
    """Generate code from templates."""
    pass


@generate.command('controller')
@click.argument('name')
@click.option('--prefix', type=str, help='Route prefix (default: /name)')
@click.option('--resource', type=str, help='Resource name (default: name)')
@click.option('--simple', is_flag=True, help='Generate simple controller')
@click.option('--with-lifecycle', is_flag=True, help='Include lifecycle hooks')
@click.option('--test', is_flag=True, help='Generate test/demo controller')
@click.option('--output', type=click.Path(), help='Output directory')
@click.pass_context
def generate_controller(ctx, name: str, prefix: Optional[str], resource: Optional[str], simple: bool, with_lifecycle: bool, test: bool, output: Optional[str]):
    """
    Generate a new controller.
    
    Examples:
      aq generate controller Users
      aq generate controller Products --prefix=/api/products
      aq generate controller Health --simple
      aq generate controller Admin --with-lifecycle
      aq generate controller Test --test
      aq generate controller Admin --output=apps/admin/
    """
    from .generators.controller import generate_controller as _generate_controller
    
    try:
        file_path = _generate_controller(
            name=name,
            output_dir=output or 'controllers',
            prefix=prefix,
            resource=resource,
            simple=simple,
            with_lifecycle=with_lifecycle,
            test=test,
        )
        
        if not ctx.obj['quiet']:
            click.echo()
            success(f"  {_CHECK} Generated controller '{name}'")
            click.echo()
            section("Controller")
            kv("Name", f"{name}Controller")
            kv("Location", str(file_path))
            if with_lifecycle:
                kv("Lifecycle", "on_startup, on_request, on_response")
            if test:
                kv("Type", "Test/Demo controller")
            click.echo()
            next_steps([
                f"Register in manifest: controllers = ['{file_path.parent.name}.{file_path.stem}:{name}Controller']",
                "Implement your business logic",
                "aq run",
            ])
    
    except Exception as e:
        error(f"  {_CROSS} Failed to generate controller: {e}")
        sys.exit(1)


@cli.command('validate')
@click.option('--strict', is_flag=True, help='Strict validation (prod-level)')
@click.option('--module', type=str, help='Validate single module')
@click.pass_context
def validate(ctx, strict: bool, module: Optional[str]):
    """
    Validate workspace manifests.
    
    Examples:
      aq validate
      aq validate --strict
      aq validate --module=users
    """
    from .commands.validate import validate_workspace
    
    try:
        result = validate_workspace(
            strict=strict,
            module_filter=module,
            verbose=ctx.obj['verbose'],
        )
        
        if not ctx.obj['quiet']:
            click.echo()
            if result.is_valid:
                success(f"  {_CHECK} Validation passed")
                click.echo()
                section("Summary")
                kv("Modules", str(result.module_count))
                kv("Routes", str(result.route_count))
                kv("DI Providers", str(result.provider_count))
                if result.fingerprint:
                    kv("Fingerprint", str(result.fingerprint)[:24])
                # Show warnings even when valid
                if hasattr(result, 'warnings') and result.warnings:
                    click.echo()
                    section("Warnings")
                    for w in result.warnings:
                        bullet(w, fg="yellow")
            else:
                error(f"  {_CROSS} Validation failed")
                click.echo()
                section("Errors")
                for fault in result.faults:
                    bullet(fault, fg="red")
                if hasattr(result, 'warnings') and result.warnings:
                    click.echo()
                    section("Warnings")
                    for w in result.warnings:
                        bullet(w, fg="yellow")
                sys.exit(1)
    
    except Exception as e:
        error(f"  {_CROSS} Validation error: {e}")
        sys.exit(1)


@cli.command('compile')
@click.option('--watch', is_flag=True, help='Watch for changes')
@click.option('--output', type=click.Path(), help='Output directory')
@click.pass_context
def compile(ctx, watch: bool, output: Optional[str]):
    """
    Compile manifests to artifacts.
    
    Examples:
      aq compile
      aq compile --watch
      aq compile --output=dist/
    """
    from .commands.compile import compile_workspace
    
    try:
        artifacts = compile_workspace(
            output_dir=output,
            watch=watch,
            verbose=ctx.obj['verbose'],
        )
        
        if not ctx.obj['quiet']:
            click.echo()
            success(f"  {_CHECK} Compilation complete")
            click.echo()
            section("Artifacts")
            kv("Count", str(len(artifacts)))
            for artifact in artifacts:
                tree_item(str(artifact))
    
    except Exception as e:
        error(f"  {_CROSS} Compilation failed: {e}")
        sys.exit(1)


@cli.command('run')
@click.option('--mode', type=click.Choice(['dev', 'test']), default='dev', help='Runtime mode')
@click.option('--port', type=int, default=8000, help='Server port')
@click.option('--host', type=str, default='127.0.0.1', help='Server host')
@click.option('--reload/--no-reload', default=True, help='Enable hot-reload')
@click.pass_context
def run(ctx, mode: str, port: int, host: str, reload: bool):
    """
    Start development server.
    
    Examples:
      aq run
      aq run --port=3000
      aq run --mode=test --no-reload
    """
    from .commands.run import run_dev_server
    
    try:
        run_dev_server(
            mode=mode,
            host=host,
            port=port,
            reload=reload,
            verbose=ctx.obj['verbose'],
        )
    
    except KeyboardInterrupt:
        if not ctx.obj['quiet']:
            click.echo()
            info(f"  {_CHECK} Server stopped gracefully")
    except Exception as e:
        error(f"  {_CROSS} Server error: {e}")
        sys.exit(1)


@cli.command('serve')
@click.option('--workers', type=int, default=1, help='Number of workers')
@click.option('--bind', type=str, default='0.0.0.0:8000', help='Bind address')
@click.option('--use-gunicorn', is_flag=True, help='Use gunicorn with UvicornWorker (recommended for production)')
@click.option('--timeout', type=int, default=120, help='Worker timeout in seconds (gunicorn only)')
@click.option('--graceful-timeout', type=int, default=30, help='Graceful shutdown timeout (gunicorn only)')
@click.pass_context
def serve(ctx, workers: int, bind: str, use_gunicorn: bool, timeout: int, graceful_timeout: int):
    """
    Start production server with compiled Crous artifacts.
    
    Uses uvicorn by default. Pass --use-gunicorn for production
    deployments with gunicorn process management and UvicornWorker.

    Examples:
      aq serve
      aq serve --workers=4
      aq serve --use-gunicorn --workers=4
      aq serve --bind=0.0.0.0:8080 --use-gunicorn --timeout=180
    """
    from .commands.serve import serve_production
    
    try:
        serve_production(
            workers=workers,
            bind=bind,
            verbose=ctx.obj['verbose'],
            use_gunicorn=use_gunicorn,
            timeout=timeout,
            graceful_timeout=graceful_timeout,
        )
    
    except KeyboardInterrupt:
        if not ctx.obj['quiet']:
            click.echo()
            info(f"  {_CHECK} Server stopped")
    except Exception as e:
        error(f"  {_CROSS} Server error: {e}")
        sys.exit(1)


@cli.command('freeze')
@click.option('--output', type=click.Path(), help='Output directory')
@click.option('--sign', is_flag=True, help='Sign artifacts')
@click.pass_context
def freeze(ctx, output: Optional[str], sign: bool):
    """
    Generate immutable artifacts for production.
    
    Examples:
      aq freeze
      aq freeze --output=dist/
      aq freeze --sign
    """
    from .commands.freeze import freeze_artifacts
    
    try:
        fingerprint = freeze_artifacts(
            output_dir=output,
            sign=sign,
            verbose=ctx.obj['verbose'],
        )
        
        if not ctx.obj['quiet']:
            click.echo()
            success(f"  {_CHECK} Artifacts frozen")
            kv("Fingerprint", fingerprint)
    
    except Exception as e:
        error(f"  {_CROSS} Freeze failed: {e}")
        sys.exit(1)


@cli.command('build')
@click.option('--mode', type=click.Choice(['dev', 'prod']), default='dev', help='Build mode')
@click.option('--output', type=click.Path(), default='build', help='Output directory')
@click.option('--compress', type=click.Choice(['none', 'lz4', 'zstd']), default=None, help='Compression')
@click.option('--check-only', is_flag=True, help='Only run checks, don\'t emit artifacts')
@click.option('--skip-checks', is_flag=True, help='Skip static checks (faster)')
@click.pass_context
def build(ctx, mode: str, output: str, compress: Optional[str], check_only: bool, skip_checks: bool):
    """
    Build the workspace (compile, check, bundle).

    Like Vite or Next.js, the build command compiles, validates,
    and bundles the entire workspace into optimized Crous binary
    artifacts. If any check fails, the build is aborted.

    Examples:
      aq build
      aq build --mode=prod
      aq build --mode=prod --compress=lz4
      aq build --check-only
      aq build --output=dist/
    """
    from aquilia.build import AquiliaBuildPipeline

    try:
        compression = compress or ("lz4" if mode == "prod" else "none")
        verbose = ctx.obj['verbose']

        if not ctx.obj['quiet']:
            click.echo()
            section("Aquilia Build Pipeline")
            kv("Mode", mode)
            kv("Compression", compression)
            kv("Output", output)
            if check_only:
                kv("Check Only", "yes")
            click.echo()

        result = AquiliaBuildPipeline.build(
            workspace_root=str(Path.cwd()),
            mode=mode,
            verbose=verbose,
            compression=compression,
            check_only=check_only,
            output_dir=output,
        )

        if not ctx.obj['quiet']:
            # Phase timings
            if verbose and result.phases:
                section("Phase Timings")
                for phase_name, ms in result.phases.items():
                    kv(f"  {phase_name}", f"{ms:.1f}ms")
                click.echo()

            # Warnings
            if result.warnings:
                for warn in result.warnings:
                    bullet(str(warn), fg="yellow")
                click.echo()

            if result.success:
                success(f"  {_CHECK} {result.summary()}")

                if result.bundle and not check_only:
                    section("Artifacts")
                    kv("Count", str(result.artifacts_count))
                    kv("Fingerprint", result.fingerprint[:16] + "…")
                    if result.bundle.bundle_path:
                        kv("Bundle", str(result.bundle.bundle_path))
                    for a in result.bundle.artifacts:
                        tree_item(f"{a.name}.crous ({a.size_bytes} bytes)")
            else:
                error(f"  {_CROSS} Build FAILED")
                click.echo()
                for err in result.errors:
                    bullet(str(err), fg="red")

                sys.exit(1)

    except ImportError as e:
        error(f"  {_CROSS} Build pipeline requires the 'crous' package: {e}")
        info("  Install with: pip install crous")
        sys.exit(1)
    except Exception as e:
        error(f"  {_CROSS} Build error: {e}")
        sys.exit(1)


@cli.group(cls=AquiliaGroup)
def manifest():
    """Manage module manifests."""
    pass


@manifest.command('update')
@click.argument('module')
@click.option('--check', is_flag=True, help='Fail if manifest is out of sync (CI mode)')
@click.option('--freeze', is_flag=True, help='Disable auto-discovery after Sync (Strict mode)')
@click.pass_context
def manifest_update(ctx, module: str, check: bool, freeze: bool):
    """
    Update manifest with auto-discovered resources.
    
    Scans the module for controllers and services, then explicitly
    writes them into manifest.py.
    
    Examples:
      aq manifest update mymod
      aq manifest update mymod --check   # For CI
      aq manifest update mymod --freeze  # For Prod
    """
    from .commands.manifest import update_manifest
    
    try:
        # Resolve workspace root (assume cwd)
        workspace_root = Path.cwd()
        
        update_manifest(
            module_name=module,
            workspace_root=workspace_root,
            check=check,
            freeze=freeze,
            verbose=ctx.obj['verbose'],
        )
        
    except Exception as e:
        error(f"  {_CROSS} Manifest update failed: {e}")
        sys.exit(1)


# Import and register add command group


@cli.group(cls=AquiliaGroup)
def inspect():
    """Inspect compiled artifacts."""
    pass


@inspect.command('routes')
@click.pass_context
def inspect_routes(ctx):
    """Show compiled routes."""
    from .commands.inspect import inspect_routes as _inspect_routes
    
    try:
        _inspect_routes(verbose=ctx.obj['verbose'])
    except Exception as e:
        error(f"  {_CROSS} Inspection failed: {e}")
        sys.exit(1)


@inspect.command('di')
@click.pass_context
def inspect_di(ctx):
    """Show DI graph."""
    from .commands.inspect import inspect_di as _inspect_di
    
    try:
        _inspect_di(verbose=ctx.obj['verbose'])
    except Exception as e:
        error(f"  {_CROSS} Inspection failed: {e}")
        sys.exit(1)


@inspect.command('modules')
@click.pass_context
def inspect_modules(ctx):
    """List all modules."""
    from .commands.inspect import inspect_modules as _inspect_modules
    
    try:
        _inspect_modules(verbose=ctx.obj['verbose'])
    except Exception as e:
        error(f"  {_CROSS} Inspection failed: {e}")
        sys.exit(1)


@inspect.command('faults')
@click.pass_context
def inspect_faults(ctx):
    """Show fault domains."""
    from .commands.inspect import inspect_faults as _inspect_faults
    
    try:
        _inspect_faults(verbose=ctx.obj['verbose'])
    except Exception as e:
        error(f"  {_CROSS} Inspection failed: {e}")
        sys.exit(1)


@inspect.command('config')
@click.pass_context
def inspect_config(ctx):
    """Show resolved configuration."""
    from .commands.inspect import inspect_config as _inspect_config
    
    try:
        _inspect_config(verbose=ctx.obj['verbose'])
    except Exception as e:
        error(f"  {_CROSS} Inspection failed: {e}")
        sys.exit(1)


@cli.command('migrate')
@click.argument('source', type=click.Choice(['legacy']))
@click.option('--dry-run', is_flag=True, help='Preview migration')
@click.pass_context
def migrate(ctx, source: str, dry_run: bool):
    """
    Migrate from Django-style layout.
    
    Examples:
      aq migrate legacy --dry-run
      aq migrate legacy
    """
    from .commands.migrate import migrate_legacy
    
    try:
        result = migrate_legacy(
            dry_run=dry_run,
            verbose=ctx.obj['verbose'],
        )
        
        if not ctx.obj['quiet']:
            click.echo()
            if dry_run:
                warning(f"  {_CHECK} Migration preview:")
            else:
                success(f"  {_CHECK} Migration complete:")
            
            for item in result.changes:
                bullet(str(item))
    
    except Exception as e:
        error(f"  {_CROSS} Migration failed: {e}")
        sys.exit(1)


@cli.command('doctor')
@click.pass_context
def doctor(ctx):
    """Diagnose workspace issues.

    Performs comprehensive health checks across all layers:
    environment, workspace structure, manifests, Aquilary pipeline,
    integrations, and deployment readiness.
    """
    from .commands.doctor import diagnose_workspace

    try:
        issues = diagnose_workspace(verbose=ctx.obj['verbose'])

        click.echo()
        if not issues:
            banner("Aquilia Doctor", subtitle=f"Workspace is healthy  {_CHECK}")
        else:
            warning(f"  Found {len(issues)} issue(s):")
            click.echo()
            section("Issues")
            for issue in issues:
                bullet(issue, fg="yellow")
            click.echo()
            next_steps([
                "Fix the issues above",
                "aq doctor -v  (verbose details)",
                "aq validate --strict  (full pipeline check)",
            ])

    except Exception as e:
        error(f"  {_CROSS} Diagnosis failed: {e}")
        sys.exit(1)


# ============================================================================
# WebSocket management
# ============================================================================

@cli.group(cls=AquiliaGroup)
def ws():
    """WebSocket management commands."""
    pass


@ws.command('inspect')
@click.option('--artifacts-dir', type=click.Path(), default='artifacts', help='Artifacts directory')
@click.pass_context
def ws_inspect(ctx, artifacts_dir: str):
    """Inspect compiled WebSocket namespaces."""
    from .commands.ws import cmd_ws_inspect
    try:
        cmd_ws_inspect({'artifacts_dir': artifacts_dir})
    except Exception as e:
        error(f"  {_CROSS} WS inspect failed: {e}")
        sys.exit(1)


@ws.command('broadcast')
@click.option('--namespace', required=True, help='Namespace')
@click.option('--room', default=None, help='Room (optional)')
@click.option('--event', required=True, help='Event name')
@click.option('--payload', default='{}', help='JSON payload')
@click.pass_context
def ws_broadcast(ctx, namespace: str, room: Optional[str], event: str, payload: str):
    """Broadcast message to namespace or room."""
    from .commands.ws import cmd_ws_broadcast
    try:
        cmd_ws_broadcast({'namespace': namespace, 'room': room, 'event': event, 'payload': payload})
    except Exception as e:
        error(f"  {_CROSS} WS broadcast failed: {e}")
        sys.exit(1)


@ws.command('gen-client')
@click.option('--lang', default='ts', help='Language (ts)')
@click.option('--out', required=True, help='Output file')
@click.option('--artifacts-dir', type=click.Path(), default='artifacts', help='Artifacts directory')
@click.pass_context
def ws_gen_client(ctx, lang: str, out: str, artifacts_dir: str):
    """Generate TypeScript client SDK from compiled WebSocket artifacts."""
    from .commands.ws import cmd_ws_gen_client
    try:
        cmd_ws_gen_client({'lang': lang, 'out': out, 'artifacts_dir': artifacts_dir})
    except Exception as e:
        error(f"  {_CROSS} WS gen-client failed: {e}")
        sys.exit(1)


@ws.command('purge-room')
@click.option('--namespace', required=True, help='Namespace')
@click.option('--room', required=True, help='Room to purge')
@click.option('--redis-url', default=None, help='Redis URL (optional)')
@click.pass_context
def ws_purge_room(ctx, namespace: str, room: str, redis_url: Optional[str]):
    """Purge a room's state from the adapter.

    Examples:\n      aq ws purge-room --namespace /chat --room room1
    """
    from .commands.ws import cmd_ws_purge_room
    try:
        cmd_ws_purge_room({'namespace': namespace, 'room': room, 'redis_url': redis_url})
    except Exception as e:
        error(f"  {_CROSS} WS purge-room failed: {e}")
        sys.exit(1)


@ws.command('kick')
@click.option('--conn', required=True, help='Connection ID to disconnect')
@click.option('--reason', default='kicked by admin', help='Reason for kick')
@click.option('--redis-url', default=None, help='Redis URL (optional)')
@click.pass_context
def ws_kick(ctx, conn: str, reason: str, redis_url: Optional[str]):
    """Kick (disconnect) a WebSocket connection.

    Examples:\n      aq ws kick --conn abc-123 --reason "violated rules"
    """
    from .commands.ws import cmd_ws_kick
    try:
        cmd_ws_kick({'conn': conn, 'reason': reason, 'redis_url': redis_url})
    except Exception as e:
        error(f"  {_CROSS} WS kick failed: {e}")
        sys.exit(1)


# ============================================================================
# Discovery
# ============================================================================

@cli.command('discover')
@click.option('--path', type=click.Path(), default=None, help='Workspace path')
@click.option('--sync', is_flag=True, help='Auto-sync discovered components into manifest.py files')
@click.option('--dry-run', is_flag=True, help='Preview sync changes without writing (use with --sync)')
@click.pass_context
def discover(ctx, path: Optional[str], sync: bool, dry_run: bool):
    """Inspect auto-discovered modules in workspace."""
    from .commands.discover import DiscoveryInspector

    try:
        workspace_root = Path(path) if path else Path.cwd()
        inspector = DiscoveryInspector(workspace_root.name, str(workspace_root))
        inspector.inspect(
            verbose=ctx.obj['verbose'],
            sync=sync,
            dry_run=dry_run,
        )
    except Exception as e:
        error(f"  {_CROSS} Discovery failed: {e}")
        sys.exit(1)


# ============================================================================
# Analytics
# ============================================================================

@cli.command('analytics')
@click.option('--path', type=click.Path(), default=None, help='Workspace path')
@click.pass_context
def analytics(ctx, path: Optional[str]):
    """Run discovery analytics and show health report."""
    from .commands.analytics import DiscoveryAnalytics, print_analysis_report

    try:
        workspace_root = Path(path) if path else Path.cwd()
        analyser = DiscoveryAnalytics(workspace_root.name, str(workspace_root))
        analysis = analyser.analyze()
        print_analysis_report(analysis)
    except Exception as e:
        error(f"  {_CROSS} Analytics failed: {e}")
        sys.exit(1)


# ============================================================================
# Mail
# ============================================================================

@cli.group(cls=AquiliaGroup)
def mail():
    """AquilaMail -- test, inspect, and validate mail configuration."""
    pass


@mail.command('check')
@click.pass_context
def mail_check(ctx):
    """
    Validate mail configuration and report issues.

    Examples:
      aq mail check
    """
    from .commands.mail import cmd_mail_check

    try:
        cmd_mail_check(verbose=ctx.obj['verbose'])
    except Exception as e:
        error(f"  {_CROSS} mail check failed: {e}")
        sys.exit(1)


@mail.command('send-test')
@click.argument('to')
@click.option('--subject', type=str, default=None, help='Email subject')
@click.option('--body', type=str, default=None, help='Email body')
@click.pass_context
def mail_send_test(ctx, to: str, subject: Optional[str], body: Optional[str]):
    """
    Send a test email to verify mail provider configuration.

    Examples:
      aq mail send-test user@example.com
      aq mail send-test user@example.com --subject="Hello"
    """
    from .commands.mail import cmd_mail_send_test

    try:
        cmd_mail_send_test(
            to=to,
            subject=subject,
            body=body,
            verbose=ctx.obj['verbose'],
        )
    except Exception as e:
        error(f"  {_CROSS} mail send-test failed: {e}")
        sys.exit(1)


@mail.command('inspect')
@click.pass_context
def mail_inspect(ctx):
    """
    Display current mail configuration as JSON.

    Examples:
      aq mail inspect
    """
    from .commands.mail import cmd_mail_inspect

    try:
        cmd_mail_inspect(verbose=ctx.obj['verbose'])
    except Exception as e:
        error(f"  {_CROSS} mail inspect failed: {e}")
        sys.exit(1)


# ============================================================================
# Cache
# ============================================================================

@cli.group(cls=AquiliaGroup)
def cache():
    """AquilaCache -- check, inspect, clear, and view cache stats."""
    pass


@cache.command('check')
@click.pass_context
def cache_check(ctx):
    """
    Validate cache configuration and test backend connectivity.

    Examples:
      aq cache check
    """
    from .commands.cache import cmd_cache_check

    try:
        cmd_cache_check(verbose=ctx.obj['verbose'])
    except Exception as e:
        error(f"  {_CROSS} cache check failed: {e}")
        sys.exit(1)


@cache.command('inspect')
@click.pass_context
def cache_inspect(ctx):
    """
    Display current cache configuration as JSON.

    Examples:
      aq cache inspect
    """
    from .commands.cache import cmd_cache_inspect

    try:
        cmd_cache_inspect(verbose=ctx.obj['verbose'])
    except Exception as e:
        error(f"  {_CROSS} cache inspect failed: {e}")
        sys.exit(1)


@cache.command('stats')
@click.pass_context
def cache_stats(ctx):
    """
    Display cache statistics from trace diagnostics.

    Examples:
      aq cache stats
    """
    from .commands.cache import cmd_cache_stats

    try:
        cmd_cache_stats(verbose=ctx.obj['verbose'])
    except Exception as e:
        error(f"  {_CROSS} cache stats failed: {e}")
        sys.exit(1)


@cache.command('clear')
@click.option('--namespace', '-n', type=str, default=None, help='Clear only this namespace')
@click.pass_context
def cache_clear(ctx, namespace: Optional[str]):
    """
    Clear all or namespace-scoped cache entries.

    Examples:
      aq cache clear
      aq cache clear --namespace http
    """
    from .commands.cache import cmd_cache_clear

    try:
        cmd_cache_clear(namespace=namespace, verbose=ctx.obj['verbose'])
    except Exception as e:
        error(f"  {_CROSS} cache clear failed: {e}")
        sys.exit(1)


# ============================================================================
# Database / Models
# ============================================================================

@cli.group(cls=AquiliaGroup)
def db():
    """Database and model ORM commands."""
    pass


@db.command('makemigrations')
@click.option('--app', type=str, default=None, help='Restrict to specific module/app')
@click.option('--migrations-dir', type=click.Path(), default='migrations', help='Migrations directory')
@click.option('--dsl/--no-dsl', default=True, help='Use new DSL format (default: True)')
@click.option('--format', 'fmt', type=click.Choice(['python', 'crous']), default='crous',
              help='Migration file format — crous (binary, default) or python')
@click.pass_context
def db_makemigrations(ctx, app: Optional[str], migrations_dir: str, dsl: bool, fmt: str):
    """
    Generate migration files from Python Model definitions.

    Uses CROUS binary format by default for compact, efficient migration
    storage.  Pass ``--format=python`` for human-readable DSL files.

    Examples:
      aq db makemigrations
      aq db makemigrations --app=products
      aq db makemigrations --format=python
      aq db makemigrations --no-dsl    # Legacy raw-SQL format
    """
    from .commands.model_cmds import cmd_makemigrations

    try:
        cmd_makemigrations(
            app=app,
            migrations_dir=migrations_dir,
            verbose=ctx.obj['verbose'],
            use_dsl=dsl,
            migration_format=fmt,
        )
    except Exception as e:
        error(f"  {_CROSS} makemigrations failed: {e}")
        sys.exit(1)


@db.command('migrate')
@click.option('--migrations-dir', type=click.Path(), default='migrations', help='Migrations directory')
@click.option('--database-url', type=str, default=None, help='Database URL (auto-detected from workspace.py)')
@click.option('--database', type=str, default=None, help='Database alias (for multi-db)')
@click.option('--target', type=str, default=None, help='Target revision (or "zero" to rollback all)')
@click.option('--fake', is_flag=True, help='Mark migrations as applied without running SQL')
@click.option('--plan', is_flag=True, help='Preview SQL without executing (dry-run)')
@click.pass_context
def db_migrate(ctx, migrations_dir: str, database_url: Optional[str], database: Optional[str],
               target: Optional[str], fake: bool, plan: bool):
    """
    Apply pending migrations to the database.

    The database URL is auto-detected from workspace.py if not specified.

    Examples:
      aq db migrate
      aq db migrate --database-url=sqlite:///prod.db
      aq db migrate --fake                # Mark as applied without running
      aq db migrate --plan                # Preview SQL only
      aq db migrate --target=zero
    """
    from .commands.model_cmds import cmd_migrate

    # Auto-detect database URL from workspace.py if not provided
    if database_url is None:
        database_url = _detect_workspace_db_url()

    try:
        cmd_migrate(
            migrations_dir=migrations_dir,
            database_url=database_url,
            target=target,
            verbose=ctx.obj['verbose'],
            fake=fake,
            plan=plan,
            database=database,
        )
    except Exception as e:
        error(f"  {_CROSS} migrate failed: {e}")
        sys.exit(1)


@db.command('dump')
@click.option('--emit', type=click.Choice(['python', 'sql']), default='python', help='Output format')
@click.option('--output-dir', type=click.Path(), default=None, help='Output directory')
@click.pass_context
def db_dump(ctx, emit: str, output_dir: Optional[str]):
    """
    Dump model schema — annotated Python overview or raw SQL DDL.

    Examples:
      aq db dump
      aq db dump --emit=sql
      aq db dump --output-dir=generated/
    """
    from .commands.model_cmds import cmd_model_dump

    try:
        cmd_model_dump(
            emit=emit,
            output_dir=output_dir,
            verbose=ctx.obj['verbose'],
        )
    except Exception as e:
        error(f"  {_CROSS} dump failed: {e}")
        sys.exit(1)


@db.command('shell')
@click.option('--database-url', type=str, default=None, help='Database URL (auto-detected from workspace.py)')
@click.pass_context
def db_shell(ctx, database_url: Optional[str]):
    """
    Open an async REPL with models pre-loaded.

    All discovered Model classes, Q query builder, and ModelRegistry
    are available in the shell namespace.

    Examples:
      aq db shell
      aq db shell --database-url=sqlite:///prod.db
    """
    from .commands.model_cmds import cmd_shell

    if database_url is None:
        database_url = _detect_workspace_db_url()

    try:
        cmd_shell(
            database_url=database_url,
            verbose=ctx.obj['verbose'],
        )
    except Exception as e:
        error(f"  {_CROSS} shell failed: {e}")
        sys.exit(1)


@db.command('inspectdb')
@click.option('--database-url', type=str, default=None, help='Database URL (auto-detected from workspace.py)')
@click.option('--table', type=str, multiple=True, help='Specific tables to inspect')
@click.option('--output', type=click.Path(), default=None, help='Output file path')
@click.pass_context
def db_inspectdb(ctx, database_url: Optional[str], table: tuple, output: Optional[str]):
    """
    Introspect database and generate Model definitions.

    Reads the database schema and emits Python Model class
    definitions that mirror the existing tables.

    Examples:
      aq db inspectdb
      aq db inspectdb --table=users --table=orders
      aq db inspectdb --output=models/generated.py
    """
    from .commands.model_cmds import cmd_inspectdb

    if database_url is None:
        database_url = _detect_workspace_db_url()

    try:
        tables = list(table) if table else None
        result = cmd_inspectdb(
            database_url=database_url,
            tables=tables,
            verbose=ctx.obj['verbose'],
        )
        if output and result:
            Path(output).parent.mkdir(parents=True, exist_ok=True)
            Path(output).write_text(result, encoding="utf-8")
            click.echo(click.style(f"  {_CHECK} Models written to {output}", fg="green"))
    except Exception as e:
        error(f"  {_CROSS} inspectdb failed: {e}")
        sys.exit(1)


@db.command('showmigrations')
@click.option('--migrations-dir', type=click.Path(), default='migrations', help='Migrations directory')
@click.option('--database-url', type=str, default=None, help='Database URL (auto-detected from workspace.py)')
@click.option('--database', type=str, default=None, help='Database alias')
@click.pass_context
def db_showmigrations(ctx, migrations_dir: str, database_url: Optional[str], database: Optional[str]):
    """
    Show all migrations and their applied/pending status.

    Examples:
      aq db showmigrations
      aq db showmigrations --migrations-dir=db/migrations
    """
    from .commands.model_cmds import cmd_showmigrations

    if database_url is None:
        database_url = _detect_workspace_db_url()

    try:
        cmd_showmigrations(
            migrations_dir=migrations_dir,
            database_url=database_url,
            verbose=ctx.obj['verbose'],
        )
    except Exception as e:
        error(f"  {_CROSS} showmigrations failed: {e}")
        sys.exit(1)


@db.command('sqlmigrate')
@click.argument('migration_name')
@click.option('--migrations-dir', type=click.Path(), default='migrations', help='Migrations directory')
@click.option('--database', type=str, default=None, help='Database alias')
@click.pass_context
def db_sqlmigrate(ctx, migration_name: str, migrations_dir: str, database: Optional[str]):
    """
    Display SQL statements for a specific migration.

    Supports both DSL and legacy migrations. For DSL migrations,
    compiles operations to SQL for the target backend.

    Examples:
      aq db sqlmigrate 20260217_210454
      aq db sqlmigrate 0002 --migrations-dir=db/migrations
    """
    from .commands.model_cmds import cmd_sqlmigrate

    try:
        cmd_sqlmigrate(
            migration_name=migration_name,
            migrations_dir=migrations_dir,
            verbose=ctx.obj['verbose'],
        )
    except Exception as e:
        error(f"  {_CROSS} sqlmigrate failed: {e}")
        sys.exit(1)


@db.command('status')
@click.option('--database-url', type=str, default=None, help='Database URL (auto-detected from workspace.py)')
@click.pass_context
def db_status(ctx, database_url: Optional[str]):
    """
    Show database status — tables, row counts, columns.

    Examples:
      aq db status
      aq db status --database-url=sqlite:///prod.db
    """
    from .commands.model_cmds import cmd_db_status

    if database_url is None:
        database_url = _detect_workspace_db_url()

    try:
        cmd_db_status(
            database_url=database_url,
            verbose=ctx.obj['verbose'],
        )
    except Exception as e:
        error(f"  {_CROSS} status failed: {e}")
        sys.exit(1)


# ============================================================================
# MLOps commands
# ============================================================================

from .commands.mlops_cmds import (
    pack_group,
    model_group,
    deploy_group,
    observe_group,
    export_group,
    plugin_group,
    lineage_group,
    experiment_group,
)

cli.add_command(pack_group)
cli.add_command(model_group)
cli.add_command(deploy_group)
cli.add_command(observe_group)
cli.add_command(export_group)
cli.add_command(plugin_group)
cli.add_command(lineage_group)
cli.add_command(experiment_group)


# ============================================================================
# Artifact commands
# ============================================================================

from .commands.artifacts import artifact_group

cli.add_command(artifact_group)


# ============================================================================
# Deploy / Production file generators
# ============================================================================

from .commands.deploy_gen import deploy_gen_group

cli.add_command(deploy_gen_group)


# ============================================================================
# Test command
# ============================================================================

@cli.command('test')
@click.argument('paths', nargs=-1, type=click.Path())
@click.option('-k', '--pattern', type=str, default=None, help='Only run tests matching pattern')
@click.option('-m', '--markers', type=str, default=None, help='Only run tests matching markers')
@click.option('--coverage', is_flag=True, help='Collect coverage')
@click.option('--coverage-html', is_flag=True, help='Generate HTML coverage report')
@click.option('--failfast', '-x', is_flag=True, help='Stop on first failure')
@click.pass_context
def test(ctx, paths: tuple, pattern: Optional[str], markers: Optional[str],
         coverage: bool, coverage_html: bool, failfast: bool):
    """
    Run the test suite with Aquilia-aware defaults.

    Sets AQUILIA_ENV=test, auto-discovers test directories,
    and configures pytest-asyncio.

    Examples:
      aq test
      aq test tests/test_users.py
      aq test -k "test_login"
      aq test --coverage
      aq test --failfast -v
    """
    from .commands.test import run_tests

    exit_code = run_tests(
        paths=list(paths) if paths else None,
        pattern=pattern,
        verbose=ctx.obj.get('verbose', False),
        coverage=coverage,
        coverage_html=coverage_html,
        failfast=failfast,
        markers=markers,
    )
    sys.exit(exit_code)


# ============================================================================
# Admin commands
# ============================================================================

@cli.group(cls=AquiliaGroup)
def admin():
    """Admin dashboard management."""
    pass


@admin.command('createsuperuser')
@click.option('--username', prompt='Username', help='Admin username')
@click.option('--password', prompt='Password', hide_input=True, confirmation_prompt=True, help='Admin password')
@click.option('--email', prompt='Email', default='', help='Admin email (optional)')
@click.pass_context
def admin_createsuperuser(ctx, username: str, password: str, email: str):
    """
    Create an admin superuser in the database.

    Stores credentials securely using Argon2id/PBKDF2 password hashing
    in the admin_users table (Django-like architecture).

    Requires ``aq db migrate`` to have been run first to create the
    admin_users table.

    Examples:
      aq admin createsuperuser
      aq admin createsuperuser --username=admin --password=secret
    """
    import asyncio

    async def _create():
        # Connect to the database and register with ORM
        database_url = _detect_workspace_db_url()
        try:
            from aquilia.db.engine import configure_database
            db = configure_database(database_url)
            await db.connect()
        except Exception:
            db = None

        try:
            from aquilia.admin.models import (
                AdminUser,
                ContentType,
                AdminPermission,
                AdminGroup,
                AdminLogEntry,
                AdminSession,
            )

            if db is None:
                raise RuntimeError(
                    "No database connection available. "
                    "Run 'aq db migrate' first to set up the database."
                )

            # Auto-ensure admin tables exist (safety net).
            # The admin models live in the framework, not the workspace,
            # so users may not have run makemigrations for them yet.
            _admin_models = [
                ContentType,
                AdminPermission,
                AdminGroup,
                AdminUser,
                AdminLogEntry,
                AdminSession,
            ]
            for _model in _admin_models:
                try:
                    create_sql = _model.generate_create_table_sql()
                    await db.execute(create_sql)
                    # Create indexes
                    for idx_sql in _model.generate_index_sql():
                        await db.execute(idx_sql)
                    # Create M2M tables
                    for m2m_sql in _model.generate_m2m_sql():
                        await db.execute(m2m_sql)
                except Exception:
                    pass  # Table already exists — that's fine

            # ORM-based creation
            try:
                user = await AdminUser.create_superuser(
                    username=username,
                    password=password,
                    email=email,
                )
                return True, str(getattr(user, 'pk', '?'))
            except Exception as e:
                raise RuntimeError(
                    f"Failed to create superuser: {e}\n"
                    "Ensure 'aq db makemigrations' and 'aq db migrate' have been run first."
                ) from e
        finally:
            if db is not None:
                try:
                    await db.disconnect()
                except Exception:
                    pass

    try:
        ok, pk_info = asyncio.run(_create())
    except Exception as e:
        error(f"  {_CROSS} {e}")
        sys.exit(1)

    if not ctx.obj.get('quiet'):
        click.echo()
        success(f"  {_CHECK} Superuser '{username}' created")
        click.echo()
        section("Admin Setup")
        kv("Username", username)
        kv("Email", email or "(none)")
        kv("Storage", "Database (admin_users table)")
        kv("Password", "Hashed with Argon2id/PBKDF2")
        click.echo()
        next_steps([
            "aq run",
            f"Visit http://localhost:8000/admin/ and log in as '{username}'",
        ])


@admin.command('status')
@click.option('--database-url', type=str, default=None, help='Database URL')
@click.pass_context
def admin_status(ctx, database_url: Optional[str]):
    """
    Show admin dashboard status and registered models.

    Examples:
      aq admin status
    """
    from aquilia.admin import AdminSite, autodiscover

    if database_url is None:
        database_url = _detect_workspace_db_url()

    site = AdminSite.default()
    site.initialize()
    autodiscover()

    if not ctx.obj.get('quiet'):
        click.echo()
        banner("AquilAdmin", subtitle="Dashboard Status")
        click.echo()

        section("Registered Models")
        models = site.get_registered_models()
        if models:
            for model_name, admin_obj in sorted(models.items()):
                admin_class_name = admin_obj.__class__.__name__
                display_fields = ", ".join(admin_obj.get_list_display()[:5])
                kv(f"  {model_name}", f"{admin_class_name}  fields=[{display_fields}]")
        else:
            info("  No models registered. Run autodiscover() in workspace.py")
        click.echo()

        section("Configuration")
        kv("Admin Auth", "Database (admin_users table)")
        kv("Dashboard URL", "/admin/")
        kv("Audit Log", f"{site.audit_log.count()} entries")
        click.echo()


@admin.command('audit')
@click.option('--limit', type=int, default=50, help='Number of entries to show')
@click.option('--action', type=str, default=None, help='Filter by action type')
@click.option('--user', type=str, default=None, help='Filter by username')
@click.pass_context
def admin_audit(ctx, limit: int, action: Optional[str], user: Optional[str]):
    """
    View admin audit trail.

    Examples:
      aq admin audit
      aq admin audit --limit=100
      aq admin audit --action=CREATE
      aq admin audit --user=admin
    """
    from aquilia.admin import AdminSite, AdminAction

    site = AdminSite.default()

    filter_action = None
    if action:
        try:
            filter_action = AdminAction(action.lower())
        except ValueError:
            error(f"  {_CROSS} Unknown action: {action}")
            click.echo(f"  Valid actions: {', '.join(a.value for a in AdminAction)}")
            sys.exit(1)

    entries = site.audit_log.get_entries(
        limit=limit,
        action=filter_action,
        user_id=user,
    )

    if not ctx.obj.get('quiet'):
        click.echo()
        section(f"Admin Audit Trail ({len(entries)} entries)")
        click.echo()

        if not entries:
            info("  No audit entries found")
        else:
            for entry in entries:
                ts = entry.timestamp.strftime("%Y-%m-%d %H:%M:%S")
                status_icon = _CHECK if entry.success else _CROSS
                model_info = f" on {entry.model_name}" if entry.model_name else ""
                click.echo(
                    f"  {dim(ts)}  {status_icon}  "
                    f"{bold(entry.action.value.upper())}{model_info}  "
                    f"by {accent(entry.username)}"
                )
                if entry.error_message:
                    click.echo(f"           {error(entry.error_message)}")
        click.echo()


def main():
    """Entry point for `aq` command."""
    cli(obj={})


if __name__ == '__main__':
    main()
