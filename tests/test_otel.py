"""Tests for OpenTelemetry support — all pass without otel SDK installed."""
import pytest

from aquilia.otel import OTelConfig, get_current_span, get_tracer, shutdown


class TestOTelConfig:
    def test_defaults(self):
        cfg = OTelConfig()
        assert cfg.service_name == "aquilia-app"
        assert cfg.service_version == ""
        assert cfg.otlp_endpoint is None
        assert cfg.trace_all is True

    def test_custom(self):
        cfg = OTelConfig(
            service_name="test-svc",
            service_version="2.0.0",
            otlp_endpoint="http://localhost:4317",
            propagators=["tracecontext"],
            resource_attrs={"env": "test"},
        )
        assert cfg.service_name == "test-svc"
        assert cfg.otlp_endpoint == "http://localhost:4317"
        assert "tracecontext" in cfg.propagators
        assert cfg.resource_attrs["env"] == "test"


class TestNoOpTracer:
    def test_get_tracer_returns_noop(self):
        tracer = get_tracer()
        assert tracer is not None

    def test_get_current_span_returns_span(self):
        span = get_current_span()
        assert span is not None
        # Should be a no-op span that doesn't raise
        span.set_attribute("test", "value")
        span.end()

    def test_shutdown_noop(self):
        shutdown()  # should not raise


class TestOTelIntegration:
    def test_setup_without_sdk(self):
        from aquilia.otel._tracer import setup

        cfg = OTelConfig(service_name="test")
        setup(cfg)  # should not raise — graceful fallback

    @pytest.mark.asyncio
    async def test_middleware_passthrough(self):
        from aquilia.otel import OTelMiddleware

        called = []

        async def mock_app(scope, receive, send):
            called.append("app")
            await send({"type": "http.response.start", "status": 200})
            await send({"type": "http.response.body", "body": b"ok", "more_body": False})

        middleware = OTelMiddleware(mock_app)

        messages = []

        async def mock_send(msg):
            messages.append(msg)

        async def mock_receive():
            return {"type": "http.request"}

        scope = {
            "type": "http",
            "method": "GET",
            "path": "/test",
            "headers": [(b"user-agent", b"test-agent")],
            "scheme": "http",
            "server": ("localhost", 8000),
        }
        await middleware(scope, mock_receive, mock_send)
        assert "app" in called
        assert messages[0]["type"] == "http.response.start"