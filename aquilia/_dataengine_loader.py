"""Fail-soft gateway to the native data engine.

This is the **only** module in ``aquilia`` that imports :mod:`aquilia._dataengine`.
Everything else imports from here, so a missing, stale, or ABI-mismatched
extension degrades to pure Python instead of breaking the import graph.

The native module has zero ``aquilia.*`` imports by construction: it is a
dependency of the framework, never a dependent. That keeps it outside the
package's import cycle (see ``docs/models-engine/01-architecture-audit.md`` §10).

Relationship to :mod:`aquilia._core_loader`
-------------------------------------------
Deliberately independent. ``_core`` is the *request* path (router, request
context) and is exercised on every request; this is the *data* path (row and
field plans) and is exercised only when an app touches the ORM or contracts.
Separate loaders, separate env vars, separate CI gates -- neither can break the
other, and either can be disabled alone.

Disabling the engine
--------------------
Set ``AQUILIA_DATAENGINE=0`` to force the pure-Python path. Used by the CI
parity job, which runs the entire suite with the engine off to prove the native
layer is removable at any time.

Usage::

    from aquilia._dataengine_loader import DATAENGINE_NATIVE

    if DATAENGINE_NATIVE:
        ...  # native fast path
"""

from __future__ import annotations

import os
from typing import Any

__all__ = [
    "DATAENGINE_NATIVE",
    "dataengine_info",
    "native_module",
]


def _dataengine_enabled() -> bool:
    """False when ``AQUILIA_DATAENGINE`` is set to a falsey value."""
    return os.environ.get("AQUILIA_DATAENGINE", "1").strip().lower() not in {
        "0",
        "false",
        "no",
        "off",
    }


DATAENGINE_NATIVE: bool = False
"""True when the native data engine loaded and is enabled."""

_LOAD_ERROR: str | None = None

_dataengine: Any = None

if _dataengine_enabled():
    try:
        from aquilia import _dataengine as _dataengine_mod  # type: ignore[attr-defined]

        _dataengine = _dataengine_mod
        DATAENGINE_NATIVE = True
    except (ImportError, AttributeError) as exc:  # pragma: no cover - depends on build environment
        # Extension absent (pure-Python install), built for a different Python
        # minor version, or built for a different architecture. All three are
        # legitimate and all three fall back.
        _LOAD_ERROR = str(exc)
else:
    _LOAD_ERROR = "disabled via AQUILIA_DATAENGINE"


def native_module() -> Any:
    """The native extension itself, or None when it is absent or disabled.

    The plan compilers need the module's ``FieldPlan``/``TypeCode`` attributes.
    Handing them the module keeps this loader the single import site, so no
    other part of ``aquilia`` ever names :mod:`aquilia._dataengine` directly.
    """
    return _dataengine


def dataengine_info() -> dict[str, Any]:
    """Diagnostics for ``aq inspect`` and bug reports.

    Returns the load state, the reason when inactive, and the extension path.
    """
    info: dict[str, Any] = {"native": DATAENGINE_NATIVE, "reason": _LOAD_ERROR}
    if DATAENGINE_NATIVE and _dataengine is not None:
        info["module"] = getattr(_dataengine, "__file__", None)
    return info
