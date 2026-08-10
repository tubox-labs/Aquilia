"""
GPU policy and CLI tests.

The GPU tests deliberately exercise both halves of the capability split —
``built`` (the elips wheel carries GPU bindings) and ``available`` (a device is
actually present) — because a GPU-enabled build on a machine with no device is a
normal, supported state, and CI runs on both kinds of host.
"""

from __future__ import annotations

import pytest
from click.testing import CliRunner

from aquilia.vectordb import GpuOptions, is_available
from aquilia.vectordb.faults import VectorGpuFault, VectorGpuUnavailableFault
from aquilia.vectordb.gpu import DeviceInfo, GpuInfo, check_plan, probe, reset_probe_cache, resolve

elips_only = pytest.mark.skipif(not is_available(), reason="elips is not installed")


@pytest.fixture(autouse=True)
def _clear_probe_cache():
    """Each test starts from an unprimed probe so injected state cannot leak."""
    reset_probe_cache()
    yield
    reset_probe_cache()


def _fake_probe(monkeypatch, info: GpuInfo) -> None:
    """Pin the capability snapshot, so policy is tested without real hardware."""
    monkeypatch.setattr("aquilia.vectordb.gpu.probe", lambda **_: info)


DEVICE = DeviceInfo(
    index=0,
    name="Test GPU",
    backend="metal",
    total_memory_bytes=8 * 1024**3,
    free_memory_bytes=4 * 1024**3,
    unified_memory=True,
    supports_fp16=True,
)

NO_BUILD = GpuInfo(built=False, available=False)
BUILT_NO_DEVICE = GpuInfo(built=True, available=False)
WITH_DEVICE = GpuInfo(built=True, available=True, devices=(DEVICE,))


# ── Capability probing ───────────────────────────────────────────────────────


def test_probe_never_raises():
    """Absence of a GPU is a normal outcome, reported rather than raised."""
    info = probe()
    assert isinstance(info.built, bool)
    assert isinstance(info.available, bool)


def test_probe_is_cached():
    assert probe() is probe()


def test_probe_refresh_rereads():
    first = probe()
    assert probe(refresh=True) is not first


def test_device_memory_is_reported_in_gib():
    assert DEVICE.memory_gb == pytest.approx(8.0)


def test_gpu_info_device_lookup():
    assert WITH_DEVICE.device(None) is DEVICE
    assert WITH_DEVICE.device(0) is DEVICE
    assert WITH_DEVICE.device(7) is None
    assert NO_BUILD.device(None) is None


def test_gpu_info_serializes():
    payload = WITH_DEVICE.to_dict()
    assert payload["built"] is True
    assert payload["devices"][0]["name"] == "Test GPU"


# ── Policy resolution ────────────────────────────────────────────────────────


def test_cpu_only_never_demands_a_device(monkeypatch):
    _fake_probe(monkeypatch, NO_BUILD)
    assert resolve(GpuOptions(policy="cpu_only")).available is False


def test_prefer_gpu_degrades_without_a_device(monkeypatch):
    _fake_probe(monkeypatch, BUILT_NO_DEVICE)
    # Degrades rather than raising — that is the whole point of "prefer".
    assert resolve(GpuOptions(policy="prefer_gpu")).available is False


def test_require_gpu_fails_when_not_built(monkeypatch):
    _fake_probe(monkeypatch, NO_BUILD)
    with pytest.raises(VectorGpuUnavailableFault) as exc:
        resolve(GpuOptions(policy="require_gpu"), store="s")
    assert "no GPU bindings" in exc.value.message


def test_require_gpu_fails_when_no_device_present(monkeypatch):
    """`built` and `available` are distinct, and the message says which failed."""
    _fake_probe(monkeypatch, BUILT_NO_DEVICE)
    with pytest.raises(VectorGpuUnavailableFault) as exc:
        resolve(GpuOptions(policy="require_gpu"), store="s")
    assert "no usable device" in exc.value.message


def test_require_gpu_succeeds_with_a_device(monkeypatch):
    _fake_probe(monkeypatch, WITH_DEVICE)
    assert resolve(GpuOptions(policy="require_gpu")).available is True


def test_require_gpu_rejects_a_missing_ordinal(monkeypatch):
    _fake_probe(monkeypatch, WITH_DEVICE)
    with pytest.raises(VectorGpuUnavailableFault) as exc:
        resolve(GpuOptions(policy="require_gpu", device=3), store="s")
    assert "device 3 not found" in exc.value.message


# ── Query-time fallback ──────────────────────────────────────────────────────


class _Plan:
    def __init__(self, gpu_index: bool):
        self.gpu_index = gpu_index
        self.strategy = "ann_index"


def test_fallback_allow_accepts_cpu_execution():
    check_plan(_Plan(gpu_index=False), GpuOptions(policy="prefer_gpu", fallback="allow"))


def test_fallback_warn_accepts_but_logs(caplog):
    check_plan(
        _Plan(gpu_index=False),
        GpuOptions(policy="prefer_gpu", fallback="warn"),
        collection="notes",
    )
    assert "fell back to CPU" in caplog.text


def test_fallback_require_raises_on_cpu_execution():
    """elips falls back per-query even under require_gpu; this is the opt-in check."""
    with pytest.raises(VectorGpuFault) as exc:
        check_plan(
            _Plan(gpu_index=False),
            GpuOptions(policy="prefer_gpu", fallback="require"),
            collection="notes",
        )
    assert exc.value.code == "VECTOR_GPU_FALLBACK"


def test_fallback_require_accepts_gpu_execution():
    check_plan(_Plan(gpu_index=True), GpuOptions(policy="prefer_gpu", fallback="require"))


def test_cpu_only_skips_the_fallback_check():
    check_plan(_Plan(gpu_index=False), GpuOptions(policy="cpu_only", fallback="require"))


# ── Native config translation ────────────────────────────────────────────────


@elips_only
def test_build_config_returns_none_for_cpu_only():
    from aquilia.vectordb.gpu import build_config

    assert build_config(GpuOptions(policy="cpu_only")) is None


@elips_only
def test_build_config_returns_none_without_a_device(monkeypatch):
    from aquilia.vectordb.gpu import build_config

    _fake_probe(monkeypatch, BUILT_NO_DEVICE)
    assert build_config(GpuOptions(policy="prefer_gpu")) is None


# ── CLI ──────────────────────────────────────────────────────────────────────


@pytest.fixture
def runner():
    return CliRunner()


def _workspace(tmp_path, extra: str = "") -> None:
    """Write a minimal workspace declaring one vector store."""
    (tmp_path / "workspace.py").write_text(
        "from aquilia.workspace import Workspace\n"
        "workspace = (\n"
        '    Workspace("cli-test")\n'
        "    .vectordb(\n"
        '        path="./vecs",\n'
        '        stores={"default": {"dimension": 8}' + extra + "},\n"
        "    )\n"
        ")\n"
    )


def test_cli_group_registers():
    from aquilia.cli.commands.vectordb import vectordb_group

    names = set(vectordb_group.commands)
    assert {"status", "gpu", "models", "inspect", "compact", "vacuum", "reindex"} <= names


def test_status_reports_no_workspace(runner, tmp_path):
    from aquilia.cli.commands.vectordb import vectordb_status

    with runner.isolated_filesystem(temp_dir=tmp_path):
        result = runner.invoke(vectordb_status)
    assert result.exit_code == 0
    assert "No vector stores configured" in result.output


def test_status_lists_configured_stores(runner, tmp_path):
    from aquilia.cli.commands.vectordb import vectordb_status

    with runner.isolated_filesystem(temp_dir=tmp_path) as cwd:
        from pathlib import Path

        _workspace(Path(cwd))
        result = runner.invoke(vectordb_status)

    assert result.exit_code == 0
    assert "default" in result.output


def test_status_json_is_machine_readable(runner, tmp_path):
    import json
    from pathlib import Path

    from aquilia.cli.commands.vectordb import vectordb_status

    with runner.isolated_filesystem(temp_dir=tmp_path) as cwd:
        _workspace(Path(cwd))
        result = runner.invoke(vectordb_status, ["--json"])

    payload = json.loads(result.output)
    assert payload["enabled"] is True
    assert payload["stores"][0]["alias"] == "default"


@elips_only
def test_gpu_command_reports_both_capability_halves(runner, tmp_path):
    import json
    from pathlib import Path

    from aquilia.cli.commands.vectordb import vectordb_gpu

    with runner.isolated_filesystem(temp_dir=tmp_path) as cwd:
        _workspace(Path(cwd))
        result = runner.invoke(vectordb_gpu, ["--json"])

    payload = json.loads(result.output)
    assert "built" in payload["probe"]
    assert "available" in payload["probe"]


@elips_only
def test_inspect_opens_and_closes_the_store(runner, tmp_path):
    import json
    from pathlib import Path

    from aquilia.cli.commands.vectordb import vectordb_inspect

    with runner.isolated_filesystem(temp_dir=tmp_path) as cwd:
        _workspace(Path(cwd))
        result = runner.invoke(vectordb_inspect, ["--json"])

    payload = json.loads(result.output)
    assert payload["stores"][0]["ok"] is True


@elips_only
def test_compact_refuses_a_read_only_store(runner, tmp_path):
    from pathlib import Path

    from aquilia.cli.commands.vectordb import vectordb_compact

    with runner.isolated_filesystem(temp_dir=tmp_path) as cwd:
        (Path(cwd) / "workspace.py").write_text(
            "from aquilia.workspace import Workspace\n"
            "workspace = (\n"
            '    Workspace("cli-test")\n'
            "    .vectordb(\n"
            '        path="./vecs",\n'
            '        stores={"ro": {"dimension": 8, "read_only": True}},\n'
            "    )\n"
            ")\n"
        )
        result = runner.invoke(vectordb_compact, ["ro"])

    assert result.exit_code == 1
    assert "read_only" in result.output


def test_unknown_store_alias_exits_nonzero(runner, tmp_path):
    from pathlib import Path

    from aquilia.cli.commands.vectordb import vectordb_inspect

    with runner.isolated_filesystem(temp_dir=tmp_path) as cwd:
        _workspace(Path(cwd))
        result = runner.invoke(vectordb_inspect, ["ghost"])

    assert result.exit_code == 1
    assert "ghost" in result.output
