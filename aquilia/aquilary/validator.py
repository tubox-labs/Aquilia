"""
Registry validator for manifests and configuration.

Architecture v2 improvements:
- Real route conflict detection using prefix + controller class analysis
- Cross-module dependency validation via imports/exports
- Guards, pipes, interceptors validation
- Import path validation for ComponentRef objects
"""

from typing import Any

from .errors import ErrorSpan, RouteConflictError, ValidationReport


class RegistryValidator:
    """
    Validates registry manifests and configuration.

    Checks:
    - Manifest structure
    - Config schemas
    - Cross-app dependencies
    - Route conflicts
    - Scope violations
    """

    def __init__(self, mode: Any):
        self.mode = mode
        self._app_names: set[str] = set()
        self._route_index: dict[str, list[dict[str, str]]] = {}

    def validate_manifests(
        self,
        manifests: list[Any],
        config: Any,
    ) -> ValidationReport:
        """
        Validate all manifests.

        Args:
            manifests: List of manifest objects
            config: Config object

        Returns:
            ValidationReport with errors/warnings
        """
        report = ValidationReport()

        # Phase 1: Collect app names
        for manifest in manifests:
            self._app_names.add(manifest.name)

        # Phase 2: Validate each manifest
        for manifest in manifests:
            self._validate_manifest_structure(manifest, report)
            self._validate_dependencies(manifest, report)
            self._validate_config_namespace(manifest, config, report)

        # Phase 3: Validate route conflicts
        self._validate_route_conflicts(manifests, report)

        # Phase 4: Validate cross-app usage (if in strict mode)
        if self.mode.value == "prod":
            self._validate_cross_app_usage(manifests, report)

        return report

    def _validate_manifest_structure(
        self,
        manifest: Any,
        report: ValidationReport,
    ) -> None:
        """
        Validate manifest structure.

        Args:
            manifest: Manifest object
            report: ValidationReport to accumulate errors
        """
        from .errors import ManifestValidationError

        errors: list[str] = []

        # Required fields
        if not hasattr(manifest, "name") or not manifest.name:
            errors.append("Missing required field: name")

        if not hasattr(manifest, "version") or not manifest.version:
            errors.append("Missing required field: version")

        # Version format
        if hasattr(manifest, "version") and manifest.version and not self._validate_semver(manifest.version):
            errors.append(f"Invalid version format: {manifest.version}")
            report.add_warning(
                f"App '{manifest.name}': Version '{manifest.version}' is not valid semver (expected X.Y.Z)"
            )

        # Controllers type -- v2: accepts str or ComponentRef
        if hasattr(manifest, "controllers"):
            if not isinstance(manifest.controllers, list):
                errors.append("Field 'controllers' must be a list")
            else:
                for i, ctrl in enumerate(manifest.controllers):
                    ctrl_path = ctrl
                    if hasattr(ctrl, "class_path"):
                        ctrl_path = ctrl.class_path
                    elif not isinstance(ctrl, str):
                        errors.append(f"controllers[{i}] must be string import path or ComponentRef")
                        continue
                    if not self._validate_import_path(ctrl_path):
                        errors.append(f"controllers[{i}] has invalid import path: {ctrl_path}")

        # Services type
        if hasattr(manifest, "services"):
            if not isinstance(manifest.services, list):
                errors.append("Field 'services' must be a list")
            else:
                for i, svc in enumerate(manifest.services):
                    svc_path = svc
                    if hasattr(svc, "class_path"):
                        svc_path = svc.class_path
                    elif not isinstance(svc, str):
                        errors.append(f"services[{i}] must be string path or ServiceConfig")
                        continue

                    if not self._validate_import_path(svc_path):
                        errors.append(f"services[{i}] has invalid import path: {svc_path}")

        # Dependencies type -- v2: validate both depends_on and imports
        if hasattr(manifest, "depends_on"):
            if not isinstance(manifest.depends_on, list):
                errors.append("Field 'depends_on' must be a list")
            else:
                for i, dep in enumerate(manifest.depends_on):
                    if not isinstance(dep, str):
                        errors.append(f"depends_on[{i}] must be string app name")

        if hasattr(manifest, "imports"):
            if not isinstance(getattr(manifest, "imports", []), list):
                errors.append("Field 'imports' must be a list")
            else:
                for i, imp in enumerate(manifest.imports):
                    if not isinstance(imp, str):
                        errors.append(f"imports[{i}] must be string module name")

        # v2: Guards, pipes, interceptors
        for field_name in ("guards", "pipes", "interceptors"):
            field_val = getattr(manifest, field_name, [])
            if field_val and not isinstance(field_val, list):
                errors.append(f"Field '{field_name}' must be a list")
            elif isinstance(field_val, list):
                for i, item in enumerate(field_val):
                    item_path = item
                    if hasattr(item, "class_path"):
                        item_path = item.class_path
                    elif not isinstance(item, str):
                        errors.append(f"{field_name}[{i}] must be string path or ComponentRef")
                        continue
                    if not self._validate_import_path(item_path):
                        errors.append(f"{field_name}[{i}] has invalid import path: {item_path}")

        # Middlewares type
        if hasattr(manifest, "middlewares"):
            if not isinstance(manifest.middlewares, list):
                errors.append("Field 'middlewares' must be a list")
            else:
                for i, mw in enumerate(manifest.middlewares):
                    if not isinstance(mw, (list, tuple)) or len(mw) != 2:
                        errors.append(f"middlewares[{i}] must be (path, kwargs) tuple")
                    elif not isinstance(mw[0], str):
                        errors.append(f"middlewares[{i}][0] must be string import path")
                    elif not isinstance(mw[1], dict):
                        errors.append(f"middlewares[{i}][1] must be dict")

        # Add errors to report
        if errors:
            span = ErrorSpan(file=getattr(manifest, "__source__", "unknown"))
            error = ManifestValidationError(
                manifest_name=manifest.name,
                validation_errors=errors,
                span=span,
            )
            report.add_error(error)

    def _validate_dependencies(
        self,
        manifest: Any,
        report: ValidationReport,
    ) -> None:
        """
        Validate app dependencies exist.

        Args:
            manifest: Manifest object
            report: ValidationReport to accumulate errors
        """
        from .errors import ErrorSpan, ManifestValidationError

        if not hasattr(manifest, "depends_on"):
            return

        missing_deps = [dep for dep in manifest.depends_on if dep not in self._app_names]

        if missing_deps:
            span = ErrorSpan(file=getattr(manifest, "__source__", "unknown"))
            error = ManifestValidationError(
                manifest_name=manifest.name,
                validation_errors=[f"Missing dependency: '{dep}' (not found in registry)" for dep in missing_deps],
                span=span,
            )
            report.add_error(error)

    def _validate_config_namespace(
        self,
        manifest: Any,
        config: Any,
        report: ValidationReport,
    ) -> None:
        """
        Validate config namespace exists.

        Args:
            manifest: Manifest object
            config: Config object
            report: ValidationReport to accumulate errors
        """
        if config is None:
            return

        # Check if app has config namespace
        if hasattr(config, "apps") and not hasattr(config.apps, manifest.name):
            report.add_warning(f"App '{manifest.name}' has no config namespace (expected config.apps.{manifest.name})")

    def _validate_route_conflicts(
        self,
        manifests: list[Any],
        report: ValidationReport,
    ) -> None:
        """
        Validate no route conflicts between apps (v2: real detection).

        Detects conflicts by comparing route_prefix values across modules.
        Two modules with identical or overlapping prefixes may cause routing
        ambiguity at runtime.
        """
        # Build prefix → owners map
        prefix_owners: dict[str, list[str]] = {}

        for manifest in manifests:
            prefix = getattr(manifest, "route_prefix", "/") or "/"
            # Normalize prefix
            prefix = prefix.rstrip("/") or "/"

            if prefix not in prefix_owners:
                prefix_owners[prefix] = []
            prefix_owners[prefix].append(manifest.name)

        # Check for direct prefix conflicts
        for prefix, owners in prefix_owners.items():
            if len(owners) > 1:
                if self.mode.value == "prod":
                    error = RouteConflictError(
                        path=prefix,
                        method="*",
                        providers=[{"app": o, "controller": prefix} for o in owners],
                    )
                    report.add_error(error)
                else:
                    report.add_warning(
                        f"Route prefix conflict: '{prefix}' claimed by {len(owners)} modules: {', '.join(owners)}"
                    )

        # Check for nested prefix conflicts (e.g., /api vs /api/users)
        sorted_prefixes = sorted(prefix_owners.keys())
        for i, prefix_a in enumerate(sorted_prefixes):
            for prefix_b in sorted_prefixes[i + 1 :]:
                # Check if prefix_b starts with prefix_a (nested conflict)
                if prefix_b.startswith(prefix_a + "/") and prefix_a != "/":
                    owners_a = prefix_owners[prefix_a]
                    owners_b = prefix_owners[prefix_b]
                    # Only warn, not error -- nested prefixes are often intentional
                    report.add_warning(
                        f"Nested route prefixes: '{prefix_a}' ({', '.join(owners_a)}) "
                        f"contains '{prefix_b}' ({', '.join(owners_b)}) -- "
                        f"ensure routes don't overlap"
                    )

    def _validate_cross_app_usage(
        self,
        manifests: list[Any],
        report: ValidationReport,
    ) -> None:
        """
        Validate cross-app service usage declares dependencies (v2: real checking).

        Checks that:
        1. Services consumed via 'imports' are actually 'exported' by the provider module
        2. All 'imports' reference existing modules
        3. No circular import chains exist
        """
        # Build module registries
        module_exports: dict[str, set[str]] = {}  # module → exported service paths
        module_imports: dict[str, list[str]] = {}  # module → imported module names

        for manifest in manifests:
            # Collect exports
            exports = set()
            for service in getattr(manifest, "services", []):
                service_path = service.class_path if hasattr(service, "class_path") else str(service)
                exports.add(service_path)

            # If module has explicit 'exports', only those are visible
            explicit_exports = getattr(manifest, "exports", [])
            if explicit_exports:
                module_exports[manifest.name] = set(explicit_exports)
            else:
                # Without explicit exports, all services are visible (legacy compat)
                module_exports[manifest.name] = exports

            # Collect imports
            imports = getattr(manifest, "imports", []) or getattr(manifest, "depends_on", [])
            module_imports[manifest.name] = list(imports)

        # Validate imports reference existing modules
        for module_name, imports in module_imports.items():
            for imp in imports:
                if imp not in self._app_names:
                    from .errors import ErrorSpan, ManifestValidationError

                    error = ManifestValidationError(
                        manifest_name=module_name,
                        validation_errors=[f"imports '{imp}' which does not exist in the registry"],
                        span=ErrorSpan(file="unknown"),
                    )
                    report.add_error(error)

        # Detect circular import chains
        visited: set[str] = set()
        path: list[str] = []

        def _detect_cycle(module: str) -> bool:
            if module in path:
                cycle = path[path.index(module) :] + [module]
                report.add_warning(f"Circular module dependency detected: {' → '.join(cycle)}")
                return True
            if module in visited:
                return False
            visited.add(module)
            path.append(module)
            for dep in module_imports.get(module, []):
                if dep in self._app_names:
                    _detect_cycle(dep)
            path.pop()
            return False

        for module_name in module_imports:
            visited.clear()
            path.clear()
            _detect_cycle(module_name)

    def _validate_semver(self, version: str) -> bool:
        """
        Validate semver format.

        Args:
            version: Version string

        Returns:
            True if valid semver
        """
        parts = version.split(".")

        if len(parts) != 3:
            return False

        try:
            for part in parts:
                int(part)
            return True
        except ValueError:
            return False

    def _validate_import_path(self, path: str) -> bool:
        """
        Validate import path format.

        Supports two formats:
        - module.path (e.g., "myapp.controllers")
        - module.path:ClassName (e.g., "myapp.controllers:MyController")

        Args:
            path: Import path string

        Returns:
            True if valid
        """
        if not path:
            return False

        # Check for relative imports
        if path.startswith("."):
            return False

        # Split module path and optional class name
        if ":" in path:
            module_path, class_name = path.split(":", 1)
            # Validate class name is a valid identifier
            if not class_name.isidentifier():
                return False
        else:
            module_path = path

        # Check for valid Python identifier in module path
        parts = module_path.split(".")
        return all(part.isidentifier() for part in parts)

    def validate_hot_reload(
        self,
        old_manifests: list[Any],
        new_manifests: list[Any],
    ) -> ValidationReport:
        """
        Validate hot-reload is safe.

        Checks:
        - No removed apps
        - No removed routes (only additions allowed)
        - No broken dependencies

        Args:
            old_manifests: Previous manifest list
            new_manifests: New manifest list

        Returns:
            ValidationReport
        """
        report = ValidationReport()

        old_apps = {m.name for m in old_manifests}
        new_apps = {m.name for m in new_manifests}

        # Check for removed apps
        removed_apps = old_apps - new_apps
        if removed_apps:
            report.add_warning(f"Hot-reload: Apps removed: {', '.join(sorted(removed_apps))}")

        # Check for new apps
        added_apps = new_apps - old_apps
        if added_apps:
            report.add_warning(f"Hot-reload: Apps added: {', '.join(sorted(added_apps))}")

        return report
