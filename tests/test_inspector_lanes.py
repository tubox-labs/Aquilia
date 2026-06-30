from pathlib import Path
from unittest.mock import AsyncMock, MagicMock

import pytest

from aquilia.controller.base import RequestCtx
from aquilia.inspector.config import InspectorConfig
from aquilia.inspector.middleware import InspectorMiddleware
from aquilia.inspector.trace import Lane, RequestTrace, _reset_current_trace, _set_current_trace
from aquilia.request import Request
from aquilia.response import Response


@pytest.mark.asyncio
async def test_versions_lane_recorded():
    config = InspectorConfig(enabled=True)
    middleware = InspectorMiddleware(config)

    request = Request(
        scope={
            "type": "http",
            "method": "GET",
            "path": "/index",
            "headers": [],
        },
        receive=None,
    )
    ctx = RequestCtx(request=request, request_id="req-versions")

    async def next_handler(req, context):
        return Response(b"ok")

    await middleware(request, ctx, next_handler)

    # Inspect the collector
    from aquilia.inspector.collector import get_collector

    trace = get_collector(config).get("req-versions")
    assert trace is not None

    version_spans = [s for s in trace.spans if s.lane == Lane.VERSIONS]
    assert len(version_spans) == 1
    span = version_spans[0]
    assert span.label == "Resolve Framework Versions"
    assert "aquilia" in span.detail
    assert "python" in span.detail


@pytest.mark.asyncio
async def test_settings_lane_recorded():
    from aquilia.config import ConfigLoader

    trace = RequestTrace(
        trace_id="req-settings",
        method="GET",
        path="/index",
        route_pattern=None,
        started_at=1.0,
        started_monotonic=1.0,
    )
    token = _set_current_trace(trace)

    try:
        loader = ConfigLoader()
        loader.config_data = {
            "app": "test",
            "security": {
                "secret_key": "mysecret",
            },
        }

        # Test normal access
        val1 = loader.get("app")
        assert val1 == "test"

        # Test sensitive access
        val2 = loader.get("security.secret_key")
        assert val2 == "mysecret"

        settings_spans = [s for s in trace.spans if s.lane == Lane.SETTINGS]
        assert len(settings_spans) == 2

        # First span check
        s1 = settings_spans[0]
        assert s1.detail["path"] == "app"
        assert s1.detail["value"] == "'test'"

        # Sensitive span check
        s2 = settings_spans[1]
        assert s2.detail["path"] == "security.secret_key"
        assert s2.detail["value"] == "***REDACTED***"
    finally:
        _reset_current_trace(token)


@pytest.mark.asyncio
async def test_templates_lane_recorded():
    from aquilia.templates.engine import TemplateEngine

    trace = RequestTrace(
        trace_id="req-templates",
        method="GET",
        path="/index",
        route_pattern=None,
        started_at=1.0,
        started_monotonic=1.0,
    )
    token = _set_current_trace(trace)

    try:
        # Mock template and env
        loader = MagicMock()
        engine = TemplateEngine(loader=loader)
        mock_template = MagicMock()
        mock_template.render_async = AsyncMock(return_value="rendered output")
        mock_template.render = MagicMock(return_value="rendered output")
        engine.get_template = MagicMock(return_value=mock_template)

        # Async render
        res_async = await engine.render("home.html", {"name": "Alice"})
        assert res_async == "rendered output"

        # Sync render
        res_sync = engine.render_sync("about.html", {"name": "Bob"})
        assert res_sync == "rendered output"

        template_spans = [s for s in trace.spans if s.lane == Lane.TEMPLATES]
        assert len(template_spans) == 2

        assert template_spans[0].detail["template_name"] == "home.html"
        assert "name" in template_spans[0].detail["context_keys"]

        assert template_spans[1].detail["template_name"] == "about.html"
        assert "name" in template_spans[1].detail["context_keys"]
    finally:
        _reset_current_trace(token)


@pytest.mark.asyncio
async def test_cache_lane_recorded():
    from aquilia.cache.service import CacheService

    trace = RequestTrace(
        trace_id="req-cache",
        method="GET",
        path="/index",
        route_pattern=None,
        started_at=1.0,
        started_monotonic=1.0,
    )
    token = _set_current_trace(trace)

    try:
        # Create mock backend
        backend = MagicMock()
        backend.name = "memory"
        mock_entry = MagicMock()
        mock_entry.value = "cached_val"
        backend.get = AsyncMock(return_value=mock_entry)
        backend.set = AsyncMock(return_value=None)
        backend.delete = AsyncMock(return_value=True)
        backend.exists = AsyncMock(return_value=True)

        config = MagicMock()
        config.apply_jitter = MagicMock(side_effect=lambda ttl: ttl)

        cache = CacheService(backend=backend, config=config)

        # Test cache methods
        await cache.get("user:1")
        await cache.set("user:1", "data", ttl=60)
        await cache.delete("user:1")
        await cache.exists("user:1")

        cache_spans = [s for s in trace.spans if s.lane == Lane.CACHE]
        assert len(cache_spans) == 4

        assert cache_spans[0].label == "Cache GET: user:1"
        assert cache_spans[0].detail["hit"] is True

        assert cache_spans[1].label == "Cache SET: user:1"
        assert cache_spans[1].detail["ttl"] == 60

        assert cache_spans[2].label == "Cache DELETE: user:1"
        assert cache_spans[2].detail["result"] is True

        assert cache_spans[3].label == "Cache EXISTS: user:1"
        assert cache_spans[3].detail["result"] is True
    finally:
        _reset_current_trace(token)


@pytest.mark.asyncio
async def test_signals_lane_recorded():
    from aquilia.models.signals import Signal

    trace = RequestTrace(
        trace_id="req-signals",
        method="GET",
        path="/index",
        route_pattern=None,
        started_at=1.0,
        started_monotonic=1.0,
    )
    token = _set_current_trace(trace)

    try:
        test_signal = Signal("test_event")

        # Connect mock receivers
        receiver1 = AsyncMock(return_value="resp1")
        receiver1.__name__ = "receiver1"
        test_signal.connect(receiver1)

        # Send signal
        await test_signal.send(sender=None)

        signal_spans = [s for s in trace.spans if s.lane == Lane.SIGNALS]
        assert len(signal_spans) == 1
        span = signal_spans[0]
        assert span.label == "Signal: test_event (from None)"
        assert span.detail["signal"] == "test_event"
        assert "receiver1" in span.detail["receivers"]
    finally:
        _reset_current_trace(token)


@pytest.mark.asyncio
async def test_static_lane_recorded():
    from aquilia.middleware_ext.static import StaticMiddleware

    trace = RequestTrace(
        trace_id="req-static",
        method="GET",
        path="/static/app.js",
        route_pattern=None,
        started_at=1.0,
        started_monotonic=1.0,
    )
    token = _set_current_trace(trace)

    try:
        middleware = StaticMiddleware()

        # Mock the lookups & serve_file to return a valid response
        middleware._trie.lookup = MagicMock(return_value=(Path("/static"), "app.js"))
        middleware._serve_file = MagicMock(return_value=Response(b"console.log('hello')", status=200))

        request = Request(
            scope={
                "type": "http",
                "method": "GET",
                "path": "/static/app.js",
                "headers": [],
            },
            receive=None,
        )
        ctx = RequestCtx(request=request, request_id="req-static")

        async def next_handler(req, context):
            return Response(b"not found", status=404)

        response = await middleware(request, ctx, next_handler)
        assert response.status == 200

        static_spans = [s for s in trace.spans if s.lane == Lane.STATIC]
        assert len(static_spans) == 1
        span = static_spans[0]
        assert span.label == "Static file: /static/app.js"
        assert span.detail["path"] == "/static/app.js"
        assert span.detail["served"] is True
        assert span.detail["status_code"] == 200
    finally:
        _reset_current_trace(token)


@pytest.mark.asyncio
async def test_mail_lane_recorded():
    from aquilia.mail.service import MailService

    trace = RequestTrace(
        trace_id="req-mail",
        method="GET",
        path="/index",
        route_pattern=None,
        started_at=1.0,
        started_monotonic=1.0,
    )
    token = _set_current_trace(trace)

    try:
        config = MagicMock()
        config.default_from = "sender@example.com"
        config.subject_prefix = "[TEST] "
        config.preview_mode = True

        service = MailService(config=config)

        # Mock EmailMessage
        msg = MagicMock()
        envelope = MagicMock()
        envelope.id = "env-123"
        envelope.subject = "Hello World"
        envelope.from_email = "sender@example.com"
        envelope.to = ["rcpt@example.com"]
        envelope.cc = []
        envelope.status.value = "sent"
        msg.build_envelope = MagicMock(return_value=(envelope, []))

        res_id = await service.send_message(msg)
        assert res_id == "env-123"

        mail_spans = [s for s in trace.spans if s.lane == Lane.MAIL]
        assert len(mail_spans) == 1
        span = mail_spans[0]
        assert span.label == "Outbound Email: [TEST] Hello World"
        assert span.detail["envelope_id"] == "env-123"
        assert span.detail["to"] == ["rcpt@example.com"]
    finally:
        _reset_current_trace(token)


@pytest.mark.asyncio
async def test_tasks_lane_recorded():
    from aquilia.tasks.engine import TaskManager

    trace = RequestTrace(
        trace_id="req-tasks",
        method="GET",
        path="/index",
        route_pattern=None,
        started_at=1.0,
        started_monotonic=1.0,
    )
    token = _set_current_trace(trace)

    try:
        backend = MagicMock()
        backend.push = AsyncMock()

        manager = TaskManager(backend=backend)

        def dummy_task():
            pass

        dummy_task.__module__ = "dummy"
        dummy_task.__qualname__ = "dummy_task"

        job_id = await manager.enqueue(dummy_task, 1, 2, queue="default")
        assert job_id is not None

        task_spans = [s for s in trace.spans if s.lane == Lane.TASKS]
        assert len(task_spans) == 1
        span = task_spans[0]
        assert "dummy_task" in span.label
        assert span.detail["queue"] == "default"
        assert span.detail["args"] == [1, 2]
    finally:
        _reset_current_trace(token)


@pytest.mark.asyncio
async def test_sockets_lane_recorded():
    from aquilia.sockets.controller import SocketController

    trace = RequestTrace(
        trace_id="req-sockets",
        method="GET",
        path="/index",
        route_pattern=None,
        started_at=1.0,
        started_monotonic=1.0,
    )
    token = _set_current_trace(trace)

    try:
        controller = SocketController()
        controller.namespace = "/chat"
        controller.adapter = MagicMock()
        controller.adapter.publish = AsyncMock()
        controller.adapter.broadcast = AsyncMock()

        await controller.publish_room("room1", "chat_msg", {"text": "hello"})
        await controller.broadcast("announcement", {"text": "welcome"})

        socket_spans = [s for s in trace.spans if s.lane == Lane.SOCKETS]
        assert len(socket_spans) == 2

        assert "WS Publish Room: room1" in socket_spans[0].label
        assert socket_spans[0].detail["event"] == "chat_msg"

        assert "WS Broadcast: announcement" in socket_spans[1].label
        assert socket_spans[1].detail["event"] == "announcement"
    finally:
        _reset_current_trace(token)


@pytest.mark.asyncio
async def test_middleware_auth_locale_captured():
    config = InspectorConfig(enabled=True)
    middleware = InspectorMiddleware(config)

    request = Request(
        scope={
            "type": "http",
            "method": "GET",
            "path": "/index",
            "headers": [],
        },
        receive=None,
    )
    # Set session, identity, locale in request state
    mock_session = MagicMock()
    mock_session.id = "sess_12345"
    mock_session.scope.value = "user"

    mock_identity = MagicMock()
    mock_identity.id = "user_99"
    mock_identity.type = "user"
    mock_identity.get_attribute = MagicMock(side_effect=lambda k, d=None: "level3" if k == "clearance" else ["admin"])

    request.state["session"] = mock_session
    request.state["identity"] = mock_identity
    request.state["locale"] = "fr-CA"

    ctx = RequestCtx(request=request, request_id="req-metadata")

    async def next_handler(req, context):
        return Response(b"ok")

    await middleware(request, ctx, next_handler)

    from aquilia.inspector.collector import get_collector

    trace = get_collector(config).get("req-metadata")
    assert trace is not None

    # Check Auth span
    auth_spans = [s for s in trace.spans if s.lane == "auth"]
    assert len(auth_spans) == 1
    auth_span = auth_spans[0]
    assert auth_span.detail["session_id"] == "sess_12345"
    assert auth_span.detail["user_id"] == "user_99"
    assert auth_span.detail["clearance"] == "level3"
    assert auth_span.detail["roles"] == ["admin"]

    # Check Locale span
    locale_spans = [s for s in trace.spans if s.lane == "i18n"]
    assert len(locale_spans) == 1
    locale_span = locale_spans[0]
    assert locale_span.detail["locale"] == "fr-CA"
