"""
Aquilia Build Pipeline — Vite-inspired compile-before-serve orchestrator.

Sequences the complete build lifecycle:

    Discovery → Validation → Static Check → Compile → Bundle → Fingerprint

Like Vite/Next.js, the build pipeline runs **before** the server starts.
If any phase fails, the build is aborted and a clear error report is
displayed — the server never boots with broken code.

Usage::

    from aquilia.build import AquiliaBuildPipeline, BuildConfig

    result = AquiliaBuildPipeline.build(workspace_root=".", mode="dev")

    if result.success:
        # Boot server from compiled artifacts
        registry = result.create_registry()
        server = AquiliaServer(aquilary_registry=registry)
    else:
        # Display errors and abort
        for error in result.errors:
            print(error)
"""

from __future__ import annotations

import importlib.util
import json
import logging
import re
import sys
import time
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from .checker import StaticChecker, CheckResult, CheckError, CheckSeverity
from .bundler import CrousBundler, BundleManifest
from .resolver import BuildResolver, ResolvedBuild

logger = logging.getLogger("aquilia.build.pipeline")


# ═══════════════════════════════════════════════════════════════════════════
# Configuration
# ═══════════════════════════════════════════════════════════════════════════


class BuildPhase(str, Enum):
    """Build pipeline phases."""
    DISCOVERY = "discovery"
    VALIDATION = "validation"
    STATIC_CHECK = "static_check"
    COMPILATION = "compilation"
    BUNDLING = "bundling"
    FINGERPRINT = "fingerprint"
    DONE = "done"


@dataclass
class BuildConfig:
    """Configuration for a build run."""
    mode: str = "dev"                       # "dev" or "prod"
    workspace_root: str = "."               # Workspace root path
    output_dir: str = "build"               # Output directory
    compression: str = "none"               # "none", "lz4", "zstd"
    verbose: bool = False                   # Verbose output
    check_only: bool = False                # Only run checks, don't emit artifacts
    skip_checks: bool = False               # Skip static checks (for speed in dev)
    strict: bool = False                    # Treat warnings as errors

    @classmethod
    def dev(cls, workspace_root: str = ".", verbose: bool = False) -> "BuildConfig":
        """Dev build config — fast, no compression."""
        return cls(
            mode="dev",
            workspace_root=workspace_root,
            output_dir="build",
            compression="none",
            verbose=verbose,
        )

    @classmethod
    def prod(cls, workspace_root: str = ".", verbose: bool = False) -> "BuildConfig":
        """Prod build config — compressed, strict."""
        return cls(
            mode="prod",
            workspace_root=workspace_root,
            output_dir="build",
            compression="lz4",
            verbose=verbose,
            strict=True,
        )


# ═══════════════════════════════════════════════════════════════════════════
# Build Errors
# ═══════════════════════════════════════════════════════════════════════════


@dataclass
class BuildError:
    """An error that occurred during a build phase."""
    phase: BuildPhase
    message: str
    file: str = ""
    line: int = 0
    hint: str = ""
    fatal: bool = True

    def __str__(self) -> str:
        location = ""
        if self.file:
            location = f"{self.file}"
            if self.line:
                location += f":{self.line}"
            location += " — "
        prefix = "✗" if self.fatal else "⚠"
        hint = f"\n    hint: {self.hint}" if self.hint else ""
        return f"  {prefix} [{self.phase.value}] {location}{self.message}{hint}"


# ═══════════════════════════════════════════════════════════════════════════
# Build Result
# ═══════════════════════════════════════════════════════════════════════════


@dataclass
class BuildResult:
    """
    Result of a complete build pipeline run.

    Contains:
    - success: Whether the build succeeded
    - errors: List of build errors
    - bundle: The bundle manifest (if build succeeded)
    - phases: Timing info for each phase
    - fingerprint: Content-addressed fingerprint of the build
    """
    success: bool = False
    errors: List[BuildError] = field(default_factory=list)
    warnings: List[BuildError] = field(default_factory=list)
    bundle: Optional[BundleManifest] = None
    phases: Dict[str, float] = field(default_factory=dict)  # phase → ms
    fingerprint: str = ""
    total_ms: float = 0.0
    files_checked: int = 0
    artifacts_count: int = 0
    config: Optional[BuildConfig] = None
    log_lines: List[str] = field(default_factory=list)  # Build log entries

    # Internal: these are populated by the pipeline for the server
    _workspace_name: str = ""
    _workspace_version: str = ""
    _modules: List[str] = field(default_factory=list)
    _module_manifests: Dict[str, Any] = field(default_factory=dict)
    _workspace_root: Optional[Path] = None

    def summary(self) -> str:
        """Human-readable build summary."""
        if self.success:
            parts = [
                f"Build succeeded in {self.total_ms:.0f}ms",
                f"{self.artifacts_count} artifacts",
                f"{self.files_checked} files checked",
            ]
            if self.fingerprint:
                parts.append(f"fingerprint:{self.fingerprint[:12]}…")
            if self.warnings:
                parts.append(f"{len(self.warnings)} warning(s)")
            return " · ".join(parts)
        else:
            return f"Build FAILED with {len(self.errors)} error(s) in {self.total_ms:.0f}ms"

    def create_registry(self) -> Any:
        """
        Create an AquilaryRegistry from the compiled build.

        This allows the server to skip manifest parsing and boot
        directly from compiled state.

        Returns:
            AquilaryRegistry instance
        """
        if not self.success:
            raise RuntimeError("Cannot create registry from failed build")

        from aquilia.aquilary.core import (
            AquilaryRegistry,
            AppContext,
            RegistryMode,
            RegistryFingerprint,
        )
        from aquilia.config import ConfigLoader

        mode = RegistryMode(self.config.mode) if self.config else RegistryMode.DEV

        # Build AppContexts from compiled module data
        app_contexts = []
        for i, module_name in enumerate(self._modules):
            manifest_obj = self._module_manifests.get(module_name)
            if manifest_obj is None:
                continue

            ctx = AppContext(
                name=getattr(manifest_obj, "name", module_name),
                version=getattr(manifest_obj, "version", "0.1.0"),
                manifest=manifest_obj,
                config_namespace={},
                controllers=getattr(manifest_obj, "controllers", []) or [],
                services=[
                    s if isinstance(s, str) else getattr(s, "class_path", str(s))
                    for s in (getattr(manifest_obj, "services", []) or [])
                ],
                depends_on=getattr(manifest_obj, "depends_on", []) or [],
                load_order=i,
            )

            # Middleware normalization
            raw_mw = getattr(manifest_obj, "middleware", []) or []
            mw_list = []
            for mw in raw_mw:
                if isinstance(mw, (tuple, list)) and len(mw) >= 2:
                    mw_list.append((mw[0], mw[1]))
                elif hasattr(mw, "class_path"):
                    mw_list.append((mw.class_path, getattr(mw, "config", {}) or {}))
                elif isinstance(mw, str):
                    mw_list.append((mw, {}))
            ctx.middlewares = mw_list

            app_contexts.append(ctx)

        # Build dependency graph
        dep_graph = {}
        for actx in app_contexts:
            dep_graph[actx.name] = actx.depends_on

        # Build route index
        route_index = {}
        for actx in app_contexts:
            prefix = getattr(actx.manifest, "route_prefix", f"/{actx.name}")
            for ctrl in actx.controllers:
                route_index[f"{prefix}/*"] = {"controller": ctrl, "module": actx.name}

        # Create config
        config = ConfigLoader()
        config.config_data["debug"] = (mode == RegistryMode.DEV)
        config.config_data["mode"] = mode.value
        config.config_data["apps"] = {m: {} for m in self._modules}
        config._build_apps_namespace()

        registry = AquilaryRegistry(
            app_contexts=app_contexts,
            fingerprint=self.fingerprint,
            mode=mode,
            dependency_graph=dep_graph,
            route_index=route_index,
            validation_report={"status": "compiled", "errors": [], "warnings": []},
            config=config,
        )

        return registry


# ═══════════════════════════════════════════════════════════════════════════
# Build Pipeline
# ═══════════════════════════════════════════════════════════════════════════


class AquiliaBuildPipeline:
    """
    Vite-inspired build pipeline for Aquilia.

    Sequences:
    1. **Discovery** — Scan modules/, discover components via AST
    2. **Validation** — Validate manifests, route conflicts, dependencies
    3. **Static Check** — Check Python syntax, import resolution
    4. **Compilation** — Compile manifests to artifact payloads
    5. **Bundling** — Serialize to Crous binary with dedup + compression
    6. **Fingerprint** — Generate deterministic build fingerprint

    If any phase fails, subsequent phases are skipped and the build
    result reports all errors with file:line references.
    """

    def __init__(self, config: BuildConfig):
        self.config = config
        self.workspace_root = Path(config.workspace_root).resolve()
        self.output_dir = self.workspace_root / config.output_dir
        self.modules_dir = self.workspace_root / "modules"

    @classmethod
    def build(
        cls,
        workspace_root: str = ".",
        mode: str = "dev",
        verbose: bool = False,
        compression: str = "",
        check_only: bool = False,
        output_dir: str = "build",
    ) -> BuildResult:
        """
        Execute the complete build pipeline.

        Args:
            workspace_root: Path to workspace root
            mode: Build mode ("dev" or "prod")
            verbose: Enable verbose output
            compression: Compression type ("none", "lz4", "zstd")
            check_only: Only run checks, don't emit artifacts
            output_dir: Output directory for build artifacts

        Returns:
            BuildResult with success status, errors, and bundle manifest
        """
        if not compression:
            compression = "lz4" if mode == "prod" else "none"

        config = BuildConfig(
            mode=mode,
            workspace_root=workspace_root,
            output_dir=output_dir,
            compression=compression,
            verbose=verbose,
            check_only=check_only,
            strict=(mode == "prod"),
        )

        pipeline = cls(config)
        return pipeline.execute()

    def execute(self) -> BuildResult:
        """Execute all build phases in sequence."""
        total_start = time.monotonic()
        result = BuildResult(config=self.config)
        result._workspace_root = self.workspace_root

        def _log(level: str, msg: str) -> None:
            """Append a timestamped log line to the result."""
            import datetime as _dt
            ts = _dt.datetime.now().strftime("%H:%M:%S.%f")[:-3]
            result.log_lines.append(f"[{ts}] [{level.upper():>5}] {msg}")

        self._log = _log

        # Ensure workspace root is on sys.path
        ws_str = str(self.workspace_root)
        if ws_str not in sys.path:
            sys.path.insert(0, ws_str)

        if self.config.verbose:
            logger.info(f"Building workspace: {self.workspace_root}")
            logger.info(f"Mode: {self.config.mode} | Compression: {self.config.compression}")

        _log("info", f"Build started — workspace: {self.workspace_root}")
        _log("info", f"Mode: {self.config.mode} | Compression: {self.config.compression}")

        # Phase 1: Discovery
        _log("info", "Phase 1/6: Discovery — scanning modules/")
        phase_start = time.monotonic()
        workspace_meta, module_names, module_manifests = self._phase_discovery(result)
        result.phases["discovery"] = (time.monotonic() - phase_start) * 1000
        _log("info", f"Discovery complete — {len(module_names)} module(s) found ({result.phases['discovery']:.0f}ms)")

        if result.errors:
            for e in result.errors:
                _log("error", str(e))
            _log("error", "Build aborted due to discovery errors")
            result.total_ms = (time.monotonic() - total_start) * 1000
            self._write_build_log(result)
            return result

        result._workspace_name = workspace_meta.get("name", "workspace")
        result._workspace_version = workspace_meta.get("version", "0.1.0")
        result._modules = module_names
        result._module_manifests = module_manifests

        # Phase 2: Validation
        _log("info", "Phase 2/6: Validation — checking manifests & dependencies")
        phase_start = time.monotonic()
        self._phase_validation(result, module_manifests)
        result.phases["validation"] = (time.monotonic() - phase_start) * 1000
        _log("info", f"Validation complete ({result.phases['validation']:.0f}ms)")

        if result.errors:
            for e in result.errors:
                _log("error", str(e))
            _log("error", "Build aborted due to validation errors")
            result.total_ms = (time.monotonic() - total_start) * 1000
            self._write_build_log(result)
            return result

        # Phase 3: Static Check
        if not self.config.skip_checks:
            _log("info", "Phase 3/6: Static Check — analyzing source files")
            phase_start = time.monotonic()
            self._phase_static_check(result)
            result.phases["static_check"] = (time.monotonic() - phase_start) * 1000
            _log("info", f"Static check complete — {result.files_checked} files ({result.phases['static_check']:.0f}ms)")

            if result.errors:
                for e in result.errors:
                    _log("error", str(e))
                _log("error", "Build aborted due to static check errors")
                result.total_ms = (time.monotonic() - total_start) * 1000
                self._write_build_log(result)
                return result
        else:
            _log("warn", "Phase 3/6: Static Check — SKIPPED (skip_checks=True)")

        # If check_only, stop here
        if self.config.check_only:
            _log("info", "check_only mode — stopping after checks")
            result.success = True
            result.total_ms = (time.monotonic() - total_start) * 1000
            self._write_build_log(result)
            return result

        # Phase 4: Compilation
        _log("info", "Phase 4/6: Compilation — compiling modules to artifacts")
        phase_start = time.monotonic()
        compiled_artifacts = self._phase_compilation(
            result, workspace_meta, module_names, module_manifests,
        )
        result.phases["compilation"] = (time.monotonic() - phase_start) * 1000
        _log("info", f"Compilation complete — {len(compiled_artifacts)} artifact(s) ({result.phases['compilation']:.0f}ms)")

        if result.errors:
            for e in result.errors:
                _log("error", str(e))
            _log("error", "Build aborted due to compilation errors")
            result.total_ms = (time.monotonic() - total_start) * 1000
            self._write_build_log(result)
            return result

        # Phase 5: Bundling
        _log("info", "Phase 5/6: Bundling — serializing to Crous binary format")
        phase_start = time.monotonic()
        bundle = self._phase_bundling(result, compiled_artifacts, workspace_meta)
        result.phases["bundling"] = (time.monotonic() - phase_start) * 1000
        _log("info", f"Bundling complete ({result.phases['bundling']:.0f}ms)")

        if result.errors:
            for e in result.errors:
                _log("error", str(e))
            _log("error", "Build aborted due to bundling errors")
            result.total_ms = (time.monotonic() - total_start) * 1000
            self._write_build_log(result)
            return result

        # Phase 6: Fingerprint
        _log("info", "Phase 6/6: Fingerprint — computing content hash")
        result.bundle = bundle
        result.fingerprint = bundle.fingerprint if bundle else ""
        result.artifacts_count = len(bundle.artifacts) if bundle else 0
        result.success = True
        result.total_ms = (time.monotonic() - total_start) * 1000

        _log("info", f"Build succeeded in {result.total_ms:.0f}ms — {result.artifacts_count} artifacts, fingerprint:{result.fingerprint[:12]}…")
        if result.warnings:
            for w in result.warnings:
                _log("warn", str(w))

        if self.config.verbose:
            logger.info(f"Build complete: {result.summary()}")

        self._write_build_log(result)
        return result

    def _write_build_log(self, result: BuildResult) -> None:
        """Persist build log lines to build_output.txt."""
        try:
            self.output_dir.mkdir(parents=True, exist_ok=True)
            log_path = self.output_dir / "build_output.txt"
            log_path.write_text("\n".join(result.log_lines) + "\n", encoding="utf-8")
        except Exception:
            pass

    # ── Phase 1: Discovery ───────────────────────────────────────────

    def _phase_discovery(
        self, result: BuildResult,
    ) -> Tuple[Dict[str, Any], List[str], Dict[str, Any]]:
        """
        Discover workspace structure and load manifests.

        Returns:
            (workspace_meta, module_names, module_manifests)
        """
        workspace_meta: Dict[str, Any] = {}
        module_names: List[str] = []
        module_manifests: Dict[str, Any] = {}

        # Read workspace.py
        ws_file = self.workspace_root / "workspace.py"
        if not ws_file.exists():
            result.errors.append(BuildError(
                phase=BuildPhase.DISCOVERY,
                message="workspace.py not found",
                hint="Run 'aq init workspace <name>' to create one",
                fatal=True,
            ))
            return workspace_meta, module_names, module_manifests

        try:
            content = ws_file.read_text(encoding="utf-8")
        except Exception as e:
            result.errors.append(BuildError(
                phase=BuildPhase.DISCOVERY,
                message=f"Cannot read workspace.py: {e}",
                file="workspace.py",
                fatal=True,
            ))
            return workspace_meta, module_names, module_manifests

        # Strip comments
        clean = "\n".join(
            line for line in content.splitlines()
            if not line.strip().startswith("#")
        )

        # Extract workspace info
        name_match = re.search(r'Workspace\("([^"]+)"', content)
        version_match = re.search(r'version="([^"]+)"', content)
        desc_match = re.search(r'description="([^"]+)"', content)

        workspace_meta = {
            "name": name_match.group(1) if name_match else "aquilia-workspace",
            "version": version_match.group(1) if version_match else "0.1.0",
            "description": desc_match.group(1) if desc_match else "",
        }

        # Extract module names
        raw_modules = re.findall(r'Module\("([^"]+)"', clean)
        module_names = [m for m in raw_modules if m != "starter"]

        workspace_meta["modules"] = module_names

        if self.config.verbose:
            logger.info(f"  Discovered {len(module_names)} module(s): {', '.join(module_names)}")

        # Load each module's manifest
        for mod_name in module_names:
            manifest_path = self.modules_dir / mod_name / "manifest.py"

            if not manifest_path.exists():
                result.errors.append(BuildError(
                    phase=BuildPhase.DISCOVERY,
                    message=f"Module manifest not found: modules/{mod_name}/manifest.py",
                    file=f"modules/{mod_name}/",
                    hint=f"Run 'aq add module {mod_name}' to create it",
                    fatal=True,
                ))
                continue

            # Safe-load the manifest (isolated namespace, no side effects)
            try:
                manifest_obj = self._safe_load_manifest(mod_name, manifest_path)
                module_manifests[mod_name] = manifest_obj

                if self.config.verbose:
                    v = getattr(manifest_obj, "version", "?")
                    c = len(getattr(manifest_obj, "controllers", []) or [])
                    s = len(getattr(manifest_obj, "services", []) or [])
                    logger.info(f"    {mod_name} v{v}: {c} controller(s), {s} service(s)")

            except Exception as e:
                result.errors.append(BuildError(
                    phase=BuildPhase.DISCOVERY,
                    message=f"Failed to load manifest for '{mod_name}': {e}",
                    file=f"modules/{mod_name}/manifest.py",
                    fatal=True,
                ))

        return workspace_meta, module_names, module_manifests

    def _safe_load_manifest(self, module_name: str, manifest_path: Path) -> Any:
        """
        Load a manifest.py file in an isolated namespace.

        Uses importlib to import the manifest module without polluting
        the global namespace. Returns the ``manifest`` variable.
        """
        spec = importlib.util.spec_from_file_location(
            f"_build_{module_name}_manifest",
            manifest_path,
        )
        if not spec or not spec.loader:
            raise ImportError(f"Cannot create module spec for {manifest_path}")

        module = importlib.util.module_from_spec(spec)
        sys.modules[spec.name] = module

        try:
            spec.loader.exec_module(module)
        finally:
            sys.modules.pop(spec.name, None)

        # Convention: manifest = AppManifest(...)
        manifest_obj = getattr(module, "manifest", None)
        if manifest_obj is not None:
            return manifest_obj

        # Fallback: find any AppManifest instance
        from aquilia.manifest import AppManifest
        for attr_name in dir(module):
            obj = getattr(module, attr_name)
            if isinstance(obj, AppManifest):
                return obj

        raise ValueError(
            f"No 'manifest' variable found in {manifest_path}. "
            f"Expected: manifest = AppManifest(name='{module_name}', ...)"
        )

    # ── Phase 2: Validation ──────────────────────────────────────────

    def _phase_validation(
        self, result: BuildResult, module_manifests: Dict[str, Any],
    ) -> None:
        """Validate manifests using the Aquilary validator."""
        try:
            from aquilia.aquilary.validator import RegistryValidator
            from aquilia.aquilary.core import RegistryMode

            mode = RegistryMode(self.config.mode) if self.config.mode in ("dev", "prod", "test") else RegistryMode.DEV
            validator = RegistryValidator(mode=mode)

            manifests = list(module_manifests.values())
            if not manifests:
                return

            # Create a minimal config for validation
            from aquilia.config import ConfigLoader
            config = ConfigLoader()

            report = validator.validate_manifests(manifests, config)

            # Convert validation errors to build errors
            for err in report.errors:
                msg = str(err) if not hasattr(err, "validation_errors") else "; ".join(
                    getattr(err, "validation_errors", [str(err)])
                )
                result.errors.append(BuildError(
                    phase=BuildPhase.VALIDATION,
                    message=msg,
                    fatal=True,
                ))

            for warn in report.warnings:
                be = BuildError(
                    phase=BuildPhase.VALIDATION,
                    message=str(warn),
                    fatal=False,
                )
                if self.config.strict:
                    result.errors.append(be)
                else:
                    result.warnings.append(be)

        except Exception as e:
            # Validation infrastructure failure — warn but don't block
            result.warnings.append(BuildError(
                phase=BuildPhase.VALIDATION,
                message=f"Validation could not run: {e}",
                fatal=False,
            ))

    # ── Phase 3: Static Check ────────────────────────────────────────

    def _phase_static_check(self, result: BuildResult) -> None:
        """Run static syntax and structure checks."""
        checker = StaticChecker(self.workspace_root, verbose=self.config.verbose)
        check_result = checker.check_all()

        result.files_checked = check_result.files_checked

        for err in check_result.errors:
            be = BuildError(
                phase=BuildPhase.STATIC_CHECK,
                message=err.message,
                file=err.file,
                line=err.line,
                hint=err.hint,
                fatal=(err.severity == CheckSeverity.ERROR),
            )
            if be.fatal:
                result.errors.append(be)
            elif self.config.strict and err.severity == CheckSeverity.WARNING:
                result.errors.append(be)
            else:
                result.warnings.append(be)

    # ── Phase 4: Compilation ─────────────────────────────────────────

    def _phase_compilation(
        self,
        result: BuildResult,
        workspace_meta: Dict[str, Any],
        module_names: List[str],
        module_manifests: Dict[str, Any],
    ) -> Dict[str, Dict[str, Any]]:
        """
        Compile manifests into artifact payload dicts.

        Returns:
            Dict of artifact_name → {kind, version, payload}
        """
        compiled: Dict[str, Dict[str, Any]] = {}

        # 1. Workspace metadata artifact
        compiled[workspace_meta["name"]] = {
            "kind": "workspace",
            "version": workspace_meta["version"],
            "payload": {
                "__format__": "aquilia-artifact",
                "schema_version": "2.0",
                "type": "workspace_metadata",
                "name": workspace_meta["name"],
                "version": workspace_meta["version"],
                "description": workspace_meta.get("description", ""),
                "modules": module_names,
                "mode": self.config.mode,
            },
        }

        # 2. Registry artifact (module catalog)
        registry_modules = []
        for mod_name in module_names:
            manifest = module_manifests.get(mod_name)
            if manifest:
                faults_cfg = getattr(manifest, "faults", None)
                default_domain = "GENERIC"
                if faults_cfg:
                    default_domain = getattr(faults_cfg, "default_domain", "GENERIC")

                registry_modules.append({
                    "name": getattr(manifest, "name", mod_name),
                    "version": getattr(manifest, "version", "0.1.0"),
                    "description": getattr(manifest, "description", ""),
                    "fault_domain": default_domain,
                    "depends_on": getattr(manifest, "depends_on", []) or [],
                    "route_prefix": getattr(manifest, "route_prefix", f"/{mod_name}"),
                })

        compiled["registry"] = {
            "kind": "registry",
            "version": workspace_meta["version"],
            "payload": {
                "__format__": "aquilia-artifact",
                "schema_version": "2.0",
                "type": "registry",
                "modules": registry_modules,
            },
        }

        # 3. Per-module artifacts
        for mod_name in module_names:
            manifest = module_manifests.get(mod_name)
            if not manifest:
                continue

            controllers = []
            for c in (getattr(manifest, "controllers", []) or []):
                controllers.append(c if isinstance(c, str) else str(c))

            services = []
            for s in (getattr(manifest, "services", []) or []):
                if isinstance(s, str):
                    services.append(s)
                elif hasattr(s, "to_dict"):
                    services.append(s.to_dict())
                else:
                    services.append(str(s))

            faults_cfg = getattr(manifest, "faults", None)
            fault_domain = "GENERIC"
            if faults_cfg:
                fault_domain = getattr(faults_cfg, "default_domain", "GENERIC")

            compiled[mod_name] = {
                "kind": "module",
                "version": getattr(manifest, "version", "0.1.0"),
                "payload": {
                    "__format__": "aquilia-artifact",
                    "schema_version": "2.0",
                    "type": "module",
                    "name": mod_name,
                    "version": getattr(manifest, "version", "0.1.0"),
                    "description": getattr(manifest, "description", ""),
                    "route_prefix": getattr(manifest, "route_prefix", f"/{mod_name}"),
                    "fault_domain": fault_domain,
                    "depends_on": getattr(manifest, "depends_on", []) or [],
                    "controllers": controllers,
                    "services": services,
                },
            }

        # 4. Routes artifact
        routes = []
        for mod_name in module_names:
            manifest = module_manifests.get(mod_name)
            if not manifest:
                continue

            prefix = getattr(manifest, "route_prefix", f"/{mod_name}")
            for ctrl in (getattr(manifest, "controllers", []) or []):
                ctrl_str = ctrl if isinstance(ctrl, str) else str(ctrl)
                cls_name = ctrl_str.rsplit(":", 1)[1] if ":" in ctrl_str else ctrl_str
                routes.append({
                    "module": mod_name,
                    "controller": cls_name,
                    "controller_path": ctrl_str,
                    "prefix": prefix,
                })

        compiled["routes"] = {
            "kind": "route",
            "version": workspace_meta["version"],
            "payload": {
                "__format__": "aquilia-artifact",
                "schema_version": "2.0",
                "type": "routes",
                "routes": routes,
            },
        }

        # 5. DI graph artifact
        providers = []
        for mod_name in module_names:
            manifest = module_manifests.get(mod_name)
            if not manifest:
                continue

            for svc in (getattr(manifest, "services", []) or []):
                svc_path = ""
                scope = "app"
                if isinstance(svc, str):
                    svc_path = svc
                elif hasattr(svc, "class_path"):
                    svc_path = svc.class_path
                    scope_val = getattr(svc, "scope", "app")
                    scope = scope_val.value if hasattr(scope_val, "value") else str(scope_val)

                if svc_path:
                    svc_name = svc_path.rsplit(":", 1)[-1] if ":" in svc_path else svc_path
                    providers.append({
                        "module": mod_name,
                        "class": svc_name,
                        "class_path": svc_path,
                        "scope": scope,
                    })

        compiled["di"] = {
            "kind": "di_graph",
            "version": workspace_meta["version"],
            "payload": {
                "__format__": "aquilia-artifact",
                "schema_version": "2.0",
                "type": "di_graph",
                "providers": providers,
            },
        }

        if self.config.verbose:
            logger.info(f"  Compiled {len(compiled)} artifacts")

        return compiled

    # ── Phase 5: Bundling ────────────────────────────────────────────

    def _phase_bundling(
        self,
        result: BuildResult,
        compiled: Dict[str, Dict[str, Any]],
        workspace_meta: Dict[str, Any],
    ) -> Optional[BundleManifest]:
        """Serialize compiled artifacts to Crous binary."""
        try:
            bundler = CrousBundler(
                output_dir=self.output_dir,
                compression=self.config.compression,
                verbose=self.config.verbose,
            )

            for name, artifact_info in compiled.items():
                bundler.bundle_artifact(
                    name=name,
                    kind=artifact_info["kind"],
                    version=artifact_info["version"],
                    payload=artifact_info["payload"],
                )

            bundle = bundler.create_bundle(
                workspace_name=workspace_meta["name"],
                workspace_version=workspace_meta["version"],
                mode=self.config.mode,
            )

            bundle.build_time_ms = sum(result.phases.values())

            return bundle

        except Exception as e:
            result.errors.append(BuildError(
                phase=BuildPhase.BUNDLING,
                message=f"Bundling failed: {e}",
                fatal=True,
            ))
            return None
