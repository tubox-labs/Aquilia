"""
Auto-Discovery Engine -- AST-based component classification and manifest sync.

Architecture v2: Scans module directories for Python classes, classifies them
by base class / decorator without importing, and can auto-update manifest.py
files with discovered components.

Pipeline:
    FileScanner → ASTClassifier → ManifestDiffer → ManifestWriter
"""

from __future__ import annotations

import ast
import logging
import re
from dataclasses import dataclass, field
from pathlib import Path

from ..manifest import ComponentKind

logger = logging.getLogger("aquilia.discovery")


# ============================================================================
# Data structures
# ============================================================================


@dataclass
class ClassifiedComponent:
    """A component discovered by the AST classifier."""

    name: str  # Class name
    kind: ComponentKind  # Detected component kind
    file_path: Path  # Absolute file path
    line: int  # Line number in file
    import_path: str = ""  # Computed "module.path:ClassName"
    bases: list[str] = field(default_factory=list)
    decorators: list[str] = field(default_factory=list)

    def __repr__(self) -> str:
        return f"<{self.kind.value}:{self.name} @ {self.file_path.name}:{self.line}>"


@dataclass
class DiscoveryResult:
    """Result of scanning a single module."""

    module_name: str
    components: list[ClassifiedComponent] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)
    files_scanned: int = 0

    @property
    def controllers(self) -> list[ClassifiedComponent]:
        return [c for c in self.components if c.kind == ComponentKind.CONTROLLER]

    @property
    def services(self) -> list[ClassifiedComponent]:
        return [c for c in self.components if c.kind == ComponentKind.SERVICE]

    @property
    def middleware(self) -> list[ClassifiedComponent]:
        return [c for c in self.components if c.kind == ComponentKind.MIDDLEWARE]

    @property
    def guards(self) -> list[ClassifiedComponent]:
        return [c for c in self.components if c.kind == ComponentKind.GUARD]

    @property
    def models(self) -> list[ClassifiedComponent]:
        return [c for c in self.components if c.kind == ComponentKind.MODEL]

    @property
    def pipes(self) -> list[ClassifiedComponent]:
        return [c for c in self.components if c.kind == ComponentKind.PIPE]

    @property
    def interceptors(self) -> list[ClassifiedComponent]:
        return [c for c in self.components if c.kind == ComponentKind.INTERCEPTOR]


@dataclass
class SyncAction:
    """Describes a change to make to a manifest file."""

    action: str  # "add" or "remove"
    component: ClassifiedComponent
    field_name: str  # Manifest field (controllers, services, etc.)


@dataclass
class SyncReport:
    """Report from a manifest sync operation."""

    module_name: str
    manifest_path: Path
    actions: list[SyncAction] = field(default_factory=list)
    dry_run: bool = False

    @property
    def added(self) -> list[SyncAction]:
        return [a for a in self.actions if a.action == "add"]

    @property
    def has_changes(self) -> bool:
        return len(self.actions) > 0


# ============================================================================
# AST Classifier
# ============================================================================


class ASTClassifier:
    """
    Classifies Python classes using AST analysis -- no imports needed.

    Inspects base classes and decorators to determine component kind.
    Safe for use with untrusted code since it never executes anything.
    """

    # Base classes that indicate component kind
    CONTROLLER_BASES: set[str] = {
        "Controller",
        "BaseController",
        "RestController",
    }
    SOCKET_CONTROLLER_BASES: set[str] = {
        "WebSocketController",
        "SocketController",
    }
    SERVICE_BASES: set[str] = {
        "Service",
        "BaseService",
    }
    MIDDLEWARE_BASES: set[str] = {
        "Middleware",
        "BaseMiddleware",
    }
    GUARD_BASES: set[str] = {
        "Guard",
        "BaseGuard",
        "AuthGuard",
    }
    PIPE_BASES: set[str] = {
        "Pipe",
        "BasePipe",
        "ValidationPipe",
        "TransformPipe",
    }
    INTERCEPTOR_BASES: set[str] = {
        "Interceptor",
        "BaseInterceptor",
        "LoggingInterceptor",
        "CacheInterceptor",
    }
    MODEL_BASES: set[str] = {
        "Model",
        "BaseModel",
        "AquiliaModel",
    }

    # Decorators that indicate component kind
    SERVICE_DECORATORS: set[str] = {
        "service",
        "injectable",
        "provides",
        "provider",
    }
    GUARD_DECORATORS: set[str] = {
        "guard",
        "auth_guard",
    }
    PIPE_DECORATORS: set[str] = {
        "pipe",
        "transform",
        "validate",
    }
    INTERCEPTOR_DECORATORS: set[str] = {
        "interceptor",
        "intercept",
    }

    def classify_file(self, file_path: Path) -> list[ClassifiedComponent]:
        """
        Parse a Python file with AST and classify its classes.

        Args:
            file_path: Path to the Python file to analyze

        Returns:
            List of classified components found in the file
        """
        try:
            source = file_path.read_text(encoding="utf-8")
            tree = ast.parse(source, filename=str(file_path))
        except (SyntaxError, UnicodeDecodeError) as e:
            logger.warning(f"Failed to parse {file_path}: {e}")
            return []

        components = []
        for node in ast.iter_child_nodes(tree):
            if isinstance(node, ast.ClassDef):
                kind = self._classify_class(node)
                if kind is not None:
                    bases = self._extract_base_names(node)
                    decorators = self._extract_decorator_names(node)
                    components.append(
                        ClassifiedComponent(
                            name=node.name,
                            kind=kind,
                            file_path=file_path,
                            line=node.lineno,
                            bases=bases,
                            decorators=decorators,
                        )
                    )

        return components

    def _classify_class(self, node: ast.ClassDef) -> ComponentKind | None:
        """Classify a single class definition by its bases and decorators."""
        bases = set(self._extract_base_names(node))
        decorators = set(self._extract_decorator_names(node))

        # Check base classes (highest priority)
        if bases & self.CONTROLLER_BASES:
            return ComponentKind.CONTROLLER
        if bases & self.SOCKET_CONTROLLER_BASES:
            return ComponentKind.SOCKET_CONTROLLER
        if bases & self.GUARD_BASES:
            return ComponentKind.GUARD
        if bases & self.PIPE_BASES:
            return ComponentKind.PIPE
        if bases & self.INTERCEPTOR_BASES:
            return ComponentKind.INTERCEPTOR
        if bases & self.MIDDLEWARE_BASES:
            return ComponentKind.MIDDLEWARE
        if bases & self.MODEL_BASES:
            return ComponentKind.MODEL
        if bases & self.SERVICE_BASES:
            return ComponentKind.SERVICE

        # Check decorators (secondary)
        if decorators & self.SERVICE_DECORATORS:
            return ComponentKind.SERVICE
        if decorators & self.GUARD_DECORATORS:
            return ComponentKind.GUARD
        if decorators & self.PIPE_DECORATORS:
            return ComponentKind.PIPE
        if decorators & self.INTERCEPTOR_DECORATORS:
            return ComponentKind.INTERCEPTOR

        return None

    def _extract_base_names(self, node: ast.ClassDef) -> list[str]:
        """Extract base class names from a ClassDef node."""
        names = []
        for base in node.bases:
            if isinstance(base, ast.Name):
                names.append(base.id)
            elif isinstance(base, ast.Attribute):
                names.append(base.attr)
        return names

    def _extract_decorator_names(self, node: ast.ClassDef) -> list[str]:
        """Extract decorator names from a ClassDef node."""
        names = []
        for dec in node.decorator_list:
            if isinstance(dec, ast.Name):
                names.append(dec.id)
            elif isinstance(dec, ast.Attribute):
                names.append(dec.attr)
            elif isinstance(dec, ast.Call):
                func = dec.func
                if isinstance(func, ast.Name):
                    names.append(func.id)
                elif isinstance(func, ast.Attribute):
                    names.append(func.attr)
        return names


# ============================================================================
# File Scanner
# ============================================================================


class FileScanner:
    """Scans module directories for Python files matching discovery patterns."""

    # Files to skip during scanning
    SKIP_FILES: set[str] = {
        "__init__.py",
        "__pycache__",
        "manifest.py",
        "conftest.py",
        "setup.py",
        "workspace.py",
    }

    SKIP_PREFIXES: tuple[str, ...] = ("test_", "_", ".")

    def __init__(self, modules_dir: Path):
        self.modules_dir = modules_dir

    def scan_module(
        self,
        module_name: str,
        patterns: list[str] | None = None,
    ) -> list[Path]:
        """
        Find all Python files in a module directory.

        Args:
            module_name: Name of the module directory
            patterns: Optional list of filename stems to include
                      (e.g., ["controllers", "services", "guards"])

        Returns:
            List of Python file paths
        """
        module_dir = self.modules_dir / module_name
        if not module_dir.is_dir():
            logger.warning(f"Module directory not found: {module_dir}")
            return []

        files = []
        for py_file in module_dir.rglob("*.py"):
            stem = py_file.stem
            name = py_file.name

            # Skip excluded files
            if name in self.SKIP_FILES:
                continue
            if any(stem.startswith(p) for p in self.SKIP_PREFIXES):
                continue

            # If patterns specified, only include matching filenames
            if patterns and stem not in patterns and not any(stem.startswith(p) for p in patterns):
                continue

            files.append(py_file)

        return sorted(files)

    def discover_modules(self) -> list[str]:
        """Discover all module directories (contain __init__.py or manifest.py)."""
        modules = []
        if not self.modules_dir.is_dir():
            return modules

        for child in sorted(self.modules_dir.iterdir()):
            if not child.is_dir():
                continue
            if child.name.startswith((".", "_")):
                continue
            # A module directory must have __init__.py or manifest.py
            if (child / "__init__.py").exists() or (child / "manifest.py").exists():
                modules.append(child.name)

        return modules


# ============================================================================
# Manifest Differ
# ============================================================================


class ManifestDiffer:
    """Compares discovered components against declared manifest components."""

    KIND_TO_FIELD = {
        ComponentKind.CONTROLLER: "controllers",
        ComponentKind.SERVICE: "services",
        ComponentKind.MIDDLEWARE: "middleware",
        ComponentKind.GUARD: "guards",
        ComponentKind.PIPE: "pipes",
        ComponentKind.INTERCEPTOR: "interceptors",
        ComponentKind.MODEL: "models",
        ComponentKind.SOCKET_CONTROLLER: "socket_controllers",
        ComponentKind.SERIALIZER: "serializers",
    }

    def diff(
        self,
        discovered: list[ClassifiedComponent],
        manifest_refs: dict[str, list[str]],
    ) -> list[SyncAction]:
        """
        Calculate actions needed to sync manifest with discovered components.

        Args:
            discovered: Components found by the scanner
            manifest_refs: Current manifest component paths by field name

        Returns:
            List of sync actions to apply
        """
        actions = []

        for component in discovered:
            field_name = self.KIND_TO_FIELD.get(component.kind)
            if field_name is None:
                continue

            existing = manifest_refs.get(field_name, [])
            # Check if the component is already declared
            if not self._is_declared(component, existing):
                actions.append(
                    SyncAction(
                        action="add",
                        component=component,
                        field_name=field_name,
                    )
                )

        return actions

    def _is_declared(self, component: ClassifiedComponent, existing: list[str]) -> bool:
        """Check if a component is already declared in the manifest."""
        class_name = component.name
        import_path = component.import_path

        for ref in existing:
            # Match by full import path
            if ref == import_path:
                return True
            # Match by class name (after ':')
            if ":" in ref and ref.split(":", 1)[1] == class_name:
                return True
            # Match by just the class name string
            if ref == class_name:
                return True

        return False


# ============================================================================
# Manifest Writer
# ============================================================================


class ManifestWriter:
    """
    Safely updates manifest.py files using text manipulation.

    Uses regex-based insertion to add new component references to the
    appropriate list field in the AppManifest(...) call.
    """

    def write_sync_actions(
        self,
        manifest_path: Path,
        actions: list[SyncAction],
        dry_run: bool = False,
    ) -> int:
        """
        Apply sync actions to a manifest file.

        Args:
            manifest_path: Path to manifest.py
            actions: List of add/remove actions
            dry_run: If True, don't actually write

        Returns:
            Number of changes applied
        """
        if not actions:
            return 0

        source = manifest_path.read_text(encoding="utf-8")
        changes = 0

        for action in actions:
            if action.action == "add":
                new_source = self._add_component(source, action.field_name, action.component.import_path)
                if new_source != source:
                    source = new_source
                    changes += 1

        if changes > 0 and not dry_run:
            manifest_path.write_text(source, encoding="utf-8")

        return changes

    def _add_component(self, source: str, field_name: str, import_path: str) -> str:
        """
        Add a component reference to a field's list in the manifest source.

        Finds the field's list and appends the new import path string.
        """
        # Pattern: find `field_name=[...]` including multiline
        # We need to insert before the closing `]` of the list
        pattern = rf"({field_name}\s*=\s*\[)(.*?)(\])"
        match = re.search(pattern, source, re.DOTALL)
        if not match:
            logger.warning(f"Could not find '{field_name}' list in manifest source")
            return source

        list_content = match.group(2)
        closing_bracket_pos = match.end(2)

        # Format the new entry
        entry = f'        "{import_path}",'

        # Determine insertion point
        stripped = list_content.rstrip()
        if stripped:
            # List has existing entries -- add after last one
            insertion = f"\n{entry}"
        else:
            # Empty list -- add first entry
            insertion = f"\n{entry}\n    "

        # Insert before the closing bracket
        new_source = source[:closing_bracket_pos] + insertion + source[closing_bracket_pos:]
        return new_source


# ============================================================================
# Auto-Discovery Engine (Orchestrator)
# ============================================================================


class AutoDiscoveryEngine:
    """
    Scans module directories for components and syncs manifest.py files.

    Pipeline:
        1. FileScanner → finds Python files matching patterns
        2. ASTClassifier → classifies classes without importing them
        3. ManifestDiffer → compares discovered vs. declared components
        4. ManifestWriter → auto-updates manifest.py with new components

    Usage:
        engine = AutoDiscoveryEngine(Path("myapp/modules"))
        result = engine.discover("products")
        report = engine.sync_manifest("products")
    """

    def __init__(self, modules_dir: Path):
        self.modules_dir = modules_dir
        self.scanner = FileScanner(modules_dir)
        self.classifier = ASTClassifier()
        self.differ = ManifestDiffer()
        self.writer = ManifestWriter()

    def discover(
        self,
        module_name: str,
        patterns: list[str] | None = None,
    ) -> DiscoveryResult:
        """
        Discover all components in a module directory.

        Args:
            module_name: Name of the module to scan
            patterns: Optional filename patterns to limit scanning

        Returns:
            DiscoveryResult with all found components
        """
        result = DiscoveryResult(module_name=module_name)
        module_dir = self.modules_dir / module_name

        files = self.scanner.scan_module(module_name, patterns)
        result.files_scanned = len(files)

        for file_path in files:
            try:
                components = self.classifier.classify_file(file_path)
                for comp in components:
                    # Compute import path relative to modules dir
                    comp.import_path = self._compute_import_path(file_path, module_dir, module_name, comp.name)
                    result.components.append(comp)
            except Exception as e:
                error_msg = f"Error scanning {file_path}: {e}"
                result.errors.append(error_msg)
                logger.warning(error_msg)

        return result

    def discover_all(self) -> dict[str, DiscoveryResult]:
        """Discover components in all modules."""
        results = {}
        for module_name in self.scanner.discover_modules():
            results[module_name] = self.discover(module_name)
        return results

    def sync_manifest(
        self,
        module_name: str,
        dry_run: bool = False,
    ) -> SyncReport:
        """
        Sync discovered components into the module's manifest.py.

        Args:
            module_name: Name of the module
            dry_run: If True, report changes without writing

        Returns:
            SyncReport describing what was (or would be) changed
        """
        manifest_path = self.modules_dir / module_name / "manifest.py"
        report = SyncReport(
            module_name=module_name,
            manifest_path=manifest_path,
            dry_run=dry_run,
        )

        if not manifest_path.exists():
            logger.warning(f"No manifest.py found for module '{module_name}'")
            return report

        # Discover components
        discovery = self.discover(module_name)

        # Parse existing manifest references
        manifest_refs = self._parse_manifest_refs(manifest_path)

        # Calculate diff
        actions = self.differ.diff(discovery.components, manifest_refs)
        report.actions = actions

        # Apply changes
        if actions and not dry_run:
            self.writer.write_sync_actions(manifest_path, actions, dry_run=False)

        return report

    def sync_all(self, dry_run: bool = False) -> list[SyncReport]:
        """Sync manifests for all discovered modules."""
        reports = []
        for module_name in self.scanner.discover_modules():
            reports.append(self.sync_manifest(module_name, dry_run=dry_run))
        return reports

    def _compute_import_path(
        self,
        file_path: Path,
        module_dir: Path,
        module_name: str,
        class_name: str,
    ) -> str:
        """
        Compute the import path for a component.

        Example: modules/users/controllers.py:UsersController
                 → "modules.users.controllers:UsersController"
        """
        relative = file_path.relative_to(module_dir.parent)
        module_parts = relative.with_suffix("").parts
        dotted = ".".join(module_parts)
        return f"{dotted}:{class_name}"

    def _parse_manifest_refs(self, manifest_path: Path) -> dict[str, list[str]]:
        """
        Parse a manifest.py file to extract existing component references.

        Returns dict of field_name → list of import path strings.
        """
        refs: dict[str, list[str]] = {}
        try:
            source = manifest_path.read_text(encoding="utf-8")
            tree = ast.parse(source)

            # Find the AppManifest(...) call
            for node in ast.walk(tree):
                if not isinstance(node, ast.Call):
                    continue
                func = node.func
                func_name = None
                if isinstance(func, ast.Name):
                    func_name = func.id
                elif isinstance(func, ast.Attribute):
                    func_name = func.attr
                if func_name != "AppManifest":
                    continue

                # Extract keyword arguments that are lists of strings
                for kw in node.keywords:
                    if kw.arg and isinstance(kw.value, ast.List):
                        paths = []
                        for elt in kw.value.elts:
                            if isinstance(elt, ast.Constant) and isinstance(elt.value, str):
                                paths.append(elt.value)
                        if paths:
                            refs[kw.arg] = paths

        except Exception as e:
            logger.warning(f"Failed to parse manifest refs from {manifest_path}: {e}")

        return refs
