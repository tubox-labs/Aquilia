"""``aq contracts`` -- developer tooling for the Contracts subsystem."""

from __future__ import annotations

import importlib
import sys
from pathlib import Path

import click

from aquilia.cli.utils.colors import _CHECK, _CROSS, dim, error, info, success, warning
from aquilia.contracts.stubs import write_module_stub


@click.group("contracts")
def contracts_group() -> None:
    """Inspect and generate artifacts for Aquilia Contracts."""


@contracts_group.command("stubs")
@click.argument("modules", nargs=-1, required=True)
@click.option(
    "--check",
    is_flag=True,
    help="Do not write; exit non-zero if any stub is missing or out of date.",
)
@click.option(
    "--path",
    "search_path",
    default=".",
    help="Directory prepended to sys.path before importing (default: current directory).",
)
def contracts_stubs(modules: tuple[str, ...], check: bool, search_path: str) -> None:
    """
    Emit .pyi stubs so type checkers can see Contract fields.

    A Contract builds its fields at class-body evaluation time and serves them
    through __getattr__, both of which are invisible to mypy and pyright. This
    writes a .pyi next to each named module declaring every field with the type
    its facet produces, which any type checker consumes without a plugin.

    Commit the generated files, then keep them honest in CI with --check.

    \b
    Examples:
    ```
        aq contracts stubs myapp.contracts
        aq contracts stubs myapp.users.contracts myapp.orders.contracts
        aq contracts stubs myapp.contracts --check
    ```
    """
    root = str(Path(search_path).resolve())
    if root not in sys.path:
        sys.path.insert(0, root)

    stale: list[str] = []
    failed: list[str] = []

    for name in modules:
        try:
            module = importlib.import_module(name)
        except Exception as exc:
            error(f"  {_CROSS} {name}: import failed -- {exc}")
            failed.append(name)
            continue

        try:
            report = write_module_stub(module, dry_run=check)
        except Exception as exc:
            error(f"  {_CROSS} {name}: {exc}")
            failed.append(name)
            continue

        if check:
            if report.is_current:
                success(f"  {_CHECK} {name}: {report.path.name} up to date")
            else:
                error(f"  {_CROSS} {name}: {report.path.name} is missing or out of date")
                stale.append(name)
        else:
            success(f"  {_CHECK} {name}: wrote {report.path}")

        if report.contracts:
            info(f"      {len(report.contracts)} contract(s): {', '.join(report.contracts)}")
        for note in report.degraded:
            warning(f"      {note}")

    if failed:
        sys.exit(1)
    if stale:
        error("")
        error("  Stubs are out of date. Regenerate with:")
        dim(f"      aq contracts stubs {' '.join(stale)}")
        sys.exit(1)
