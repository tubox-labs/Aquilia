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


def _facet_type_code(facet: Any, tc: Any) -> int | None:
    """Map a facet to its TypeCode, or None when it is not representable.

    Uses ``type(facet) is X`` rather than isinstance, per 05 §2.3.1: a subclass
    may override ``cast``/``seal``, and running the base semantics against a
    subclass that redefined them is exactly the silent divergence this whole
    design is built to avoid.
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

    exact = type(facet)
    if exact is TextFacet:
        return tc.STR
    if exact is IntFacet:
        return tc.INT
    if exact is FloatFacet:
        return tc.FLOAT
    if exact is BoolFacet:
        return tc.BOOL
    if exact is UUIDFacet:
        return tc.UUID
    if exact is DateFacet:
        return tc.DATE
    if exact is DateTimeFacet:
        return tc.DATETIME
    if exact is TimeFacet:
        return tc.TIME
    # DecimalFacet is omitted from v1: its seal() enforces max_digits and
    # decimal_places, which need exponent-aware inspection that is not worth
    # reproducing natively for a conversion already measured at parity with one
    # boundary crossing.
    return None


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
    if spec.is_nested_contract:
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

    # Constraints this plan does not model. A pattern needs the regex engine;
    # choices and multiple_of need comparisons whose error text differs per case.
    if getattr(facet, "pattern", None) is not None:
        return False
    if getattr(facet, "choices", None):
        return False
    if getattr(facet, "multiple_of", None) is not None:
        return False

    return True


def _build_plan(contract_cls: type) -> CompiledPlan | None:
    """Compile the representable fields; escape the rest to Python."""
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
    ff = de.FieldFlags
    plan = de.FieldPlan()
    escaped: set[str] = set()

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

        code = _facet_type_code(facet, tc)
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

        plan.add(
            # sys.intern so the native dict lookup hits its pointer-equality
            # fast path rather than comparing string contents per field per
            # payload.
            sys.intern(fname),
            code,
            flags,
            default if has_default else None,
            getattr(facet, "min_value", None),
            getattr(facet, "max_value", None),
            -1 if min_length is None else int(min_length),
            -1 if max_length is None else int(max_length),
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
