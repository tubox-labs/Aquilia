"""Unit tests for the workspace file watcher path-filtering logic."""

from __future__ import annotations

from pathlib import Path

import pytest

from aquilia.devplatform.config import AquiliaDevelopmentConfig
from aquilia.devplatform.reload.watcher import WorkspaceWatcher


@pytest.fixture
def watcher(tmp_path, runtime):
    cfg = AquiliaDevelopmentConfig(port=8000, reload=True, reload_dirs=[tmp_path])
    return WorkspaceWatcher(cfg, runtime), tmp_path


class TestFiltering:
    def test_within_workspace_kept(self, watcher):
        w, root = watcher
        f = root / "controllers.py"
        f.write_text("x")
        assert w._filter_paths({f}) == {f.resolve()}

    def test_pycache_dropped(self, watcher):
        w, root = watcher
        f = root / "__pycache__" / "mod.cpython-311.pyc"
        f.parent.mkdir(parents=True)
        f.write_text("x")
        assert w._filter_paths({f}) == set()

    def test_pyc_dropped(self, watcher):
        w, root = watcher
        f = root / "mod.pyc"
        f.write_text("x")
        assert w._filter_paths({f}) == set()

    def test_outside_workspace_dropped(self, watcher, tmp_path_factory):
        w, root = watcher
        outside = tmp_path_factory.mktemp("outside") / "evil.py"
        outside.write_text("x")
        assert w._filter_paths({outside}) == set()

    def test_exclude_pattern(self, tmp_path, runtime):
        cfg = AquiliaDevelopmentConfig(port=8000, reload=True, reload_dirs=[tmp_path], reload_excludes=["*.log"])
        w = WorkspaceWatcher(cfg, runtime)
        f = tmp_path / "debug.log"
        f.write_text("x")
        assert w._filter_paths({f}) == set()

    def test_is_within_workspace(self, watcher):
        w, root = watcher
        assert w._is_within_workspace((root / "a.py").resolve())
        assert not w._is_within_workspace(Path("/tmp/definitely/outside/a.py"))


class TestNonSourceDropped:
    """Root fix for false reloads: only .py source survives the filter."""

    @pytest.mark.parametrize(
        "relpath",
        [
            ".aquilia/audit.surp",  # written by serving /admin/
            ".aquilia/discovery_cache.surp",  # written by discovery
            "app.db",
            "data.sqlite",
            "debug.log",
            "media/avatars/1.png",
            "notes.txt",
        ],
    )
    def test_non_python_dropped(self, watcher, relpath):
        w, root = watcher
        f = root / relpath
        f.parent.mkdir(parents=True, exist_ok=True)
        f.write_text("x")
        assert w._filter_paths({f}) == set()

    def test_admin_write_set_never_reloads(self, watcher):
        """Simulate the exact write set from opening /admin/ — no reload."""
        w, root = watcher
        audit = root / ".aquilia" / "audit.surp"
        audit.parent.mkdir(parents=True, exist_ok=True)
        audit.write_text("x")
        avatar = root / "media" / "avatars" / "u.png"
        avatar.parent.mkdir(parents=True, exist_ok=True)
        avatar.write_text("x")
        assert w._filter_paths({audit, avatar}) == set()

    def test_source_change_still_kept(self, watcher):
        w, root = watcher
        src = root / "controllers.py"
        src.write_text("x")
        assert w._filter_paths({src}) == {src.resolve()}
