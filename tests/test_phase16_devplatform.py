"""
Phase 16 — DevPlatform: Framework Integration & Security Hardening.

Verifies:
  Task 1 — Fault system: DEVPLATFORM_DOMAIN registered, DevPlatformFault
           hierarchy present, report_fault routes through FaultEngine.

  Task 2 — Config: AquiliaDevelopmentConfig loads via pyconfig.Env, validates
           in __post_init__ (ConfigurationFault), to_dict() round-trips,
           AQ_DEV_FD=0 no longer coerced to None.

  Task 3 — Datastructures: SingletonMixin gives per-class singletons,
           BoundedCache evicts LRU.

  Task 4 — Security: WebSocket max frame size guard, UDS stale-socket
           handling, redact_body_preview scrubs token prefixes, workspace
           root validation.

  Task 5 — Wiring: Lane.DEVPLATFORM exists, WebSocketTracker register/
           unregister lifecycle, RequestRecord body preview populated.
"""

import os
import socket
import stat
import tempfile

import pytest

from aquilia.faults.core import DOMAIN_DEFAULTS, Fault, FaultDomain, Severity

# ============================================================================
# Task 1 — Fault system
# ============================================================================
from aquilia.devplatform.faults import (
    DEVPLATFORM_DOMAIN,
    ConfigurationFault,
    DevPlatformFault,
    InspectorFault,
    ReloadFault,
    StartupFault,
    WorkerFault,
    report_fault,
)


class TestDevPlatformFaults:
    def test_domain_registered_as_standard(self):
        assert FaultDomain.DEVPLATFORM.name == "devplatform"
        assert DEVPLATFORM_DOMAIN is FaultDomain.DEVPLATFORM
        assert FaultDomain.DEVPLATFORM in DOMAIN_DEFAULTS

    def test_all_faults_subclass_base_and_fault(self):
        for cls in (StartupFault, ReloadFault, InspectorFault, WorkerFault, ConfigurationFault):
            assert issubclass(cls, DevPlatformFault)
            assert issubclass(cls, Fault)

    def test_faults_carry_domain_and_code(self):
        fault = StartupFault("socket bind failed")
        assert fault.domain == DEVPLATFORM_DOMAIN
        assert fault.code == "DEVPLATFORM_STARTUP_FAILED"
        assert "socket bind failed" in fault.message
        assert fault.metadata["reason"] == "socket bind failed"

    def test_severity_taxonomy(self):
        assert StartupFault("x").severity == Severity.FATAL
        assert ConfigurationFault("x").severity == Severity.FATAL
        assert ReloadFault("x").severity == Severity.ERROR
        assert InspectorFault("x").severity == Severity.WARN
        assert WorkerFault("x").severity == Severity.WARN

    def test_report_fault_routes_to_fault_engine(self):
        processed = []

        class FakeEngine:
            def process(self, fault):
                processed.append(fault)

        class FakeApp:
            fault_engine = FakeEngine()

        fault = WorkerFault("boom")
        report_fault(fault, app=FakeApp())
        assert processed == [fault]

    def test_report_fault_logs_when_no_engine(self, caplog):
        # No app / no fault_engine → falls back to logging, must not raise.
        report_fault(InspectorFault("no engine reachable"), app=None)


# ============================================================================
# Task 2 — Config
# ============================================================================
from aquilia.devplatform.config import AquiliaDevelopmentConfig


class TestConfig:
    def test_defaults(self):
        c = AquiliaDevelopmentConfig()
        assert c.host == "127.0.0.1"
        assert c.port == 8000
        assert c.http == "h11"
        assert c.ws == "auto"

    def test_to_dict_round_trip(self):
        c = AquiliaDevelopmentConfig(port=8080)
        d = c.to_dict()
        d.pop("reload_dirs")  # Path list, reconstructed separately
        c2 = AquiliaDevelopmentConfig(**d)
        assert c2.port == 8080
        assert c2.to_dict()["host"] == c.to_dict()["host"]

    def test_invalid_http_raises_configuration_fault(self):
        with pytest.raises(ConfigurationFault):
            AquiliaDevelopmentConfig(http="bogus")

    def test_invalid_ws_raises(self):
        with pytest.raises(ConfigurationFault):
            AquiliaDevelopmentConfig(ws="bogus")

    def test_negative_fd_raises(self):
        with pytest.raises(ConfigurationFault):
            AquiliaDevelopmentConfig(fd=-1)

    def test_out_of_range_port_raises(self):
        with pytest.raises(ConfigurationFault):
            AquiliaDevelopmentConfig(port=99999)

    def test_non_positive_threshold_raises(self):
        with pytest.raises(ConfigurationFault):
            AquiliaDevelopmentConfig(sql_explain_threshold_ms=0)

    def test_fd_zero_env_not_coerced_to_none(self, monkeypatch):
        monkeypatch.setenv("AQ_DEV_FD", "0")
        c = AquiliaDevelopmentConfig()
        assert c.fd == 0

    def test_env_override(self, monkeypatch):
        monkeypatch.setenv("AQ_DEV_PORT", "9123")
        c = AquiliaDevelopmentConfig()
        assert c.port == 9123


# ============================================================================
# Task 3 — Datastructures
# ============================================================================
from aquilia.devplatform.core._base import SingletonMixin
from aquilia.devplatform.core._cache import BoundedCache


class TestSingletonMixin:
    def test_per_class_singletons(self):
        class A(SingletonMixin):
            pass

        class B(SingletonMixin):
            pass

        a1, a2 = A.get_instance(), A.get_instance()
        b1 = B.get_instance()
        assert a1 is a2
        assert a1 is not b1

    def test_reset_instance(self):
        class C(SingletonMixin):
            pass

        first = C.get_instance()
        C.reset_instance()
        assert C.get_instance() is not first


class TestBoundedCache:
    def test_lru_eviction(self):
        cache: BoundedCache[str, int] = BoundedCache(max_size=2)
        cache.set("a", 1)
        cache.set("b", 2)
        cache.get("a")  # touch a → b now oldest
        cache.set("c", 3)  # evicts b
        assert cache.get("b") is None
        assert cache.get("a") == 1
        assert cache.get("c") == 3

    def test_len_and_contains(self):
        cache: BoundedCache[str, int] = BoundedCache(max_size=4)
        cache.set("k", 1)
        assert "k" in cache
        assert len(cache) == 1


# ============================================================================
# Task 4 — Security
# ============================================================================
from aquilia.devplatform.core.protocol import redact_body_preview
from aquilia.devplatform.core.websocket_transport import _MAX_FRAME_SIZE
from aquilia.devplatform.devserver import AquiliaDevelopmentServer


class TestSecurity:
    def test_max_frame_size_is_bounded(self):
        assert 0 < _MAX_FRAME_SIZE <= 64 * 1024 * 1024

    def test_body_preview_scrubs_bearer(self):
        out = redact_body_preview(b'{"auth": "Bearer supersecrettoken"}')
        assert "supersecrettoken" not in out
        assert "REDACTED" in out

    def test_body_preview_empty_is_none(self):
        assert redact_body_preview(b"") is None

    def test_body_preview_size_capped(self):
        big = b"x" * 10000
        out = redact_body_preview(big, limit=100)
        assert len(out) <= 102  # 100 + ellipsis

    @pytest.mark.skipif(not hasattr(socket, "AF_UNIX"), reason="AF_UNIX support required")
    def test_prepare_uds_unlinks_stale_socket(self):
        with tempfile.TemporaryDirectory() as d:
            path = os.path.join(d, "test.sock")
            s = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
            s.bind(path)
            s.close()  # leaves a stale socket file on disk
            assert stat.S_ISSOCK(os.stat(path).st_mode)
            AquiliaDevelopmentServer._prepare_uds_path(path)
            assert not os.path.exists(path)

    def test_prepare_uds_refuses_non_socket(self):
        with tempfile.TemporaryDirectory() as d:
            path = os.path.join(d, "regular.txt")
            with open(path, "w") as f:
                f.write("important data")
            with pytest.raises(StartupFault):
                AquiliaDevelopmentServer._prepare_uds_path(path)
            assert os.path.exists(path)  # not clobbered

    def test_workspace_root_rejects_relative(self, monkeypatch):
        from aquilia.devplatform.reload.analyzer import _resolve_workspace_root

        monkeypatch.setenv("AQUILIA_WORKSPACE", "relative/path")
        with pytest.raises(ConfigurationFault):
            _resolve_workspace_root()

    def test_workspace_root_none_when_unset(self, monkeypatch):
        from aquilia.devplatform.reload.analyzer import _resolve_workspace_root

        monkeypatch.delenv("AQUILIA_WORKSPACE", raising=False)
        assert _resolve_workspace_root() is None


# ============================================================================
# Task 5 — Wiring
# ============================================================================
from aquilia.devplatform.core.websocket import WebSocketEntry, WebSocketTracker
from aquilia.inspector.trace import Lane


class TestWiring:
    def test_devplatform_lane_exists(self):
        assert Lane.DEVPLATFORM.value == "devplatform"

    def test_websocket_tracker_lifecycle(self):
        WebSocketTracker.reset_instance()
        tracker = WebSocketTracker.get_instance()
        tracker.register(WebSocketEntry(connection_id="c1", path="/ws", client_addr="127.0.0.1:5000"))
        assert tracker.active_count == 1
        tracker.record_inbound_frame("c1")
        tracker.record_outbound_frame("c1")
        entries = tracker.get_active_connections()
        assert entries[0].inbound_frames == 1
        assert entries[0].outbound_frames == 1
        tracker.unregister("c1", code=1000)
        assert tracker.active_count == 0
        assert tracker.total_disconnected == 1
        WebSocketTracker.reset_instance()

    def test_request_record_body_preview_field(self):
        from aquilia.devplatform.core.state import RequestRecord

        rec = RequestRecord(trace_id="t", method="POST", path="/", status_code=200, duration_ms=1.0)
        rec.request_body_preview = redact_body_preview(b'{"x": 1}')
        d = rec.to_dict()
        assert d["request_body_preview"] == '{"x": 1}'
