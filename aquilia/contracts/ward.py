"""
Aquilia Contract Ward -- explicit cross-field validator registration.

Replaces the fragile seal_*/async_seal_* name-prefix scanning with
explicit @ward decorator registration, discovered once at class-body
evaluation time.

Usage::

    from aquilia.contracts import ward

    class OrderContract(Contract):
        @ward
        def total_matches_items(self, data):
            computed = sum(i.price * i.qty for i in data.items)
            if abs(computed - data.total) > 0.01:
                self.reject("total", f"Expected {computed}, got {data.total}")

        @ward(mode="async")
        async def discount_code_valid(self, data):
            if data.discount_code and not await lookup(data.discount_code):
                self.reject("discount_code", "Unknown code")

Deprecated: the ``seal_*`` / ``async_seal_*`` prefix convention
--------------------------------------------------------------

Before the decorator existed, a method was registered as a validator purely
because its name began with ``seal_`` or ``async_seal_``. That convention is
deprecated since Aquilia 1.3.0 and is removed in 2.0.0.

Why it is going away — each of these has cost real debugging time:

* **A rename silently disables validation.** Renaming ``seal_total`` to
  ``check_total`` during a routine cleanup removes the rule with no error, no
  warning, and no failing test unless one happens to cover that exact rule. The
  Contract keeps reporting success on payloads it should reject.
* **A name collision silently creates one.** A helper legitimately named
  ``seal_envelope`` on a Contract is executed as a validator on every request,
  with its return value discarded and any exception it raises converted into a
  user-facing field error.
* **Async mode is inferred, not declared.** Mode came from
  ``inspect.iscoroutinefunction``, so a validator awaiting the database while
  written as a sync ``def`` was registered as sync — the coroutine was created,
  never awaited, and the check never ran.
* **No room to grow.** Ordering, conditions, and validation groups have nowhere
  to live in a naming convention. ``@ward`` carries them as metadata.

Migration is mechanical — decorate the method; the body does not change::

    # Before (deprecated)
    class OrderContract(Contract):
        def seal_total(self, data):
            if data["total"] < 0:
                self.reject("total", "Must not be negative")

        async def async_seal_stock(self, data):
            if not await in_stock(data["sku"]):
                self.reject("sku", "Out of stock")

    # After
    class OrderContract(Contract):
        @ward
        def total_not_negative(self, data):          # rename now safe
            if data["total"] < 0:
                self.reject("total", "Must not be negative")

        @ward(mode="async")
        async def stock_available(self, data):
            if not await in_stock(data["sku"]):
                self.reject("sku", "Out of stock")

Note that ``mode="async"`` becomes explicit, and the methods may be renamed to
describe the rule rather than to satisfy the scanner.

To find every affected method in a codebase, promote the warning to an error::

    python -W error::DeprecationWarning -c "import myapp.contracts"

Or, in ``pytest.ini`` / ``pyproject.toml``::

    [tool.pytest.ini_options]
    filterwarnings = ["error::DeprecationWarning"]

Both surface each legacy method with its class name, its exact replacement
decorator, and the file and line that declared it.
"""

from __future__ import annotations

import inspect
import warnings
from collections.abc import Callable, Sequence
from dataclasses import dataclass
from typing import Any

__all__ = [
    "ward",
    "WardMethod",
    "collect_ward_methods",
    "legacy_prefix_message",
    "DEPRECATED_PREFIX_SINCE",
    "DEPRECATED_PREFIX_REMOVED_IN",
]


# ---------------------------------------------------------------------------
# WardMethod
# ---------------------------------------------------------------------------


@dataclass(frozen=True, slots=True)
class WardMethod:
    """
    Descriptor for a single cross-field validator registered on a Contract.

    Attributes:
        name: Method name.
        fn: The underlying callable.
        mode: ``"sync"`` or ``"async"``.
        order: Sort key. Lower runs first; ties keep definition order.
        when: Optional predicate receiving the validated data. The ward runs
            only when it returns truthy.
        groups: Group names this ward belongs to. An empty tuple means the ward
            always runs; otherwise it runs only when one of its groups is
            active.
    """

    name: str
    fn: object  # the callable
    mode: str  # "sync" or "async"
    order: int = 0
    when: Callable[[Any], bool] | None = None
    groups: tuple[str, ...] = ()

    def should_run(self, data: Any, active_groups: frozenset[str] | None) -> bool:
        """
        Decide whether this ward applies to the current validation pass.

        Args:
            data: The validated data, passed to the ``when`` predicate.
            active_groups: Groups requested for this pass, or ``None`` when the
                caller did not restrict groups.

        Returns:
            True if the ward should run.

        Notes:
            An ungrouped ward always applies: it expresses an invariant that
            holds regardless of which group the caller asked for.

            A ``when`` predicate that raises is treated as "does not apply".
            The predicate is a routing decision, not a validation rule — a
            broken predicate must not manufacture a field error attributed to
            the ward it was gating.
        """
        if self.groups and (active_groups is None or not active_groups.intersection(self.groups)):
            return False

        if self.when is None:
            return True
        try:
            return bool(self.when(data))
        except Exception:
            return False


# ---------------------------------------------------------------------------
# @ward decorator
# ---------------------------------------------------------------------------

_VALID_MODES = frozenset({"sync", "async"})


class ward:
    """Decorator (and decorator-factory) for registering Contract ward methods.

    Supports two usage patterns:

    * **Bare decorator** — ``@ward`` attaches sync metadata::

          @ward
          def my_validator(self, data): ...

    * **Parameterised decorator** — ``@ward(mode="async")``::

          @ward(mode="async")
          async def my_async_validator(self, data): ...

    Args:
        fn: The decorated function (bare usage only).
        mode: ``"sync"`` (default) or ``"async"``.
        order: Sort key within the ward phase. Lower runs first; wards sharing
            an order keep definition order. Use this when one ward's rejection
            makes another's work redundant or misleading.
        when: Predicate receiving the validated data; the ward runs only when it
            returns truthy. For conditional rules — a shipping-address check
            that applies only to physical orders, say.
        groups: Group names. A ward with groups runs only when
            ``is_sealed(groups=...)`` names one of them; a ward without groups
            always runs.

    Examples:
    ```
        Ordering and conditions::

            @ward(order=-10)
            def cheapest_check_first(self, data): ...

            @ward(when=lambda data: data.get("kind") == "physical")
            def needs_shipping_address(self, data): ...

            @ward(groups=("checkout",))
            def payment_method_valid(self, data): ...
    ```
    In all cases the decorated function receives a ``__ward_meta__`` dict.
    """

    # Use __new__ so that ``ward(fn)`` (bare) returns the decorated *fn*
    # directly, while ``ward(mode=...)`` returns a *ward* instance whose
    # ``__call__`` acts as the real decorator.

    def __new__(
        cls,
        fn: Callable[..., Any] | None = None,
        *,
        mode: str = "sync",
        order: int = 0,
        when: Callable[[Any], bool] | None = None,
        groups: str | Sequence[str] = (),
    ) -> Any:  # noqa: ANN401
        if mode not in _VALID_MODES:
            raise ValueError(f"Invalid ward mode {mode!r}; expected one of {sorted(_VALID_MODES)}")
        if when is not None and not callable(when):
            raise TypeError(f"@ward(when=...) expects a callable, got {type(when).__name__}")

        normalized_groups = _normalize_groups(groups)

        if fn is not None:
            # Bare usage: @ward  (fn is the decorated method)
            if not callable(fn):
                raise TypeError(f"@ward expects a callable, got {type(fn).__name__}")
            fn.__ward_meta__ = {  # type: ignore[attr-defined]
                "mode": mode,
                "name": fn.__name__,
                "order": order,
                "when": when,
                "groups": normalized_groups,
            }
            return fn  # type: ignore[return-value]

        # Factory usage: @ward(mode="async") — return a real instance whose
        # __call__ will do the attaching.
        instance = super().__new__(cls)
        instance._mode = mode  # type: ignore[attr-defined]
        instance._order = order  # type: ignore[attr-defined]
        instance._when = when  # type: ignore[attr-defined]
        instance._groups = normalized_groups  # type: ignore[attr-defined]
        return instance

    def __init__(
        self,
        fn: Callable[..., Any] | None = None,
        *,
        mode: str = "sync",
        order: int = 0,
        when: Callable[[Any], bool] | None = None,
        groups: str | Sequence[str] = (),
    ) -> None:
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
        fn.__ward_meta__ = {  # type: ignore[attr-defined]
            "mode": self._mode,
            "name": fn.__name__,
            "order": self._order,
            "when": self._when,
            "groups": self._groups,
        }
        return fn


def _normalize_groups(groups: str | Sequence[str]) -> tuple[str, ...]:
    """Accept a single group name or a sequence, returning a tuple."""
    if isinstance(groups, str):
        return (groups,)
    return tuple(groups)


# ---------------------------------------------------------------------------
# Legacy seal_* / async_seal_* prefix convention (deprecated)
# ---------------------------------------------------------------------------

#: Release in which the legacy ``seal_*``/``async_seal_*`` prefix convention was
#: deprecated in favour of the explicit :class:`ward` decorator.
DEPRECATED_PREFIX_SINCE: str = "1.3.0"

#: Release in which prefix scanning is removed. After this version a method
#: named ``seal_total`` is an ordinary method that never runs as a validator.
DEPRECATED_PREFIX_REMOVED_IN: str = "2.0.0"


def legacy_prefix_message(owner: str, method: str, *, is_async: bool) -> str:
    """
    Build the deprecation message for one legacy-prefixed validator.

    The message names the exact replacement for *this* method rather than
    restating the general rule, so the fix can be applied without opening the
    documentation. A warning a developer cannot act on directly is a warning
    that gets filtered out.

    Args:
        owner: Name of the Contract class declaring the method.
        method: The ``seal_*``/``async_seal_*`` method name.
        is_async: Whether the method is a coroutine function, which decides
            whether the replacement needs ``mode="async"``.

    Returns:
        A message naming the offending method, its replacement decorator, and
        the release in which the legacy behavior stops working.

    Examples:
        A sync validator::

            >>> msg = legacy_prefix_message("OrderContract", "seal_total", is_async=False)
            >>> "@ward instead" in msg
            True

        An async one is told to use the parameterised form::

            >>> msg = legacy_prefix_message("OrderContract", "async_seal_stock", is_async=True)
            >>> '@ward(mode="async") instead' in msg
            True
    """
    decorator = '@ward(mode="async")' if is_async else "@ward"
    return (
        f"{owner}.{method} is registered as a validator by the deprecated "
        f"seal_*/async_seal_* prefix convention (deprecated in Aquilia "
        f"{DEPRECATED_PREFIX_SINCE}, removed in {DEPRECATED_PREFIX_REMOVED_IN}). "
        f"Decorate it with {decorator} instead — the method body does not need "
        f"to change, and you may then rename it freely. After "
        f"{DEPRECATED_PREFIX_REMOVED_IN}, {owner}.{method} will be treated as an "
        f"ordinary method and will silently stop validating."
    )


# ---------------------------------------------------------------------------
# collect_ward_methods
# ---------------------------------------------------------------------------


def collect_ward_methods(
    name: str,
    bases: tuple[type, ...],
    namespace: dict[str, Any],
) -> list[WardMethod]:
    """Collect all ward methods for a Contract class being constructed.

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
                order=meta.get("order", 0),
                when=meta.get("when"),
                groups=meta.get("groups", ()),
            )

    # 3. Backward-compat: the legacy seal_*/async_seal_* prefix convention.
    #
    # Deprecated since 1.3.0; scheduled for removal in 2.0.0. See
    # DEPRECATED_PREFIX_REMOVED_IN and the module docstring for the rationale
    # and the migration path.
    for attr_name, obj in namespace.items():
        if not callable(obj):
            continue
        if hasattr(obj, "__ward_meta__"):
            continue  # already registered via @ward
        if not (attr_name.startswith("seal_") or attr_name.startswith("async_seal_")):
            continue

        is_async = inspect.iscoroutinefunction(obj)
        mode = "async" if is_async else "sync"
        warnings.warn(
            legacy_prefix_message(name, attr_name, is_async=is_async),
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

    # Stable sort keeps definition order within an equal `order`, so wards that
    # do not set one behave exactly as before.
    ordered.sort(key=lambda wm: wm.order)
    return ordered
