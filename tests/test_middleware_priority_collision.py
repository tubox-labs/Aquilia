"""Regression tests for middleware priority collisions (#65).

Two middlewares registered at the same scope and priority resolve by insertion
order — a Python stable-sort implementation detail, not a contract. Collisions
were silently accepted, so a refactor that reordered registration calls could
reorder security middleware with nothing to catch it.
"""

import logging

import pytest

from aquilia.faults.domains import ConfigInvalidFault
from aquilia.middleware import Middleware
from aquilia.middleware.stack import MiddlewareStack


class _Noop(Middleware):
    async def __call__(self, request, ctx, next_handler):
        return await next_handler(request, ctx)


def test_collision_at_same_scope_and_priority_warns(caplog):
    stack = MiddlewareStack()
    stack.add(_Noop(), scope="global", priority=11, name="first")

    with caplog.at_level(logging.WARNING, logger="aquilia.middleware"):
        stack.add(_Noop(), scope="global", priority=11, name="second")

    assert "priority collision" in caplog.text
    # Both participants named, so the warning is actionable.
    assert "first" in caplog.text
    assert "second" in caplog.text

    # Warning only — the middleware is still registered.
    assert len(stack.middlewares) == 2


def test_strict_mode_raises_structured_fault():
    stack = MiddlewareStack(strict_priorities=True)
    stack.add(_Noop(), scope="global", priority=11, name="first")

    with pytest.raises(ConfigInvalidFault) as exc:
        stack.add(_Noop(), scope="global", priority=11, name="second")

    assert exc.value.code == "CONFIG_INVALID"


def test_distinct_priorities_do_not_warn(caplog):
    stack = MiddlewareStack()

    with caplog.at_level(logging.WARNING, logger="aquilia.middleware"):
        stack.add(_Noop(), scope="global", priority=11, name="cors")
        stack.add(_Noop(), scope="global", priority=12, name="rate_limit")

    assert "priority collision" not in caplog.text


def test_same_priority_in_different_scopes_is_fine(caplog):
    """Scope rank dominates priority, so these can never be ambiguous."""
    stack = MiddlewareStack()

    with caplog.at_level(logging.WARNING, logger="aquilia.middleware"):
        stack.add(_Noop(), scope="global", priority=11, name="global_mw")
        stack.add(_Noop(), scope="app", priority=11, name="app_mw")
        stack.add(_Noop(), scope="route", priority=11, name="route_mw")

    assert "priority collision" not in caplog.text


def test_framework_default_chain_has_no_collisions(caplog):
    """A stock app must not trip the new warning.

    CORS/inspector both used 11 and rate-limit/toolbar both used 12, so this
    would have failed before the priorities were separated.
    """
    from aquilia.config import ConfigLoader
    from aquilia.manifest import AppManifest
    from aquilia.server import AquiliaServer
    from aquilia.workspace import Workspace

    manifest = AppManifest(name="collision_probe", version="0.0.1")
    ws = Workspace("collision-ws").inspector(enabled=True)
    # CORS (11) and rate limiting (12) are what the inspector pair used to clash
    # with, so both must be on for this test to exercise the real collision.
    ws.security(cors_enabled=True, rate_limiting=True)

    config_loader = ConfigLoader()
    config_loader.config_data = ws.to_dict()
    config_loader._build_apps_namespace()

    with caplog.at_level(logging.WARNING, logger="aquilia.middleware"):
        server = AquiliaServer(manifests=[manifest], config=config_loader)

    assert "priority collision" not in caplog.text

    seen: dict[tuple[str, int], str] = {}
    for desc in server.middleware_stack.middlewares:
        key = (desc.scope, desc.priority)
        assert key not in seen, f"{desc.name} collides with {seen[key]} at {key}"
        seen[key] = desc.name


def test_ordering_is_still_ascending_by_priority():
    """Guard the invariant the whole priority scheme rests on."""
    stack = MiddlewareStack()
    stack.add(_Noop(), scope="global", priority=20, name="late")
    stack.add(_Noop(), scope="global", priority=5, name="early")
    stack.add(_Noop(), scope="app", priority=1, name="app_scope")

    stack._sort_middlewares()
    assert [d.name for d in stack.middlewares] == ["early", "late", "app_scope"]
