"""Artifact inspection commands -- live workspace introspection.

Provides real-time inspection of the workspace by loading modules
and analyzing their manifests, controllers, services, routes, DI graph,
fault domains, and resolved configuration.
"""

import importlib
import importlib.util
import re
import sys
from pathlib import Path
from typing import Any

from aquilia.cli.utils.workspace import get_workspace_file
from aquilia.faults.domains import ConfigMissingFault


def _ensure_workspace_root() -> Path:
    """Ensure we're in an Aquilia workspace and return root."""
    workspace_root = Path.cwd()
    ws_file = get_workspace_file(workspace_root)
    if not ws_file:
        raise ConfigMissingFault(key="workspace.py")
    return workspace_root


def _get_workspace_modules(workspace_root: Path) -> list[str]:
    """Extract module names from workspace.py.

    Strips comment lines before scanning so that commented-out
    ``Module(...)`` declarations are not picked up.
    """
    ws_file = get_workspace_file(workspace_root)
    if not ws_file:
        return []
    lines = ws_file.read_text(encoding="utf-8").splitlines()
    active_lines = [ln for ln in lines if not ln.lstrip().startswith("#")]
    content = "\n".join(active_lines)
    return re.findall(r'Module\("([^"]+)"', content)


def _load_manifest_instance(workspace_root: Path, module_name: str) -> Any | None:
    """Load the manifest instance from a module's manifest.py."""
    ws_abs = str(workspace_root.resolve())
    if ws_abs not in sys.path:
        sys.path.insert(0, ws_abs)

    manifest_path = workspace_root / "modules" / module_name / "manifest.py"
    if not manifest_path.exists():
        return None

    try:
        spec = importlib.util.spec_from_file_location(f"_inspect_{module_name}_manifest", manifest_path)
        if not spec or not spec.loader:
            return None
        mod = importlib.util.module_from_spec(spec)
        sys.modules[spec.name] = mod
        spec.loader.exec_module(mod)

        # Try the conventional 'manifest' attribute first
        manifest_obj = getattr(mod, "manifest", None)
        if manifest_obj is not None:
            return manifest_obj

        # Fallback: look for any AppManifest instance
        from aquilia.manifest import AppManifest

        for _name, obj in vars(mod).items():
            if isinstance(obj, AppManifest):
                return obj
        return None
    except Exception:
        return None


# ---------------------------------------------------------------------------
# inspect routes
# ---------------------------------------------------------------------------


def inspect_routes(verbose: bool = False) -> None:
    """Show all routes, using the framework's own metadata extractor.

    Previously this probed ``__controller_routes__`` / ``__route__`` /
    ``_route_meta`` -- none of which exist. Every controller therefore fell
    into a "could not be extracted statically" branch that counted the
    controller as a single route, so a 5-route controller displayed as 1.
    """
    from aquilia.cli.core.workspace import load_workspace
    from aquilia.cli.introspect.routes import collect_routes

    workspace_root = _ensure_workspace_root()
    ws = load_workspace(workspace_root)

    if not ws.module_names:
        print("No modules registered in workspace.")
        return

    print("\n  Route Inspection")
    print("=" * 70)

    collected = collect_routes(ws)
    total_routes = 0
    failures = 0

    by_module: dict[str, list] = {}
    for entry in collected:
        by_module.setdefault(entry.module, []).append(entry)

    for module_name in sorted(by_module):
        print(f"\n  {module_name}")
        for entry in by_module[module_name]:
            if entry.error:
                failures += 1
                print(f"     !  {entry.controller or module_name}: {entry.error}")
                continue
            print(f"     {entry.controller}  (prefix: {entry.prefix or '/'})")
            for route in sorted(entry.routes, key=lambda r: (r.full_path, r.http_method)):
                flag = "  [deprecated]" if route.deprecated else ""
                print(f"       {route.http_method:<8} {route.full_path:<38} -> {route.handler}{flag}")
                total_routes += 1

    print(f"\n{'─' * 70}")
    print(f"  Total routes: {total_routes}")
    print(f"  Modules:      {len(ws.module_names)}")
    if failures:
        print(f"  Failed:       {failures} controller(s) could not be read")
    print()


# ---------------------------------------------------------------------------
# inspect di
# ---------------------------------------------------------------------------


def inspect_di(verbose: bool = False) -> None:
    """Show the DI service graph from module manifests."""
    workspace_root = _ensure_workspace_root()
    modules = _get_workspace_modules(workspace_root)

    if not modules:
        print("No modules registered in workspace.")
        return

    print("\n  DI / Service Inspection")
    print("=" * 70)

    total_services = 0

    for module_name in sorted(modules):
        manifest = _load_manifest_instance(workspace_root, module_name)
        if not manifest:
            print(f"\n  !  Module '{module_name}': manifest not loadable")
            continue

        services = getattr(manifest, "services", []) or []
        name = getattr(manifest, "name", module_name)

        print(f"\n  {name}")

        if not services:
            print("     No services registered.")
            continue

        for svc in services:
            if isinstance(svc, str):
                svc_display = svc.rsplit(":", 1)[-1] if ":" in svc else svc.split(".")[-1]
                scope = _detect_service_scope(workspace_root, svc)
                print(f"     • {svc_display:<35} scope={scope:<12} path={svc}")
            else:
                class_path = getattr(svc, "class_path", str(svc))
                scope = getattr(svc, "scope", "app")
                svc_display = class_path.rsplit(":", 1)[-1] if ":" in class_path else str(svc)
                scope_val = scope.value if hasattr(scope, "value") else str(scope)
                print(f"     • {svc_display:<35} scope={scope_val:<12} path={class_path}")
            total_services += 1

    print(f"\n{'─' * 70}")
    print(f"  Total services: {total_services}")
    print(f"  Modules:        {len(modules)}")
    print()


def _detect_service_scope(workspace_root: Path, svc_ref: str) -> str:
    """Try to detect the scope of a service from its class."""
    if ":" not in svc_ref:
        return "app"
    try:
        ws_abs = str(workspace_root.resolve())
        if ws_abs not in sys.path:
            sys.path.insert(0, ws_abs)
        mod_path, cls_name = svc_ref.rsplit(":", 1)
        mod = importlib.import_module(mod_path)
        cls = getattr(mod, cls_name, None)
        if cls:
            scope = getattr(cls, "__di_scope__", None)
            if scope:
                return scope.value if hasattr(scope, "value") else str(scope)
    except Exception:
        pass
    return "app"


# ---------------------------------------------------------------------------
# inspect modules
# ---------------------------------------------------------------------------


def inspect_modules(verbose: bool = False) -> None:
    """List all modules with metadata."""
    workspace_root = _ensure_workspace_root()
    modules = _get_workspace_modules(workspace_root)

    if not modules:
        print("No modules registered in workspace.")
        return

    print("\n  Module Inspection")
    print("=" * 70)

    print(f"\n  {'Module':<20} {'Version':<10} {'Route':<20} {'Controllers':<12} {'Services':<10}")
    print(f"  {'─' * 20} {'─' * 10} {'─' * 20} {'─' * 12} {'─' * 10}")

    for module_name in sorted(modules):
        manifest = _load_manifest_instance(workspace_root, module_name)
        if not manifest:
            print(f"  {module_name:<20} {'?':<10} {'?':<20} {'?':<12} {'?':<10}")
            continue

        version = getattr(manifest, "version", "?")
        route_prefix = getattr(manifest, "route_prefix", f"/{module_name}")
        controllers = getattr(manifest, "controllers", []) or []
        services = getattr(manifest, "services", []) or []
        name = getattr(manifest, "name", module_name)

        print(f"  {name:<20} {version:<10} {route_prefix:<20} {len(controllers):<12} {len(services):<10}")

    if verbose:
        print("\n  Detailed Module Information:")
        print(f"  {'─' * 60}")
        for module_name in sorted(modules):
            manifest = _load_manifest_instance(workspace_root, module_name)
            if not manifest:
                continue
            name = getattr(manifest, "name", module_name)
            description = getattr(manifest, "description", "")
            author = getattr(manifest, "author", "")
            tags = getattr(manifest, "tags", [])
            depends = getattr(manifest, "depends_on", [])

            print(f"\n  {name}")
            if description:
                print(f"     Description: {description}")
            if author:
                print(f"     Author:      {author}")
            if tags:
                print(f"     Tags:        {', '.join(tags)}")
            if depends:
                print(f"     Depends on:  {', '.join(depends)}")

    print(f"\n{'─' * 70}")
    print(f"  Total modules: {len(modules)}")
    print()


# ---------------------------------------------------------------------------
# inspect faults
# ---------------------------------------------------------------------------


def inspect_faults(verbose: bool = False) -> None:
    """Show fault domains from module manifests."""
    workspace_root = _ensure_workspace_root()
    modules = _get_workspace_modules(workspace_root)

    if not modules:
        print("No modules registered in workspace.")
        return

    print("\n  Fault Domain Inspection")
    print("=" * 70)

    for module_name in sorted(modules):
        manifest = _load_manifest_instance(workspace_root, module_name)
        if not manifest:
            print(f"\n  !  Module '{module_name}': manifest not loadable")
            continue

        name = getattr(manifest, "name", module_name)
        faults_config = getattr(manifest, "faults", None)

        print(f"\n  {name}")

        if not faults_config:
            print("     No fault configuration defined.")
            continue

        domain = getattr(faults_config, "default_domain", "GENERIC")
        strategy = getattr(faults_config, "strategy", "propagate")
        handlers = getattr(faults_config, "handlers", []) or []

        print(f"     Domain:   {domain}")
        print(f"     Strategy: {strategy}")

        if handlers:
            print("     Handlers:")
            for h in handlers:
                h_domain = getattr(h, "domain", "?")
                h_path = getattr(h, "handler_path", "?")
                print(f"       • {h_domain} → {h_path}")
        else:
            print("     Handlers: (none)")

    print(f"\n{'─' * 70}")
    print(f"  Total modules: {len(modules)}")
    print()


# ---------------------------------------------------------------------------
# inspect config
# ---------------------------------------------------------------------------


def inspect_config(verbose: bool = False) -> None:
    """Show resolved configuration from workspace + config files."""
    workspace_root = _ensure_workspace_root()

    print("\n  Configuration Inspection")
    print("=" * 70)

    ws_file = get_workspace_file(workspace_root)
    print(f"\n  Workspace file: {ws_file.name if ws_file else 'NOT FOUND'}")
    print(f"  Workspace root: {workspace_root}")

    config_dir = workspace_root / "config"
    if config_dir.exists():
        config_files = sorted(config_dir.glob("*.py"))
        if config_files:
            print("\n  Config directory: config/ (legacy)")
            for cf in config_files:
                print(f"    • {cf.name}")

            if verbose:
                for cf in config_files:
                    print(f"\n  ── {cf.name} ──")
                    try:
                        content = cf.read_text(encoding="utf-8")
                        for line in content.strip().splitlines():
                            print(f"    {line}")
                    except Exception as e:
                        print(f"    Error reading: {e}")
        else:
            print("\n  Config: inline in workspace.py (AquilaConfig)")
    else:
        print("\n  Config: inline in workspace.py (AquilaConfig)")

    import os

    aquilia_vars = {k: v for k, v in os.environ.items() if k.startswith("AQUILIA_")}
    if aquilia_vars:
        print("\n  Environment variables:")
        for k, v in sorted(aquilia_vars.items()):
            print(f"    {k}={v}")
    else:
        print("\n  Environment variables: (none set)")

    print(f"\n{'─' * 70}")
    print()
