"""Development server command."""

import os
import re
import sys
from pathlib import Path
from typing import Any

from aquilia.cli.discovery_utils import EnhancedDiscovery
from aquilia.cli.generators.workspace import WorkspaceGenerator
from aquilia.discovery.engine import AutoDiscoveryEngine
from aquilia.faults.domains import ConfigMissingFault


def _load_workspace_runtime_config(workspace_root: Path) -> dict[str, Any]:
    """
    Load runtime configuration from workspace.py's AquilaConfig.

    Reads the ``workspace`` variable, calls ``to_dict()``, and returns
    the ``runtime`` section.  This gives us the resolved env_config
    values (host, port, workers, reload, etc.) that the user defined
    in their ``AquilaConfig.Server`` subclass.

    Returns an empty dict if anything goes wrong so callers can
    safely fall back to hardcoded defaults.
    """
    ws_file = workspace_root / "workspace.py"
    if not ws_file.exists():
        return {}

    try:
        import importlib.util

        # Ensure the workspace root is importable
        if str(workspace_root) not in sys.path:
            sys.path.insert(0, str(workspace_root))

        spec = importlib.util.spec_from_file_location(
            "_aq_ws_runtime",
            ws_file,
        )
        if spec is None or spec.loader is None:
            return {}

        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)

        workspace = getattr(module, "workspace", None)
        if workspace is None:
            return {}

        config_dict = workspace.to_dict()
        return config_dict.get("runtime", {})
    except Exception:
        return {}


# Fields from AquilaConfig.Server that map directly to uvicorn.Config
# parameters.  Anything NOT in this set is silently ignored so that
# Aquilia-only fields (mode, debug) don't cause TypeError.
_UVICORN_KNOWN_PARAMS = frozenset(
    {
        "host",
        "port",
        "uds",
        "fd",
        "loop",
        "http",
        "ws",
        "ws_max_size",
        "ws_max_queue",
        "ws_ping_interval",
        "ws_ping_timeout",
        "ws_per_message_deflate",
        "lifespan",
        "interface",
        "reload",
        "reload_dirs",
        "reload_delay",
        "reload_includes",
        "reload_excludes",
        "workers",
        "log_level",
        "access_log",
        "use_colors",
        "proxy_headers",
        "server_header",
        "date_header",
        "forwarded_allow_ips",
        "root_path",
        "limit_concurrency",
        "limit_max_requests",
        "backlog",
        "timeout_keep_alive",
        "timeout_worker_healthcheck",
        "timeout_graceful_shutdown",
        "ssl_keyfile",
        "ssl_certfile",
        "ssl_keyfile_password",
        "ssl_ca_certs",
        "ssl_ciphers",
        "headers",
        "factory",
        "h11_max_incomplete_event_size",
    }
)

# ADP-specific keys in AquilaConfig.Server that are NOT forwarded to uvicorn
_ADP_CONFIG_KEYS = frozenset(
    {
        "use_adp",
        "adp_inspector",
        "adp_max_request_history",
        "adp_profiler",
        "adp_sql_explain_threshold_ms",
        "adp_n_plus_one_detection",
        "adp_memory_snapshot_interval_s",
    }
)


def _build_uvicorn_kwargs(
    rt: dict[str, Any],
    *,
    overrides: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """
    Build a ``uvicorn.run()`` keyword-argument dict from the runtime
    config section (``AquilaConfig.Server`` → ``to_dict()[\"server\"]``).

    Only keys that match a known ``uvicorn.Config`` parameter are
    included.  ``None`` values are omitted so uvicorn uses its own
    default for that parameter.

    *overrides* are merged last and always win (CLI flags).
    """
    kwargs: dict[str, Any] = {}
    for key, val in rt.items():
        if key in _UVICORN_KNOWN_PARAMS and val is not None:
            kwargs[key] = val
    if overrides:
        for key, val in overrides.items():
            if val is not None:
                kwargs[key] = val
    return kwargs


def _build_adp_config(rt: dict[str, Any], *, overrides: dict[str, Any] | None = None) -> Any:
    """
    Build an AquiliaDevelopmentConfig from the runtime config section.

    Reads all adp_* keys from AquilaConfig.Server and applies CLI overrides.
    Returns an AquiliaDevelopmentConfig instance.

    Raises:
        ConfigurationFault: if any resolved value fails
            ``AquiliaDevelopmentConfig.__post_init__`` validation.
    """
    from pathlib import Path

    from aquilia.devplatform.config import AquiliaDevelopmentConfig

    overrides = overrides or {}

    def _pick(cli_key: str, rt_key: str, default: Any) -> Any:
        """CLI flag > workspace config > default. None-safe (fd=0 is valid)."""
        cli_val = overrides.get(cli_key)
        if cli_val is not None:
            return cli_val
        rt_val = rt.get(rt_key)
        if rt_val is not None:
            return rt_val
        return default

    reload_dirs_raw = rt.get("reload_dirs") or [str(Path.cwd())]

    return AquiliaDevelopmentConfig(
        host=_pick("host", "host", "127.0.0.1"),
        port=_pick("port", "port", 8000),
        uds=_pick("uds", "adp_uds", None),
        fd=_pick("fd", "adp_fd", None),
        http=_pick("http", "adp_http", "h11"),
        ws=_pick("ws", "adp_ws", "auto"),
        reload=_pick("reload", "reload", True),
        reload_dirs=[Path(d) for d in reload_dirs_raw],
        reload_excludes=rt.get("reload_excludes") or [],
        log_level=(rt.get("log_level") or "INFO").upper(),
        inspector_enabled=rt.get("adp_inspector", True),
        max_request_history=rt.get("adp_max_request_history", 500),
        profiler_enabled=rt.get("adp_profiler", False),
        sql_explain_threshold_ms=rt.get("adp_sql_explain_threshold_ms", 50.0),
        n_plus_one_detection=rt.get("adp_n_plus_one_detection", True),
        memory_snapshot_interval_s=rt.get("adp_memory_snapshot_interval_s", 30.0),
        timeout_graceful_shutdown=float(rt.get("timeout_graceful_shutdown") or 5.0),
    )


def _validate_workspace_config(workspace_root: Path, verbose: bool = False) -> list[str]:
    """
    Validate that all modules registered in workspace.py/manifest.py actually exist.

    Checks:
    1. All registered module directories exist
    2. All manifest.py files can be found
    3. All controller/service imports are valid file paths
    4. No circular or missing dependencies

    Args:
        workspace_root: Path to workspace root
        verbose: Enable verbose output

    Returns:
        List of error messages (empty if validation passes)
    """
    errors = []

    try:
        # Check if workspace.py exists and is valid
        workspace_py = workspace_root / "workspace.py"
        if not workspace_py.exists():
            errors.append("workspace.py not found in workspace root")
            return errors

        # Read workspace.py to find registered modules
        try:
            workspace_content = workspace_py.read_text(encoding="utf-8")
        except Exception as e:
            errors.append(f"Cannot read workspace.py: {str(e)[:60]}")
            return errors

        # Remove comment lines to avoid matching commented-out modules
        # This fixes the issue where default templates have commented-out 'auth' and 'users' modules
        clean_content = "\n".join(line for line in workspace_content.splitlines() if not line.strip().startswith("#"))

        # Extract module names from workspace.py
        import re

        module_matches = re.findall(r'Module\("([^"]+)"', clean_content)
        module_names = list(set(module_matches))  # Deduplicate

        # The "starter" pseudo-module lives in workspace root (starter.py),
        # not under modules/.  Skip it during validation -- the server
        # auto-loads it via _load_starter_controller().
        module_names = [m for m in module_names if m != "starter"]

        if not module_names:
            # No modules registered - that's OK
            return errors

        modules_dir = workspace_root / "modules"
        if not modules_dir.exists():
            errors.append(f"modules directory not found at {modules_dir}")
            return errors

        # Validate each registered module
        for module_name in module_names:
            module_dir = modules_dir / module_name

            # Check if module directory exists
            if not module_dir.exists():
                errors.append(f"Module directory not found: modules/{module_name}")
                continue

            # Check if manifest.py exists
            manifest_path = module_dir / "manifest.py"
            if not manifest_path.exists():
                errors.append(f"Module manifest not found: modules/{module_name}/manifest.py")
                continue

            # Read manifest and validate imports
            try:
                manifest_content = manifest_path.read_text(encoding="utf-8")
            except Exception as e:
                errors.append(f"Cannot read manifest for {module_name}: {str(e)[:50]}")
                continue

            # Extract controller and service imports (skip commented lines)
            # Format: "modules.mymodule.services:MymoduleService"
            imports = []
            for line in manifest_content.split("\n"):
                # Skip lines that are comments
                stripped = line.strip()
                if stripped.startswith("#"):
                    continue
                # Extract quoted strings with ':' pattern from this line
                line_imports = re.findall(r'"([^"]*:[\w]+)"', line)
                imports.extend(line_imports)

            # Validate each import can be resolved
            for import_path in imports:
                if ":" not in import_path:
                    continue

                module_path, class_name = import_path.split(":")

                # Convert module path to file path
                # Example: "modules.mymodule.services" -> "modules/mymodule/services.py"
                parts = module_path.split(".")

                # Skip 'modules' prefix and rebuild path starting from module_dir
                if parts[0] == "modules" and len(parts) > 1:
                    parts = parts[1:]  # Remove 'modules' prefix

                # Skip module name itself (parts[0] is module_name)
                if parts and parts[0] == module_name:
                    parts = parts[1:]

                # Build file path
                try:
                    base_path = module_dir
                    for part in parts:
                        base_path = base_path / part

                    file_path = base_path.with_suffix(".py")
                    package_init = base_path / "__init__.py"

                    if not file_path.exists() and not package_init.exists():
                        errors.append(
                            f"Import error in {module_name}: {import_path} "
                            f"(file not found: {file_path.relative_to(workspace_root)})"
                        )
                except Exception as e:
                    errors.append(f"Cannot validate import {import_path} in {module_name}: {str(e)[:40]}")

    except Exception as e:
        errors.append(f"Unexpected error during validation: {str(e)[:60]}")

    return errors


def _discover_and_update_manifests(workspace_root: Path, verbose: bool = False) -> None:
    """
    Discover all components in all modules and auto-update manifest.py and workspace.py.
    """
    import sys
    from pathlib import Path

    workspace_root = Path(workspace_root)
    modules_dir = workspace_root / "modules"
    if not modules_dir.exists():
        return

    # Add workspace root to Python path for imports
    workspace_abs = workspace_root.resolve()
    if str(workspace_abs) not in sys.path:
        sys.path.insert(0, str(workspace_abs))

    try:
        engine = AutoDiscoveryEngine(modules_dir)
        reports = engine.sync_all(dry_run=False)
        if verbose:
            for report in reports:
                if report.has_changes:
                    print(f"  Synced manifest for module {report.module_name}")
                    for action in report.added:
                        print(f"    + Added {action.component.name}")
                    for action in report.removed:
                        print(f"    - Removed {action.component.name}")
    except Exception as e:
        if verbose:
            print(f"  ! AST Discovery Engine sync failed: {e}")

    try:
        generator = WorkspaceGenerator(name=workspace_root.name, path=workspace_root)
        discovered = generator._discover_modules()
        if discovered:
            workspace_py_path = workspace_root / "workspace.py"
            if workspace_py_path.exists():
                generator.update_workspace_config(workspace_py_path, discovered)
    except Exception as e:
        if verbose:
            print(f"  ! Failed to update workspace.py: {e}")


def _discover_and_display_routes(workspace_root: Path, verbose: bool = False) -> None:
    """
    Discover all modules and their routes before starting server.

    Args:
        workspace_root: Path to workspace root
        verbose: Enable verbose output
    """
    import sys
    from pathlib import Path

    workspace_root = Path(workspace_root)

    # Add workspace root to path
    workspace_abs = workspace_root.resolve()
    if str(workspace_abs) not in sys.path:
        sys.path.insert(0, str(workspace_abs))

    modules_dir = workspace_root / "modules"
    if not modules_dir.exists():
        return

    discovery = EnhancedDiscovery(verbose=False)

    # Collect all discovered modules with their controllers and services
    discovered_modules = {}

    # Discover all modules with manifest.py
    for module_dir in modules_dir.iterdir():
        if not module_dir.is_dir() or module_dir.name.startswith("_"):
            continue

        manifest_path = module_dir / "manifest.py"
        if not manifest_path.exists():
            continue

        module_name = module_dir.name
        base_package = f"modules.{module_name}"

        try:
            # Use enhanced discovery
            result = discovery.discover_module_controllers_and_services(base_package, module_name)
            # Handle both 2-tuple (legacy) and 3-tuple (new) return values
            if len(result) == 3:
                discovered_controllers, discovered_services, discovered_sockets = result
            else:
                discovered_controllers, discovered_services = result
                discovered_sockets = []

            # Extract metadata from manifest
            manifest_content = manifest_path.read_text(encoding="utf-8")
            import re

            version = re.search(r'version="([^"]+)"', manifest_content)
            description = re.search(r'description="([^"]+)"', manifest_content)
            route_prefix = re.search(r'route_prefix="([^"]+)"', manifest_content)
            tags = re.findall(
                r'"([^"]+)"',
                re.search(r"tags=\[(.*?)\]", manifest_content).group(1)
                if re.search(r"tags=\[(.*?)\]", manifest_content)
                else "",
            )

            discovered_modules[module_name] = {
                "name": module_name,
                "version": version.group(1) if version else "0.1.0",
                "description": description.group(1) if description else f"{module_name.capitalize()} module",
                "route_prefix": route_prefix.group(1) if route_prefix else f"/{module_name}",
                "tags": tags or [module_name, "core"],
                "controllers_list": [c["path"] if isinstance(c, dict) else c for c in discovered_controllers],
                "services_list": [s["path"] if isinstance(s, dict) else s for s in discovered_services],
                "sockets_list": [
                    {
                        "path": s["path"] if isinstance(s, dict) else s,
                        "namespace": s.get("metadata", {}).get("namespace", "") if isinstance(s, dict) else "",
                    }
                    for s in discovered_sockets
                ],
                "controllers_count": len(discovered_controllers),
                "services_count": len(discovered_services),
                "sockets_count": len(discovered_sockets),
                "has_controllers": len(discovered_controllers) > 0,
                "has_services": len(discovered_services) > 0,
                "has_sockets": len(discovered_sockets) > 0,
            }

            if verbose:
                print(f"\n  Discovering module: {module_name}")
                if discovered_controllers:
                    print(f"  + Found {len(discovered_controllers)} controller(s)")
                if discovered_services:
                    print(f"  + Found {len(discovered_services)} service(s)")

        except Exception as e:
            if verbose:
                print(f"  !  Error discovering {module_name}: {str(e)[:80]}")

    if not discovered_modules:
        return

    # Now display the results

    try:
        generator = WorkspaceGenerator(name=workspace_root.name, path=workspace_root)

        sorted_names = generator._resolve_dependencies(discovered_modules)
        validation = generator._validate_modules(discovered_modules)
    except Exception:
        sorted_names = sorted(discovered_modules.keys())
        validation = {"valid": True, "warnings": [], "errors": []}

    # Discovery data is collected above and available in discovered_modules.
    # Presentation is handled by `aq discover` or the ADP terminal UI (D key).
    # No print() output during server startup — keeps the launch banner clean.


def _write_discovery_report(workspace_root: Path, discovered: dict, sorted_names: list[str], validation: dict) -> None:
    """
    Write discovery report to routes.md file.

    Args:
        workspace_root: Path to workspace root
        discovered: Dictionary of discovered modules
        sorted_names: Module names in load order
        validation: Validation results
    """
    try:
        report_lines = [
            "# Auto-Discovered Routes & Modules\n",
            f"*Generated: {__import__('datetime').datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*\n",
            "\n## Module Routes\n",
        ]

        # Module table
        report_lines.append("| Module | Route Prefix | Version | Tags | Components |\n")
        report_lines.append("|--------|--------------|---------|------|------------|\n")

        for mod_name in sorted_names:
            mod = discovered[mod_name]
            tags = ", ".join(mod.get("tags", [])[:3]) if mod.get("tags") else "-"
            components = []
            if mod["has_services"]:
                components.append("Services")
            if mod["has_controllers"]:
                components.append("Controllers")
            if mod["has_middleware"]:
                components.append("Middleware")
            comp_str = ", ".join(components) if components else "-"

            report_lines.append(f"| {mod_name} | `{mod['route_prefix']}` | {mod['version']} | {tags} | {comp_str} |\n")

        # Dependencies section
        has_deps = any(mod.get("depends_on") for mod in discovered.values())
        if has_deps:
            report_lines.append("\n## Dependencies\n\n")
            for mod_name in sorted_names:
                mod = discovered[mod_name]
                deps = mod.get("depends_on", [])
                if deps:
                    deps_str = " → ".join(deps)
                    report_lines.append(f"- **{mod_name}** depends on: {deps_str}\n")
                else:
                    report_lines.append(f"- **{mod_name}** (no dependencies)\n")

        # Statistics
        with_services = sum(1 for m in discovered.values() if m["has_services"])
        with_controllers = sum(1 for m in discovered.values() if m["has_controllers"])
        with_middleware = sum(1 for m in discovered.values() if m["has_middleware"])

        report_lines.append("\n## Statistics\n\n")
        report_lines.append(f"- **Total Modules**: {len(discovered)}\n")
        report_lines.append(f"- **With Services**: {with_services}\n")
        report_lines.append(f"- **With Controllers**: {with_controllers}\n")
        report_lines.append(f"- **With Middleware**: {with_middleware}\n")
        report_lines.append(f"- **Load Order**: {' → '.join(sorted_names)}\n")

        # Validation section
        report_lines.append("\n## Validation\n\n")
        if validation["errors"]:
            report_lines.append(f"**Errors**: {len(validation['errors'])}\n\n")
            for error in validation["errors"]:
                report_lines.append(f"- {error}\n")
        elif validation["warnings"]:
            report_lines.append(f"**Warnings**: {len(validation['warnings'])}\n\n")
            for warning in validation["warnings"]:
                report_lines.append(f"- {warning}\n")
        else:
            report_lines.append("**Status**: All modules validated!\n")

        # Write report
        report_file = workspace_root / "ROUTES.md"
        report_file.write_text("".join(report_lines), encoding="utf-8")

    except Exception:
        # Silently fail - don't interrupt server startup
        pass


def run_dev_server(
    mode: str = "dev",
    host: str | None = None,
    port: int | None = None,
    reload: bool | None = None,
    uds: str | None = None,
    fd: int | None = None,
    http: str | None = None,
    ws: str | None = None,
    verbose: bool = False,
) -> None:
    """
    Start the Aquilia Native Development Platform (ADP) server.

    The ADP is the default development server since Aquilia 1.3+.
    It provides framework-aware hot-reload, N+1 query detection, and
    memory tracking. Debugging surfaces through Aquilia's Inspector
    (``/__aquilia__/inspector/``), not a separate dashboard.

    Set ``use_adp = False`` in ``AquilaConfig.Server`` to fall back to
    plain uvicorn. Production mode (``mode="prod"``) always uses uvicorn
    regardless of ``use_adp`` — the ADP is a development tool, not a
    production ASGI server.

    Resolution order for host / port / reload / uds / fd / http / ws:
    1. Explicit CLI flags (``--host``, ``--port``, ``--reload``, ``--uds``,
       ``--fd``, ``--http``, ``--ws``)
    2. AquilaConfig values from ``workspace.py`` (``adp_uds``, ``adp_http``,
       ``adp_ws`` — see ``_build_adp_config``)
    3. Hardcoded fallback defaults (``http="h11"``, ``ws="auto"``, no
       ``uds``/``fd``)

    ``uds``/``fd`` take priority over ``host``/``port`` at bind time (see
    ``AquiliaDevelopmentServer.start``) — set at most one binding mode.

    Args:
        mode: Runtime mode (dev, test)
        host: Server host (None = read from workspace config)
        port: Server port (None = read from workspace config)
        reload: Enable hot-reload (None = read from workspace config)
        uds: UNIX domain socket path to bind instead of host:port
        fd: Inherited file descriptor to bind instead of host:port
        http: HTTP transport engine — "h11" (native, default) or "auto" (uvicorn)
        ws: WebSocket support — "auto" (native RFC 6455, default) or "none"
        verbose: Enable verbose output
    """

    workspace_root = Path.cwd()

    # Add workspace root to Python path for imports
    if str(workspace_root) not in sys.path:
        sys.path.insert(0, str(workspace_root))

    # ── Resolve runtime settings from AquilaConfig ───────────────────
    rt = _load_workspace_runtime_config(workspace_root)
    host = host if host is not None else rt.get("host", "127.0.0.1")
    port = port if port is not None else rt.get("port", 8000)
    port = _resolve_port(host, port)
    reload = reload if reload is not None else rt.get("reload", True)

    # Set environment variables
    os.environ["AQUILIA_ENV"] = mode
    os.environ["AQUILIA_WORKSPACE"] = str(workspace_root)

    # ===== AUTO-DISCOVER & UPDATE MANIFESTS FIRST =====
    _discover_and_update_manifests(workspace_root, verbose)

    # VALIDATE WORKSPACE CONFIGURATION BEFORE PROCEEDING
    validation_errors = _validate_workspace_config(workspace_root, verbose)
    if validation_errors:
        import click

        click.secho(
            "\n  Workspace validation failed! Fix these issues before starting the server:\n", fg="red", bold=True
        )
        for error in validation_errors:
            if "Import error" in error:
                parts = error.split(": ", 1)
                prefix = parts[0] + ": " if len(parts) > 1 else error
                detail = parts[1] if len(parts) > 1 else ""
                click.echo(
                    click.style("    - ", fg="red", bold=True)
                    + click.style(prefix, fg="yellow", bold=True)
                    + click.style(detail, fg="white")
                )
            elif "not found" in error or "Cannot read" in error:
                click.echo(click.style("    - ", fg="red", bold=True) + click.style(error, fg="red"))
            else:
                click.echo(click.style("    - ", fg="red", bold=True) + click.style(error, fg="white"))
        click.echo()
        return

    # Strategy 1: Check for workspace configuration (workspace.py) and auto-create app
    workspace_config = workspace_root / "workspace.py"
    if workspace_config.exists():
        if verbose:
            print("  Found workspace configuration: workspace.py")
        app_module = _create_workspace_app(workspace_root, mode, verbose)
        if verbose:
            print("  Using workspace-generated app")
    else:
        # Strategy 2: Look for existing app module
        app_module = _find_app_module(workspace_root, verbose)

        if not app_module:
            raise ConfigMissingFault(
                key="asgi.application",
                metadata={
                    "hint": (
                        "Could not find ASGI application.\n\n"
                        "Expected one of:\n"
                        "  1. Workspace configuration: workspace.py (recommended)\n"
                        "  2. main.py with 'app' variable\n"
                        "  3. app.py with 'app' variable\n"
                        "  4. server.py with 'app' or 'server' variable\n\n"
                        "For workspace-based projects:\n"
                        "  Run: aq init workspace <name>\n"
                        "  Then: aq add module <module_name>\n\n"
                        "For standalone apps, create main.py:\n"
                        "  from aquilia import AquiliaServer\n"
                        "  from aquilia.manifest import AppManifest\n\n"
                        "  class MyAppManifest(AppManifest):\n"
                        "      name = 'myapp'\n"
                        "      version = '1.0.0'\n"
                        "      controllers = []\n\n"
                        "  server = AquiliaServer(manifests=[MyAppManifest])\n"
                        "  app = server.app\n"
                    ),
                },
            )

    if verbose:
        print("\n  Starting Aquilia development server...")
        print(f"  Mode: {mode}")
        print(f"  Host: {host}:{port}")
        print(f"  Reload: {reload}")
        print(f"  App: {app_module}")

    # Discover and display all routes before starting server
    _discover_and_display_routes(workspace_root, verbose)

    # ── Decide ADP vs uvicorn ─────────────────────────────────────────
    # ADP is a development tool only. Production mode always uses uvicorn
    # regardless of use_adp; in dev/test mode use_adp (default True) applies.
    use_adp: bool = rt.get("use_adp", True) and mode != "prod"

    if rt.get("use_adp", True) and mode == "prod":
        import click

        click.secho("  ADP is development-only — production mode uses uvicorn.", fg="yellow")

    if use_adp:
        _run_with_adp(
            app_module=app_module,
            workspace_root=workspace_root,
            mode=mode,
            rt=rt,
            host=host,
            port=port,
            reload=reload,
            uds=uds,
            fd=fd,
            http=http,
            ws=ws,
            verbose=verbose,
        )
    else:
        _run_with_uvicorn_legacy(
            app_module=app_module,
            workspace_root=workspace_root,
            rt=rt,
            host=host,
            port=port,
            reload=reload,
            verbose=verbose,
        )


def _run_with_adp(
    app_module: str,
    workspace_root: Path,
    mode: str,
    rt: dict,
    host: str,
    port: int,
    reload: bool,
    uds: str | None = None,
    fd: int | None = None,
    http: str | None = None,
    ws: str | None = None,
    verbose: bool = False,
) -> None:
    """
    Start the Aquilia Native Development Platform.

    Loads the ASGI app from app_module, wraps it in ADP instrumentation, and
    serves it.

    Transport is selected by ``http``:
      - "h11" (default) — native h11-based ASGI transport built into ADP
        (aquilia.devplatform.core.h11_transport). Pure-python, predictable,
        no external HTTP server dependency for the dev loop.
      - "auto" — uvicorn as the HTTP transport, ADP instrumentation wrapped
        around the app. Use when you need uvicorn-specific behavior (HTTP/2,
        proven production parity) during development.

    Falls back to uvicorn if the ADP package itself cannot be imported.
    """
    import asyncio
    import importlib

    import click

    try:
        from aquilia.devplatform.devserver import AquiliaDevelopmentServer
    except ImportError as exc:
        click.secho(
            f"  ! ADP import failed ({exc}) — falling back to uvicorn.",
            fg="yellow",
        )
        _run_with_uvicorn_legacy(
            app_module=app_module,
            workspace_root=workspace_root,
            rt=rt,
            host=host,
            port=port,
            reload=reload,
            verbose=verbose,
        )
        return

    # Build ADP config from AquilaConfig.Server values
    adp_config = _build_adp_config(
        rt,
        overrides={"host": host, "port": port, "reload": reload, "uds": uds, "fd": fd, "http": http, "ws": ws},
    )

    if adp_config.http == "auto":
        # Uvicorn as the transport, ADP instrumentation wrapped around the app.
        try:
            import uvicorn
        except ImportError:
            click.secho("  ! --http auto requires uvicorn, but it is not installed. Using h11 instead.", fg="yellow")
            adp_config.http = "h11"
        else:
            _write_adp_runtime_wrapper(workspace_root, app_module, adp_config, mode)
            adp_app_module = "runtime._adp_app:adp_app"

            uv_kwargs = {
                "host": adp_config.host,
                "port": adp_config.port,
                "reload": adp_config.reload,
                "reload_dirs": [str(d) for d in adp_config.reload_dirs] if adp_config.reload else None,
                "log_level": adp_config.log_level.lower(),
                "use_colors": True,
            }
            uv_kwargs = {k: v for k, v in uv_kwargs.items() if v is not None}
            uvicorn.run(app=adp_app_module, **uv_kwargs)
            return

    # Native h11 transport (default): AquiliaDevelopmentServer drives its own
    # asyncio TCP/UDS acceptor — see aquilia.devplatform.core.h11_transport.
    async def _adp_main() -> None:
        mod_path, _, attr = app_module.partition(":")
        mod = importlib.import_module(mod_path.replace("/", ".").replace(".py", ""))
        app = getattr(mod, attr or "app")

        from aquilia.devplatform.ui import ADPTerminalUI

        dev_server = AquiliaDevelopmentServer(adp_config)
        loop = asyncio.get_running_loop()

        def _on_quit() -> None:
            # Called from the UI keyboard thread — hop back onto the event loop
            # to run the async graceful shutdown safely.
            loop.call_soon_threadsafe(lambda: asyncio.ensure_future(dev_server.stop()))

        def _on_reload() -> None:
            # Manual reload (R key): trigger a full process restart via the
            # reload executor from the event loop thread.
            from aquilia.devplatform.reload.analyzer import ReloadPlan, ReloadStrategy
            from aquilia.devplatform.reload.executor import ModuleReloadExecutor

            async def _do_reload() -> None:
                plan = ReloadPlan(strategy=ReloadStrategy.FULL, reason="manual reload (R)")
                executor = ModuleReloadExecutor(
                    plan, dev_server.get_runtime(), shutdown_timeout=adp_config.timeout_graceful_shutdown
                )
                await executor.execute()

            loop.call_soon_threadsafe(lambda: asyncio.ensure_future(_do_reload()))

        ui = ADPTerminalUI(
            adp_config,
            runtime=dev_server.get_runtime(),
            mode=mode,
            on_reload=_on_reload,
            on_quit=_on_quit,
        )
        ui.render_header()
        ui.start()
        try:
            await dev_server.start(app)
        finally:
            ui.stop()

    asyncio.run(_adp_main())


def _write_adp_runtime_wrapper(
    workspace_root: Path,
    app_module: str,
    adp_config: Any,
    mode: str,
) -> None:
    """
    Generate runtime/_adp_app.py — a thin ASGI wrapper that layers ADP
    instrumentation around the workspace's Aquilia app.

    This file is re-generated on every ``aq run`` so it always reflects
    the current ADP configuration.
    """
    runtime_dir = workspace_root / "runtime"
    runtime_dir.mkdir(exist_ok=True)

    # Ensure runtime/__init__.py exists
    init_path = runtime_dir / "__init__.py"
    if not init_path.exists():
        init_path.write_text("# Auto-generated by Aquilia ADP\n", encoding="utf-8")

    # Serialize the full config via its own to_dict() — single source of
    # truth. Adding a field to AquiliaDevelopmentConfig automatically flows
    # through here; no per-field kwarg list to keep in sync.
    config_dict = adp_config.to_dict()

    wrapper_code = f'''\
"""
Aquilia ADP Runtime Wrapper — auto-generated by ``aq run``.
DO NOT EDIT — regenerated on every launch.
"""
from __future__ import annotations

from pathlib import Path

from aquilia.devplatform.config import AquiliaDevelopmentConfig
from aquilia.devplatform.core.lifespan import ASGILifespanManager
from aquilia.devplatform.core.protocol import ADPProtocolHandler
from aquilia.devplatform.core.runtime import RuntimeStateStore

# ── Load base Aquilia app ────────────────────────────────────────────────────
from runtime.app import app as _aquilia_app

# ── Build ADP config (serialized from the resolved workspace config) ────────
_config_dict = {config_dict!r}
_config_dict["reload_dirs"] = [Path(d) for d in _config_dict["reload_dirs"]]
_adp_config = AquiliaDevelopmentConfig(**_config_dict)

# ── Wrap with ADP protocol handler ──────────────────────────────────────────
_runtime = RuntimeStateStore.get_instance()
_lifespan_app = ASGILifespanManager(_aquilia_app, _adp_config, _runtime)
adp_app = ADPProtocolHandler(_lifespan_app, _adp_config, _runtime)
'''
    wrapper_path = runtime_dir / "_adp_app.py"
    wrapper_path.write_text(wrapper_code, encoding="utf-8")


def _run_with_uvicorn_legacy(
    app_module: str,
    workspace_root: Path,
    rt: dict,
    host: str,
    port: int,
    reload: bool,
    verbose: bool,
) -> None:
    """Legacy uvicorn-only dev server (use_adp=False in AquilaConfig.Server)."""
    try:
        import uvicorn
    except ImportError:
        raise ImportError(
            "uvicorn is required to run the development server.\n"
            "Install it with: pip install uvicorn\n"
            "Or with extras: pip install 'aquilia[server]'"
        )

    uv_kwargs = _build_uvicorn_kwargs(
        rt,
        overrides={
            "host": host,
            "port": port,
            "reload": reload,
        },
    )
    uv_kwargs.setdefault("reload_dirs", [str(workspace_root)] if reload else None)
    uv_kwargs.setdefault("use_colors", True)
    if verbose:
        uv_kwargs["log_level"] = "debug"
    else:
        uv_kwargs.setdefault("log_level", "info")

    uvicorn.run(app=app_module, **uv_kwargs)


def _create_workspace_app(workspace_root: Path, mode: str, verbose: bool = False) -> str:
    """
    Create an ASGI app from workspace configuration.

    This generates a runtime app loader module that:
    1. Loads the workspace configuration (workspace.py)
    2. Discovers and loads module manifests (manifest.py)
    3. Creates AquiliaServer with all manifests
    4. Returns the ASGI app

    Args:
        workspace_root: Path to workspace root
        mode: Runtime mode (dev, test, prod)
        verbose: Enable verbose output

    Returns:
        Module path (e.g., "runtime.app:app")
    """
    runtime_dir = workspace_root / "runtime"
    runtime_dir.mkdir(exist_ok=True)

    # Create runtime app loader
    app_file = runtime_dir / "app.py"

    # Generate the app loader code
    app_code = _generate_workspace_app_code(workspace_root, mode, verbose)

    # Write the app file
    app_file.write_text(app_code, encoding="utf-8")

    if verbose:
        print(f"  Generated runtime app: {app_file}")

    # Return the module path
    return "runtime.app:app"


def _generate_workspace_app_code(workspace_root: Path, mode: str, verbose: bool = False) -> str:
    """
    Generate the ASGI application entrypoint for the workspace.

    Architecture (v3 — AquiliaRuntime):
    Delegates the full bootstrap lifecycle to :class:`aquilia.runtime.AquiliaRuntime`,
    which encapsulates path setup, logging, config loading, manifest discovery,
    and server construction in a structured, typed, phase-gated class.

    The generated code is self-contained, reload-safe (no side-effects at
    import time that break ``uvicorn --reload``), and compatible with all
    ASGI servers (uvicorn, hypercorn, granian, daphne, gunicorn+uvicorn).

    Returns:
        Python source code as string
    """
    from datetime import datetime

    # ── Introspect workspace.py ──────────────────────────────────────
    workspace_file = workspace_root / "workspace.py"
    workspace_content = workspace_file.read_text(encoding="utf-8")

    # Workspace name
    name_match = re.search(r'Workspace\(\s*(?:name\s*=\s*)?["\']([^"\']+)["\']', workspace_content)
    workspace_name = name_match.group(1) if name_match else "aquilia-app"

    # Strip comments before extracting modules to avoid commented-out matches
    clean_lines = [line for line in workspace_content.splitlines() if not line.strip().startswith("#")]
    clean_content = "\n".join(clean_lines)

    # Extract module names from .module(Module("name" ...))
    modules = re.findall(r'\.module\(\s*Module\(\s*["\']([^"\']+)["\']', clean_content)
    # Deduplicate while preserving order
    seen: set = set()
    modules = [m for m in modules if m not in seen and not seen.add(m)]  # type: ignore[func-returns-value]

    # The starter pseudo-module lives at workspace root, not under modules/
    modules = [m for m in modules if m != "starter"]

    if verbose:
        print(f"  Discovered modules: {', '.join(modules) or '(none)'}")

    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    code = f'''\
"""
Aquilia ASGI Runtime — {workspace_name}
{"=" * (23 + len(workspace_name))}

Auto-generated by ``aq run``.  DO NOT EDIT — regenerated on every launch.

Timestamp : {timestamp}
Workspace : {workspace_name}
Mode      : {mode}
Modules   : {len(modules)} ({", ".join(modules) or "none"})

Usage
-----
Development  : aq run
Production   : uvicorn runtime.app:app --host 0.0.0.0 --port 8000 --workers 4
Gunicorn     : gunicorn runtime.app:app -k uvicorn.workers.UvicornWorker -w 4
Hypercorn    : hypercorn runtime.app:app --bind 0.0.0.0:8000
Docker       : CMD ["uvicorn", "runtime.app:app", "--host", "0.0.0.0"]
"""

from __future__ import annotations

from pathlib import Path

from aquilia.runtime import AquiliaRuntime

# ────────────────────────────────────────────────────────────────────────
# Bootstrap via AquiliaRuntime
# ────────────────────────────────────────────────────────────────────────
_WORKSPACE_ROOT = Path(__file__).resolve().parent.parent

runtime = AquiliaRuntime.from_workspace(
    workspace_root=_WORKSPACE_ROOT,
    mode="{mode}",
)

# ────────────────────────────────────────────────────────────────────────
# ASGI application export
# ────────────────────────────────────────────────────────────────────────
server = runtime.server
app = runtime.app
'''

    return code


def _find_app_module(workspace_root: Path, verbose: bool = False) -> str | None:
    """
    Find the ASGI app module.

    Looks for:
    1. main.py with 'app' or 'application'
    2. app.py with 'app' or 'application'
    3. server.py with 'app' or 'server'

    Returns:
        Module path (e.g., "main:app") or None if not found
    """
    candidates = [
        ("main.py", ["app", "application", "server"]),
        ("app.py", ["app", "application", "server"]),
        ("server.py", ["app", "server", "application"]),
        ("asgi.py", ["app", "application"]),
    ]

    for filename, var_names in candidates:
        file_path = workspace_root / filename
        if file_path.exists():
            # Try to detect which variable is defined
            content = file_path.read_text(encoding="utf-8")

            for var_name in var_names:
                # Look for variable assignments
                if f"{var_name} =" in content or f"{var_name}=" in content:
                    module_name = filename.replace(".py", "")
                    app_ref = f"{module_name}:{var_name}"

                    if verbose:
                        print(f"Found app: {app_ref}")

                    return app_ref

    return None


def _resolve_port(host: str, port: int) -> int:
    """
    Resolve the port to bind via the devplatform :class:`PortManager`.

    Port recovery now lives in ``aquilia.devplatform.portmanager`` and probes
    with the same socket options the dev server binds with (``SO_REUSEADDR``),
    so a just-terminated server's ``TIME_WAIT`` port is reclaimed instead of
    triggering a false 8000 -> 8001 hop. Only a genuinely live listener causes
    a switch. The manager's ``reason`` is surfaced to the developer.
    """
    import click

    from aquilia.devplatform.portmanager import PortManager

    decision = PortManager().resolve(host, port)
    if decision.switched:
        click.secho(decision.reason, fg="yellow", bold=True)
    return decision.port
