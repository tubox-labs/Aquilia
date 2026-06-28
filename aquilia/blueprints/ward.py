"""
Aquilia Blueprint Ward -- explicit cross-field validator registration.

Replaces the fragile seal_*/async_seal_* name-prefix scanning with
explicit @ward decorator registration, discovered once at class-body
evaluation time.

Usage::

    from aquilia.blueprints import ward

    class OrderBlueprint(Blueprint):
        @ward
        def total_matches_items(self, data):
            computed = sum(i.price * i.qty for i in data.items)
            if abs(computed - data.total) > 0.01:
                self.reject("total", f"Expected {computed}, got {data.total}")

        @ward(mode="async")
        async def discount_code_valid(self, data):
            if data.discount_code and not await lookup(data.discount_code):
                self.reject("discount_code", "Unknown code")
"""

from __future__ import annotations

import inspect
import warnings
from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

__all__ = ["ward", "WardMethod", "collect_ward_methods"]


# ---------------------------------------------------------------------------
# WardMethod
# ---------------------------------------------------------------------------


@dataclass(frozen=True, slots=True)
class WardMethod:
    """Descriptor for a single cross-field validator registered on a Blueprint."""

    name: str
    fn: object  # the callable
    mode: str  # "sync" or "async"


# ---------------------------------------------------------------------------
# @ward decorator
# ---------------------------------------------------------------------------

_VALID_MODES = frozenset({"sync", "async"})


class ward:
    """Decorator (and decorator-factory) for registering Blueprint ward methods.

    Supports two usage patterns:

    * **Bare decorator** — ``@ward`` attaches sync metadata::

          @ward
          def my_validator(self, data): ...

    * **Parameterised decorator** — ``@ward(mode="async")``::

          @ward(mode="async")
          async def my_async_validator(self, data): ...

    In both cases the decorated function receives a ``__ward_meta__`` dict
    with keys ``"mode"`` and ``"name"``.
    """

    # Use __new__ so that ``ward(fn)`` (bare) returns the decorated *fn*
    # directly, while ``ward(mode=...)`` returns a *ward* instance whose
    # ``__call__`` acts as the real decorator.

    def __new__(cls, fn: Callable[..., Any] | None = None, *, mode: str = "sync") -> Any:  # noqa: ANN401
        if mode not in _VALID_MODES:
            raise ValueError(f"Invalid ward mode {mode!r}; expected one of {sorted(_VALID_MODES)}")

        if fn is not None:
            # Bare usage: @ward  (fn is the decorated method)
            if not callable(fn):
                raise TypeError(f"@ward expects a callable, got {type(fn).__name__}")
            fn.__ward_meta__ = {"mode": mode, "name": fn.__name__}  # type: ignore[attr-defined]
            return fn  # type: ignore[return-value]

        # Factory usage: @ward(mode="async") — return a real instance whose
        # __call__ will do the attaching.
        instance = super().__new__(cls)
        instance._mode = mode  # type: ignore[attr-defined]
        return instance

    def __init__(self, fn: Callable[..., Any] | None = None, *, mode: str = "sync") -> None:
        # When __new__ returned the decorated fn directly, Python will still
        # call __init__ on it (but `self` will be the fn, not a ward instance).
        # Guard against that by checking the type.
        if not isinstance(self, ward):
            return
        self._mode: str = mode  # already set in __new__, repeated for clarity

    def __call__(self, fn: Callable[..., Any]) -> Callable[..., Any]:
        """Apply the decorator when used as ``@ward(mode=...)``."""
        if not callable(fn):
            raise TypeError(f"@ward(...) expects a callable, got {type(fn).__name__}")
        fn.__ward_meta__ = {"mode": self._mode, "name": fn.__name__}  # type: ignore[attr-defined]
        return fn


# ---------------------------------------------------------------------------
# collect_ward_methods
# ---------------------------------------------------------------------------


def collect_ward_methods(
    name: str,
    bases: tuple[type, ...],
    namespace: dict[str, Any],
) -> list[WardMethod]:
    """Collect all ward methods for a Blueprint class being constructed.

    Called during class-body evaluation (typically from a metaclass or
    ``__init_subclass__`` hook).

    Parameters
    ----------
    name:
        The name of the class being created.
    bases:
        The base classes of the class being created.
    namespace:
        The class namespace (``dict``) produced by executing the class body.

    Returns
    -------
    list[WardMethod]
        Ward methods in stable order: inherited first (preserving MRO /
        definition order), then own methods in definition order.  If a
        subclass defines a ward with the same name as a parent's, the
        subclass version replaces the parent's.
    """

    # 1. Collect inherited wards keyed by name (preserves override semantics).
    inherited: dict[str, WardMethod] = {}
    for base in bases:
        for wm in getattr(base, "_ward_methods", ()):
            inherited[wm.name] = wm

    # 2. Scan namespace for explicit @ward-decorated callables.
    own: dict[str, WardMethod] = {}
    for attr_name, obj in namespace.items():
        if callable(obj) and hasattr(obj, "__ward_meta__"):
            meta: dict[str, str] = obj.__ward_meta__
            own[meta["name"]] = WardMethod(
                name=meta["name"],
                fn=obj,
                mode=meta["mode"],
            )

    # 3. Backward-compat: scan for seal_*/async_seal_* prefix convention.
    # TODO(deprecation): remove seal_*/async_seal_* scanning in next major version
    for attr_name, obj in namespace.items():
        if not callable(obj):
            continue
        if hasattr(obj, "__ward_meta__"):
            continue  # already registered via @ward
        if not (attr_name.startswith("seal_") or attr_name.startswith("async_seal_")):
            continue

        mode = "async" if inspect.iscoroutinefunction(obj) else "sync"
        warnings.warn(
            f"{name}.{attr_name}: seal_*/async_seal_* prefix convention is "
            f"deprecated. Use @ward or @ward(mode='async') instead.",
            DeprecationWarning,
            stacklevel=3,
        )
        own.setdefault(attr_name, WardMethod(name=attr_name, fn=obj, mode=mode))

    # 4. Merge: inherited first, then own (own overrides inherited by key).
    merged: dict[str, WardMethod] = {}
    merged.update(inherited)
    merged.update(own)

    # Stable ordering: inherited keys first (in their original order), then
    # any new own keys not already present in inherited (definition order).
    ordered: list[WardMethod] = []
    seen: set[str] = set()
    for key in inherited:
        ordered.append(merged[key])
        seen.add(key)
    for key in own:
        if key not in seen:
            ordered.append(merged[key])
            seen.add(key)

    return ordered
