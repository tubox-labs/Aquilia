"""Performance gates -- regression detectors, not aspirations.

``docs/models-engine/07-testing-strategy.md`` §9 and ``08`` §4 set the shape of
this file. Budgets are the *measured* post-native numbers plus headroom, so a
failure means something regressed rather than that a target was ambitious.

Marked ``slow`` and excluded from the default run: a 200 ns measurement on a
shared CI runner is noise, and a gate that fails spuriously gets ignored, which
is worse than not having it. Run nightly, or explicitly:

    pytest tests/dataengine/test_perf_gates.py -m slow -q

The ratio assertions matter more than the absolute ones. An absolute budget
tuned on an M-series laptop will fail on a slower runner; "native must beat
Python" holds on any hardware.
"""

from __future__ import annotations

import timeit
import uuid
from datetime import date, datetime

import pytest

from aquilia._dataengine_loader import DATAENGINE_NATIVE
from aquilia.contracts import Contract
from aquilia.contracts._native_plan import field_plan_for
from aquilia.models import Model
from aquilia.models._native_plan import row_plan_for
from aquilia.models.fields_module import (
    BooleanField,
    CharField,
    DateTimeField,
    DecimalField,
    FloatField,
    IntegerField,
    JSONField,
    UUIDField,
)

pytestmark = [
    pytest.mark.slow,
    pytest.mark.skipif(not DATAENGINE_NATIVE, reason="native data engine not built"),
]

# Measured values plus ~60% headroom, which is roughly the spread between a
# quiet laptop and a busy shared runner.
GATES_NS = {
    "hydrate_row_9col": 1_500,
    "validate_payload_8f": 1_800,
}
GATES_US = {
    "hydrate_100_rows": 150,
    "validate_100_payloads": 150,
}


class PerfWide(Model):
    name = CharField(max_length=100)
    count = IntegerField()
    ratio = FloatField()
    active = BooleanField()
    created = DateTimeField(null=True)
    price = DecimalField(max_digits=10, decimal_places=2, null=True)
    ident = UUIDField(null=True)
    payload = JSONField(null=True)

    class Meta:
        table_name = "de_perf_wide"
        app_label = "dataengine_perf"


class PerfPayload(Contract):
    name: str
    count: int
    ratio: float
    active: bool
    created: datetime
    start: date
    ident: uuid.UUID
    city: str


ROW = {
    "id": 1,
    "name": "alice",
    "count": 42,
    "ratio": 1.5,
    "active": 1,
    "created": "2026-01-15T10:30:00",
    "price": "19.99",
    "ident": "550e8400-e29b-41d4-a716-446655440000",
    "payload": '{"k": "v"}',
}

PAYLOAD = {
    "name": "alice",
    "count": 42,
    "ratio": 1.5,
    "active": True,
    "created": "2026-01-15T10:30:00",
    "start": "2026-01-15",
    "ident": "550e8400-e29b-41d4-a716-446655440000",
    "city": "NYC",
}


def _ns(fn, number):
    """Best-of-5 nanoseconds per call. Minimum, because noise only adds time."""
    return min(timeit.repeat(fn, repeat=5, number=number)) / number * 1e9


def _row_plan():
    plan = row_plan_for(PerfWide, tuple(ROW.keys()))
    assert plan is not None, "PerfWide must stay eligible or this gate measures nothing"
    return plan


def _field_plan():
    plan = field_plan_for(PerfPayload).plan
    assert plan is not None, "PerfPayload must stay eligible or this gate measures nothing"
    return plan


# ---------------------------------------------------------------------------
# Absolute budgets
# ---------------------------------------------------------------------------


def test_hydrate_row_budget():
    plan = _row_plan()
    rows = [dict(ROW)]
    got = _ns(lambda: plan.execute(rows), 20_000)
    assert got <= GATES_NS["hydrate_row_9col"], f"{got:.0f} ns > {GATES_NS['hydrate_row_9col']} ns"


def test_hydrate_100_rows_budget():
    plan = _row_plan()
    rows = [dict(ROW) for _ in range(100)]
    got = _ns(lambda: plan.execute(rows), 300) / 1000
    assert got <= GATES_US["hydrate_100_rows"], f"{got:.1f} us > {GATES_US['hydrate_100_rows']} us"


def test_validate_payload_budget():
    plan = _field_plan()
    got = _ns(lambda: plan.execute(PAYLOAD), 20_000)
    assert got <= GATES_NS["validate_payload_8f"], f"{got:.0f} ns > {GATES_NS['validate_payload_8f']} ns"


def test_validate_100_payloads_budget():
    plan = _field_plan()
    got = _ns(lambda: [plan.execute(PAYLOAD) for _ in range(100)], 200) / 1000
    assert got <= GATES_US["validate_100_payloads"], f"{got:.1f} us > {GATES_US['validate_100_payloads']} us"


# ---------------------------------------------------------------------------
# Ratio assertions -- machine-independent, so these are the ones that hold
# everywhere and the ones worth trusting on shared CI.
# ---------------------------------------------------------------------------


def test_native_hydration_beats_python():
    plan = _row_plan()
    rows = [dict(ROW) for _ in range(100)]
    from_row = PerfWide.from_row
    native = _ns(lambda: plan.execute(rows), 300)
    python = _ns(lambda: [from_row(r) for r in rows], 300)
    assert native < python, f"native {native:.0f} ns is not faster than python {python:.0f} ns"


def test_native_validation_beats_python():
    plan = _field_plan()
    sigil = PerfPayload._sigil
    native = _ns(lambda: plan.execute(PAYLOAD), 20_000)
    python = _ns(lambda: sigil.validate(PAYLOAD), 20_000)
    assert native < python, f"native {native:.0f} ns is not faster than python {python:.0f} ns"


# ---------------------------------------------------------------------------
# Correctness measurements that are numeric but not about speed (08 §5)
# ---------------------------------------------------------------------------


def test_plan_cache_is_bounded_by_distinct_shapes():
    """The cache is keyed on (model, row shape), so repeated queries of the same
    shape must not grow it."""
    from aquilia.models import _native_plan as np

    keys = tuple(ROW.keys())
    before = np.plan_cache_size()
    for _ in range(1_000):
        row_plan_for(PerfWide, keys)
    assert np.plan_cache_size() == before


def test_plan_build_cost_is_amortised():
    """If building a plan cost more than ~100 hydrations, caching it across
    queries would be the only thing making it worthwhile -- so check it is not
    absurd relative to the work it saves."""
    from aquilia.models import _native_plan as np

    keys = tuple(ROW.keys())
    build = _ns(lambda: np._build_plan(PerfWide, keys), 200)
    plan = _row_plan()
    rows = [dict(ROW) for _ in range(100)]
    one_batch = _ns(lambda: plan.execute(rows), 200)
    assert build < one_batch * 10, f"plan build {build:.0f} ns vs one 100-row batch {one_batch:.0f} ns"
