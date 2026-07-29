"""
Regression tests for the Contracts nested-pipeline audit (BP-SEC-023 … BP-SEC-027).

These pin the second audit pass, which found that nested Contracts were
validated *structurally only*: ``Sigil.validate`` recursed into
``nested_cls._sigil.validate()``, so a nested Contract's ``@ward`` methods and
its object-level ``validate()`` hook never ran. Any business rule expressed on
a nested Contract — an authorization check, a cross-field invariant — was
silently unenforced.

The same pass added the async serialization pipeline and first-class input
adapters.

Numbering continues the ``BP-SEC-*`` sequence in
``tests/test_contract_audit_regressions.py``.
"""

from __future__ import annotations

import asyncio
from dataclasses import dataclass
from typing import TypedDict

import pytest

from aquilia.contracts import Contract, ward
from aquilia.contracts.annotations import NestedContractFacet
from aquilia.contracts.exceptions import ContractAsyncMismatchFault, LensUnresolvedFault
from aquilia.contracts.facets import IntFacet, TextFacet
from aquilia.contracts.lenses import Lens

# ════════════════════════════════════════════════════════════════════════
# BP-SEC-023 — nested Contract wards must actually run
# ════════════════════════════════════════════════════════════════════════


class _InnerWarded(Contract):
    name = TextFacet()

    @ward
    def reject_bad(self, data):
        if data["name"] == "bad":
            self.reject("name", "inner rejected")


class _OuterWarded(Contract):
    inner = NestedContractFacet(_InnerWarded)


class _OuterWardedMany(Contract):
    items = NestedContractFacet(_InnerWarded, many=True)


class TestNestedWardsRun:
    """A nested Contract's wards enforce its rules; they are not decoration."""

    def test_nested_ward_rejects(self):
        contract = _OuterWarded(data={"inner": {"name": "bad"}})
        assert contract.is_sealed() is False
        assert contract.errors == {"inner": {"name": ["inner rejected"]}}

    def test_nested_ward_allows_valid(self):
        contract = _OuterWarded(data={"inner": {"name": "fine"}})
        assert contract.is_sealed() is True
        assert dict(contract.validated_data) == {"inner": {"name": "fine"}}

    def test_nested_many_reports_failing_index(self):
        contract = _OuterWardedMany(data={"items": [{"name": "fine"}, {"name": "bad"}]})
        assert contract.is_sealed() is False
        # The index of the offending row is preserved, not flattened away.
        assert contract.errors == {"items": {"1": {"name": ["inner rejected"]}}}

    def test_nested_validate_hook_runs_once(self):
        calls: list[str] = []

        class Inner(Contract):
            name = TextFacet()

            def validate(self, data):
                calls.append(data["name"])
                return data

        class Outer(Contract):
            inner = NestedContractFacet(Inner)

        assert Outer(data={"inner": {"name": "x"}}).is_sealed() is True
        # Exactly once: a validate() override may write audit rows or emit
        # metrics, so a duplicate call is a correctness bug, not just waste.
        assert calls == ["x"]


# ════════════════════════════════════════════════════════════════════════
# BP-SEC-024 — nested async wards: guarded in sync, awaited in async
# ════════════════════════════════════════════════════════════════════════


class _InnerAsync(Contract):
    name = TextFacet()

    @ward(mode="async")
    async def reject_bad(self, data):
        await asyncio.sleep(0)
        if data["name"] == "bad":
            self.reject("name", "async inner rejected")


class _OuterAsync(Contract):
    inner = NestedContractFacet(_InnerAsync)


class _OuterAsyncMany(Contract):
    items = NestedContractFacet(_InnerAsync, many=True)


class TestNestedAsyncWards:
    """Async wards on a nested Contract are neither skipped nor mis-dispatched."""

    def test_has_async_wards_walks_nested_tree(self):
        # The outer Contract declares no wards of its own; the flag must still
        # be True, or callers would take the sync path and skip validation.
        assert list(_OuterAsync._ward_methods) == []
        assert _OuterAsync(data={"inner": {"name": "x"}}).has_async_wards is True

    def test_sync_call_raises_rather_than_skipping(self):
        contract = _OuterAsync(data={"inner": {"name": "bad"}})
        with pytest.raises(ContractAsyncMismatchFault):
            contract.is_sealed()

    async def test_async_rejects(self):
        contract = _OuterAsync(data={"inner": {"name": "bad"}})
        assert await contract.is_sealed_async() is False
        assert contract.errors == {"inner": {"name": ["async inner rejected"]}}

    async def test_async_allows_valid(self):
        contract = _OuterAsync(data={"inner": {"name": "fine"}})
        assert await contract.is_sealed_async() is True

    async def test_async_many_reports_failing_index(self):
        contract = _OuterAsyncMany(data={"items": [{"name": "fine"}, {"name": "bad"}]})
        assert await contract.is_sealed_async() is False
        assert contract.errors == {"items": {"1": {"name": ["async inner rejected"]}}}

    async def test_sync_ward_not_run_twice_in_async_path(self):
        calls: list[str] = []

        class Inner(Contract):
            name = TextFacet()

            @ward
            def sync_ward(self, data):
                calls.append("sync")

            @ward(mode="async")
            async def async_ward(self, data):
                await asyncio.sleep(0)

        class Outer(Contract):
            inner = NestedContractFacet(Inner)

        assert await Outer(data={"inner": {"name": "x"}}).is_sealed_async() is True
        # The sync phase runs during structural validation; the async drain must
        # not replay it.
        assert calls == ["sync"]

    async def test_deeply_nested_async_ward_still_reached(self):
        class Level3(Contract):
            name = TextFacet()

            @ward(mode="async")
            async def check(self, data):
                await asyncio.sleep(0)
                self.reject("name", "level3 rejected")

        class Level2(Contract):
            child = NestedContractFacet(Level3)

        class Level1(Contract):
            child = NestedContractFacet(Level2)

        contract = Level1(data={"child": {"child": {"name": "x"}}})
        assert contract.has_async_wards is True
        assert await contract.is_sealed_async() is False
        assert contract.errors == {"child": {"child": {"name": ["level3 rejected"]}}}


class TestRecursiveContractTermination:
    """A self-referential Contract must not hang the async-ward walk."""

    def test_self_referential_has_async_wards_terminates(self):
        class Node(Contract):
            name = TextFacet()
            child = NestedContractFacet("Node", required=False)

        # Cycle detection stops the walk; without it this recurses forever.
        assert Node(data={"name": "x"}).has_async_wards is False


# ════════════════════════════════════════════════════════════════════════
# BP-SEC-025 — async serialization resolves lazy ORM relations
# ════════════════════════════════════════════════════════════════════════


class _Related:
    def __init__(self, name: str, pk: int = 1):
        self.name = name
        self.pk = pk
        self.id = pk


class _LazyManager:
    """Stand-in for Aquilia's RelatedManager, whose ``all()`` is a coroutine."""

    def __init__(self, items):
        self._items = items

    async def all(self):
        return self._items


class _RelatedContract(Contract):
    name = TextFacet()


class _OwnerContract(Contract):
    title = TextFacet()
    related = Lens(_RelatedContract, many=True, source="related")


class _Owner:
    def __init__(self, related):
        self.title = "owner"
        self.pk = 1
        self.id = 1
        self.related = related


class TestAsyncSerialization:
    """``to_dict_async`` awaits what ``to_dict`` can only refuse."""

    def test_sync_still_raises_on_unresolved(self):
        owner = _Owner(_LazyManager([_Related("a")]))
        with pytest.raises(LensUnresolvedFault):
            _OwnerContract(instance=owner).to_dict()

    async def test_async_resolves_lazy_manager(self):
        owner = _Owner(_LazyManager([_Related("a"), _Related("b")]))
        result = await _OwnerContract(instance=owner).to_dict_async()
        assert result == {"title": "owner", "related": [{"name": "a"}, {"name": "b"}]}

    async def test_async_matches_sync_for_prefetched(self):
        owner = _Owner([_Related("a")])
        sync_result = _OwnerContract(instance=owner).to_dict()
        async_result = await _OwnerContract(instance=owner).to_dict_async()
        assert sync_result == async_result

    async def test_async_many(self):
        owners = [_Owner(_LazyManager([_Related("a")])), _Owner([_Related("b")])]
        result = await _OwnerContract.to_dict_many_async(owners)
        assert result == [
            {"title": "owner", "related": [{"name": "a"}]},
            {"title": "owner", "related": [{"name": "b"}]},
        ]

    async def test_async_to_one_relation(self):
        class OwnerOne(Contract):
            title = TextFacet()
            related = Lens(_RelatedContract, source="related")

        owner = _Owner(_Related("solo"))
        assert await OwnerOne(instance=owner).to_dict_async() == {
            "title": "owner",
            "related": {"name": "solo"},
        }

    async def test_async_null_relation(self):
        owner = _Owner(None)
        assert await _OwnerContract(instance=owner).to_dict_async() == {
            "title": "owner",
            "related": None,
        }


# ════════════════════════════════════════════════════════════════════════
# BP-SEC-026 — input adapters
# ════════════════════════════════════════════════════════════════════════


class _PersonContract(Contract):
    name = TextFacet()
    age = IntFacet()


@dataclass
class _PersonDataclass:
    name: str
    age: int


class _PersonTypedDict(TypedDict):
    name: str
    age: int


class TestInputAdapters:
    """Structured Python objects are first-class Contract input."""

    def test_dataclass_input(self):
        contract = _PersonContract(data=_PersonDataclass("Kai", 30))
        assert contract.is_sealed() is True
        assert dict(contract.validated_data) == {"name": "Kai", "age": 30}

    def test_typed_dict_input(self):
        payload: _PersonTypedDict = {"name": "Kai", "age": 30}
        assert _PersonContract(data=payload).is_sealed() is True

    def test_attrs_style_input(self):
        # Emulates an attrs class without taking a test dependency on attrs.
        class _Attr:
            def __init__(self, name):
                self.name = name

        class _PersonAttrs:
            __attrs_attrs__ = (_Attr("name"), _Attr("age"))

            def __init__(self, name, age):
                self.name = name
                self.age = age

        contract = _PersonContract(data=_PersonAttrs("Kai", 30))
        assert contract.is_sealed() is True
        assert dict(contract.validated_data) == {"name": "Kai", "age": 30}

    def test_dataclass_still_validated(self):
        # Adaptation is not a bypass — facet rules still apply.
        contract = _PersonContract(data=_PersonDataclass("Kai", "not-an-int"))
        assert contract.is_sealed() is False
        assert "age" in contract.errors

    def test_nested_dataclass_input(self):
        @dataclass
        class Inner:
            name: str

        @dataclass
        class Outer:
            inner: Inner

        class InnerContract(Contract):
            name = TextFacet()

        class OuterContract(Contract):
            inner = NestedContractFacet(InnerContract)

        contract = OuterContract(data=Outer(Inner("deep")))
        assert contract.is_sealed() is True
        assert dict(contract.validated_data) == {"inner": {"name": "deep"}}

    def test_dataclass_in_bulk_path(self):
        rows = [_PersonDataclass("A", 1), _PersonDataclass("B", 2)]
        outcomes = _PersonContract.seal_many(rows)
        assert [o.ok for o in outcomes] == [True, True]


# ════════════════════════════════════════════════════════════════════════
# BP-SEC-027 — non-mapping input reports the real problem
# ════════════════════════════════════════════════════════════════════════


class TestNonMappingInput:
    """A scalar body is a malformed payload, not a set of missing fields."""

    @pytest.mark.parametrize(
        ("payload", "type_name"),
        [
            ("a string", "str"),
            (42, "int"),
            (["a", "list"], "list"),
            (None, "NoneType"),
        ],
    )
    def test_reports_expected_object(self, payload, type_name):
        contract = _PersonContract(data=payload)
        assert contract.is_sealed() is False
        # Previously coerced to {}, producing a "this field is required" error
        # per field — a misdiagnosis that sent developers hunting the wrong bug.
        assert contract.errors == {"__all__": [f"Expected an object, got {type_name}"]}

    def test_bulk_path_reports_expected_object(self):
        outcomes = _PersonContract.seal_many(["not a row"])
        assert outcomes[0].ok is False
        assert outcomes[0].errors == {"__all__": ["Expected an object, got str"]}


# ════════════════════════════════════════════════════════════════════════
# BP-SEC-037 — the ``list[Contract]`` annotation is a nested relation too
# ════════════════════════════════════════════════════════════════════════


class _AnnotatedInner(Contract):
    qty = IntFacet()

    @ward
    def qty_positive(self, data):
        if data["qty"] < 1:
            self.reject("qty", "Must be at least 1")


class _AnnotatedOuter(Contract):
    items: list[_AnnotatedInner] = None


class _AnnotatedAsyncInner(Contract):
    sku = TextFacet()

    @ward(mode="async")
    async def in_stock(self, data):
        if data["sku"] == "gone":
            self.reject("sku", "Out of stock")


class _AnnotatedAsyncOuter(Contract):
    items: list[_AnnotatedAsyncInner] = None


class TestAnnotatedListOfContracts:
    """
    ``items: list[Item]`` and ``NestedContractFacet(Item, many=True)`` mean the
    same thing to a reader, so they must mean the same thing to the validator.

    The annotation builds ``ListFacet(child=NestedContractFacet)``, a different
    facet type. Detection that matched only ``NestedContractFacet`` classified
    the far more common annotated spelling as an ordinary list, so it ran
    structural validation alone — the nested-pipeline fix did not reach it.
    """

    def test_nested_ward_rejects(self):
        contract = _AnnotatedOuter(data={"items": [{"qty": 5}, {"qty": 0}]})
        assert contract.is_sealed() is False
        assert contract.errors == {"items": {"1": {"qty": ["Must be at least 1"]}}}

    def test_valid_rows_pass_through(self):
        contract = _AnnotatedOuter(data={"items": [{"qty": 2}]})
        assert contract.is_sealed() is True
        assert dict(contract.validated_data) == {"items": [{"qty": 2}]}

    def test_matches_the_explicit_facet_spelling(self):
        """Both spellings must produce the same errors for the same payload."""
        payload = {"items": [{"qty": 0}]}

        class _ExplicitOuter(Contract):
            items = NestedContractFacet(_AnnotatedInner, many=True)

        annotated = _AnnotatedOuter(data=payload)
        explicit = _ExplicitOuter(data=payload)
        annotated.is_sealed()
        explicit.is_sealed()
        assert annotated.errors == explicit.errors

    def test_async_wards_are_detected_through_the_list(self):
        """Reporting ``False`` here sends the caller down the sync path, where
        the ward is skipped silently rather than raising."""
        assert _AnnotatedAsyncOuter(data={}).has_async_wards is True

    async def test_async_nested_ward_rejects(self):
        contract = _AnnotatedAsyncOuter(data={"items": [{"sku": "ok"}, {"sku": "gone"}]})
        assert await contract.is_sealed_async() is False
        assert contract.errors == {"items": {"1": {"sku": ["Out of stock"]}}}

    def test_sync_entry_point_raises_for_async_wards(self):
        contract = _AnnotatedAsyncOuter(data={"items": [{"sku": "gone"}]})
        with pytest.raises(ContractAsyncMismatchFault):
            contract.is_sealed()

    def test_json_schema_references_the_nested_definition(self):
        """An annotated list of Contracts is an array of ``$ref``, not an
        untyped array — OpenAPI consumers generate from this."""
        schema = _AnnotatedOuter._sigil.to_json_schema()
        assert schema["properties"]["items"] == {
            "type": "array",
            "items": {"$ref": "#/$defs/_AnnotatedInner"},
        }

    def test_dataclass_rows_are_adapted(self):
        @dataclass
        class _Row:
            qty: int

        contract = _AnnotatedOuter(data={"items": [_Row(qty=3)]})
        assert contract.is_sealed() is True
        assert dict(contract.validated_data) == {"items": [{"qty": 3}]}
