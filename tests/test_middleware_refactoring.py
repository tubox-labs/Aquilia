from unittest.mock import MagicMock
import pytest
from aquilia.middleware import Middleware, MiddlewareStack
from aquilia.request import Request
from aquilia.response import Response
from aquilia.di import RequestCtx


# 1. Test Base class inheritance
def test_middleware_inheritance():
    assert issubclass(Middleware, object)


# 2. Test successful addition of valid middleware
@pytest.mark.asyncio
async def test_valid_middleware_addition():
    stack = MiddlewareStack()

    class ValidMiddleware(Middleware):
        async def __call__(self, request: Request, ctx: RequestCtx, next_handler):
            return await next_handler(request, ctx)

    # Adding valid class
    stack.add(ValidMiddleware(), name="valid")
    # Verify it is in active list
    descriptors = stack.middlewares
    assert len(descriptors) == 1
    assert descriptors[0].name == "valid"


# 3. Test startup validation: non-callable, wrong class, wrong signature, non-async
def test_invalid_middleware_validation():
    stack = MiddlewareStack()

    # Case A: Does not inherit from Middleware (and is a class)
    class NoInherit:
        async def __call__(self, request, ctx, next_handler):
            pass

    with pytest.raises(TypeError, match="must inherit from the 'Middleware' base class"):
        stack.add(NoInherit(), name="no_inherit")

    # Case B: Callable has wrong parameter count (needs exactly 3 parameters after self)
    class WrongParamCount(Middleware):
        async def __call__(self, request, next_handler):
            pass

    with pytest.raises(TypeError, match="has an invalid signature"):
        stack.add(WrongParamCount(), name="wrong_params")

    # Case C: Not a coroutine function (non-async __call__)
    class NonAsync(Middleware):
        def __call__(self, request, ctx, next_handler):
            pass

    with pytest.raises(TypeError, match="must be a coroutine function"):
        stack.add(NonAsync(), name="non_async")


# 4. Test runtime safeguards: None return (broken chain)
@pytest.mark.asyncio
async def test_runtime_safeguard_none_return():
    stack = MiddlewareStack()

    class BrokenChainMiddleware(Middleware):
        async def __call__(self, request, ctx, next_handler):
            # Forgot to call next_handler or return Response
            return None

    stack.add(BrokenChainMiddleware(), name="broken")
    
    async def final_handler(request, ctx):
        return Response(b"ok")

    handler = stack.build_handler(final_handler)
    
    # Executing the handler should raise RuntimeError
    req = MagicMock(spec=Request)
    ctx = MagicMock(spec=RequestCtx)
    
    with pytest.raises(RuntimeError, match="returned None instead of a Response object"):
        await handler(req, ctx)


# 5. Test runtime safeguards: non-Response return
@pytest.mark.asyncio
async def test_runtime_safeguard_invalid_type_return():
    stack = MiddlewareStack()

    class InvalidReturnMiddleware(Middleware):
        async def __call__(self, request, ctx, next_handler):
            return "not a response object"

    stack.add(InvalidReturnMiddleware(), name="invalid")
    
    async def final_handler(request, ctx):
        return Response(b"ok")

    handler = stack.build_handler(final_handler)
    
    req = MagicMock(spec=Request)
    ctx = MagicMock(spec=RequestCtx)
    
    with pytest.raises(TypeError, match="returned invalid type 'str' instead of a Response object"):
        await handler(req, ctx)


# 6. Test execution ordering and parameter propagation
@pytest.mark.asyncio
async def test_execution_order_and_propagation():
    stack = MiddlewareStack()
    calls = []

    class Middleware1(Middleware):
        async def __call__(self, request, ctx, next_handler):
            calls.append("mw1_start")
            res = await next_handler(request, ctx)
            calls.append("mw1_end")
            return res

    class Middleware2(Middleware):
        async def __call__(self, request, ctx, next_handler):
            calls.append("mw2_start")
            res = await next_handler(request, ctx)
            calls.append("mw2_end")
            return res

    # Priority of Middleware1 is lower (runs first because of stack order/priority)
    stack.add(Middleware1(), name="mw1", priority=10)
    stack.add(Middleware2(), name="mw2", priority=20)

    async def final_handler(request, ctx):
        calls.append("final")
        return Response(b"ok")

    handler = stack.build_handler(final_handler)
    
    req = MagicMock(spec=Request)
    ctx = MagicMock(spec=RequestCtx)
    
    res = await handler(req, ctx)
    assert res._content == b"ok"
    # mw1 (priority 10) runs before mw2 (priority 20)
    assert calls == ["mw1_start", "mw2_start", "final", "mw2_end", "mw1_end"]
