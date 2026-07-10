"""Regression tests for deterministic nested Contract field resolution."""

import pytest

from aquilia.contracts import Contract, IntFacet, NestedContractFacet
from aquilia.faults.domains import ConfigInvalidFault


class _Obj:
    def __init__(self, **kwargs):
        for key, value in kwargs.items():
            setattr(self, key, value)


class NameContract(Contract):
    first_name: str
    last_name: str


class AltNameContract(Contract):
    first_name: str


def test_annotation_only_nested_contract_roundtrip():
    class UsersContract(Contract):
        name: NameContract

    bp = UsersContract(data={"name": {"first_name": "Ada", "last_name": "Lovelace"}})
    assert bp.is_sealed() is True
    assert bp.validated_data["name"]["first_name"] == "Ada"

    instance = _Obj(name=_Obj(first_name="Ada", last_name="Lovelace"))
    out = UsersContract(instance=instance).to_dict()
    assert out == {"name": {"first_name": "Ada", "last_name": "Lovelace"}}


def test_facet_only_nested_contract_roundtrip():
    class UsersContract(Contract):
        name = NestedContractFacet(NameContract)

    bp = UsersContract(data={"name": {"first_name": "Ada", "last_name": "Lovelace"}})
    assert bp.is_sealed() is True
    assert bp.validated_data["name"]["last_name"] == "Lovelace"

    instance = _Obj(name=_Obj(first_name="Ada", last_name="Lovelace"))
    out = UsersContract(instance=instance).to_dict()
    assert out == {"name": {"first_name": "Ada", "last_name": "Lovelace"}}


def test_combined_annotation_and_nested_facet_merges_into_one_field():
    def _name_guard(value):
        if value.get("first_name") == "blocked":
            raise ValueError("name is blocked")

    class UsersContract(Contract):
        name: NameContract
        name = NestedContractFacet(NameContract, label="Display Name", validators=[_name_guard])

    ok = UsersContract(data={"name": {"first_name": "Ada", "last_name": "Lovelace"}})
    assert ok.is_sealed() is True

    bad = UsersContract(data={"name": {"first_name": "blocked", "last_name": "User"}})
    assert bad.is_sealed() is False
    assert "name" in bad.errors
    assert "blocked" in " ".join(bad.errors["name"])

    bound = ok._bound_facets["name"]
    assert isinstance(bound, NestedContractFacet)
    assert bound.label == "Display Name"


def test_mismatched_annotation_and_nested_facet_type_raises_clear_error():
    with pytest.raises(ConfigInvalidFault, match="type mismatch"):

        class UsersContract(Contract):
            name: NameContract
            name = NestedContractFacet(AltNameContract)


def test_mismatched_nested_cardinality_raises_clear_error():
    with pytest.raises(ConfigInvalidFault, match="conflicting cardinality"):

        class UsersContract(Contract):
            name: NameContract
            name = NestedContractFacet(NameContract, many=True)


def test_deep_nested_contract_serialization_and_deserialization():
    class StreetContract(Contract):
        line1: str

    class AddressContract(Contract):
        street: StreetContract

    class ProfileContract(Contract):
        address: AddressContract
        address = NestedContractFacet(AddressContract)

    class UsersContract(Contract):
        profile: ProfileContract

    payload = {
        "profile": {
            "address": {
                "street": {
                    "line1": "221B Baker Street",
                }
            }
        }
    }
    bp = UsersContract(data=payload)
    assert bp.is_sealed() is True
    assert bp.validated_data["profile"]["address"]["street"]["line1"] == "221B Baker Street"

    instance = _Obj(profile=_Obj(address=_Obj(street=_Obj(line1="221B Baker Street"))))
    out = UsersContract(instance=instance).to_dict()
    assert out == payload


def test_non_nested_explicit_facet_behavior_remains_backward_compatible():
    class LegacyContract(Contract):
        age: int
        age = IntFacet(min_value=10)

    bp = LegacyContract(data={"age": 9})
    assert bp.is_sealed() is False
    assert "age" in bp.errors
    assert "at least 10" in " ".join(bp.errors["age"])


def test_empty_contract_initialization_and_validation():
    class EmptyContract(Contract):
        pass

    bp = EmptyContract(data={})
    assert bp.is_sealed() is True
    assert bp.errors == {}
    assert bp.validated_data == {}


def test_class_attribute_assigned_nested_contract():
    class UsersContract(Contract):
        name = NameContract

    bp = UsersContract(data={"name": {"first_name": "Ada", "last_name": "Lovelace"}})
    assert bp.is_sealed() is True
    assert bp.validated_data["name"]["first_name"] == "Ada"
    assert bp.validated_data["name"]["last_name"] == "Lovelace"


def test_meta_class_raises_contract_fault():
    from aquilia.contracts.exceptions import ContractFault

    with pytest.raises(ContractFault, match="defined 'class Meta'"):
        class MetaContract(Contract):
            name: str

            class Meta:
                fields = "__all__"


def test_generic_subscriptable_nested_contract():
    # 1. Single instance
    class UsersContract(Contract):
        name: NestedContractFacet[NameContract]

    bp = UsersContract(data={"name": {"first_name": "Ada", "last_name": "Lovelace"}})
    assert bp.is_sealed() is True
    assert bp.validated_data["name"]["first_name"] == "Ada"

    instance = _Obj(name=_Obj(first_name="Ada", last_name="Lovelace"))
    assert UsersContract(instance=instance).to_dict() == {"name": {"first_name": "Ada", "last_name": "Lovelace"}}

    # 2. List (many) instance
    class UsersListContract(Contract):
        names: NestedContractFacet[NameContract, True]

    bp_list = UsersListContract(data={"names": [{"first_name": "Ada", "last_name": "Lovelace"}]})
    assert bp_list.is_sealed() is True
    assert bp_list.validated_data["names"][0]["first_name"] == "Ada"

    # 3. Forward reference (string representation)
    class LazyUsersContract(Contract):
        name: NestedContractFacet["NameContract"]

    bp_lazy = LazyUsersContract(data={"name": {"first_name": "Ada", "last_name": "Lovelace"}})
    assert bp_lazy.is_sealed() is True
    assert bp_lazy.validated_data["name"]["first_name"] == "Ada"

