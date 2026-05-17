import pytest
from aquilia.blueprints import Blueprint, Facet, CastFault, SealFault
from aquilia.blueprints.facets import TextFacet, IntFacet
from aquilia.blueprints.annotations import NestedBlueprintFacet

def test_missing_required_field():
    class MyBlueprint(Blueprint):
        name = TextFacet(required=True)

    bp = MyBlueprint(data={})
    assert bp.is_sealed() is False
    assert bp.errors == {'name': ['This field is required']}

    try:
        bp.is_sealed(raise_fault=True)
    except SealFault as e:
        body = e.as_response_body()
        assert body['errors'] == {'name': ['This field is required']}
        assert body['fault'] == 'BP200'
        # Check details via metadata matching the middleware expectation
        assert getattr(e, 'metadata', {}).get('details') == {'field': 'name', 'reason': 'This field is required'}

def test_custom_rule():
    class CustomBlueprint(Blueprint):
        age = IntFacet()

        def seal_age(self, data):
            if data.get('age', 0) < 18:
                self.reject('age', 'Must be at least 18')

    bp = CustomBlueprint(data={'age': 15})
    assert bp.is_sealed() is False

    try:
        bp.is_sealed(raise_fault=True)
    except SealFault as e:
        body = e.as_response_body()
        assert body['errors'] == {'age': ['Must be at least 18']}

def test_nested_blueprint_failure():
    class AddressBP(Blueprint):
        city = TextFacet(required=True)

    class UserBP(Blueprint):
        name = TextFacet(required=True)
        address = NestedBlueprintFacet(AddressBP, required=True)

    bp = UserBP(data={"name": "Alice", "address": {}})
    assert bp.is_sealed() is False

    try:
        bp.is_sealed(raise_fault=True)
    except SealFault as e:
        body = e.as_response_body()
        # Expect address validation error to be correctly bubbled up
        assert body['errors'] == {'address': [{'city': ['This field is required']}]}

def test_invalid_type():
    class TypeBP(Blueprint):
        count = IntFacet()

    bp = TypeBP(data={'count': 'not-a-number'})
    assert bp.is_sealed() is False
    try:
        bp.is_sealed(raise_fault=True)
    except SealFault as e:
        body = e.as_response_body()
        assert 'count' in body['errors']

def test_regression_generic_error_code():
    # Make sure we still return BP200 as the main error code
    class AnyBP(Blueprint):
        val = IntFacet(required=True)

    bp = AnyBP(data={})
    try:
        bp.is_sealed(raise_fault=True)
    except SealFault as e:
        assert e.code == "BP200"
