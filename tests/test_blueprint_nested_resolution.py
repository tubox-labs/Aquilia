"""Regression tests for deterministic nested Blueprint field resolution."""

import pytest

from aquilia.blueprints import Blueprint, IntFacet, NestedBlueprintFacet
from aquilia.faults.domains import ConfigInvalidFault


class _Obj:
    def __init__(self, **kwargs):
        for key, value in kwargs.items():
            setattr(self, key, value)


class NameBlueprint(Blueprint):
    first_name: str
    last_name: str


class AltNameBlueprint(Blueprint):
    first_name: str


def test_annotation_only_nested_blueprint_roundtrip():
    class UsersBlueprint(Blueprint):
        name: NameBlueprint

    bp = UsersBlueprint(data={"name": {"first_name": "Ada", "last_name": "Lovelace"}})
    assert bp.is_sealed() is True
    assert bp.validated_data["name"]["first_name"] == "Ada"

    instance = _Obj(name=_Obj(first_name="Ada", last_name="Lovelace"))
    out = UsersBlueprint(instance=instance).to_dict()
    assert out == {"name": {"first_name": "Ada", "last_name": "Lovelace"}}


def test_facet_only_nested_blueprint_roundtrip():
    class UsersBlueprint(Blueprint):
        name = NestedBlueprintFacet(NameBlueprint)

    bp = UsersBlueprint(data={"name": {"first_name": "Ada", "last_name": "Lovelace"}})
    assert bp.is_sealed() is True
    assert bp.validated_data["name"]["last_name"] == "Lovelace"

    instance = _Obj(name=_Obj(first_name="Ada", last_name="Lovelace"))
    out = UsersBlueprint(instance=instance).to_dict()
    assert out == {"name": {"first_name": "Ada", "last_name": "Lovelace"}}


def test_combined_annotation_and_nested_facet_merges_into_one_field():
    def _name_guard(value):
        if value.get("first_name") == "blocked":
            raise ValueError("name is blocked")

    class UsersBlueprint(Blueprint):
        name: NameBlueprint
        name = NestedBlueprintFacet(NameBlueprint, label="Display Name", validators=[_name_guard])

    ok = UsersBlueprint(data={"name": {"first_name": "Ada", "last_name": "Lovelace"}})
    assert ok.is_sealed() is True

    bad = UsersBlueprint(data={"name": {"first_name": "blocked", "last_name": "User"}})
    assert bad.is_sealed() is False
    assert "name" in bad.errors
    assert "blocked" in " ".join(bad.errors["name"])

    bound = ok._bound_facets["name"]
    assert isinstance(bound, NestedBlueprintFacet)
    assert bound.label == "Display Name"


def test_mismatched_annotation_and_nested_facet_type_raises_clear_error():
    with pytest.raises(ConfigInvalidFault, match="type mismatch"):

        class UsersBlueprint(Blueprint):
            name: NameBlueprint
            name = NestedBlueprintFacet(AltNameBlueprint)


def test_mismatched_nested_cardinality_raises_clear_error():
    with pytest.raises(ConfigInvalidFault, match="conflicting cardinality"):

        class UsersBlueprint(Blueprint):
            name: NameBlueprint
            name = NestedBlueprintFacet(NameBlueprint, many=True)


def test_deep_nested_blueprint_serialization_and_deserialization():
    class StreetBlueprint(Blueprint):
        line1: str

    class AddressBlueprint(Blueprint):
        street: StreetBlueprint

    class ProfileBlueprint(Blueprint):
        address: AddressBlueprint
        address = NestedBlueprintFacet(AddressBlueprint)

    class UsersBlueprint(Blueprint):
        profile: ProfileBlueprint

    payload = {
        "profile": {
            "address": {
                "street": {
                    "line1": "221B Baker Street",
                }
            }
        }
    }
    bp = UsersBlueprint(data=payload)
    assert bp.is_sealed() is True
    assert bp.validated_data["profile"]["address"]["street"]["line1"] == "221B Baker Street"

    instance = _Obj(profile=_Obj(address=_Obj(street=_Obj(line1="221B Baker Street"))))
    out = UsersBlueprint(instance=instance).to_dict()
    assert out == payload


def test_non_nested_explicit_facet_behavior_remains_backward_compatible():
    class LegacyBlueprint(Blueprint):
        age: int
        age = IntFacet(min_value=10)

    bp = LegacyBlueprint(data={"age": 9})
    assert bp.is_sealed() is False
    assert "age" in bp.errors
    assert "at least 10" in " ".join(bp.errors["age"])


def test_empty_blueprint_initialization_and_validation():
    class EmptyBlueprint(Blueprint):
        pass

    bp = EmptyBlueprint(data={})
    assert bp.is_sealed() is True
    assert bp.errors == {}
    assert bp.validated_data == {}


def test_class_attribute_assigned_nested_blueprint():
    class UsersBlueprint(Blueprint):
        name = NameBlueprint

    bp = UsersBlueprint(data={"name": {"first_name": "Ada", "last_name": "Lovelace"}})
    assert bp.is_sealed() is True
    assert bp.validated_data["name"]["first_name"] == "Ada"
    assert bp.validated_data["name"]["last_name"] == "Lovelace"


def test_meta_class_raises_blueprint_fault():
    from aquilia.blueprints.exceptions import BlueprintFault

    with pytest.raises(BlueprintFault, match="defined 'class Meta'"):
        class MetaBlueprint(Blueprint):
            name: str

            class Meta:
                fields = "__all__"


def test_generic_subscriptable_nested_blueprint():
    # 1. Single instance
    class UsersBlueprint(Blueprint):
        name: NestedBlueprintFacet[NameBlueprint]

    bp = UsersBlueprint(data={"name": {"first_name": "Ada", "last_name": "Lovelace"}})
    assert bp.is_sealed() is True
    assert bp.validated_data["name"]["first_name"] == "Ada"

    instance = _Obj(name=_Obj(first_name="Ada", last_name="Lovelace"))
    assert UsersBlueprint(instance=instance).to_dict() == {"name": {"first_name": "Ada", "last_name": "Lovelace"}}

    # 2. List (many) instance
    class UsersListBlueprint(Blueprint):
        names: NestedBlueprintFacet[NameBlueprint, True]

    bp_list = UsersListBlueprint(data={"names": [{"first_name": "Ada", "last_name": "Lovelace"}]})
    assert bp_list.is_sealed() is True
    assert bp_list.validated_data["names"][0]["first_name"] == "Ada"

    # 3. Forward reference (string representation)
    class LazyUsersBlueprint(Blueprint):
        name: NestedBlueprintFacet["NameBlueprint"]

    bp_lazy = LazyUsersBlueprint(data={"name": {"first_name": "Ada", "last_name": "Lovelace"}})
    assert bp_lazy.is_sealed() is True
    assert bp_lazy.validated_data["name"]["first_name"] == "Ada"

