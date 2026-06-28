"""
Aquilia Blueprint Pipeline -- >> operator composition for transform chains.

A Pipeline is a sequence of Rune steps that run left to right.
Runes can be plain callables (transforms) or Facets (which run .cast() + .seal()).

Usage::

    from aquilia.blueprints.transforms import strip, lower

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
    """Ordered sequence of Rune steps composed via >>."""

    __slots__ = ("runes",)

    def __init__(self, runes: list[Rune]):
        self.runes = list(runes)

    def __rshift__(self, other: Any) -> Pipeline:
        other_rune = _as_rune(other)
        if isinstance(other_rune, Pipeline):
            return Pipeline([*self.runes, *other_rune.runes])
        return Pipeline([*self.runes, other_rune])

    def run(self, value: Any) -> tuple[bool, Any, str | None]:
        """Run each rune in order.

        If a rune is a Facet, call ``.cast()`` then ``.seal()``.
        Otherwise call it as a plain function.

        Returns:
            ``(ok, final_value, error_or_none)``.
            Never raises.  Uses try/except internally.
        """
        for rune in self.runes:
            try:
                if rune.is_facet:
                    value = rune.fn.cast(value)
                    value = rune.fn.seal(value)
                else:
                    value = rune.fn(value)
            except Exception as exc:
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
