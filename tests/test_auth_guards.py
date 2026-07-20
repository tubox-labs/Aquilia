"""
Brutal test suite for flat AquilAuth Guard System and Decorators.

Verifies:
1. First-class API: Class references in Flow pipelines (e.g. `pipeline = [AuthGuard]`)
2. First-class API: Class instances in Flow pipelines (e.g. `pipeline = [AuthGuard()]`)
3. Composable `requires` decorator with both class references and instances
4. Flat file exports and integration with Flow pipelines
5. Ctx-first decorators (`@authenticated`, `@roles_required`, `@scopes_required`, `@optional_auth`)
"""

from __future__ import annotations

from typing import Any

import pytest

from aquilia.auth.core import Identity, IdentityStatus, IdentityType
from aquilia.auth.decorators import authenticated, optional_auth, roles_required, scopes_required
from aquilia.auth.guards import AuthGuard, RoleGuard, ScopeGuard, requires
from aquilia.flow import FlowContext, FlowPipeline, FlowStatus


class MockIdentityStore:
    async def get(self, identity_id: str) -> Identity | None:
        return Identity(
            id=identity_id,
            type=IdentityType.USER,
            attributes={"email": "test@example.com", "roles": ["admin"]},
            status=IdentityStatus.ACTIVE,
        )


class FakeRequest:
    def __init__(self, identity: Identity | None = None) -> None:
        self.state = {"identity": identity}


class FakeCtx:
    def __init__(self, identity: Identity | None = None) -> None:
        self.identity = identity
        self.request = FakeRequest(identity)


@pytest.mark.asyncio
async def test_auth_guard_as_class_in_flow_pipeline():
    """Verify that passing the raw class AuthGuard works inside a Flow pipeline."""
    # 1. Without identity -> must fail/raise
    flow_ctx_anonymous = FlowContext()
    flow_ctx_anonymous.identity = None  # type: ignore[attr-defined]

    pipe = FlowPipeline("test_pipe")
    pipe.guard(AuthGuard)

    result = await pipe.execute(flow_ctx_anonymous)
    assert result.status == FlowStatus.GUARDED
    from aquilia.auth.faults import AUTH_REQUIRED

    assert isinstance(result.error, AUTH_REQUIRED)

    # 2. With identity -> must pass
    flow_ctx_auth = FlowContext()
    identity = Identity(
        id="usr_123",
        type=IdentityType.USER,
        attributes={"roles": ["user"]},
        status=IdentityStatus.ACTIVE,
    )
    flow_ctx_auth.identity = identity  # type: ignore[attr-defined]

    result_auth = await pipe.execute(flow_ctx_auth)
    assert result_auth.status == FlowStatus.SUCCESS


@pytest.mark.asyncio
async def test_auth_guard_as_instance_in_flow_pipeline():
    """Verify that passing the AuthGuard() instance works inside a Flow pipeline."""
    flow_ctx_anonymous = FlowContext()
    flow_ctx_anonymous.identity = None  # type: ignore[attr-defined]

    pipe = FlowPipeline("test_pipe")
    pipe.guard(AuthGuard(optional=False))

    result = await pipe.execute(flow_ctx_anonymous)
    assert result.status == FlowStatus.GUARDED


@pytest.mark.asyncio
async def test_role_guard_in_flow_pipeline():
    """Verify RoleGuard checking roles on the flow context identity."""
    flow_ctx = FlowContext()
    flow_ctx.identity = Identity(
        id="usr_123",
        type=IdentityType.USER,
        attributes={"roles": ["user"]},
        status=IdentityStatus.ACTIVE,
    )  # type: ignore[attr-defined]

    # Required role "admin" is missing -> must fail
    pipe = FlowPipeline("test_pipe")
    pipe.guard(RoleGuard("admin"))
    result = await pipe.execute(flow_ctx)
    assert result.status == FlowStatus.GUARDED
    from aquilia.auth.faults import AUTHZ_INSUFFICIENT_ROLE

    assert isinstance(result.error, AUTHZ_INSUFFICIENT_ROLE)

    # Required role "user" matches -> must pass
    pipe_ok = FlowPipeline("test_pipe_ok")
    pipe_ok.guard(RoleGuard("user"))
    result_ok = await pipe_ok.execute(flow_ctx)
    assert result_ok.status == FlowStatus.SUCCESS


@pytest.mark.asyncio
async def test_scope_guard_in_flow_pipeline():
    """Verify ScopeGuard checking scopes on the flow context identity."""
    flow_ctx = FlowContext()
    flow_ctx.identity = Identity(
        id="usr_123",
        type=IdentityType.USER,
        attributes={"scopes": ["read:users"]},
        status=IdentityStatus.ACTIVE,
    )  # type: ignore[attr-defined]

    # Required scope "write:users" is missing -> must fail
    pipe = FlowPipeline("test_pipe")
    pipe.guard(ScopeGuard("write:users"))
    result = await pipe.execute(flow_ctx)
    assert result.status == FlowStatus.GUARDED
    from aquilia.auth.faults import AUTHZ_INSUFFICIENT_SCOPE

    assert isinstance(result.error, AUTHZ_INSUFFICIENT_SCOPE)

    # Required scope "read:users" matches -> must pass
    pipe_ok = FlowPipeline("test_pipe_ok")
    pipe_ok.guard(ScopeGuard("read:users"))
    result_ok = await pipe_ok.execute(flow_ctx)
    assert result_ok.status == FlowStatus.SUCCESS


@pytest.mark.asyncio
async def test_composable_requires_decorator():
    """Verify @requires decorator with both class references and instances."""
    identity_admin = Identity(
        id="usr_admin",
        type=IdentityType.USER,
        attributes={"roles": ["admin"]},
        status=IdentityStatus.ACTIVE,
    )

    @requires(AuthGuard, RoleGuard("admin"))
    async def handler_admin(ctx: Any) -> str:
        return "success"

    # Test 1: Anonymous -> raises AUTH_REQUIRED
    ctx_anon = FakeCtx(None)
    from aquilia.auth.faults import AUTH_REQUIRED, AUTHZ_INSUFFICIENT_ROLE

    with pytest.raises(AUTH_REQUIRED):
        await handler_admin(ctx_anon)

    # Test 2: User without admin role -> raises AUTHZ_INSUFFICIENT_ROLE
    identity_user = Identity(
        id="usr_user",
        type=IdentityType.USER,
        attributes={"roles": ["user"]},
        status=IdentityStatus.ACTIVE,
    )
    ctx_user = FakeCtx(identity_user)
    with pytest.raises(AUTHZ_INSUFFICIENT_ROLE):
        await handler_admin(ctx_user)

    # Test 3: User with admin role -> passes
    ctx_admin = FakeCtx(identity_admin)
    res = await handler_admin(ctx_admin)
    assert res == "success"


@pytest.mark.asyncio
async def test_ctx_first_decorators():
    """Verify flat decorators_new replacement."""
    identity = Identity(
        id="usr_123",
        type=IdentityType.USER,
        attributes={"roles": ["admin"], "scopes": ["write"]},
        status=IdentityStatus.ACTIVE,
    )

    @authenticated
    async def get_profile(ctx: Any) -> str:
        return "profile"

    @roles_required("admin")
    async def get_admin(ctx: Any) -> str:
        return "admin"

    @scopes_required("write")
    async def do_write(ctx: Any) -> str:
        return "write"

    @optional_auth
    async def get_optional(ctx: Any) -> str:
        return "optional"

    ctx_auth = FakeCtx(identity)
    ctx_anon = FakeCtx(None)

    # test @authenticated
    assert await get_profile(ctx_auth) == "profile"
    from aquilia.auth.faults import AUTH_REQUIRED

    with pytest.raises(AUTH_REQUIRED):
        await get_profile(ctx_anon)

    # test @roles_required
    assert await get_admin(ctx_auth) == "admin"
    with pytest.raises(AUTH_REQUIRED):
        await get_admin(ctx_anon)

    # test @scopes_required
    assert await do_write(ctx_auth) == "write"
    with pytest.raises(AUTH_REQUIRED):
        await do_write(ctx_anon)

    # test @optional_auth
    assert await get_optional(ctx_auth) == "optional"
    assert await get_optional(ctx_anon) == "optional"
