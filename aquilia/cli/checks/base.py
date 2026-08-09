"""The check protocol and registry.

One ``Check`` abstraction replaces the divergent implementations in
``doctor.py`` (597 lines) and ``validate.py`` (372 lines), which had drifted
apart while nominally answering the same question. ``doctor`` and ``validate``
become two *selections* over this registry.

Findings carry a severity, and the worst severity determines the exit code, so
a computed warning can no longer render as a green "healthy" banner.
"""

from __future__ import annotations

from collections.abc import Callable, Iterable
from dataclasses import dataclass, field

from aquilia.cli.core.context import AqContext
from aquilia.faults.core import Severity

__all__ = [
    "Finding",
    "Check",
    "CheckResult",
    "register_check",
    "all_checks",
    "checks_for",
    "run_checks",
]


@dataclass
class Finding:
    """One observation about the workspace.

    ``code`` is a stable identifier (``AQ_DB_MISSING``) suitable for
    documentation, ``--explain``, and CI allowlists.
    """

    code: str
    message: str
    severity: Severity = Severity.ERROR
    remedy: str | None = None
    location: str | None = None
    detail: str | None = None

    @property
    def is_failure(self) -> bool:
        return self.severity in (Severity.ERROR, Severity.FATAL)

    def to_dict(self) -> dict:
        return {
            "code": self.code,
            "message": self.message,
            "severity": self.severity.value,
            "remedy": self.remedy,
            "location": self.location,
            "detail": self.detail,
        }


@dataclass
class Check:
    """A named, tagged workspace check.

    ``run`` receives the ``AqContext`` and yields ``Finding`` objects. Yielding
    nothing means "passed" -- checks never print, so the same check serves
    human, JSON, and test output.
    """

    name: str
    summary: str
    run: Callable[[AqContext], Iterable[Finding]]
    tags: tuple[str, ...] = ()
    subsystem: str = "core"
    requires_workspace: bool = True

    def __call__(self, ctx: AqContext) -> list[Finding]:
        return list(self.run(ctx))


@dataclass
class CheckResult:
    """Outcome of running one check."""

    check: Check
    findings: list[Finding] = field(default_factory=list)
    error: str | None = None
    skipped: bool = False
    skip_reason: str | None = None

    @property
    def ok(self) -> bool:
        return not self.error and not any(f.is_failure for f in self.findings)

    @property
    def severities(self) -> list[Severity]:
        sev = [f.severity for f in self.findings]
        if self.error:
            sev.append(Severity.ERROR)
        return sev


_REGISTRY: dict[str, Check] = {}


def register_check(
    name: str,
    summary: str,
    *,
    tags: Iterable[str] = (),
    subsystem: str = "core",
    requires_workspace: bool = True,
) -> Callable:
    """Decorator registering a generator function as a check.

    ::

        @register_check("db.migrations", "Migrations applied", tags=["db"])
        def check_migrations(ctx):
            if pending:
                yield Finding("AQ_DB_PENDING", "...", Severity.WARN)
    """

    def decorator(fn: Callable[[AqContext], Iterable[Finding]]) -> Callable:
        _REGISTRY[name] = Check(
            name=name,
            summary=summary,
            run=fn,
            tags=tuple(tags),
            subsystem=subsystem,
            requires_workspace=requires_workspace,
        )
        return fn

    return decorator


def all_checks() -> list[Check]:
    """Every registered check, ordered by name for stable output."""
    _load_builtin_checks()
    return [_REGISTRY[k] for k in sorted(_REGISTRY)]


def checks_for(
    tags: Iterable[str] | None = None,
    subsystems: Iterable[str] | None = None,
) -> list[Check]:
    """Checks matching any given tag and any given subsystem."""
    tagset = set(tags or ())
    subs = set(subsystems or ())
    out = []
    for check in all_checks():
        if tagset and not (tagset & set(check.tags)):
            continue
        if subs and check.subsystem not in subs:
            continue
        out.append(check)
    return out


def run_checks(ctx: AqContext, checks: Iterable[Check]) -> list[CheckResult]:
    """Run checks, isolating failures.

    A check that raises is reported as a failed check rather than crashing the
    command -- one broken probe must not hide the other twenty results.
    """
    results: list[CheckResult] = []
    has_workspace = ctx.workspace.exists

    for check in checks:
        if check.requires_workspace and not has_workspace:
            results.append(
                CheckResult(
                    check=check,
                    skipped=True,
                    skip_reason="no workspace in current directory",
                )
            )
            continue
        try:
            results.append(CheckResult(check=check, findings=list(check.run(ctx))))
        except Exception as exc:  # noqa: BLE001 - isolation is the point
            results.append(CheckResult(check=check, error=f"{type(exc).__name__}: {exc}"))
    return results


def _load_builtin_checks() -> None:
    """Import built-in check modules so their decorators register.

    Kept lazy to avoid import cycles and to keep ``aq --help`` fast.
    """
    global _LOADED
    if _LOADED:
        return
    _LOADED = True
    from aquilia.cli.checks import subsystems, workspace  # noqa: F401


_LOADED = False
