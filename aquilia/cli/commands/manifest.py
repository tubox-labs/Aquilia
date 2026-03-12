"""
Manifest management commands.

Provides commands to update and manage manifest.py files.
Supports both manifest formats:
  1. AppManifest dataclass:   manifest = AppManifest(name=..., controllers=[...], services=[...])
  2. Module builder fluent:   manifest = Module("...").register_controllers(...).register_services(...)

This command scans for controllers/services, detects drift against
what is declared in manifest.py, and optionally updates the file.
"""

import sys
import re
import ast
from pathlib import Path
import logging
from typing import List, Optional, Set, Tuple

from aquilia.utils.scanner import PackageScanner

logger = logging.getLogger("aquilia.cli.manifest")


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
        self.controllers: Set[str] = set()
        self.services: Set[str] = set()

    def parse(self) -> Tuple[List[str], List[str]]:
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
    def _extract_str(node: ast.AST) -> Optional[str]:
        if isinstance(node, ast.Constant) and isinstance(node.value, str):
            return node.value
        return None

    @staticmethod
    def _get_call_name(node: ast.Call) -> Optional[str]:
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


def update_manifest(module_name: str, workspace_root: Path, check: bool = False, freeze: bool = False, verbose: bool = False):
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
            controllers = scanner.scan_package(
                location,
                predicate=lambda cls: (
                    cls.__name__.endswith("Controller") or
                    cls.__name__.endswith("Handler") or
                    cls.__name__.endswith("View") or
                    hasattr(cls, '__controller_routes__') or
                    hasattr(cls, 'prefix')
                ),
            )
            all_controllers.extend(controllers)
        except ImportError:
            pass
    
    # Strategy 2: Enhanced individual file scanning
    try:
        import importlib
        from pathlib import Path
        module_package = importlib.import_module(base_package)
        if hasattr(module_package, '__path__'):
            module_dir = Path(module_package.__path__[0])
            
            # Intelligent file pattern matching
            controller_patterns = [
                "*controller*.py", "*ctrl*.py", "*handler*.py", 
                "*view*.py", "*route*.py", "*api*.py",
                "*endpoint*.py", "*resource*.py"
            ]
            
            candidate_files = set()
            for pattern in controller_patterns:
                candidate_files.update(module_dir.glob(pattern))
            
            # Also scan all Python files (fallback)
            all_py_files = set(module_dir.glob("*.py"))
            other_files = all_py_files - candidate_files - {
                module_dir / "__init__.py", 
                module_dir / "manifest.py",
                module_dir / "config.py",
                module_dir / "settings.py"
            }
            
            for py_file in sorted(candidate_files) + sorted(other_files):
                if py_file.stem in ['__init__', 'manifest', 'config', 'settings']:
                    continue
                
                # Quick content analysis for performance
                try:
                    content = py_file.read_text(encoding='utf-8', errors='ignore')
                    if not ('Controller' in content or 'Handler' in content or 
                           'View' in content or 'class ' in content):
                        continue
                except Exception:
                    continue
                
                submodule_name = f"{base_package}.{py_file.stem}"
                try:
                    file_controllers = scanner.scan_package(
                        submodule_name,
                        predicate=lambda cls: (
                            cls.__name__.endswith("Controller") or
                            cls.__name__.endswith("Handler") or
                            cls.__name__.endswith("View") or
                            hasattr(cls, '__controller_routes__') or
                            hasattr(cls, 'prefix') or
                            # Duck typing for controller-like classes
                            any(hasattr(cls, method) for method in ['get', 'post', 'put', 'delete'])
                        ),
                    )
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
    
    found_services = sorted(list(set(
        f"{s.__module__}:{s.__name__}" for s in services
    )))
    
    # 2. Parse Existing Manifest -- AST-based for both formats
    content = manifest_path.read_text(encoding="utf-8")
    
    try:
        parser = _ManifestParser(content)
        existing_controllers, existing_services = parser.parse()
    except SyntaxError as e:
        print(f"Error: manifest.py has a syntax error at line {e.lineno}: {e.msg}")
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
    if manifest_format == "module":
        # Module builder: replace register_controllers/register_services calls
        sync_marker = "# --- Synced Resources (aq manifest update) ---"

        def generate_builder_block(method: str, items: List[str]) -> str:
            if not items:
                return ""
            items_str = ",\n    ".join([f'"{item}"' for item in items])
            return f"\nmanifest.{method}(\n    {items_str}\n)\n"

        new_block = f"\n\n{sync_marker}"
        new_block += generate_builder_block("register_controllers", found_controllers)
        new_block += generate_builder_block("register_services", found_services)

        if sync_marker in content:
            parts = content.split(sync_marker)
            content = parts[0].rstrip() + new_block
        else:
            content = content.rstrip() + new_block

    else:
        # AppManifest dataclass: update controllers=[...] and services=[...] lists in-place
        # Use regex for targeted replacement of list contents
        ctrl_items = ", ".join(f'"{c}"' for c in found_controllers)
        svc_items = ", ".join(f'"{s}"' for s in found_services)

        # Replace controllers list
        content = re.sub(
            r'(controllers\s*=\s*\[)[^\]]*(\])',
            rf'\g<1>{ctrl_items}\2',
            content,
            count=1,
        )

        # Replace services list (only simple string lists -- ServiceConfig objects untouched)
        # Only replace if services are plain strings, not ServiceConfig objects
        if "ServiceConfig(" not in content:
            content = re.sub(
                r'(services\s*=\s*\[)[^\]]*(\])',
                rf'\g<1>{svc_items}\2',
                content,
                count=1,
            )
    
    # Handle Freeze Mode (Disable autodiscovery)
    if freeze:
        # Regex replace .auto_discover(True) -> .auto_discover(False)
        content = re.sub(r'\.auto_discover\(True\)', '.auto_discover(False)', content)
        # Also handle cases where it might be omitted or default (trickier, implying explicit True is best practice)
        print(f" Freezing manifest (auto_discover=False)")
        
    manifest_path.write_text(content, encoding="utf-8")
    print(f"Updated {manifest_path.relative_to(workspace_root)}")
    
    if missing_controllers or missing_services:
        print(f"  Synced {len(missing_controllers) + len(missing_services)} new items.")
