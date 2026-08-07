"""Micro-benchmarks for the contract validation engine.

Isolates ``Sigil.validate`` from the HTTP stack so the native ``FieldPlan``
speedup is measured directly rather than diluted by transport and middleware.

Each case reports:

``python_us``
    Validation with the native plan disabled (pure-Python field loop).
``native_us``
    Validation with the native plan enabled.
``coverage``
    Fraction of declared fields the native plan handles. Fields it cannot
    represent "escape" back to Python, so coverage bounds the achievable
    speedup: a case at 0.5 coverage can never reach the full native gain.

Run directly::

    python benchmarks/engine/microbench_contracts.py

Exit code is always 0; this is a measurement tool, not a gate. Throughput
gates live in ``benchmarks/run.py``.
"""

from __future__ import annotations

import timeit
from typing import Any

from aquilia.contracts import Contract
from aquilia.contracts._native_plan import _PLAN_CACHE, field_plan_for
from aquilia.contracts.annotations import Field

# Repeat count for timeit; the minimum across repeats is reported to suppress
# scheduler noise, which is the standard practice for microbenchmarks.
REPEATS = 5
ITERATIONS = 20_000


class FlatContract(Contract):
    """All-scalar contract -- the case the native plan covers completely."""

    name: str = Field(min_length=1, max_length=100)
    age: int = Field(ge=0, le=150)
    score: float = Field(ge=0.0, le=100.0)
    active: bool = Field(default=True)


class ListContract(Contract):
    """Homogeneous list fields, covered natively since the list-plan work.

    Declared without ``default_factory`` on purpose. A factory is a Python
    callable, and the engine may never invoke one, so a field carrying it is
    escaped to Python by design -- see ``ListDefaultContract`` below for what
    that costs.
    """

    tags: list[str]
    scores: list[int]


class ListDefaultContract(Contract):
    """Same list fields, but with ``default_factory``.

    Included to keep the cost of that escape visible: it is a real and
    reasonable way to declare a list field, and it forfeits native handling.
    """

    tags: list[str] = Field(default_factory=list)
    scores: list[int] = Field(default_factory=list)


class AddressContract(Contract):
    """Leaf contract used as the nested payload below."""

    street: str = Field(min_length=1, max_length=200)
    city: str = Field(min_length=1, max_length=100)
    zipcode: str = Field(min_length=3, max_length=10)


class NestedContract(Contract):
    """Scalars plus a nested contract.

    The nested field escapes the outer plan, but ``run_nested_contract``
    dispatches through ``AddressContract._sigil.validate``, which has its own
    native plan -- so acceleration still applies one level down.
    """

    name: str = Field(min_length=1, max_length=100)
    age: int = Field(ge=0, le=150)
    address: AddressContract = Field()


CASES: list[tuple[str, type[Contract], dict[str, Any]]] = [
    ("flat_4_scalars", FlatContract, {"name": "Alice", "age": 30, "score": 95.5, "active": True}),
    ("lists", ListContract, {"tags": ["a", "b", "c"], "scores": [1, 2, 3]}),
    ("lists_w_factory", ListDefaultContract, {"tags": ["a", "b", "c"], "scores": [1, 2, 3]}),
    (
        "nested_1_level",
        NestedContract,
        {
            "name": "Bob",
            "age": 25,
            "address": {"street": "1 Main St", "city": "Springfield", "zipcode": "12345"},
        },
    ),
]


def _plan_coverage(contract_cls: type[Contract]) -> tuple[int, int]:
    """Return ``(covered, total)`` field counts for the contract's native plan.

    ``total`` counts declared fields. ``covered`` is ``total`` minus the fields
    the plan reports as escaped. Returns ``(0, total)`` when no plan compiled.
    """
    total = len(contract_cls._sigil.fields)
    compiled = field_plan_for(contract_cls)
    if compiled is None:
        return 0, total
    return total - len(compiled.escaped), total


def _time_validate(contract_cls: type[Contract], payload: dict[str, Any], *, native: bool) -> float:
    """Time one ``Sigil.validate`` call in microseconds.

    ``native=False`` pins the contract's plan-cache entry to ``None`` so
    ``Sigil.validate`` takes the pure-Python field loop. The previous cache
    entry is always restored, including on error, so ordering of the two
    measurements cannot affect the result.
    """
    sigil = contract_cls._sigil
    had_entry = contract_cls in _PLAN_CACHE
    saved = _PLAN_CACHE.get(contract_cls)
    if not native:
        # Nested contracts dispatch through their own sigil, so their plans must
        # be suppressed too or the "python" number stays partly accelerated.
        _PLAN_CACHE[contract_cls] = None
        for spec in sigil.fields.values():
            nested = getattr(spec.facet, "contract_cls", None)
            if isinstance(nested, type):
                _PLAN_CACHE[nested] = None
    try:
        samples = timeit.repeat(
            lambda: sigil.validate(payload),
            number=ITERATIONS,
            repeat=REPEATS,
        )
    finally:
        if had_entry:
            _PLAN_CACHE[contract_cls] = saved
        else:
            _PLAN_CACHE.pop(contract_cls, None)
        for spec in sigil.fields.values():
            nested = getattr(spec.facet, "contract_cls", None)
            if isinstance(nested, type):
                _PLAN_CACHE.pop(nested, None)
    return min(samples) / ITERATIONS * 1e6


def main() -> None:
    """Measure and print the native-plan speedup for every case."""
    print("=" * 78)
    print("Contract validation -- native FieldPlan vs pure Python (us per validate)")
    print("=" * 78)
    print(f"{'case':<18}{'python':>10}{'native':>10}{'speedup':>10}{'coverage':>12}")
    print("-" * 78)

    for label, contract_cls, payload in CASES:
        # Warm the plan and prove the payload is valid before timing it, so a
        # silent validation failure cannot be mistaken for a fast path.
        errors, _ = contract_cls._sigil.validate(payload)
        assert not errors, f"{label} payload rejected: {errors}"

        py_us = _time_validate(contract_cls, payload, native=False)
        nat_us = _time_validate(contract_cls, payload, native=True)
        speedup = py_us / nat_us if nat_us > 0 else 0.0
        covered, total = _plan_coverage(contract_cls)

        print(
            f"{label:<18}{py_us:>9.2f}{nat_us:>10.2f}{speedup:>9.2f}x"
            f"{covered:>8}/{total:<4}"
        )

    print("-" * 78)
    print("speedup < 1.00x means the plan is not helping -- investigate coverage.")


if __name__ == "__main__":
    main()
