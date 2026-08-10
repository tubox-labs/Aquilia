"""
AquilaVectorDB — Lookup compilation to ``elips.Filter``.

Translates Aquilia's ``field__lookup=value`` syntax into native elips metadata
predicates, and provides :class:`VF` — a composable node mirroring
``aquilia.models.query.QNode`` — for OR / NOT trees.

Supported lookups
-----------------

===================  ==========================================================
``f=v`` / ``f__exact``  ``compare(key, "eq", v)``
``f__ne``               ``compare(key, "ne", v)``
``f__gt`` ``__gte``     ``compare(key, "gt" | "ge", v)``
``f__lt`` ``__lte``     ``compare(key, "lt" | "le", v)``
``f__in``               ``in_set(key, values)``
``f__contains``         ``has_substring(key, v)``
``f__startswith``       ``has_substring`` + post-filter (see below)
``f__endswith``         ``has_substring`` + post-filter (see below)
``f__range``            ``ge`` AND ``le``
===================  ==========================================================

Deliberate rejections, each raising :class:`VectorLookupFault` rather than
returning quietly wrong records:

* ``__isnull`` — elips has no null. An absent metadata key simply fails to
  match, so neither ``True`` nor ``False`` has a faithful translation.
* range lookups over ``Decimal`` / ``UUID`` / ``bytes`` — these encode to
  strings where lexicographic order is not value order (``"9" > "10"``).
  Equality and ``__in`` remain available.
* unknown suffixes — a typo'd lookup would otherwise be read as a payload key
  named ``"field__typo"`` and match nothing.

Prefix / suffix caveat
----------------------

elips offers substring containment but not anchored matching. ``__startswith``
and ``__endswith`` therefore compile to a *containment* filter (which the engine
can push down) and set a residual predicate that the query layer applies to the
returned records. Anchoring is exact; only the push-down is approximate, so the
engine may examine more candidates than strictly necessary.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

from aquilia.vectordb.faults import VectorLookupFault

if TYPE_CHECKING:
    from aquilia.vectordb.metaclass import VectorSchema

#: Lookup suffix → elips comparator name.
_COMPARATORS: dict[str, str] = {
    "exact": "eq",
    "eq": "eq",
    "ne": "ne",
    "gt": "gt",
    "gte": "ge",
    "ge": "ge",
    "lt": "lt",
    "lte": "le",
    "le": "le",
}

#: Suffixes needing ordered comparison in the *encoded* space.
_ORDERED = {"gt", "gte", "ge", "lt", "lte", "le", "range"}

#: Every recognised suffix. Anything else is a typo, not a payload key.
_KNOWN = set(_COMPARATORS) | {"in", "contains", "icontains", "startswith", "endswith", "range", "isnull"}

#: Attribute prefix routing a lookup to embedding provenance rather than to a
#: declared payload — ``lineage__model="all-MiniLM-L6-v2"``.
_LINEAGE_PREFIX = "lineage__"

#: Provenance attributes a lineage lookup may name.
_LINEAGE_ATTRS = frozenset({"provider", "model", "revision"})

#: Residual attribute sentinel meaning "pass the whole record to the test",
#: rather than one of its attribute values.
_RECORD_SELF = "__record__"

#: Lookups that apply to a string provenance identifier.
_LINEAGE_LOOKUPS = frozenset({"exact", "eq", "ne", "in", "contains", "icontains", "startswith", "endswith"})


@dataclass(frozen=True)
class Residual:
    """
    A predicate the engine cannot express, applied to returned records.

    Args:
        attr: Model attribute the predicate tests.
        test: Callable receiving the *decoded* attribute value.
        description: Human-readable form, used in ``repr`` and explain output.
    """

    attr: str
    test: Callable[[Any], bool]
    description: str

    def __repr__(self) -> str:
        return f"<Residual {self.description}>"


@dataclass
class CompiledFilter:
    """
    Result of compiling a lookup set.

    Attributes:
        native: The ``elips.Filter``, or ``None`` when nothing pushed down.
        residuals: Predicates to apply to returned records.
    """

    native: Any | None
    residuals: list[Residual]

    def is_empty(self) -> bool:
        """True when this filter constrains nothing."""
        return self.native is None and not self.residuals


class VF:
    """
    Composable vector filter node — the OR / NOT companion to keyword lookups.

    Keyword lookups passed to ``filter()`` are AND-ed. Anything else needs an
    explicit tree, built with ``&``, ``|``, and ``~``::

        from aquilia.vectordb import VF

        node = (VF(kind="doc") & VF(year__gte=2023)) | VF(pinned=True)
        hits = await Doc.vectors.search(q).filter(node).top(10)

        fresh = ~VF(archived=True)

    Named ``VF`` rather than ``Q`` to keep it unmistakable against
    ``aquilia.models.query.Q`` (a queryset) and ``QNode`` (its SQL sibling).
    """

    AND = "AND"
    OR = "OR"

    __slots__ = ("lookups", "negated", "children", "connector")

    def __init__(self, **lookups: Any):
        """Create a leaf node whose lookups are AND-ed together."""
        self.lookups: dict[str, Any] = lookups
        self.negated: bool = False
        self.children: list[VF] = []
        self.connector: str = self.AND

    def __and__(self, other: VF) -> VF:
        """Combine with AND, returning a new node; neither operand is mutated."""
        node = VF()
        node.connector = self.AND
        node.children = [self, other]
        return node

    def __or__(self, other: VF) -> VF:
        """Combine with OR, returning a new node; neither operand is mutated."""
        node = VF()
        node.connector = self.OR
        node.children = [self, other]
        return node

    def __invert__(self) -> VF:
        """Return a negated copy; ``self`` is unchanged."""
        clone = VF(**self.lookups)
        clone.negated = not self.negated
        clone.children = list(self.children)
        clone.connector = self.connector
        return clone

    def __repr__(self) -> str:
        if self.children:
            neg = "~" if self.negated else ""
            return f"{neg}VF({self.connector}, children={len(self.children)})"
        neg = "~" if self.negated else ""
        return f"{neg}VF({self.lookups})"


def _split_lookup(expr: str) -> tuple[str, str]:
    """
    Split ``"field__lookup"`` into ``(attr, suffix)``.

    A trailing segment is only treated as a lookup when it is a *recognised*
    suffix, so an attribute legitimately named ``created_at`` is not read as
    ``created`` + ``at``.
    """
    if "__" in expr:
        head, _, tail = expr.rpartition("__")
        if head and tail in _KNOWN:
            return head, tail
    return expr, "exact"


def _lineage_residual(expr: str, attr: str, suffix: str, value: Any) -> Residual:
    """
    Build the residual predicate for a ``lineage__*`` lookup.

    Provenance is engine-owned metadata living on the record rather than in the
    filterable payload, so there is nothing to push down: the predicate runs in
    Python against the hydrated record. Correct, and honest about the cost — a
    lineage-only query reads the collection rather than narrowing it in the index.

    Args:
        expr: The original lookup expression, for fault messages.
        attr: Attribute half of the lookup, including the ``lineage__`` prefix.
        suffix: Lookup suffix.
        value: Comparison value.

    Raises:
        VectorLookupFault: On an unknown provenance attribute, or an operator
            that does not apply to a string identifier.
    """
    field = attr[len(_LINEAGE_PREFIX) :]
    if field not in _LINEAGE_ATTRS:
        known = ", ".join(sorted(_LINEAGE_ATTRS))
        raise VectorLookupFault(
            lookup=expr,
            reason=f"unknown lineage attribute {field!r}. Available: {known}",
        )

    if suffix in _ORDERED:
        raise VectorLookupFault(
            lookup=expr,
            reason=(
                f"lineage.{field} is a string identifier, so range comparison is "
                f"not meaningful. Use exact, __in, or __contains."
            ),
        )

    if suffix not in _LINEAGE_LOOKUPS:
        raise VectorLookupFault(
            lookup=expr,
            reason=f"lookup {suffix!r} is not supported on lineage attributes",
        )

    def test(record: Any, _field: str = field, _suffix: str = suffix, _value: Any = value) -> bool:
        lineage = getattr(record, "lineage", None)
        if lineage is None:
            return False
        actual = str(getattr(lineage, _field, "") or "")
        if _suffix in ("exact", "eq"):
            return actual == str(_value)
        if _suffix == "ne":
            return actual != str(_value)
        if _suffix == "in":
            return actual in {str(v) for v in _value}
        if _suffix == "contains":
            return str(_value) in actual
        if _suffix == "icontains":
            return str(_value).lower() in actual.lower()
        if _suffix == "startswith":
            return actual.startswith(str(_value))
        return actual.endswith(str(_value))

    return Residual(_RECORD_SELF, test, f"lineage.{field} {suffix} {value!r}")


def _key_residual(expr: str, suffix: str, value: Any) -> Residual:
    """
    Build the residual predicate for a lookup on the key attribute.

    A record's key is engine-owned identity, not payload metadata, and
    ``elips.Filter`` predicates only reach metadata — so a key lookup cannot be
    pushed down. It runs in Python against the hydrated record instead.

    Prefer :meth:`VectorManager.get` for a single key and
    :meth:`VectorManager.get_many` for a known set: both address the record
    directly, where a ``key__exact`` filter reads the collection to find it.

    Args:
        expr: The original lookup expression, for fault messages.
        suffix: Lookup suffix.
        value: Comparison value.

    Raises:
        VectorLookupFault: On an operator that does not apply to a string key.
    """
    if suffix in _ORDERED:
        raise VectorLookupFault(
            lookup=expr,
            reason=(
                "a record key is an opaque string identifier, so range comparison is "
                "not meaningful. Use exact, __in, __contains, __startswith, or __endswith."
            ),
        )

    if suffix not in _LINEAGE_LOOKUPS:
        raise VectorLookupFault(
            lookup=expr,
            reason=f"lookup {suffix!r} is not supported on a record key",
        )

    def test(record: Any, _suffix: str = suffix, _value: Any = value) -> bool:
        actual = str(getattr(record, "key", "") or "")
        if _suffix in ("exact", "eq"):
            return actual == str(_value)
        if _suffix == "ne":
            return actual != str(_value)
        if _suffix == "in":
            return actual in {str(v) for v in _value}
        if _suffix == "contains":
            return str(_value) in actual
        if _suffix == "icontains":
            return str(_value).lower() in actual.lower()
        if _suffix == "startswith":
            return actual.startswith(str(_value))
        return actual.endswith(str(_value))

    return Residual(_RECORD_SELF, test, f"key {suffix} {value!r}")


class FilterCompiler:
    """
    Compiles lookups against a model's schema into ``elips.Filter`` trees.

    Args:
        schema: The model's :class:`~aquilia.vectordb.metaclass.VectorSchema`,
            supplying payload key names and codecs.
    """

    def __init__(self, schema: VectorSchema):
        self._schema = schema

    # ── Public API ───────────────────────────────────────────────────────

    def compile(self, nodes: tuple[VF, ...], lookups: dict[str, Any]) -> CompiledFilter:
        """
        Compile positional :class:`VF` nodes and keyword lookups into one filter.

        All parts are AND-ed together, matching ``Q.filter()`` semantics.

        Args:
            nodes: Positional filter nodes.
            lookups: Keyword lookups.

        Returns:
            A :class:`CompiledFilter`.

        Raises:
            VectorLookupFault: On an unsupported or unknown lookup.
        """
        from elips import Filter

        native: Any | None = None
        residuals: list[Residual] = []

        for node in nodes:
            sub, sub_res = self._compile_node(node)
            residuals.extend(sub_res)
            if sub is not None:
                native = sub if native is None else native.and_(sub)

        for expr, value in lookups.items():
            leaf, leaf_res = self._compile_lookup(expr, value)
            residuals.extend(leaf_res)
            if leaf is not None:
                native = leaf if native is None else native.and_(leaf)

        # An all-residual filter still needs a native placeholder-free result;
        # `None` means "no push-down", which the query layer reads as scan-all.
        if native is not None and Filter is not None and native.matches_all():
            native = None

        return CompiledFilter(native=native, residuals=residuals)

    # ── Internals ────────────────────────────────────────────────────────

    def _compile_node(self, node: VF) -> tuple[Any | None, list[Residual]]:
        """Recursively compile a :class:`VF` tree.

        A negated subtree containing residuals cannot be evaluated correctly —
        ``NOT (pushdown AND residual)`` is not ``NOT pushdown AND NOT residual``
        — so that combination is rejected rather than silently mis-evaluated.
        """
        from elips import Filter

        native: Any | None = None
        residuals: list[Residual] = []

        for expr, value in node.lookups.items():
            leaf, leaf_res = self._compile_lookup(expr, value)
            residuals.extend(leaf_res)
            if leaf is not None:
                native = leaf if native is None else native.and_(leaf)

        for child in node.children:
            sub, sub_res = self._compile_node(child)
            residuals.extend(sub_res)
            if sub is None:
                continue
            if native is None:
                native = sub
            elif node.connector == VF.OR:
                native = native.or_(sub)
            else:
                native = native.and_(sub)

        if node.negated:
            if residuals:
                raise VectorLookupFault(
                    lookup=", ".join(node.lookups),
                    reason=(
                        "cannot negate a filter containing a prefix/suffix match — "
                        "elips has no anchored-match predicate to invert. Restructure "
                        "the query so the negation applies only to exact/range lookups."
                    ),
                )
            if native is not None:
                native = Filter.not_(native)

        return native, residuals

    def _compile_lookup(self, expr: str, value: Any) -> tuple[Any | None, list[Residual]]:
        """Compile a single ``field__lookup=value`` pair."""
        from elips import Filter

        attr, suffix = _split_lookup(expr)

        # Provenance lives outside the payload namespace — elips stores it on the
        # record itself, not in metadata — so it cannot be pushed down and is
        # evaluated as a residual against the hydrated record instead.
        if attr.startswith(_LINEAGE_PREFIX):
            return None, [_lineage_residual(expr, attr, suffix, value)]

        # The key is identity rather than metadata, and Filter predicates only
        # reach metadata. Same treatment, same reason.
        if attr == self._schema.key_attr:
            return None, [_key_residual(expr, suffix, value)]

        spec = self._schema.payload_by_attr.get(attr)

        if spec is None:
            known = ", ".join(sorted(self._schema.payload_by_attr)) or "(none)"
            hint = ""
            if self._schema.key_attr:
                hint = f" The key attribute is {self._schema.key_attr!r}."
            raise VectorLookupFault(
                lookup=expr,
                reason=(f"{self._schema.model_name!r} has no payload attribute {attr!r}. Available: {known}.{hint}"),
            )

        key = spec.key
        codec = spec.codec

        if suffix == "isnull":
            raise VectorLookupFault(
                lookup=expr,
                reason=(
                    "elips metadata has no null concept — an absent key does not match any "
                    "predicate. Model absence explicitly with a sentinel payload value "
                    f"(e.g. {attr}='' or a boolean has_{attr} flag) and filter on that."
                ),
            )

        if suffix in _ORDERED and not codec.orderable:
            raise VectorLookupFault(
                lookup=expr,
                reason=(
                    f"{attr!r} encodes to {codec.meta_type.__name__} via the {codec.name!r} codec, "
                    f"where ordering is lexicographic rather than by value (e.g. '9' > '10'). "
                    f"Range lookups would return wrong records; use exact or __in instead."
                ),
            )

        # ── Exact / comparison ───────────────────────────────────────────
        if suffix in _COMPARATORS:
            return Filter.compare(key, _COMPARATORS[suffix], codec.encode(value)), []

        # ── Membership ───────────────────────────────────────────────────
        if suffix == "in":
            values = [codec.encode(v) for v in value]
            if not values:
                # An empty __in matches nothing. There is no "match nothing"
                # Filter primitive, so express it as a residual that always
                # fails — correct, and it short-circuits in the query layer.
                return None, [Residual(attr, lambda _v: False, f"{attr} in ()")]
            return Filter.in_set(key, values), []

        # ── Substring ────────────────────────────────────────────────────
        if suffix in ("contains", "icontains"):
            needle = str(value)
            if suffix == "icontains":
                # elips substring matching is case-sensitive; fold the case in
                # a residual and push down nothing, since no case-insensitive
                # containment can be expressed natively.
                low = needle.lower()
                return None, [Residual(attr, lambda v, _l=low: _l in str(v).lower(), f"{attr} icontains {needle!r}")]
            return Filter.has_substring(key, needle), []

        if suffix in ("startswith", "endswith"):
            needle = str(value)
            anchored = str.startswith if suffix == "startswith" else str.endswith

            def test(v: Any, _n: str = needle, _a: Any = anchored) -> bool:
                return bool(_a(str(v), _n))

            return (
                Filter.has_substring(key, needle),
                [Residual(attr, test, f"{attr} {suffix} {needle!r}")],
            )

        # ── Range ────────────────────────────────────────────────────────
        if suffix == "range":
            try:
                low, high = value
            except (TypeError, ValueError) as exc:
                raise VectorLookupFault(
                    lookup=expr,
                    reason=f"__range expects a (low, high) pair, got {value!r}",
                ) from exc
            lo = Filter.compare(key, "ge", codec.encode(low))
            hi = Filter.compare(key, "le", codec.encode(high))
            return lo.and_(hi), []

        raise VectorLookupFault(
            lookup=expr,
            reason=f"unknown lookup suffix {suffix!r}. Supported: {', '.join(sorted(_KNOWN))}",
        )


def apply_residuals(records: list[Any], residuals: list[Residual]) -> list[Any]:
    """
    Filter hydrated records through residual predicates.

    Args:
        records: Model instances, in engine order.
        residuals: Predicates to apply; a record must satisfy all of them.

    Returns:
        The surviving records, order preserved.

    Notes:
        A residual whose ``attr`` is the record sentinel receives the whole
        record rather than one attribute value — that is how lineage predicates
        reach provenance, which lives beside the payload rather than in it.
    """
    if not residuals:
        return records

    out = []
    for rec in records:
        for res in residuals:
            if res.attr == _RECORD_SELF:
                if not res.test(rec):
                    break
                continue
            value = getattr(rec, res.attr, None)
            if value is None or not res.test(value):
                break
        else:
            out.append(rec)
    return out


__all__ = ["CompiledFilter", "FilterCompiler", "Residual", "VF", "apply_residuals"]
