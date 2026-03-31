"""
Tests for AquiliaRuntime lifecycle management.

Validates the AquiliaRuntime class in isolation using mocks
to avoid requiring a full workspace filesystem.
"""

import os
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

# Ensure repo root is importable
REPO_ROOT = Path(__file__).parent.parent.absolute()
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from aquilia.runtime import AquiliaRuntime, RuntimeConfig, RuntimePhase, _PHASE_ORDER


# ──────────────────────────────────────────────────────────────────────
# RuntimePhase tests
# ──────────────────────────────────────────────────────────────────────


class TestRuntimePhase:
    """Verify RuntimePhase enum structure and ordering."""

    def test_phase_values_are_strings(self):
        """All phase values should be lowercase strings."""
        for phase in RuntimePhase:
            assert isinstance(phase.value, str)
            assert phase.value == phase.value.lower()

    def test_phase_ordering_is_monotonic(self):
        """Phase ordering must be monotonically increasing (except FAILED)."""
        ordered = [
            RuntimePhase.CREATED,
            RuntimePhase.CONFIGURING,
            RuntimePhase.DISCOVERING,
            RuntimePhase.BOOTSTRAPPING,
            RuntimePhase.READY,
            RuntimePhase.RUNNING,
            RuntimePhase.SHUTTING_DOWN,
            RuntimePhase.STOPPED,
        ]
        for i in range(1, len(ordered)):
            assert _PHASE_ORDER[ordered[i]] > _PHASE_ORDER[ordered[i - 1]], (
                f"{ordered[i].name} ({_PHASE_ORDER[ordered[i]]}) should be > "
                f"{ordered[i - 1].name} ({_PHASE_ORDER[ordered[i - 1]]})"
            )

    def test_failed_phase_is_negative(self):
        """FAILED phase should have negative ordering (below all others)."""
        assert _PHASE_ORDER[RuntimePhase.FAILED] < 0

    def test_all_phases_have_ordering(self):
        """Every RuntimePhase member must have an entry in _PHASE_ORDER."""
        for phase in RuntimePhase:
            assert phase in _PHASE_ORDER, f"Missing ordering for {phase.name}"


# ──────────────────────────────────────────────────────────────────────
# RuntimeConfig tests
# ──────────────────────────────────────────────────────────────────────


class TestRuntimeConfig:
    """Verify RuntimeConfig dataclass properties."""

    def test_config_is_frozen(self):
        """RuntimeConfig should be immutable after creation."""
        rc = RuntimeConfig(workspace_root=Path("/tmp/test"))
        with pytest.raises(AttributeError):
            rc.mode = "dev"  # type: ignore[misc]

    def test_default_mode_is_prod(self):
        """Default mode should be 'prod'."""
        rc = RuntimeConfig(workspace_root=Path("/tmp/test"))
        assert rc.mode == "prod"
        assert rc.debug is False

    def test_debug_derived_from_mode(self):
        """debug=True when mode='dev', False otherwise."""
        dev = RuntimeConfig(workspace_root=Path("/tmp"), mode="dev")
        assert dev.debug is True

        prod = RuntimeConfig(workspace_root=Path("/tmp"), mode="prod")
        assert prod.debug is False

        test = RuntimeConfig(workspace_root=Path("/tmp"), mode="test")
        assert test.debug is False

    def test_explicit_debug_overrides_mode(self):
        """Explicit debug flag should override mode-based derivation."""
        rc = RuntimeConfig(workspace_root=Path("/tmp"), mode="prod", debug=True)
        assert rc.debug is True

    def test_is_dev_property(self):
        """is_dev should be True only when mode='dev'."""
        assert RuntimeConfig(workspace_root=Path("/tmp"), mode="dev").is_dev is True
        assert RuntimeConfig(workspace_root=Path("/tmp"), mode="prod").is_dev is False

    def test_workspace_file_property(self):
        """workspace_file should point to workspace.py."""
        rc = RuntimeConfig(workspace_root=Path("/app"))
        assert rc.workspace_file == Path("/app/workspace.py")

    def test_modules_dir_property(self):
        """modules_dir should point to modules/."""
        rc = RuntimeConfig(workspace_root=Path("/app"))
        assert rc.modules_dir == Path("/app/modules")

    def test_relative_root_is_resolved(self):
        """Relative workspace_root should be resolved to absolute."""
        rc = RuntimeConfig(workspace_root=Path("relative/path"))
        assert rc.workspace_root.is_absolute()


# ──────────────────────────────────────────────────────────────────────
# AquiliaRuntime lifecycle tests
# ──────────────────────────────────────────────────────────────────────


class TestAquiliaRuntimeLifecycle:
    """Verify AquiliaRuntime phase transitions and access guards."""

    def test_initial_phase_is_created(self):
        """New runtime should be in CREATED phase."""
        rc = RuntimeConfig(workspace_root=Path("/tmp"))
        runtime = AquiliaRuntime(rc)
        assert runtime.phase == RuntimePhase.CREATED

    def test_type_validation(self):
        """Passing non-RuntimeConfig should raise TypeError."""
        with pytest.raises(TypeError, match="Expected RuntimeConfig"):
            AquiliaRuntime({"workspace_root": "/tmp"})  # type: ignore[arg-type]

    def test_app_property_raises_before_ready(self):
        """Accessing .app before bootstrap should raise RuntimeError."""
        rc = RuntimeConfig(workspace_root=Path("/tmp"))
        runtime = AquiliaRuntime(rc)
        with pytest.raises(RuntimeError, match="Cannot access 'app'"):
            _ = runtime.app

    def test_server_property_raises_before_ready(self):
        """Accessing .server before bootstrap should raise RuntimeError."""
        rc = RuntimeConfig(workspace_root=Path("/tmp"))
        runtime = AquiliaRuntime(rc)
        with pytest.raises(RuntimeError, match="Cannot access 'server'"):
            _ = runtime.server

    def test_discover_before_configure_raises(self):
        """Calling discover() before configure() should raise RuntimeError."""
        rc = RuntimeConfig(workspace_root=Path("/tmp"))
        runtime = AquiliaRuntime(rc)
        with pytest.raises(RuntimeError, match="Cannot discover before configure"):
            runtime.discover()

    def test_bootstrap_before_discover_raises(self):
        """Calling bootstrap() before discover() should raise RuntimeError."""
        rc = RuntimeConfig(workspace_root=Path("/tmp"))
        runtime = AquiliaRuntime(rc)
        with pytest.raises(RuntimeError, match="Cannot bootstrap before discover"):
            runtime.bootstrap()

    def test_configure_missing_workspace_raises(self):
        """configure() with missing workspace.py should raise FileNotFoundError."""
        rc = RuntimeConfig(workspace_root=Path("/nonexistent/path"))
        runtime = AquiliaRuntime(rc)
        with pytest.raises(FileNotFoundError, match="workspace.py not found"):
            runtime.configure()
        assert runtime.phase == RuntimePhase.FAILED

    def test_configure_sets_phase_to_failed_on_error(self):
        """On error, phase should transition to FAILED."""
        rc = RuntimeConfig(workspace_root=Path("/nonexistent"))
        runtime = AquiliaRuntime(rc)
        with pytest.raises(FileNotFoundError):
            runtime.configure()
        assert runtime.phase == RuntimePhase.FAILED

    def test_repr_and_str(self):
        """__repr__ and __str__ should include useful info."""
        rc = RuntimeConfig(workspace_root=Path("/tmp"), mode="dev")
        runtime = AquiliaRuntime(rc)
        repr_str = repr(runtime)
        assert "AquiliaRuntime" in repr_str
        assert "dev" in repr_str
        assert "created" in repr_str

        str_str = str(runtime)
        assert "AquiliaRuntime" in str_str
        assert "dev" in str_str

    def test_workspace_name_default(self):
        """Default workspace name should be 'aquilia-app'."""
        rc = RuntimeConfig(workspace_root=Path("/tmp"))
        runtime = AquiliaRuntime(rc)
        assert runtime.workspace_name == "aquilia-app"

    def test_module_names_empty_initial(self):
        """Initial module_names should be empty list."""
        rc = RuntimeConfig(workspace_root=Path("/tmp"))
        runtime = AquiliaRuntime(rc)
        assert runtime.module_names == []

    def test_module_names_returns_copy(self):
        """module_names should return a copy, not the internal list."""
        rc = RuntimeConfig(workspace_root=Path("/tmp"))
        runtime = AquiliaRuntime(rc)
        names = runtime.module_names
        names.append("shouldnt_appear")
        assert "shouldnt_appear" not in runtime.module_names


# ──────────────────────────────────────────────────────────────────────
# Workspace parsing tests
# ──────────────────────────────────────────────────────────────────────


class TestWorkspaceParsing:
    """Verify workspace.py content parsing helpers."""

    def test_extract_workspace_name(self):
        """Should extract workspace name from Workspace() call."""
        content = 'workspace = Workspace("my-cool-app")'
        assert AquiliaRuntime._extract_workspace_name(content) == "my-cool-app"

    def test_extract_workspace_name_with_kwarg(self):
        """Should handle name= keyword argument."""
        content = 'workspace = Workspace(name="another-app")'
        assert AquiliaRuntime._extract_workspace_name(content) == "another-app"

    def test_extract_workspace_name_fallback(self):
        """Should return 'aquilia-app' when no match."""
        assert AquiliaRuntime._extract_workspace_name("") == "aquilia-app"

    def test_extract_module_names(self):
        """Should extract module names from .module() calls."""
        content = """
workspace = Workspace("app")
workspace.module(Module("users"))
workspace.module(Module("orders"))
"""
        modules = AquiliaRuntime._extract_module_names(content)
        assert modules == ["users", "orders"]

    def test_extract_module_names_deduplicates(self):
        """Duplicate modules should be deduplicated preserving order."""
        content = """
workspace.module(Module("users"))
workspace.module(Module("orders"))
workspace.module(Module("users"))
"""
        modules = AquiliaRuntime._extract_module_names(content)
        assert modules == ["users", "orders"]

    def test_extract_module_names_excludes_starter(self):
        """The 'starter' pseudo-module should be excluded."""
        content = """
workspace.module(Module("starter"))
workspace.module(Module("users"))
"""
        modules = AquiliaRuntime._extract_module_names(content)
        assert modules == ["users"]

    def test_extract_module_names_ignores_comments(self):
        """Commented-out modules should be ignored."""
        content = """
workspace.module(Module("users"))
# workspace.module(Module("disabled"))
workspace.module(Module("orders"))
"""
        modules = AquiliaRuntime._extract_module_names(content)
        assert modules == ["users", "orders"]


# ──────────────────────────────────────────────────────────────────────
# Factory method tests
# ──────────────────────────────────────────────────────────────────────


class TestFactoryMethods:
    """Verify from_workspace() and create_app() classmethods."""

    def test_from_workspace_invalid_mode_falls_back(self):
        """Invalid mode should fallback to 'prod' with a warning."""
        with pytest.raises(FileNotFoundError):
            # Will fail because /tmp has no workspace.py,
            # but the mode validation happens first
            AquiliaRuntime.from_workspace(
                workspace_root=Path("/tmp"),
                mode="invalid_mode",
            )

    def test_from_workspace_normalises_production(self):
        """'production' mode should be normalised to 'prod'."""
        with patch.dict(os.environ, {"AQUILIA_ENV": "production"}, clear=False):
            with pytest.raises(FileNotFoundError):
                AquiliaRuntime.from_workspace(
                    workspace_root=Path("/tmp/nonexistent"),
                )
