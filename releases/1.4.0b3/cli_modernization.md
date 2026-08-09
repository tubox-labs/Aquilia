# CLI Architecture Modernization — v1.4.0b3

## Overview & Motivation

In previous releases, the Aquilia CLI (`aq`) contained significant structural debt:
1. **Inconsistent Exit Codes**: Commands printed warning/error banners but returned exit code `0` unconditionally. Continuous integration pipelines were unable to rely on `aq validate` or `aq doctor` to fail broken builds.
2. **Scattered Error Exit Calls**: ~150 scattered `sys.exit(1)` invocations were hardcoded into command bodies, making CLI logic impossible to unit test without process termination.
3. **Competing Workspace Guards**: Three different functions (`_ensure_workspace_root`, `_require_workspace`, and `ConfigMissingFault`) checked for `workspace.py` using different rules and error messages.
4. **Brittle Regex Workspace Parsing**: `workspace.py` and `manifest.py` were parsed using regular expressions (e.g. `re.findall(r'Module\("([^"]+)"')`), missing commented-out modules, ignoring `.starter("name")` starter routes, and ignoring module-level `route_prefix` settings.
5. **Help Category Drift**: `AquiliaGroup._CATEGORIES` relied on a manually maintained literal list of command strings. Commands like `deploy-gen` vs `deploy` caused 7 core commands to silently fall into the "Other" category in `aq --help`.

v1.4.0b3 replaces this legacy implementation with a modular architecture under `aquilia.cli.core`.

---

## The `aquilia.cli.core` Package

```
aquilia/cli/core/
├── __init__.py        # Re-exports core primitives
├── exits.py           # ExitCode enum, SEVERITY_ORDER, exit_code_for()
├── faults.py          # CLI_DOMAIN and CliFault hierarchy
├── context.py         # AqContext ambient state thread
├── workspace.py       # LoadedWorkspace, load_workspace(), Python-first loader
└── registry.py        # CommandSpec, CATEGORY_ORDER, single source of help grouping
```

---

## 1. Single Source of Truth for Exit Codes (`exits.py`)

`ExitCode` establishes a strict contract for process return values:

```python
from enum import IntEnum

class ExitCode(IntEnum):
    OK = 0          # All checks passed / findings <= WARN
    FAILED = 1      # At least one ERROR or FATAL finding
    USAGE = 2       # Command line argument/invocation error
    CONFIG = 3      # Workspace or configuration file missing / load failure
    INTERNAL = 4    # Unhandled CLI exception (bug in CLI engine)
```

### Severity Mapping

Check severities (`INFO`, `WARN`, `ERROR`, `FATAL`) map deterministically to process exit codes:

```python
from aquilia.cli.core.exits import exit_code_for
from aquilia.faults.core import Severity

# Only ERROR and FATAL cause process failure (ExitCode.FAILED / 1)
exit_code_for([Severity.INFO, Severity.WARN])  # -> ExitCode.OK (0)
exit_code_for([Severity.WARN, Severity.ERROR]) # -> ExitCode.FAILED (1)
```

---

## 2. Structured CLI Fault Hierarchy (`faults.py`)

Instead of invoking `sys.exit(1)` inside command handlers, commands raise typed subclasses of `CliFault`. The CLI entrypoint (`cli`) catches faults at the process boundary and converts them to exit codes.

```python
from aquilia.cli.core.faults import CliFault, WorkspaceNotFoundFault
from aquilia.faults.core import FaultDomain, Severity

CLI_DOMAIN = FaultDomain.custom("CLI", "Aquilia command-line interface faults")

class CliFault(Fault):
    code = "CLI_ERROR"
    message = "CLI operation failed"
    domain = CLI_DOMAIN
    severity = Severity.ERROR

class WorkspaceNotFoundFault(CliFault):
    code = "CLI_WORKSPACE_NOT_FOUND"
    message = "No Aquilia workspace found in the current directory"
    severity = Severity.ERROR
```

### Benefit for Testing

Commands can now be tested as normal Python functions without mocking `sys.exit()`:

```python
# Unit test example
import pytest
from aquilia.cli.core.faults import WorkspaceNotFoundFault

def test_require_workspace_raises_fault(tmp_path):
    ctx = AqContext(cwd=tmp_path)
    with pytest.raises(WorkspaceNotFoundFault):
        ctx.require_workspace()
```

---

## 3. Ambient CLI State (`AqContext`)

`AqContext` replaces ad-hoc `ctx.obj` dictionary access. The workspace is resolved lazily upon first access:

```python
from dataclasses import dataclass, field
from pathlib import Path
from aquilia.cli.core.workspace import LoadedWorkspace, load_workspace

@dataclass
class AqContext:
    cwd: Path = field(default_factory=Path.cwd)
    verbose: bool = False
    quiet: bool = False
    json_output: bool = False
    no_color: bool = False
    strict: bool = False
    module_filter: str | None = None
    mode: str = field(default_factory=lambda: os.environ.get("AQUILIA_ENV", "dev"))
    _workspace: LoadedWorkspace | None = field(default=None, repr=False)

    @property
    def workspace(self) -> LoadedWorkspace:
        if self._workspace is None:
            self._workspace = load_workspace(self.cwd)
        return self._workspace

    def require_workspace(self) -> LoadedWorkspace:
        ws = self.workspace
        if not ws.exists:
            raise WorkspaceNotFoundFault(path=str(self.cwd))
        return ws
```

---

## 4. Python-First Workspace Loader (`workspace.py`)

`workspace.py` is a Python module, so `load_workspace()` imports it cleanly via `importlib` instead of scraping source text with regular expressions.

```python
from aquilia.cli.core.workspace import load_workspace

ws = load_workspace(Path.cwd())
print(f"Root: {ws.root}")
print(f"Modules: {ws.module_names}")
print(f"Starter Controller: {ws.starter_module}")

# Manifest resolution with caching
manifest = ws.manifest("users")
print(f"Controllers: {manifest.controllers}")
```

### Regex Fallback Mechanism

If `workspace.py` contains syntax or import errors, `load_workspace()` falls back to a non-evaluating regex scan and sets `ws.used_fallback = True`. This allows `aq doctor` to inspect and report on a broken workspace rather than failing immediately.

---

## 5. Category-Driven Command Registry (`registry.py`)

Command categories are maintained in a single registry mapping command names to display categories in `aq --help`:

```python
CATEGORY_ORDER = (
    "Scaffold", "Develop", "Production", "Database",
    "Admin", "Inspect", "Subsystems", "Deploy",
    "Migration", "Other"
)

# Single source of truth for aq --help
_CATEGORIES = {
    "init": "Scaffold", "add": "Scaffold", "generate": "Scaffold",
    "run": "Develop", "dev": "Develop", "validate": "Develop",
    "test": "Develop", "discover": "Develop", "doctor": "Develop",
    "serve": "Production", "db": "Database", "admin": "Admin",
    "inspect": "Inspect", "manifest": "Inspect", "ws": "Subsystems",
    "cache": "Subsystems", "mail": "Subsystems", "deploy": "Deploy",
    "migrate": "Migration",
}
```

Help integrity tests enforce that every registered Click command maps to a category, preventing unassigned commands from drifting into "Other".
