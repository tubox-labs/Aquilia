"""Workspace checks -- the core health surface.

Consolidates what ``doctor.py`` and ``validate.py`` each did partially and
inconsistently. Every check yields findings with an explicit severity rather
than printing, so ``doctor``, ``validate``, ``--json`` and the tests all read
the same data.
"""

from __future__ import annotations

import importlib
import sys
from collections.abc import Iterator

from aquilia.cli.checks.base import Finding, register_check
from aquilia.cli.core.context import AqContext
from aquilia.cli.core.workspace import ensure_importable
from aquilia.cli.introspect.routes import collect_routes
from aquilia.faults.core import Severity

__all__ = [
    "check_db_reachable",
    "check_di_providers",
    "check_manifest_loadable",
    "check_manifest_refs",
    "check_modules",
    "check_python",
    "check_route_conflicts",
    "check_routes_parsable",
    "check_workspace",
]

MIN_PYTHON = (3, 10)


@register_check(
    "env.python",
    "Interpreter meets the minimum supported version",
    tags=["env", "quick"],
    subsystem="env",
    requires_workspace=False,
)
def check_python(ctx: AqContext) -> Iterator[Finding]:
    if sys.version_info[:2] < MIN_PYTHON:
        got = ".".join(str(p) for p in sys.version_info[:3])
        yield Finding(
            "AQ_PY_TOO_OLD",
            f"Python {got} is below the required {MIN_PYTHON[0]}.{MIN_PYTHON[1]}",
            Severity.FATAL,
            remedy=f"Use Python {MIN_PYTHON[0]}.{MIN_PYTHON[1]}+",
        )


@register_check(
    "workspace.present",
    "workspace.py exists and imports cleanly",
    tags=["workspace", "quick"],
    subsystem="workspace",
)
def check_workspace(ctx: AqContext) -> Iterator[Finding]:
    ws = ctx.workspace
    if ws.load_error:
        yield Finding(
            "AQ_WS_LOAD_FAILED",
            ws.load_error,
            Severity.ERROR,
            location=str(ws.workspace_file or ws.root),
            remedy="Fix the import error in workspace.py",
        )
        return
    if ws.used_fallback:
        yield Finding(
            "AQ_WS_REGEX_FALLBACK",
            "workspace.py did not expose a `workspace` object; module list came from a text scan",
            Severity.WARN,
            location=str(ws.workspace_file or ws.root),
            remedy="Assign the Workspace instance to a module-level `workspace` variable",
        )


@register_check(
    "workspace.modules",
    "Declared modules exist on disk and are declared",
    tags=["workspace", "modules", "quick"],
    subsystem="workspace",
)
def check_modules(ctx: AqContext) -> Iterator[Finding]:
    ws = ctx.workspace
    declared = set(ws.module_names)
    on_disk = set(ws.existing_module_dirs())

    if not declared and not on_disk:
        yield Finding(
            "AQ_WS_NO_MODULES",
            "Workspace declares no modules",
            Severity.WARN,
            remedy="Create one with `aq add module <name>`",
        )
        return

    for missing in sorted(declared - on_disk):
        yield Finding(
            "AQ_MODULE_MISSING_DIR",
            f"Module '{missing}' is declared in workspace.py but modules/{missing}/ does not exist",
            Severity.ERROR,
            remedy="Create the module or remove it from workspace.py",
        )
    for orphan in sorted(on_disk - declared):
        yield Finding(
            "AQ_MODULE_NOT_DECLARED",
            f"modules/{orphan}/ exists but is not declared in workspace.py",
            Severity.WARN,
            remedy=f'Add Module("{orphan}") to workspace.py, or delete the directory',
        )


@register_check(
    "manifest.loadable",
    "Every declared module has an importable manifest",
    tags=["workspace", "manifest", "quick"],
    subsystem="manifest",
)
def check_manifest_loadable(ctx: AqContext) -> Iterator[Finding]:
    ws = ctx.workspace
    for name in sorted(ws.module_names):
        manifest_path = ws.module_dir(name) / "manifest.py"
        if not manifest_path.exists():
            yield Finding(
                "AQ_MANIFEST_MISSING",
                f"Module '{name}' has no manifest.py",
                Severity.ERROR,
                location=str(manifest_path),
                remedy="Every module needs a manifest.py declaring an AppManifest",
            )
            continue
        if ws.manifest(name) is None:
            yield Finding(
                "AQ_MANIFEST_NOT_LOADABLE",
                f"manifest.py for '{name}' could not be imported or exposes no AppManifest",
                Severity.ERROR,
                location=str(manifest_path),
                remedy="Check for syntax/import errors and a module-level `manifest = AppManifest(...)`",
            )


@register_check(
    "manifest.references",
    "Manifest component references resolve to real classes",
    tags=["manifest", "deep"],
    subsystem="manifest",
)
def check_manifest_refs(ctx: AqContext) -> Iterator[Finding]:
    """Catches the class of bug that let a corrupted manifest pass validation.

    ``aq manifest update`` could write a reference the runtime then rejected at
    boot, while ``aq validate`` still reported success.
    """
    ws = ctx.workspace
    ensure_importable(ws.root)
    fields = ("controllers", "services", "models", "middleware", "tasks", "socket_controllers")

    for name in sorted(ws.module_names):
        manifest = ws.manifest(name)
        if manifest is None:
            continue
        for field_name in fields:
            for ref in getattr(manifest, field_name, []) or []:
                if not isinstance(ref, str):
                    continue
                location = f"modules/{name}/manifest.py"
                if ":" not in ref:
                    yield Finding(
                        "AQ_REF_MALFORMED",
                        f"{name}.{field_name}: '{ref}' is not in 'module.path:ClassName' form",
                        Severity.ERROR,
                        location=location,
                        remedy="Use the 'module.path:ClassName' reference format",
                    )
                    continue
                module_path, class_name = ref.rsplit(":", 1)
                try:
                    mod = importlib.import_module(module_path)
                except Exception as exc:
                    yield Finding(
                        "AQ_REF_IMPORT_FAILED",
                        f"{name}.{field_name}: cannot import '{module_path}' ({exc})",
                        Severity.ERROR,
                        location=location,
                    )
                    continue
                if getattr(mod, class_name, None) is None:
                    yield Finding(
                        "AQ_REF_MISSING_ATTR",
                        f"{name}.{field_name}: '{class_name}' not found in '{module_path}'",
                        Severity.ERROR,
                        location=location,
                        remedy="The manifest references a class that does not exist",
                    )


@register_check(
    "routes.parsable",
    "All controller route metadata extracts cleanly",
    tags=["routes", "deep"],
    subsystem="routes",
)
def check_routes_parsable(ctx: AqContext) -> Iterator[Finding]:
    """Surface route extraction errors the old CLI hid."""
    ws = ctx.workspace
    for cr in collect_routes(ws):
        if cr.error:
            yield Finding(
                "AQ_ROUTE_EXTRACTION_FAILED",
                f"{cr.module}: {cr.error}",
                Severity.ERROR,
                location=f"modules/{cr.module}/",
                remedy="Fix the import or metadata issue in the controller",
            )


@register_check(
    "routes.conflicts",
    "No route path + method collisions",
    tags=["routes", "deep"],
    subsystem="routes",
)
def check_route_conflicts(ctx: AqContext) -> Iterator[Finding]:
    """Detect overlapping routes before boot."""
    ws = ctx.workspace
    seen: dict[tuple[str, str], tuple[str, str]] = {}
    for cr in collect_routes(ws):
        if cr.error:
            continue
        for route in cr.routes:
            key = (route.http_method, route.full_path)
            if key in seen:
                prev_mod, prev_ctrl = seen[key]
                yield Finding(
                    "AQ_ROUTE_CONFLICT",
                    f"{route.http_method} {route.full_path} is declared in both {prev_mod}.{prev_ctrl} and {cr.module}.{cr.controller}",
                    Severity.ERROR,
                    location=f"modules/{cr.module}/",
                    remedy="Remove or rename one of the conflicting routes",
                )
            else:
                seen[key] = (cr.module, cr.controller)


@register_check(
    "di.providers",
    "Service providers are registered and resolvable",
    tags=["di", "deep"],
    subsystem="di",
)
def check_di_providers(ctx: AqContext) -> Iterator[Finding]:
    """Surface DI wiring errors before runtime."""
    ws = ctx.workspace
    provider_count = 0
    for name in sorted(ws.module_names):
        manifest = ws.manifest(name)
        if manifest is None:
            continue
        for svc_ref in getattr(manifest, "services", []) or []:
            provider_count += 1
            if not isinstance(svc_ref, str) or ":" not in svc_ref:
                continue
            module_path, class_name = svc_ref.rsplit(":", 1)
            try:
                ensure_importable(ws.root)
                mod = importlib.import_module(module_path)
                if getattr(mod, class_name, None) is None:
                    yield Finding(
                        "AQ_DI_PROVIDER_MISSING",
                        f"{name}: provider '{class_name}' not found in '{module_path}'",
                        Severity.ERROR,
                        location=f"modules/{name}/manifest.py",
                    )
            except Exception as exc:
                yield Finding(
                    "AQ_DI_PROVIDER_UNLOADABLE",
                    f"{name}: provider '{svc_ref}' could not be imported ({exc})",
                    Severity.ERROR,
                    location=f"modules/{name}/manifest.py",
                )

    if provider_count == 0 and ws.module_names:
        yield Finding(
            "AQ_DI_NO_PROVIDERS",
            "No services registered across all modules",
            Severity.INFO,
        )


@register_check(
    "db.reachable",
    "Database configuration is valid and reachable",
    tags=["db", "deep"],
    subsystem="db",
)
def check_db_reachable(ctx: AqContext) -> Iterator[Finding]:
    """Confirms the DB is configured and reachable.

    The old ``doctor`` produced a 0 exit code even when the DB did not exist.
    This check makes that visible as an ERROR.
    """
    ws = ctx.workspace
    from pathlib import Path

    from aquilia.cli.core.workspace import load_module_file

    ws_mod = load_module_file(ws.workspace_file, "_aq_ws_db_check")
    if ws_mod is None:
        return
    workspace_obj = getattr(ws_mod, "workspace", None)
    if workspace_obj is None:
        return
    db_cfg = getattr(workspace_obj, "database", None) or getattr(workspace_obj, "_database", None)
    if db_cfg is None:
        yield Finding(
            "AQ_DB_NOT_CONFIGURED",
            "No database integration configured in workspace",
            Severity.WARN,
            remedy="Add DatabaseIntegration to workspace.py if you need persistence",
        )
        return
    db_path = getattr(db_cfg, "path", None)
    if db_path:
        resolved = Path(ws.root) / db_path
        if not resolved.exists():
            yield Finding(
                "AQ_DB_MISSING",
                f"Database file does not exist: {resolved}",
                Severity.ERROR,
                location=str(resolved),
                remedy="Run migrations to create the DB, or check the configured path",
            )
