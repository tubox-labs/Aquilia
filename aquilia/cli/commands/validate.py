"""Manifest validation command.

Uses the Aquilia Manifest-First Architecture pipeline:
  1. Load manifests via ManifestLoader
  2. Validate via RegistryValidator
  3. Build dependency graph via DependencyGraph
  4. Generate fingerprint via FingerprintGenerator

This replaces legacy regex-only validation with the real
Aquilary compilation pipeline for accurate, production-grade checks.
"""

from pathlib import Path
from typing import Optional, List
from dataclasses import dataclass, field
import importlib.util
import sys
import re


@dataclass
class ValidationResult:
    """Result of manifest validation."""

    is_valid: bool
    module_count: int
    route_count: int
    provider_count: int
    faults: list[str]
    warnings: list[str] = field(default_factory=list)
    fingerprint: Optional[str] = None


def _load_manifest_object(module_name: str, manifest_path: Path):
    """Safely load an AppManifest instance from a manifest.py file."""
    spec = importlib.util.spec_from_file_location(
        f"_validate_{module_name}_manifest", manifest_path,
    )
    if not spec or not spec.loader:
        raise ImportError(f"Could not create spec for {manifest_path}")

    mod = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = mod
    spec.loader.exec_module(mod)

    from aquilia.manifest import AppManifest

    manifest_obj = getattr(mod, "manifest", None)
    if manifest_obj is None:
        for _attr_name, obj in vars(mod).items():
            if isinstance(obj, AppManifest):
                manifest_obj = obj
                break
            if (
                isinstance(obj, type)
                and issubclass(obj, AppManifest)
                and obj is not AppManifest
            ):
                manifest_obj = obj()
                break

    return manifest_obj


def validate_workspace(
    strict: bool = False,
    module_filter: Optional[str] = None,
    verbose: bool = False,
) -> ValidationResult:
    """
    Validate workspace manifests using the Aquilary pipeline.

    Phase 1 -- Structure: workspace file, directories, module presence
    Phase 2 -- Manifest: load each AppManifest, validate fields
    Phase 3 -- Pipeline: RegistryValidator → DependencyGraph
    Phase 4 -- Strict: controller/service import resolution, fingerprint

    Args:
        strict: Enable strict (production-level) validation
        module_filter: Validate only specific module
        verbose: Enable verbose output

    Returns:
        ValidationResult with validation status, statistics, and optional fingerprint
    """
    workspace_root = Path.cwd()
    workspace_config = workspace_root / "workspace.py"

    if not workspace_config.exists():
        from aquilia.faults.domains import ConfigMissingFault
        raise ConfigMissingFault(key="workspace.py")

    faults: List[str] = []
    warnings: List[str] = []
    module_count = 0
    route_count = 0
    provider_count = 0
    fingerprint = None

    # Ensure workspace root is importable
    ws_abs = str(workspace_root.resolve())
    if ws_abs not in sys.path:
        sys.path.insert(0, ws_abs)

    # ── Phase 1: Parse workspace.py for registered modules ──
    try:
        workspace_content = workspace_config.read_text()
        # Strip comment lines to avoid matching commented-out modules
        clean_content = "\n".join(
            line for line in workspace_content.splitlines()
            if not line.strip().startswith("#")
        )
        modules = re.findall(r'Module\("([^"]+)"', clean_content)
        # Deduplicate preserving order
        seen: set = set()
        unique_modules: list = []
        for m in modules:
            if m not in seen:
                seen.add(m)
                unique_modules.append(m)
        modules = unique_modules
    except Exception as e:
        faults.append(f"Invalid workspace configuration: {e}")
        return ValidationResult(
            is_valid=False, module_count=0, route_count=0,
            provider_count=0, faults=faults, warnings=warnings,
        )

    if not modules:
        warnings.append("No modules registered in workspace.py")

    # ── Phase 2: Per-module validation ──
    modules_to_validate = [module_filter] if module_filter else modules
    loaded_manifests = []

    for module_name in modules_to_validate:
        if module_name == "starter":
            continue  # Starter is auto-loaded, not a real module

        module_path = workspace_root / "modules" / module_name
        manifest_path = module_path / "manifest.py"

        # Directory existence
        if not module_path.exists():
            faults.append(f"Module '{module_name}' directory not found: modules/{module_name}/")
            continue

        # Manifest existence
        if not manifest_path.exists():
            faults.append(f"Module '{module_name}' missing manifest.py")
            continue

        # __init__.py existence
        if not (module_path / "__init__.py").exists():
            warnings.append(f"Module '{module_name}' missing __init__.py (may cause import issues)")

        # Load and validate manifest
        try:
            manifest_obj = _load_manifest_object(module_name, manifest_path)
            if manifest_obj is None:
                faults.append(
                    f"Module '{module_name}' manifest.py has no AppManifest instance"
                )
                continue

            loaded_manifests.append(manifest_obj)
            module_count += 1

            # Count routes (controllers) and providers (services)
            controllers = getattr(manifest_obj, "controllers", []) or []
            services = getattr(manifest_obj, "services", []) or []
            route_count += len(controllers)
            provider_count += len(services)

            # Basic field validation
            name = getattr(manifest_obj, "name", "")
            version = getattr(manifest_obj, "version", "")
            if not name:
                faults.append(f"Module '{module_name}' manifest missing 'name'")
            if not version:
                faults.append(f"Module '{module_name}' manifest missing 'version'")

            # Dependency existence check
            depends_on = getattr(manifest_obj, "depends_on", []) or []
            for dep in depends_on:
                if dep not in modules:
                    faults.append(
                        f"Module '{module_name}' depends on '{dep}' which is not registered"
                    )

            # Controller/service import path validation
            for ctrl_ref in controllers:
                if isinstance(ctrl_ref, str) and ":" in ctrl_ref:
                    mod_path, cls_name = ctrl_ref.rsplit(":", 1)
                    parts = mod_path.split(".")
                    if parts[0] == "modules" and len(parts) > 1:
                        file_parts = parts[1:]
                        file_path = workspace_root / "modules"
                        for p in file_parts:
                            file_path = file_path / p
                        file_path = file_path.with_suffix(".py")
                        if not file_path.exists():
                            pkg_init = file_path.with_suffix("") / "__init__.py"
                            if not pkg_init.exists():
                                faults.append(
                                    f"Module '{module_name}' controller not found: "
                                    f"{ctrl_ref} (expected {file_path.relative_to(workspace_root)})"
                                )

            for svc_ref in services:
                svc_str = svc_ref if isinstance(svc_ref, str) else getattr(svc_ref, "class_path", "")
                if isinstance(svc_str, str) and ":" in svc_str:
                    mod_path, cls_name = svc_str.rsplit(":", 1)
                    parts = mod_path.split(".")
                    if parts[0] == "modules" and len(parts) > 1:
                        file_parts = parts[1:]
                        file_path = workspace_root / "modules"
                        for p in file_parts:
                            file_path = file_path / p
                        file_path = file_path.with_suffix(".py")
                        if not file_path.exists():
                            pkg_init = file_path.with_suffix("") / "__init__.py"
                            if not pkg_init.exists():
                                faults.append(
                                    f"Module '{module_name}' service not found: "
                                    f"{svc_str} (expected {file_path.relative_to(workspace_root)})"
                                )

            # Strict mode -- additional checks
            if strict:
                # Required files for a complete module
                required_files = ["controllers.py", "services.py", "faults.py"]
                for fname in required_files:
                    if not (module_path / fname).exists():
                        warnings.append(
                            f"Module '{module_name}' missing recommended file '{fname}'"
                        )

                # Route prefix check
                route_prefix = getattr(manifest_obj, "route_prefix", None)
                if not route_prefix:
                    warnings.append(
                        f"Module '{module_name}' has no route_prefix set"
                    )

                # Fault domain check
                fault_config = getattr(manifest_obj, "faults", None)
                if fault_config is None:
                    warnings.append(
                        f"Module '{module_name}' has no fault handling configured"
                    )

        except Exception as e:
            faults.append(f"Invalid manifest in module '{module_name}': {e}")

    # ── Phase 3: Aquilary pipeline validation ──
    if loaded_manifests and not faults:
        try:
            from aquilia.aquilary.core import RegistryMode
            from aquilia.aquilary.validator import RegistryValidator
            from aquilia.aquilary.graph import DependencyGraph

            mode = RegistryMode.PROD if strict else RegistryMode.DEV
            validator = RegistryValidator(mode=mode)

            # Load config from workspace if available for namespace checks
            _config = None
            try:
                from aquilia.config import ConfigLoader
                _config = ConfigLoader.load(paths=["workspace.py"])
                _config._build_apps_namespace()
            except Exception:
                pass

            pipeline_report = validator.validate_manifests(loaded_manifests, _config)

            for err in pipeline_report.errors:
                err_str = str(err)
                if err_str not in faults:
                    faults.append(f"[Aquilary] {err_str}")

            for w in pipeline_report.warnings:
                if w not in warnings:
                    warnings.append(f"[Aquilary] {w}")

            # Dependency graph cycle detection
            graph = DependencyGraph()
            for m in loaded_manifests:
                graph.add_node(
                    m.name,
                    getattr(m, "depends_on", []) or [],
                )

            cycle = graph.find_cycle()
            if cycle:
                cycle_str = " → ".join(cycle)
                faults.append(f"Dependency cycle detected: {cycle_str}")

            if verbose:
                order = graph.topological_sort()
                print(f"  Load order: {' → '.join(order)}")

        except ImportError:
            warnings.append(
                "Aquilary pipeline not available -- skipping deep validation"
            )
        except Exception as e:
            warnings.append(f"Aquilary pipeline validation error: {e}")

    # ── Phase 4: Fingerprint (strict only) ──
    if strict and loaded_manifests and not faults:
        try:
            from aquilia.aquilary.fingerprint import FingerprintGenerator

            fp = FingerprintGenerator.generate(loaded_manifests)
            fingerprint = fp
            if verbose:
                print(f"  Registry fingerprint: {fp}")
        except Exception:
            pass

    return ValidationResult(
        is_valid=len(faults) == 0,
        module_count=module_count,
        route_count=route_count,
        provider_count=provider_count,
        faults=faults,
        warnings=warnings,
        fingerprint=fingerprint,
    )
