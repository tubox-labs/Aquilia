import asyncio
from typing import Annotated, Any
import pytest
from unittest.mock import MagicMock, AsyncMock

from aquilia.blueprints import Blueprint, Facet, ward
from aquilia.blueprints.core import BlueprintContext
from aquilia.di.core import Container
from aquilia.di.providers import BlueprintProvider, ValueProvider
from aquilia.di.dep import Dep, Header, Query
from aquilia.di.request_dag import RequestDAG
from aquilia.controller import Controller, GET, RequestCtx, ControllerFactory, InstantiationMode
from aquilia.controller.validation import validate_body
from aquilia.request import Request
from aquilia.response import Response

# ---------------------------------------------------------------------------
# Test Objects: Blueprints with Sync & Async Wards
# ---------------------------------------------------------------------------

class PromoService:
    async def exists(self, code: str) -> bool:
        return code == "SUPER10"


class AsyncWardBlueprint(Blueprint):
    code: str
    amount: float

    @ward(mode="async")
    async def validate_code(self, data):
        # Access string alias resolved from BlueprintContext fall-through
        promo_service = self.context["promo_service"]
        if not await promo_service.exists(data.code):
            self.reject("code", "Invalid promotion code")

    @ward
    def validate_amount(self, data):
        if data.amount <= 0:
            self.reject("amount", "Amount must be positive")


class MixedWardsBlueprint(Blueprint):
    val: int

    @ward
    def check_sync(self, data):
        if data.val == 0:
            self.reject("val", "Cannot be zero")

    @ward(mode="async")
    async def check_async(self, data):
        if data.val < 0:
            self.reject("val", "Cannot be negative")


# ---------------------------------------------------------------------------
# Findings 1 & 4: Async Ward Validation, Properties Bypass Protection & Context Alias
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_async_ward_validation_execution():
    """Verify that is_sealed_async runs both sync and async wards."""
    container = Container()
    container.register(ValueProvider(PromoService(), "promo_service"))

    context = {"container": container}
    
    # Valid Case
    bp = AsyncWardBlueprint(data={"code": "SUPER10", "amount": 100.0}, context=context)
    is_ok = await bp.is_sealed_async()
    assert is_ok is True
    assert bp.validated_data.code == "SUPER10"
    assert bp.validated_data.amount == 100.0

    # Invalid Case (Async Ward Rejected)
    bp2 = AsyncWardBlueprint(data={"code": "INVALID", "amount": 100.0}, context=context)
    is_ok = await bp2.is_sealed_async()
    assert is_ok is False
    assert "code" in bp2.errors

    # Invalid Case (Sync Ward Rejected)
    bp3 = AsyncWardBlueprint(data={"code": "SUPER10", "amount": -5.0}, context=context)
    is_ok = await bp3.is_sealed_async()
    assert is_ok is False
    assert "amount" in bp3.errors


def test_async_ward_sync_validation_fails_loudly():
    """Verify that calling is_sealed() on a blueprint with async wards raises RuntimeError."""
    bp = AsyncWardBlueprint(data={"code": "SUPER10", "amount": 100.0})
    with pytest.raises(RuntimeError, match="Blueprint contains async wards.*must be validated using is_sealed_async"):
        bp.is_sealed()


def test_validated_data_and_errors_properties_protected():
    """Verify accessing validated_data or errors properties before async seal raises RuntimeError."""
    bp = AsyncWardBlueprint(data={"code": "SUPER10", "amount": 100.0})
    with pytest.raises(RuntimeError, match="Blueprint contains async wards.*must be validated using await is_sealed_async"):
        _ = bp.validated_data

    with pytest.raises(RuntimeError, match="Blueprint contains async wards.*must be validated using await is_sealed_async"):
        _ = bp.errors


@pytest.mark.asyncio
async def test_async_ward_di_provider_auto_seal():
    """Verify BlueprintProvider with auto_seal=True executes async validation."""
    container = Container(scope="request")
    container.register(ValueProvider(PromoService(), "promo_service"))
    
    # Simulate Request
    req = MagicMock(spec=Request)
    req.headers = {"content-type": "application/json"}
    req.json = AsyncMock(return_value={"code": "SUPER10", "amount": 50.0})
    req.state = {"container": container}
    await container.register_instance(Request, req, scope="request")

    provider = BlueprintProvider(AsyncWardBlueprint, auto_seal=True)
    ctx = MagicMock()
    ctx.container = container

    bp_instance = await provider.instantiate(ctx)
    assert bp_instance.validated_data.code == "SUPER10"


@pytest.mark.asyncio
async def test_async_ward_request_dag_resolution():
    """Verify RequestDAG resolves Blueprint and runs async validation properly."""
    container = Container(scope="request")
    container.register(ValueProvider(PromoService(), "promo_service"))

    req = MagicMock(spec=Request)
    req.headers = {"content-type": "application/json"}
    req.json = AsyncMock(return_value={"code": "SUPER10", "amount": 50.0})
    req.state = {"container": container}
    await container.register_instance(Request, req, scope="request")

    dag = RequestDAG(container, request=req)
    dep = Dep()
    
    resolved = await dag._resolve_single_sub_dep("bp", AsyncWardBlueprint, None)
    assert isinstance(resolved, AsyncWardBlueprint)
    assert resolved.validated_data.amount == 50.0


@pytest.mark.asyncio
async def test_validate_body_decorator_runs_async_ward():
    """Verify validate_body decorator properly invokes async validation."""
    container = Container(scope="request")
    container.register(ValueProvider(PromoService(), "promo_service"))

    req = MagicMock(spec=Request)
    req.headers = {"content-type": "application/json"}
    # Return invalid data to trigger validation failure
    req.json = AsyncMock(return_value={"code": "INVALID", "amount": 10.0})
    req.state = {"container": container}
    
    ctx = MagicMock(spec=RequestCtx)
    ctx.request = req
    ctx.body = AsyncMock(return_value=b'{"code": "INVALID", "amount": 10.0}')
    ctx.container = container

    class DummyController:
        @validate_body(AsyncWardBlueprint)
        async def handle(self, ctx, body):
            return Response(b"Success", status=200)

    controller = DummyController()
    response = await controller.handle(ctx)
    assert response.status == 422


@pytest.mark.asyncio
async def test_multiple_async_wards_and_mixed_failure_propagation():
    """Verify failure propagation in mixed sync and async wards."""
    container = Container()
    
    # Sync fails
    bp = MixedWardsBlueprint(data={"val": 0}, context={"container": container})
    is_ok = await bp.is_sealed_async()
    assert is_ok is False
    assert bp.errors["val"] == ["Cannot be zero"]

    # Async fails
    bp2 = MixedWardsBlueprint(data={"val": -5}, context={"container": container})
    is_ok = await bp2.is_sealed_async()
    assert is_ok is False
    assert bp2.errors["val"] == ["Cannot be negative"]


@pytest.mark.asyncio
async def test_async_ward_cancellation_handling():
    """Verify that cancellation of async validation is properly propagated."""
    class LaggyPromoService:
        async def exists(self, code: str) -> bool:
            await asyncio.sleep(10.0)
            return True

    container = Container()
    container.register(ValueProvider(LaggyPromoService(), "promo_service"))

    bp = AsyncWardBlueprint(data={"code": "SUPER10", "amount": 100.0}, context={"container": container})

    task = asyncio.create_task(bp.is_sealed_async())
    await asyncio.sleep(0.01)
    task.cancel()

    with pytest.raises(asyncio.CancelledError):
        await task


# ---------------------------------------------------------------------------
# Finding 2: Controller Constructor Dependency Injection (Header, Query & request-aware extractors)
# ---------------------------------------------------------------------------

async def dummy_dep_fn(
    auth: Annotated[str, Header("Authorization")],
    limit: Annotated[int, Query("limit", default=10)],
) -> dict:
    return {"auth": auth, "limit": limit}


class DemoController(Controller):
    def __init__(self, data: Annotated[dict, Dep(dummy_dep_fn)]):
        self.data = data


@pytest.mark.asyncio
async def test_controller_constructor_di_with_extractors():
    """Verify constructor DI correctly resolves Header and Query extractors using RequestCtx."""
    container = Container(scope="request")
    
    # Create mock request with headers and query parameters
    req = MagicMock(spec=Request)
    req.headers = {"authorization": "Token secret123"}
    req.query_param = MagicMock(return_value="25")
    
    ctx = RequestCtx(request=req, container=container)

    factory = ControllerFactory(app_container=container)
    controller = await factory.create(
        DemoController,
        mode=InstantiationMode.PER_REQUEST,
        request_container=container,
        ctx=ctx,
    )

    assert isinstance(controller, DemoController)
    assert controller.data["auth"] == "Token secret123"
    assert controller.data["limit"] == 25


# ---------------------------------------------------------------------------
# Finding 3: Blueprint Provider Request Lookup & Scope Isolation
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_request_registration_and_scope_isolation():
    """Verify request token registration and concurrent scope isolation."""
    app_container = Container(scope="app")

    # Simulate Request A
    req_a = MagicMock(spec=Request)
    req_a.headers = {"x-request-id": "req_a"}
    container_a = app_container.create_request_scope()
    await container_a.register_instance(Request, req_a, scope="request")

    # Simulate Request B
    req_b = MagicMock(spec=Request)
    req_b.headers = {"x-request-id": "req_b"}
    container_b = app_container.create_request_scope()
    await container_b.register_instance(Request, req_b, scope="request")

    # Verify lookup returns correct request from respective containers
    resolved_a = await container_a.resolve_async(Request)
    resolved_b = await container_b.resolve_async(Request)

    assert resolved_a.headers["x-request-id"] == "req_a"
    assert resolved_b.headers["x-request-id"] == "req_b"


# ---------------------------------------------------------------------------
# Stress and Concurrency Validation
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_high_volume_concurrency_stress():
    """Verify framework architecture stability under concurrent stress."""
    app_container = Container(scope="app")
    app_container.register(ValueProvider(PromoService(), "promo_service"))

    async def run_single_operation(index: int):
        # 1. Create isolated request scope
        req_scope = app_container.create_request_scope()
        
        # 2. Mock request & register
        req = MagicMock(spec=Request)
        req.headers = {"content-type": "application/json"}
        req.json = AsyncMock(return_value={"code": "SUPER10", "amount": float(index)})
        req.state = {"container": req_scope}
        await req_scope.register_instance(Request, req, scope="request")

        # 3. Resolve using BlueprintProvider with auto_seal
        provider = BlueprintProvider(AsyncWardBlueprint, auto_seal=True)
        ctx = MagicMock()
        ctx.container = req_scope
        
        bp = await provider.instantiate(ctx)
        assert bp.validated_data.code == "SUPER10"
        assert bp.validated_data.amount == float(index)

    # Run 500 concurrent operations
    tasks = [run_single_operation(i) for i in range(1, 501)]
    await asyncio.gather(*tasks)
