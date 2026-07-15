"""Unit tests for the ADP plugin manager and platform hook facade."""

from __future__ import annotations

from aquilia.devplatform.core.runtime import RuntimeStateStore
from aquilia.devplatform.platform import AquiliaDevelopmentPlatform
from aquilia.devplatform.plugins.protocol import AquiliaDevelopmentPlugin


class GoodPlugin:
    name = "good"
    version = "1.0"

    def __init__(self):
        self.inited = False
        self.shut = False

    def initialize(self, platform):
        self.inited = True

    def shutdown(self):
        self.shut = True


class BadInitPlugin:
    name = "bad"
    version = "0.1"

    def initialize(self, platform):
        raise RuntimeError("init fail")

    def shutdown(self):
        pass


class TestPluginRegistration:
    def test_manual_register_and_list(self, runtime):
        platform = AquiliaDevelopmentPlatform(runtime)
        p = GoodPlugin()
        platform.register_plugin_direct(p)
        assert p.inited
        assert {"name": "good", "version": "1.0"} in platform.list_plugins()

    def test_bad_plugin_isolated(self, runtime):
        platform = AquiliaDevelopmentPlatform(runtime)
        platform.register_plugin_direct(BadInitPlugin())  # must not raise
        # bad plugin not added
        assert platform.list_plugins() == []

    def test_shutdown_all(self, runtime):
        platform = AquiliaDevelopmentPlatform(runtime)
        p = GoodPlugin()
        platform.register_plugin_direct(p)
        platform.shutdown_plugins()
        assert p.shut


class TestHooks:
    def test_request_end_hook_fires(self, runtime):
        platform = AquiliaDevelopmentPlatform(runtime)
        seen = []
        platform.on_request_end(lambda rec: seen.append(rec))
        from aquilia.devplatform.core.state import RequestRecord

        rec = RequestRecord(trace_id="t", method="GET", path="/", status_code=200, duration_ms=1.0)
        runtime.record_request(rec)
        assert seen and seen[0] is rec

    def test_request_end_hook_failure_isolated(self, runtime):
        platform = AquiliaDevelopmentPlatform(runtime)

        def boom(rec):
            raise ValueError("hook boom")

        platform.on_request_end(boom)
        from aquilia.devplatform.core.state import RequestRecord

        runtime.record_request(
            RequestRecord(trace_id="t", method="GET", path="/", status_code=200, duration_ms=1.0)
        )  # must not raise

    def test_exception_hook_isolated(self, runtime):
        platform = AquiliaDevelopmentPlatform(runtime)

        def boom(exc, ctx):
            raise ValueError("nope")

        platform.on_exception(boom)
        platform.fire_exception(RuntimeError("x"))  # must not raise
