from __future__ import annotations

import asyncio
import uuid
from datetime import date, datetime, time
from decimal import Decimal
from enum import Enum

import pytest

from aquilia._datastructures import MultiDict
from aquilia._uploads import FormData
from aquilia.blueprints import Blueprint, ChoiceFacet, ListFacet, NestedBlueprintFacet, TextFacet
from aquilia.blueprints.sigil import (
    extract_flat_list_mapping,
    extract_nested_mapping,
    get_field_value,
    get_keys,
    is_mapping_like,
)
from aquilia.controller.base import Controller, RequestCtx
from aquilia.controller.decorators import POST
from aquilia.controller.engine import ControllerEngine
from aquilia.request import Request

# ═══════════════════════════════════════════════════════════════════════════
#  Blueprint Definitions
# ═══════════════════════════════════════════════════════════════════════════


class StatusEnum(str, Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"


class ChildBlueprint(Blueprint):
    street: str
    city: str


class ProductBlueprint(Blueprint):
    name: str
    age: int
    price: float
    tags: list[str]


class ComprehensiveBlueprint(Blueprint):
    # Primitives
    name: str
    age: int
    price: float
    discount: Decimal
    is_active: bool

    # Date/Time/UUID
    created_at: datetime
    start_date: date
    alert_time: time
    id_uuid: uuid.UUID

    # Enum
    status: StatusEnum

    # Collections
    tags: list[str]
    metadata: dict

    # Nested Blueprint
    address: ChildBlueprint
    address = NestedBlueprintFacet(ChildBlueprint)

    # Optional / default / nullable
    description: str | None = None
    rating: int = 5


class UnionMemberABlueprint(Blueprint):
    type_field: str
    type_field = ChoiceFacet(choices=["A"])
    value_a: int


class UnionMemberBBlueprint(Blueprint):
    type_field: str
    type_field = ChoiceFacet(choices=["B"])
    value_b: str


# ═══════════════════════════════════════════════════════════════════════════
#  Helpers
# ═══════════════════════════════════════════════════════════════════════════


def make_mock_request(
    method: str = "POST",
    content_type: str | None = None,
    body: bytes = b"",
    query_string: bytes = b"",
) -> Request:
    headers = {}
    if content_type:
        headers["content-type"] = content_type
    headers["content-length"] = str(len(body))

    scope = {
        "type": "http",
        "method": method,
        "path": "/",
        "query_string": query_string,
        "headers": [(k.encode(), v.encode()) for k, v in headers.items()],
    }

    async def receive():
        return {"type": "http.request", "body": body}

    return Request(scope=scope, receive=receive)


def make_multipart_body(
    fields: dict[str, str | list[str]],
    files: dict[str, tuple[str, bytes, str]] | None = None,
    boundary: str = "33333333333333333333333333333333",
) -> bytes:
    lines = []
    for k, v in fields.items():
        if isinstance(v, list):
            for val in v:
                lines.append(f"--{boundary}")
                lines.append(f'Content-Disposition: form-data; name="{k}"')
                lines.append("")
                lines.append(str(val))
        else:
            lines.append(f"--{boundary}")
            lines.append(f'Content-Disposition: form-data; name="{k}"')
            lines.append("")
            lines.append(str(v))

    if files:
        for k, (filename, content, content_type) in files.items():
            lines.append(f"--{boundary}")
            lines.append(f'Content-Disposition: form-data; name="{k}"; filename="{filename}"')
            lines.append(f"Content-Type: {content_type}")
            lines.append("")
            if isinstance(content, str):
                content = content.encode("utf-8")
            lines.append(content)

    lines.append(f"--{boundary}--")
    lines.append("")

    body_parts = []
    for line in lines:
        if isinstance(line, bytes):
            body_parts.append(line)
        else:
            body_parts.append(line.encode("utf-8"))
    return b"\r\n".join(body_parts)


# ═══════════════════════════════════════════════════════════════════════════
#  Unit Tests: Mapping-Like Helpers
# ═══════════════════════════════════════════════════════════════════════════


def test_helper_is_mapping_like():
    assert is_mapping_like({}) is True
    assert is_mapping_like(MultiDict()) is True
    assert is_mapping_like(FormData()) is True
    assert is_mapping_like([]) is False
    assert is_mapping_like("string") is False


def test_helper_get_keys():
    d = {"a": 1, "b": 2}
    assert get_keys(d) == {"a", "b"}

    md = MultiDict()
    md.add("a", "1")
    md.add("c", "2")
    assert get_keys(md) == {"a", "c"}

    fd = FormData(fields=md, files={"file_field": []})
    assert get_keys(fd) == {"a", "c", "file_field"}


def test_helper_get_field_value_and_nested_mappings():
    # MultiDict
    md = MultiDict()
    md.add("name", "Ada")
    md.add("tags", "a")
    md.add("tags", "b")
    md.add("address.street", "Main St")
    md.add("address.city", "London")

    assert get_field_value(md, "name", TextFacet()) == "Ada"
    assert get_field_value(md, "tags", ListFacet()) == ["a", "b"]

    nested = extract_nested_mapping(md, "address")
    assert isinstance(nested, MultiDict)
    assert nested.get("street") == "Main St"
    assert nested.get("city") == "London"


def test_helper_flat_list_mapping():
    md = MultiDict()
    md.add("[0].street", "St 1")
    md.add("[0].city", "City 1")
    md.add("[1].street", "St 2")
    md.add("[1].city", "City 2")

    items = extract_flat_list_mapping(md)
    assert len(items) == 2
    assert isinstance(items[0], FormData) or isinstance(items[0], MultiDict)
    # Extract child values
    assert get_field_value(items[0], "street", TextFacet()) == "St 1"
    assert get_field_value(items[1], "city", TextFacet()) == "City 2"


# ═══════════════════════════════════════════════════════════════════════════
#  Integration Tests: Request Lifecycle & Formats
# ═══════════════════════════════════════════════════════════════════════════


def test_blueprint_json_validation_regression():
    data = {"name": "John", "age": 25, "price": 10.5, "tags": ["a", "b"]}
    bp = ProductBlueprint(data=data)
    assert bp.is_sealed() is True
    assert bp.validated_data["name"] == "John"
    assert bp.validated_data["age"] == 25
    assert bp.validated_data["price"] == 10.5
    assert bp.validated_data["tags"] == ["a", "b"]


def test_blueprint_form_urlencoded_validation():
    # application/x-www-form-urlencoded format
    form_data = MultiDict()
    form_data.add("name", "John")
    form_data.add("age", "25")
    form_data.add("price", "10.5")
    form_data.add("tags", "a")
    form_data.add("tags", "b")

    bp = ProductBlueprint(data=form_data)
    assert bp.is_sealed() is True
    assert bp.validated_data["name"] == "John"
    assert bp.validated_data["age"] == 25
    assert bp.validated_data["price"] == 10.5
    assert bp.validated_data["tags"] == ["a", "b"]


def test_blueprint_multipart_form_validation():
    # Construct a parsed multipart format
    fields = MultiDict()
    fields.add("name", "John")
    fields.add("age", "25")
    fields.add("price", "10.5")
    fields.add("tags[]", "a")
    fields.add("tags[]", "b")

    form_data = FormData(fields=fields, files={})
    bp = ProductBlueprint(data=form_data)
    assert bp.is_sealed() is True
    assert bp.validated_data["name"] == "John"
    assert bp.validated_data["age"] == 25
    assert bp.validated_data["price"] == 10.5
    assert bp.validated_data["tags"] == ["a", "b"]


def test_comprehensive_coercion_types_form():
    form_data = MultiDict()
    form_data.add("name", "Ada")
    form_data.add("age", "30")
    form_data.add("price", "99.99")
    form_data.add("discount", "15.50")
    form_data.add("is_active", "yes")  # bool coercion
    form_data.add("created_at", "2026-06-28T12:00:00")
    form_data.add("start_date", "2026-06-28")
    form_data.add("alert_time", "12:00:00")

    id_val = str(uuid.uuid4())
    form_data.add("id_uuid", id_val)
    form_data.add("status", "active")
    form_data.add("tags", "tech")
    form_data.add("tags", "science")
    form_data.add("metadata", '{"key": "val"}')  # JSON string fallback
    form_data.add("address.street", "10 Downing St")
    form_data.add("address.city", "London")
    form_data.add("description", "")  # Empty string coercion to None

    bp = ComprehensiveBlueprint(data=form_data)
    assert bp.is_sealed() is True
    vd = bp.validated_data
    assert vd["name"] == "Ada"
    assert vd["age"] == 30
    assert vd["price"] == 99.99
    assert vd["discount"] == Decimal("15.50")
    assert vd["is_active"] is True
    assert vd["created_at"] == datetime(2026, 6, 28, 12, 0, 0)
    assert vd["start_date"] == date(2026, 6, 28)
    assert vd["alert_time"] == time(12, 0, 0)
    assert vd["id_uuid"] == uuid.UUID(id_val)
    assert vd["status"] == StatusEnum.ACTIVE
    assert vd["tags"] == ["tech", "science"]
    assert vd["metadata"] == {"key": "val"}
    assert vd["address"]["street"] == "10 Downing St"
    assert vd["address"]["city"] == "London"
    assert vd["description"] is None
    assert vd["rating"] == 5  # default value


def test_blueprint_union_validation_from_form():
    union = UnionMemberABlueprint | UnionMemberBBlueprint

    # Try choice A
    form_a = MultiDict()
    form_a.add("type_field", "A")
    form_a.add("value_a", "123")

    errors, validated = union.validate(form_a)
    assert not errors
    assert validated["type_field"] == "A"
    assert validated["value_a"] == 123

    # Try choice B
    form_b = MultiDict()
    form_b.add("type_field", "B")
    form_b.add("value_b", "hello")

    errors, validated = union.validate(form_b)
    assert not errors
    assert validated["type_field"] == "B"
    assert validated["value_b"] == "hello"


# ═══════════════════════════════════════════════════════════════════════════
#  Controller Engine Parameter Binding Tests
# ═══════════════════════════════════════════════════════════════════════════


class ProductController(Controller):
    @POST("/")
    async def create(self, ctx: RequestCtx, product: ProductBlueprint):
        return product


@pytest.mark.asyncio
async def test_controller_engine_binds_form_urlencoded():
    # Setup mock request with form urlencoded body
    body_str = "name=John&age=25&price=10.5&tags=a&tags=b"
    req = make_mock_request(
        method="POST",
        content_type="application/x-www-form-urlencoded",
        body=body_str.encode("utf-8"),
    )

    ctx = RequestCtx(request=req)
    from aquilia.controller.factory import ControllerFactory

    engine = ControllerEngine(ControllerFactory())

    # Introspect/compile endpoint metadata
    from aquilia.controller.metadata import extract_controller_metadata

    meta = extract_controller_metadata(ProductController, "test:Product")
    route_meta = meta.routes[0]

    # Resolve parameter binding
    kwargs, _ = await engine._bind_parameters(route_meta, req, ctx, path_params={}, container=None)
    assert "product" in kwargs
    validated_product = kwargs["product"]
    assert validated_product["name"] == "John"
    assert validated_product["age"] == 25
    assert validated_product["price"] == 10.5
    assert validated_product["tags"] == ["a", "b"]


@pytest.mark.asyncio
async def test_controller_engine_binds_multipart():
    body_bytes = make_multipart_body(
        fields={
            "name": "Jane",
            "age": "28",
            "price": "24.50",
            "tags[]": ["x", "y"],
        }
    )
    req = make_mock_request(
        method="POST",
        content_type="multipart/form-data; boundary=33333333333333333333333333333333",
        body=body_bytes,
    )

    ctx = RequestCtx(request=req)
    from aquilia.controller.factory import ControllerFactory

    engine = ControllerEngine(ControllerFactory())

    from aquilia.controller.metadata import extract_controller_metadata

    meta = extract_controller_metadata(ProductController, "test:Product")
    route_meta = meta.routes[0]

    kwargs, _ = await engine._bind_parameters(route_meta, req, ctx, path_params={}, container=None)
    assert "product" in kwargs
    validated_product = kwargs["product"]
    assert validated_product["name"] == "Jane"
    assert validated_product["age"] == 28
    assert validated_product["price"] == 24.50
    assert validated_product["tags"] == ["x", "y"]


# ═══════════════════════════════════════════════════════════════════════════
#  Edge Cases
# ═══════════════════════════════════════════════════════════════════════════


def test_missing_and_invalid_values_form():
    # Missing required field 'price'
    form_data = MultiDict()
    form_data.add("name", "John")
    form_data.add("age", "25")
    form_data.add("tags", "a")

    bp = ProductBlueprint(data=form_data)
    assert bp.is_sealed() is False
    assert "price" in bp.errors
    assert bp.errors["price"] == ["This field is required"]

    # Invalid integer type for 'age'
    form_data = MultiDict()
    form_data.add("name", "John")
    form_data.add("age", "not-an-int")
    form_data.add("price", "10.5")
    form_data.add("tags", "a")

    bp = ProductBlueprint(data=form_data)
    assert bp.is_sealed() is False
    assert "age" in bp.errors
    assert "integer" in "".join(bp.errors["age"]).lower()


def test_empty_string_coercion_rules():
    class TestEmptyStringBlueprint(Blueprint):
        required_int: int
        optional_int: int | None = None
        required_str: str
        optional_str: str | None = None

    # Empty string passed to required_int -> should fail validation (cannot convert "" to int, and is required)
    form_data = MultiDict()
    form_data.add("required_int", "")
    form_data.add("required_str", "hello")

    bp = TestEmptyStringBlueprint(data=form_data)
    assert bp.is_sealed() is False
    assert "required_int" in bp.errors

    # Empty string passed to optional_int -> should succeed (coerced to None)
    form_data = MultiDict()
    form_data.add("required_int", "12")
    form_data.add("optional_int", "")
    form_data.add("required_str", "hello")

    bp = TestEmptyStringBlueprint(data=form_data)
    assert bp.is_sealed() is True
    assert bp.validated_data["optional_int"] is None
    assert bp.validated_data["required_str"] == "hello"


# ═══════════════════════════════════════════════════════════════════════════
#  Stress and Concurrency Tests
# ═══════════════════════════════════════════════════════════════════════════


@pytest.mark.asyncio
async def test_concurrent_blueprint_validation_stress():
    # Simulate multiple concurrent validations of form data
    async def validate_one(i: int):
        form_data = MultiDict()
        form_data.add("name", f"Product-{i}")
        form_data.add("age", str(20 + i % 10))
        form_data.add("price", str(10.5 + i))
        form_data.add("tags", f"tag-{i}")
        form_data.add("tags", "all")

        bp = ProductBlueprint(data=form_data)
        assert bp.is_sealed() is True
        assert bp.validated_data["name"] == f"Product-{i}"
        assert len(bp.validated_data["tags"]) == 2

    # Run 100 validations concurrently
    tasks = [validate_one(i) for i in range(100)]
    await asyncio.gather(*tasks)
