"""Rendering for check results: human and JSON.

Checks never print -- they yield findings. Rendering lives here so human
output, ``--json`` for CI, and test assertions all consume the same data.
"""

from __future__ import annotations

import json
from collections.abc import Iterable

from aquilia.cli.checks.base import CheckResult
from aquilia.cli.core.exits import ExitCode, exit_code_for, max_severity, severity_rank
from aquilia.faults.core import Severity

__all__ = ["render_human", "render_json", "summarise", "result_exit_code"]

_MARK = {
    Severity.INFO: "i",
    Severity.WARN: "!",
    Severity.ERROR: "x",
    Severity.FATAL: "X",
}


def summarise(results: Iterable[CheckResult]) -> dict:
    """Aggregate counts by severity, plus totals."""
    results = list(results)
    counts = {s.value: 0 for s in (Severity.INFO, Severity.WARN, Severity.ERROR, Severity.FATAL)}
    for res in results:
        for finding in res.findings:
            counts[finding.severity.value] = counts.get(finding.severity.value, 0) + 1
    errored = [r for r in results if r.error]
    return {
        "checks_run": len([r for r in results if not r.skipped]),
        "checks_skipped": len([r for r in results if r.skipped]),
        "checks_errored": len(errored),
        "findings": counts,
        "total_findings": sum(counts.values()),
        "passed": all(r.ok for r in results),
    }


def result_exit_code(results: Iterable[CheckResult]) -> ExitCode:
    """Worst severity across all results becomes the exit code."""
    severities: list[Severity] = []
    for res in results:
        severities.extend(res.severities)
    return exit_code_for(severities)


def render_human(results: Iterable[CheckResult], *, verbose: bool = False) -> str:
    """Human-readable report.

    Unlike the old ``doctor``, warnings are shown by default. Hiding computed
    warnings behind ``-v`` is what let a broken workspace look healthy.
    """
    results = list(results)
    lines: list[str] = []
    summary = summarise(results)

    for res in results:
        if res.skipped:
            if verbose:
                lines.append(f"  -  {res.check.name}: skipped ({res.skip_reason})")
            continue
        if res.error:
            lines.append(f"  x  {res.check.name}: check itself failed -- {res.error}")
            continue
        if not res.findings:
            if verbose:
                lines.append(f"  ok {res.check.name}")
            continue
        for finding in sorted(res.findings, key=lambda f: -severity_rank(f.severity)):
            mark = _MARK.get(finding.severity, "?")
            lines.append(f"  {mark}  [{finding.code}] {finding.message}")
            if finding.location:
                lines.append(f"        at: {finding.location}")
            if finding.remedy:
                lines.append(f"        fix: {finding.remedy}")
            if verbose and finding.detail:
                lines.append(f"        {finding.detail}")

    counts = summary["findings"]
    if summary["total_findings"] == 0 and not summary["checks_errored"]:
        lines.append("")
        lines.append(f"  All {summary['checks_run']} checks passed.")
    else:
        lines.append("")
        parts = [
            f"{counts[s.value]} {s.value}"
            for s in (Severity.FATAL, Severity.ERROR, Severity.WARN, Severity.INFO)
            if counts.get(s.value)
        ]
        lines.append(f"  {summary['checks_run']} checks run: " + ", ".join(parts))
        worst = max_severity(
            [f.severity for r in results for f in r.findings] + ([Severity.ERROR] if summary["checks_errored"] else [])
        )
        if worst and severity_rank(worst) >= severity_rank(Severity.ERROR):
            lines.append("  Result: FAILED")
        else:
            lines.append("  Result: passed with warnings")

    return "\n".join(lines)


def render_json(results: Iterable[CheckResult]) -> str:
    """Machine-readable report for CI."""
    results = list(results)
    payload = {
        "summary": summarise(results),
        "exit_code": int(result_exit_code(results)),
        "checks": [
            {
                "name": r.check.name,
                "summary": r.check.summary,
                "subsystem": r.check.subsystem,
                "tags": list(r.check.tags),
                "skipped": r.skipped,
                "skip_reason": r.skip_reason,
                "error": r.error,
                "findings": [f.to_dict() for f in r.findings],
            }
            for r in results
        ],
    }
    return json.dumps(payload, indent=2)
