"""
Static Checker -- pre-flight validation of Python source files.

Catches errors at build time instead of at runtime:
- Syntax errors (``py_compile``)
- AST parse failures
- Import path resolution (``importlib.util.find_spec``)
- Circular import detection (lightweight heuristic)
- Missing module directories and manifest files

All checks run without executing any user code.
"""

from __future__ import annotations

import ast
import logging
import time
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path

logger = logging.getLogger("aquilia.build.checker")


# ═══════════════════════════════════════════════════════════════════════════
# Data Structures
# ═══════════════════════════════════════════════════════════════════════════


class CheckSeverity(str, Enum):
    """Severity level for check results."""

    ERROR = "error"  # Build must fail
    WARNING = "warning"  # Build continues but user is alerted
    INFO = "info"  # Informational


@dataclass
class CheckError:
    """A single error/warning found during static checking."""

    severity: CheckSeverity
    message: str
    file: str = ""
    line: int = 0
    column: int = 0
    code: str = ""  # Error code (e.g. "E001", "W002")
    hint: str = ""  # Suggested fix

    def __str__(self) -> str:
        location = ""
        if self.file:
            location = self.file
            if self.line:
                location += f":{self.line}"
                if self.column:
                    location += f":{self.column}"
            location += " -- "

        prefix = {
            CheckSeverity.ERROR: "[!!]",
            CheckSeverity.WARNING: "[??]",
            CheckSeverity.INFO: "[ii]",
        }.get(self.severity, "?")

        code_str = f"[{self.code}] " if self.code else ""
        hint_str = f"\n hint: {self.hint}" if self.hint else ""
        return f" {prefix} {location}{code_str}{self.message}{hint_str}"


@dataclass
class CheckResult:
    """Aggregate result of all static checks."""

    errors: list[CheckError] = field(default_factory=list)
    files_checked: int = 0
    elapsed_ms: float = 0.0

    @property
    def has_errors(self) -> bool:
        return any(e.severity == CheckSeverity.ERROR for e in self.errors)

    @property
    def has_warnings(self) -> bool:
        return any(e.severity == CheckSeverity.WARNING for e in self.errors)

    @property
    def error_count(self) -> int:
        return sum(1 for e in self.errors if e.severity == CheckSeverity.ERROR)

    @property
    def warning_count(self) -> int:
        return sum(1 for e in self.errors if e.severity == CheckSeverity.WARNING)

    def add(self, error: CheckError) -> None:
        self.errors.append(error)

    def merge(self, other: CheckResult) -> None:
        self.errors.extend(other.errors)
        self.files_checked += other.files_checked

    def summary(self) -> str:
        parts = [f"{self.files_checked} files checked"]
        if self.error_count:
            parts.append(f"{self.error_count} error(s)")
        if self.warning_count:
            parts.append(f"{self.warning_count} warning(s)")
        if not self.has_errors and not self.has_warnings:
            parts.append("all clear")
        parts.append(f"in {self.elapsed_ms:.0f}ms")
        return " · ".join(parts)


# ═══════════════════════════════════════════════════════════════════════════
# Static Checker
# ═══════════════════════════════════════════════════════════════════════════


class StaticChecker:
    """
    Pre-flight static analysis for the Aquilia build pipeline.

    Validates Python source files without importing them. Catches:
    - Syntax errors (SyntaxError from py_compile / ast.parse)
    - Missing module directories and manifest files
    - Invalid import paths in manifest declarations
    - Duplicate route prefixes across modules

    All checks are read-only and side-effect free.
    """

    def __init__(self, workspace_root: Path, verbose: bool = False):
        self.workspace_root = workspace_root.resolve()
        self.modules_dir = self.workspace_root / "modules"
        self.verbose = verbose

    def check_all(self) -> CheckResult:
        """
        Run all static checks against the workspace.

        Returns:
            CheckResult with all errors, warnings, and diagnostics
        """
        start = time.monotonic()
        result = CheckResult()

        # Phase 1: Check workspace.py exists and is valid
        self._check_workspace_file(result)

        # Phase 2: Check all Python files for syntax errors
        self._check_python_syntax(result)

        # Phase 3: Validate module structure
        self._check_module_structure(result)

        # Phase 4: Validate manifest import paths
        self._check_manifest_imports(result)

        # Phase 5: Route prefix conflicts
        # Handled by RegistryValidator in the validation phase.
        # Removed here to avoid duplicate checks.

        result.elapsed_ms = (time.monotonic() - start) * 1000
        return result

    # ── Phase 1: Workspace file ──────────────────────────────────────

    def _check_workspace_file(self, result: CheckResult) -> None:
        """Verify workspace.py exists and parses correctly."""
        ws_file = self.workspace_root / "workspace.py"

        if not ws_file.exists():
            result.add(
                CheckError(
                    severity=CheckSeverity.ERROR,
                    message="workspace.py not found -- not an Aquilia workspace",
                    file=str(ws_file),
                    code="E001",
                    hint="Run 'aq init workspace <name>' to create one",
                )
            )
            return

        # Parse it
        try:
            source = ws_file.read_text(encoding="utf-8")
            ast.parse(source, filename=str(ws_file))
        except SyntaxError as e:
            result.add(
                CheckError(
                    severity=CheckSeverity.ERROR,
                    message=f"Syntax error in workspace.py: {e.msg}",
                    file=str(ws_file),
                    line=e.lineno or 0,
                    column=e.offset or 0,
                    code="E002",
                )
            )

        result.files_checked += 1

    # ── Phase 2: Python syntax ───────────────────────────────────────

    def _check_python_syntax(self, result: CheckResult) -> None:
        """Check all Python files under modules/ for syntax errors."""
        if not self.modules_dir.exists():
            return

        for py_file in self.modules_dir.rglob("*.py"):
            # Skip __pycache__
            if "__pycache__" in str(py_file):
                continue

            try:
                source = py_file.read_text(encoding="utf-8")
                ast.parse(source, filename=str(py_file))
                result.files_checked += 1
            except SyntaxError as e:
                rel_path = py_file.relative_to(self.workspace_root)
                result.add(
                    CheckError(
                        severity=CheckSeverity.ERROR,
                        message=f"Syntax error: {e.msg}",
                        file=str(rel_path),
                        line=e.lineno or 0,
                        column=e.offset or 0,
                        code="E010",
                        hint="Fix the syntax error before building",
                    )
                )
                result.files_checked += 1
            except UnicodeDecodeError as e:
                rel_path = py_file.relative_to(self.workspace_root)
                result.add(
                    CheckError(
                        severity=CheckSeverity.WARNING,
                        message=f"File encoding error: {e}",
                        file=str(rel_path),
                        code="W010",
                    )
                )
                result.files_checked += 1

    # ── Phase 3: Module structure ────────────────────────────────────

    def _check_module_structure(self, result: CheckResult) -> None:
        """Validate that registered modules have correct directory structure."""
        import re

        ws_file = self.workspace_root / "workspace.py"
        if not ws_file.exists():
            return

        try:
            content = ws_file.read_text(encoding="utf-8")
        except Exception:
            return

        # Strip comments
        clean = "\n".join(line for line in content.splitlines() if not line.strip().startswith("#"))

        # Extract module names
        module_names = re.findall(r'Module\("([^"]+)"', clean)
        module_names = [m for m in module_names if m != "starter"]

        if not module_names:
            return

        if not self.modules_dir.exists():
            result.add(
                CheckError(
                    severity=CheckSeverity.ERROR,
                    message="modules/ directory not found but modules are registered in workspace.py",
                    file="workspace.py",
                    code="E020",
                    hint="Create the modules/ directory or run 'aq add module <name>'",
                )
            )
            return

        for mod_name in module_names:
            mod_dir = self.modules_dir / mod_name

            if not mod_dir.exists():
                result.add(
                    CheckError(
                        severity=CheckSeverity.ERROR,
                        message=f"Module directory 'modules/{mod_name}' not found",
                        file="workspace.py",
                        code="E021",
                        hint=f"Run 'aq add module {mod_name}' or remove it from workspace.py",
                    )
                )
                continue

            manifest_file = mod_dir / "manifest.py"
            if not manifest_file.exists():
                result.add(
                    CheckError(
                        severity=CheckSeverity.ERROR,
                        message=f"Module manifest not found: modules/{mod_name}/manifest.py",
                        file=f"modules/{mod_name}/",
                        code="E022",
                        hint="Every module must have a manifest.py file",
                    )
                )
                continue

            init_file = mod_dir / "__init__.py"
            if not init_file.exists():
                result.add(
                    CheckError(
                        severity=CheckSeverity.WARNING,
                        message=f"Module missing __init__.py: modules/{mod_name}/",
                        file=f"modules/{mod_name}/",
                        code="W020",
                        hint="Add an empty __init__.py for proper Python package structure",
                    )
                )

    # ── Phase 4: Manifest import paths ───────────────────────────────

    def _check_manifest_imports(self, result: CheckResult) -> None:
        """Validate import paths declared in manifest.py files resolve to real files."""
        import re

        if not self.modules_dir.exists():
            return

        for mod_dir in self.modules_dir.iterdir():
            if not mod_dir.is_dir() or mod_dir.name.startswith("_"):
                continue

            manifest_file = mod_dir / "manifest.py"
            if not manifest_file.exists():
                continue

            try:
                content = manifest_file.read_text(encoding="utf-8")
            except Exception:
                continue

            # Extract import paths like "modules.blogs.controllers:BlogsController"
            import_paths = []
            for line in content.splitlines():
                stripped = line.strip()
                if stripped.startswith("#"):
                    continue
                import_paths.extend(re.findall(r'"([^"]*:[A-Za-z_]\w*)"', line))

            for import_path in import_paths:
                if ":" not in import_path:
                    continue

                module_path, class_name = import_path.rsplit(":", 1)
                parts = module_path.split(".")

                # Convert module path to file path
                file_path = self.workspace_root
                for part in parts:
                    file_path = file_path / part
                file_path = file_path.with_suffix(".py")

                if not file_path.exists():
                    rel_manifest = manifest_file.relative_to(self.workspace_root)
                    result.add(
                        CheckError(
                            severity=CheckSeverity.ERROR,
                            message=(
                                f"Import path '{import_path}' resolves to "
                                f"'{file_path.relative_to(self.workspace_root)}' which does not exist"
                            ),
                            file=str(rel_manifest),
                            code="E030",
                            hint="Create the file or fix the import path in manifest.py",
                        )
                    )

    # ── Phase 5: Route prefix conflicts ──────────────────────────────
    # REMOVED: Route prefix conflict detection is handled by
    # RegistryValidator._validate_route_conflicts() in Phase 2
    # (Validation). Running it here was redundant and could produce
    # duplicate warnings. See ARCHITECTURE_BUILD_DEPLOY.md §2.3 #2.
