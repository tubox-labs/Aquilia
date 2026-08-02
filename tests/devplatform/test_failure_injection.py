"""Failure-injection tests: optional deps missing, resource exhaustion, faults."""

from __future__ import annotations

import builtins

import socket

import pytest

from aquilia.devplatform.config import AquiliaDevelopmentConfig
from aquilia.devplatform.faults import ConfigurationFault, StartupFault
from aquilia.devplatform.devserver import AquiliaDevelopmentServer


class TestOptionalDepsMissing:
    def test_rss_without_psutil(self, monkeypatch):
        real_import = builtins.__import__

        def fake_import(name, *a, **k):
            if name == "psutil":
                raise ImportError("no psutil")
            return real_import(name, *a, **k)

        monkeypatch.setattr(builtins, "__import__", fake_import)
        from aquilia.devplatform.diagnostics.system import read_rss_bytes

        # Must still return a value (proc/resource fallback or 0), never raise.
        assert read_rss_bytes() >= 0

    def test_cpu_sampler_without_psutil(self, monkeypatch):
        real_import = builtins.__import__

        def fake_import(name, *a, **k):
            if name == "psutil":
                raise ImportError("no psutil")
            return real_import(name, *a, **k)

        monkeypatch.setattr(builtins, "__import__", fake_import)
        from aquilia.devplatform.diagnostics.system import CPUSampler

        s = CPUSampler()
        assert s.sample() >= 0.0

    async def test_watcher_without_watchfiles(self, monkeypatch, tmp_path, runtime, caplog):
        real_import = builtins.__import__

        def fake_import(name, *a, **k):
            if name == "watchfiles":
                raise ImportError("no watchfiles")
            return real_import(name, *a, **k)

        monkeypatch.setattr(builtins, "__import__", fake_import)
        from aquilia.devplatform.reload.watcher import WorkspaceWatcher

        cfg = AquiliaDevelopmentConfig(port=8000, reload=True, reload_dirs=[tmp_path])
        w = WorkspaceWatcher(cfg, runtime)
        await w.watch()  # returns cleanly, disables reload
        assert not w._running


class TestConfigValidation:
    def test_invalid_http(self):
        with pytest.raises(ConfigurationFault):
            AquiliaDevelopmentConfig(http="bogus")

    def test_invalid_ws(self):
        with pytest.raises(ConfigurationFault):
            AquiliaDevelopmentConfig(ws="bogus")

    def test_negative_fd(self):
        with pytest.raises(ConfigurationFault):
            AquiliaDevelopmentConfig(fd=-5)

    def test_port_out_of_range(self):
        with pytest.raises(ConfigurationFault):
            AquiliaDevelopmentConfig(port=70000)

    def test_zero_threshold(self):
        with pytest.raises(ConfigurationFault):
            AquiliaDevelopmentConfig(memory_snapshot_interval_s=0)

    def test_to_dict_round_trip(self):
        c = AquiliaDevelopmentConfig(port=8123, http="auto")
        d = c.to_dict()
        d.pop("reload_dirs")
        c2 = AquiliaDevelopmentConfig(**d)
        assert c2.port == 8123 and c2.http == "auto"


class TestUDSHardening:
    def test_refuses_non_socket_file(self, tmp_path):
        f = tmp_path / "data.txt"
        f.write_text("precious")
        with pytest.raises(StartupFault):
            AquiliaDevelopmentServer._prepare_uds_path(str(f))
        assert f.exists()  # not clobbered

    @pytest.mark.skipif(not hasattr(socket, "AF_UNIX"), reason="AF_UNIX support required")
    def test_unlinks_stale_socket(self):
        import os
        import socket as _s
        import tempfile

        tmpdir_kwargs = {"dir": "/tmp"} if os.path.exists("/tmp") else {}
        with tempfile.TemporaryDirectory(**tmpdir_kwargs) as d:
            path = os.path.join(d, "s.sock")
            srv = _s.socket(_s.AF_UNIX, _s.SOCK_STREAM)
            srv.bind(path)
            srv.close()
            AquiliaDevelopmentServer._prepare_uds_path(path)
            assert not os.path.exists(path)
