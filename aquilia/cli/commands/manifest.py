"""
Manifest management commands.

Provides commands to update and manage manifest.py files.
Supports both manifest formats:
  1. AppManifest dataclass:   manifest = AppManifest(name=..., controllers=[...], services=[...])
  2. Module builder fluent:   manifest = Module("...").register_controllers(...).register_services(...)

This command scans for controllers/services, detects drift against
what is declared in manifest.py, and optionally updates the file.

Legacy ``Module``-builder manifests are rewritten to the modern
``AppManifest`` syntax -- ``Module.register_controllers()`` is a
deprecated no-op (audit F-MAN-10 / N-3), so syncing into those calls
wrote dead code.
"""

import ast
import logging
import re
import sys
from pathlib import Path

from aquilia.utils.scanner import PackageScanner

logger = logging.getLogger("aquilia.cli.manifest")


def _is_controller_class(cls: type) -> bool:
    """Controller detection for ``aq manifest update`` scans.

    The old check duck-typed on ``get``/``post``/``put``/``delete``
    methods, which classified any service or model with a ``get`` method
    as a controller (audit N-2).  Only explicit controller markers count:
    subclassing the ``Controller`` base, the route metadata marker, or a
    controller naming convention.
    """
    from aquilia.controller import Controller

    try:
        if issubclass(cls, Controller):
            return True
    except TypeError:
        # Non-class objects slipped into the scan -- not a controller.
        return False
    return (
        hasattr(cls, "__controller_routes__")
        or hasattr(cls, "prefix")
        or cls.__name__.endswith("Controller")
        or cls.__name__.endswith("Handler")
        or cls.__name__.endswith("View")
    )


def _replace_manifest_list(source: str, field_name: str, items: list[str]) -> str | None:
    """Replace an ``AppManifest(...)`` keyword list in place using AST spans.

    Returns the rewritten source, or ``None`` when the field is not
    declared as a plain string list (missing, or holding ServiceConfig
    objects) -- callers must leave those alone.

    The old raw ``re.sub`` matched the first *textual*
    ``controllers = [`` occurrence, which could be a commented-out list
    (audit N-5).  AST spans always target the real declaration.
    """
    try:
        tree = ast.parse(source)
    except SyntaxError:
        return None

    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        func = node.func
        if isinstance(func, ast.Name):
            func_name = func.id
        elif isinstance(func, ast.Attribute):
            func_name = func.attr
        else:
            continue
        if func_name != "AppManifest":
            continue

        for kw in node.keywords:
            if kw.arg != field_name or not isinstance(kw.value, ast.List):
                continue
            # Only rewrite lists of plain string refs; ServiceConfig-style
            # entries carry configuration that a path-only rewrite drops.
            if not all(isinstance(elt, ast.Constant) and isinstance(elt.value, str) for elt in kw.value.elts):
                return None

            lines = source.split("\n")
            lst = kw.value
            indent = " " * lst.col_offset
            if items:
                entries = "".join(f'\n{indent}    "{item}",' for item in items)
                replacement = f"[{entries}\n{indent}]"
            else:
                replacement = "[]"

            s_line, s_col = lst.lineno - 1, lst.col_offset
            e_line, e_col = lst.end_lineno - 1, lst.end_col_offset
            lines[s_line : e_line + 1] = [lines[s_line][:s_col] + replacement + lines[e_line][e_col:]]
            return "\n".join(lines)

    return None


def _format_ref_list(items: list[str]) -> str:
    """Render a list of refs as a multi-line Python list literal."""
    if not items:
        return "[]"
    entries = "".join(f'\n        "{item}",' for item in items)
    return f"[{entries}\n    ]"


def _extract_module_builder_metadata(source: str, module_name: str) -> dict:
    """Read identity metadata out of a legacy ``Module(...)`` builder manifest."""
    version = "0.1.0"
    description = f"{module_name.capitalize()} module"
    depends_on: list[str] = []
    try:
        tree = ast.parse(source)
    except SyntaxError:
        return {"version": version, "description": description, "depends_on": depends_on}

    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        if isinstance(node.func, ast.Name) and node.func.id == "Module":
            for kw in node.keywords:
                if kw.arg == "version" and isinstance(kw.value, ast.Constant):
                    version = str(kw.value.value)
                elif kw.arg == "description" and isinstance(kw.value, ast.Constant):
                    description = str(kw.value.value)
        elif isinstance(node.func, ast.Attribute) and node.func.attr == "depends_on":
            for arg in node.args:
                if isinstance(arg, ast.Constant) and isinstance(arg.value, str):
                    depends_on.append(arg.value)

    return {"version": version, "description": description, "depends_on": depends_on}


def _emit_modern_manifest(
    module_name: str,
    version: str,
    description: str,
    controllers: list[str],
    services: list[str],
    imports_list: list[str],
    freeze: bool = False,
) -> str:
    """Render a modern ``AppManifest`` manifest.py (audit N-3).

    ``Module.register_controllers()`` / ``register_services()`` are
    deprecated no-ops -- syncing into them wrote dead code.  The modern
    component declaration syntax is ``AppManifest(controllers=[...],
    services=[...])``.

    With ``freeze=True`` the emitted manifest declares
    ``auto_discover=False``: the legacy builder syntax is being replaced,
    so a post-hoc regex for ``.auto_discover(True)`` would find nothing to
    rewrite and the freeze would silently not happen (audit N-4).
    """
    imports_line = ""
    if imports_list:
        deps = ", ".join(f'"{dep}"' for dep in imports_list)
        imports_line = f"\n    imports=[{deps}],"
    freeze_line = "\n    auto_discover=False," if freeze else ""

    return (
        f'"""\n'
        f"Module Manifest: {module_name}\n"
        f"Generated by: aq manifest update {module_name}\n"
        f'"""\n\n'
        f"from aquilia import AppManifest\n\n\n"
        f"manifest = AppManifest(\n"
        f'    name="{module_name}",\n'
        f'    version="{version}",\n'
        f'    description="{description}",\n'
        f"    controllers={_format_ref_list(controllers)},\n"
        f"    services={_format_ref_list(services)},"
        f"{imports_line}"
        f"{freeze_line}\n"
        f")\n\n\n"
        f'__all__ = ["manifest"]\n'
    )


# ═══════════════════════════════════════════════════════════════════════════
# AST-Based Manifest Parser
# ═══════════════════════════════════════════════════════════════════════════


class _ManifestParser:
    """
    Parse manifest.py with AST to extract declared controllers/services.

    Handles both declaration styles:
      - AppManifest(controllers=["a:B", ...], services=[ServiceConfig(...), ...])
      - Module("name").register_controllers("a:B", ...).register_services("a:B", ...)
    """

    def __init__(self, source: str):
        self.source = source
        self.tree = ast.parse(source)
        self.controllers: set[str] = set()
        self.services: set[str] = set()

    def parse(self) -> tuple[list[str], list[str]]:
        """Parse and return (controllers, services)."""
        for node in ast.walk(self.tree):
            # ── AppManifest(...) dataclass ──
            if isinstance(node, ast.Call):
                func_name = self._get_call_name(node)
                if func_name == "AppManifest":
                    self._extract_appmanifest_args(node)
                # ── Module(...).register_controllers(...) builder ──
                elif func_name in ("register_controllers", "register_services"):
                    target = "controllers" if func_name == "register_controllers" else "services"
                    for arg in node.args:
                        val = self._extract_str(arg)
                        if val:
                            getattr(self, target).add(val)

        return sorted(self.controllers), sorted(self.services)

    def _extract_appmanifest_args(self, call: ast.Call):
        for kw in call.keywords:
            if kw.arg == "controllers" and isinstance(kw.value, ast.List):
                for elt in kw.value.elts:
                    val = self._extract_str(elt)
                    if val:
                        self.controllers.add(val)
            elif kw.arg == "services" and isinstance(kw.value, ast.List):
                for elt in kw.value.elts:
                    val = self._extract_str(elt)
                    if val:
                        self.services.add(val)
                    # ServiceConfig("path:Class", ...) -- extract first positional arg
                    if isinstance(elt, ast.Call):
                        svc_name = self._get_call_name(elt)
                        if svc_name == "ServiceConfig" and elt.args:
                            sval = self._extract_str(elt.args[0])
                            if sval:
                                self.services.add(sval)
                        # Also check keyword arg: ServiceConfig(class_path="path:Class")
                        for skw in elt.keywords:
                            if skw.arg == "class_path":
                                sval = self._extract_str(skw.value)
                                if sval:
                                    self.services.add(sval)

    @staticmethod
    def _extract_str(node: ast.AST) -> str | None:
        if isinstance(node, ast.Constant) and isinstance(node.value, str):
            return node.value
        return None

    @staticmethod
    def _get_call_name(node: ast.Call) -> str | None:
        if isinstance(node.func, ast.Name):
            return node.func.id
        if isinstance(node.func, ast.Attribute):
            return node.func.attr
        return None


# ═══════════════════════════════════════════════════════════════════════════
# Manifest Format Detection
# ═══════════════════════════════════════════════════════════════════════════


def _detect_manifest_format(source: str) -> str:
    """
    Detect whether manifest.py uses AppManifest dataclass or Module builder.
    Returns 'appmanifest' or 'module'.
    """
    if "AppManifest(" in source:
        return "appmanifest"
    if "Module(" in source:
        return "module"
    # Fallback -- older projects may use either
    return "appmanifest"


def update_manifest(
    module_name: str, workspace_root: Path, check: bool = False, freeze: bool = False, verbose: bool = False
):
    """
    Update manifest.py with auto-discovered resources.

    Args:
        module_name: Name of the module
        workspace_root: Root of the workspace
        check: If True, fail if updates are needed (dry-run)
        freeze: If True, disable auto-discovery after updating
        verbose: Verbose output
    """
    module_dir = workspace_root / "modules" / module_name
    manifest_path = module_dir / "manifest.py"

    if not manifest_path.exists():
        print(f"Error: Module '{module_name}' not found or missing manifest.py")
        sys.exit(1)

    if verbose:
        print(f"Scanning module '{module_name}'...")

    # 1. Scan for resources
    scanner = PackageScanner()
    base_package = f"modules.{module_name}"

    # N-1 (data-destruction guard): the package scans below swallow
    # ImportError.  When the workspace package could not be imported, the
    # scan "found" nothing, the diff classified every declared component as
    # "extra", and the rewrite EMPTIED the manifest's lists.  Verify the
    # package imports first and refuse to touch the manifest when it does
    # not.
    import importlib

    ws_abs = str(workspace_root.resolve())
    if ws_abs not in sys.path:
        sys.path.insert(0, ws_abs)
    try:
        importlib.import_module(base_package)
    except Exception as e:
        print(f"Error: could not import {base_package} ({e}); refusing to update manifest")
        sys.exit(1)

    # Enhanced Controller Discovery with Intelligence
    all_controllers = []

    # Strategy 1: Standard subpackage scanning
    standard_locations = [
        f"{base_package}.controllers",
        f"{base_package}.test_routes",
        f"{base_package}.handlers",
        f"{base_package}.views",
        f"{base_package}.routes",
    ]

    for location in standard_locations:
        try:
            controllers = scanner.scan_package(location, predicate=_is_controller_class)
            all_controllers.extend(controllers)
        except ImportError:
            pass

    # Strategy 2: Enhanced individual file scanning
    try:
        module_package = importlib.import_module(base_package)
        if hasattr(module_package, "__path__"):
            module_dir = Path(module_package.__path__[0])

            # Intelligent file pattern matching
            controller_patterns = [
                "*controller*.py",
                "*ctrl*.py",
                "*handler*.py",
                "*view*.py",
                "*route*.py",
                "*api*.py",
                "*endpoint*.py",
                "*resource*.py",
            ]

            candidate_files = set()
            for pattern in controller_patterns:
                candidate_files.update(module_dir.glob(pattern))

            # Also scan all Python files (fallback)
            all_py_files = set(module_dir.glob("*.py"))
            other_files = (
                all_py_files
                - candidate_files
                - {
                    module_dir / "__init__.py",
                    module_dir / "manifest.py",
                    module_dir / "config.py",
                    module_dir / "settings.py",
                }
            )

            for py_file in sorted(candidate_files) + sorted(other_files):
                if py_file.stem in ["__init__", "manifest", "config", "settings"]:
                    continue

                # Quick content analysis for performance
                try:
                    content = py_file.read_text(encoding="utf-8", errors="ignore")
                    if not (
                        "Controller" in content or "Handler" in content or "View" in content or "class " in content
                    ):
                        continue
                except Exception:
                    continue

                submodule_name = f"{base_package}.{py_file.stem}"
                try:
                    file_controllers = scanner.scan_package(submodule_name, predicate=_is_controller_class)
                    all_controllers.extend(file_controllers)
                except Exception:
                    pass

    except Exception as scan_error:
        if verbose:
            print(f"  !  Enhanced individual file scan failed for {module_name}: {scan_error}")

    # Deduplicate results
    unique_controllers = {}
    for controller in all_controllers:
        key = f"{controller.__module__}:{controller.__name__}"
        if key not in unique_controllers:
            unique_controllers[key] = controller

    found_controllers = sorted(unique_controllers.keys())

    # Discover Services
    services = scanner.scan_package(
        f"{base_package}.services",
        predicate=lambda cls: cls.__name__.endswith("Service") or hasattr(cls, "__di_scope__"),
    )

    found_services = sorted(list(set(f"{s.__module__}:{s.__name__}" for s in services)))

    # 2. Parse Existing Manifest -- AST-based for both formats
    original_content = manifest_path.read_text(encoding="utf-8")
    content = original_content

    try:
        parser = _ManifestParser(content)
        existing_controllers, existing_services = parser.parse()
    except SyntaxError as e:
        print(f"Error: manifest.py has a syntax error at line {e.lineno}: {e.msg}")
        sys.exit(1)

    # N-1 (belt and braces): even when the package imports, a scan that
    # found nothing while the manifest declares components is a failed
    # scan (a submodule raising on import is swallowed too).  Never write
    # a destructive diff from a failed scan.
    if not found_controllers and not found_services and (existing_controllers or existing_services):
        print(
            f"Error: scan of modules.{module_name} found no controllers/services while the "
            f"manifest declares {len(existing_controllers)} controller(s) and "
            f"{len(existing_services)} service(s); refusing to write a destructive diff"
        )
        sys.exit(1)

    manifest_format = _detect_manifest_format(content)

    # Compute Diff
    missing_controllers = set(found_controllers) - set(existing_controllers)
    extra_controllers = set(existing_controllers) - set(found_controllers)

    missing_services = set(found_services) - set(existing_services)
    extra_services = set(existing_services) - set(found_services)

    has_changes = bool(missing_controllers or extra_controllers or missing_services or extra_services)

    # Handle Check Mode
    if check:
        if not has_changes:
            print(f"Manifest for '{module_name}' is in sync.")
            sys.exit(0)
        else:
            print(f"Manifest for '{module_name}' is OUT OF SYNC.")
            if missing_controllers:
                print(f"  Missing Controllers: {', '.join(missing_controllers)}")
            if extra_controllers:
                print(f"  Extra Controllers:   {', '.join(extra_controllers)}")
            if missing_services:
                print(f"  Missing Services:    {', '.join(missing_services)}")
            if extra_services:
                print(f"  Extra Services:      {', '.join(extra_services)}")
            sys.exit(1)

    # Handle Update
    if not has_changes and not freeze:
        print(f"Manifest for '{module_name}' is already up to date.")
        return

    # ── Update based on detected format ──
    freeze_applied = False
    if manifest_format == "module":
        # N-3: the Module builder's register_controllers()/register_services()
        # are deprecated NO-OPs -- syncing into them wrote dead code.  Rewrite
        # the manifest to the modern AppManifest syntax instead, preserving
        # the identity metadata and dependencies of the legacy declaration.
        # N-4: the rewrite drops the builder's `.auto_discover(True)` chain
        # element, so the freeze is baked into the emitted manifest here --
        # the regex below would otherwise find nothing and leave the
        # rewritten manifest auto-discovering.
        metadata = _extract_module_builder_metadata(content, module_name)
        content = _emit_modern_manifest(
            module_name=module_name,
            version=metadata["version"],
            description=metadata["description"],
            controllers=found_controllers,
            services=found_services,
            imports_list=metadata["depends_on"],
            freeze=freeze,
        )
        if freeze:
            freeze_applied = True
            print(" Freezing manifest (auto_discover=False)")

    else:
        # AppManifest dataclass: update controllers=[...] and services=[...]
        # lists in place via AST spans (N-5).  The old raw re.sub matched the
        # first textual `controllers = [` occurrence, which can be a
        # commented-out list.  Fields that are not plain string lists (e.g.
        # ServiceConfig objects) are left untouched.
        # Only a field that actually drifted is rewritten -- reformatting an
        # in-sync list on every `--freeze` run rewrote (and reformatted) the
        # file while claiming an "Updated" that changed nothing (audit N-4).
        if missing_controllers or extra_controllers:
            replaced = _replace_manifest_list(content, "controllers", found_controllers)
            if replaced is not None:
                content = replaced
        if missing_services or extra_services:
            replaced = _replace_manifest_list(content, "services", found_services)
            if replaced is not None:
                content = replaced

    # Handle Freeze Mode (Disable autodiscovery)
    if freeze and not freeze_applied:
        # N-4: handle BOTH the builder form `.auto_discover(True)` and the
        # AppManifest keyword form `auto_discover=True`; report honestly
        # when neither is present.
        frozen = re.sub(r"\.auto_discover\(True\)", ".auto_discover(False)", content)
        frozen = re.sub(r"\bauto_discover\s*=\s*True\b", "auto_discover=False", frozen)
        if frozen != content:
            content = frozen
            print(" Freezing manifest (auto_discover=False)")
        else:
            print(" Freeze: no auto_discover=True found -- nothing to disable")

    # N-5: validate the rewritten manifest with the AST parser before
    # committing it to disk; a failed write must never corrupt the file.
    try:
        ast.parse(content)
    except SyntaxError as e:
        print(f"Error: rewritten manifest.py has a syntax error at line {e.lineno}: {e.msg}; aborting write")
        sys.exit(1)

    # Honest reporting (F-MAN-05): only claim "Updated" when the content
    # actually changed -- e.g. `--freeze` on an already-frozen manifest.
    if content == original_content:
        print(f"Manifest for '{module_name}' is already up to date.")
        return

    manifest_path.write_text(content, encoding="utf-8")
    print(f"Updated {manifest_path.relative_to(workspace_root)}")

    if missing_controllers or missing_services:
        print(f"  Synced {len(missing_controllers) + len(missing_services)} new items.")
