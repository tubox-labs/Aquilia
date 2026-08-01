"""
Aquilia Contract Pipeline -- >> operator composition for transform chains.

A Pipeline is a sequence of Rune steps that run left to right.
Runes can be plain callables (transforms) or Facets (which run .cast() + .seal()).

Usage::

    from aquilia.contracts.transforms import strip, lower

    pipeline = Facet.text() >> strip >> lower
    ok, value, error = pipeline.run("  HELLO  ")
    # ok=True, value="hello", error=None
"""

from __future__ import annotations

from typing import Any

__all__ = ["Rune", "Pipeline", "_as_rune"]


class Rune:
    """Atomic transform/constraint node in a Pipeline."""

    __slots__ = ("fn", "name", "is_facet")

    def __init__(self, fn: Any, name: str | None = None, is_facet: bool = False):
        self.fn = fn
        self.name = name or getattr(fn, "__name__", type(fn).__name__)
        self.is_facet = is_facet

    def __rshift__(self, other: Any) -> Pipeline:
        return Pipeline([self, _as_rune(other)])

    def __repr__(self) -> str:
        kind = "Facet" if self.is_facet else "Transform"
        return f"<Rune {kind} '{self.name}'>"


class Pipeline:
    """
    An ordered sequence of transformation and validation steps ("Runes") composed via the ``>>`` operator.

    Purpose:
        Enables fluent, functional composition of facets and data transforms (e.g. ``Facet.text() >> strip >> lower``).
        Executes composed pipelines sequentially during Contract casting and validation passes.

    Lifecycle:
        1. **Definition Time**: Constructed when combining facets and functions using ``>>``.
        2. **Execution Time**: Called via ``pipeline.run(value)`` during facet value casting/sealing.

    Execution Order:
        1. Iterate over composed ``Rune`` steps from left to right.
        2. If a rune is a ``Facet``: call ``cast(val)`` followed by ``seal(val)``.
        3. If a rune is a callable transform: invoke ``fn(val)``.
        4. Return ``(True, final_value, None)`` on success, or catch errors and return ``(False, value, error_msg)``.

    Parameters:
        runes (list[Rune]):
            List of ordered ``Rune`` instances composing this pipeline.

    Returns:
        Pipeline: An initialized pipeline instance ready for execution.

    Exceptions:
        None directly raised during ``run()`` (errors are caught and returned in tuple).

    Notes:
        - Immutable & Reusable: Pipeline execution does not mutate internal rune definitions.
        - Supports nested pipeline concatenation via ``pipeline1 >> pipeline2``.

    Internal Behaviour:
        Catches ``CastFault`` and arbitrary ``Exception`` subclasses to return unified ``(ok, value, error)`` tuples.

    Edge Cases:
        - If a transform within the pipeline fails, execution stops immediately and returns the value state prior to failure.

    Examples:
        >>> from aquilia.contracts.transforms import strip, lower
        >>> pipe = Facet.text(min_length=3) >> strip >> lower
        >>> ok, val, err = pipe.run("  ALICE  ")
        >>> (ok, val)
        (True, 'alice')
    """

    __slots__ = ("runes",)

    def __init__(self, runes: list[Rune]):
        self.runes = list(runes)

    def __rshift__(self, other: Any) -> Pipeline:
        other_rune = _as_rune(other)
        if isinstance(other_rune, Pipeline):
            return Pipeline([*self.runes, *other_rune.runes])
        return Pipeline([*self.runes, other_rune])

    def run(self, value: Any) -> tuple[bool, Any, str | None]:
        """
        Execute all composed pipeline runes sequentially on input value.

        Purpose:
            Applies type coercion, transforms, and validators step-by-step from left to right.

        Lifecycle:
            Invoked when validating or casting inputs bound to a Pipeline-backed Facet.

        Execution Order:
            1. Iterate over each ``Rune`` in ``self.runes``.
            2. Apply facet casting/sealing or plain callable invocation.
            3. On failure: catch exception and return tuple with ``ok=False``.
            4. On completion: return tuple with ``ok=True``.

        Parameters:
            value (Any):
                The raw input value to transform and validate.

        Returns:
            tuple[bool, Any, str | None]:
                Tuple containing ``(success_flag, transformed_value, error_message_or_none)``.

        Exceptions:
            None. Internal exceptions are trapped and returned as error string in result tuple.
        """
        for rune in self.runes:
            try:
                if rune.is_facet:
                    value = rune.fn.cast(value)
                    value = rune.fn.seal(value)
                else:
                    value = rune.fn(value)
            except Exception as exc:
                from aquilia.contracts.exceptions import CastFault

                if isinstance(exc, CastFault):
                    msg = exc.field_errors.get(exc.field, [str(exc)])[0]
                    return (False, value, msg)
                return (False, value, str(exc))
        return (True, value, None)

    def __repr__(self) -> str:
        steps = " >> ".join(r.name for r in self.runes)
        return f"<Pipeline {steps}>"


def _as_rune(obj: Any) -> Rune | Pipeline:
    """Convert a plain callable, Facet, or Pipeline into a Rune.

    - If *obj* is already a ``Rune``, return as-is.
    - If *obj* is a ``Pipeline``, return it (caller handles flattening).
    - If *obj* has ``.cast()`` and ``.seal()`` (i.e. a Facet), wrap as
      a facet-mode Rune.
    - Otherwise, wrap as a plain-callable Rune.
    """
    if isinstance(obj, Rune):
        return obj
    if isinstance(obj, Pipeline):
        return obj
    if hasattr(obj, "cast") and hasattr(obj, "seal"):
        return Rune(obj, name=type(obj).__name__, is_facet=True)
    if callable(obj):
        return Rune(obj, name=getattr(obj, "__name__", repr(obj)), is_facet=False)
    raise TypeError(f"Cannot convert {type(obj).__name__} to Rune")
