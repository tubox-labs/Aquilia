from unittest.mock import MagicMock

import pytest

from aquilia.controller.base import RequestCtx
from aquilia.controller.engine import ControllerEngine
from aquilia.di import Container
from aquilia.effects import EffectProvider, EffectRegistry
from aquilia.flow import FlowContext
from aquilia.request import Request


@pytest.mark.asyncio
async def test_special_parameter_injection():
    container = Container()
    req = MagicMock(spec=Request)
    req.state = {}
    ctx = MagicMock(spec=RequestCtx)
    ctx.container = container
    ctx.request = req

    engine = ControllerEngine(MagicMock(), MagicMock())

    # Case 1: Method has req: RequestCtx
    async def handler_with_req(self, req: RequestCtx):
        pass

    kwargs = {}
    engine._bind_special_parameters(handler_with_req, req, ctx, kwargs)
    assert kwargs["req"] is ctx

    # Case 2: Method has request: Request
    async def handler_with_request(self, request: Request):
        pass

    kwargs = {}
    engine._bind_special_parameters(handler_with_request, req, ctx, kwargs)
    assert kwargs["request"] is req

    # Case 3: Method has custom named req of type Request
    async def handler_with_custom_req_type(self, my_req: Request):
        pass

    kwargs = {}
    engine._bind_special_parameters(handler_with_custom_req_type, req, ctx, kwargs)
    assert kwargs["my_req"] is req

    # Case 4: Method has ctx: FlowContext
    async def handler_with_flow_ctx(self, ctx: FlowContext):
        pass

    kwargs = {}
    engine._bind_special_parameters(handler_with_flow_ctx, req, ctx, kwargs)
    assert isinstance(kwargs["ctx"], FlowContext)
    assert kwargs["ctx"].request is req


@pytest.mark.asyncio
async def test_flow_context_effect_resolution():
    registry = EffectRegistry()

    class MockCacheProvider(EffectProvider):
        async def initialize(self):
            pass

        async def acquire(self, mode=None):
            return "mocked_cache_resource"

        async def release(self, resource, success=True):
            pass

    registry.register("Cache", MockCacheProvider())
    await registry.initialize_all()

    # Mock request
    req = MagicMock(spec=Request)
    # Mock state
    state_dict = {"effects": {"Cache": "mocked_cache_resource"}}
    req.state = state_dict

    # Mock get_effect / has_effect on Request
    def get_effect(name: str):
        effects = state_dict.get("effects", {})
        if name in effects:
            return effects[name]
        raise KeyError(name)

    def has_effect(name: str):
        return name in state_dict.get("effects", {})

    req.get_effect = get_effect
    req.has_effect = has_effect

    # 1. FlowContext should inherit pre-acquired effects from request
    flow_ctx = FlowContext(request=req)
    assert flow_ctx.get_effect("Cache") == "mocked_cache_resource"
    assert flow_ctx.has_effect("Cache") is True

    # 2. RequestCtx should delegate get_effect and has_effect to request
    ctx = RequestCtx(request=req)
    assert ctx.get_effect("Cache") == "mocked_cache_resource"
    assert ctx.has_effect("Cache") is True
