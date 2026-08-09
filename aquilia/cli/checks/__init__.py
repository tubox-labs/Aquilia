"""Workspace check engine.

``doctor`` and ``validate`` are two selections over one registry, replacing
the previously divergent implementations.
"""

from aquilia.cli.checks.base import (
    Check,
    CheckResult,
    Finding,
    all_checks,
    checks_for,
    register_check,
    run_checks,
)

__all__ = [
    "Check",
    "CheckResult",
    "Finding",
    "all_checks",
    "checks_for",
    "register_check",
    "run_checks",
]
