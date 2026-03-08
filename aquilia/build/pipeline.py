"""
Aquilia Build Pipeline -- compile-before-serve orchestrator.

Sequences the complete build lifecycle:

    Discovery → Validation → Static Check → Compile → Bundle → Fingerprint

The build pipeline runs **before** the server starts.
If any phase fails, the build is aborted and a clear error report is
displayed -- the server never boots with broken code.

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

import ast
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
    DONE = "done"


@dataclass
class BuildManifest:
    """
    Typed representation of ``build/manifest.json``.

    This is the **build → deploy contract**: the build pipeline writes
    this file, and the deploy system reads it to avoid re-introspecting
    the workspace.  If a valid ``BuildManifest`` exists the deploy CLI
    can skip ``WorkspaceIntrospector`` entirely.

    Use ``BuildManifest.load(build_dir)`` to deserialise from disk, or
    ``BuildManifest.to_deploy_context()`` to convert into the dict
    format expected by deployment generators.
    """
    schema_version: str = "2.0"
    workspace_name: str = ""
    workspace_version: str = "0.1.0"
    build_mode: str = "dev"
    build_fingerprint: str = ""
    build_timestamp: str = ""
    modules: List[Dict[str, Any]] = field(default_factory=list)
    features: Dict[str, bool] = field(default_factory=dict)
    dependency_graph: Dict[str, List[str]] = field(default_factory=dict)
    artifacts: List[Dict[str, Any]] = field(default_factory=list)
    bundle_path: str = "bundle.crous"
    warnings_count: int = 0

    # ── Factory ──────────────────────────────────────────────────────

    @classmethod
    def load(cls, build_dir: Path) -> "BuildManifest":
        """
        Load a ``BuildManifest`` from ``build/manifest.json``.

        Raises:
            FileNotFoundError: manifest.json does not exist
            ValueError: manifest.json has an invalid format
        """
        manifest_path = build_dir / "manifest.json"
        if not manifest_path.exists():
            raise FileNotFoundError(f"No build manifest at {manifest_path}")

        data = json.loads(manifest_path.read_text(encoding="utf-8"))

        fmt = data.get("__format__", "")
        if fmt != "aquilia-build-manifest":
            raise ValueError(
                f"Invalid build manifest format: {fmt!r} "
                f"(expected 'aquilia-build-manifest')"
            )

        return cls(
            schema_version=data.get("schema_version", "2.0"),
            workspace_name=data.get("workspace_name", ""),
            workspace_version=data.get("workspace_version", "0.1.0"),
            build_mode=data.get("build_mode", "dev"),
            build_fingerprint=data.get("build_fingerprint", ""),
            build_timestamp=data.get("build_timestamp", ""),
            modules=data.get("modules", []),
            features=data.get("features", {}),
            dependency_graph=data.get("dependency_graph", {}),
            artifacts=data.get("artifacts", []),
            bundle_path=data.get("bundle_path", "bundle.crous"),
            warnings_count=data.get("warnings_count", 0),
        )

    # ── Deploy context conversion ────────────────────────────────────

    def to_deploy_context(self, workspace_root: Path) -> Dict[str, Any]:
        """
        Convert the build manifest into the ``wctx`` dict used by
        ``WorkspaceIntrospector.introspect()`` and all deployment
        generators.

        This is the canonical bridge: when a build manifest exists
        the deploy CLI calls this instead of re-scanning the workspace.
        """
        from datetime import datetime, timezone

        feat = self.features

        # Count controllers + services from module metadata
        total_controllers = 0
        total_services = 0
        module_names: List[str] = []
        for mod in self.modules:
            module_names.append(mod.get("name", ""))
            total_controllers += len(mod.get("controllers", []))
            total_services += len(mod.get("services", []))

        # Detect DB driver from workspace (fast filesystem check)
        db_driver = "sqlite"
        for cfg_name in ("prod.yaml", "production.yaml", "base.yaml"):
            cfg_path = workspace_root / "config" / cfg_name
            if cfg_path.exists():
                try:
                    import re as _re
                    cfg_text = cfg_path.read_text(encoding="utf-8")
                    m = _re.search(r'url:\s*"?([^"\s]+)', cfg_text)
                    if m:
                        url_lower = m.group(1).lower()
                        if "postgres" in url_lower:
                            db_driver = "postgres"
                        elif "mysql" in url_lower or "mariadb" in url_lower:
                            db_driver = "mysql"
                    break
                except Exception:
                    pass

        # Detect Python version from pyproject.toml
        python_version = "3.12"
        pyproject = workspace_root / "pyproject.toml"
        if pyproject.exists():
            try:
                import re as _re
                txt = pyproject.read_text(encoding="utf-8")
                m = _re.search(r'requires-python\s*=\s*">=(\d+\.\d+)"', txt)
                if m:
                    major, minor = m.group(1).split(".")
                    python_version = m.group(1) if int(minor) >= 12 else "3.12"
            except Exception:
                pass

        # Worker sizing heuristic
        workers = min(8, max(2, 2 + len(module_names) // 4))

        return {
            # Identity
            "name": self.workspace_name,
            "version": self.workspace_version,
            "python_version": python_version,
            # Server
            "port": 8000,
            "host": "0.0.0.0",
            "workers": workers,
            # Modules
            "modules": module_names,
            "module_count": len(module_names),
            "controller_count": total_controllers,
            "service_count": total_services,
            # Features — map build manifest feature flags → wctx keys
            "has_db": feat.get("db", False),
            "db_url": "",
            "db_driver": db_driver,
            "has_cache": feat.get("cache", False),
            "cache_backend": "redis" if feat.get("cache") else "memory",
            "has_sessions": feat.get("sessions", False),
            "session_store": "redis" if feat.get("sessions") else "memory",
            "has_websockets": feat.get("websockets", False),
            "has_mlops": feat.get("mlops", False),
            "has_mail": feat.get("mail", False),
            "has_auth": feat.get("auth", False),
            "has_templates": feat.get("templates", False),
            "has_static": feat.get("static", False),
            "has_migrations": feat.get("migrations", False),
            "has_openapi": False,
            "has_effects": feat.get("effects", False),
            "has_faults": feat.get("faults", False),
            "cors_enabled": feat.get("cors", False),
            "csrf_protection": feat.get("csrf", False),
            "helmet_enabled": False,
            "rate_limiting": False,
            "tracing_enabled": feat.get("tracing", False),
            "metrics_enabled": feat.get("metrics", False),
            "logging_enabled": False,
            # Dependency info
            "has_pyproject": (workspace_root / "pyproject.toml").exists(),
            "dependencies": [],
            "has_requirements_txt": (workspace_root / "requirements.txt").exists(),
            # Deployment-relevant paths
            "has_dockerfile": (workspace_root / "Dockerfile").exists(),
            "has_compose": (workspace_root / "docker-compose.yml").exists(),
            "has_k8s": (workspace_root / "k8s").exists(),
            # Build metadata
            "build_fingerprint": self.build_fingerprint,
            "build_mode": self.build_mode,
            "build_timestamp": self.build_timestamp,
            "generated_at": datetime.now(tz=timezone.utc).isoformat(),
            "_from_build_manifest": True,
        }


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
    force: bool = False                     # Bypass incremental build cache

    @classmethod
    def dev(cls, workspace_root: str = ".", verbose: bool = False) -> "BuildConfig":
        """Dev build config -- fast, no compression."""
        return cls(
            mode="dev",
            workspace_root=workspace_root,
            output_dir="build",
            compression="none",
            verbose=verbose,
        )

    @classmethod
    def prod(cls, workspace_root: str = ".", verbose: bool = False) -> "BuildConfig":
        """Prod build config -- compressed, strict."""
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
            location += " -- "
        prefix = "" if self.fatal else ""
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
    Aquilia build pipeline.

    Sequences:
    1. **Discovery** -- Scan modules/, discover components via AST
    2. **Validation** -- Validate manifests, route conflicts, dependencies
    3. **Static Check** -- Check Python syntax, import resolution
    4. **Compilation** -- Compile manifests to artifact payloads
    5. **Bundling** -- Serialize to Crous binary with dedup + compression,
       compute fingerprint, and write build manifest

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
        force: bool = False,
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
            force: Bypass incremental build cache

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
            force=force,
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

        _log("info", f"Build started -- workspace: {self.workspace_root}")
        _log("info", f"Mode: {self.config.mode} | Compression: {self.config.compression}")
        if self.config.force:
            _log("info", "Force build -- ignoring cache")

        # ── Incremental: check if full rebuild is needed ─────────────
        # If all phase hashes match and a bundle already exists, the
        # build can be skipped entirely.  Discovery + Validation still
        # run (they're fast and produce essential in-memory state), but
        # static-check, compilation, and bundling are skippable.
        all_cached = (
            not self.config.force
            and not self.config.check_only
            and self._phase_is_cached("discovery")
            and self._phase_is_cached("static_check")
            and self._phase_is_cached("compilation")
            and (self.output_dir / "bundle.crous").exists()
            and (self.output_dir / "manifest.json").exists()
        )
        if all_cached:
            _log("info", "Incremental build: all inputs unchanged -- skipping rebuild")
            result.success = True
            result.total_ms = (time.monotonic() - total_start) * 1000
            # Load fingerprint from existing manifest
            try:
                manifest_data = json.loads(
                    (self.output_dir / "manifest.json").read_text(encoding="utf-8")
                )
                result.fingerprint = manifest_data.get("build_fingerprint", "")
                result.artifacts_count = len(manifest_data.get("artifacts", []))
            except Exception:
                pass
            _log("info", f"Build skipped (cached) in {result.total_ms:.0f}ms")
            self._write_build_log(result)
            return result

        # Phase 1: Discovery
        _log("info", "Phase 1/5: Discovery -- scanning modules/")
        phase_start = time.monotonic()
        workspace_meta, module_names, module_manifests = self._phase_discovery(result)
        result.phases["discovery"] = (time.monotonic() - phase_start) * 1000
        _log("info", f"Discovery complete -- {len(module_names)} module(s) found ({result.phases['discovery']:.0f}ms)")

        if result.errors:
            for e in result.errors:
                _log("error", str(e))
            _log("error", "Build aborted due to discovery errors")
            self._invalidate_cache()
            result.total_ms = (time.monotonic() - total_start) * 1000
            self._write_build_log(result)
            return result

        result._workspace_name = workspace_meta.get("name", "workspace")
        result._workspace_version = workspace_meta.get("version", "0.1.0")
        result._modules = module_names
        result._module_manifests = module_manifests

        # Phase 2: Validation
        _log("info", "Phase 2/5: Validation -- checking manifests & dependencies")
        phase_start = time.monotonic()
        self._phase_validation(result, module_manifests)
        result.phases["validation"] = (time.monotonic() - phase_start) * 1000
        _log("info", f"Validation complete ({result.phases['validation']:.0f}ms)")

        if result.errors:
            for e in result.errors:
                _log("error", str(e))
            _log("error", "Build aborted due to validation errors")
            self._invalidate_cache()
            result.total_ms = (time.monotonic() - total_start) * 1000
            self._write_build_log(result)
            return result

        self._save_phase_hash("discovery")

        # Phase 3: Static Check
        if not self.config.skip_checks:
            if self._phase_is_cached("static_check"):
                _log("info", "Phase 3/5: Static Check -- SKIPPED (cached, inputs unchanged)")
            else:
                _log("info", "Phase 3/5: Static Check -- analyzing source files")
                phase_start = time.monotonic()
                self._phase_static_check(result)
                result.phases["static_check"] = (time.monotonic() - phase_start) * 1000
                _log("info", f"Static check complete -- {result.files_checked} files ({result.phases['static_check']:.0f}ms)")

                if result.errors:
                    for e in result.errors:
                        _log("error", str(e))
                    _log("error", "Build aborted due to static check errors")
                    self._invalidate_cache()
                    result.total_ms = (time.monotonic() - total_start) * 1000
                    self._write_build_log(result)
                    return result

                self._save_phase_hash("static_check")
        else:
            _log("warn", "Phase 3/5: Static Check -- SKIPPED (skip_checks=True)")

        # If check_only, stop here
        if self.config.check_only:
            _log("info", "check_only mode -- stopping after checks")
            result.success = True
            result.total_ms = (time.monotonic() - total_start) * 1000
            self._write_build_log(result)
            return result

        # Phase 4: Compilation
        _log("info", "Phase 4/5: Compilation -- compiling modules to artifacts")
        phase_start = time.monotonic()
        compiled_artifacts = self._phase_compilation(
            result, workspace_meta, module_names, module_manifests,
        )
        result.phases["compilation"] = (time.monotonic() - phase_start) * 1000
        _log("info", f"Compilation complete -- {len(compiled_artifacts)} artifact(s) ({result.phases['compilation']:.0f}ms)")

        if result.errors:
            for e in result.errors:
                _log("error", str(e))
            _log("error", "Build aborted due to compilation errors")
            self._invalidate_cache()
            result.total_ms = (time.monotonic() - total_start) * 1000
            self._write_build_log(result)
            return result

        self._save_phase_hash("compilation")

        # Phase 5: Bundling + Fingerprint
        _log("info", "Phase 5/5: Bundling -- serializing to Crous binary + fingerprint")
        phase_start = time.monotonic()
        bundle = self._phase_bundling(result, compiled_artifacts, workspace_meta)
        result.phases["bundling"] = (time.monotonic() - phase_start) * 1000
        _log("info", f"Bundling complete ({result.phases['bundling']:.0f}ms)")

        if result.errors:
            for e in result.errors:
                _log("error", str(e))
            _log("error", "Build aborted due to bundling errors")
            self._invalidate_cache()
            result.total_ms = (time.monotonic() - total_start) * 1000
            self._write_build_log(result)
            return result

        # Finalize build result
        result.bundle = bundle
        result.fingerprint = bundle.fingerprint if bundle else ""
        result.artifacts_count = len(bundle.artifacts) if bundle else 0
        result.success = True
        result.total_ms = (time.monotonic() - total_start) * 1000

        # Write build/manifest.json (build → deploy contract)
        try:
            self._write_build_manifest(result, workspace_meta, module_manifests)
            _log("info", "Build manifest written to build/manifest.json")
        except Exception as e:
            _log("warn", f"Could not write build manifest: {e}")
            result.warnings.append(BuildError(
                phase=BuildPhase.BUNDLING,
                message=f"Could not write build/manifest.json: {e}",
                fatal=False,
            ))

        _log("info", f"Build succeeded in {result.total_ms:.0f}ms -- {result.artifacts_count} artifacts, fingerprint:{result.fingerprint[:12]}…")
        if result.warnings:
            for w in result.warnings:
                _log("warn", str(w))

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

    # ── Incremental Build Cache ──────────────────────────────────────

    def _cache_dir(self) -> Path:
        """Return the .build-cache directory path."""
        return self.output_dir / ".build-cache"

    def _compute_input_hash(self, phase: str) -> str:
        """
        Compute a content-hash of the inputs relevant to a build phase.

        Phase → input mapping:
        - ``discovery``: workspace.py + modules/*/manifest.py
        - ``validation``: same as discovery (manifests drive validation)
        - ``static_check``: all .py files under modules/
        - ``compilation``: discovery hash + mode + compression
        - ``bundling``: compilation hash

        Returns:
            hex SHA-256 digest of the concatenated input content
        """
        import hashlib as _hl

        hasher = _hl.sha256()

        # Always include the build mode and compression in the hash
        hasher.update(f"mode={self.config.mode}\n".encode())
        hasher.update(f"compression={self.config.compression}\n".encode())
        hasher.update(f"strict={self.config.strict}\n".encode())

        if phase in ("discovery", "validation", "compilation", "bundling"):
            # Hash workspace.py
            ws_file = self.workspace_root / "workspace.py"
            if ws_file.exists():
                hasher.update(ws_file.read_bytes())
            else:
                hasher.update(b"__no_workspace__")

            # Hash all manifest.py files
            if self.modules_dir.exists():
                for manifest_file in sorted(self.modules_dir.glob("*/manifest.py")):
                    hasher.update(str(manifest_file.relative_to(self.workspace_root)).encode())
                    hasher.update(manifest_file.read_bytes())

        if phase == "static_check":
            # Hash all .py source files under modules/
            if self.modules_dir.exists():
                for py_file in sorted(self.modules_dir.rglob("*.py")):
                    hasher.update(str(py_file.relative_to(self.workspace_root)).encode())
                    hasher.update(py_file.read_bytes())

        return hasher.hexdigest()

    def _phase_is_cached(self, phase: str) -> bool:
        """
        Check if a phase can be skipped because its inputs haven't changed.

        Returns True if the phase hash matches the stored hash AND
        ``--force`` was not specified.
        """
        if self.config.force:
            return False

        cache_dir = self._cache_dir()
        cache_file = cache_dir / f"{phase}.hash"
        if not cache_file.exists():
            return False

        try:
            stored_hash = cache_file.read_text(encoding="utf-8").strip()
            current_hash = self._compute_input_hash(phase)
            return stored_hash == current_hash
        except Exception:
            return False

    def _save_phase_hash(self, phase: str) -> None:
        """Persist the current input hash for a phase."""
        try:
            cache_dir = self._cache_dir()
            cache_dir.mkdir(parents=True, exist_ok=True)
            cache_file = cache_dir / f"{phase}.hash"
            current_hash = self._compute_input_hash(phase)
            cache_file.write_text(current_hash + "\n", encoding="utf-8")
        except Exception:
            pass

    def _invalidate_cache(self) -> None:
        """Remove all cached hashes (used on build failure)."""
        try:
            cache_dir = self._cache_dir()
            if cache_dir.exists():
                for f in cache_dir.glob("*.hash"):
                    f.unlink(missing_ok=True)
        except Exception:
            pass

    # ── Phase 1: Discovery ───────────────────────────────────────────

    def _phase_discovery(
        self, result: BuildResult,
    ) -> Tuple[Dict[str, Any], List[str], Dict[str, Any]]:
        """
        Discover workspace structure and load manifests.

        Uses AST-based parsing for reliable extraction of workspace
        metadata and module declarations. Falls back to regex if AST
        parsing fails (e.g. syntax errors in workspace.py).

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

        # ── AST-based discovery (preferred) ──────────────────────────
        ast_ok = False
        try:
            workspace_meta, module_names = self._discover_workspace_ast(content)
            ast_ok = True
        except Exception as e:
            # AST failed — fall back to regex
            result.warnings.append(BuildError(
                phase=BuildPhase.DISCOVERY,
                message=f"AST discovery failed, using regex fallback: {e}",
                fatal=False,
            ))

        # ── Regex fallback ───────────────────────────────────────────
        if not ast_ok:
            workspace_meta, module_names = self._discover_workspace_regex(content)

        workspace_meta["modules"] = module_names

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

            except Exception as e:
                result.errors.append(BuildError(
                    phase=BuildPhase.DISCOVERY,
                    message=f"Failed to load manifest for '{mod_name}': {e}",
                    file=f"modules/{mod_name}/manifest.py",
                    fatal=True,
                ))

        return workspace_meta, module_names, module_manifests

    # ── AST Discovery ────────────────────────────────────────────────

    def _discover_workspace_ast(
        self, content: str,
    ) -> Tuple[Dict[str, Any], List[str]]:
        """
        AST-based workspace discovery.

        Parses workspace.py as an AST and walks the tree for:
        - ``Workspace("name", version="…", description="…")`` calls
        - ``Module("name", …)`` calls

        This is safe (no code execution) and correctly handles:
        - Multi-line chained calls (``.module(Module("x"))``)
        - Keyword arguments in any order
        - Nested call chains
        - Comments and decorators (ignored by AST)

        Returns:
            (workspace_meta, module_names)
        """
        tree = ast.parse(content, filename="workspace.py")

        workspace_name = "aquilia-workspace"
        workspace_version = "0.1.0"
        workspace_description = ""
        module_names: List[str] = []

        for node in ast.walk(tree):
            if not isinstance(node, ast.Call):
                continue

            func_name = self._resolve_ast_call_name(node)

            if func_name == "Workspace":
                # Extract positional name arg
                if node.args and isinstance(node.args[0], ast.Constant):
                    workspace_name = str(node.args[0].value)
                # Extract keyword args
                for kw in node.keywords:
                    if not isinstance(kw.value, ast.Constant):
                        continue
                    if kw.arg == "name" and not node.args:
                        workspace_name = str(kw.value.value)
                    elif kw.arg == "version":
                        workspace_version = str(kw.value.value)
                    elif kw.arg == "description":
                        workspace_description = str(kw.value.value)

            elif func_name == "Module":
                # Extract module name from first positional arg
                if node.args and isinstance(node.args[0], ast.Constant):
                    mod_name = str(node.args[0].value)
                    if mod_name != "starter":
                        module_names.append(mod_name)
                else:
                    # Try keyword: Module(name="x")
                    for kw in node.keywords:
                        if kw.arg == "name" and isinstance(kw.value, ast.Constant):
                            mod_name = str(kw.value.value)
                            if mod_name != "starter":
                                module_names.append(mod_name)
                            break

        workspace_meta = {
            "name": workspace_name,
            "version": workspace_version,
            "description": workspace_description,
        }

        return workspace_meta, module_names

    @staticmethod
    def _resolve_ast_call_name(node: ast.Call) -> str:
        """
        Resolve the function name from an ast.Call node.

        Handles:
        - Simple calls: ``Workspace(...)`` → ``"Workspace"``
        - Attribute calls: ``Integration.di(...)`` → ``"Integration.di"``
        - Chained method calls: ``.module(Module(...))`` → ``"module"``

        Returns the resolved name, or "" if unresolvable.
        """
        func = node.func
        if isinstance(func, ast.Name):
            return func.id
        elif isinstance(func, ast.Attribute):
            # e.g. Integration.di  or  obj.module
            if isinstance(func.value, ast.Name):
                return f"{func.value.id}.{func.attr}"
            # Chained: something.something.method — return just the method
            return func.attr
        return ""

    # ── Regex fallback ───────────────────────────────────────────────

    def _discover_workspace_regex(
        self, content: str,
    ) -> Tuple[Dict[str, Any], List[str]]:
        """
        Regex-based workspace discovery (legacy fallback).

        Used when AST parsing fails (e.g. due to syntax errors or
        dynamic constructs). Less reliable than AST for multi-line
        and complex expressions.

        Returns:
            (workspace_meta, module_names)
        """
        # Strip comments
        clean = "\n".join(
            line for line in content.splitlines()
            if not line.strip().startswith("#")
        )

        name_match = re.search(r'Workspace\("([^"]+)"', content)
        version_match = re.search(r'version="([^"]+)"', content)
        desc_match = re.search(r'description="([^"]+)"', content)

        workspace_meta = {
            "name": name_match.group(1) if name_match else "aquilia-workspace",
            "version": version_match.group(1) if version_match else "0.1.0",
            "description": desc_match.group(1) if desc_match else "",
        }

        raw_modules = re.findall(r'Module\("([^"]+)"', clean)
        module_names = [m for m in raw_modules if m != "starter"]

        return workspace_meta, module_names

    # ── Build Manifest (JSON) ────────────────────────────────────────

    def _write_build_manifest(
        self,
        result: BuildResult,
        workspace_meta: Dict[str, Any],
        module_manifests: Dict[str, Any],
    ) -> None:
        """
        Write build/manifest.json — the build → deploy contract.

        This JSON file captures everything the deploy system needs
        so it can skip re-introspection when a build is available.
        """
        import datetime as _dt

        modules_list = []
        for mod_name in result._modules:
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
                elif hasattr(s, "class_path"):
                    services.append(s.class_path)
                else:
                    services.append(str(s))
            modules_list.append({
                "name": getattr(manifest, "name", mod_name),
                "version": getattr(manifest, "version", "0.1.0"),
                "description": getattr(manifest, "description", ""),
                "route_prefix": getattr(manifest, "route_prefix", f"/{mod_name}"),
                "depends_on": getattr(manifest, "depends_on", []) or [],
                "controllers": controllers,
                "services": services,
            })

        # Detect workspace features by scanning manifest attributes
        features: Dict[str, bool] = {}
        ws_content = ""
        ws_file = self.workspace_root / "workspace.py"
        if ws_file.exists():
            try:
                ws_content = ws_file.read_text(encoding="utf-8")
            except Exception:
                pass
        features = self._detect_workspace_features(ws_content)

        # Artifacts list
        artifacts_list = []
        if result.bundle:
            for a in result.bundle.artifacts:
                artifacts_list.append({
                    "name": a.name,
                    "kind": a.kind,
                    "version": a.version,
                    "size_bytes": a.size_bytes,
                    "digest": a.digest,
                })

        build_manifest = {
            "__format__": "aquilia-build-manifest",
            "schema_version": "2.0",
            "workspace_name": workspace_meta.get("name", ""),
            "workspace_version": workspace_meta.get("version", ""),
            "build_mode": self.config.mode,
            "build_fingerprint": result.fingerprint,
            "build_timestamp": _dt.datetime.now(_dt.timezone.utc).isoformat(),
            "modules": modules_list,
            "features": features,
            "dependency_graph": {
                mod["name"]: mod["depends_on"] for mod in modules_list
            },
            "artifacts": artifacts_list,
            "bundle_path": "bundle.crous",
            "warnings_count": len(result.warnings),
        }

        manifest_path = self.output_dir / "manifest.json"
        manifest_path.write_text(
            json.dumps(build_manifest, indent=2, default=str) + "\n",
            encoding="utf-8",
        )

    def _detect_workspace_features(self, ws_content: str) -> Dict[str, bool]:
        """
        Detect workspace ecosystem features via AST, with regex fallback.

        Scans workspace.py for Integration.xyz() calls (AST) or
        known patterns (regex) to build a features dict.

        Returns:
            Dict of feature_name → bool
        """
        features: Dict[str, bool] = {
            "db": False,
            "cache": False,
            "sessions": False,
            "websockets": False,
            "mlops": False,
            "mail": False,
            "auth": False,
            "templates": False,
            "static": False,
            "migrations": False,
            "faults": False,
            "effects": False,
            "cors": False,
            "csrf": False,
            "tracing": False,
            "metrics": False,
            "admin": False,
            "i18n": False,
        }

        if not ws_content:
            return features

        # ── AST-based detection (preferred) ──────────────────────────
        try:
            tree = ast.parse(ws_content, filename="workspace.py")
            integration_methods: set = set()
            top_level_methods: set = set()

            for node in ast.walk(tree):
                if not isinstance(node, ast.Call):
                    continue
                func = node.func

                # Integration.xyz() calls
                if isinstance(func, ast.Attribute):
                    if isinstance(func.value, ast.Name) and func.value.id == "Integration":
                        integration_methods.add(func.attr)
                    # Chained calls like .sessions(), .middleware()
                    elif isinstance(func.value, ast.Call):
                        top_level_methods.add(func.attr)
                    # Nested attribute: Integration.templates.source() etc
                    elif isinstance(func.value, ast.Attribute):
                        if isinstance(func.value.value, ast.Name) and func.value.value.id == "Integration":
                            integration_methods.add(func.value.attr)

            # Map Integration method names → features
            _integration_to_feature = {
                "database": "db", "db": "db",
                "cache": "cache",
                "sessions": "sessions",
                "websockets": "websockets", "sockets": "websockets",
                "mlops": "mlops",
                "mail": "mail",
                "auth": "auth",
                "templates": "templates",
                "static_files": "static", "static": "static",
                "fault_handling": "faults", "faults": "faults",
                "effects": "effects",
                "cors": "cors",
                "csrf": "csrf",
                "tracing": "tracing",
                "metrics": "metrics",
                "admin": "admin",
                "i18n": "i18n",
                "routing": None,  # routing is always present
                "di": None,
                "registry": None,
                "patterns": None,
                "middleware": None,
            }
            for method_name in integration_methods:
                feat = _integration_to_feature.get(method_name)
                if feat and feat in features:
                    features[feat] = True

            # Chained workspace methods: .sessions(), .middleware(), etc.
            _toplevel_to_feature = {
                "sessions": "sessions",
                "security": "cors",
                "telemetry": "tracing",
            }
            for method_name in top_level_methods:
                feat = _toplevel_to_feature.get(method_name)
                if feat and feat in features:
                    features[feat] = True

            # Check for migrations directory
            if (self.workspace_root / "migrations").is_dir():
                features["migrations"] = True

            return features

        except Exception:
            pass

        # ── Regex fallback ───────────────────────────────────────────
        # Strip comment lines
        active_lines = [
            line for line in ws_content.splitlines()
            if not line.strip().startswith("#")
        ]
        active = "\n".join(active_lines)

        _regex_patterns = {
            "db": r"Integration\.database\(",
            "cache": r"Integration\.cache\(",
            "sessions": r"\.sessions\(|Integration\.sessions\(",
            "websockets": r"Integration\.(?:websockets|sockets)\(",
            "mlops": r"Integration\.mlops\(",
            "mail": r"Integration\.mail\(",
            "auth": r"Integration\.auth\(",
            "templates": r"Integration\.templates",
            "static": r"Integration\.static_files\(",
            "faults": r"Integration\.fault_handling\(",
            "effects": r"Integration\.effects\(",
            "cors": r"Integration\.cors\(|cors_enabled\s*=\s*True",
            "csrf": r"Integration\.csrf\(|csrf_protection\s*=\s*True",
            "tracing": r"tracing_enabled\s*=\s*True|Integration\.tracing\(",
            "metrics": r"metrics_enabled\s*=\s*True|Integration\.metrics\(",
            "admin": r"Integration\.admin\(",
            "i18n": r"Integration\.i18n\(",
        }
        for feat_name, pattern in _regex_patterns.items():
            if re.search(pattern, active):
                features[feat_name] = True

        if (self.workspace_root / "migrations").is_dir():
            features["migrations"] = True

        return features

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

            # Create a minimal config for validation, seeded with app
            # namespaces so _validate_config_namespace doesn't false-positive.
            from aquilia.config import ConfigLoader
            config = ConfigLoader()
            config.config_data["apps"] = {m: {} for m in module_manifests}
            config._build_apps_namespace()

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
            # Validation infrastructure failure -- warn but don't block
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

            # Propagate per-artifact errors from bundler
            for err_msg in bundler.bundle_errors:
                result.errors.append(BuildError(
                    phase=BuildPhase.BUNDLING,
                    message=err_msg,
                    fatal=True,
                ))

            bundle.build_time_ms = sum(result.phases.values())

            return bundle

        except Exception as e:
            result.errors.append(BuildError(
                phase=BuildPhase.BUNDLING,
                message=f"Bundling failed: {e}",
                fatal=True,
            ))
            return None
