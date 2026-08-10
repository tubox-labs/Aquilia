"""
AquilaVectorDB — Field expression nodes.

The typed half of the dual-syntax filter engine (§4.2 of the implementation
plan). A :class:`FieldExpression` is what a comparison against a field
descriptor evaluates to::

    Document.views >= 10          # FieldExpression("views", "gte", 10)
    Document.source.in_(["web"])  # FieldExpression("source", "in", ["web"])

Expressions compose with ``&``, ``|``, and ``~`` into the same :class:`VF` trees
keyword lookups build, so both syntaxes land in one
:class:`~aquilia.vectordb.filters.FilterCompiler` path and neither can drift
from the other::

    (Document.views >= 10) & ~(Document.kind == "draft")

Why a node and not a compiled filter
------------------------------------

An expression is built at *class* scope, long before any store is open, and
carries no reference to ``elips``. Compilation happens in the query layer where
the schema (and therefore the storage key and codec for each attribute) is
known. That is what lets a module define reusable filter constants at import
time on a machine with no vector store configured.
"""

from __future__ import annotations

from typing import Any

from aquilia.vectordb.filters import VF

#: Operator name → the lookup suffix :class:`FilterCompiler` already speaks.
#:
#: Expressions deliberately reuse the keyword-lookup vocabulary rather than
#: introducing a parallel one: one compiler, one set of rejections, one place
#: where a codec's orderability is checked.
OPERATORS: dict[str, str] = {
    "eq": "exact",
    "ne": "ne",
    "gt": "gt",
    "gte": "gte",
    "lt": "lt",
    "lte": "lte",
    "in": "in",
    "contains": "contains",
    "icontains": "icontains",
    "startswith": "startswith",
    "endswith": "endswith",
    "range": "range",
}


class FieldExpression:
    """
    One comparison between a field and a value.

    Produced by the operator overloads on
    :class:`~aquilia.vectordb.fields.BaseVectorField`; rarely constructed
    directly.

    Args:
        attr: Model attribute name the comparison tests.
        op: Operator key from :data:`OPERATORS`.
        value: The operand.

    Example::

        expr = Document.views >= 10
        hits = await Document.vectors.filter(expr).all()
    """

    __slots__ = ("attr", "op", "value")

    def __init__(self, attr: str, op: str, value: Any) -> None:
        self.attr = attr
        self.op = op
        self.value = value

    # ── Composition ──────────────────────────────────────────────────────

    def as_vf(self) -> VF:
        """
        Return this expression as a single-lookup :class:`VF` node.

        The bridge between the two syntaxes: everything downstream of here
        only ever sees ``VF``.
        """
        suffix = OPERATORS.get(self.op, self.op)
        return VF(**{f"{self.attr}__{suffix}": self.value})

    def __and__(self, other: FieldExpression | VF) -> VF:
        """Combine with AND, yielding a :class:`VF` tree."""
        return self.as_vf() & _as_vf(other)

    def __or__(self, other: FieldExpression | VF) -> VF:
        """Combine with OR, yielding a :class:`VF` tree."""
        return self.as_vf() | _as_vf(other)

    def __invert__(self) -> VF:
        """Negate, yielding a :class:`VF` tree."""
        return ~self.as_vf()

    def __rand__(self, other: VF) -> VF:
        """Support ``VF(...) & expression``."""
        return _as_vf(other) & self.as_vf()

    def __ror__(self, other: VF) -> VF:
        """Support ``VF(...) | expression``."""
        return _as_vf(other) | self.as_vf()

    # ── Guards ───────────────────────────────────────────────────────────

    def __bool__(self) -> bool:
        """
        Always raises.

        ``if Document.views >= 10:`` is a filter that was never applied — and
        without this guard it would silently evaluate true and the query would
        return everything. The same reason ``VectorQuery.__bool__`` raises.
        """
        from aquilia.vectordb.faults import VectorQueryFault

        raise VectorQueryFault(
            reason=(
                f"a field expression ({self!r}) has no boolean value. Pass it to "
                f"filter()/exclude(), or combine expressions with & | ~ rather than "
                f"'and'/'or'/'not'."
            )
        )

    def __repr__(self) -> str:
        return f"<FieldExpression {self.attr} {self.op} {self.value!r}>"


def _as_vf(other: Any) -> VF:
    """Coerce an expression or node into a :class:`VF`."""
    if isinstance(other, FieldExpression):
        return other.as_vf()
    if isinstance(other, VF):
        return other
    from aquilia.vectordb.faults import VectorQueryFault

    raise VectorQueryFault(
        reason=(
            f"cannot combine a field expression with {type(other).__name__}; expected another expression or a VF node"
        )
    )


def to_vf(value: Any) -> VF:
    """
    Coerce any supported filter form into a :class:`VF`.

    The single funnel through which all three filter syntaxes reach the
    compiler, which is what keeps them from diverging: keyword lookups, Python
    expressions, and EQL strings become the same node tree, so push-down
    analysis and residual handling are decided in exactly one place.

    Args:
        value: A :class:`VF`, a :class:`FieldExpression`, or an EQL string.

    Returns:
        The equivalent :class:`VF` node.

    Raises:
        VectorQueryFault: When ``value`` is not a recognized filter form.
        VectorEQLFault: When ``value`` is a string that does not parse as EQL.
    """
    if isinstance(value, str):
        from aquilia.vectordb.eql import parse_eql

        return parse_eql(value)
    return _as_vf(value)


__all__ = ["OPERATORS", "FieldExpression", "to_vf"]
