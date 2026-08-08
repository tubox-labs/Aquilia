"""WebSocket middleware subsystem: stack, lifecycle, builtins, and runtime wiring.

The subsystem replaces three parallel mechanisms that all existed and none of
which ever executed: the old flat ``sockets/middleware.py`` chain (no call
sites), ``SocketGuard.check_message`` (no call sites), and the ``@Socket``
limit kwargs (stored, never read). Several tests below assert those are now
actually wired, because "declared but never invoked" is precisely the failure
mode this replaces.
"""

from __future__ import annotations

import asyncio
import json
import time

import pytest

from aquilia.faults import Fault
from aquilia.faults.domains import ConfigInvalidFault
from aquilia.sockets.controller import SocketController
from aquilia.sockets.decorators import Event, OnConnect, Socket
from aquilia.sockets.envelope import MessageEnvelope, MessageType
from aquilia.sockets.middleware import (
    MessageValidationMiddleware,
    SocketAuthMiddleware,
    SocketCtx,
    SocketFaultMiddleware,
    SocketLoggingMiddleware,
    SocketMetricsMiddleware,
    SocketMiddleware,
    SocketMiddlewareChain,
    SocketMiddlewareStack,
    SocketPermissionMiddleware,
    SocketRateLimitMiddleware,
)
from aquilia.sockets.runtime import AquilaSockets, RouteMetadata, SocketRouter


# ── Fixtures / helpers ───────────────────────────────────────────────────────


class FakeConnection:
    """Minimal Connection stand-in: only what SocketCtx and the builtins touch."""

    def __init__(self, connection_id="conn-1", namespace="/chat", identity=None, session=None):
        self.connection_id = connection_id
        self.namespace = namespace
        self.identity = identity
        self.session = session
        self.container = None
        self.scope = None
        self.state = {}
        self.messages_sent = 0
        self.messages_received = 0
        self._connected = True
        self.sent = []
        self.acks = []

    @property
    def is_connected(self):
        return self._connected

    async def send_event(self, event, payload, ack=False):
        self.sent.append((event, payload))
        self.messages_sent += 1

    async def send_json(self, data):
        self.sent.append(("__json__", data))
        self.messages_sent += 1

    async def send_ack(self, message_id, status="ok", data=None, error=None):
        self.acks.append({"id": message_id, "status": status, "data": data, "error": error})

    async def resolve(self, name, optional=False):
        return f"resolved:{name}"


class FakeIdentity:
    def __init__(self, id="u1", roles=(), scopes=(), active=True, type_value="user"):
        self.id = id
        self._roles = set(roles)
        self._scopes = set(scopes)
        self._active = active
        self.type = type("T", (), {"value": type_value})()

    def has_role(self, role):
        return role in self._roles

    def has_scope(self, scope):
        return scope in self._scopes or "*" in self._scopes

    def is_active(self):
        return self._active


def envelope(event="message.send", payload=None, msg_id=None, ack=False):
    return MessageEnvelope(
        type=MessageType.EVENT,
        event=event,
        payload=payload if payload is not None else {},
        id=msg_id,
        ack=ack,
    )


def ctx_for(conn=None, **kwargs):
    return SocketCtx(conn or FakeConnection(**kwargs))


class Recorder(SocketMiddleware):
    """Records entry/exit across all three hooks."""

    def __init__(self, tag, log):
        self.tag = tag
        self.log = log

    async def on_connect(self, ctx, next_handler):
        self.log.append(f"{self.tag}:connect>")
        await next_handler(ctx)
        self.log.append(f"{self.tag}:connect<")

    async def on_message(self, envelope, ctx, next_handler):
        self.log.append(f"{self.tag}:msg>")
        result = await next_handler(envelope, ctx)
        self.log.append(f"{self.tag}:msg<")
        return result

    async def on_disconnect(self, ctx, reason):
        self.log.append(f"{self.tag}:disconnect")


async def noop_connect(ctx):
    return None


async def noop_message(envelope, ctx):
    return None


# ── Stack: registration and validation ───────────────────────────────────────


class TestRegistration:
    def test_rejects_non_socket_middleware(self):
        stack = SocketMiddlewareStack()

        class NotMiddleware:
            pass

        with pytest.raises(ConfigInvalidFault, match="must inherit from"):
            stack.add(NotMiddleware())

    def test_legacy_three_arg_callable_gets_a_migration_message(self):
        """The pre-package interface was (conn, envelope, next) and never ran."""
        stack = SocketMiddlewareStack()

        class LegacyMiddleware:
            async def __call__(self, conn, envelope, next):
                return await next(conn, envelope)

        with pytest.raises(ConfigInvalidFault) as excinfo:
            stack.add(LegacyMiddleware())

        message = str(excinfo.value)
        assert "pre-1.5" in message
        assert "on_message" in message

    def test_rejects_non_async_hook(self):
        stack = SocketMiddlewareStack()

        class Sync(SocketMiddleware):
            def on_message(self, envelope, ctx, next_handler):  # not async
                return None

        with pytest.raises(ConfigInvalidFault, match="coroutine function"):
            stack.add(Sync())

    def test_rejects_wrong_arity(self):
        stack = SocketMiddlewareStack()

        class WrongArity(SocketMiddleware):
            async def on_message(self, envelope):  # missing ctx + next_handler
                return None

        with pytest.raises(ConfigInvalidFault, match="invalid signature"):
            stack.add(WrongArity())

    def test_middleware_overriding_nothing_warns(self, caplog):
        stack = SocketMiddlewareStack()

        class Empty(SocketMiddleware):
            pass

        stack.add(Empty())
        assert "overrides none of" in caplog.text

    def test_hook_detection_populates_only_relevant_chains(self):
        stack = SocketMiddlewareStack()

        class MessageOnly(SocketMiddleware):
            async def on_message(self, envelope, ctx, next_handler):
                return await next_handler(envelope, ctx)

        stack.add(MessageOnly())
        stack._ensure_sorted()

        assert len(stack._message) == 1
        # An on_message-only middleware must not add a frame to connect.
        assert stack._connect == []
        assert stack._disconnect == []

    def test_describe_reports_hooks(self):
        stack = SocketMiddlewareStack()
        stack.add(Recorder("a", []), priority=10)

        described = stack.describe()
        assert described[0]["name"] == "Recorder"
        assert set(described[0]["hooks"]) == {"on_connect", "on_message", "on_disconnect"}


# ── Stack: ordering ──────────────────────────────────────────────────────────


class TestOrdering:
    async def test_ascending_priority_is_outermost(self):
        """Same contract as HTTP: lower priority wraps higher."""
        log = []
        stack = SocketMiddlewareStack()
        stack.add(Recorder("outer", log), priority=1)
        stack.add(Recorder("inner", log), priority=99)

        await stack.build_message_handler(noop_message)(envelope(), ctx_for())

        assert log == ["outer:msg>", "inner:msg>", "inner:msg<", "outer:msg<"]

    async def test_scope_outranks_priority(self):
        """A global middleware runs before a namespace one even at worse priority."""
        log = []
        stack = SocketMiddlewareStack()
        stack.add(Recorder("ns", log), scope="namespace:/chat", priority=1)
        stack.add(Recorder("global", log), scope="global", priority=99)

        await stack.build_message_handler(noop_message)(envelope(), ctx_for())

        assert log.index("global:msg>") < log.index("ns:msg>")

    def test_collision_warns(self, caplog):
        stack = SocketMiddlewareStack()
        stack.add(Recorder("a", []), priority=10, name="a")
        stack.add(Recorder("b", []), priority=10, name="b")

        assert "priority collision" in caplog.text

    def test_collision_is_fatal_under_strict(self):
        stack = SocketMiddlewareStack(strict_priorities=True)
        stack.add(Recorder("a", []), priority=10, name="a")

        with pytest.raises(ConfigInvalidFault, match="priority collision"):
            stack.add(Recorder("b", []), priority=10, name="b")

    def test_same_priority_different_scope_does_not_collide(self, caplog):
        stack = SocketMiddlewareStack()
        stack.add(Recorder("a", []), scope="global", priority=10, name="a")
        stack.add(Recorder("b", []), scope="namespace:/chat", priority=10, name="b")

        assert "priority collision" not in caplog.text

    def test_scoped_filters_other_namespaces(self):
        stack = SocketMiddlewareStack()
        stack.add(Recorder("global", []), scope="global", priority=1)
        stack.add(Recorder("chat", []), scope="namespace:/chat", priority=2)
        stack.add(Recorder("feed", []), scope="namespace:/feed", priority=3)

        names = {d.name for d in stack.scoped("/chat").middlewares}
        assert names == {"Recorder"}
        assert len(stack.scoped("/chat").middlewares) == 2  # global + chat

    async def test_event_scoped_middleware_only_runs_for_its_event(self):
        log = []
        stack = SocketMiddlewareStack()
        stack.add(Recorder("scoped", log), scope="event:message.send", priority=10)

        handler = stack.build_message_handler(noop_message)

        await handler(envelope(event="other.event"), ctx_for())
        assert log == []

        await handler(envelope(event="message.send"), ctx_for())
        assert log == ["scoped:msg>", "scoped:msg<"]


# ── Stack: execution semantics ───────────────────────────────────────────────


class TestExecution:
    async def test_short_circuit_skips_the_handler(self):
        reached = []

        class Blocker(SocketMiddleware):
            async def on_message(self, envelope, ctx, next_handler):
                return {"blocked": True}  # never awaits next_handler

        async def final(envelope, ctx):
            reached.append(envelope.event)
            return None

        stack = SocketMiddlewareStack()
        stack.add(Blocker())

        result = await stack.build_message_handler(final)(envelope(), ctx_for())

        assert result == {"blocked": True}
        assert reached == []

    async def test_none_is_a_valid_result(self):
        """Unlike HTTP, a socket handler may legitimately reply with nothing."""
        stack = SocketMiddlewareStack()
        stack.add(Recorder("a", []))

        assert await stack.build_message_handler(noop_message)(envelope(), ctx_for()) is None

    async def test_non_dict_result_is_rejected(self):
        class BadReturn(SocketMiddleware):
            async def on_message(self, envelope, ctx, next_handler):
                await next_handler(envelope, ctx)
                return "a string is not an ack payload"

        stack = SocketMiddlewareStack()
        stack.add(BadReturn())

        with pytest.raises(ConfigInvalidFault, match="expected a dict"):
            await stack.build_message_handler(noop_message)(envelope(), ctx_for())

    async def test_connect_chain_wraps_final_handler(self):
        log = []
        stack = SocketMiddlewareStack()
        stack.add(Recorder("a", log), priority=1)

        async def final(ctx):
            log.append("final")

        await stack.build_connect_handler(final)(ctx_for())

        assert log == ["a:connect>", "final", "a:connect<"]

    async def test_connect_fault_propagates(self):
        class Rejector(SocketMiddleware):
            async def on_connect(self, ctx, next_handler):
                from aquilia.sockets.faults import WS_FORBIDDEN

                raise WS_FORBIDDEN("nope")

        stack = SocketMiddlewareStack()
        stack.add(Rejector())

        with pytest.raises(Fault) as excinfo:
            await stack.build_connect_handler(noop_connect)(ctx_for())
        assert excinfo.value.code == "WS_FORBIDDEN"

    async def test_disconnect_runs_in_reverse_order(self):
        log = []
        stack = SocketMiddlewareStack()
        stack.add(Recorder("first", log), priority=1)
        stack.add(Recorder("second", log), priority=2)

        await stack.run_disconnect(ctx_for(), "bye")

        assert log == ["second:disconnect", "first:disconnect"]

    async def test_one_failing_disconnect_hook_does_not_strand_the_rest(self):
        log = []

        class Exploder(SocketMiddleware):
            async def on_disconnect(self, ctx, reason):
                raise RuntimeError("metrics backend down")

        stack = SocketMiddlewareStack()
        stack.add(Recorder("survivor", log), priority=1)
        stack.add(Exploder(), priority=2)

        await stack.run_disconnect(ctx_for(), "bye")

        assert log == ["survivor:disconnect"]


# ── SocketCtx ────────────────────────────────────────────────────────────────


class TestSocketCtx:
    def test_state_is_the_connection_state_not_a_copy(self):
        """One bag, two accessors — otherwise middleware and handlers desync."""
        conn = FakeConnection()
        ctx = SocketCtx(conn)

        ctx.state["k"] = "v"
        assert conn.state["k"] == "v"
        assert ctx.state is conn.state

    def test_identity_reads_through_to_the_connection(self):
        """A property, not a snapshot: re-auth mid-connection must be visible."""
        conn = FakeConnection()
        ctx = SocketCtx(conn)
        assert ctx.identity is None

        conn.identity = FakeIdentity()
        assert ctx.identity is conn.identity

    def test_client_key_prefers_identity(self):
        conn = FakeConnection(connection_id="c1")
        ctx = SocketCtx(conn)
        assert ctx.client_key() == "conn:c1"

        conn.identity = FakeIdentity(id="u7")
        assert ctx.client_key() == "user:u7"

    def test_message_framing_tracks_event_and_elapsed(self):
        ctx = ctx_for()
        assert ctx.event is None

        ctx.begin_message("ping")
        assert ctx.event == "ping"
        assert ctx.message_elapsed_ms >= 0.0

        ctx.end_message()
        assert ctx.event is None
        assert ctx.message_elapsed_ms == 0.0

    async def test_resolve_delegates_to_the_container(self):
        assert await ctx_for().resolve("presence") == "resolved:presence"


# ── Builtin: faults ──────────────────────────────────────────────────────────


class TestFaultMiddleware:
    async def test_fault_becomes_an_error_ack(self):
        from aquilia.sockets.faults import WS_FORBIDDEN

        conn = FakeConnection()
        stack = SocketMiddlewareStack()
        stack.add(SocketFaultMiddleware(), priority=2)

        async def final(envelope, ctx):
            raise WS_FORBIDDEN("denied")

        result = await stack.build_message_handler(final)(envelope(msg_id="m1"), SocketCtx(conn))

        assert result is None
        assert conn.acks[0]["status"] == "error"
        assert "denied" in conn.acks[0]["error"]

    async def test_unexpected_exception_is_not_leaked_to_the_client(self):
        conn = FakeConnection()
        stack = SocketMiddlewareStack()
        stack.add(SocketFaultMiddleware(debug=False), priority=2)

        async def final(envelope, ctx):
            raise RuntimeError("postgres://user:hunter2@db:5432 unreachable")

        await stack.build_message_handler(final)(envelope(msg_id="m1"), SocketCtx(conn))

        assert conn.acks[0]["error"] == "Internal server error"
        assert "hunter2" not in json.dumps(conn.acks)

    async def test_debug_mode_includes_the_detail(self):
        conn = FakeConnection()
        stack = SocketMiddlewareStack()
        stack.add(SocketFaultMiddleware(debug=True), priority=2)

        async def final(envelope, ctx):
            raise RuntimeError("boom")

        await stack.build_message_handler(final)(envelope(msg_id="m1"), SocketCtx(conn))

        assert "boom" in conn.acks[0]["error"]

    async def test_error_event_when_the_message_carried_no_id(self):
        conn = FakeConnection()
        stack = SocketMiddlewareStack()
        stack.add(SocketFaultMiddleware(), priority=2)

        async def final(envelope, ctx):
            raise RuntimeError("boom")

        await stack.build_message_handler(final)(envelope(), SocketCtx(conn))

        assert conn.acks == []
        assert conn.sent[0][0] == "error"

    async def test_one_bad_message_does_not_kill_the_connection(self):
        conn = FakeConnection()
        stack = SocketMiddlewareStack()
        stack.add(SocketFaultMiddleware(), priority=2)
        calls = []

        async def final(envelope, ctx):
            calls.append(envelope.event)
            if envelope.event == "bad":
                raise RuntimeError("boom")
            return None

        handler = stack.build_message_handler(final)
        await handler(envelope(event="bad"), SocketCtx(conn))
        await handler(envelope(event="good"), SocketCtx(conn))

        assert calls == ["bad", "good"]


# ── Builtin: validation ──────────────────────────────────────────────────────


class TestValidation:
    async def test_oversized_payload_is_rejected(self):
        stack = SocketMiddlewareStack()
        stack.add(MessageValidationMiddleware(max_payload_size=50))

        big = envelope(payload={"text": "x" * 200})

        with pytest.raises(Fault) as excinfo:
            await stack.build_message_handler(noop_message)(big, ctx_for())
        assert excinfo.value.code == "WS_PAYLOAD_TOO_LARGE"

    async def test_missing_event_is_rejected(self):
        stack = SocketMiddlewareStack()
        stack.add(MessageValidationMiddleware())

        with pytest.raises(Fault) as excinfo:
            await stack.build_message_handler(noop_message)(envelope(event=""), ctx_for())
        assert excinfo.value.code == "WS_MESSAGE_INVALID"

    async def test_event_whitelist(self):
        stack = SocketMiddlewareStack()
        stack.add(MessageValidationMiddleware(allowed_events=["ping"]))
        handler = stack.build_message_handler(noop_message)

        await handler(envelope(event="ping"), ctx_for())

        with pytest.raises(Fault) as excinfo:
            await handler(envelope(event="admin.wipe"), ctx_for())
        assert excinfo.value.code == "WS_UNSUPPORTED_EVENT"

    async def test_unserialisable_payload_is_invalid_not_size_zero(self):
        stack = SocketMiddlewareStack()
        stack.add(MessageValidationMiddleware())

        bad = envelope(payload={"obj": object()})

        with pytest.raises(Fault) as excinfo:
            await stack.build_message_handler(noop_message)(bad, ctx_for())
        assert excinfo.value.code == "WS_MESSAGE_INVALID"


# ── Builtin: rate limiting ───────────────────────────────────────────────────


class TestRateLimit:
    async def test_burst_then_reject(self):
        stack = SocketMiddlewareStack()
        stack.add(SocketRateLimitMiddleware(messages_per_second=1, burst=3))
        handler = stack.build_message_handler(noop_message)
        ctx = ctx_for()

        for _ in range(3):
            await handler(envelope(), ctx)

        with pytest.raises(Fault) as excinfo:
            await handler(envelope(), ctx)
        assert excinfo.value.code == "WS_RATE_LIMIT_EXCEEDED"

    async def test_refills_over_elapsed_time(self):
        mw = SocketRateLimitMiddleware(messages_per_second=2, burst=1)
        stack = SocketMiddlewareStack()
        stack.add(mw)
        handler = stack.build_message_handler(noop_message)
        ctx = ctx_for()

        await handler(envelope(), ctx)

        bucket = mw._buckets.get_or_create(ctx.client_key(), mw._factory)
        assert bucket.consume()[0] is False

        # Rewind: at 2 tokens/sec one second is a full refill.
        bucket.last_refill -= 1.0
        await handler(envelope(), ctx)

    async def test_connections_are_limited_independently(self):
        stack = SocketMiddlewareStack()
        stack.add(SocketRateLimitMiddleware(messages_per_second=1, burst=1))
        handler = stack.build_message_handler(noop_message)

        await handler(envelope(), ctx_for(connection_id="a"))
        await handler(envelope(), ctx_for(connection_id="b"))

    async def test_identity_shares_one_bucket_across_connections(self):
        """An authenticated user cannot multiply their limit by reconnecting."""
        stack = SocketMiddlewareStack()
        stack.add(SocketRateLimitMiddleware(messages_per_second=1, burst=1, key_by="client"))
        handler = stack.build_message_handler(noop_message)

        identity = FakeIdentity(id="u1")
        await handler(envelope(), ctx_for(connection_id="a", identity=identity))

        with pytest.raises(Fault):
            await handler(envelope(), ctx_for(connection_id="b", identity=identity))

    async def test_identity_keying_skips_anonymous(self):
        stack = SocketMiddlewareStack()
        stack.add(SocketRateLimitMiddleware(messages_per_second=1, burst=1, key_by="identity"))
        handler = stack.build_message_handler(noop_message)
        ctx = ctx_for()

        for _ in range(5):
            await handler(envelope(), ctx)

    async def test_exempt_events_bypass(self):
        stack = SocketMiddlewareStack()
        stack.add(SocketRateLimitMiddleware(messages_per_second=1, burst=1, exempt_events=["ping"]))
        handler = stack.build_message_handler(noop_message)
        ctx = ctx_for()

        for _ in range(5):
            await handler(envelope(event="ping"), ctx)

    async def test_disconnect_releases_the_bucket(self):
        """The pre-package limiter kept per-connection dicts forever."""
        mw = SocketRateLimitMiddleware(messages_per_second=1, burst=1, key_by="connection")
        stack = SocketMiddlewareStack()
        stack.add(mw)
        ctx = ctx_for(connection_id="doomed")

        await stack.build_message_handler(noop_message)(envelope(), ctx)
        assert "conn:doomed" in mw._buckets._buckets

        await stack.run_disconnect(ctx, "client disconnect")
        assert "conn:doomed" not in mw._buckets._buckets

    def test_invalid_key_by_fails_at_construction(self):
        with pytest.raises(ConfigInvalidFault):
            SocketRateLimitMiddleware(key_by="nonsense")

    def test_shares_the_http_token_bucket(self):
        from aquilia.middleware_ext.rate_limit import _BucketStore, _TokenBucket

        mw = SocketRateLimitMiddleware()
        assert isinstance(mw._buckets, _BucketStore)
        assert isinstance(mw._factory(), _TokenBucket)


# ── Builtin: auth and permissions ────────────────────────────────────────────


class TestAuth:
    async def test_anonymous_handshake_rejected(self):
        stack = SocketMiddlewareStack()
        stack.add(SocketAuthMiddleware(require_identity=True))

        with pytest.raises(Fault) as excinfo:
            await stack.build_connect_handler(noop_connect)(ctx_for())
        assert excinfo.value.code == "WS_AUTH_REQUIRED"

    async def test_authenticated_handshake_passes(self):
        stack = SocketMiddlewareStack()
        stack.add(SocketAuthMiddleware(require_identity=True))

        await stack.build_connect_handler(noop_connect)(ctx_for(identity=FakeIdentity()))

    async def test_inactive_identity_rejected(self):
        stack = SocketMiddlewareStack()
        stack.add(SocketAuthMiddleware())

        with pytest.raises(Fault) as excinfo:
            await stack.build_connect_handler(noop_connect)(ctx_for(identity=FakeIdentity(active=False)))
        assert excinfo.value.code == "WS_FORBIDDEN"

    async def test_identity_type_whitelist(self):
        stack = SocketMiddlewareStack()
        stack.add(SocketAuthMiddleware(allowed_identity_types=["staff"]))

        with pytest.raises(Fault):
            await stack.build_connect_handler(noop_connect)(ctx_for(identity=FakeIdentity(type_value="user")))

    async def test_revoked_identity_is_caught_on_recheck(self):
        """A long-lived socket must not outlive its authorization."""
        identity = FakeIdentity()
        conn = FakeConnection(identity=identity)
        ctx = SocketCtx(conn)

        stack = SocketMiddlewareStack()
        stack.add(SocketAuthMiddleware(recheck_interval=300))

        await stack.build_connect_handler(noop_connect)(ctx)
        handler = stack.build_message_handler(noop_message)
        await handler(envelope(), ctx)  # inside the interval: no recheck

        identity._active = False
        ctx.state["_auth_last_check"] = time.monotonic() - 400  # force the interval to elapse

        with pytest.raises(Fault) as excinfo:
            await handler(envelope(), ctx)
        assert excinfo.value.code == "WS_FORBIDDEN"

    async def test_recheck_can_be_disabled(self):
        identity = FakeIdentity()
        ctx = ctx_for(identity=identity)

        stack = SocketMiddlewareStack()
        stack.add(SocketAuthMiddleware(recheck_interval=0))
        await stack.build_connect_handler(noop_connect)(ctx)

        identity._active = False
        await stack.build_message_handler(noop_message)(envelope(), ctx)

    async def test_state_lives_on_the_context_not_the_middleware(self):
        """The guard this replaces leaked a dict entry per connection, forever."""
        mw = SocketAuthMiddleware()
        ctx = ctx_for(identity=FakeIdentity())

        stack = SocketMiddlewareStack()
        stack.add(mw)
        await stack.build_connect_handler(noop_connect)(ctx)

        assert "_auth_last_check" in ctx.state
        assert not any(isinstance(v, dict) and ctx.connection_id in v for v in vars(mw).values())


class TestPermissions:
    async def test_role_requirement_enforced(self):
        stack = SocketMiddlewareStack()
        stack.add(SocketPermissionMiddleware(require_roles={"room.moderate": ["moderator"]}))
        handler = stack.build_message_handler(noop_message)

        with pytest.raises(Fault) as excinfo:
            await handler(envelope(event="room.moderate"), ctx_for(identity=FakeIdentity(roles=["user"])))
        assert excinfo.value.code == "WS_FORBIDDEN"

        await handler(envelope(event="room.moderate"), ctx_for(identity=FakeIdentity(roles=["moderator"])))

    async def test_unlisted_events_allowed_by_default(self):
        stack = SocketMiddlewareStack()
        stack.add(SocketPermissionMiddleware(require_roles={"admin.x": ["admin"]}))

        await stack.build_message_handler(noop_message)(envelope(event="chat.send"), ctx_for())

    async def test_default_deny_blocks_unlisted_events(self):
        stack = SocketMiddlewareStack()
        stack.add(SocketPermissionMiddleware(require_roles={"admin.x": ["admin"]}, default_deny=True))

        with pytest.raises(Fault):
            await stack.build_message_handler(noop_message)(envelope(event="chat.send"), ctx_for())

    async def test_mode_all_requires_every_role(self):
        stack = SocketMiddlewareStack()
        stack.add(SocketPermissionMiddleware(require_roles={"x": ["a", "b"]}, mode="all"))
        handler = stack.build_message_handler(noop_message)

        with pytest.raises(Fault):
            await handler(envelope(event="x"), ctx_for(identity=FakeIdentity(roles=["a"])))

        await handler(envelope(event="x"), ctx_for(identity=FakeIdentity(roles=["a", "b"])))

    async def test_scope_requirement(self):
        stack = SocketMiddlewareStack()
        stack.add(SocketPermissionMiddleware(require_scopes={"m.sub": ["metrics:read"]}))
        handler = stack.build_message_handler(noop_message)

        with pytest.raises(Fault):
            await handler(envelope(event="m.sub"), ctx_for(identity=FakeIdentity()))

        await handler(envelope(event="m.sub"), ctx_for(identity=FakeIdentity(scopes=["metrics:read"])))

    async def test_anonymous_hits_auth_required_not_forbidden(self):
        stack = SocketMiddlewareStack()
        stack.add(SocketPermissionMiddleware(require_roles={"x": ["admin"]}))

        with pytest.raises(Fault) as excinfo:
            await stack.build_message_handler(noop_message)(envelope(event="x"), ctx_for())
        assert excinfo.value.code == "WS_AUTH_REQUIRED"


# ── Builtin: metrics and logging ─────────────────────────────────────────────


class TestMetrics:
    async def test_counts_lifecycle_and_messages(self):
        mw = SocketMetricsMiddleware()
        stack = SocketMiddlewareStack()
        stack.add(mw)
        ctx = ctx_for()

        await stack.build_connect_handler(noop_connect)(ctx)
        await stack.build_message_handler(noop_message)(envelope(event="ping"), ctx)
        await stack.run_disconnect(ctx, "client disconnect")

        snap = mw.snapshot()
        assert snap["connections"] == {"opened": 1, "closed": 1, "active": 0}
        assert snap["messages"]["total"] == 1
        assert snap["messages"]["by_event"] == {"ping": 1}
        assert snap["disconnect_reasons"] == {"client disconnect": 1}

    async def test_rejected_handshake_does_not_leak_an_active_connection(self):
        mw = SocketMetricsMiddleware()
        stack = SocketMiddlewareStack()
        stack.add(mw, priority=6)
        stack.add(SocketAuthMiddleware(), priority=15)

        with pytest.raises(Fault):
            await stack.build_connect_handler(noop_connect)(ctx_for())

        assert mw.snapshot()["connections"]["active"] == 0

    async def test_failed_messages_are_counted_and_timed(self):
        mw = SocketMetricsMiddleware()
        stack = SocketMiddlewareStack()
        stack.add(mw)

        async def final(envelope, ctx):
            raise RuntimeError("boom")

        with pytest.raises(RuntimeError):
            await stack.build_message_handler(final)(envelope(event="bad"), ctx_for())

        snap = mw.snapshot()
        assert snap["messages"]["errors"] == 1
        # Timed in `finally`: a chain that fails slowly must not look healthy.
        assert snap["latency_ms"]["bad"]["count"] == 1

    async def test_latency_window_is_bounded(self):
        mw = SocketMetricsMiddleware(latency_window=10)
        stack = SocketMiddlewareStack()
        stack.add(mw)
        handler = stack.build_message_handler(noop_message)
        ctx = ctx_for()

        for _ in range(50):
            await handler(envelope(event="ping"), ctx)

        assert mw.snapshot()["latency_ms"]["ping"]["count"] == 10
        assert mw.snapshot()["messages"]["by_event"]["ping"] == 50


class TestLogging:
    async def test_logs_message_without_payload_by_default(self, caplog):
        import logging as _logging

        caplog.set_level(_logging.DEBUG, logger="aquilia.sockets.middleware.logging")

        stack = SocketMiddlewareStack()
        stack.add(SocketLoggingMiddleware())

        await stack.build_message_handler(noop_message)(
            envelope(event="chat.send", payload={"text": "my private message"}),
            ctx_for(),
        )

        assert "chat.send" in caplog.text
        assert "my private message" not in caplog.text

    async def test_payload_logging_is_opt_in_and_truncated(self, caplog):
        import logging as _logging

        caplog.set_level(_logging.DEBUG, logger="aquilia.sockets.middleware.logging")

        stack = SocketMiddlewareStack()
        stack.add(SocketLoggingMiddleware(log_payloads=True, max_payload_chars=20))

        await stack.build_message_handler(noop_message)(
            envelope(payload={"text": "y" * 500}),
            ctx_for(),
        )

        assert "truncated" in caplog.text


# ── Chain config builder ─────────────────────────────────────────────────────


class TestChainBuilder:
    def test_use_produces_serialisable_entries(self):
        chain = SocketMiddlewareChain.chain().use("pkg.mod.Thing", priority=12, messages_per_second=5)

        assert chain.to_list() == [
            {
                "path": "pkg.mod.Thing",
                "priority": 12,
                "scope": "global",
                "name": "Thing",
                "kwargs": {"messages_per_second": 5},
            }
        ]

    def test_presets_always_include_fault_handling(self):
        for preset in (
            SocketMiddlewareChain.defaults(),
            SocketMiddlewareChain.production(),
            SocketMiddlewareChain.minimal(),
        ):
            paths = [e["path"] for e in preset.to_list()]
            assert any("SocketFaultMiddleware" in p for p in paths)

    def test_production_includes_rate_limiting(self):
        paths = [e["path"] for e in SocketMiddlewareChain.production().to_list()]
        assert any("SocketRateLimitMiddleware" in p for p in paths)

    def test_preset_priorities_respect_the_bands(self):
        for entry in SocketMiddlewareChain.production().to_list():
            assert entry["priority"] < 50  # framework bands


# ── Runtime integration ──────────────────────────────────────────────────────


@Socket("/chat/:room")
class ChatSocket(SocketController):
    @OnConnect()
    async def on_connect(self, conn):
        conn.state["connected"] = True

    @Event("ping")
    async def ping(self, conn, payload):
        await conn.send_event("pong", {})

    @Event("boom")
    async def boom(self, conn, payload):
        raise RuntimeError("handler exploded")


def build_runtime(stack=None, max_message_size=65536):
    router = SocketRouter()
    router.register(
        "/chat/:room",
        RouteMetadata(
            namespace="/chat/:room",
            path_pattern="/chat/:room",
            controller_class=ChatSocket,
            handlers={},
            schemas={},
            guards=[],
            allowed_origins=None,
            max_connections=None,
            message_rate_limit=None,
            max_message_size=max_message_size,
        ),
    )
    runtime = AquilaSockets(router=router, middleware_stack=stack)
    runtime.controller_instances["/chat/:room"] = ChatSocket()
    return runtime


async def drive(runtime, frames):
    """Run one connection through the ASGI protocol, returning what was sent."""
    sent = []
    queue = list(frames) + [{"type": "websocket.disconnect", "code": 1000}]
    it = iter(queue)

    async def receive():
        return next(it)

    async def send(message):
        sent.append(message)

    scope = {
        "type": "websocket",
        "path": "/chat/general",
        "headers": [],
        "query_string": b"",
        "client": ("1.2.3.4", 1234),
    }
    await runtime.handle_websocket(scope, receive, send)
    return sent


def frame(event, payload=None, msg_id=None):
    body = {"event": event, "payload": payload or {}}
    if msg_id:
        body["id"] = msg_id
    return {"type": "websocket.receive", "text": json.dumps(body)}


class TestRuntimeIntegration:
    async def test_chains_actually_execute(self):
        """The property the whole subsystem exists for."""
        log = []
        stack = SocketMiddlewareStack()
        stack.add(Recorder("mw", log))

        runtime = build_runtime(stack)
        await runtime.initialize()
        await drive(runtime, [frame("ping")])

        assert log == ["mw:connect>", "mw:connect<", "mw:msg>", "mw:msg<", "mw:disconnect"]

    async def test_connect_rejection_closes_without_accepting(self):
        class Rejector(SocketMiddleware):
            async def on_connect(self, ctx, next_handler):
                from aquilia.sockets.faults import WS_FORBIDDEN

                raise WS_FORBIDDEN("no entry")

        stack = SocketMiddlewareStack()
        stack.add(Rejector())

        runtime = build_runtime(stack)
        await runtime.initialize()
        sent = await drive(runtime, [])

        assert [m["type"] for m in sent] == ["websocket.close"]
        assert sent[0]["code"] == 1008  # WS_FORBIDDEN's ws_close_code

    async def test_accepted_connection_reaches_the_handler(self):
        runtime = build_runtime(SocketMiddlewareStack())
        await runtime.initialize()
        sent = await drive(runtime, [frame("ping")])

        assert sent[0]["type"] == "websocket.accept"
        assert any(m["type"] == "websocket.send" and "pong" in m["text"] for m in sent)

    async def test_handler_error_reports_back_to_the_client(self):
        """Previously logged and swallowed: the client was told nothing."""
        stack = SocketMiddlewareStack()
        stack.add(SocketFaultMiddleware(), priority=2)

        runtime = build_runtime(stack)
        await runtime.initialize()
        sent = await drive(runtime, [frame("boom", msg_id="m1")])

        payloads = [json.loads(m["text"]) for m in sent if m["type"] == "websocket.send"]
        assert any(p.get("payload", {}).get("status") == "error" for p in payloads)

    async def test_undecodable_frame_gets_an_error_not_silence(self):
        runtime = build_runtime(SocketMiddlewareStack())
        await runtime.initialize()
        sent = await drive(runtime, [{"type": "websocket.receive", "text": "{not json"}])

        payloads = [json.loads(m["text"]) for m in sent if m["type"] == "websocket.send"]
        assert any(p.get("event") == "error" for p in payloads)

    async def test_oversized_frame_rejected_before_decode(self):
        runtime = build_runtime(SocketMiddlewareStack(), max_message_size=50)
        await runtime.initialize()
        sent = await drive(runtime, [frame("ping", {"text": "x" * 500})])

        payloads = [json.loads(m["text"]) for m in sent if m["type"] == "websocket.send"]
        error = next(p for p in payloads if p.get("event") == "error")
        assert error["payload"]["code"] == "WS_PAYLOAD_TOO_LARGE"

    async def test_short_circuit_reply_is_delivered(self):
        class Blocker(SocketMiddleware):
            async def on_message(self, envelope, ctx, next_handler):
                return {"blocked": True}

        stack = SocketMiddlewareStack()
        stack.add(Blocker())

        runtime = build_runtime(stack)
        await runtime.initialize()
        sent = await drive(runtime, [frame("ping", msg_id="m1")])

        payloads = [json.loads(m["text"]) for m in sent if m["type"] == "websocket.send"]
        assert any(p.get("payload", {}).get("data") == {"blocked": True} for p in payloads)
        # The handler was skipped, so no pong.
        assert not any("pong" in m.get("text", "") for m in sent)

    async def test_disconnect_hooks_run_on_client_disconnect(self):
        log = []
        stack = SocketMiddlewareStack()
        stack.add(Recorder("mw", log))

        runtime = build_runtime(stack)
        await runtime.initialize()
        await drive(runtime, [])

        assert "mw:disconnect" in log

    async def test_disconnect_hooks_run_on_server_shutdown(self):
        log = []
        stack = SocketMiddlewareStack()
        stack.add(Recorder("mw", log))

        runtime = build_runtime(stack)
        await runtime.initialize()

        sent = []
        started = asyncio.Event()
        never = asyncio.Event()

        async def receive():
            started.set()
            await never.wait()  # hold the connection open
            return {"type": "websocket.disconnect", "code": 1000}

        async def send(message):
            sent.append(message)

        scope = {
            "type": "websocket",
            "path": "/chat/general",
            "headers": [],
            "query_string": b"",
            "client": ("1.2.3.4", 1),
        }
        task = asyncio.create_task(runtime.handle_websocket(scope, receive, send))
        await started.wait()

        await runtime.shutdown()

        assert "mw:disconnect" in log
        never.set()
        task.cancel()

    async def test_namespace_scoped_middleware_only_binds_its_namespace(self):
        log = []
        stack = SocketMiddlewareStack()
        stack.add(Recorder("other", log), scope="namespace:/feed", priority=10)

        runtime = build_runtime(stack)
        await runtime.initialize()
        await drive(runtime, [frame("ping")])

        assert log == []

    async def test_path_params_are_extracted(self):
        """@Socket("/chat/:room") never matched before: the matcher was misused."""
        runtime = build_runtime(SocketMiddlewareStack())
        match = await runtime.router.match("/chat/general")

        assert match is not None
        assert match[2] == {"room": "general"}
