"""Exit codes and severity ranking for the Aquilia CLI.

Single source of truth for how a check result becomes a process exit code.
Before this module, commands printed banners and returned 0 unconditionally,
so a workspace with a missing database reported "healthy".

``Severity`` is reused from ``aquilia.faults`` (a ``str`` Enum, therefore
unordered). ``severity_rank`` supplies the ordering the exit mapping needs.
"""

from __future__ import annotations

from enum import IntEnum

from aquilia.faults.core import Severity

__all__ = [
    "ExitCode",
    "SEVERITY_ORDER",
    "exit_code_for",
    "max_severity",
    "severity_rank",
]


class ExitCode(IntEnum):
    """Process exit codes.

    Stable contract -- CI pipelines and tests depend on these values.
    """

    OK = 0
    """No findings above WARN."""

    FAILED = 1
    """At least one ERROR/FATAL finding: the workspace is broken."""

    USAGE = 2
    """Bad invocation (Click's own convention for argument errors)."""

    CONFIG = 3
    """Workspace or configuration could not be loaded at all."""

    INTERNAL = 4
    """Unexpected CLI failure -- a bug in the CLI itself."""


SEVERITY_ORDER: dict[Severity, int] = {
    Severity.INFO: 0,
    Severity.WARN: 1,
    Severity.ERROR: 2,
    Severity.FATAL: 3,
}


def severity_rank(severity: Severity | str) -> int:
    """Return the sortable rank of a severity.

    Accepts a ``Severity`` or its string value so callers can pass either
    without normalising first.
    """
    if isinstance(severity, str) and not isinstance(severity, Severity):
        try:
            severity = Severity(severity)
        except ValueError:
            return 0
    return SEVERITY_ORDER.get(severity, 0)


def max_severity(severities) -> Severity | None:
    """Highest severity in an iterable, or ``None`` when empty."""
    ranked = [(severity_rank(s), s) for s in severities]
    if not ranked:
        return None
    return max(ranked, key=lambda pair: pair[0])[1]


def exit_code_for(severities) -> ExitCode:
    """Map a collection of severities to an exit code.

    ERROR and FATAL fail the command; INFO and WARN do not. Warnings stay
    visible in output but do not break a build -- that distinction is the
    whole point of having severities.
    """
    worst = max_severity(severities)
    if worst is None:
        return ExitCode.OK
    return ExitCode.FAILED if severity_rank(worst) >= SEVERITY_ORDER[Severity.ERROR] else ExitCode.OK
