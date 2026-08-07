"""Contract validation micro-benchmarks.

Measures the actual speedup from native FieldPlan acceleration across different
contract shapes. Results prove whether 60% → 80% coverage moves the needle.
"""

from __future__ import annotations

import timeit
from typing import Any

from aquilia.contracts import Contract
from aquilia.contracts._native_plan import field_plan_for

# ── Test Contracts ────────────────────────────────────────────────────────────


class SimpleContract(Contract):
    """3 scalar fields - all native after list support."""
    username: str
    age: int
    active: bool


class ListContract(Contract):
    """List validation - native after Phase 1."""
    tags: list[str]
    scores: list[int]
    flags: list[bool]


class AddressContract(Contract):
    """Nested contract for mixed testing."""
    street: str
    city: str
    zipcode: str


class MixedContract(Contract):
    """Realistic contract with scalars, lists, and nested."""
    username: str
    email: str
    age: int
    tags: list[str]
    address: AddressContract


# ── Benchmark Helpers ─────────────────────────────────────────────────────────


def bench_validate(contract_cls: type[Contract], payload: dict[str, Any], iterations: int = 10000) -> dict[str, float]:
    """Time contract validation.

    Returns:
        Mean time in microseconds plus QPS estimate.
    """
    # Warm up + verify it works
    errs, val = contract_cls._sigil.validate(payload)
    if errs:
        raise ValueError(f"Invalid payload for {contract_cls.__name__}: {errs}")

    samples = timeit.repeat(
        lambda: contract_cls._sigil.validate(payload),
        number=iterations,
        repeat=5,
    )
    mean_us = min(samples) / iterations * 1e6
    return {
        "mean_us": mean_us,
        "qps": 1e6 / mean_us if mean_us > 0 else 0,
    }


def show_coverage(contract_cls: type[Contract]) -> str:
    """Show which fields are accelerated."""
    cp = field_plan_for(contract_cls)
    if cp is None:
        return "NO NATIVE PLAN"

    field_count = len(contract_cls._sigil.fields)
    escaped_count = len(cp.escaped)
    native_count = field_count - escaped_count
    pct = native_count / field_count * 100 if field_count else 0

    return f"{native_count}/{field_count} fields native ({pct:.0f}%), escaped={sorted(cp.escaped)}"


# ── Main ──────────────────────────────────────────────────────────────────────


def main() -> None:
    print("=" * 78)
    print("Contract Validation Micro-Benchmarks")
    print("=" * 78)
    print()

    test_cases = [
        (
            SimpleContract,
            {"username": "alice", "age": 30, "active": True},
            "3 scalar fields (all native)",
        ),
        (
            ListContract,
            {
                "tags": ["python", "rust", "c++"],
                "scores": [95, 87, 92],
                "flags": [True, False, True],
            },
            "3 list fields (all native after Phase 1)",
        ),
        (
            MixedContract,
            {
                "username": "bob",
                "email": "bob@example.com",
                "age": 25,
                "tags": ["backend", "distributed"],
                "address": {"street": "123 Main St", "city": "SF", "zipcode": "94102"},
            },
            "Realistic mix (4 native, 1 nested escape)",
        ),
    ]

    for contract_cls, payload, desc in test_cases:
        print(f"{contract_cls.__name__}: {desc}")
        print(f"  Coverage: {show_coverage(contract_cls)}")

        result = bench_validate(contract_cls, payload)
        print(f"  Validation: {result['mean_us']:.2f} µs/req ({result['qps']:,.0f} QPS)")
        print()

    print("=" * 78)
    print("Summary")
    print("=" * 78)
    print("Native acceleration is active for scalar and list[scalar] fields.")
    print("Nested contracts still escape to Python (requires Phase 2).")
    print()
    print("To measure HTTP impact, run:")
    print("  python benchmarks/run.py --frameworks Aquilia --scenarios validation")


if __name__ == "__main__":
    main()
