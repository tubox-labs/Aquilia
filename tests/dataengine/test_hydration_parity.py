"""Hydration parity, led by the data-loss gate.

``docs/models-engine/07-testing-strategy.md`` §3.1 identifies the highest-risk
defect in this whole project, and it is not a crash:

    if ``_original_values`` is wrong, ``save()`` either writes columns that did
    not change or **silently skips columns that did**. The second is data loss,
    and no existing test would catch it, because today's tests hydrate and save
    through the same code path.

So the first tests in this file compare a natively-hydrated instance against a
Python-hydrated one field by field, and then compare what ``save()`` would
actually write. Everything else follows.
"""

from __future__ import annotations

import gc
import uuid
from datetime import datetime
from decimal import Decimal

import pytest

from aquilia._dataengine_loader import DATAENGINE_NATIVE
from aquilia.models import Model
from aquilia.models._native_plan import row_plan_for
from aquilia.models.fields_module import (
    BooleanField,
    CharField,
    DateField,
    DateTimeField,
    DecimalField,
    FloatField,
    IntegerField,
    JSONField,
    TextField,
    UUIDField,
)

pytestmark = pytest.mark.skipif(not DATAENGINE_NATIVE, reason="native data engine not built")


class Wide(Model):
    name = CharField(max_length=100)
    count = IntegerField()
    ratio = FloatField()
    active = BooleanField()
    created = DateTimeField(null=True)
    started = DateField(null=True)
    price = DecimalField(max_digits=10, decimal_places=2, null=True)
    ident = UUIDField(null=True)
    payload = JSONField(null=True)
    notes = TextField(null=True)

    class Meta:
        table_name = "de_wide"
        app_label = "dataengine_tests"


ROW = {
    "id": 1,
    "name": "alice",
    "count": 42,
    "ratio": 1.5,
    "active": 1,
    "created": "2026-01-15T10:30:00",
    "started": "2026-01-15",
    "price": "19.99",
    "ident": "550e8400-e29b-41d4-a716-446655440000",
    "payload": '{"k": "v"}',
    "notes": "hello",
}

ATTRS = ("id", "name", "count", "ratio", "active", "created", "started", "price", "ident", "payload", "notes")


def _plan():
    plan = row_plan_for(Wide, tuple(ROW.keys()))
    assert plan is not None, "Wide must be eligible or these tests prove nothing"
    return plan


def _both(row):
    """Hydrate the same row natively and in Python."""
    native = _plan().execute([dict(row)])
    assert native is not None, "expected the native path to handle this row"
    return native[0], Wide.from_row(dict(row))


# ---------------------------------------------------------------------------
# The data-loss gate -- 07 §3.1
# ---------------------------------------------------------------------------


def test_original_values_are_identical():
    native, python = _both(ROW)
    assert native._original_values == python._original_values
    assert set(native._original_values) == set(python._original_values)
    for key, value in native._original_values.items():
        assert type(value) is type(python._original_values[key]), key


def test_save_after_native_hydration_reports_identical_dirty_fields():
    """A native-hydrated instance must produce the same UPDATE as a
    Python-hydrated one. This is the data-loss gate."""
    native, python = _both(ROW)
    native.name = "changed"
    python.name = "changed"
    assert native.get_dirty_fields() == python.get_dirty_fields() == {"name": "changed"}


def test_untouched_instance_has_no_dirty_fields():
    """If the snapshot held raw rather than converted values, every parsed
    column would read back as spuriously dirty."""
    native, python = _both(ROW)
    assert native.get_dirty_fields() == python.get_dirty_fields() == {}


@pytest.mark.parametrize("attr", ["count", "ratio", "created", "price", "ident", "payload"])
def test_dirty_tracking_per_column(attr):
    native, python = _both(ROW)
    assert native.get_dirty_fields() == python.get_dirty_fields()
    new_value = {
        "count": 99,
        "ratio": 9.9,
        "created": datetime(2030, 1, 1),
        "price": Decimal("1.00"),
        "ident": uuid.uuid4(),
        "payload": {"z": 1},
    }[attr]
    setattr(native, attr, new_value)
    setattr(python, attr, new_value)
    assert native.get_dirty_fields() == python.get_dirty_fields()


def test_setting_a_field_to_its_existing_value_is_not_dirty():
    native, python = _both(ROW)
    native.name = native.name
    python.name = python.name
    assert native.get_dirty_fields() == python.get_dirty_fields()


# ---------------------------------------------------------------------------
# Attribute parity
# ---------------------------------------------------------------------------


def test_all_attributes_match_python():
    native, python = _both(ROW)
    for attr in ATTRS:
        n, p = getattr(native, attr), getattr(python, attr)
        assert n == p, attr
        assert type(n) is type(p), attr


def test_decimal_exponent_is_preserved():
    """Decimal("19.99") and Decimal("19.990") compare equal but are not
    interchangeable -- exponent is part of the value for money."""
    native, python = _both(ROW)
    assert native.price.as_tuple() == python.price.as_tuple() == Decimal("19.99").as_tuple()


@pytest.mark.parametrize(
    "override",
    [
        {"count": 0},
        {"count": -1},
        {"count": 123456789012345678901234567890},
        {"ratio": 0.0},
        {"active": 0},
        {"created": None},
        {"created": ""},  # blank string -> None, per DateTimeField.to_python
        {"started": None},
        {"price": None},
        {"price": ""},
        {"price": "0.00"},
        {"ident": None},
        {"ident": ""},
        {"payload": None},
        {"payload": "[]"},
        {"payload": "not json"},  # JSONField returns unparseable input as-is
        {"notes": None},
        {"name": "unicode: café ☕"},
        {"name": ""},
    ],
)
def test_value_variants_match_python(override):
    row = {**ROW, **override}
    native_batch = _plan().execute([dict(row)])
    python = Wide.from_row(dict(row))
    if native_batch is None:
        return  # deferred to Python, which is always correct
    native = native_batch[0]
    for attr in ATTRS:
        assert getattr(native, attr) == getattr(python, attr), attr
        assert type(getattr(native, attr)) is type(getattr(python, attr)), attr
    assert native._original_values == python._original_values


def test_null_columns_stay_none():
    row = {**ROW, "created": None, "price": None, "ident": None, "payload": None, "notes": None}
    native, python = _both(row)
    for attr in ("created", "price", "ident", "payload", "notes"):
        assert getattr(native, attr) is None
        assert getattr(python, attr) is None


# ---------------------------------------------------------------------------
# Signals -- 04 §3.1, hydration bypasses __init__
# ---------------------------------------------------------------------------


def test_hydration_fires_no_init_signals():
    """from_row uses cls.__new__(cls), so pre_init/post_init do not fire today.
    A native path that constructed instances differently would emit 2,000
    spurious dispatches per 1,000-row page."""
    from aquilia.models import signals

    calls = []

    def listener(**kwargs):
        calls.append(kwargs)

    for name in ("pre_init", "post_init"):
        sig = getattr(signals, name, None)
        if sig is not None and hasattr(sig, "connect"):
            sig.connect(listener)

    _plan().execute([dict(ROW)] * 100)
    assert calls == []


# ---------------------------------------------------------------------------
# Batch semantics
# ---------------------------------------------------------------------------


def test_batch_hydration_matches_row_by_row():
    rows = [{**ROW, "id": i, "count": i} for i in range(50)]
    native = _plan().execute([dict(r) for r in rows])
    python = [Wide.from_row(dict(r)) for r in rows]
    assert native is not None
    assert len(native) == len(python) == 50
    for n, p in zip(native, python, strict=True):
        assert n.id == p.id
        assert n.count == p.count
        assert n._original_values == p._original_values


def test_empty_batch():
    assert _plan().execute([]) == []


def test_instances_are_independent():
    rows = [{**ROW, "id": i} for i in range(10)]
    out = _plan().execute([dict(r) for r in rows])
    for i, inst in enumerate(out):
        assert inst.id == i
    out[0].name = "mutated"
    assert out[1].name == "alice"


def test_hydrated_instance_is_the_right_class():
    native, python = _both(ROW)
    assert type(native) is type(python) is Wide


# ---------------------------------------------------------------------------
# Eligibility
# ---------------------------------------------------------------------------


def test_plan_is_cached_per_model_and_shape():
    keys = tuple(ROW.keys())
    assert row_plan_for(Wide, keys) is row_plan_for(Wide, keys)


def test_partial_row_is_ineligible():
    """Deferred fields need the guard-class swap, excluded from v1. An absent
    column must never become None -- indistinguishable from a real SQL NULL."""
    assert row_plan_for(Wide, ("id", "name")) is None


def test_unmapped_column_is_ineligible():
    """Annotations and select_related aliases arrive as unmapped keys."""
    assert row_plan_for(Wide, (*ROW.keys(), "annotated_total")) is None


def test_custom_to_python_subclass_is_ineligible():
    class WeirdField(CharField):
        def to_python(self, value):  # noqa: ANN001, ANN201
            return f"weird:{value}"

    class WithWeird(Model):
        odd = WeirdField(max_length=10)

        class Meta:
            table_name = "de_weird"
            app_label = "dataengine_tests"

    assert row_plan_for(WithWeird, ("id", "odd")) is None


def test_non_list_rows_fall_back():
    assert _plan().execute(tuple([dict(ROW)])) is None


# ---------------------------------------------------------------------------
# Memory -- 07 §7 asserts on growth, not absolute counts
# ---------------------------------------------------------------------------


def test_no_object_growth_over_100k_rows():
    plan = _plan()
    rows = [dict(ROW) for _ in range(100)]
    for _ in range(10):
        plan.execute(rows)
    gc.collect()
    before = len(gc.get_objects())
    for _ in range(1000):
        plan.execute(rows)
    gc.collect()
    assert len(gc.get_objects()) - before < 100


def test_hydrated_instances_are_collectable():
    import weakref

    out = _plan().execute([dict(ROW)])
    ref = weakref.ref(out[0])
    del out
    gc.collect()
    assert ref() is None


def test_row_refcount_is_balanced():
    import sys

    plan = _plan()
    name = "a-distinct-string-for-refcounting"
    row = {**ROW, "name": name}
    plan.execute([dict(row)])
    gc.collect()
    before = sys.getrefcount(name)
    for _ in range(5_000):
        out = plan.execute([dict(row)])
        del out
    gc.collect()
    assert sys.getrefcount(name) == before
