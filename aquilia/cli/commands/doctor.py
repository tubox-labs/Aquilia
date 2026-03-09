"""Workspace diagnostics command -- ``aq doctor``.

Performs comprehensive health checks on an Aquilia workspace covering
every layer of the Manifest-First Architecture:

  Phase 1 -- Environment:   Python version, Aquilia installation, dependencies
  Phase 2 -- Workspace:     File presence, directory structure, config files
  Phase 3 -- Manifests:     Load, validate, field completeness
  Phase 4 -- Pipeline:      Aquilary validation, dependency graph, fingerprint
  Phase 5 -- Integrations:  DB connectivity, cache, sessions, mail, auth, templates
  Phase 6 -- Deployment:    Docker files, compose, Kubernetes manifests
"""

import re
import sys
import os
import importlib.util
from pathlib import Path
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass, field


@dataclass
class DiagnosticResult:
    """Structured diagnostic result."""

    category: str
    label: str
    passed: bool
    detail: str = ""


@dataclass
class DiagnosticReport:
    """Complete diagnostic report."""

    results: List[DiagnosticResult] = field(default_factory=list)
    issues: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)

    @property
    def passed(self) -> bool:
        return len(self.issues) == 0

    def add(
        self,
        category: str,
        label: str,
        passed: bool,
        detail: str = "",
    ) -> None:
        self.results.append(DiagnosticResult(category, label, passed, detail))
        if not passed and "warn" not in category.lower():
            self.issues.append(f"[{category}] {label}: {detail}" if detail else f"[{category}] {label}")

    def warn(self, message: str) -> None:
        self.warnings.append(message)


def _check_python_version(report: DiagnosticReport) -> None:
    """Check Python version meets minimum requirements (>=3.10)."""
    v = sys.version_info
    version_str = f"{v.major}.{v.minor}.{v.micro}"
    if v >= (3, 10):
        report.add("Environment", f"Python {version_str}", True)
    else:
        report.add("Environment", f"Python {version_str}", False,
                    "Aquilia requires Python >= 3.10")


def _check_aquilia_installation(report: DiagnosticReport) -> None:
    """Check Aquilia framework is installed and importable."""
    try:
        import aquilia
        version = getattr(aquilia, "__version__", "unknown")
        report.add("Environment", f"Aquilia {version} installed", True)
    except ImportError:
        report.add("Environment", "Aquilia not installed", False,
                    "Install with: pip install aquilia")
        return

    # Check key sub-packages
    sub_packages = [
        ("aquilia.manifest", "Manifest system"),
        ("aquilia.aquilary", "Aquilary registry"),
        ("aquilia.config", "Config system"),
        ("aquilia.server", "Server engine"),
        ("aquilia.di", "DI container"),
        ("aquilia.faults", "Fault system"),
        ("aquilia.controller", "Controller system"),
        ("aquilia.effects", "Effects system"),
        ("aquilia.blueprints", "Blueprints"),
    ]
    for mod_path, label in sub_packages:
        try:
            importlib.import_module(mod_path)
            report.add("Environment", label, True)
        except ImportError as e:
            report.add("Environment", label, False, str(e)[:60])


def _check_dependencies(report: DiagnosticReport, workspace_root: Path) -> None:
    """Check key runtime dependencies."""
    # Check uvicorn (required for dev server)
    try:
        import uvicorn
        report.add("Dependencies", "uvicorn", True, getattr(uvicorn, "__version__", ""))
    except ImportError:
        report.warn("uvicorn not installed (needed for: aq run)")

    # Check optional but common dependencies
    optional_deps = {
        "orjson": "Fast JSON serialization",
        "pyyaml": "YAML config parsing",
        "click": "CLI framework",
        "watchfiles": "Hot-reload file watching",
    }
    for pkg, desc in optional_deps.items():
        try:
            mod = importlib.import_module(pkg)
            report.add("Dependencies", f"{pkg} ({desc})", True)
        except ImportError:
            report.warn(f"{pkg} not installed -- {desc}")

    # Check requirements.txt / pyproject.toml consistency
    req_file = workspace_root / "requirements.txt"
    pyproject = workspace_root / "pyproject.toml"
    if req_file.exists():
        report.add("Dependencies", "requirements.txt present", True)
    elif pyproject.exists():
        report.add("Dependencies", "pyproject.toml present", True)
    else:
        report.warn("No requirements.txt or pyproject.toml found")


def _check_workspace_structure(
    report: DiagnosticReport,
    workspace_root: Path,
    verbose: bool,
) -> Optional[Path]:
    """Check workspace file presence and directory structure."""
    from ..utils.workspace import get_workspace_file

    ws_file = get_workspace_file(workspace_root)
    if not ws_file:
        report.add("Workspace", "Workspace config file", False,
                    "Missing workspace.py or aquilia.py")
        return None

    report.add("Workspace", f"Workspace file: {ws_file.name}", True)

    # Required directories
    for dir_name in ("modules",):
        d = workspace_root / dir_name
        if d.exists():
            report.add("Workspace", f"{dir_name}/ directory", True)
        else:
            report.add("Workspace", f"{dir_name}/ directory", False, "Missing")

    # Recommended directories
    for dir_name in ():
        d = workspace_root / dir_name
        if d.exists():
            report.add("Workspace", f"{dir_name}/ directory", True)
        else:
            report.warn(f"Recommended directory missing: {dir_name}/")

    # Check for inline AquilaConfig in workspace.py
    if ws_file:
        try:
            ws_content = ws_file.read_text(encoding="utf-8")
            if "AquilaConfig" in ws_content:
                report.add("Config", "AquilaConfig in workspace.py", True)
            else:
                report.warn("workspace.py has no AquilaConfig — env config missing")
        except Exception:
            pass

    return ws_file


def _check_manifests(
    report: DiagnosticReport,
    workspace_root: Path,
    ws_file: Path,
    verbose: bool,
) -> Tuple[List[str], list]:
    """Load and validate all module manifests."""
    try:
        ws_content = ws_file.read_text()
        # Strip comments to avoid matching commented-out modules
        clean = "\n".join(
            line for line in ws_content.splitlines()
            if not line.strip().startswith("#")
        )
        registered_modules = re.findall(r'Module\("([^"]+)"', clean)
        # Deduplicate
        seen: set = set()
        unique: list = []
        for m in registered_modules:
            if m not in seen:
                seen.add(m)
                unique.append(m)
        registered_modules = unique
    except Exception as e:
        report.add("Manifests", "Parse workspace.py", False, str(e)[:80])
        return [], []

    if not registered_modules:
        report.warn("No modules registered in workspace configuration")
        return [], []

    report.add("Manifests", f"{len(registered_modules)} module(s) registered", True,
               ", ".join(registered_modules))

    modules_dir = workspace_root / "modules"
    if not modules_dir.exists():
        return registered_modules, []

    # Ensure workspace root is in sys.path
    ws_abs = str(workspace_root.resolve())
    if ws_abs not in sys.path:
        sys.path.insert(0, ws_abs)

    loaded_manifests = []

    for mod_name in registered_modules:
        if mod_name == "starter":
            continue

        mod_dir = modules_dir / mod_name

        # Directory exists?
        if not mod_dir.exists():
            report.add("Manifests", f"Module '{mod_name}' directory", False,
                        f"modules/{mod_name}/ not found")
            continue

        # manifest.py exists?
        manifest_path = mod_dir / "manifest.py"
        if not manifest_path.exists():
            report.add("Manifests", f"Module '{mod_name}' manifest.py", False, "Missing")
            continue

        # __init__.py exists?
        if not (mod_dir / "__init__.py").exists():
            report.warn(f"Module '{mod_name}' missing __init__.py")

        # Load manifest
        manifest_obj = None
        try:
            spec = importlib.util.spec_from_file_location(
                f"_doctor_{mod_name}_manifest", manifest_path,
            )
            if spec and spec.loader:
                mod = importlib.util.module_from_spec(spec)
                sys.modules[spec.name] = mod
                spec.loader.exec_module(mod)

                manifest_obj = getattr(mod, "manifest", None)
                if manifest_obj is None:
                    from aquilia.manifest import AppManifest
                    for _n, obj in vars(mod).items():
                        if isinstance(obj, AppManifest):
                            manifest_obj = obj
                            break

            if manifest_obj is None:
                report.add("Manifests", f"Module '{mod_name}' manifest", False,
                           "No AppManifest instance found")
                continue

            loaded_manifests.append(manifest_obj)
            report.add("Manifests", f"Module '{mod_name}' manifest loaded", True)

        except Exception as e:
            report.add("Manifests", f"Module '{mod_name}' manifest", False,
                        f"Import error: {str(e)[:80]}")
            continue

        # Validate controller references
        controllers = getattr(manifest_obj, "controllers", []) or []
        for ctrl_ref in controllers:
            if not isinstance(ctrl_ref, str) or ":" not in ctrl_ref:
                continue
            mod_path, cls_name = ctrl_ref.rsplit(":", 1)
            parts = mod_path.split(".")
            if parts[0] == "modules" and len(parts) > 1:
                file_parts = parts[1:]
                file_path = workspace_root / "modules"
                for p in file_parts:
                    file_path = file_path / p
                file_path = file_path.with_suffix(".py")
                if not file_path.exists():
                    pkg_path = file_path.with_suffix("") / "__init__.py"
                    if not pkg_path.exists():
                        report.add(
                            "Manifests",
                            f"Controller ref: {ctrl_ref}",
                            False,
                            f"File not found: {file_path.relative_to(workspace_root)}",
                        )

        # Validate service references
        services = getattr(manifest_obj, "services", []) or []
        for svc_ref in services:
            svc_str = svc_ref if isinstance(svc_ref, str) else getattr(svc_ref, "class_path", "")
            if not isinstance(svc_str, str) or ":" not in svc_str:
                continue
            mod_path, cls_name = svc_str.rsplit(":", 1)
            parts = mod_path.split(".")
            if parts[0] == "modules" and len(parts) > 1:
                file_parts = parts[1:]
                file_path = workspace_root / "modules"
                for p in file_parts:
                    file_path = file_path / p
                file_path = file_path.with_suffix(".py")
                if not file_path.exists():
                    pkg_path = file_path.with_suffix("") / "__init__.py"
                    if not pkg_path.exists():
                        report.add(
                            "Manifests",
                            f"Service ref: {svc_str}",
                            False,
                            f"File not found: {file_path.relative_to(workspace_root)}",
                        )

        # Dependency check
        depends_on = getattr(manifest_obj, "depends_on", []) or []
        for dep in depends_on:
            if dep not in registered_modules:
                report.add(
                    "Manifests",
                    f"Module '{mod_name}' dependency",
                    False,
                    f"Depends on '{dep}' which is not registered",
                )

        # Recommended module files
        recommended = ["controllers.py", "services.py", "faults.py"]
        for fname in recommended:
            if not (mod_dir / fname).exists():
                report.warn(f"Module '{mod_name}' missing recommended file: {fname}")

    return registered_modules, loaded_manifests


def _check_pipeline(
    report: DiagnosticReport,
    loaded_manifests: list,
    verbose: bool,
) -> None:
    """Run the Aquilary pipeline: validation, dependency graph, fingerprint."""
    if not loaded_manifests:
        report.warn("No manifests loaded -- skipping pipeline checks")
        return

    try:
        from aquilia.aquilary.core import RegistryMode
        from aquilia.aquilary.validator import RegistryValidator
        from aquilia.aquilary.graph import DependencyGraph
        from aquilia.aquilary.fingerprint import FingerprintGenerator
    except ImportError:
        report.warn("Aquilary not available -- skipping pipeline checks")
        return

    # Validation
    try:
        validator = RegistryValidator(mode=RegistryMode.DEV)

        # Load config for namespace validation if available
        _config = None
        try:
            from aquilia.config import ConfigLoader
            _config = ConfigLoader.load(paths=["workspace.py"])
            _config._build_apps_namespace()
        except Exception:
            pass

        report_obj = validator.validate_manifests(loaded_manifests, _config)
        if report_obj.has_errors():
            for err in report_obj.errors:
                report.add("Pipeline", "Registry validation", False, str(err)[:120])
        else:
            report.add("Pipeline", "Registry validation passed", True)
        for w in report_obj.warnings:
            report.warn(w)
    except Exception as e:
        report.add("Pipeline", "Registry validation", False, str(e)[:80])

    # Dependency graph
    try:
        graph = DependencyGraph()
        for m in loaded_manifests:
            graph.add_node(m.name, getattr(m, "depends_on", []) or [])

        cycle = graph.find_cycle()
        if cycle:
            report.add("Pipeline", "Dependency cycle", False,
                       " → ".join(cycle))
        else:
            report.add("Pipeline", "No dependency cycles", True)

        order = graph.topological_sort()
        report.add("Pipeline", f"Load order: {' → '.join(order)}", True)
    except Exception as e:
        report.add("Pipeline", "Dependency graph", False, str(e)[:80])

    # Fingerprint
    try:
        fp = FingerprintGenerator.generate(loaded_manifests)
        fp_str = fp if isinstance(fp, str) else str(fp)
        report.add("Pipeline", f"Registry fingerprint: {fp_str[:24]}", True)
    except Exception as e:
        report.warn(f"Could not generate fingerprint: {e}")


def _check_integrations(
    report: DiagnosticReport,
    workspace_root: Path,
    verbose: bool,
) -> None:
    """Check workspace integrations (DB, cache, sessions, etc.)."""
    ws_file = workspace_root / "workspace.py"
    if not ws_file.exists():
        return

    content = ws_file.read_text()

    # Database
    if ".database(" in content:
        report.add("Integrations", "Database configured", True)
        url_match = re.search(r'url="([^"]+)"', content)
        if url_match:
            url = url_match.group(1)
            if "sqlite" in url:
                report.add("Integrations", "Database driver: SQLite", True)
            elif "postgres" in url:
                report.add("Integrations", "Database driver: PostgreSQL", True)
            elif "mysql" in url:
                report.add("Integrations", "Database driver: MySQL", True)

    # Sessions
    if ".sessions(" in content:
        report.add("Integrations", "Sessions configured", True)
    else:
        report.warn("Sessions not configured")

    # Cache
    if "Integration.cache" in content:
        report.add("Integrations", "Cache configured", True)

    # Auth
    if "Integration.auth" in content:
        report.add("Integrations", "Auth configured", True)

    # Templates
    if "Integration.templates" in content:
        report.add("Integrations", "Templates configured", True)

    # Static files
    if "Integration.static_files" in content:
        report.add("Integrations", "Static files configured", True)

    # Security
    security_checks = {
        "cors_enabled=True": "CORS enabled",
        "csrf_protection=True": "CSRF protection enabled",
        "helmet_enabled=True": "Security headers (Helmet) enabled",
        "rate_limiting=True": "Rate limiting enabled",
    }
    for pattern, label in security_checks.items():
        if pattern in content:
            report.add("Security", label, True)


def _check_deployment(
    report: DiagnosticReport,
    workspace_root: Path,
    verbose: bool,
) -> None:
    """Check deployment readiness."""
    files = {
        "Dockerfile": "Docker image build",
        ".dockerignore": "Docker build context filter",
        "docker-compose.yml": "Docker Compose orchestration",
    }

    for fname, desc in files.items():
        fpath = workspace_root / fname
        if fpath.exists():
            report.add("Deployment", f"{fname} ({desc})", True)
        else:
            report.warn(f"Missing deployment file: {fname}")

    # Kubernetes
    k8s_dir = workspace_root / "k8s"
    if k8s_dir.exists():
        report.add("Deployment", "Kubernetes manifests", True)

    # .env file
    env_file = workspace_root / ".env"
    if env_file.exists():
        report.add("Deployment", ".env file present", True)
    else:
        report.warn("No .env file found (recommended for secrets)")

    # .gitignore
    gitignore = workspace_root / ".gitignore"
    if gitignore.exists():
        report.add("Deployment", ".gitignore present", True)


def diagnose_workspace(verbose: bool = False) -> List[str]:
    """
    Comprehensive workspace diagnostics.

    Returns a list of issue strings (empty = healthy workspace).
    Prints check results when verbose=True.

    Args:
        verbose: Enable verbose output with per-check results

    Returns:
        List of issues found
    """
    workspace_root = Path.cwd()
    report = DiagnosticReport()

    try:
        from ..utils.colors import _CHECK, _CROSS
    except ImportError:
        _CHECK = "[ok]"
        _CROSS = "[!!]"

    # ── Phase 1: Environment ──
    _check_python_version(report)
    _check_aquilia_installation(report)
    _check_dependencies(report, workspace_root)

    # ── Phase 2: Workspace structure ──
    ws_file = _check_workspace_structure(report, workspace_root, verbose)
    if ws_file is None:
        # Can't continue without workspace file
        if verbose:
            for r in report.results:
                icon = _CHECK if r.passed else _CROSS
                detail = f" -- {r.detail}" if r.detail else ""
                print(f"  {icon} [{r.category}] {r.label}{detail}")
        return report.issues

    # ── Phase 3: Manifests ──
    registered_modules, loaded_manifests = _check_manifests(
        report, workspace_root, ws_file, verbose,
    )

    # ── Phase 4: Aquilary pipeline ──
    _check_pipeline(report, loaded_manifests, verbose)

    # ── Phase 5: Integrations ──
    _check_integrations(report, workspace_root, verbose)

    # ── Phase 6: Deployment ──
    _check_deployment(report, workspace_root, verbose)

    # ── Print results ──
    if verbose:
        current_category = ""
        for r in report.results:
            if r.category != current_category:
                current_category = r.category
                print(f"\n  ── {current_category} ──")
            icon = _CHECK if r.passed else _CROSS
            detail = f" -- {r.detail}" if r.detail else ""
            print(f"    {icon} {r.label}{detail}")

        if report.warnings:
            print(f"\n  ── Warnings ──")
            for w in report.warnings:
                print(f"    {w}")

        if not report.issues and not report.warnings:
            print(f"\n  {_CHECK} All checks passed -- workspace is healthy")

    return report.issues
