import pytest
from datetime import date, datetime
from enum import Enum
import uuid
from typing import Annotated, Literal

from aquilia.blueprints import Blueprint, ward, Facet
from aquilia.blueprints.annotations import Field
from aquilia.blueprints.core import BlueprintUnion
from aquilia.blueprints.exceptions import SealFault

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
            self.reject(
                "total",
                f"Expected {computed}, got {data.total}"
            )

    @ward(mode="async")
    async def discount_code_is_valid(self, data):
        if (
            data.discount_code
            and not await self.context["promo_service"].exists(
                data.discount_code
            )
        ):
            self.reject(
                "discount_code",
                "Unknown or expired code"
            )

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
