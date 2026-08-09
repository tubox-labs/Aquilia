"""Core CLI infrastructure: context, workspace loading, exit codes, faults.

Imported by commands and checks. Contains no command definitions, so it is
safe to import from anywhere in the CLI without circularity.
"""

from aquilia.cli.core.context import AqContext
from aquilia.cli.core.exits import (
    SEVERITY_ORDER,
    ExitCode,
    exit_code_for,
    max_severity,
    severity_rank,
)
from aquilia.cli.core.faults import (
    CLI_DOMAIN,
    CheckFailedFault,
    CliFault,
    ModuleNotFoundFault,
    WorkspaceLoadFault,
    WorkspaceNotFoundFault,
)
from aquilia.cli.core.workspace import (
    LoadedWorkspace,
    ensure_importable,
    load_manifest,
    load_module_file,
    load_workspace,
)

__all__ = [
    "AqContext",
    "CLI_DOMAIN",
    "CheckFailedFault",
    "CliFault",
    "ExitCode",
    "LoadedWorkspace",
    "ModuleNotFoundFault",
    "SEVERITY_ORDER",
    "WorkspaceLoadFault",
    "WorkspaceNotFoundFault",
    "ensure_importable",
    "exit_code_for",
    "load_manifest",
    "load_module_file",
    "load_workspace",
    "max_severity",
    "severity_rank",
]
