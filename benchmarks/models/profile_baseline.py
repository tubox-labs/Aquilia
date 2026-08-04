"""Baseline measurements for the models / db / contracts hot paths.

Purpose: establish, with evidence, where per-row and per-payload time actually
goes before any native engine is designed. The Phase 9 engine work showed that
design documents written from assumed costs get the target wrong -- the binding
overhead was assumed at ~60 ns and measured at 7.7 ns, which inverted three
component decisions.

The two candidate hot paths:

  1. Row -> model hydration   Model.from_row()  (aquilia/models/base.py:2045)
     Per row: one dict.get per column, one field.to_python, one descriptor
     __set__, plus a dict write for the dirty-tracking snapshot.

  2. Payload -> validated     Sigil.validate()  (aquilia/contracts/sigil.py:169)
     Per field: get_field_value, then facet.cast + facet.seal.

Run:  python benchmarks/models/profile_baseline.py
      python benchmarks/models/profile_baseline.py --json out.json
"""

from __future__ import annotations

import argparse
import cProfile
import io
import json
import pstats
import sys
import timeit
import uuid
from datetime import date, datetime
from decimal import Decimal
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

REPEAT = 5
RESULTS: dict[str, float] = {}


def bench(label: str, stmt, *, number: int, setup=None) -> float:
    """Best-of-REPEAT nanoseconds per operation.

    Minimum rather than mean: these are CPU-bound, so every noise source
    (scheduling, thermal, other processes) only ever adds time.
    """
    timer = timeit.Timer(stmt, setup=setup) if setup else timeit.Timer(stmt)
    per_op = min(timer.repeat(REPEAT, number)) / number
    RESULTS[label] = per_op * 1e9
    return per_op * 1e9


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


def build_model():
    """A model with a realistic field mix: cheap and expensive to_python()."""
    from aquilia.models import Model
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

    class Wide(Model):
        # cheap: to_python is a pass-through
        name = CharField(max_length=100)
        count = IntegerField()
        ratio = FloatField()
        active = BooleanField()
        # expensive: to_python parses
        created = DateTimeField(null=True)
        price = DecimalField(max_digits=10, decimal_places=2, null=True)
        ident = UUIDField(null=True)
        payload = JSONField(null=True)

        class Meta:
            table_name = "wide"
            app_label = "bench"

    return Wide


def build_contract():
    from aquilia.contracts import Contract

    class Payload(Contract):
        name: str
        count: int
        ratio: float
        active: bool
        created: datetime
        price: Decimal
        ident: uuid.UUID
        start: date

    return Payload


ROW_CHEAP = {"name": "alice", "count": 42, "ratio": 1.5, "active": 1}
ROW_FULL = {
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
    "count": "42",
    "ratio": "1.5",
    "active": "true",
    "created": "2026-01-15T10:30:00",
    "price": "19.99",
    "ident": "550e8400-e29b-41d4-a716-446655440000",
    "start": "2026-01-15",
}


# ---------------------------------------------------------------------------
# Hot path 1 -- row hydration
# ---------------------------------------------------------------------------


def bench_hydration(Wide) -> None:  # noqa: N803 - a model class
    print("\n-- row -> model hydration (Model.from_row) --")

    from_row = Wide.from_row
    bench("from_row_cheap_4col_ns", lambda: from_row(ROW_CHEAP), number=20_000)
    bench("from_row_full_8col_ns", lambda: from_row(ROW_FULL), number=20_000)

    # Per-component decomposition, so the design targets the real cost.
    fields = dict(Wide._non_m2m_fields)
    cheap_field = fields["name"]
    dt_field = fields["created"]
    dec_field = fields["price"]
    uuid_field = fields["ident"]
    json_field = fields["payload"]

    bench("to_python_char_ns", lambda: cheap_field.to_python("alice"), number=200_000)
    bench("to_python_datetime_ns", lambda: dt_field.to_python("2026-01-15T10:30:00"), number=100_000)
    bench("to_python_decimal_ns", lambda: dec_field.to_python("19.99"), number=100_000)
    bench("to_python_uuid_ns", lambda: uuid_field.to_python("550e8400-e29b-41d4-a716-446655440000"), number=100_000)
    bench("to_python_json_ns", lambda: json_field.to_python('{"k": "v"}'), number=100_000)

    # The descriptor write and the raw dict write it wraps.
    inst = Wide.from_row(ROW_CHEAP)
    bench("descriptor_set_ns", lambda: setattr(inst, "name", "bob"), number=200_000)
    d = inst.__dict__
    bench("raw_dict_write_ns", lambda: d.__setitem__("name", "bob"), number=200_000)

    # Batch shape: what a 100-row page actually costs.
    rows_cheap = [ROW_CHEAP] * 100
    rows_full = [ROW_FULL] * 100
    bench("hydrate_100_cheap_us", lambda: [from_row(r) for r in rows_cheap], number=500)
    bench("hydrate_100_full_us", lambda: [from_row(r) for r in rows_full], number=500)

    for k in (
        "from_row_cheap_4col_ns",
        "from_row_full_8col_ns",
        "to_python_char_ns",
        "to_python_datetime_ns",
        "to_python_decimal_ns",
        "to_python_uuid_ns",
        "to_python_json_ns",
        "descriptor_set_ns",
        "raw_dict_write_ns",
    ):
        print(f"  {k:34} {RESULTS[k]:10.1f} ns")
    for k in ("hydrate_100_cheap_us", "hydrate_100_full_us"):
        print(f"  {k:34} {RESULTS[k] / 1000:10.2f} us")


# ---------------------------------------------------------------------------
# Hot path 2 -- contract validation
# ---------------------------------------------------------------------------


def bench_contracts(Payload) -> None:  # noqa: N803 - a contract class
    print("\n-- payload -> validated (Sigil.validate / Contract.is_sealed) --")

    sigil = Payload._sigil
    bench("sigil_validate_8field_ns", lambda: sigil.validate(PAYLOAD), number=10_000)
    bench("contract_is_sealed_8field_ns", lambda: Payload(data=PAYLOAD).is_sealed(), number=10_000)
    bench("contract_construct_ns", lambda: Payload(data=PAYLOAD), number=20_000)

    # Facet cast+seal in isolation, the per-field unit the native engine targets.
    facets = {name: spec.facet for name, spec in sigil.fields.items()}

    def cast_seal(facet, raw):
        return facet.seal(facet.cast(raw))

    for label, fname, raw in (
        ("facet_text_ns", "name", "alice"),
        ("facet_int_ns", "count", "42"),
        ("facet_float_ns", "ratio", "1.5"),
        ("facet_bool_ns", "active", "true"),
        ("facet_datetime_ns", "created", "2026-01-15T10:30:00"),
        ("facet_decimal_ns", "price", "19.99"),
        ("facet_uuid_ns", "ident", "550e8400-e29b-41d4-a716-446655440000"),
        ("facet_date_ns", "start", "2026-01-15"),
    ):
        f = facets.get(fname)
        if f is None:
            continue
        bench(label, lambda f=f, raw=raw: cast_seal(f, raw), number=100_000)

    # get_field_value: called once per field per payload.
    from aquilia.contracts.sigil import get_field_value

    name_facet = facets["name"]
    bench("get_field_value_ns", lambda: get_field_value(PAYLOAD, "name", name_facet), number=200_000)

    # Batch: validating a 100-item list payload.
    bench("validate_100_payloads_us", lambda: [sigil.validate(PAYLOAD) for _ in range(100)], number=100)

    for k in sorted(RESULTS):
        if k.startswith(("sigil_", "contract_", "facet_", "get_field")):
            print(f"  {k:34} {RESULTS[k]:10.1f} ns")
    print(f"  {'validate_100_payloads_us':34} {RESULTS['validate_100_payloads_us'] / 1000:10.2f} us")


# ---------------------------------------------------------------------------
# Hot path 3 -- SQL generation
# ---------------------------------------------------------------------------


def bench_sql() -> None:
    print("\n-- SQL generation --")
    from aquilia.models.sql_builder import SQLBuilder

    def simple():
        return (
            SQLBuilder()
            .select("id", "name")
            .from_table("users")
            .where("active = ?", True)
            .order_by("name")
            .limit(10)
            .build()
        )

    def complex_q():
        b = SQLBuilder().select("u.id", "u.name", "p.title").from_table("users u")
        b.join("posts p", on="p.user_id = u.id")
        for i in range(5):
            b.where(f"u.col{i} = ?", i)
        return b.order_by("u.name").limit(50).build()

    bench("sql_build_simple_ns", simple, number=20_000)
    bench("sql_build_complex_ns", complex_q, number=10_000)
    for k in ("sql_build_simple_ns", "sql_build_complex_ns"):
        print(f"  {k:34} {RESULTS[k]:10.1f} ns")


# ---------------------------------------------------------------------------
# Profile: where does hydration actually spend its time?
# ---------------------------------------------------------------------------


def profile_hydration(Wide) -> None:  # noqa: N803 - a model class
    print("\n-- cProfile: 5,000 x from_row (full 8-column row) --")
    rows = [ROW_FULL] * 5_000
    from_row = Wide.from_row
    prof = cProfile.Profile()
    prof.enable()
    for r in rows:
        from_row(r)
    prof.disable()
    buf = io.StringIO()
    pstats.Stats(prof, stream=buf).sort_stats("tottime").print_stats(18)
    for line in buf.getvalue().splitlines():
        if line.strip() and ("aquilia" in line or "ncalls" in line or "{" in line):
            print("  " + line.rstrip())


def profile_validate(Payload) -> None:  # noqa: N803 - a contract class
    print("\n-- cProfile: 5,000 x Sigil.validate (8 fields) --")
    sigil = Payload._sigil
    prof = cProfile.Profile()
    prof.enable()
    for _ in range(5_000):
        sigil.validate(PAYLOAD)
    prof.disable()
    buf = io.StringIO()
    pstats.Stats(prof, stream=buf).sort_stats("tottime").print_stats(18)
    for line in buf.getvalue().splitlines():
        if line.strip() and ("aquilia" in line or "ncalls" in line or "{" in line):
            print("  " + line.rstrip())


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--json", type=Path, help="write raw results here")
    args = ap.parse_args()

    print("=" * 78)
    print("MODELS / DB / CONTRACTS BASELINE")
    print("=" * 78)

    Wide = build_model()
    Payload = build_contract()

    bench_hydration(Wide)
    bench_contracts(Payload)
    bench_sql()
    profile_hydration(Wide)
    profile_validate(Payload)

    if args.json:
        args.json.write_text(json.dumps(RESULTS, indent=2, sort_keys=True))
        print(f"\nwrote {args.json}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
