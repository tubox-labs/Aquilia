import uuid
from datetime import date, datetime
from enum import Enum
from typing import Annotated, Literal

import pytest

from aquilia.blueprints import Blueprint, Facet, ward


# Enums and Types for testing
class UserRole(Enum):
    ADMIN = "admin"
    USER = "user"


class OrderItemBlueprint(Blueprint):
    product_id: int
    qty: Annotated[int, Facet.int[1:]]
    price: Annotated[float, Facet.float[0:]]


class OrderBlueprint(Blueprint):
    items: list[OrderItemBlueprint]
    total: Annotated[float, Facet.float[0:]]
    discount_code: Annotated[str | None, Facet.text()] = None

    @ward
    def total_matches_items(self, data):
        computed = sum(i.price * i.qty for i in data.items)
        if abs(computed - data.total) > 0.01:
            self.reject("total", f"Expected {computed}, got {data.total}")

    @ward(mode="async")
    async def discount_code_is_valid(self, data):
        if data.discount_code and not await self.context["promo_service"].exists(data.discount_code):
            self.reject("discount_code", "Unknown or expired code")


class PromoServiceMock:
    async def exists(self, code: str) -> bool:
        return code == "VALID10"


# 1. Ward Validation Reproduction
@pytest.mark.asyncio
async def test_ward_validation_nested_and_async():
    context = {"promo_service": PromoServiceMock()}
    data = {
        "items": [
            {"product_id": 1, "qty": 2, "price": 10.0},
            {"product_id": 2, "qty": 1, "price": 5.0},
        ],
        "total": 25.0,
        "discount_code": "VALID10",
    }

    bp = OrderBlueprint(data=data, context=context)
    # This should pass without raising 'builtin_function_or_method' object is not iterable
    is_ok = await bp.is_sealed_async()
    assert is_ok is True, f"Validation failed: {bp.errors}"


# 2. Union Schema Generation Failure Reproduction
class Circle(Blueprint):
    kind: Literal["circle"] = "circle"
    radius: Annotated[float, Facet.float[0:]]


class Square(Blueprint):
    kind: Literal["square"] = "square"
    side: Annotated[float, Facet.float[0:]]


Shape = Circle | Square


def test_union_schema_generation():
    # This should generate schema without set subscription TypeError
    schema = Shape.to_json_schema()
    assert "oneOf" in schema
    # Verify discriminator
    assert schema.get("discriminator") == {"propertyName": "kind"}


# 3. Serialization Reproduction
class ComplexUserBlueprint(Blueprint):
    id: uuid.UUID
    name: str
    role: UserRole
    created_at: datetime
    active: bool = True
    birthday: date | None = None


def test_to_dict_inbound_and_outbound():
    user_id = uuid.uuid4()
    now = datetime.now()
    birth = date(1990, 1, 1)

    # Test inbound (data validation -> to_dict() returns validated data)
    data = {
        "id": str(user_id),
        "name": "Alice",
        "role": "admin",
        "created_at": now.isoformat(),
        "active": True,
        "birthday": birth.isoformat(),
    }

    bp = ComplexUserBlueprint(data=data)
    assert bp.is_sealed() is True
    out_dict = bp.to_dict()
    assert out_dict["name"] == "Alice"
    assert out_dict["active"] is True
    assert isinstance(out_dict["id"], uuid.UUID)

    # Test class-level to_dict and to_dict_many (outbound serialization)
    class _MockUser:
        def __init__(self):
            self.id = user_id
            self.name = "Alice"
            self.role = UserRole.ADMIN
            self.created_at = now
            self.active = True
            self.birthday = birth

    user_obj = _MockUser()
    serialized = ComplexUserBlueprint.to_dict(user_obj)
    assert serialized["name"] == "Alice"
    assert serialized["role"] == "admin"
    assert serialized["created_at"] == now.isoformat()
    assert serialized["birthday"] == birth.isoformat()
    assert serialized["id"] == str(user_id)

    serialized_list = ComplexUserBlueprint.to_dict_many([user_obj, user_obj])
    assert len(serialized_list) == 2
    assert serialized_list[0]["name"] == "Alice"


class Drawing(Blueprint):
    shape: Circle | Square


def test_union_serialization():
    class _MockDrawing:
        def __init__(self, shape):
            self.shape = shape

    class _MockCircle:
        def __init__(self, radius):
            self.kind = "circle"
            self.radius = radius

    drawing = _MockDrawing(shape=_MockCircle(radius=10.0))
    serialized = Drawing.to_dict(drawing)
    assert serialized == {"shape": {"kind": "circle", "radius": 10.0}}


def test_blueprint_as_serialization_input():
    # Verify that a sealed blueprint instance passed to the class's to_dict
    # returns its validated data directly.
    class DummyBlueprint(Blueprint):
        name: str

    bp = DummyBlueprint(data={"name": "Alice"})
    assert bp.is_sealed() is True

    # 1. Instance level to_dict()
    assert bp.to_dict() == {"name": "Alice"}

    # 2. Class level to_dict(bp)
    assert DummyBlueprint.to_dict(bp) == {"name": "Alice"}

    # 3. Class level to_dict_many([bp])
    assert DummyBlueprint.to_dict_many([bp]) == [{"name": "Alice"}]


def test_dataobject_dict_shadowing_and_json_serialization():
    from aquilia.utils.data import DataObject

    # 1. Standard dictionary containing keys matching method names
    data = DataObject({"items": [{"qty": 2, "price": 5.0}], "keys": ["a", "b"], "values": [1, 2], "get": "value"})

    # 2. Assert values are accessible via dot-notation (shadowing)
    assert data.items == [{"qty": 2, "price": 5.0}]
    assert data.keys == ["a", "b"]
    assert data.values == [1, 2]
    assert data.get == "value"

    # 3. Assert calling them as methods still invokes original dict methods
    assert list(data.items()) == [
        ("items", [{"qty": 2, "price": 5.0}]),
        ("keys", ["a", "b"]),
        ("values", [1, 2]),
        ("get", "value"),
    ]
    assert list(data.keys()) == ["items", "keys", "values", "get"]
    assert list(data.values()) == [[{"qty": 2, "price": 5.0}], ["a", "b"], [1, 2], "value"]

    # 4. Assert json serialization compiles cleanly
    import json

    from aquilia.response import _json_default_serializer

    serialized = json.dumps(data, default=_json_default_serializer)
    assert json.loads(serialized) == {
        "items": [{"qty": 2, "price": 5.0}],
        "keys": ["a", "b"],
        "values": [1, 2],
        "get": "value",
    }


def test_dataobject_advanced_features():
    import pytest

    from aquilia.utils.data import DataObject

    # 1. Deep recursive wrapping
    raw = {"user": {"name": "Kai", "roles": [{"name": "admin"}, {"name": "editor"}], "settings": ({"theme": "dark"},)}}
    data = DataObject(raw)
    assert isinstance(data.user, DataObject)
    assert isinstance(data.user.roles[0], DataObject)
    assert data.user.roles[0].name == "admin"
    assert isinstance(data.user.settings[0], DataObject)
    assert data.user.settings[0].theme == "dark"

    # Test that setting dynamic lists also wraps recursively
    data.user.new_roles = [{"name": "guest"}]
    assert isinstance(data.user.new_roles[0], DataObject)
    assert data.user.new_roles[0].name == "guest"

    # 2. Immutability / freezing
    assert data.is_frozen() is False
    data.freeze()
    assert data.is_frozen() is True
    assert data.user.is_frozen() is True
    assert data.user.roles[0].is_frozen() is True

    # Mutating frozen DataObject should raise TypeError
    with pytest.raises(TypeError, match="frozen"):
        data.user.name = "New"
    with pytest.raises(TypeError, match="frozen"):
        data["new_key"] = 1
    with pytest.raises(TypeError, match="frozen"):
        del data.user
    with pytest.raises(TypeError, match="frozen"):
        data.clear()

    # 3. Convenience Methods
    # Unfreeze to test update/merge
    unfrozen = DataObject(data.to_plain())
    assert unfrozen.is_frozen() is False

    # Find dot-path
    assert unfrozen.find("user.name") == "Kai"
    assert unfrozen.find("user.roles.0.name") == "admin"
    assert unfrozen.find("user.settings.0.theme") == "dark"
    assert unfrozen.find("user.non_existent", "Default") == "Default"

    # Flatten
    flat = unfrozen.flatten()
    assert flat["user.name"] == "Kai"
    assert flat["user.roles.0.name"] == "admin"
    assert flat["user.settings.0.theme"] == "dark"

    # Update recursive
    unfrozen.update_recursive({"user": {"name": "Kai A.", "settings": [{"theme": "light"}]}})
    assert unfrozen.user.name == "Kai A."
    assert isinstance(unfrozen.user.settings[0], DataObject)
    assert unfrozen.user.settings[0].theme == "light"

    # Merge
    merged = unfrozen.merge({"user": {"profile": "Developer"}})
    assert merged.user.name == "Kai A."
    assert merged.user.profile == "Developer"
    assert "profile" not in unfrozen.user  # Original is untouched

    # to_json
    js = unfrozen.to_json()
    assert '"theme": "light"' in js


def test_field_positional_default_and_ellipsis():
    from aquilia.blueprints import Field
    from aquilia.blueprints.facets import UNSET
    from aquilia.faults.domains import ConfigInvalidFault

    # 1. Test single positional default value
    f1 = Field("hello")
    assert f1.default == "hello"
    assert f1.required is None

    # 2. Test Ellipsis positional value
    f2 = Field(...)
    assert f2.default is UNSET
    assert f2.required is True

    # 3. Test multiple positional arguments should raise TypeError
    with pytest.raises(TypeError, match="takes at most 1 positional argument"):
        Field("hello", "world")

    # 4. Test both positional and keyword default should raise ConfigInvalidFault
    with pytest.raises(ConfigInvalidFault, match="Cannot specify both positional default/Ellipsis and keyword 'default'"):
        Field("hello", default="world")

    with pytest.raises(ConfigInvalidFault, match="Cannot specify both positional default/Ellipsis and keyword 'default'"):
        Field(..., default="Login Successfully")


def test_blueprint_with_field_ellipsis_validation():
    from aquilia.blueprints import Blueprint, Field

    class UserLoginBP(Blueprint):
        username: str = Field(...)
        message: str = Field(default="Login Successfully")

    # missing username should fail validation
    bp_fail = UserLoginBP(data={"message": "custom message"})
    assert bp_fail.is_sealed() is False
    assert "username" in bp_fail.errors

    # username provided should pass validation
    bp_pass = UserLoginBP(data={"username": "alice"})
    assert bp_pass.is_sealed() is True
    assert bp_pass.to_dict()["message"] == "Login Successfully"

