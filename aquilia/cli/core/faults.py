"""CLI fault domain.

Per ``CLAUDE.md``: framework-domain errors use ``Fault`` subclasses with a
stable ``code``, ``message``, ``domain`` and ``severity`` -- never raw
``ValueError``/``RuntimeError``.

These replace the ~150 scattered ``sys.exit(1)`` calls in command bodies.
A command that raises instead of exiting can be unit-tested as a plain
function; ``main.py`` maps the fault to an exit code at the boundary.
"""

from __future__ import annotations

from aquilia.faults.core import Fault, FaultDomain, Severity

__all__ = [
    "CLI_DOMAIN",
    "CliFault",
    "WorkspaceNotFoundFault",
    "WorkspaceLoadFault",
    "ModuleNotFoundFault",
    "CheckFailedFault",
]

CLI_DOMAIN = FaultDomain.custom("CLI", "Aquilia command-line interface faults")


class CliFault(Fault):
    """Base class for CLI faults."""

    code = "CLI_ERROR"
    message = "CLI operation failed"
    domain = CLI_DOMAIN
    severity = Severity.ERROR


class WorkspaceNotFoundFault(CliFault):
    """No workspace.py / aquilia.py found."""

    code = "CLI_WORKSPACE_NOT_FOUND"
    message = "No Aquilia workspace found in the current directory"
    severity = Severity.ERROR

    def __init__(self, path: str | None = None, **kwargs):
        detail = f"No workspace.py or aquilia.py found in {path}" if path else self.message
        super().__init__(message=detail, path=path, **kwargs)


class WorkspaceLoadFault(CliFault):
    """workspace.py exists but could not be imported."""

    code = "CLI_WORKSPACE_LOAD_FAILED"
    message = "Workspace could not be loaded"
    severity = Severity.ERROR

    def __init__(self, path: str | None = None, reason: str | None = None, **kwargs):
        detail = f"Failed to load workspace at {path}: {reason}" if path else self.message
        super().__init__(message=detail, path=path, reason=reason, **kwargs)


class ModuleNotFoundFault(CliFault):
    """A named module is not present in the workspace."""

    code = "CLI_MODULE_NOT_FOUND"
    message = "Module not found in workspace"
    severity = Severity.ERROR

    def __init__(self, module: str | None = None, **kwargs):
        detail = f"Module '{module}' not found in this workspace" if module else self.message
        super().__init__(message=detail, module=module, **kwargs)


class CheckFailedFault(CliFault):
    """A health check run produced ERROR/FATAL findings."""

    code = "CLI_CHECK_FAILED"
    message = "One or more checks failed"
    severity = Severity.ERROR
