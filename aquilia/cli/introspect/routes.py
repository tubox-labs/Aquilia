"""Route introspection.

The old ``inspect.py`` probed ``__controller_routes__``, ``__route__`` and
``_route_meta``. None of those exist -- the real attribute is
``__route_metadata__`` -- so every controller fell into a "routes could not be
extracted statically" branch that then counted the *controller* as one route.
A five-route controller reported 1.

This module calls ``ControllerCompiler`` -- the same component the server uses
at boot, with the same ``base_prefix`` -- so the reported paths are exactly
the paths the server serves, trailing slashes and all.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from aquilia.cli.core.workspace import LoadedWorkspace, ensure_importable, load_module_file

__all__ = ["RouteInfo", "ControllerRoutes", "extract_routes", "collect_routes"]


@dataclass
class RouteInfo:
    """One route, resolved to the path the server will serve."""

    http_method: str
    path: str
    full_path: str
    handler: str
    controller: str
    module: str
    tags: list[str]
    deprecated: bool = False
    status_code: int = 200

    @property
    def key(self) -> tuple[str, str]:
        """Identity for conflict detection."""
        return (self.http_method, self.full_path)


@dataclass
class ControllerRoutes:
    """Routes for a single controller, or the reason extraction failed."""

    controller: str
    module: str
    prefix: str
    routes: list[RouteInfo]
    error: str | None = None

    @property
    def ok(self) -> bool:
        return self.error is None


def _resolve_class(workspace_root: Path, ref: Any) -> tuple[Any | None, str, str | None]:
    """Resolve a manifest controller reference to a class object.

    Handles ``"module.path:ClassName"`` strings and already-imported classes.
    Returns ``(cls, display_name, error)``.
    """
    if not isinstance(ref, str):
        return ref, getattr(ref, "__name__", str(ref)), None

    ensure_importable(workspace_root)
    if ":" not in ref:
        return None, ref.split(".")[-1], f"Malformed reference '{ref}' (expected 'module:Class')"

    module_path, class_name = ref.rsplit(":", 1)
    try:
        import importlib

        mod = importlib.import_module(module_path)
    except Exception as exc:
        return None, class_name, f"Import failed for '{module_path}': {exc}"

    cls = getattr(mod, class_name, None)
    if cls is None:
        return None, class_name, f"'{class_name}' not found in '{module_path}'"
    return cls, class_name, None


def extract_routes(
    workspace_root: Path,
    ref: Any,
    module: str = "",
    module_prefix: str = "",
) -> ControllerRoutes:
    """Extract routes for one controller.

    Uses ``ControllerCompiler`` -- the same component the server calls at boot
    with the same ``base_prefix`` -- so reported paths are exactly the paths
    served, trailing slashes and all. Reimplementing prefix joining here is
    how the CLI previously drifted from the runtime.
    """
    cls, display, error = _resolve_class(workspace_root, ref)
    if cls is None:
        return ControllerRoutes(display, module, "", [], error=error)

    try:
        from aquilia.controller.compiler import ControllerCompiler

        compiled = ControllerCompiler().compile_controller(cls, base_prefix=module_prefix or "")
    except Exception as exc:
        return ControllerRoutes(display, module, "", [], error=f"Route compilation failed: {exc}")

    meta = getattr(compiled, "metadata", None)
    class_name = getattr(meta, "class_name", None) or getattr(cls, "__name__", display)
    class_tags = list(getattr(meta, "tags", []) or [])
    routes: list[RouteInfo] = []

    for route in getattr(compiled, "routes", []) or []:
        rmeta = getattr(route, "route_metadata", None)
        routes.append(
            RouteInfo(
                http_method=getattr(route, "http_method", "GET"),
                path=getattr(rmeta, "path_template", "") or "",
                full_path=getattr(route, "full_path", "") or "",
                handler=getattr(rmeta, "handler_name", None) or "?",
                controller=class_name,
                module=module,
                tags=list(getattr(rmeta, "tags", []) or []) or class_tags,
                deprecated=bool(getattr(rmeta, "deprecated", False)),
                status_code=int(getattr(rmeta, "status_code", 200) or 200),
            )
        )

    return ControllerRoutes(class_name, module, module_prefix or "", routes)


def collect_routes(ws: LoadedWorkspace) -> list[ControllerRoutes]:
    """Every controller in every declared module, in stable order.

    Includes the workspace-root starter controller if ``workspace.py`` declares
    ``.starter("name")`` and the file exists. The server mounts it at ``GET /``.
    """
    results: list[ControllerRoutes] = []

    # ── Starter controller (workspace root, no prefix) ──
    if ws.starter_module:
        from aquilia.controller import Controller

        mod = load_module_file(ws.root / f"{ws.starter_module}.py", f"_aq_starter_{ws.starter_module}")
        if mod is not None:
            for attr_name in dir(mod):
                obj = getattr(mod, attr_name, None)
                if isinstance(obj, type) and issubclass(obj, Controller) and obj is not Controller:
                    results.append(extract_routes(ws.root, obj, module="(starter)", module_prefix=""))
                    break

    # ── Module controllers ──
    for module_name in sorted(ws.module_names):
        manifest = ws.manifest(module_name)
        if manifest is None:
            results.append(
                ControllerRoutes(
                    controller="",
                    module=module_name,
                    prefix="",
                    routes=[],
                    error=f"manifest for '{module_name}' is not loadable",
                )
            )
            continue
        module_prefix = ws.route_prefix(module_name)
        for ref in getattr(manifest, "controllers", []) or []:
            results.append(extract_routes(ws.root, ref, module_name, module_prefix))
    return results


def count_routes(ws: LoadedWorkspace) -> int:
    """Total real routes across the workspace.

    The previous CLI reported the *controller* count here, so a five-route
    controller displayed as "1 route".
    """
    return sum(len(cr.routes) for cr in collect_routes(ws))
