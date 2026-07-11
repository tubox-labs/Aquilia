import inspect
from unittest.mock import MagicMock

import pytest

from aquilia.auth import authenticated, exempt
from aquilia.auth.core import Identity, IdentityType
from aquilia.auth.guards import AuthGuard
from aquilia.auth.integration.aquila_sessions import AuthPrincipal
from aquilia.controller.base import Controller, RequestCtx
from aquilia.controller.decorators import GET
from aquilia.controller.engine import ControllerEngine
from aquilia.controller.metadata import _extract_method_params
from aquilia.di import Container
from aquilia.sessions import Session, SessionPrincipal


class DummyController(Controller):
    @GET("/me")
    @authenticated
    async def dashboard(self, ctx: RequestCtx, identity: Identity, session: Session, principal: SessionPrincipal):
        return {"identity": identity, "session": session, "principal": principal}

    @GET("/public")
    @exempt
    async def public_route(self, ctx: RequestCtx):
        return {"status": "public"}


def _make_request(method="GET", path="/", headers=None, state=None):
    from aquilia.request import Request

    scope = {
        "type": "http",
        "method": method,
        "path": path,
        "headers": [(k.encode(), v.encode()) for k, v in (headers or {}).items()],
    }

    async def receive():
        return {"type": "http.request", "body": b""}

    req = Request(scope=scope, receive=receive)
    if state:
        req.state.update(state)
    return req


def _make_ctx(request=None, **kwargs):
    req = request or _make_request()
    return RequestCtx(
        request=req,
        identity=kwargs.get("identity"),
        session=kwargs.get("session"),
        container=kwargs.get("container"),
        state=kwargs.get("state", {}),
    )


def test_metadata_source_classification():
    """Verify SessionPrincipal and AuthPrincipal are classified as DI source."""
    sig = inspect.signature(DummyController.dashboard)
    params = _extract_method_params(DummyController.dashboard, sig, "/me")

    param_map = {p.name: p for p in params}

    assert "identity" in param_map
    assert param_map["identity"].source == "di"

    assert "session" in param_map
    assert param_map["session"].source == "di"

    assert "principal" in param_map
    assert param_map["principal"].source == "di"


@pytest.mark.asyncio
async def test_multiple_parameter_injection_in_decorator():
    """Verify all requested parameters are injected by @authenticated decorator."""
    identity = Identity(id="user_123", type=IdentityType.USER, attributes={})
    session = Session(id="sess_123")
    session.mark_authenticated(AuthPrincipal.from_identity(identity))

    func_kwargs = {
        "ctx": MagicMock(spec=RequestCtx),
        "identity": identity,
        "session": session,
    }

    @authenticated
    async def dummy_handler(ctx, identity: Identity, session: Session, principal: SessionPrincipal):
        return identity, session, principal

    res_identity, res_session, res_principal = await dummy_handler(**func_kwargs)

    assert res_identity is identity
    assert res_session is session
    assert isinstance(res_principal, AuthPrincipal)
    assert res_principal.id == "user_123"


@pytest.mark.asyncio
async def test_engine_resolves_principal_proactively():
    """Verify ControllerEngine proactively extracts principal from session/identity if missing from DI."""
    container = Container()
    identity = Identity(id="user_456", type=IdentityType.USER, attributes={})
    session = Session(id="sess_456")
    session.mark_authenticated(AuthPrincipal.from_identity(identity))

    req = _make_request(state={"session": session, "identity": identity})
    ctx = _make_ctx(request=req, session=session, identity=identity, container=container)

    # We do NOT register SessionPrincipal in the container, to test proactive fallback
    engine = ControllerEngine(MagicMock(), MagicMock())

    class TestController(Controller):
        async def my_handler(self, principal: SessionPrincipal):
            return principal

    # Mock route metadata
    route_metadata = MagicMock()
    sig = inspect.signature(TestController.my_handler)
    route_metadata.parameters = _extract_method_params(TestController.my_handler, sig, "/")

    kwargs, _ = await engine._bind_parameters(route_metadata, req, ctx, {}, container)

    assert "principal" in kwargs
    assert isinstance(kwargs["principal"], AuthPrincipal)
    assert kwargs["principal"].id == "user_456"


@pytest.mark.asyncio
async def test_exempt_bypasses_class_level_auth_guard():
    """Verify @exempt routes bypass class-level AuthGuard in pipeline."""
    from aquilia.controller.factory import ControllerFactory

    factory = ControllerFactory()
    engine = ControllerEngine(factory)

    # Setup mock AuthGuard that always raises AUTH_REQUIRED
    class StrictAuthGuard(AuthGuard):
        async def __call__(self, context):
            from aquilia.auth.faults import AUTH_REQUIRED

            raise AUTH_REQUIRED()

    class SecureController(Controller):
        pipeline = [StrictAuthGuard()]

        @GET("/login")
        @exempt
        async def login(self, ctx):
            return {"status": "ok"}

    # Access metadata of CompiledRoute
    from aquilia.controller.compiler import ControllerCompiler

    compiler = ControllerCompiler()
    compiled = compiler.compile_controller(SecureController)
    route = compiled.routes[0]  # The login route

    req = _make_request(path="/login")
    ctx = _make_ctx(request=req, container=Container())

    # Executing the route should NOT raise AUTH_REQUIRED because it's exempt
    response = await engine.execute(route, req, {}, ctx.container)

    assert response is not None
    assert response.status == 200
    assert "ok" in response._content
