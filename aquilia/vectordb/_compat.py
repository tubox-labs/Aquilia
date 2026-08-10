"""
AquilaVectorDB — elips import shim and exception mapping.

Two jobs, both about keeping the optional dependency genuinely optional:

1. :func:`require_elips` imports ``elips`` on first use and turns a missing
   package into :class:`VectorNotInstalledFault` instead of a
   ``ModuleNotFoundError`` raised several frames into a query.
2. :func:`translate` maps native ``elips`` exceptions onto the vectordb fault
   taxonomy, so callers only ever catch ``VectorFault`` subclasses and no elips
   type leaks across the framework boundary.

Every elips exception derives from ``ElipsError`` (itself a ``RuntimeError``),
so the mapping is by concrete class with an ``ElipsError`` catch-all — an elips
release that adds a subclass degrades to :class:`VectorStoreFault` rather than
escaping untranslated.
"""

from __future__ import annotations

from typing import Any

from aquilia.vectordb.faults import (
    VectorConfigFault,
    VectorDimensionFault,
    VectorFault,
    VectorLockFault,
    VectorNotFoundFault,
    VectorNotInstalledFault,
    VectorStoreFault,
)

_elips_module: Any | None = None


def require_elips() -> Any:
    """
    Import and return the ``elips`` module.

    Returns:
        The imported ``elips`` module.

    Raises:
        VectorNotInstalledFault: When ``elips`` is not installed.
    """
    global _elips_module
    if _elips_module is not None:
        return _elips_module

    try:
        import elips
    except ImportError as exc:
        raise VectorNotInstalledFault(reason=str(exc)) from exc

    _elips_module = elips
    return elips


def is_available() -> bool:
    """Return whether ``elips`` can be imported, without raising."""
    try:
        require_elips()
    except VectorNotInstalledFault:
        return False
    return True


def translate(
    exc: BaseException,
    *,
    store: str = "",
    operation: str = "",
    context: str = "",
) -> VectorFault:
    """
    Map a native elips exception onto a vectordb fault.

    Args:
        exc: The caught exception.
        store: Store alias for context.
        operation: Operation being attempted, e.g. ``"write"``.
        context: Extra detail, e.g. the collection name.

    Returns:
        The corresponding :class:`VectorFault`. A fault passed in is returned
        unchanged, so wrapping an already-translated error is a no-op and
        nesting ``translate`` calls is safe.
    """
    if isinstance(exc, VectorFault):
        return exc

    try:
        elips = require_elips()
    except VectorNotInstalledFault as fault:
        return fault

    name = type(exc).__name__
    message = str(exc)

    lock_conflict = getattr(elips, "LockConflict", None)
    if lock_conflict is not None and isinstance(exc, lock_conflict):
        return VectorLockFault(path=store or context, reason=message)

    dim_mismatch = getattr(elips, "DimensionMismatch", None)
    if dim_mismatch is not None and isinstance(exc, dim_mismatch):
        expected, actual = _parse_dimensions(message)
        return VectorDimensionFault(expected=expected, actual=actual, context=context or store)

    not_found = getattr(elips, "NotFound", None)
    if not_found is not None and isinstance(exc, not_found):
        return VectorNotFoundFault(model=context or store or "record")

    config_error = getattr(elips, "ConfigError", None)
    if config_error is not None and isinstance(exc, config_error):
        return VectorConfigFault(reason=message, store=store)

    invalid_vector = getattr(elips, "InvalidVector", None)
    if invalid_vector is not None and isinstance(exc, invalid_vector):
        return VectorConfigFault(reason=f"invalid vector: {message}", store=store)

    parse_error = getattr(elips, "ParseError", None)
    if parse_error is not None and isinstance(exc, parse_error):
        return VectorConfigFault(reason=f"parse error: {message}", store=store)

    gpu_error = getattr(elips, "GpuError", None)
    if gpu_error is not None and isinstance(exc, gpu_error):
        from aquilia.vectordb.faults import VectorGpuUnavailableFault

        return VectorGpuUnavailableFault(reason=message, policy="gpu")

    # StorageError and any future ElipsError subclass.
    return VectorStoreFault(
        store=store or context or "vectordb",
        operation=operation or "operation",
        reason=f"{name}: {message}" if name != "StorageError" else message,
    )


def _parse_dimensions(message: str) -> tuple[int, int]:
    """
    Best-effort extraction of the expected/actual pair from a mismatch message.

    Falls back to ``(0, 0)`` when the text does not carry two integers; the
    fault is still correctly typed, just without the numbers, which beats
    failing inside error handling.
    """
    import re

    numbers = [int(n) for n in re.findall(r"\d+", message)]
    if len(numbers) >= 2:
        return numbers[0], numbers[1]
    return 0, 0


__all__ = ["is_available", "require_elips", "translate"]
