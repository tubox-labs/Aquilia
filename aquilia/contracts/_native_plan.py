"""Compile a Contract's Sigil into a native FieldPlan, when it is safe to.

This module owns **eligibility** -- the rule that keeps the native validation
path safe (``docs/models-engine/03-engine-design.md`` §8).

Eligibility is decided **per field**, not per contract
---------------------------------------------------
The original rule rejected the whole plan if any single field was not
representable. A ``NestedContractFacet`` is not representable, and nested
objects are the normal case in real APIs, so one nested field disabled native
validation for the entire contract -- the native path was effectively dead in
production while carrying its full maintenance cost.

The resolution is compositional. A field the native plan cannot represent is
not a reason to reject its fourteen siblings; it is simply **escaped**. The
compiled plan carries only the fields it can decide, and :func:`field_plan_for`
returns the escaped names alongside it. The caller runs the native plan for the
first set and ``Sigil.validate(..., _only=escaped)`` for the second.

Why this does not reintroduce divergence risk
---------------------------------------------
The safety property is unchanged because escaped fields are not reimplemented
anywhere -- they run the *identical* ``Sigil.validate`` loop that would have
handled them if no plan existed at all. There is no second implementation of a
field's semantics, so there is nothing that can silently drift. Only the
*granularity* of the native/Python decision changed: it was per contract, it is
now per field.

Two independent layers of conservatism remain:

1. **Compile time (here).** A facet with a pipeline, validators, a
   ``default_factory``, a regex pattern, or a custom subclass is escaped to
   Python rather than represented.
2. **Run time (fieldplan.cpp).** Even within a compiled plan, any *value* the
   native code cannot decide with certainty aborts the whole payload back to
   ``Sigil.validate``. That is what makes error messages byte-identical and
   correctly localised: failures are always rendered by the Python path.
"""

from __future__ import annotations

import sys
from typing import Any, NamedTuple

from aquilia._dataengine_loader import DATAENGINE_NATIVE, native_module

__all__ = ["CompiledPlan", "field_plan_for", "plan_cache_size"]


class CompiledPlan(NamedTuple):
    """A native plan plus the fields it does not cover.

    Attributes:
        plan: The native ``FieldPlan`` handling ``covered`` fields.
        escaped: Field names the plan does not represent. The caller must run
            these through ``Sigil.validate(..., _only=escaped)``. Empty means
            the plan covers the whole contract and no Python pass is needed.
    """

    plan: Any
    escaped: frozenset[str]


# Contract class -> CompiledPlan, or None when the contract is ineligible. The
# None entries matter as much as the plans: they stop a rejected contract from
# being re-analysed on every request.
#
# Keyed by the class object itself. Plans are immutable once built, and dev-mode
# hot reload creates new classes which miss the cache naturally, so there is no
# invalidation path and therefore no staleness bug (03 §11).
_PLAN_CACHE: dict[type, CompiledPlan | None] = {}


def plan_cache_size() -> int:
    """Number of contracts analysed. Used by the plan-cache-bound test."""
    return len(_PLAN_CACHE)


def _facet_type_code(facet: Any, tc: Any, ck: Any) -> tuple[int | None, int]:
    """Map a facet to (TypeCode, ContainerKind), or (None, _) when not representable.

    Returns:
        A pair (type_code, container_kind). The type code describes the scalar
        element type; the container describes the shape. When container is NONE,
        type_code applies to the value directly. When container is LIST/SET/TUPLE,
        type_code applies to each element. None means the facet is not
        representable and must be escaped.
    """
    from aquilia.contracts.facets import (
        BoolFacet,
        BytesFacet,
        ChoiceFacet,
        DateFacet,
        DateTimeFacet,
        DecimalFacet,
        DictFacet,
        DurationFacet,
        EnumFacet,
        FloatFacet,
        IntFacet,
        ListFacet,
        LiteralFacet,
        SetFacet,
        TextFacet,
        TimeFacet,
        TupleFacet,
        UUIDFacet,
    )

    exact = type(facet)

    # Scalar facets
    if exact is TextFacet:
        return (tc.STR, ck.NONE)
    if exact is IntFacet:
        return (tc.INT, ck.NONE)
    if exact is FloatFacet:
        # FloatFacet.seal tests multiple_of with an epsilon comparison whose
        # result at the boundary depends on binary rounding. The native path
        # implements only the exact integer test, so a float multiple_of is
        # escaped rather than approximated.
        if getattr(facet, "multiple_of", None) is not None:
            return (None, ck.NONE)
        return (tc.FLOAT, ck.NONE)
    if exact is BoolFacet:
        return (tc.BOOL, ck.NONE)
    if exact is UUIDFacet:
        return (tc.UUID, ck.NONE)
    if exact is DateFacet:
        return (tc.DATE, ck.NONE)
    if exact is DateTimeFacet:
        return (tc.DATETIME, ck.NONE)
    if exact is TimeFacet:
        return (tc.TIME, ck.NONE)
    if exact is DecimalFacet:
        return (tc.DECIMAL, ck.NONE)
    if exact is DurationFacet:
        return (tc.DURATION, ck.NONE)
    if exact is BytesFacet:
        return (tc.BYTES, ck.NONE)

    # ChoiceFacet and its LiteralFacet subclass both reduce to one frozenset
    # membership test. LiteralFacet builds itself as ChoiceFacet(choices=[value])
    # so a single code covers both.
    if exact is ChoiceFacet or exact is LiteralFacet:
        return (tc.CHOICE, ck.NONE)

    # EnumFacet: native lookup by value then by name. Only safe when the class
    # has not overridden `_missing_` -- that hook is arbitrary Python which
    # EnumMeta.__call__ invokes on a lookup miss, and the native path replaces
    # that call with a plain dict lookup.
    if exact is EnumFacet:
        if not _enum_is_plain(getattr(facet, "enum_class", None)):
            return (None, ck.NONE)
        return (tc.ENUM, ck.NONE)

    # DictFacet. The value facet becomes the element code; without one, values
    # pass through untouched, which is exactly what `result[k] = v` does.
    if exact is DictFacet:
        value_facet = getattr(facet, "value_facet", None)
        if value_facet is None:
            return (tc.PASSTHROUGH, ck.DICT)
        if not _child_is_plain(value_facet):
            return (None, ck.NONE)
        element = _SCALAR_ELEMENT_CODES(tc).get(type(value_facet))
        if element is None:
            return (None, ck.NONE)
        return (element, ck.DICT)

    # Containers. The element type is carried in the type code and the shape in
    # the container kind, so each element type is expressed once rather than
    # once per container.
    container_kinds = {ListFacet: ck.LIST, SetFacet: ck.SET, TupleFacet: ck.TUPLE}
    kind = container_kinds.get(exact)
    if kind is not None:
        # `unique` is not an attribute of any of these facets today. Checked
        # defensively so that adding one later escapes to Python instead of
        # being ignored here, which would silently accept duplicates.
        if getattr(facet, "unique", False):
            return (None, ck.NONE)

        child_facet = getattr(facet, "child", None)
        if child_facet is None:
            return (None, ck.NONE)

        # A child carrying its own constraints or user code is not represented:
        # the element cast applies the bare scalar cast and would skip them.
        if not _child_is_plain(child_facet):
            return (None, ck.NONE)

        element = _SCALAR_ELEMENT_CODES(tc).get(type(child_facet))
        if element is None:
            # Nested contracts as elements are handled by the caller, which has
            # the recursion budget needed to compile a sub-plan.
            return (None, ck.NONE)
        return (element, kind)

    return (None, ck.NONE)


def _SCALAR_ELEMENT_CODES(tc: Any) -> dict:
    """Element type codes usable inside a container or as a dict value.

    Only the scalar casts appear here. A container element runs the bare cast
    with no flags and without its facet's ``seal``, so anything whose semantics
    live in ``seal`` (Choice, Enum, Decimal precision) is deliberately absent --
    including it would silently drop those constraints.
    """
    from aquilia.contracts.facets import (
        BoolFacet,
        DateFacet,
        DateTimeFacet,
        FloatFacet,
        IntFacet,
        TextFacet,
        TimeFacet,
        UUIDFacet,
    )

    return {
        TextFacet: tc.STR,
        IntFacet: tc.INT,
        FloatFacet: tc.FLOAT,
        BoolFacet: tc.BOOL,
        UUIDFacet: tc.UUID,
        DateFacet: tc.DATE,
        DateTimeFacet: tc.DATETIME,
        TimeFacet: tc.TIME,
    }


def _nested_is_plain(nested_cls: Any) -> bool:
    """Whether a nested Contract's validation is purely structural.

    ``run_nested_contract`` (sigil.py) does more than run the child's Sigil: it
    instantiates the child, runs its ``@ward`` methods, and calls its
    object-level ``validate()`` hook. Both are user Python, which the engine may
    never execute -- so a child declaring either is escaped.

    A child with no wards and no ``validate`` override reduces to exactly its
    structural pass, which is what a sub-plan reproduces.
    """
    from aquilia.contracts.core import Contract

    if not isinstance(nested_cls, type) or not issubclass(nested_cls, Contract):
        return False
    if getattr(nested_cls, "_ward_methods", None):
        return False
    # An overridden validate() can rewrite or reject the validated data.
    if nested_cls.validate is not Contract.validate:
        return False
    return True


def _enum_is_plain(enum_class: Any) -> bool:
    """Whether an Enum class resolves values by its plain lookup tables.

    ``EnumFacet.cast`` calls ``enum_class(value)``, which is
    ``EnumMeta.__call__``: it consults ``_value2member_map_`` and, on a miss,
    calls the ``_missing_`` hook. The native path replaces that with a dict
    lookup, which is exact only while ``_missing_`` is the inherited no-op --
    an override can return any member it likes for an unmapped value.
    """
    from enum import Enum

    if not isinstance(enum_class, type) or not issubclass(enum_class, Enum):
        return False

    own = getattr(enum_class, "_missing_", None)
    base = getattr(Enum, "_missing_", None)
    if own is None or base is None:
        return False
    # Both are bound classmethods; compare the underlying functions.
    return getattr(own, "__func__", own) is getattr(base, "__func__", base)


def _child_is_plain(child: Any) -> bool:
    """Whether a list child facet carries nothing the element cast would skip.

    ``cast_list_of`` applies only the scalar cast to each element -- it does not
    run the child's ``seal``. A child with length bounds, numeric bounds, a
    pattern, validators, or a pipeline therefore has constraints the native path
    would silently drop, so such a list is escaped to Python entirely.
    """
    if getattr(child, "validators", None):
        return False
    if getattr(child, "_pipeline", None) is not None:
        return False
    for attr in ("min_length", "max_length", "min_value", "max_value", "pattern", "multiple_of"):
        if getattr(child, attr, None) is not None:
            return False
    # A blank element is rejected by TextFacet.seal unless allow_blank; the
    # element cast is called with kFieldNone, which assumes the default.
    if getattr(child, "allow_blank", False):
        return False
    return True


def _field_is_eligible(spec: Any, facet: Any) -> bool:
    """Whether a field can be represented natively.

    False is not a failure -- the field is escaped to ``Sigil.validate``, which
    is the same code that would have run for it anyway. So the bar here is
    "can the native plan reproduce this field's semantics *exactly*", and
    anything short of certainty answers no.
    """
    # User code. None of this can run natively, by the rule in 01 §6: the engine
    # may compute plans and convert values, but must never call a Python callable.
    if spec.pipeline is not None:
        return False
    if getattr(facet, "validators", None):
        return False

    # A default_factory is a callable, and even a plain `default` that happens to
    # be callable is invoked by Sigil.validate (`facet.default() if callable(...)`).
    if getattr(spec, "default_factory", None) is not None:
        return False
    default = getattr(facet, "default", None)
    if callable(default):
        return False

    # Skipped or context-resolved facet kinds never reach the native loop.
    if facet.read_only:
        return False

    # `pattern`, `choices`, `multiple_of`, and nested Contracts are no longer
    # blanket rejections: _facet_type_code decides them per facet type. It
    # answers only for an exact known type, so a facet carrying one of those
    # attributes without native support for it (PolymorphicFacet.choices,
    # FloatFacet.multiple_of, EmailFacet's class-level regex) is escaped there
    # instead.

    return True


#: How deep a chain of nested Contracts the compiler will follow.
#:
#: Bounds compile-time recursion. It is far below
#: :data:`~aquilia.contracts.exceptions.MAX_NESTING_DEPTH` (32, the *runtime*
#: payload limit) because a plan nested this deep would be a schema-design
#: problem, not a performance opportunity -- and every level multiplies the
#: compiled plan's size. A chain deeper than this escapes to Python, which
#: enforces the real limit.
MAX_PLAN_NESTING: int = 6


def _compile_nested(
    facet: Any,
    tc: Any,
    ck: Any,
    depth: int,
    building: frozenset[type],
) -> tuple[int | None, int, Any]:
    """Compile a nested-Contract field into (code, container, sub_plan).

    Returns ``(None, ck.NONE, None)`` when the field must be escaped, which is
    the answer for every case the sub-plan cannot reproduce exactly:

    * a forward reference that has not resolved yet
    * a self-referential or cyclic Contract (compiling it would not terminate)
    * a chain deeper than :data:`MAX_PLAN_NESTING`
    * a child declaring ``@ward`` methods or a ``validate()`` override, both of
      which ``run_nested_contract`` executes and neither of which may run natively
    * a child whose own plan is partial -- an escaped field inside the child has
      no way to be reported through the parent's single native pass
    """
    from aquilia.contracts.sigil import resolve_nested

    if depth >= MAX_PLAN_NESTING:
        return (None, ck.NONE, None)

    nested_cls, is_many = resolve_nested(facet)
    if nested_cls is None:
        # Unresolved forward reference. It may resolve later, but this plan is
        # cached, so answering "escape" now is the safe permanent answer.
        return (None, ck.NONE, None)

    if nested_cls in building:
        # Self-referential, directly or through a cycle. Recursing would not
        # terminate, and a plan cannot express unbounded depth anyway.
        return (None, ck.NONE, None)

    if not _nested_is_plain(nested_cls):
        return (None, ck.NONE, None)

    sub = _build_plan(nested_cls, depth + 1, building)
    if sub is None or sub.escaped:
        # A partial child plan cannot be used: the parent runs one native pass
        # and has nowhere to report the child's escaped fields from.
        return (None, ck.NONE, None)

    return (tc.NESTED, ck.LIST if is_many else ck.NONE, sub.plan)


def _build_plan(contract_cls: type, _depth: int = 0, _building: frozenset[type] = frozenset()) -> CompiledPlan | None:
    """Compile the representable fields; escape the rest to Python.

    Args:
        contract_cls: The Contract to compile.
        _depth: Nested-Contract recursion depth. Bounded by
            :data:`MAX_PLAN_NESTING`.
        _building: Contracts already being compiled further up this recursion.
            A Contract that reappears is self-referential (directly or through a
            cycle); compiling it would not terminate, so the field naming it is
            escaped.
    """
    de = native_module()
    if de is None:
        return None

    from aquilia.contracts.facets import UNSET, Computed, Constant, Inject

    sigil = getattr(contract_cls, "_sigil", None)
    if sigil is None:
        return None

    # These are whole-contract properties, not per-field ones, so they still
    # reject outright -- there is no subset of fields for which they are false.
    #
    # strict mode has *different* semantics -- cast is skipped entirely
    # (sigil.py) -- so it is a separate execution mode, not a flag.
    if sigil.strict:
        return None
    # Schema migrations run before the field loop and rewrite the payload, so a
    # plan that read the original payload would validate pre-migration data.
    if sigil.revision is not None and sigil.migrate_from:
        return None

    tc = de.TypeCode
    ck = de.ContainerKind
    ff = de.FieldFlags
    plan = de.FieldPlan()
    escaped: set[str] = set()
    building = _building | {contract_cls}

    for fname, spec in sigil.fields.items():
        facet = spec.facet

        # Computed/Constant are skipped by the Python loop and Inject resolves
        # from request context; none is payload-derived. They cost nothing in
        # the Python loop, so escaping them is free and keeps this compiler from
        # having to model three more kinds.
        if isinstance(facet, (Computed, Constant, Inject)):
            escaped.add(fname)
            continue

        if not _field_is_eligible(spec, facet):
            escaped.add(fname)
            continue

        # Nested Contracts compile to a sub-plan that the native field runs over
        # the nested payload. Resolved before the scalar mapping because
        # `list[ItemContract]` is a ListFacet whose child is a nested facet --
        # _facet_type_code would see the ListFacet and find no scalar element.
        nested_plan = None
        if spec.is_nested_contract:
            code, container, nested_plan = _compile_nested(facet, tc, ck, _depth, building)
            if code is None:
                escaped.add(fname)
                continue
        else:
            code, container = _facet_type_code(facet, tc, ck)
            if code is None:
                escaped.add(fname)
                continue

        flags = 0
        if facet.required:
            flags |= ff.REQUIRED
        if facet.allow_null:
            flags |= ff.ALLOW_NULL

        default = facet.default
        has_default = default is not UNSET
        if has_default:
            flags |= ff.HAS_DEFAULT

        if getattr(facet, "trim", False):
            flags |= ff.TRIM
        if getattr(facet, "allow_blank", False):
            flags |= ff.ALLOW_BLANK

        min_length = getattr(facet, "min_length", None)
        max_length = getattr(facet, "max_length", None)
        min_items = getattr(facet, "min_items", None)
        max_items = getattr(facet, "max_items", None)
        max_digits = getattr(facet, "max_digits", None)
        decimal_places = getattr(facet, "decimal_places", None)
        max_keys = getattr(facet, "max_keys", None)
        pattern = getattr(facet, "pattern", None)

        # ChoiceFacet.seal tests `value not in self._valid_values`. Freezing the
        # set once here means the per-request cost is one hash lookup rather
        # than rebuilding a collection per payload. LiteralFacet inherits
        # _valid_values as a one-element set, so it needs no special case.
        choices = None
        if code == tc.CHOICE:
            valid = getattr(facet, "_valid_values", None)
            if valid is None:
                escaped.add(fname)
                continue
            try:
                choices = frozenset(valid)
            except TypeError:
                # An unhashable choice value cannot live in a set -- which means
                # the Python `in` test would raise too. Let Python own it.
                escaped.add(fname)
                continue

        # EnumFacet: hand the native side the two indexes the Enum machinery
        # already maintains rather than building a third. `_value2member_map_`
        # is what EnumMeta.__call__ consults, and `__members__` is what the
        # by-name fallback (`enum_class[value]`) consults, so using them keeps
        # the lookup identical by construction.
        enum_cls = enum_by_value = enum_by_name = None
        if code == tc.ENUM:
            enum_cls = getattr(facet, "enum_class", None)
            try:
                enum_by_value = dict(enum_cls._value2member_map_)
                enum_by_name = dict(enum_cls.__members__)
            except (AttributeError, TypeError):
                escaped.add(fname)
                continue

        plan.add(
            # sys.intern so the native dict lookup hits its pointer-equality
            # fast path rather than comparing string contents per field per
            # payload.
            sys.intern(fname),
            code,
            container,
            flags,
            default if has_default else None,
            getattr(facet, "min_value", None),
            getattr(facet, "max_value", None),
            -1 if min_length is None else int(min_length),
            -1 if max_length is None else int(max_length),
            getattr(facet, "multiple_of", None),
            choices,
            enum_cls,
            enum_by_value,
            enum_by_name,
            -1 if min_items is None else int(min_items),
            -1 if max_items is None else int(max_items),
            -1 if max_digits is None else int(max_digits),
            -1 if decimal_places is None else int(decimal_places),
            # The *compiled* re.Pattern, not the source text. Only an exact
            # TextFacet reaches here -- EmailFacet and friends are subclasses
            # with their own seal overrides, so _facet_type_code declines them.
            pattern,
            nested_plan,
            -1 if max_keys is None else int(max_keys),
        )

    # Nothing native to do. Returning a plan here would add a failed dict lookup
    # per field and a second validate() call for no gain, so this is strictly
    # worse than not having a plan at all.
    if len(plan) == 0:
        return None

    return CompiledPlan(plan, frozenset(escaped))


def field_plan_for(contract_cls: type) -> CompiledPlan | None:
    """Return the cached :class:`CompiledPlan` for a contract, or None.

    One plan per contract class: the Sigil is immutable after class build
    (01 §4.1), so the plan is too.
    """
    if not DATAENGINE_NATIVE:
        return None

    try:
        return _PLAN_CACHE[contract_cls]
    except KeyError:
        pass

    try:
        plan = _build_plan(contract_cls)
    except Exception:
        # Compilation is an optimisation, never a correctness requirement. An
        # unexpected shape anywhere in the Sigil means "use Python", not "fail
        # the request".
        plan = None

    # Under a free-threaded build two threads may build the same plan
    # concurrently. Both are identical and immutable, so one simply wins; no
    # lock is needed (03 §11).
    _PLAN_CACHE[contract_cls] = plan
    return plan
