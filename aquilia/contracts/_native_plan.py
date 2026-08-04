"""Compile a Contract's Sigil into a native FieldPlan, when it is safe to.

This module owns **eligibility** -- the rule that keeps the native validation
path safe (``docs/models-engine/03-engine-design.md`` §8). A plan compiles only
when every field is representable; if any field is not, the whole plan is
rejected and the contract keeps the pure-Python path forever.

There is deliberately no such thing as a partial plan. A mixed path would be a
second implementation of the same semantics that could silently diverge, so the
choice is made once, per contract, at first use.

Two independent layers of conservatism:

1. **Compile time (here).** A facet with a pipeline, validators, a
   ``default_factory``, a regex pattern, or a custom subclass never produces a
   plan at all.
2. **Run time (fieldplan.cpp).** Even within a compiled plan, any *value* the
   native code cannot decide with certainty aborts the payload back to
   ``Sigil.validate``. That is what makes error messages byte-identical and
   correctly localised: failures are always rendered by the Python path.
"""

from __future__ import annotations

from typing import Any

from aquilia._dataengine_loader import DATAENGINE_NATIVE, native_module

__all__ = ["field_plan_for", "plan_cache_size"]


# Contract class -> FieldPlan, or None when the contract is ineligible. The
# None entries matter as much as the plans: they stop a rejected contract from
# being re-analysed on every request.
#
# Keyed by the class object itself. Plans are immutable once built, and dev-mode
# hot reload creates new classes which miss the cache naturally, so there is no
# invalidation path and therefore no staleness bug (03 §11).
_PLAN_CACHE: dict[type, Any] = {}


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
    """Every condition that forces a field -- and so its whole plan -- to Python."""
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


def _build_plan(contract_cls: type) -> Any:
    """Compile, or return None when any field is ineligible."""
    de = native_module()
    if de is None:
        return None

    from aquilia.contracts.facets import UNSET, Computed, Constant, Inject

    sigil = getattr(contract_cls, "_sigil", None)
    if sigil is None:
        return None

    # strict mode has *different* semantics -- cast is skipped entirely
    # (sigil.py) -- so it is a separate execution mode, not a flag.
    if sigil.strict:
        return None
    # Schema migrations run before the field loop and rewrite the payload.
    if sigil.revision is not None and sigil.migrate_from:
        return None

    tc = de.TypeCode
    ff = de.FieldFlags
    plan = de.FieldPlan()

    for fname, spec in sigil.fields.items():
        facet = spec.facet

        # Computed/Constant are skipped by the Python loop and Inject resolves
        # from request context; none is payload-derived.
        if isinstance(facet, (Computed, Constant, Inject)):
            return None

        if not _field_is_eligible(spec, facet):
            return None

        code = _facet_type_code(facet, tc)
        if code is None:
            return None

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
            _intern(fname),
            code,
            flags,
            default if has_default else None,
            getattr(facet, "min_value", None),
            getattr(facet, "max_value", None),
            -1 if min_length is None else int(min_length),
            -1 if max_length is None else int(max_length),
        )

    # A contract with no eligible fields would "succeed" trivially on every
    # payload, which is not a useful fast path and hides mistakes.
    if len(plan) == 0:
        return None

    return plan


def _intern(s: str) -> str:
    import sys

    return sys.intern(s)


def field_plan_for(contract_cls: type) -> Any:
    """Return the cached FieldPlan for a contract, or None if it is ineligible.

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
