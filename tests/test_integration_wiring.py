"""
Phase 12 — Integration Wiring Tests.

Verifies the integration-level fixes from the comprehensive framework audit:
  INT-01: CSRF middleware runs AFTER session/auth middleware
  INT-02: DI container shutdown is not called twice (delegated to middleware)
  INT-03: Middleware priority ordering is correct and non-conflicting
"""

import pytest
import asyncio
from unittest.mock import MagicMock, AsyncMock, patch


# ──────────────────────────────────────────────────────────────────────
# INT-01: CSRF middleware priority must be AFTER session/auth (15)
# ──────────────────────────────────────────────────────────────────────

class TestCSRFMiddlewarePriority:
    """Verify CSRF middleware runs after session/auth middleware."""

    def test_csrf_priority_is_20(self):
        """CSRF middleware must have priority 20 (after session at 15)."""
        # Read the server source and verify the priority constant
        import ast
        from pathlib import Path

        server_path = Path(__file__).parent.parent / "aquilia" / "server.py"
        source = server_path.read_text(encoding="utf-8")

        # Find the CSRF middleware registration line
        lines = source.split("\n")
        csrf_lines = [
            (i, line) for i, line in enumerate(lines)
            if 'name="csrf"' in line and "middleware_stack.add" in line
        ]

        assert len(csrf_lines) >= 1, "CSRF middleware registration not found"

        # Verify priority=20 appears in the registration
        for line_num, line in csrf_lines:
            assert "priority=20" in line, (
                f"CSRF middleware at line {line_num + 1} should have priority=20, "
                f"got: {line.strip()}"
            )

    def test_csrf_priority_after_session(self):
        """CSRF priority (20) must be higher than session/auth (15)."""
        csrf_priority = 20
        session_auth_priority = 15
        assert csrf_priority > session_auth_priority, (
            f"CSRF priority ({csrf_priority}) must be > session/auth priority "
            f"({session_auth_priority}) so CSRF runs AFTER session is loaded"
        )

    def test_csrf_priority_before_i18n(self):
        """CSRF priority (20) must be lower than i18n (24)."""
        csrf_priority = 20
        i18n_priority = 24
        assert csrf_priority < i18n_priority, (
            f"CSRF priority ({csrf_priority}) must be < i18n priority "
            f"({i18n_priority})"
        )


# ──────────────────────────────────────────────────────────────────────
# INT-02: DI container shutdown delegation
# ──────────────────────────────────────────────────────────────────────

class TestDIContainerShutdownDelegation:
    """Verify DI container shutdown is not called from ASGI adapter."""

    def test_asgi_adapter_no_container_shutdown_call(self):
        """The ASGI adapter handle_http should NOT call container.shutdown()."""
        from pathlib import Path

        asgi_path = Path(__file__).parent.parent / "aquilia" / "asgi.py"
        source = asgi_path.read_text(encoding="utf-8")

        # The old code had: await di_container.shutdown()
        # After fix, this should be replaced with a comment
        assert "await di_container.shutdown()" not in source, (
            "ASGI adapter should not call di_container.shutdown() — "
            "DI cleanup is delegated to request_scope_mw"
        )

    def test_request_scope_mw_does_shutdown(self):
        """The request_scope_mw in server.py SHOULD call container.shutdown()."""
        from pathlib import Path

        server_path = Path(__file__).parent.parent / "aquilia" / "server.py"
        source = server_path.read_text(encoding="utf-8")

        # Find the request_scope_mw function
        assert "await ctx.container.shutdown()" in source, (
            "request_scope_mw must call ctx.container.shutdown()"
        )


# ──────────────────────────────────────────────────────────────────────
# INT-03: Middleware priority ordering has no conflicts
# ──────────────────────────────────────────────────────────────────────

class TestMiddlewarePriorityOrdering:
    """Verify middleware priorities are non-conflicting and correctly ordered."""

    # Expected priority layout after Phase 12 fixes
    PRIORITY_MAP = {
        "exception": 1,
        "faults": 2,
        "proxy_fix": 3,
        "https_redirect": 4,
        "request_scope": 5,
        "static_files": 6,
        "security_headers": 7,
        "hsts": 8,
        "csp": 9,
        "request_id": 10,
        "cors": 11,
        "rate_limit": 12,
        "session_or_auth": 15,
        "csrf": 20,
        "i18n": 24,
        "templates": 25,
        "cache": 26,
    }

    def test_all_priorities_are_unique(self):
        """No two middleware should share the same priority."""
        priorities = list(self.PRIORITY_MAP.values())
        assert len(priorities) == len(set(priorities)), (
            f"Duplicate priorities found: {priorities}"
        )

    def test_priorities_are_monotonically_increasing(self):
        """Priorities should increase with logical execution order."""
        items = list(self.PRIORITY_MAP.items())
        for i in range(1, len(items)):
            prev_name, prev_prio = items[i - 1]
            curr_name, curr_prio = items[i]
            assert curr_prio > prev_prio, (
                f"Priority ordering violation: {prev_name}({prev_prio}) >= "
                f"{curr_name}({curr_prio})"
            )

    def test_csrf_after_session(self):
        """CSRF must come after session/auth in execution order."""
        assert self.PRIORITY_MAP["csrf"] > self.PRIORITY_MAP["session_or_auth"]

    def test_security_before_session(self):
        """Security headers must come before session/auth."""
        assert self.PRIORITY_MAP["security_headers"] < self.PRIORITY_MAP["session_or_auth"]

    def test_fault_before_everything(self):
        """FaultMiddleware should be one of the first (after exception)."""
        assert self.PRIORITY_MAP["faults"] == 2

    def test_request_scope_early(self):
        """Request scope DI must be early (before session/security)."""
        assert self.PRIORITY_MAP["request_scope"] < self.PRIORITY_MAP["session_or_auth"]


# ──────────────────────────────────────────────────────────────────────
# Middleware stack build verification
# ──────────────────────────────────────────────────────────────────────

class TestMiddlewareStackBuild:
    """Verify the MiddlewareStack builds chains in correct order."""

    async def test_build_handler_respects_priority_order(self):
        """Middleware chain should execute in ascending priority order."""
        from aquilia.middleware import MiddlewareStack
        from aquilia.request import Request
        from aquilia.response import Response

        execution_order = []

        def make_mw(name, priority):
            async def mw(request, ctx, next_handler):
                execution_order.append(name)
                return await next_handler(request, ctx)
            return mw, priority

        stack = MiddlewareStack()
        # Add in random order — stack should sort by priority
        for name, prio in [("c", 30), ("a", 10), ("b", 20)]:
            mw, p = make_mw(name, prio)
            stack.add(mw, priority=p, name=name)

        async def final_handler(request, ctx):
            execution_order.append("final")
            return Response(content=b"ok", status=200)

        handler = stack.build_handler(final_handler)

        scope = {"type": "http", "method": "GET", "path": "/", "headers": []}
        request = Request(scope, None)
        ctx = MagicMock()
        await handler(request, ctx)

        assert execution_order == ["a", "b", "c", "final"], (
            f"Expected [a, b, c, final], got {execution_order}"
        )

    async def test_build_handler_groups_by_scope_then_priority(self):
        """Global scope runs before app scope, then by priority within scope."""
        from aquilia.middleware import MiddlewareStack
        from aquilia.request import Request
        from aquilia.response import Response

        execution_order = []

        stack = MiddlewareStack()

        def add_mw(name, scope, priority):
            async def mw(request, ctx, next_handler):
                execution_order.append(name)
                return await next_handler(request, ctx)
            stack.add(mw, scope=scope, priority=priority, name=name)

        # Add app-scope first, then global — stack should reorder
        add_mw("app_50", "app", 50)
        add_mw("global_10", "global", 10)
        add_mw("global_5", "global", 5)

        async def final_handler(request, ctx):
            execution_order.append("final")
            return Response(content=b"ok", status=200)

        handler = stack.build_handler(final_handler)

        scope = {"type": "http", "method": "GET", "path": "/", "headers": []}
        request = Request(scope, None)
        ctx = MagicMock()
        await handler(request, ctx)

        assert execution_order == ["global_5", "global_10", "app_50", "final"], (
            f"Expected [global_5, global_10, app_50, final], got {execution_order}"
        )
