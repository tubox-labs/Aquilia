"""The workspace loader.

Replaces ten hand-rolled ``spec_from_file_location`` copies and five regex
parsers that scraped ``Module("...")`` out of ``workspace.py``. ``workspace.py``
is Python, so it is imported, not pattern-matched. The regex path survives only
as a fallback for a workspace whose imports fail.

Every module here is import-safe: nothing raises on a missing workspace, and
``sys.path`` bootstrapping happens once in ``ensure_importable``.
"""

from __future__ import annotations

import importlib.util
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from aquilia.cli.utils.workspace import find_workspace_root, get_workspace_file

__all__ = [
    "LoadedWorkspace",
    "ensure_importable",
    "load_manifest",
    "load_module_file",
    "load_workspace",
]

_MODULE_RE = re.compile(r'Module\(\s*["\']([^"\']+)["\']')


def ensure_importable(workspace_root: Path) -> str:
    """Put the workspace root on ``sys.path`` (idempotent).

    Several commands scanned module files without doing this, so imports
    silently failed and the scan reported "nothing found" as success.
    """
    resolved = str(workspace_root.resolve())
    if resolved not in sys.path:
        sys.path.insert(0, resolved)
    return resolved


def load_module_file(path: Path, module_name: str) -> Any | None:
    """Import a standalone .py file, returning the module or ``None``."""
    if not path.exists():
        return None
    try:
        spec = importlib.util.spec_from_file_location(module_name, path)
        if not spec or not spec.loader:
            return None
        mod = importlib.util.module_from_spec(spec)
        sys.modules[spec.name] = mod
        spec.loader.exec_module(mod)
        return mod
    except Exception:
        return None


def load_manifest(workspace_root: Path, module_name: str) -> Any | None:
    """Load a module's ``AppManifest`` instance, or ``None``."""
    ensure_importable(workspace_root)
    manifest_path = workspace_root / "modules" / module_name / "manifest.py"
    mod = load_module_file(manifest_path, f"_aq_manifest_{module_name}")
    if mod is None:
        return None

    manifest_obj = getattr(mod, "manifest", None)
    if manifest_obj is not None:
        return manifest_obj

    try:
        from aquilia.manifest import AppManifest
    except Exception:
        return None
    for obj in vars(mod).values():
        if isinstance(obj, AppManifest):
            return obj
    return None


@dataclass
class LoadedWorkspace:
    """A resolved workspace: paths, declared modules, and loaded manifests.

    ``module_names`` comes from importing ``workspace.py`` when possible and
    falls back to a regex scan, so a workspace with a broken import is still
    inspectable rather than reported as empty.
    """

    root: Path
    workspace_file: Path | None = None
    module_names: list[str] = field(default_factory=list)
    workspace_obj: Any | None = None
    load_error: str | None = None
    used_fallback: bool = False
    _manifests: dict[str, Any] = field(default_factory=dict, repr=False)
    _route_prefixes: dict[str, str] = field(default_factory=dict, repr=False)

    @property
    def exists(self) -> bool:
        return self.workspace_file is not None

    @property
    def modules_dir(self) -> Path:
        return self.root / "modules"

    def module_dir(self, name: str) -> Path:
        return self.modules_dir / name

    def manifest(self, module_name: str) -> Any | None:
        """Load and cache a module's manifest."""
        if module_name not in self._manifests:
            self._manifests[module_name] = load_manifest(self.root, module_name)
        return self._manifests[module_name]

    def manifests(self) -> dict[str, Any]:
        """All declared modules mapped to their manifest (or ``None``)."""
        return {name: self.manifest(name) for name in self.module_names}

    @property
    def starter_module(self) -> str | None:
        """The ``.starter("name")`` declaration, if the file exists.

        The server mounts this controller at ``GET /``. The old CLI ignored it,
        so a workspace serving 6 routes reported 5 even after the count bug.
        """
        name = getattr(self.workspace_obj, "_starter", None)
        if not isinstance(name, str) or not name:
            return None
        return name if (self.root / f"{name}.py").exists() else None

    def route_prefix(self, module_name: str) -> str:
        """The module's ``route_prefix`` from workspace.py, or ``""``.

        The runtime composes ``route_prefix + controller.prefix + path``. The
        old CLI ignored this, so a module mounted at ``/users`` displayed its
        routes at ``/`` -- the paths shown were not the paths served.
        """
        return self._route_prefixes.get(module_name, "")

    def existing_module_dirs(self) -> list[str]:
        """Module directories actually on disk (may differ from declared)."""
        if not self.modules_dir.is_dir():
            return []
        return sorted(d.name for d in self.modules_dir.iterdir() if d.is_dir() and not d.name.startswith(("_", ".")))


def _module_names_from_source(ws_file: Path) -> list[str]:
    """Regex fallback: scan ``Module("name")`` skipping commented lines."""
    try:
        lines = ws_file.read_text(encoding="utf-8").splitlines()
    except Exception:
        return []
    active = [ln for ln in lines if not ln.lstrip().startswith("#")]
    return _MODULE_RE.findall("\n".join(active))


def _modules_from_obj(workspace_obj: Any) -> tuple[list[str], dict[str, str]]:
    """Pull declared module names and route prefixes off a Workspace instance.

    ``Module("users").route_prefix("/users")`` stores onto a ``ModuleConfig``,
    which is what ``Workspace.modules`` actually holds.
    """
    names: list[str] = []
    prefixes: dict[str, str] = {}
    modules = getattr(workspace_obj, "modules", None) or getattr(workspace_obj, "_modules", None) or []
    try:
        iterator = list(modules.values()) if isinstance(modules, dict) else list(modules)
    except Exception:
        return names, prefixes
    for entry in iterator:
        name = entry if isinstance(entry, str) else getattr(entry, "name", None) or getattr(entry, "module_name", None)
        if not (isinstance(name, str) and name):
            continue
        names.append(name)
        config = getattr(entry, "_config", None) or entry
        prefix = getattr(config, "route_prefix", None)
        if isinstance(prefix, str) and prefix:
            prefixes[name] = prefix
    return names, prefixes


def load_workspace(start: Path | None = None, *, import_workspace: bool = True) -> LoadedWorkspace:
    """Locate and load the workspace. Never raises.

    Set ``import_workspace=False`` to stay purely static (no user module-level
    code executes) -- used by checks that must not have side effects.
    """
    root = find_workspace_root(start or Path.cwd()) or (start or Path.cwd())
    ws_file = get_workspace_file(root)
    ws = LoadedWorkspace(root=root, workspace_file=ws_file)
    if ws_file is None:
        return ws

    if import_workspace:
        ensure_importable(root)
        mod = load_module_file(ws_file, "_aq_workspace")
        if mod is not None:
            ws.workspace_obj = getattr(mod, "workspace", None) or getattr(mod, "ws", None)
            if ws.workspace_obj is not None:
                ws.module_names, ws._route_prefixes = _modules_from_obj(ws.workspace_obj)
        else:
            ws.load_error = f"Could not import {ws_file.name}"

    if not ws.module_names:
        ws.module_names = _module_names_from_source(ws_file)
        ws.used_fallback = import_workspace
    return ws
