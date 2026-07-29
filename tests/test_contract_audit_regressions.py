"""
Regression tests for the Contracts architecture audit (BP-SEC-014 … BP-SEC-021).

Each class below pins the behaviour of one confirmed defect found during the
Contracts deep-audit pass. The tests are written to fail loudly if the old
behaviour is ever reintroduced, so they double as executable documentation of
*why* each fix exists.

Numbering continues the ``BP-SEC-*`` sequence established in
``tests/test_contract_security.py``.
"""

from __future__ import annotations

import asyncio
from decimal import Decimal

import pytest

from aquilia.contracts import Contract, computed, ward
from aquilia.contracts.exceptions import LensUnresolvedFault
from aquilia.contracts.facets import BytesFacet, IntFacet, TextFacet
from aquilia.contracts.lenses import Lens

# ════════════════════════════════════════════════════════════════════════
# BP-SEC-014 — "__minimal__" projection must restrict, never expose everything
# ════════════════════════════════════════════════════════════════════════


class _UserRow:
    id = 1
    name = "Alice"
    password_hash = "SUPER_SECRET"
    created_at = "2026-01-01"


class MinimalUserContract(Contract):
    id = IntFacet()
    name = TextFacet()
    password_hash = TextFacet()
    created_at = TextFacet(read_only=True)

    class Spec:
        projections = {"public": "__minimal__", "everything": "__all__"}
        default_projection = "everything"


class TestBPSEC014_MinimalProjection:
    """
    ``"__minimal__"`` previously resolved to an empty ``frozenset``, which is
    falsy — so the per-field filter ``if projection_fields and ...`` never
    excluded anything and the projection returned *every* field, including ones
    a developer had deliberately hidden behind it.
    """

    def test_minimal_excludes_non_minimal_fields(self):
        data = MinimalUserContract(instance=_UserRow(), projection="public").data
        assert "password_hash" not in data
        assert "name" not in data

    def test_minimal_includes_pk_and_read_only(self):
        data = MinimalUserContract(instance=_UserRow(), projection="public").data
        assert data["id"] == 1
        assert data["created_at"] == "2026-01-01"

    def test_all_projection_still_exposes_everything(self):
        data = MinimalUserContract(instance=_UserRow(), projection="everything").data
        assert set(data) == {"id", "name", "password_hash", "created_at"}

    def test_minimal_schema_is_restricted_too(self):
        schema = MinimalUserContract.to_schema(projection="public")
        assert set(schema["properties"]) == {"id", "created_at"}

    def test_empty_projection_renders_nothing(self):
        """An empty projection means 'expose nothing', not 'expose all'."""

        class NoPkContract(Contract):
            name = TextFacet()

            class Spec:
                projections = {"m": "__minimal__"}

        assert NoPkContract(instance=_UserRow(), projection="m").data == {}


# ════════════════════════════════════════════════════════════════════════
# BP-SEC-015 — nesting depth enforced on the real validation path
# ════════════════════════════════════════════════════════════════════════


class TreeNodeContract(Contract):
    label: str
    child: "TreeNodeContract" = None


def _nest(levels: int) -> dict:
    payload: dict = {"label": "leaf"}
    for _ in range(levels):
        payload = {"label": "branch", "child": payload}
    return payload


class TestBPSEC015_SigilNestingDepth:
    """
    ``Sigil.validate()`` recursed into nested Contracts directly, bypassing the
    guard that lived on ``NestedContractFacet.cast()``. A few kilobytes of
    deeply nested JSON therefore produced an uncaught ``RecursionError`` inside
    the request coroutine instead of a clean validation error.
    """

    def test_deeply_nested_payload_is_rejected_not_crashed(self):
        bp = TreeNodeContract(data=_nest(3000))
        assert bp.is_sealed() is False
        assert bp.errors  # structured error, no RecursionError escaped

    def test_shallow_nesting_still_validates(self):
        bp = TreeNodeContract(data=_nest(5))
        assert bp.is_sealed() is True

    def test_depth_error_mentions_the_limit(self):
        bp = TreeNodeContract(data=_nest(200))
        bp.is_sealed()
        assert "depth" in repr(bp.errors).lower()


# ════════════════════════════════════════════════════════════════════════
# BP-SEC-016 — object-level validate() runs exactly once per row
# ════════════════════════════════════════════════════════════════════════


_validate_calls: list[int] = []


class CountingContract(Contract):
    n = IntFacet()

    def validate(self, data):
        _validate_calls.append(data["n"])
        return data


class TestBPSEC016_BulkValidateInvokedOnce:
    """
    ``seal_many``/``seal_stream`` duplicated the ward-invocation block five
    times and read ``inst.errors`` — a property that lazily triggers a *full*
    ``is_sealed()`` cycle — causing ``validate()`` to run up to three times per
    row. Any override with side effects (metrics, audit writes, external calls)
    fired three times for every record.
    """

    def setup_method(self):
        _validate_calls.clear()

    def test_seal_many_calls_validate_once_per_row(self):
        outcomes = CountingContract.seal_many([{"n": 1}, {"n": 2}, {"n": 3}])
        assert [o.ok for o in outcomes] == [True, True, True]
        assert _validate_calls == [1, 2, 3]

    def test_seal_many_parallel_calls_validate_once_per_row(self):
        outcomes = CountingContract.seal_many([{"n": 1}, {"n": 2}], parallel=True)
        assert all(o.ok for o in outcomes)
        assert sorted(_validate_calls) == [1, 2]

    def test_seal_many_reports_failures_per_row(self):
        outcomes = CountingContract.seal_many([{"n": 1}, {"n": "bad"}])
        assert [o.ok for o in outcomes] == [True, False]
        assert outcomes[1].errors and "n" in outcomes[1].errors

    def test_seal_many_raise_on_any(self):
        from aquilia.contracts.exceptions import SealFault

        with pytest.raises(SealFault):
            CountingContract.seal_many([{"n": "bad"}], raise_on_any=True)

    def test_seal_stream_calls_validate_once_per_record(self):
        async def _chunks():
            yield b'{"n": 1}\n{"n": 2}\n'

        async def _run():
            return [o async for o in CountingContract.seal_stream(_chunks())]

        outcomes = asyncio.run(_run())
        assert [o.ok for o in outcomes] == [True, True]
        assert _validate_calls == [1, 2]

    def test_seal_stream_reports_malformed_json(self):
        async def _chunks():
            yield b'{"n": 1}\nnot json\n'

        async def _run():
            return [o async for o in CountingContract.seal_stream(_chunks())]

        outcomes = asyncio.run(_run())
        assert outcomes[0].ok is True
        assert outcomes[1].ok is False
        assert "JSON parse error" in outcomes[1].errors["__all__"][0]

    def test_seal_stream_flushes_trailing_buffer(self):
        async def _chunks():
            yield b'{"n": 7}'  # no trailing newline

        async def _run():
            return [o async for o in CountingContract.seal_stream(_chunks())]

        outcomes = asyncio.run(_run())
        assert [o.ok for o in outcomes] == [True]
        assert _validate_calls == [7]


# ════════════════════════════════════════════════════════════════════════
# BP-SEC-017 — async validation works for many=True collections
# ════════════════════════════════════════════════════════════════════════


class AsyncItemContract(Contract):
    n = IntFacet()

    @ward(mode="async")
    async def reject_large(self, data):
        await asyncio.sleep(0)
        if data["n"] > 5:
            self.reject("n", "too big")


class TestBPSEC017_AsyncMany:
    """
    ``_seal_many`` built each child Contract and called the *synchronous*
    ``is_sealed()``. When the child declared an async ward that raised
    ``ContractAsyncMismatchFault`` from inside the loop — so bulk bodies with
    an async uniqueness check could not be validated at all.
    """

    def test_async_many_validates_every_item(self):
        async def _run():
            bp = AsyncItemContract(data=[{"n": 1}, {"n": 2}], many=True)
            ok = await bp.is_sealed_async()
            return ok, bp.validated_data

        ok, validated = asyncio.run(_run())
        assert ok is True
        assert [dict(item) for item in validated] == [{"n": 1}, {"n": 2}]

    def test_async_many_reports_per_item_errors(self):
        async def _run():
            bp = AsyncItemContract(data=[{"n": 1}, {"n": 9}], many=True)
            ok = await bp.is_sealed_async()
            return ok, bp.errors

        ok, errors = asyncio.run(_run())
        assert ok is False
        assert errors["1"]["n"] == ["too big"]

    def test_async_single_still_works(self):
        async def _run():
            bp = AsyncItemContract(data={"n": 9})
            return await bp.is_sealed_async(), bp.errors

        ok, errors = asyncio.run(_run())
        assert ok is False
        assert errors["n"] == ["too big"]

    def test_async_many_respects_max_items(self):
        async def _run():
            bp = AsyncItemContract(data=[{"n": 1}] * 5, many=True, context={"max_many_items": 2})
            return await bp.is_sealed_async(), bp.errors

        ok, errors = asyncio.run(_run())
        assert ok is False
        assert "exceeding the maximum" in errors["__all__"][0]


# ════════════════════════════════════════════════════════════════════════
# BP-SEC-018 — Lens fails loudly on unresolved to-many relations
# ════════════════════════════════════════════════════════════════════════


class _RelatedItem:
    def __init__(self, item_id: int):
        self.id = item_id


class _UnresolvedManager:
    async def all(self):  # mirrors RelatedManager.all()
        return []


class ItemLensContract(Contract):
    id = IntFacet()


class OrderLensContract(Contract):
    id = IntFacet()
    items = Lens(ItemLensContract, many=True)


class TestBPSEC018_LensUnresolved:
    """
    ``Lens.mold()`` returned ``[]`` when handed an un-awaited related manager.
    An empty list is indistinguishable from a genuinely empty relation, so the
    API silently shipped wrong data — including, at worst, an empty permission
    list read by a caller as "this user has no permissions".
    """

    def test_unresolved_manager_raises(self):
        order = type("Order", (), {"id": 1, "items": _UnresolvedManager()})()
        with pytest.raises(LensUnresolvedFault):
            OrderLensContract(instance=order).data

    def test_fault_names_the_field(self):
        order = type("Order", (), {"id": 1, "items": _UnresolvedManager()})()
        with pytest.raises(LensUnresolvedFault) as exc:
            OrderLensContract(instance=order).data
        assert exc.value.field == "items"

    def test_materialized_list_still_molds(self):
        order = type("Order", (), {"id": 1, "items": [_RelatedItem(7), _RelatedItem(8)]})()
        assert OrderLensContract(instance=order).data == {"id": 1, "items": [{"id": 7}, {"id": 8}]}

    def test_empty_list_is_still_valid(self):
        order = type("Order", (), {"id": 1, "items": []})()
        assert OrderLensContract(instance=order).data == {"id": 1, "items": []}


# ════════════════════════════════════════════════════════════════════════
# BP-SEC-019 — IntFacet rejects non-integer floats instead of truncating
# ════════════════════════════════════════════════════════════════════════


class QuantityContract(Contract):
    quantity = IntFacet()


class TestBPSEC019_IntTruncation:
    """
    ``IntFacet.cast()`` called ``int(value)`` directly, so ``3.9`` silently
    became ``3`` — a client's ``{"quantity": 3.9}`` was persisted as ``3`` with
    no indication anything had been dropped. ``"3.9"`` was already rejected, so
    the same logical input behaved differently depending on its wire type.
    """

    @pytest.mark.parametrize("value", [3.9, -0.5, Decimal("3.5")])
    def test_fractional_values_rejected(self, value):
        bp = QuantityContract(data={"quantity": value})
        assert bp.is_sealed() is False
        assert "quantity" in bp.errors

    @pytest.mark.parametrize(("value", "expected"), [(3, 3), (3.0, 3), ("3", 3), (Decimal("3.0"), 3)])
    def test_integral_values_accepted(self, value, expected):
        bp = QuantityContract(data={"quantity": value})
        assert bp.is_sealed() is True
        assert bp.validated_data["quantity"] == expected

    @pytest.mark.parametrize("value", [float("nan"), float("inf"), float("-inf")])
    def test_non_finite_rejected(self, value):
        bp = QuantityContract(data={"quantity": value})
        assert bp.is_sealed() is False

    def test_bool_still_rejected(self):
        bp = QuantityContract(data={"quantity": True})
        assert bp.is_sealed() is False

    def test_non_numeric_string_still_rejected(self):
        bp = QuantityContract(data={"quantity": "3.9"})
        assert bp.is_sealed() is False


# ════════════════════════════════════════════════════════════════════════
# BP-SEC-020 — bytes fields are functional end to end
# ════════════════════════════════════════════════════════════════════════


class BinaryContract(Contract):
    payload = BytesFacet(max_length=8)


class AnnotatedBinaryContract(Contract):
    payload: bytes


class TestBPSEC020_BytesFacet:
    """
    ``ANNOTATION_TO_FACET`` mapped ``bytes`` to ``TextFacet``, whose ``cast()``
    whitelist rejects real ``bytes`` — so a ``payload: bytes`` field rejected
    every genuine bytes value while accepting plain strings, making the type
    annotation actively misleading.
    """

    def test_raw_bytes_accepted(self):
        bp = BinaryContract(data={"payload": b"hello"})
        assert bp.is_sealed() is True
        assert bp.validated_data["payload"] == b"hello"

    def test_base64_string_decoded(self):
        bp = BinaryContract(data={"payload": "aGVsbG8="})
        assert bp.is_sealed() is True
        assert bp.validated_data["payload"] == b"hello"

    def test_invalid_base64_rejected(self):
        bp = BinaryContract(data={"payload": "not base64!!!"})
        assert bp.is_sealed() is False

    def test_max_length_enforced_on_decoded_bytes(self):
        bp = BinaryContract(data={"payload": b"x" * 9})
        assert bp.is_sealed() is False

    def test_outbound_molds_to_base64(self):
        row = type("Row", (), {"payload": b"hello"})()
        assert BinaryContract(instance=row).data == {"payload": "aGVsbG8="}

    def test_hex_encoding_round_trips(self):
        class HexContract(Contract):
            payload = BytesFacet(encoding="hex")

        bp = HexContract(data={"payload": "68656c6c6f"})
        assert bp.is_sealed() is True
        assert bp.validated_data["payload"] == b"hello"

    def test_bytes_annotation_routes_to_bytes_facet(self):
        bp = AnnotatedBinaryContract(data={"payload": b"hi"})
        assert bp.is_sealed() is True
        assert bp.validated_data["payload"] == b"hi"

    def test_schema_declares_byte_format(self):
        schema = BinaryContract.to_schema()
        assert schema["properties"]["payload"]["format"] == "byte"


# ════════════════════════════════════════════════════════════════════════
# BP-SEC-021 — @computed receives the live Contract instance
# ════════════════════════════════════════════════════════════════════════


class _Person:
    first = "Ada"
    last = "Lovelace"


class ComputedContract(Contract):
    first = TextFacet()
    last = TextFacet()

    @computed
    def full_name(self, instance) -> str:
        return f"{instance.first} {instance.last}"

    @computed
    def greeting(self, instance) -> str:
        return f"{self.context.get('greeting', 'Hello')}, {instance.first}"

    @computed
    def has_instance(self, instance) -> bool:
        return self.instance is not None


class TestBPSEC021_ComputedBinding:
    """
    ``Computed.extract()`` reconstructed a bare owner via ``cls.__new__(cls)``
    because facets are class-level and never bound per instance. That shell
    skipped ``__init__``, so any ``@computed`` method touching ``self.context``,
    ``self.instance``, or ``self._validated_data`` raised ``AttributeError`` in
    production while doc-style examples (which only use the ``instance``
    argument) kept working.
    """

    def test_instance_argument_still_works(self):
        assert ComputedContract(instance=_Person()).data["full_name"] == "Ada Lovelace"

    def test_context_is_available_on_self(self):
        data = ComputedContract(instance=_Person(), context={"greeting": "Hi"}).data
        assert data["greeting"] == "Hi, Ada"

    def test_instance_is_available_on_self(self):
        assert ComputedContract(instance=_Person()).data["has_instance"] is True

    def test_default_context_does_not_raise(self):
        assert ComputedContract(instance=_Person()).data["greeting"] == "Hello, Ada"


# ════════════════════════════════════════════════════════════════════════
# BP-SEC-022 — unmapped Union members are surfaced, not dropped
# ════════════════════════════════════════════════════════════════════════


class _NoFacetForThis:
    """An arbitrary user type with no ``ANNOTATION_TO_FACET`` entry."""


class TestBPSEC022_UnionNarrowing:
    """
    A union member with no ``ANNOTATION_TO_FACET`` entry was skipped silently,
    building a ``PolymorphicFacet`` that accepted fewer types than the
    annotation promised — surfacing much later as a confusing "wrong type"
    rejection rather than a declaration-time problem.
    """

    def test_unmapped_union_member_warns(self):
        with pytest.warns(UserWarning, match="no Facet mapping"):

            class WeirdUnionContract(Contract):
                value: int | _NoFacetForThis

    def test_fully_mapped_union_does_not_warn(self):
        import warnings

        with warnings.catch_warnings():
            warnings.simplefilter("error", UserWarning)

            class FineUnionContract(Contract):
                value: int | str

            bp = FineUnionContract(data={"value": 5})
            assert bp.is_sealed() is True
