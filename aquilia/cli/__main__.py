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
@click.option('--verbose', '-v', is_flag=True, help='Verbose output (show debug details, full tracebacks)')
@click.option('--quiet', '-q', is_flag=True, help='Minimal output (suppress banners & decorations)')
@click.option('--debug', is_flag=True, help='Enable debug mode (full stack traces on errors)')
@click.option('--no-color', is_flag=True, help='Disable coloured output')
@click.pass_context
def cli(ctx, verbose: bool, quiet: bool, debug: bool, no_color: bool):
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
    ctx.obj['debug'] = debug
    ctx.obj['no_color'] = no_color

    # Disable click/ANSI colour if requested
    if no_color:
        ctx.color = False

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
@click.option('--json', 'as_json', is_flag=True, help='Output results as JSON')
@click.pass_context
def validate(ctx, strict: bool, module: Optional[str], as_json: bool):
    """
    Validate workspace manifests.
    
    Examples:
      aq validate
      aq validate --strict
      aq validate --module=users
      aq validate --json
    """
    from .commands.validate import validate_workspace
    
    try:
        result = validate_workspace(
            strict=strict,
            module_filter=module,
            verbose=ctx.obj['verbose'],
        )

        if as_json:
            import json as _json
            click.echo(_json.dumps({
                "valid": result.is_valid,
                "modules": result.module_count,
                "routes": result.route_count,
                "providers": result.provider_count,
                "fingerprint": str(result.fingerprint)[:24] if result.fingerprint else None,
                "faults": result.faults if hasattr(result, 'faults') else [],
                "warnings": result.warnings if hasattr(result, 'warnings') else [],
            }, indent=2))
            if not result.is_valid:
                sys.exit(1)
            return
        
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
@click.option('--skip-checks', is_flag=True, help='Skip pre-flight dependency checks')
@click.pass_context
def run(ctx, mode: str, port: int, host: str, reload: bool, skip_checks: bool):
    """
    Start development server.

    Runs admin pre-flight checks automatically when admin integration
    is detected in workspace.py. Use --skip-checks to bypass.

    Examples:
      aq run
      aq run --port=3000
      aq run --mode=test --no-reload
      aq run --skip-checks
    """
    from .commands.run import run_dev_server

    # ── Admin pre-flight checks ──────────────────────────────────────
    if not skip_checks:
        workspace_file = Path("workspace.py")
        if workspace_file.exists():
            ws_content = workspace_file.read_text()
            active_lines = "\n".join(
                line for line in ws_content.splitlines()
                if not line.strip().startswith("#")
            )
            if "Integration.admin(" in active_lines:
                # Check session support
                has_sessions = (
                    ".sessions(" in active_lines
                    or "Integration.sessions(" in active_lines
                    or "Integration.auth(" in active_lines
                )
                if not has_sessions:
                    click.echo()
                    warning(
                        f"  ! Admin integration detected but sessions are NOT configured.\n"
                        f"    Admin login will NOT work without session support.\n"
                        f"    Run 'aq admin setup' to auto-configure everything.\n"
                        f"    Or:  'aq admin check' for full diagnostics.\n"
                        f"    Use --skip-checks to suppress this warning."
                    )
                    click.echo()

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
@click.option('--json', 'as_json', is_flag=True, help='Output results as JSON')
@click.pass_context
def doctor(ctx):
    """Diagnose workspace issues.

    Performs comprehensive health checks across all layers:
    environment, workspace structure, manifests, Aquilary pipeline,
    integrations, and deployment readiness.

    Examples:
      aq doctor
      aq doctor -v
      aq doctor --json
    """
    from .commands.doctor import diagnose_workspace

    try:
        issues = diagnose_workspace(verbose=ctx.obj['verbose'])

        if as_json:
            import json as _json
            click.echo(_json.dumps({
                "healthy": len(issues) == 0,
                "issue_count": len(issues),
                "issues": issues,
            }, indent=2))
            return

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
        if ctx.obj.get('debug'):
            import traceback
            traceback.print_exc()
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
@click.option('--json', 'as_json', is_flag=True, help='Output results as JSON')
@click.pass_context
def discover(ctx, path: Optional[str], sync: bool, dry_run: bool, as_json: bool):
    """Inspect auto-discovered modules in workspace.

    Examples:
      aq discover
      aq discover --sync
      aq discover --sync --dry-run
      aq discover --json
    """
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
        if ctx.obj.get('debug'):
            import traceback
            traceback.print_exc()
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
    """Admin dashboard management and diagnostics."""
    pass


@admin.command('check')
@click.option('--fix', is_flag=True, help='Auto-fix missing configuration by uncommenting workspace.py sections')
@click.option('--json', 'as_json', is_flag=True, help='Output results as JSON')
@click.pass_context
def admin_check(ctx, fix: bool, as_json: bool):
    """
    Pre-flight check for admin dashboard dependencies.

    Validates that all required integrations (sessions, database,
    static files, templates) are properly configured in workspace.py
    before starting the server.

    Run this BEFORE 'aq run' to catch configuration issues early.

    Examples:
      aq admin check
      aq admin check --fix
      aq admin check --json
    """
    workspace_file = Path("workspace.py")
    if not workspace_file.exists():
        error(f"  {_CROSS} workspace.py not found")
        sys.exit(1)

    content = workspace_file.read_text()

    # Remove comment-only lines for active config detection
    active_lines = "\n".join(
        line for line in content.splitlines()
        if not line.strip().startswith("#")
    )

    checks: list[dict] = []

    # 1. Admin integration enabled?
    admin_enabled = "Integration.admin(" in active_lines
    checks.append({
        "name": "Admin Integration",
        "status": "ok" if admin_enabled else "fail",
        "detail": "Integration.admin() is configured" if admin_enabled else (
            "Integration.admin() not found in workspace.py. "
            "Add: .integrate(Integration.admin(url_prefix='/admin', auto_discover=True))"
        ),
    })

    if not admin_enabled:
        # No point checking dependencies if admin isn't even enabled
        if as_json:
            import json as _json
            click.echo(_json.dumps({"passed": False, "checks": checks}, indent=2))
        else:
            click.echo()
            banner("AquilAdmin", subtitle="Pre-flight Check")
            click.echo()
            error(f"  {_CROSS} Admin integration is not enabled in workspace.py")
            click.echo()
            next_steps([
                "Add .integrate(Integration.admin(...)) to workspace.py",
                "aq admin check",
            ])
        sys.exit(1)

    # 2. Sessions enabled?
    sessions_active = (
        ".sessions(" in active_lines
        or "Integration.sessions(" in active_lines
    )
    auth_active = "Integration.auth(" in active_lines
    has_session_support = sessions_active or auth_active
    checks.append({
        "name": "Sessions",
        "status": "ok" if has_session_support else "fail",
        "detail": (
            ("Sessions via .sessions()" if sessions_active else "Sessions via Integration.auth()")
            if has_session_support else (
                "Sessions are NOT configured. Admin login requires sessions. "
                "Uncomment .sessions(...) in workspace.py or enable Integration.auth()"
            )
        ),
    })

    # 3. Database configured?
    db_active = "Integration.database(" in active_lines
    db_has_url = bool(_re.search(r'url\s*=\s*["\']', active_lines))
    if db_active and db_has_url:
        db_status = "ok"
        db_detail = "Database integration with URL configured"
    elif db_active:
        db_status = "warn"
        db_detail = "Database integration enabled but no URL specified (using default sqlite)"
    else:
        db_status = "warn"
        db_detail = "No database integration found. Admin users are stored in admin_users table"
    checks.append({"name": "Database", "status": db_status, "detail": db_detail})

    # 4. Static files configured?
    static_active = "Integration.static_files(" in active_lines
    checks.append({
        "name": "Static Files",
        "status": "ok" if static_active else "warn",
        "detail": (
            "Static files middleware configured"
            if static_active else
            "Static files not configured. Admin CSS/JS may not load. "
            "Add: .integrate(Integration.static_files(directories={\"/static\": \"static\"}))"
        ),
    })

    # 5. Templates configured?
    templates_active = "Integration.templates" in active_lines or "templates" in active_lines.lower()
    checks.append({
        "name": "Templates",
        "status": "ok" if templates_active else "info",
        "detail": (
            "Template engine configured"
            if templates_active else
            "Template engine not explicitly configured (admin uses built-in renderer)"
        ),
    })

    # 6. Superuser exists?
    has_superuser = False
    su_detail = "Unknown (cannot check without database connection)"
    try:
        import asyncio as _aio
        database_url = _detect_workspace_db_url()

        async def _check_su():
            from aquilia.db.engine import configure_database
            db = configure_database(database_url)
            await db.connect()
            try:
                result = await db.fetch_one("SELECT COUNT(*) as cnt FROM admin_users WHERE is_superuser = 1")
                return result["cnt"] if result else 0
            finally:
                await db.disconnect()

        count = _aio.run(_check_su())
        has_superuser = count > 0
        su_detail = f"{count} superuser(s) found" if has_superuser else (
            "No superusers found. Run: aq admin createsuperuser"
        )
    except Exception:
        su_detail = "Could not check (database not accessible or table missing). Run: aq db migrate && aq admin createsuperuser"
    checks.append({
        "name": "Superuser",
        "status": "ok" if has_superuser else "warn",
        "detail": su_detail,
    })

    # 7. assets/ directory exists?
    assets_dir = Path("assets")
    has_assets = assets_dir.is_dir()
    checks.append({
        "name": "Admin Assets",
        "status": "ok" if has_assets else "info",
        "detail": (
            f"assets/ directory found ({len(list(assets_dir.iterdir()))} files)"
            if has_assets else
            "assets/ directory not found (admin will use default styles)"
        ),
    })

    # ── Output ───────────────────────────────────────────────────────
    all_passed = all(c["status"] in ("ok", "info") for c in checks)
    has_failures = any(c["status"] == "fail" for c in checks)

    if as_json:
        import json as _json
        click.echo(_json.dumps({
            "passed": all_passed,
            "has_failures": has_failures,
            "checks": checks,
        }, indent=2))
    else:
        click.echo()
        banner("AquilAdmin", subtitle="Pre-flight Check")
        click.echo()

        _status_icons = {"ok": _CHECK, "fail": _CROSS, "warn": "!", "info": _BULLET}
        _status_colors = {"ok": "green", "fail": "red", "warn": "yellow", "info": "cyan"}

        for c in checks:
            icon = _status_icons.get(c["status"], "?")
            color = _status_colors.get(c["status"], "white")
            name_styled = click.style(f"{c['name']}:", bold=True)
            icon_styled = click.style(f"  {icon}", fg=color)
            click.echo(f"{icon_styled} {name_styled}")
            if ctx.obj.get('verbose') or c["status"] in ("fail", "warn"):
                dim(f"      {c['detail']}")

        click.echo()
        if has_failures:
            error(f"  {_CROSS} Pre-flight check FAILED — fix the errors above before running aq run")
            click.echo()
            if not has_session_support:
                panel(
                    [
                        "The admin dashboard requires session support.",
                        "",
                        "  Quick fix:   aq admin setup",
                        "  Manual fix:  Uncomment .sessions(...) in workspace.py",
                        "",
                        "  Or add this to your workspace.py:",
                        "",
                        "    from datetime import timedelta",
                        "    from aquilia.sessions import SessionPolicy",
                        "",
                        "    .sessions(",
                        "        policies=[",
                        '            SessionPolicy(name="default",',
                        "                ttl=timedelta(days=7),",
                        "                idle_timeout=timedelta(hours=1),",
                        "            ),",
                        "        ],",
                        "    )",
                    ],
                    title="Required: Enable Sessions",
                    fg="yellow",
                )
            sys.exit(1)
        elif any(c["status"] == "warn" for c in checks):
            warning(f"  ! Pre-flight check passed with warnings")
        else:
            success(f"  {_CHECK} All pre-flight checks passed")
        click.echo()

    # ── Auto-fix ─────────────────────────────────────────────────────
    if fix and not has_session_support:
        # Uncomment the .sessions(...) block
        if "# .sessions(" in content:
            fixed = content.replace("# .sessions(", ".sessions(")
            # Uncomment lines within the sessions block
            lines = fixed.splitlines()
            in_sessions_block = False
            fixed_lines = []
            for line in lines:
                stripped = line.lstrip()
                if ".sessions(" in line and not stripped.startswith("#"):
                    in_sessions_block = True
                    fixed_lines.append(line)
                    continue
                if in_sessions_block:
                    if stripped.startswith("# ") and (
                        "policies=" in stripped
                        or "SessionPolicy" in stripped
                        or "ttl=" in stripped
                        or "idle_timeout=" in stripped
                        or "]," in stripped
                        or ")," in stripped
                        or ")" in stripped
                    ):
                        # Uncomment
                        fixed_lines.append(line.replace("# ", "", 1))
                    else:
                        fixed_lines.append(line)
                    if stripped.rstrip().endswith(")") and "SessionPolicy" not in stripped:
                        in_sessions_block = False
                else:
                    fixed_lines.append(line)

            workspace_file.write_text("\n".join(fixed_lines))
            success(f"  {_CHECK} Auto-fixed: Uncommented .sessions(...) in workspace.py")
            click.echo()
            next_steps([
                "Review workspace.py to verify the sessions config",
                "aq admin check",
                "aq run",
            ])


@admin.command('createsuperuser')
@click.option('--username', prompt=click.style('  Username', fg='cyan', bold=True), help='Admin username')
@click.option('--email', prompt=click.style('  Email', fg='cyan', bold=True), help='Admin email (required)')
@click.option('--password', prompt=click.style('  Password', fg='cyan', bold=True), hide_input=True, confirmation_prompt=click.style('  Confirm password', fg='cyan', bold=True), help='Admin password')
@click.option('--no-input', is_flag=True, hidden=True, help='Non-interactive mode (requires all options)')
@click.pass_context
def admin_createsuperuser(ctx, username: str, email: str, password: str, no_input: bool):
    """
    Create an admin superuser in the database.

    Stores credentials securely using Argon2id/PBKDF2 password hashing
    in the admin_users table (Django-like architecture).

    Requires ``aq db migrate`` to have been run first to create the
    admin_users table.

    Examples:
      aq admin createsuperuser
      aq admin createsuperuser --username=admin --email=admin@site.com --password=secret
    """
    import asyncio
    import time as _ctime

    # ── Validate inputs ──────────────────────────────────────────────
    click.echo()
    banner("Aquilia", subtitle="Admin Superuser Setup")
    click.echo()

    # Validate username
    if not username or len(username.strip()) < 2:
        error(f"  {_CROSS} Username must be at least 2 characters")
        sys.exit(1)

    # Validate email is provided and looks valid
    if not email or "@" not in email or "." not in email.split("@")[-1]:
        error(f"  {_CROSS} A valid email address is required")
        sys.exit(1)

    # Validate password strength
    if len(password) < 4:
        error(f"  {_CROSS} Password must be at least 4 characters")
        sys.exit(1)

    section("Credentials")
    kv("Username", username)
    kv("Email", email)
    kv("Password", click.style("*" * len(password), dim=True))
    click.echo()

    # ── Create superuser ─────────────────────────────────────────────
    step(1, "Connecting to database...")

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

    t0 = _ctime.monotonic()
    try:
        ok, pk_info = asyncio.run(_create())
    except Exception as e:
        click.echo()
        error(f"  {_CROSS} {e}")
        click.echo()
        panel(
            [
                "Troubleshooting:",
                "",
                "1. Ensure the database is running",
                "2. Run: aq db makemigrations",
                "3. Run: aq db migrate",
                "4. Then retry: aq admin createsuperuser",
            ],
            title="Help",
            fg="red",
        )
        sys.exit(1)

    elapsed = (_ctime.monotonic() - t0) * 1000

    if not ctx.obj.get('quiet'):
        step(2, "Hashing password with Argon2id/PBKDF2...")
        step(3, "Writing to admin_users table...")
        click.echo()

        # ── Success banner ───────────────────────────────────────────
        success(f"  {_CHECK} Superuser created successfully!")
        click.echo()

        # ── Details panel ────────────────────────────────────────────
        section("Account Details")
        kv("Username", username)
        kv("Email", email)
        kv("Role", click.style("superadmin", fg="magenta", bold=True))
        kv("Storage", "Database (admin_users table)")
        kv("Password", "Hashed (Argon2id/PBKDF2)")
        kv("Created in", f"{elapsed:.0f}ms")
        click.echo()

        # ── Permissions ──────────────────────────────────────────────
        section("Permissions")
        bullet("Full admin dashboard access", fg="green")
        bullet("Create, read, update, delete all models", fg="green")
        bullet("Manage users, groups, and permissions", fg="green")
        bullet("View audit logs", fg="green")
        click.echo()

        # ── Next steps ───────────────────────────────────────────────
        next_steps([
            "aq admin check",
            "aq run",
            f"Visit http://localhost:8000/admin/",
            f"Log in with username '{username}' and your password",
        ])


@admin.command('listusers')
@click.option('--database-url', type=str, default=None, help='Database URL')
@click.option('--json', 'as_json', is_flag=True, help='Output as JSON')
@click.option('--active-only', is_flag=True, help='Show only active users')
@click.pass_context
def admin_listusers(ctx, database_url: Optional[str], as_json: bool, active_only: bool):
    """
    List all admin users.

    Examples:
      aq admin listusers
      aq admin listusers --json
      aq admin listusers --active-only
    """
    import asyncio

    if database_url is None:
        database_url = _detect_workspace_db_url()

    async def _list():
        from aquilia.db.engine import configure_database
        db = configure_database(database_url)
        await db.connect()
        try:
            query = "SELECT id, username, email, is_active, is_superuser, is_staff, date_joined, last_login FROM admin_users"
            if active_only:
                query += " WHERE is_active = 1"
            query += " ORDER BY date_joined DESC"
            rows = await db.fetch_all(query)
            return [dict(r) for r in rows]
        finally:
            await db.disconnect()

    try:
        users = asyncio.run(_list())
    except Exception as e:
        error(f"  {_CROSS} Failed to list users: {e}")
        if ctx.obj.get('verbose'):
            import traceback
            traceback.print_exc()
        sys.exit(1)

    if as_json:
        import json as _json
        # Convert datetime objects to strings
        for u in users:
            for k, v in u.items():
                if hasattr(v, 'isoformat'):
                    u[k] = v.isoformat()
        click.echo(_json.dumps(users, indent=2))
        return

    if not ctx.obj.get('quiet'):
        click.echo()
        section(f"Admin Users ({len(users)})")
        click.echo()

        if not users:
            info("  No admin users found. Run: aq admin createsuperuser")
        else:
            headers = ["ID", "Username", "Email", "Active", "Super", "Staff", "Joined"]
            rows_data = []
            for u in users:
                joined = u.get("date_joined", "")
                if hasattr(joined, 'strftime'):
                    joined = joined.strftime("%Y-%m-%d")
                rows_data.append([
                    str(u.get("id", "?"))[:8],
                    u.get("username", ""),
                    u.get("email", ""),
                    _CHECK if u.get("is_active") else _CROSS,
                    _CHECK if u.get("is_superuser") else _CROSS,
                    _CHECK if u.get("is_staff") else _CROSS,
                    str(joined)[:10],
                ])
            table(headers, rows_data)
        click.echo()


@admin.command('changepassword')
@click.argument('username')
@click.option('--password', prompt=click.style('  New password', fg='cyan', bold=True),
              hide_input=True, confirmation_prompt=click.style('  Confirm password', fg='cyan', bold=True),
              help='New password')
@click.option('--database-url', type=str, default=None, help='Database URL')
@click.pass_context
def admin_changepassword(ctx, username: str, password: str, database_url: Optional[str]):
    """
    Change an admin user's password.

    Examples:
      aq admin changepassword admin
      aq admin changepassword admin --password=newsecret
    """
    import asyncio

    if database_url is None:
        database_url = _detect_workspace_db_url()

    if len(password) < 4:
        error(f"  {_CROSS} Password must be at least 4 characters")
        sys.exit(1)

    async def _change():
        from aquilia.db.engine import configure_database
        from aquilia.auth.hashing import PasswordHasher
        db = configure_database(database_url)
        await db.connect()
        try:
            hasher = PasswordHasher()
            hashed = hasher.hash(password)
            result = await db.execute(
                "UPDATE admin_users SET password_hash = :hash WHERE username = :username",
                {"hash": hashed, "username": username},
            )
            # Check if user was found
            row = await db.fetch_one(
                "SELECT id FROM admin_users WHERE username = :username",
                {"username": username},
            )
            return row is not None
        finally:
            await db.disconnect()

    try:
        found = asyncio.run(_change())
    except Exception as e:
        error(f"  {_CROSS} Failed to change password: {e}")
        sys.exit(1)

    if found:
        click.echo()
        success(f"  {_CHECK} Password changed for user '{username}'")
        click.echo()
    else:
        error(f"  {_CROSS} User '{username}' not found")
        sys.exit(1)


@admin.command('setup')
@click.option('--non-interactive', '-y', is_flag=True, help='Skip confirmation prompts')
@click.option('--database-url', type=str, default=None, help='Database URL to use (default: sqlite:///db.sqlite3)')
@click.pass_context
def admin_setup(ctx, non_interactive: bool, database_url: Optional[str]):
    """
    Auto-configure all admin dependencies in workspace.py.

    This is the one-stop command to get the admin dashboard running.
    It performs every step needed:

    \b
      1. Ensures .sessions(...) is enabled in workspace.py
      2. Ensures Integration.admin(...) is present
      3. Ensures Integration.database(...) is present
      4. Ensures Integration.static_files(...) is present
      5. Adds the required imports (SessionPolicy, timedelta)
      6. Runs database migrations for admin tables
      7. Prompts to create a superuser if none exists

    Examples:
      aq admin setup
      aq admin setup -y
      aq admin setup --database-url=postgresql://...
    """
    import asyncio
    import textwrap

    click.echo()
    banner("AquilAdmin", subtitle="Auto-Setup")
    click.echo()

    workspace_file = Path("workspace.py")
    if not workspace_file.exists():
        error(f"  {_CROSS} workspace.py not found — run 'aq init workspace <name>' first")
        sys.exit(1)

    content = workspace_file.read_text()
    original_content = content

    # Remove comment-only lines for active config detection
    def _active(text: str) -> str:
        return "\n".join(
            line for line in text.splitlines()
            if not line.strip().startswith("#")
        )

    active = _active(content)
    changes_made: list[str] = []

    # ── Step 1: Ensure required imports ──────────────────────────────
    step(1, "Checking imports...")
    needed_imports: list[str] = []
    if "from datetime import timedelta" not in content and "timedelta" not in content:
        needed_imports.append("from datetime import timedelta")
    if "SessionPolicy" not in content:
        needed_imports.append("from aquilia.sessions import SessionPolicy")

    if needed_imports:
        # Insert after the last import line
        lines = content.splitlines()
        last_import_idx = 0
        for i, line in enumerate(lines):
            stripped = line.strip()
            if stripped.startswith("from ") or stripped.startswith("import "):
                if not stripped.startswith("#"):
                    last_import_idx = i

        for imp in needed_imports:
            lines.insert(last_import_idx + 1, imp)
            last_import_idx += 1
            changes_made.append(f"Added import: {imp}")

        content = "\n".join(lines)
        active = _active(content)
        success(f"    {_CHECK} Added {len(needed_imports)} import(s)")
    else:
        dim(f"    {_CHECK} Imports already present")

    # ── Step 2: Ensure sessions are enabled ──────────────────────────
    step(2, "Checking sessions config...")
    has_sessions = (
        ".sessions(" in active
        or "Integration.sessions(" in active
        or "Integration.auth(" in active
    )
    if not has_sessions:
        # Check if there's a commented-out .sessions block we can uncomment
        if "# .sessions(" in content:
            # Uncomment the entire .sessions(...) block
            lines = content.splitlines()
            in_sessions_block = False
            brace_depth = 0
            for i, line in enumerate(lines):
                stripped = line.lstrip()
                if not in_sessions_block and stripped.startswith("# .sessions("):
                    lines[i] = line.replace("# .sessions(", ".sessions(", 1)
                    in_sessions_block = True
                    brace_depth = line.count("(") - line.count(")")
                    continue
                if in_sessions_block:
                    if stripped.startswith("# "):
                        lines[i] = line.replace("# ", "", 1)
                    brace_depth += line.count("(") - line.count(")")
                    if brace_depth <= 0:
                        in_sessions_block = False

            content = "\n".join(lines)
            active = _active(content)
            changes_made.append("Uncommented .sessions(...) block")
            success(f"    {_CHECK} Uncommented .sessions(...) block")
        else:
            # Inject a sessions block before the admin integration or at the end
            sessions_block = textwrap.dedent("""\

    # Sessions — required for admin login
    .sessions(
        policies=[
            SessionPolicy(
                name="default",
                ttl=timedelta(days=7),
                idle_timeout=timedelta(hours=1),
            ),
        ],
    )""")
            # Find the admin integration line or the closing ')'
            lines = content.splitlines()
            insert_idx = None
            for i, line in enumerate(lines):
                if "Integration.admin(" in line and not line.lstrip().startswith("#"):
                    insert_idx = i
                    break
            if insert_idx is None:
                # Insert before the last ')'
                for i in range(len(lines) - 1, -1, -1):
                    if lines[i].strip() == ")":
                        insert_idx = i
                        break
            if insert_idx is not None:
                for j, sline in enumerate(sessions_block.splitlines()):
                    lines.insert(insert_idx + j, sline)
                content = "\n".join(lines)
                active = _active(content)
                changes_made.append("Injected .sessions(...) block")
                success(f"    {_CHECK} Injected .sessions(...) config")
            else:
                warning(f"    ! Could not find insertion point — add .sessions() manually")
    else:
        dim(f"    {_CHECK} Sessions already configured")

    # ── Step 3: Ensure Integration.admin(...) ────────────────────────
    step(3, "Checking admin integration...")
    if "Integration.admin(" not in active:
        if "# .integrate(Integration.admin(" in content or "#.integrate(Integration.admin(" in content:
            # Uncomment it
            content = _re.sub(
                r"#\s*\.integrate\(Integration\.admin\(",
                ".integrate(Integration.admin(",
                content,
                count=1,
            )
            # Also uncomment any following commented lines until closing ))
            lines = content.splitlines()
            in_admin_block = False
            for i, line in enumerate(lines):
                if ".integrate(Integration.admin(" in line and not line.lstrip().startswith("#"):
                    in_admin_block = True
                    continue
                if in_admin_block:
                    stripped = line.lstrip()
                    if stripped.startswith("# "):
                        lines[i] = line.replace("# ", "", 1)
                    if "))" in line:
                        in_admin_block = False
            content = "\n".join(lines)
            active = _active(content)
            changes_made.append("Uncommented Integration.admin(...)")
            success(f"    {_CHECK} Uncommented admin integration")
        else:
            # Inject admin integration before the closing ')'
            admin_block = textwrap.dedent("""\

    # Admin Dashboard
    .integrate(Integration.admin(
        url_prefix="/admin",
        site_title="Admin",
        auto_discover=True,
    ))""")
            lines = content.splitlines()
            for i in range(len(lines) - 1, -1, -1):
                if lines[i].strip() == ")":
                    for j, sline in enumerate(admin_block.splitlines()):
                        lines.insert(i + j, sline)
                    break
            content = "\n".join(lines)
            active = _active(content)
            changes_made.append("Injected Integration.admin(...)")
            success(f"    {_CHECK} Injected admin integration")
    else:
        dim(f"    {_CHECK} Admin integration already configured")

    # ── Step 4: Ensure Integration.database(...) ─────────────────────
    step(4, "Checking database integration...")
    if "Integration.database(" not in active:
        warning(f"    ! No database integration found — admin needs a database")
        info(f"      Add: .integrate(Integration.database(pool_size=5))")
    else:
        dim(f"    {_CHECK} Database integration present")

    # ── Step 5: Ensure Integration.static_files(...) ─────────────────
    step(5, "Checking static files integration...")
    if "Integration.static_files(" not in active:
        warning(f"    ! No static files integration — admin CSS/JS may not load")
        info(f'      Add: .integrate(Integration.static_files(directories={{"/static": "static"}}))')
    else:
        dim(f"    {_CHECK} Static files integration present")

    # ── Write workspace.py if changed ────────────────────────────────
    if content != original_content:
        click.echo()
        section("Changes to workspace.py")
        for change in changes_made:
            bullet(change, fg="green")
        click.echo()

        if not non_interactive:
            if not click.confirm(click.style("  Apply these changes to workspace.py?", bold=True), default=True):
                info(f"  {_CROSS} Aborted — no changes written")
                sys.exit(0)

        workspace_file.write_text(content)
        success(f"  {_CHECK} workspace.py updated")
    else:
        click.echo()
        dim(f"  {_CHECK} workspace.py already fully configured")

    # ── Step 6: Ensure admin tables exist ────────────────────────────
    click.echo()
    step(6, "Ensuring admin database tables...")

    db_url = database_url or _detect_workspace_db_url()

    async def _ensure_tables():
        try:
            from aquilia.db.engine import configure_database
            db = configure_database(db_url)
            await db.connect()
        except Exception as e:
            return False, f"Database connection failed: {e}"

        try:
            from aquilia.admin.models import (
                AdminUser, ContentType, AdminPermission,
                AdminGroup, AdminLogEntry, AdminSession,
            )
            _admin_models = [
                ContentType, AdminPermission, AdminGroup,
                AdminUser, AdminLogEntry, AdminSession,
            ]
            created = 0
            for _model in _admin_models:
                try:
                    create_sql = _model.generate_create_table_sql()
                    await db.execute(create_sql)
                    for idx_sql in _model.generate_index_sql():
                        await db.execute(idx_sql)
                    for m2m_sql in _model.generate_m2m_sql():
                        await db.execute(m2m_sql)
                    created += 1
                except Exception:
                    pass  # Table already exists
            return True, f"{created} table(s) checked/created"
        finally:
            try:
                await db.disconnect()
            except Exception:
                pass

    try:
        ok, detail = asyncio.run(_ensure_tables())
        if ok:
            success(f"    {_CHECK} {detail}")
        else:
            warning(f"    ! {detail}")
    except Exception as e:
        warning(f"    ! Could not ensure tables: {e}")
        info(f"      Run 'aq db migrate' manually")

    # ── Step 7: Check for superuser ──────────────────────────────────
    step(7, "Checking for superuser...")

    async def _check_su():
        try:
            from aquilia.db.engine import configure_database
            db = configure_database(db_url)
            await db.connect()
            try:
                result = await db.fetch_one(
                    "SELECT COUNT(*) as cnt FROM admin_users WHERE is_superuser = 1"
                )
                return result["cnt"] if result else 0
            finally:
                await db.disconnect()
        except Exception:
            return -1  # Unknown

    try:
        su_count = asyncio.run(_check_su())
    except Exception:
        su_count = -1

    if su_count > 0:
        dim(f"    {_CHECK} {su_count} superuser(s) found")
    elif su_count == 0:
        warning(f"    ! No superusers found")
        if not non_interactive:
            if click.confirm(click.style("  Create a superuser now?", bold=True), default=True):
                # Invoke the createsuperuser command
                ctx.invoke(admin_createsuperuser)
                return
        else:
            info(f"      Run 'aq admin createsuperuser' to create one")
    else:
        dim(f"    ? Could not check (run 'aq db migrate' first)")

    # ── Done ─────────────────────────────────────────────────────────
    click.echo()
    success(f"  {_CHECK} Admin setup complete!")
    click.echo()
    next_steps([
        "aq admin check          (verify configuration)",
        "aq run                  (start the dev server)",
        "Visit http://localhost:8000/admin/",
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
