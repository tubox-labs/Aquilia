"""
Auto-Discovery Engine -- Next-Gen AST-based component classification, manifest sync, caching, and validation.

Pipeline:
    FileScanner → DiscoveryCache → ASTClassifier (Extensible) → ManifestDiffer → ManifestWriter
"""

from __future__ import annotations

import ast
import hashlib
import logging
import re
from dataclasses import dataclass, field
from pathlib import Path

from ..manifest import ComponentKind

logger = logging.getLogger("aquilia.discovery")


# ============================================================================
# Extensible Rules Registry
# ============================================================================


@dataclass
class ComponentRule:
    """Discovery rules matching base classes, decorators, or suffixes."""

    kind: ComponentKind
    base_classes: set[str] = field(default_factory=set)
    decorators: set[str] = field(default_factory=set)
    name_suffixes: set[str] = field(default_factory=set)


_RULES_REGISTRY: dict[ComponentKind, ComponentRule] = {}


def register_component_rule(
    kind: ComponentKind,
    base_classes: set[str] | None = None,
    decorators: set[str] | None = None,
    name_suffixes: set[str] | None = None,
) -> None:
    """Register or extend an auto-discovery rule for a component kind."""
    if kind not in _RULES_REGISTRY:
        _RULES_REGISTRY[kind] = ComponentRule(kind)

    rule = _RULES_REGISTRY[kind]
    if base_classes:
        rule.base_classes.update(base_classes)
    if decorators:
        rule.decorators.update(decorators)
    if name_suffixes:
        rule.name_suffixes.update(name_suffixes)


def _init_default_rules() -> None:
    # Controller
    register_component_rule(
        ComponentKind.CONTROLLER,
        base_classes={"Controller", "BaseController", "RestController"},
        name_suffixes={"Controller"},
    )
    # SocketController
    register_component_rule(
        ComponentKind.SOCKET_CONTROLLER,
        base_classes={"WebSocketController", "SocketController"},
        decorators={"Socket", "SocketController", "WebSocket", "WebSocketController"},
        name_suffixes={"SocketController"},
    )
    # Service
    register_component_rule(
        ComponentKind.SERVICE,
        base_classes={"Service", "BaseService"},
        decorators={"service", "injectable", "provides", "provider"},
        name_suffixes={"Service"},
    )
    # Middleware
    register_component_rule(
        ComponentKind.MIDDLEWARE,
        base_classes={"Middleware", "BaseMiddleware"},
        name_suffixes={"Middleware"},
    )
    # Guard
    register_component_rule(
        ComponentKind.GUARD,
        base_classes={"Guard", "BaseGuard", "AuthGuard"},
        decorators={"guard", "auth_guard"},
        name_suffixes={"Guard"},
    )
    # Pipe
    register_component_rule(
        ComponentKind.PIPE,
        base_classes={"Pipe", "BasePipe", "ValidationPipe", "TransformPipe"},
        decorators={"pipe", "transform", "validate"},
        name_suffixes={"Pipe"},
    )
    # Interceptor
    register_component_rule(
        ComponentKind.INTERCEPTOR,
        base_classes={"Interceptor", "BaseInterceptor", "LoggingInterceptor", "CacheInterceptor"},
        decorators={"interceptor", "intercept"},
        name_suffixes={"Interceptor"},
    )
    # Model
    register_component_rule(
        ComponentKind.MODEL,
        base_classes={"Model", "BaseModel", "AquiliaModel"},
        name_suffixes={"Model"},
    )
    # Background Tasks
    register_component_rule(
        ComponentKind.TASK,
        decorators={"task"},
        name_suffixes={"Task"},
    )
    # Event Handlers & Signals
    register_component_rule(
        ComponentKind.EVENT_HANDLER,
        decorators={"receiver", "event_handler"},
        name_suffixes={"Receiver", "EventHandler"},
    )
    # Integrations
    register_component_rule(
        ComponentKind.INTEGRATION,
        base_classes={"Integration"},
        name_suffixes={"Integration"},
    )
    # CLI Commands
    register_component_rule(
        ComponentKind.COMMAND,
        base_classes={"Command"},
        name_suffixes={"Command"},
    )
    # Custom Validators
    register_component_rule(
        ComponentKind.VALIDATOR,
        decorators={"validator"},
        name_suffixes={"Validator"},
    )


_init_default_rules()


# ============================================================================
# Discovery Caching
# ============================================================================


class DiscoveryCache:
    """Maintains file metadata hashes to avoid redundant AST parsing using SURP format."""

    def __init__(self, cache_file: Path):
        self.cache_file = cache_file
        self._data: dict[str, dict] = {}
        self.load()

    def load(self) -> None:
        if self.cache_file.exists():
            try:
                import surp as surp_backend

                self._data = surp_backend.decode_from_file(str(self.cache_file)) or {}
            except Exception:
                self._data = {}
        else:
            self._data = {}

    def save(self) -> None:
        try:
            self.cache_file.parent.mkdir(parents=True, exist_ok=True)
            import surp as surp_backend

            surp_backend.encode_to_file(self._data, str(self.cache_file))
        except Exception as e:
            logger.warning(f"Failed to save discovery cache: {e}")

    def get(self, file_path: str) -> dict | None:
        return self._data.get(file_path)

    def set(self, file_path: str, mtime: float, file_hash: str, components: list[dict]) -> None:
        self._data[file_path] = {
            "mtime": mtime,
            "hash": file_hash,
            "components": components,
        }


def _compute_file_hash(path: Path) -> str:
    hasher = hashlib.sha256()
    try:
        with open(path, "rb") as f:
            for chunk in iter(lambda: f.read(65536), b""):
                hasher.update(chunk)
    except Exception:
        return ""
    return hasher.hexdigest()


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

    @property
    def socket_controllers(self) -> list[ClassifiedComponent]:
        return [c for c in self.components if c.kind == ComponentKind.SOCKET_CONTROLLER]

    @property
    def tasks(self) -> list[ClassifiedComponent]:
        return [c for c in self.components if c.kind == ComponentKind.TASK]

    @property
    def event_handlers(self) -> list[ClassifiedComponent]:
        return [c for c in self.components if c.kind == ComponentKind.EVENT_HANDLER]

    @property
    def integrations(self) -> list[ClassifiedComponent]:
        return [c for c in self.components if c.kind == ComponentKind.INTEGRATION]

    @property
    def commands(self) -> list[ClassifiedComponent]:
        return [c for c in self.components if c.kind == ComponentKind.COMMAND]

    @property
    def validators(self) -> list[ClassifiedComponent]:
        return [c for c in self.components if c.kind == ComponentKind.VALIDATOR]


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
    def removed(self) -> list[SyncAction]:
        return [a for a in self.actions if a.action == "remove"]

    @property
    def has_changes(self) -> bool:
        return len(self.actions) > 0


# ============================================================================
# AST Classifier
# ============================================================================


class ASTClassifier:
    """Classifies Python classes using extensible AST analysis registry."""

    def classify_file(self, file_path: Path) -> list[ClassifiedComponent]:
        """Parse a Python file with AST and classify its classes."""
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
        """Classify a single class definition using the extensible rules registry."""
        bases = set(self._extract_base_names(node))
        decorators = set(self._extract_decorator_names(node))
        class_name = node.name

        # Priority list
        for kind in [
            ComponentKind.SOCKET_CONTROLLER,
            ComponentKind.CONTROLLER,
            ComponentKind.GUARD,
            ComponentKind.PIPE,
            ComponentKind.INTERCEPTOR,
            ComponentKind.MIDDLEWARE,
            ComponentKind.MODEL,
            ComponentKind.TASK,
            ComponentKind.EVENT_HANDLER,
            ComponentKind.INTEGRATION,
            ComponentKind.COMMAND,
            ComponentKind.VALIDATOR,
            ComponentKind.SERVICE,
        ]:
            rule = _RULES_REGISTRY.get(kind)
            if not rule:
                continue

            if bases & rule.base_classes:
                return kind
            if decorators & rule.decorators:
                return kind
            if any(class_name.endswith(suffix) for suffix in rule.name_suffixes):
                return kind

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
        """Find all Python files in a module directory."""
        module_dir = self.modules_dir / module_name
        if not module_dir.is_dir():
            logger.warning(f"Module directory not found: {module_dir}")
            return []

        files = []
        for py_file in module_dir.rglob("*.py"):
            stem = py_file.stem
            name = py_file.name

            if name in self.SKIP_FILES:
                continue
            if any(stem.startswith(p) for p in self.SKIP_PREFIXES):
                continue

            if patterns:
                # Match against every path component relative to the module dir
                # (directory names as well as the file stem), so a pattern like
                # "models" matches both models.py and models/register.py.
                rel_parts = py_file.relative_to(module_dir).with_suffix("").parts
                matches = any(part in patterns or any(part.startswith(p) for p in patterns) for part in rel_parts)
                if not matches:
                    continue

            files.append(py_file)

        return sorted(files)

    def discover_modules(self) -> list[str]:
        """Discover all module directories containing manifest.py or __init__.py."""
        modules = []
        if not self.modules_dir.is_dir():
            return modules

        for child in sorted(self.modules_dir.iterdir()):
            if not child.is_dir():
                continue
            if child.name.startswith((".", "_")):
                continue
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

    def __init__(self, root_package: str = "modules"):
        self.root_package = root_package

    def diff(
        self,
        discovered: list[ClassifiedComponent],
        manifest_refs: dict[str, list[str]],
        module_prefix: str | None = None,
    ) -> list[SyncAction]:
        """Calculate actions needed to sync manifest with discovered components."""
        actions = []

        # 1. Additions
        for component in discovered:
            field_name = self.KIND_TO_FIELD.get(component.kind)
            if field_name is None:
                continue

            existing = manifest_refs.get(field_name, [])
            if not self._is_declared(component, existing):
                actions.append(
                    SyncAction(
                        action="add",
                        component=component,
                        field_name=field_name,
                    )
                )

        # 2. Removals
        if module_prefix:
            for field_name, existing in manifest_refs.items():
                kind = None
                for k, f in self.KIND_TO_FIELD.items():
                    if f == field_name:
                        kind = k
                        break
                if kind is None:
                    continue

                discovered_kind = [c for c in discovered if c.kind == kind]
                discovered_paths = {c.import_path for c in discovered_kind}

                for ref in existing:
                    if ref.startswith(f"{module_prefix}."):
                        if ref not in discovered_paths:
                            class_name = ref.split(":", 1)[1] if ":" in ref else ref
                            is_moved = any(c.name == class_name for c in discovered_kind)
                            if not is_moved:
                                dummy_comp = ClassifiedComponent(
                                    name=class_name,
                                    kind=kind,
                                    file_path=Path(""),
                                    line=0,
                                    import_path=ref,
                                )
                                actions.append(
                                    SyncAction(
                                        action="remove",
                                        component=dummy_comp,
                                        field_name=field_name,
                                    )
                                )

        return actions

    def _is_declared(self, component: ClassifiedComponent, existing: list[str]) -> bool:
        """Check if a component is already declared in the manifest.

        Only an exact dotted-path match counts as "declared" -- a ref with
        the same class name but a different (stale) path is a rename, not a
        duplicate, and must still surface as an "add" so ManifestWriter can
        rewrite the stale entry in place (see _add_component's class-name
        match-and-replace logic).
        """
        import_path = component.import_path
        return any(ref == import_path for ref in existing)


# ============================================================================
# Manifest Writer
# ============================================================================


class ManifestWriter:
    """Updates manifest.py files using text manipulation."""

    def write_sync_actions(
        self,
        manifest_path: Path,
        actions: list[SyncAction],
        dry_run: bool = False,
    ) -> int:
        """Apply sync actions to a manifest file."""
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
            elif action.action == "remove":
                new_source = self._remove_component(source, action.field_name, action.component.import_path)
                if new_source != source:
                    source = new_source
                    changes += 1

        if changes > 0 and not dry_run:
            manifest_path.write_text(source, encoding="utf-8")

        return changes

    def _remove_component(self, source: str, field_name: str, import_path: str) -> str:
        """Remove a component reference from a field's list in the manifest source."""
        pattern = rf"({field_name}\s*=\s*\[)(.*?)(\])"
        match = re.search(pattern, source, re.DOTALL)
        if not match:
            return source

        list_content = match.group(2)
        start_pos, end_pos = match.start(2), match.end(2)

        escaped_path = re.escape(import_path)
        item_pattern = rf'["\']{escaped_path}["\']'
        item_match = re.search(item_pattern, list_content)
        if not item_match:
            return source

        item_start = item_match.start()
        item_end = item_match.end()

        after_str = list_content[item_end:]
        comma_after_match = re.match(r"\s*,\s*", after_str)
        if comma_after_match:
            item_end += comma_after_match.end()
        else:
            before_str = list_content[:item_start]
            comma_before_match = re.search(r",\s*$", before_str)
            if comma_before_match:
                item_start -= len(comma_before_match.group(0))

        new_list_content = list_content[:item_start] + list_content[item_end:]
        return source[:start_pos] + new_list_content + source[end_pos:]

    def _add_component(self, source: str, field_name: str, import_path: str) -> str:
        """Add a component reference to a field's list in the manifest source."""
        pattern = rf"({field_name}\s*=\s*\[)(.*?)(\])"
        match = re.search(pattern, source, re.DOTALL)
        if not match:
            logger.warning(f"Could not find '{field_name}' list in manifest source")
            return source

        list_content = match.group(2)
        start_pos, end_pos = match.start(2), match.end(2)
        class_name = import_path.split(":", 1)[1]

        item_pattern = rf'["\']([^"\']*?:)?{class_name}["\']'
        item_match = re.search(item_pattern, list_content)
        if item_match:
            old_item = item_match.group(0)
            quote = old_item[0]
            new_item = f"{quote}{import_path}{quote}"
            new_list_content = list_content[: item_match.start()] + new_item + list_content[item_match.end() :]
            return source[:start_pos] + new_list_content + source[end_pos:]

        closing_bracket_pos = match.end(2)
        entry = f'        "{import_path}",'

        stripped = list_content.rstrip()
        if stripped:
            insertion = f"\n{entry}"
        else:
            insertion = f"\n{entry}\n    "

        new_source = source[:closing_bracket_pos] + insertion + source[closing_bracket_pos:]
        return new_source


# ============================================================================
# Auto-Discovery Engine (Orchestrator)
# ============================================================================


class AutoDiscoveryEngine:
    """Scans module directories for components and syncs configurations."""

    def __init__(self, modules_dir: Path):
        self.modules_dir = modules_dir.resolve()
        self.scanner = FileScanner(self.modules_dir)
        self.classifier = ASTClassifier()
        self.differ = ManifestDiffer(self.modules_dir.name)
        self.writer = ManifestWriter()

    def discover(
        self,
        module_name: str,
        patterns: list[str] | None = None,
    ) -> DiscoveryResult:
        """Discover all components in a module directory."""
        result = DiscoveryResult(module_name=module_name)
        module_dir = self.modules_dir / module_name

        files = self.scanner.scan_module(module_name, patterns)
        result.files_scanned = len(files)

        # Initialize discovery cache
        cache_file = self.modules_dir.parent / ".aquilia" / "discovery_cache.surp"
        cache = DiscoveryCache(cache_file)

        for file_path in files:
            try:
                mtime = file_path.stat().st_mtime
                file_hash = _compute_file_hash(file_path)
                cached_entry = cache.get(str(file_path))

                if cached_entry and cached_entry.get("mtime") == mtime and cached_entry.get("hash") == file_hash:
                    # Load components from cache
                    for c_data in cached_entry.get("components", []):
                        comp = ClassifiedComponent(
                            name=c_data["name"],
                            kind=ComponentKind(c_data["kind"]),
                            file_path=Path(c_data["file_path"]),
                            line=c_data["line"],
                            import_path=c_data.get("import_path", ""),
                            bases=c_data.get("bases", []),
                            decorators=c_data.get("decorators", []),
                        )
                        result.components.append(comp)
                    continue

                # Parse and classify
                components = self.classifier.classify_file(file_path)
                c_list = []
                for comp in components:
                    comp.import_path = self._compute_import_path(file_path, module_dir, module_name, comp.name)
                    result.components.append(comp)
                    c_list.append(
                        {
                            "name": comp.name,
                            "kind": comp.kind.value,
                            "file_path": str(comp.file_path),
                            "line": comp.line,
                            "import_path": comp.import_path,
                            "bases": comp.bases,
                            "decorators": comp.decorators,
                        }
                    )

                cache.set(str(file_path), mtime, file_hash, c_list)
            except Exception as e:
                error_msg = f"Error scanning {file_path}: {e}"
                result.errors.append(error_msg)
                logger.warning(error_msg)

        cache.save()
        return result

    def discover_all(self) -> dict[str, DiscoveryResult]:
        """Discover components in all modules."""
        results = {}
        for module_name in self.scanner.discover_modules():
            patterns = self._module_discover_patterns(module_name)
            results[module_name] = self.discover(module_name, patterns=patterns)
        return results

    def _module_discover_patterns(self, module_name: str) -> list[str] | None:
        """Read a module's manifest.py `discover_patterns` list, if declared."""
        manifest_path = self.modules_dir / module_name / "manifest.py"
        if not manifest_path.exists():
            return None
        return self._parse_manifest_refs(manifest_path).get("discover_patterns")

    def sync_manifest(
        self,
        module_name: str,
        dry_run: bool = False,
    ) -> SyncReport:
        """Sync discovered components into the module's manifest.py."""
        manifest_path = self.modules_dir / module_name / "manifest.py"
        report = SyncReport(
            module_name=module_name,
            manifest_path=manifest_path,
            dry_run=dry_run,
        )

        if not manifest_path.exists():
            logger.warning(f"No manifest.py found for module '{module_name}'")
            return report

        manifest_refs = self._parse_manifest_refs(manifest_path)
        discovery = self.discover(module_name, patterns=manifest_refs.get("discover_patterns"))

        module_prefix = f"{self.differ.root_package}.{module_name}"
        actions = self.differ.diff(discovery.components, manifest_refs, module_prefix)
        report.actions = actions

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
        """Compute import path for a component."""
        relative = file_path.resolve().relative_to(self.modules_dir.parent)
        module_parts = relative.with_suffix("").parts
        dotted = ".".join(module_parts)
        return f"{dotted}:{class_name}"

    def _parse_manifest_refs(self, manifest_path: Path) -> dict[str, list[str]]:
        """Parse manifest.py file to extract existing component references."""
        refs: dict[str, list[str]] = {}
        try:
            source = manifest_path.read_text(encoding="utf-8")
            tree = ast.parse(source)

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

                for kw in node.keywords:
                    if kw.arg and isinstance(kw.value, ast.List):
                        paths = []
                        for elt in kw.value.elts:
                            if isinstance(elt, ast.Constant) and isinstance(elt.value, str):
                                paths.append(elt.value)
                            elif isinstance(elt, ast.Call):
                                if (
                                    elt.args
                                    and isinstance(elt.args[0], ast.Constant)
                                    and isinstance(elt.args[0].value, str)
                                ):
                                    paths.append(elt.args[0].value)
                                else:
                                    for kwarg in elt.keywords:
                                        if (
                                            kwarg.arg in ("class_path", "class_ref")
                                            and isinstance(kwarg.value, ast.Constant)
                                            and isinstance(kwarg.value.value, str)
                                        ):
                                            paths.append(kwarg.value.value)
                        if paths:
                            refs[kw.arg] = paths
        except Exception as e:
            logger.warning(f"Failed to parse manifest refs from {manifest_path}: {e}")

        return refs

    def validate_workspace(self, workspace_path: Path) -> dict[str, list[str]]:
        """Validate workspace structure, route prefixes, and component integrity."""
        errors = []
        warnings = []

        if not workspace_path.exists():
            errors.append(f"workspace.py not found at {workspace_path}")
            return {"errors": errors, "warnings": warnings}

        discovered_modules = self.scanner.discover_modules()
        manifest_data = {}

        for mod in discovered_modules:
            manifest_path = self.modules_dir / mod / "manifest.py"
            if manifest_path.exists():
                manifest_refs = self._parse_manifest_refs(manifest_path)
                imports = manifest_refs.get("imports", [])
                depends_on = manifest_refs.get("depends_on", [])
                deps = list(set(imports + depends_on))

                content = manifest_path.read_text(encoding="utf-8")
                route_prefix = f"/{mod}"
                route_match = re.search(r'route_prefix\s*=\s*["\']([^"\']+)["\']', content)
                if route_match:
                    route_prefix = route_match.group(1)

                manifest_data[mod] = {
                    "dependencies": deps,
                    "route_prefix": route_prefix,
                    "components": self.discover(mod).components,
                }

        # DFS Cycle Detection
        visited = {}
        cycle_path = []

        def dfs(node: str) -> bool:
            visited[node] = 1
            cycle_path.append(node)
            for dep in manifest_data.get(node, {}).get("dependencies", []):
                if dep not in manifest_data:
                    continue
                if visited.get(dep, 0) == 1:
                    cycle = cycle_path[cycle_path.index(dep) :] + [dep]
                    errors.append(f"Circular dependency cycle detected: {' -> '.join(cycle)}")
                    return True
                elif visited.get(dep, 0) == 0:
                    if dfs(dep):
                        return True
            cycle_path.pop()
            visited[node] = 2
            return False

        for mod in manifest_data:
            if visited.get(mod, 0) == 0:
                dfs(mod)

        # Duplicate route prefix detection
        routes = {}
        for mod, data in manifest_data.items():
            prefix = data["route_prefix"]
            if prefix in routes:
                errors.append(f"Duplicate route prefix '{prefix}' registered in modules '{mod}' and '{routes[prefix]}'")
            else:
                routes[prefix] = mod

        # Missing dependency detection
        for mod, data in manifest_data.items():
            for dep in data["dependencies"]:
                if dep not in manifest_data:
                    errors.append(f"Module '{mod}' depends on unregistered module '{dep}'")

        # Duplicate component name warnings
        classes = {}
        for mod, data in manifest_data.items():
            for comp in data["components"]:
                key = (comp.kind, comp.name)
                if key in classes:
                    warnings.append(
                        f"Duplicate component class name '{comp.name}' of kind '{comp.kind.value}' "
                        f"found in module '{mod}' ({comp.file_path.name}:{comp.line}) "
                        f"and module '{classes[key]}'"
                    )
                else:
                    classes[key] = f"{mod} ({comp.file_path.name}:{comp.line})"

        return {"errors": errors, "warnings": warnings}
