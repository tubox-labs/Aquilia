from __future__ import annotations

import json

import pytest

from aquilia.blueprints import Blueprint, NestedBlueprintFacet
from aquilia.blueprints.exceptions import SealFault
from aquilia.controller.base import Controller, RequestCtx
from aquilia.controller.compiler import ControllerCompiler
from aquilia.controller.decorators import POST
from aquilia.controller.engine import ControllerEngine
from aquilia.controller.factory import ControllerFactory
from aquilia.controller.metadata import extract_controller_metadata
from aquilia.request import Request

# ═══════════════════════════════════════════════════════════════════════════
#  Blueprints Setup
# ═══════════════════════════════════════════════════════════════════════════


class OrderBlueprint(Blueprint):
    order_id: int
    item_name: str


class ArticleBlueprint(Blueprint):
    article_id: int
    title: str


class ChildBlueprint(Blueprint):
    street: str
    city: str


class NestedBlueprint(Blueprint):
    name: str
    address: ChildBlueprint
    address = NestedBlueprintFacet(ChildBlueprint)


# ═══════════════════════════════════════════════════════════════════════════
#  Controllers Setup
# ═══════════════════════════════════════════════════════════════════════════


class MultiBlueprintController(Controller):
    @POST("/order")
    async def order_async(self, ctx: RequestCtx, orders: OrderBlueprint, article: ArticleBlueprint):
        return {"orders": orders.validated_data, "article": article.validated_data}

    @POST("/order_sync")
    def order_sync(self, ctx: RequestCtx, orders: OrderBlueprint, article: ArticleBlueprint):
        return {"orders": orders.validated_data, "article": article.validated_data}

    @POST("/single")
    async def single(self, ctx: RequestCtx, orders: OrderBlueprint):
        return {"orders": orders.validated_data}

    @POST("/nested")
    async def nested(self, ctx: RequestCtx, orders: OrderBlueprint, profile: NestedBlueprint):
        return {"orders": orders.validated_data, "profile": profile.validated_data}


# ═══════════════════════════════════════════════════════════════════════════
#  Helpers
# ═══════════════════════════════════════════════════════════════════════════


def make_mock_request(
    method: str = "POST",
    content_type: str | None = "application/json",
    body: dict | bytes = b"",
) -> Request:
    headers = {}
    if content_type:
        headers["content-type"] = content_type

    if isinstance(body, dict):
        body_bytes = json.dumps(body).encode("utf-8")
    else:
        body_bytes = body

    headers["content-length"] = str(len(body_bytes))

    scope = {
        "type": "http",
        "method": method,
        "path": "/",
        "query_string": b"",
        "headers": [(k.encode(), v.encode()) for k, v in headers.items()],
    }

    async def receive():
        return {"type": "http.request", "body": body_bytes}

    return Request(scope=scope, receive=receive)


# ═══════════════════════════════════════════════════════════════════════════
#  Tests
# ═══════════════════════════════════════════════════════════════════════════


@pytest.mark.asyncio
async def test_single_blueprint_parameter():
    """Verify that a handler with one blueprint parameter parses and resolves correctly."""
    payload = {"order_id": 123, "item_name": "Keyboard"}
    req = make_mock_request(body=payload)
    ctx = RequestCtx(request=req)

    engine = ControllerEngine(ControllerFactory())
    meta = extract_controller_metadata(MultiBlueprintController, "test:MultiBlueprint")

    # Find route metadata for single
    route_meta = next(r for r in meta.routes if r.handler_name == "single")

    kwargs, _ = await engine._bind_parameters(route_meta, req, ctx, path_params={}, container=None)

    assert "orders" in kwargs
    assert kwargs["orders"]["order_id"] == 123
    assert kwargs["orders"]["item_name"] == "Keyboard"


@pytest.mark.asyncio
async def test_multiple_blueprint_parameters():
    """Verify that a handler with two blueprint parameters resolves both from the same body."""
    payload = {
        "order_id": 456,
        "item_name": "Mouse",
        "article_id": 789,
        "title": "Unboxing Mouse",
    }
    req = make_mock_request(body=payload)
    ctx = RequestCtx(request=req)

    engine = ControllerEngine(ControllerFactory())
    meta = extract_controller_metadata(MultiBlueprintController, "test:MultiBlueprint")

    # Find route metadata for order_async
    route_meta = next(r for r in meta.routes if r.handler_name == "order_async")

    kwargs, _ = await engine._bind_parameters(route_meta, req, ctx, path_params={}, container=None)

    assert "orders" in kwargs
    assert "article" in kwargs

    assert kwargs["orders"]["order_id"] == 456
    assert kwargs["orders"]["item_name"] == "Mouse"
    assert kwargs["article"]["article_id"] == 789
    assert kwargs["article"]["title"] == "Unboxing Mouse"


@pytest.mark.asyncio
async def test_invalid_payloads_consolidated_errors():
    """Verify validation fails cleanly and consolidates errors from all failed blueprint parameters."""
    # Invalid payloads for both: order_id is missing, item_name is missing,
    # article_id is string that can't cast to int, title is missing.
    payload = {
        "article_id": "not-an-int",
    }
    req = make_mock_request(body=payload)
    ctx = RequestCtx(request=req)

    engine = ControllerEngine(ControllerFactory())
    meta = extract_controller_metadata(MultiBlueprintController, "test:MultiBlueprint")
    route_meta = next(r for r in meta.routes if r.handler_name == "order_async")

    with pytest.raises(SealFault) as exc_info:
        await engine._bind_parameters(route_meta, req, ctx, path_params={}, container=None)

    errors = exc_info.value.field_errors
    # Should contain errors from both blueprints
    assert "order_id" in errors  # from OrderBlueprint
    assert "item_name" in errors  # from OrderBlueprint
    assert "article_id" in errors  # from ArticleBlueprint
    assert "title" in errors  # from ArticleBlueprint


@pytest.mark.asyncio
async def test_nested_blueprint_validation():
    """Verify that a blueprint parameter with nested fields validates successfully or raises proper nested error."""
    payload = {
        "order_id": 111,
        "item_name": "Laptop",
        "name": "John Doe",
        "address": {
            "street": "123 Main St",
            # city is missing!
        },
    }
    req = make_mock_request(body=payload)
    ctx = RequestCtx(request=req)

    engine = ControllerEngine(ControllerFactory())
    meta = extract_controller_metadata(MultiBlueprintController, "test:MultiBlueprint")
    route_meta = next(r for r in meta.routes if r.handler_name == "nested")

    with pytest.raises(SealFault) as exc_info:
        await engine._bind_parameters(route_meta, req, ctx, path_params={}, container=None)

    errors = exc_info.value.field_errors
    assert "address" in errors
    assert "city" in errors["address"]


@pytest.mark.asyncio
async def test_engine_execution_sync_and_async():
    """Verify the full execute cycle runs successfully for sync and async handlers with multiple blueprints."""
    payload = {
        "order_id": 456,
        "item_name": "Mouse",
        "article_id": 789,
        "title": "Unboxing Mouse",
    }

    compiler = ControllerCompiler()
    compiled_controller = compiler.compile_controller(MultiBlueprintController)

    # 1. Test async handler
    req_async = make_mock_request(body=payload)
    engine = ControllerEngine(ControllerFactory())

    compiled_async = next(r for r in compiled_controller.routes if r.route_metadata.handler_name == "order_async")

    from aquilia.di import Container

    container = Container()

    response_async = await engine.execute(compiled_async, req_async, path_params={}, container=container)
    assert response_async.status == 200

    content_async = response_async._content
    if isinstance(content_async, bytes):
        content_async = content_async.decode("utf-8")
    res_data = json.loads(content_async)
    assert res_data["orders"]["order_id"] == 456
    assert res_data["article"]["title"] == "Unboxing Mouse"

    # 2. Test sync handler
    req_sync = make_mock_request(body=payload)
    compiled_sync = next(r for r in compiled_controller.routes if r.route_metadata.handler_name == "order_sync")

    response_sync = await engine.execute(compiled_sync, req_sync, path_params={}, container=container)
    assert response_sync.status == 200

    content_sync = response_sync._content
    if isinstance(content_sync, bytes):
        content_sync = content_sync.decode("utf-8")
    res_data_sync = json.loads(content_sync)
    assert res_data_sync["orders"]["order_id"] == 456
    assert res_data_sync["article"]["title"] == "Unboxing Mouse"


from typing import Annotated

from aquilia.blueprints import Facet, ward
from aquilia.blueprints.transforms import dasherize, lower, strip


# Define User's OrderItemBlueprint
class UserOrderItemBlueprint(Blueprint):
    product_id: int
    qty: Annotated[int, Facet.int[1:]]
    price: Annotated[float, Facet.float[0:]]


# Define User's OrderBlueprint
class UserOrderBlueprint(Blueprint):
    items: list[UserOrderItemBlueprint]
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


# Define User's ArticleBlueprint
class UserArticleBlueprint(Blueprint):
    slug: Annotated[str, Facet.text() >> strip >> lower >> dasherize >> Facet.pattern(r"^[a-z0-9-]+$")]


# Define Controller
class UserOrderController(Controller):
    @POST("/order")
    async def order(self, ctx: RequestCtx, orders: UserOrderBlueprint, article: UserArticleBlueprint):
        return {"orders": orders.validated_data, "article": article.validated_data}


# Define PromoService
class PromoService:
    async def exists(self, code: str) -> bool:
        return code == "SAVE50"


@pytest.mark.asyncio
async def test_blueprint_context_di_service_resolution():
    """Verify that a blueprint's async ward method can resolve and invoke registered services from the DI container via self.context."""
    # Compile routes
    compiler = ControllerCompiler()
    compiled_controller = compiler.compile_controller(UserOrderController)
    compiled_route = compiled_controller.routes[0]

    # Register services in DI container
    from aquilia.di import Container

    container = Container()
    container.bind("promo_service", PromoService, scope="singleton")

    # 1. Test valid payload
    payload_valid = {
        "items": [
            {"product_id": 1, "qty": 2, "price": 10.0},
            {"product_id": 2, "qty": 1, "price": 5.0},
        ],
        "total": 25.0,
        "discount_code": "SAVE50",
        "slug": "  Cool-Product-Title  ",
    }

    req_valid = make_mock_request(body=payload_valid)
    engine = ControllerEngine(ControllerFactory())

    try:
        response = await engine.execute(compiled_route, req_valid, path_params={}, container=container)
    except SealFault as e:
        raise AssertionError(f"Validation failed with errors: {e.field_errors}")
    assert response.status == 200

    content = response._content
    if isinstance(content, bytes):
        content = content.decode("utf-8")
    res_data = json.loads(content)

    # Assert valid data parsed and coerced/transformed slug
    assert res_data["orders"]["total"] == 25.0
    assert res_data["orders"]["discount_code"] == "SAVE50"
    assert res_data["article"]["slug"] == "cool-product-title"

    # 2. Test invalid payload (invalid discount code)
    payload_invalid = {
        "items": [
            {"product_id": 1, "qty": 2, "price": 10.0},
        ],
        "total": 20.0,
        "discount_code": "INVALID_CODE",
        "slug": "product-slug",
    }

    req_invalid = make_mock_request(body=payload_invalid)

    with pytest.raises(SealFault) as exc_info:
        await engine._bind_parameters(
            compiled_route.route_metadata,
            req_invalid,
            RequestCtx(request=req_invalid),
            path_params={},
            container=container,
        )

    errors = exc_info.value.field_errors
    assert "discount_code" in errors
    assert errors["discount_code"] == ["Unknown or expired code"]
