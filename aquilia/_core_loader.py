"""Fail-soft gateway to the native core engine.

This is the **only** module in ``aquilia`` that imports :mod:`aquilia._core`.
Everything else imports from here, so a missing, stale, or ABI-mismatched
extension degrades to pure Python instead of breaking the import graph.

The native module has zero ``aquilia.*`` imports by construction: it is a
dependency of the framework, never a dependent. That keeps it outside the
package's import cycle (see ``docs/engine/01-architecture-audit.md`` §6).

Disabling the engine
--------------------
Set ``AQUILIA_ENGINE=0`` to force the pure-Python path. Used by the CI parity
job, which runs the entire suite with the engine off to prove the native layer
is removable at any time.

Usage::

    from aquilia._core_loader import NATIVE, Router

    if NATIVE:
        ...  # native fast path
"""

from __future__ import annotations

import os
from typing import Any

__all__ = [
    "NATIVE",
    "DEFER",
    "ParamKind",
    "RequestContext",
    "Router",
    "engine_info",
]


def _engine_enabled() -> bool:
    """False when ``AQUILIA_ENGINE`` is set to a falsey value."""
    return os.environ.get("AQUILIA_ENGINE", "1").strip().lower() not in {
        "0",
        "false",
        "no",
        "off",
    }


NATIVE: bool = False
"""True when the native engine loaded and is enabled."""

_LOAD_ERROR: str | None = None

Router: Any = None
RequestContext: Any = None
ParamKind: Any = None
DEFER: Any = None

if _engine_enabled():
    try:
        from aquilia._core import (  # type: ignore[import-not-found]
            DEFER,
            ParamKind,
            RequestContext,
            Router,
        )

        NATIVE = True
    except ImportError as exc:  # pragma: no cover - depends on build environment
        # Extension absent (pure-Python install), built for a different Python
        # minor version, or built for a different architecture. All three are
        # legitimate and all three fall back.
        _LOAD_ERROR = str(exc)
else:
    _LOAD_ERROR = "disabled via AQUILIA_ENGINE"


def engine_info() -> dict[str, Any]:
    """Diagnostics for ``aq inspect`` and bug reports.

    Returns the load state, the reason when inactive, and the extension path.
    """
    info: dict[str, Any] = {"native": NATIVE, "reason": _LOAD_ERROR}
    if NATIVE:
        try:
            from aquilia import _core  # type: ignore[import-not-found]

            info["module"] = getattr(_core, "__file__", None)
        except ImportError:  # pragma: no cover - NATIVE implies importable
            pass
    return info
