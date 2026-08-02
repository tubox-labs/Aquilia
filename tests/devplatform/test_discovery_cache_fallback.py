"""
Regression + unit tests for the discovery cache surp/JSON fallback.

Guards the 'No module named surp' noisy-warning bug: when the optional ``surp``
backend is absent the cache must fall back to JSON silently (debug, not
warning) and remain fully functional.
"""

from __future__ import annotations

import logging
from pathlib import Path

from aquilia.discovery.engine import DiscoveryCache, _detect_cache_backend


def test_backend_detected():
    assert _detect_cache_backend() in ("surp", "json")


def test_json_fallback_path_when_no_surp(tmp_path: Path, monkeypatch):
    # Force the json backend regardless of whether surp is installed.
    monkeypatch.setattr("aquilia.discovery.engine._detect_cache_backend", lambda: "json")
    cache = DiscoveryCache(tmp_path / ".aquilia" / "discovery_cache.surp")
    # .surp suffix rewritten to .json under the json backend.
    assert cache.cache_file.suffix == ".json"


def test_roundtrip(tmp_path: Path, monkeypatch):
    monkeypatch.setattr("aquilia.discovery.engine._detect_cache_backend", lambda: "json")
    path = tmp_path / ".aquilia" / "discovery_cache.surp"
    c = DiscoveryCache(path)
    c.set("mod/x.py", 123.0, "hashval", [{"kind": "controller"}])
    c.save()
    c2 = DiscoveryCache(path)
    entry = c2.get("mod/x.py")
    assert entry == {"mtime": 123.0, "hash": "hashval", "components": [{"kind": "controller"}]}


def test_save_no_warning_when_surp_missing(tmp_path: Path, monkeypatch, caplog):
    """The core regression: a missing optional backend must not WARN."""
    monkeypatch.setattr("aquilia.discovery.engine._detect_cache_backend", lambda: "json")
    c = DiscoveryCache(tmp_path / "c.surp")
    c.set("a", 1.0, "h", [])
    with caplog.at_level(logging.WARNING, logger="aquilia.discovery"):
        c.save()
    warnings = [r for r in caplog.records if r.levelno >= logging.WARNING]
    assert warnings == []


def test_corrupt_cache_starts_empty(tmp_path: Path, monkeypatch):
    monkeypatch.setattr("aquilia.discovery.engine._detect_cache_backend", lambda: "json")
    path = tmp_path / "c.json"
    path.write_text("{not valid json", encoding="utf-8")
    c = DiscoveryCache(path)
    assert c.get("anything") is None


def test_save_to_readonly_dir_is_nonfatal(tmp_path: Path, monkeypatch, caplog):
    monkeypatch.setattr("aquilia.discovery.engine._detect_cache_backend", lambda: "json")
    # Point at a path whose parent cannot be created (a file where a dir is expected).
    blocker = tmp_path / "blocker"
    blocker.write_text("x", encoding="utf-8")
    c = DiscoveryCache(blocker / "sub" / "c.json")
    c.set("a", 1.0, "h", [])
    with caplog.at_level(logging.WARNING, logger="aquilia.discovery"):
        c.save()  # must not raise, must not WARN
    assert [r for r in caplog.records if r.levelno >= logging.WARNING] == []
