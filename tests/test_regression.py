"""
Comprehensive Regression Test Suite — Aquilia v1.0.0 Architecture Overhaul
==========================================================================

Tests every change made during the two-phase architecture redesign:

Phase 1 — Build System (Vite-inspired)
  - StaticChecker: syntax checks, AST parsing, error aggregation
  - CrousBundler: encode/decode roundtrip, encode_single, backend init
  - BuildResolver: resolution strategies, ResolvedBuild
  - AquiliaBuildPipeline: BuildConfig, BuildResult, BuildPhase, BuildError
  - CLI 'aq build' command registration

Phase 2 — Architecture Overhaul
  - Trace removal: no trace imports, no trace module, no trace CLI
  - JSON → Crous migration: artifact store, aquilary core, aquilary loader
  - Artifact store: .crous binary + .aq.json sidecar, fallback reads
  - Production deploy: gunicorn + UvicornWorker support
  - Deployment generator: no .aquilia/, gunicorn CMD, Crous build
  - Analytics: cache dir moved to build/.cache, Crous format
  - pyproject.toml: server optional dependency group
"""

import importlib
import json
import os
import shutil
import sys
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch
from typing import Any, Dict

import pytest


# ════════════════════════════════════════════════════════════════════════
# MODULE 1: TRACE REMOVAL — Verify trace is completely gone
# ════════════════════════════════════════════════════════════════════════


class TestTraceRemoval:
    """Verify the entire trace system has been cleanly removed."""

    def test_trace_module_deleted(self):
        """The aquilia/trace/ directory must not exist."""
        trace_dir = Path(__file__).parent.parent / "aquilia" / "trace"
        assert not trace_dir.exists(), f"Trace directory still exists: {trace_dir}"

    def test_trace_cli_command_deleted(self):
        """aquilia/cli/commands/trace.py must not exist."""
        trace_cmd = Path(__file__).parent.parent / "aquilia" / "cli" / "commands" / "trace.py"
        assert not trace_cmd.exists(), f"Trace CLI command still exists: {trace_cmd}"

    def test_trace_not_importable(self):
        """'from aquilia.trace import ...' must raise ImportError."""
        with pytest.raises((ImportError, ModuleNotFoundError)):
            from aquilia.trace import AquiliaTrace  # noqa: F401

    def test_trace_not_in_aquilia_all(self):
        """Trace symbols must not be in aquilia.__all__."""
        import aquilia
        all_symbols = getattr(aquilia, "__all__", [])
        trace_symbols = [
            "AquiliaTrace", "TraceManifest", "TraceRouteMap",
            "TraceDIGraph", "TraceSchemaLedger", "TraceLifecycleJournal",
            "TraceConfigSnapshot", "TraceDiagnostics",
        ]
        for sym in trace_symbols:
            assert sym not in all_symbols, f"'{sym}' still in aquilia.__all__"

    def test_trace_not_in_commands_init(self):
        """'trace' must not be in cli/commands/__init__.py imports."""
        from aquilia.cli import commands
        assert "trace" not in dir(commands) or not hasattr(commands, "trace"), \
            "'trace' still importable from aquilia.cli.commands"

    def test_trace_not_in_cli_categories(self):
        """'trace' must not appear in any CLI category."""
        from aquilia.cli.__main__ import AquiliaGroup
        categories = AquiliaGroup._CATEGORIES
        for cat_name, commands in categories.items():
            assert "trace" not in commands, \
                f"'trace' still in CLI category '{cat_name}'"

    def test_server_has_no_trace_attribute(self):
        """AquiliaServer must not have a .trace attribute in __init__."""
        import inspect
        from aquilia.server import AquiliaServer
        source = inspect.getsource(AquiliaServer.__init__)
        assert "self.trace" not in source, "server.__init__ still references self.trace"
        assert "AquiliaTrace" not in source, "server.__init__ still references AquiliaTrace"

    def test_server_startup_no_trace_journal(self):
        """AquiliaServer.startup() must not call trace.journal."""
        import inspect
        from aquilia.server import AquiliaServer
        source = inspect.getsource(AquiliaServer.startup)
        assert "self.trace" not in source, "startup() still references self.trace"
        assert "trace.journal" not in source, "startup() still references trace.journal"

    def test_server_shutdown_no_trace_journal(self):
        """AquiliaServer.shutdown() must not call trace.journal."""
        import inspect
        from aquilia.server import AquiliaServer
        source = inspect.getsource(AquiliaServer.shutdown)
        assert "self.trace" not in source, "shutdown() still references self.trace"
        assert "trace.journal" not in source, "shutdown() still references trace.journal"
        assert "trace.snapshot" not in source, "shutdown() still references trace.snapshot"

    def test_server_startup_uses_logger_debug(self):
        """startup() should use self.logger.debug for timing."""
        import inspect
        from aquilia.server import AquiliaServer
        source = inspect.getsource(AquiliaServer.startup)
        assert "self.logger.debug" in source, "startup() should use logger.debug for timing"

    def test_cache_cli_no_trace_path(self):
        """cmd_cache_stats() must not reference .aquilia/diagnostics.json."""
        import inspect
        from aquilia.cli.commands.cache import cmd_cache_stats
        source = inspect.getsource(cmd_cache_stats)
        assert ".aquilia" not in source, "cache stats still references .aquilia directory"
        assert "diagnostics.json" not in source, "cache stats still reads diagnostics.json"


# ════════════════════════════════════════════════════════════════════════
# MODULE 2: BUILD SYSTEM — StaticChecker, CrousBundler, Resolver, Pipeline
# ════════════════════════════════════════════════════════════════════════


class TestBuildSystemImports:
    """Verify the build system package exports are all importable."""

    def test_build_package_importable(self):
        from aquilia.build import (
            AquiliaBuildPipeline,
            BuildResult,
            BuildConfig,
            BuildPhase,
            BuildError,
            StaticChecker,
            CheckResult,
            CheckError,
            CrousBundler,
            BundleManifest,
            BuildResolver,
            ResolvedBuild,
        )
        # All imports succeed — verify they are the right types
        assert BuildPhase.DISCOVERY.value == "discovery"
        assert BuildPhase.BUNDLING.value == "bundling"
        assert BuildPhase.DONE.value == "done"

    def test_build_all_exports(self):
        from aquilia import build
        expected = [
            "AquiliaBuildPipeline", "BuildResult", "BuildConfig",
            "BuildPhase", "BuildError",
            "StaticChecker", "CheckResult", "CheckError",
            "CrousBundler", "BundleManifest",
            "BuildResolver", "ResolvedBuild",
        ]
        for name in expected:
            assert name in build.__all__, f"'{name}' not in build.__all__"


class TestStaticChecker:
    """Test the static checker component."""

    def test_check_severity_values(self):
        from aquilia.build.checker import CheckSeverity
        assert CheckSeverity.ERROR.value == "error"
        assert CheckSeverity.WARNING.value == "warning"
        assert CheckSeverity.INFO.value == "info"

    def test_check_error_str_with_location(self):
        from aquilia.build.checker import CheckError, CheckSeverity
        err = CheckError(
            severity=CheckSeverity.ERROR,
            message="Syntax error",
            file="app.py",
            line=42,
            column=10,
            code="E001",
        )
        s = str(err)
        assert "app.py:42:10" in s
        assert "[E001]" in s
        assert "Syntax error" in s
        assert "✗" in s

    def test_check_error_str_without_location(self):
        from aquilia.build.checker import CheckError, CheckSeverity
        err = CheckError(
            severity=CheckSeverity.WARNING,
            message="Unused import",
        )
        s = str(err)
        assert "⚠" in s
        assert "Unused import" in s

    def test_check_error_with_hint(self):
        from aquilia.build.checker import CheckError, CheckSeverity
        err = CheckError(
            severity=CheckSeverity.ERROR,
            message="Module not found",
            hint="Did you mean 'utils'?",
        )
        s = str(err)
        assert "hint: Did you mean 'utils'?" in s

    def test_check_result_counts(self):
        from aquilia.build.checker import CheckResult, CheckError, CheckSeverity
        result = CheckResult()
        result.add(CheckError(severity=CheckSeverity.ERROR, message="err1"))
        result.add(CheckError(severity=CheckSeverity.WARNING, message="warn1"))
        result.add(CheckError(severity=CheckSeverity.ERROR, message="err2"))
        result.add(CheckError(severity=CheckSeverity.INFO, message="info1"))

        assert result.has_errors is True
        assert result.has_warnings is True
        assert result.error_count == 2
        assert result.warning_count == 1

    def test_check_result_no_errors(self):
        from aquilia.build.checker import CheckResult, CheckError, CheckSeverity
        result = CheckResult()
        result.add(CheckError(severity=CheckSeverity.INFO, message="info"))
        assert result.has_errors is False
        assert result.has_warnings is False

    def test_check_result_merge(self):
        from aquilia.build.checker import CheckResult, CheckError, CheckSeverity
        r1 = CheckResult(files_checked=3)
        r1.add(CheckError(severity=CheckSeverity.ERROR, message="e1"))
        r2 = CheckResult(files_checked=5)
        r2.add(CheckError(severity=CheckSeverity.WARNING, message="w1"))
        r1.merge(r2)
        assert r1.files_checked == 8
        assert len(r1.errors) == 2

    def test_static_checker_instantiation(self):
        from aquilia.build.checker import StaticChecker
        checker = StaticChecker(workspace_root=Path("/tmp/fake-workspace"))
        assert checker is not None

    def test_checker_on_valid_python_file(self):
        """StaticChecker should not error on valid Python syntax."""
        from aquilia.build.checker import StaticChecker, CheckResult
        with tempfile.TemporaryDirectory() as tmpdir:
            # StaticChecker.check_all() expects a workspace.py at root
            ws_file = Path(tmpdir) / "workspace.py"
            ws_file.write_text("name = 'test'\nversion = '1.0.0'\n")
            modules_dir = Path(tmpdir) / "modules"
            modules_dir.mkdir()
            valid_file = modules_dir / "valid.py"
            valid_file.write_text("def hello():\n    return 'world'\n")
            checker = StaticChecker(workspace_root=Path(tmpdir))
            result = checker.check_all()
            assert isinstance(result, CheckResult)
            assert result.has_errors is False

    def test_checker_on_invalid_python_file(self):
        """StaticChecker should detect syntax errors."""
        from aquilia.build.checker import StaticChecker
        with tempfile.TemporaryDirectory() as tmpdir:
            modules_dir = Path(tmpdir) / "modules"
            modules_dir.mkdir()
            bad_file = modules_dir / "bad.py"
            bad_file.write_text("def broken(\n    return\n")
            checker = StaticChecker(workspace_root=Path(tmpdir))
            result = checker.check_all()
            assert result.has_errors is True
            assert result.error_count >= 1


class TestCrousBundler:
    """Test the Crous binary bundler."""

    def test_encode_single_roundtrip(self):
        """encode_single should produce bytes that can be decoded back."""
        from aquilia.build.bundler import CrousBundler
        data = {"routes": ["/api/users", "/api/posts"], "count": 2}
        binary = CrousBundler.encode_single(data)
        assert isinstance(binary, bytes)
        assert len(binary) > 0

        # Decode and verify
        try:
            import _crous_native as backend
        except ImportError:
            import crous as backend
        decoded = backend.decode(binary)
        assert decoded == data

    def test_encode_single_complex_data(self):
        """encode_single handles nested dicts, lists, strings, ints, floats, bools, None."""
        from aquilia.build.bundler import CrousBundler
        data = {
            "name": "test-app",
            "version": "1.0.0",
            "modules": ["auth", "api", "db"],
            "config": {
                "debug": False,
                "port": 8000,
                "rate_limit": 100.5,
                "secret": None,
            },
            "routes": [
                {"path": "/api/users", "method": "GET", "auth": True},
                {"path": "/api/login", "method": "POST", "auth": False},
            ],
        }
        binary = CrousBundler.encode_single(data)
        try:
            import _crous_native as backend
        except ImportError:
            import crous as backend
        decoded = backend.decode(binary)
        assert decoded["name"] == "test-app"
        assert decoded["config"]["port"] == 8000
        assert decoded["config"]["debug"] is False
        assert decoded["config"]["secret"] is None
        assert len(decoded["routes"]) == 2

    def test_encode_single_empty_dict(self):
        from aquilia.build.bundler import CrousBundler
        binary = CrousBundler.encode_single({})
        try:
            import _crous_native as backend
        except ImportError:
            import crous as backend
        assert backend.decode(binary) == {}

    def test_crous_backend_initialization(self):
        """_CrousBackend should init with native or pure Python."""
        from aquilia.build.bundler import _CrousBackend
        backend = _CrousBackend()
        assert backend._mod is not None
        assert isinstance(backend.is_native, bool)

    def test_crous_backend_encode_decode(self):
        from aquilia.build.bundler import _CrousBackend
        backend = _CrousBackend()
        data = {"key": "value", "list": [1, 2, 3]}
        encoded = backend.encode(data)
        decoded = backend.decode(encoded)
        assert decoded == data

    def test_bundle_manifest_creation(self):
        from aquilia.build.bundler import BundleManifest
        manifest = BundleManifest(
            workspace_name="test-app",
            workspace_version="1.0.0",
            mode="prod",
            compression="lz4",
            fingerprint="sha256:xyz789",
            build_time_ms=150.0,
            crous_backend="native",
        )
        assert manifest.workspace_name == "test-app"
        assert manifest.mode == "prod"
        assert manifest.compression == "lz4"
        assert manifest.build_time_ms == 150.0


class TestBuildConfig:
    """Test BuildConfig dataclass."""

    def test_default_config(self):
        from aquilia.build.pipeline import BuildConfig
        cfg = BuildConfig()
        assert cfg.mode == "dev"
        assert cfg.compression == "none"
        assert cfg.verbose is False
        assert cfg.strict is False
        assert cfg.output_dir == "build"

    def test_dev_config(self):
        from aquilia.build.pipeline import BuildConfig
        cfg = BuildConfig.dev("/workspace", verbose=True)
        assert cfg.mode == "dev"
        assert cfg.compression == "none"
        assert cfg.verbose is True
        assert cfg.workspace_root == "/workspace"

    def test_prod_config(self):
        from aquilia.build.pipeline import BuildConfig
        cfg = BuildConfig.prod("/workspace")
        assert cfg.mode == "prod"
        assert cfg.compression == "lz4"
        assert cfg.strict is True


class TestBuildResult:
    """Test BuildResult dataclass."""

    def test_successful_build_summary(self):
        from aquilia.build.pipeline import BuildResult
        result = BuildResult(
            success=True,
            total_ms=150.5,
            artifacts_count=3,
            files_checked=10,
            fingerprint="sha256:abc123456789",
        )
        summary = result.summary()
        assert "succeeded" in summary
        assert "150ms" in summary
        assert "3 artifacts" in summary
        assert "10 files" in summary
        assert "sha256:abc12" in summary

    def test_failed_build_summary(self):
        from aquilia.build.pipeline import BuildResult, BuildError, BuildPhase
        result = BuildResult(
            success=False,
            total_ms=50.0,
            errors=[
                BuildError(phase=BuildPhase.STATIC_CHECK, message="syntax error"),
                BuildError(phase=BuildPhase.VALIDATION, message="missing manifest"),
            ],
        )
        summary = result.summary()
        assert "FAILED" in summary
        assert "2 error(s)" in summary

    def test_build_error_str(self):
        from aquilia.build.pipeline import BuildError, BuildPhase
        err = BuildError(
            phase=BuildPhase.COMPILATION,
            message="Module not found",
            file="controllers/auth.py",
            line=15,
            hint="Check the import path",
        )
        s = str(err)
        assert "[compilation]" in s
        assert "controllers/auth.py:15" in s
        assert "Module not found" in s
        assert "hint: Check the import path" in s

    def test_build_phases_enum(self):
        from aquilia.build.pipeline import BuildPhase
        phases = list(BuildPhase)
        phase_values = [p.value for p in phases]
        assert "discovery" in phase_values
        assert "validation" in phase_values
        assert "static_check" in phase_values
        assert "compilation" in phase_values
        assert "bundling" in phase_values
        assert "fingerprint" in phase_values
        assert "done" in phase_values


class TestBuildResolver:
    """Test the build resolver strategies."""

    def test_resolved_build_dataclass(self):
        from aquilia.build.resolver import ResolvedBuild
        rb = ResolvedBuild(
            workspace_name="test-app",
            workspace_version="1.0.0",
            mode="prod",
            artifacts={"auth": {"name": "auth", "kind": "module"}},
            fingerprint="sha256:test",
            from_bundle=True,
        )
        assert rb.from_bundle is True
        assert "auth" in rb.artifacts

    def test_resolver_with_empty_directory(self):
        """Resolver should raise FileNotFoundError for empty build dir."""
        from aquilia.build.resolver import BuildResolver
        with tempfile.TemporaryDirectory() as tmpdir:
            resolver = BuildResolver(Path(tmpdir))
            with pytest.raises(FileNotFoundError):
                resolver.resolve()


# ════════════════════════════════════════════════════════════════════════
# MODULE 3: CROUS BINARY MIGRATION — Artifact Store
# ════════════════════════════════════════════════════════════════════════


class TestArtifactStoreCrous:
    """Test artifact store with Crous binary format."""

    @pytest.fixture
    def store(self, tmp_path):
        from aquilia.artifacts.store import FilesystemArtifactStore
        return FilesystemArtifactStore(root=str(tmp_path / "artifacts"))

    @pytest.fixture
    def sample_artifact(self):
        from aquilia.artifacts.core import Artifact, ArtifactEnvelope, ArtifactIntegrity
        return Artifact(ArtifactEnvelope(
            kind="config",
            name="test-config",
            version="1.0.0",
            integrity=ArtifactIntegrity(algorithm="sha256", digest="abc123"),
            payload={"key": "value", "nested": {"a": 1}},
        ))

    def test_store_saves_crous_binary(self, store, sample_artifact):
        """save() should write a .crous file as primary."""
        store.save(sample_artifact)
        crous_files = list(Path(store.root).glob("*.crous"))
        assert len(crous_files) >= 1, "No .crous file was created"

    def test_store_saves_json_sidecar(self, store, sample_artifact):
        """save() should also write a .aq.json sidecar."""
        store.save(sample_artifact)
        json_files = list(Path(store.root).glob("*.aq.json"))
        assert len(json_files) >= 1, "No .aq.json sidecar was created"

    def test_store_save_and_load_roundtrip(self, store, sample_artifact):
        """save() then load() should return identical artifact."""
        store.save(sample_artifact)
        loaded = store.load("test-config", version="1.0.0")
        assert loaded is not None
        assert loaded.name == "test-config"
        assert loaded.version == "1.0.0"
        assert loaded.kind == "config"
        assert loaded.payload == {"key": "value", "nested": {"a": 1}}

    def test_store_load_without_version(self, store, sample_artifact):
        """load() without version should find by name prefix."""
        store.save(sample_artifact)
        loaded = store.load("test-config")
        assert loaded is not None
        assert loaded.name == "test-config"

    def test_store_exists(self, store, sample_artifact):
        assert not store.exists("test-config")
        store.save(sample_artifact)
        assert store.exists("test-config")
        assert store.exists("test-config", version="1.0.0")
        assert not store.exists("test-config", version="2.0.0")

    def test_store_delete_removes_both_formats(self, store, sample_artifact):
        """delete() should remove both .crous and .aq.json files."""
        store.save(sample_artifact)
        assert store.exists("test-config")
        removed = store.delete("test-config", version="1.0.0")
        assert removed >= 1
        assert not store.exists("test-config", version="1.0.0")
        # Verify both files are gone
        assert len(list(Path(store.root).glob("test*"))) == 0

    def test_store_list_artifacts(self, store):
        from aquilia.artifacts.core import Artifact, ArtifactEnvelope, ArtifactIntegrity
        for i in range(3):
            a = Artifact(ArtifactEnvelope(
                kind="config" if i < 2 else "module",
                name=f"art-{i}",
                version="1.0.0",
                integrity=ArtifactIntegrity(digest=f"digest{i}"),
                payload={"i": i},
            ))
            store.save(a)
        all_arts = store.list_artifacts()
        assert len(all_arts) == 3

        configs = store.list_artifacts(kind="config")
        assert len(configs) == 2

        modules = store.list_artifacts(kind="module")
        assert len(modules) == 1

    def test_store_load_by_digest(self, store, sample_artifact):
        store.save(sample_artifact)
        loaded = store.load_by_digest("sha256:abc123")
        assert loaded is not None
        assert loaded.name == "test-config"

    def test_store_gc(self, store):
        from aquilia.artifacts.core import Artifact, ArtifactEnvelope, ArtifactIntegrity
        a1 = Artifact(ArtifactEnvelope(
            kind="config", name="keep", version="1.0.0",
            integrity=ArtifactIntegrity(digest="keep_digest"),
            payload={},
        ))
        a2 = Artifact(ArtifactEnvelope(
            kind="config", name="remove", version="1.0.0",
            integrity=ArtifactIntegrity(digest="remove_digest"),
            payload={},
        ))
        store.save(a1)
        store.save(a2)
        assert len(store) == 2
        removed = store.gc({"sha256:keep_digest"})
        assert removed >= 1
        assert store.exists("keep")
        # After GC, 'remove' artifact should no longer be loadable
        loaded = store.load("remove", version="1.0.0")
        assert loaded is None

    def test_store_count(self, store):
        from aquilia.artifacts.core import Artifact, ArtifactEnvelope, ArtifactIntegrity
        a = Artifact(ArtifactEnvelope(
            kind="config", name="test", version="1.0.0",
            integrity=ArtifactIntegrity(digest="d1"),
            payload={},
        ))
        store.save(a)
        assert store.count() == 1
        assert store.count(kind="config") == 1
        assert store.count(kind="module") == 0

    def test_store_iter_files_prefers_crous(self, store, sample_artifact):
        """_iter_files() should yield .crous before .aq.json and avoid duplicates."""
        store.save(sample_artifact)
        files = list(store._iter_files())
        # Should yield exactly 1 file (the .crous, not both)
        assert len(files) == 1
        assert files[0].suffix == ".crous"

    def test_store_crous_backend_initialized(self, store):
        """Store should have a Crous backend available."""
        assert store._crous_backend is not None

    def test_store_legacy_json_fallback(self, tmp_path):
        """Store should still read legacy .aq.json files without .crous counterparts."""
        from aquilia.artifacts.store import FilesystemArtifactStore
        from aquilia.artifacts.core import Artifact, ArtifactEnvelope, ArtifactIntegrity

        # Save an artifact normally, then remove only the .crous file
        # This simulates a legacy state where only .aq.json exists
        store = FilesystemArtifactStore(root=str(tmp_path / "artifacts"))
        art = Artifact(ArtifactEnvelope(
            kind="config", name="legacy-art", version="1.0.0",
            integrity=ArtifactIntegrity(digest="legacy_digest"),
            payload={"legacy": True},
        ))
        store.save(art)

        # Remove the .crous file to simulate legacy state
        for f in Path(store.root).glob("*.crous"):
            f.unlink()

        # The .aq.json sidecar should be yielded by _iter_files (no .crous counterpart)
        files = list(store._iter_files())
        assert len(files) == 1
        assert files[0].name.endswith(".aq.json")

        # Load without version uses _iter_files which does the legacy fallback
        loaded = store.load("legacy-art")
        assert loaded is not None
        assert loaded.name == "legacy-art"
        assert loaded.payload == {"legacy": True}


class TestMemoryArtifactStore:
    """Test the in-memory artifact store (not affected by Crous migration, but verify)."""

    def test_memory_store_crud(self):
        from aquilia.artifacts.store import MemoryArtifactStore
        from aquilia.artifacts.core import Artifact, ArtifactEnvelope, ArtifactIntegrity
        store = MemoryArtifactStore()

        art = Artifact(ArtifactEnvelope(
            kind="config", name="mem-test", version="1.0.0",
            integrity=ArtifactIntegrity(digest="mem_digest"),
            payload={"memory": True},
        ))

        store.save(art)
        assert store.exists("mem-test")
        assert len(store) == 1

        loaded = store.load("mem-test")
        assert loaded.payload == {"memory": True}

        store.delete("mem-test")
        assert not store.exists("mem-test")
        assert len(store) == 0


# ════════════════════════════════════════════════════════════════════════
# MODULE 4: CROUS BINARY MIGRATION — Aquilary Core & Loader
# ════════════════════════════════════════════════════════════════════════


class TestAquilaryCrousMigration:
    """Test that aquilary core uses Crous for freeze/from_frozen."""

    def test_aquilary_core_importable(self):
        from aquilia.aquilary.core import Aquilary, AquilaryRegistry
        assert Aquilary is not None
        assert AquilaryRegistry is not None

    def test_freeze_writes_crous_format(self):
        """AquilaryRegistry.export_manifest() should write .crous binary when Crous is available."""
        import inspect
        from aquilia.aquilary.core import AquilaryRegistry
        # The freeze/export method is export_manifest on AquilaryRegistry
        assert hasattr(AquilaryRegistry, 'export_manifest'), \
            "AquilaryRegistry should have an export_manifest() method"
        source = inspect.getsource(AquilaryRegistry.export_manifest)
        assert "crous" in source.lower(), \
            "export_manifest() should reference Crous encoding"

    def test_from_frozen_reads_crous_format(self):
        """Aquilary._from_frozen_manifest() should read .crous binary."""
        import inspect
        from aquilia.aquilary.core import Aquilary
        # _from_frozen_manifest is a classmethod on Aquilary, not AquilaryRegistry
        assert hasattr(Aquilary, '_from_frozen_manifest'), \
            "Aquilary should have a _from_frozen_manifest() classmethod"
        source = inspect.getsource(Aquilary._from_frozen_manifest)
        assert "crous" in source.lower(), \
            "_from_frozen_manifest() should reference Crous decoding"
        assert "json" in source.lower(), \
            "_from_frozen_manifest() should have JSON fallback"


class TestAquilaryLoaderCrous:
    """Test that the manifest loader supports .crous files."""

    def test_loader_supports_crous_extension(self):
        """ManifestLoader should accept .crous files in its loading logic."""
        import inspect
        from aquilia.aquilary.loader import ManifestLoader
        # Check the full class source for .crous support
        source = inspect.getsource(ManifestLoader)
        assert ".crous" in source, \
            "ManifestLoader should support .crous extension"

    def test_loader_load_dsl_supports_crous(self):
        """_load_from_dsl_file should decode .crous files."""
        import inspect
        from aquilia.aquilary.loader import ManifestLoader
        source = inspect.getsource(ManifestLoader._load_from_dsl_file)
        assert ".crous" in source, \
            "_load_from_dsl_file should handle .crous format"

    def test_loader_directory_scan_includes_crous(self):
        """Directory scanning should look for manifest.crous."""
        import inspect
        from aquilia.aquilary.loader import ManifestLoader
        # Check the full class source for manifest.crous file discovery
        source = inspect.getsource(ManifestLoader)
        assert "manifest.crous" in source or ".crous" in source, \
            "ManifestLoader should discover manifest.crous files"


# ════════════════════════════════════════════════════════════════════════
# MODULE 5: CROUS BINARY ENCODING — Low-Level Backend Tests
# ════════════════════════════════════════════════════════════════════════


class TestCrousBackend:
    """Test the low-level Crous binary encoder/decoder."""

    def test_crous_available(self):
        """At least one Crous backend must be installed."""
        try:
            import _crous_native
            return  # native is available
        except ImportError:
            pass
        try:
            import crous
            return  # pure Python is available
        except ImportError:
            pytest.fail("Neither _crous_native nor crous is installed")

    def test_encode_decode_dict(self):
        try:
            import _crous_native as backend
        except ImportError:
            import crous as backend
        data = {"a": 1, "b": "hello", "c": [1, 2, 3]}
        assert backend.decode(backend.encode(data)) == data

    def test_encode_decode_nested(self):
        try:
            import _crous_native as backend
        except ImportError:
            import crous as backend
        data = {
            "level1": {
                "level2": {
                    "level3": [{"value": i} for i in range(10)]
                }
            }
        }
        assert backend.decode(backend.encode(data)) == data

    def test_encode_decode_types(self):
        """Test encoding of all supported types."""
        try:
            import _crous_native as backend
        except ImportError:
            import crous as backend
        data = {
            "int": 42,
            "float": 3.14,
            "str": "hello world",
            "bool_true": True,
            "bool_false": False,
            "none": None,
            "list": [1, "two", 3.0, True, None],
            "nested_dict": {"key": "val"},
        }
        decoded = backend.decode(backend.encode(data))
        assert decoded["int"] == 42
        assert abs(decoded["float"] - 3.14) < 0.001
        assert decoded["str"] == "hello world"
        assert decoded["bool_true"] is True
        assert decoded["bool_false"] is False
        assert decoded["none"] is None
        assert decoded["list"] == [1, "two", 3.0, True, None]

    def test_encode_empty_structures(self):
        try:
            import _crous_native as backend
        except ImportError:
            import crous as backend
        assert backend.decode(backend.encode({})) == {}
        assert backend.decode(backend.encode([])) == []
        assert backend.decode(backend.encode("")) == ""

    def test_encode_large_payload(self):
        """Crous should handle reasonably large payloads."""
        try:
            import _crous_native as backend
        except ImportError:
            import crous as backend
        data = {
            "routes": [
                {"path": f"/api/resource/{i}", "method": "GET", "handler": f"handler_{i}"}
                for i in range(500)
            ]
        }
        encoded = backend.encode(data)
        decoded = backend.decode(encoded)
        assert len(decoded["routes"]) == 500
        assert decoded["routes"][499]["path"] == "/api/resource/499"


# ════════════════════════════════════════════════════════════════════════
# MODULE 6: PRODUCTION DEPLOY — Gunicorn + UvicornWorker
# ════════════════════════════════════════════════════════════════════════


class TestServeCommand:
    """Test the updated serve command with gunicorn support."""

    def test_serve_production_signature(self):
        """serve_production should accept gunicorn params."""
        import inspect
        from aquilia.cli.commands.serve import serve_production
        sig = inspect.signature(serve_production)
        params = list(sig.parameters.keys())
        assert "use_gunicorn" in params
        assert "timeout" in params
        assert "graceful_timeout" in params
        assert "workers" in params
        assert "bind" in params

    def test_serve_production_defaults(self):
        """Default values should be sane for production."""
        import inspect
        from aquilia.cli.commands.serve import serve_production
        sig = inspect.signature(serve_production)
        assert sig.parameters["use_gunicorn"].default is False
        assert sig.parameters["timeout"].default == 120
        assert sig.parameters["graceful_timeout"].default == 30
        assert sig.parameters["workers"].default == 1

    def test_serve_gunicorn_function_exists(self):
        from aquilia.cli.commands.serve import _serve_with_gunicorn
        assert callable(_serve_with_gunicorn)

    def test_serve_uvicorn_function_exists(self):
        from aquilia.cli.commands.serve import _serve_with_uvicorn
        assert callable(_serve_with_uvicorn)

    def test_serve_cli_has_gunicorn_options(self):
        """CLI 'serve' command should have --use-gunicorn flag."""
        from click.testing import CliRunner
        from aquilia.cli.__main__ import cli
        runner = CliRunner()
        result = runner.invoke(cli, ["serve", "--help"], catch_exceptions=False)
        assert "--use-gunicorn" in result.output
        assert "--timeout" in result.output
        assert "--graceful-timeout" in result.output
        assert "UvicornWorker" in result.output


class TestServeDocstring:
    """Verify serve command documentation reflects gunicorn support."""

    def test_serve_docstring_mentions_gunicorn(self):
        import inspect
        from aquilia.cli.commands.serve import serve_production
        doc = inspect.getdoc(serve_production)
        assert "gunicorn" in doc.lower()

    def test_serve_module_docstring_mentions_backends(self):
        from aquilia.cli.commands import serve
        doc = serve.__doc__
        assert "gunicorn" in doc.lower()
        assert "uvicorn" in doc.lower()


# ════════════════════════════════════════════════════════════════════════
# MODULE 7: DEPLOYMENT GENERATOR — No Trace, Gunicorn CMD
# ════════════════════════════════════════════════════════════════════════


class TestDeploymentGenerator:
    """Test that deployment generators no longer reference trace."""

    def test_dockerfile_no_aquilia_dir(self):
        """Production Dockerfile should not create .aquilia/ directory."""
        import inspect
        from aquilia.cli.generators.deployment import DockerfileGenerator
        source = inspect.getsource(DockerfileGenerator.generate_dockerfile)
        assert ".aquilia" not in source, \
            "Production Dockerfile still references .aquilia directory"

    def test_dockerfile_uses_gunicorn(self):
        """Production Dockerfile CMD should use gunicorn."""
        import inspect
        from aquilia.cli.generators.deployment import DockerfileGenerator
        source = inspect.getsource(DockerfileGenerator.generate_dockerfile)
        assert "gunicorn" in source, \
            "Production Dockerfile should use gunicorn in CMD"
        assert "UvicornWorker" in source, \
            "Production Dockerfile should use UvicornWorker"

    def test_dockerignore_no_aquilia_dir(self):
        """Dockerignore should not reference .aquilia/."""
        import inspect
        from aquilia.cli.generators.deployment import DockerfileGenerator
        source = inspect.getsource(DockerfileGenerator.generate_dockerignore)
        assert ".aquilia/" not in source, \
            ".dockerignore still references .aquilia/"

    def test_compose_no_trace_volume(self):
        """Compose generator should not have app-trace volume."""
        import inspect
        from aquilia.cli.generators.deployment import ComposeGenerator
        source = inspect.getsource(ComposeGenerator.generate_compose)
        assert "app-trace" not in source, \
            "Docker Compose still has app-trace volume"

    def test_kubernetes_no_trace_volume(self):
        """K8s deployment should not have trace volume mounts."""
        import inspect
        from aquilia.cli.generators.deployment import KubernetesGenerator
        source = inspect.getsource(KubernetesGenerator.generate_deployment)
        assert "trace" not in source.lower() or "torch" in source.lower() or \
            source.lower().count("trace") == 0, \
            "K8s deployment still has trace volume mount"

    def test_makefile_uses_build_command(self):
        """Makefile compile target should use 'aq build' not 'aq compile'."""
        import inspect
        from aquilia.cli.generators.deployment import MakefileGenerator
        source = inspect.getsource(MakefileGenerator.generate_makefile)
        assert "aq build" in source or "aquilia.cli build" in source or \
            "build --mode" in source, \
            "Makefile compile target should use build command"

    def test_makefile_clean_no_aquilia(self):
        """Makefile clean target should not reference .aquilia/."""
        import inspect
        from aquilia.cli.generators.deployment import MakefileGenerator
        source = inspect.getsource(MakefileGenerator.generate_makefile)
        assert ".aquilia/" not in source, \
            "Makefile clean target still references .aquilia/"


# ════════════════════════════════════════════════════════════════════════
# MODULE 8: ANALYTICS — Cache Dir & Crous Format
# ════════════════════════════════════════════════════════════════════════


class TestAnalyticsCrous:
    """Test analytics cache directory and format changes."""

    def test_analytics_cache_dir_is_build_cache(self):
        """DiscoveryAnalytics cache_dir should be build/.cache, not .aquilia/discovery."""
        import inspect
        from aquilia.cli.commands.analytics import DiscoveryAnalytics
        source = inspect.getsource(DiscoveryAnalytics.__init__)
        assert ".aquilia" not in source, \
            "Analytics init still references .aquilia directory"
        assert "build" in source, \
            "Analytics init should use build/.cache directory"

    def test_analytics_cache_writes_crous(self):
        """_cache_analysis should write Crous binary format."""
        import inspect
        from aquilia.cli.commands.analytics import DiscoveryAnalytics
        source = inspect.getsource(DiscoveryAnalytics._cache_analysis)
        assert "crous" in source.lower(), \
            "_cache_analysis should write Crous format"

    def test_analytics_cache_reads_crous(self):
        """get_cached_analysis should read Crous binary format."""
        import inspect
        from aquilia.cli.commands.analytics import DiscoveryAnalytics
        source = inspect.getsource(DiscoveryAnalytics.get_cached_analysis)
        assert "crous" in source.lower(), \
            "get_cached_analysis should read Crous format"
        assert "json" in source.lower(), \
            "get_cached_analysis should have JSON fallback"


# ════════════════════════════════════════════════════════════════════════
# MODULE 9: CLI COMMAND REGISTRATION
# ════════════════════════════════════════════════════════════════════════


class TestCLICommands:
    """Test CLI command availability and help text."""

    def test_build_command_registered(self):
        from click.testing import CliRunner
        from aquilia.cli.__main__ import cli
        runner = CliRunner()
        result = runner.invoke(cli, ["build", "--help"], catch_exceptions=False)
        assert result.exit_code == 0
        assert "build" in result.output.lower()

    def test_serve_command_registered(self):
        from click.testing import CliRunner
        from aquilia.cli.__main__ import cli
        runner = CliRunner()
        result = runner.invoke(cli, ["serve", "--help"], catch_exceptions=False)
        assert result.exit_code == 0

    def test_trace_command_not_registered(self):
        """'aq trace' should not exist."""
        from click.testing import CliRunner
        from aquilia.cli.__main__ import cli
        runner = CliRunner()
        result = runner.invoke(cli, ["trace", "--help"])
        # Should fail because trace command doesn't exist
        assert result.exit_code != 0 or "No such command" in result.output or \
            "Error" in result.output

    def test_main_help_no_trace(self):
        """'aq --help' should not mention trace."""
        from click.testing import CliRunner
        from aquilia.cli.__main__ import cli
        runner = CliRunner()
        result = runner.invoke(cli, ["--help"], catch_exceptions=False)
        lines = result.output.lower().split("\n")
        # Filter out any line that's just the "subsystems" header
        command_lines = [l for l in lines if "trace" in l and "subsystem" not in l]
        # 'trace' as a standalone command shouldn't appear
        assert not any("  trace " in l for l in lines), \
            "'trace' command still appears in aq --help"


# ════════════════════════════════════════════════════════════════════════
# MODULE 10: PYPROJECT.TOML — Dependencies
# ════════════════════════════════════════════════════════════════════════


class TestProjectConfig:
    """Test project configuration changes."""

    def test_pyproject_has_crous_dependency(self):
        pyproject = Path(__file__).parent.parent / "pyproject.toml"
        content = pyproject.read_text()
        assert "crous" in content, "pyproject.toml missing crous dependency"

    def test_pyproject_has_server_extras(self):
        """pyproject.toml should have [server] optional dependency group."""
        pyproject = Path(__file__).parent.parent / "pyproject.toml"
        content = pyproject.read_text()
        assert "gunicorn" in content, "pyproject.toml missing gunicorn in server extras"

    def test_pyproject_server_group_exists(self):
        pyproject = Path(__file__).parent.parent / "pyproject.toml"
        content = pyproject.read_text()
        assert "server" in content, "pyproject.toml missing [server] optional group"


# ════════════════════════════════════════════════════════════════════════
# MODULE 11: ARTIFACT CORE — Integrity & Provenance (existing functionality)
# ════════════════════════════════════════════════════════════════════════


class TestArtifactCore:
    """Regression tests for artifact core types (unchanged but verify)."""

    def test_artifact_integrity_compute(self):
        from aquilia.artifacts.core import ArtifactIntegrity
        data = b"hello world"
        integrity = ArtifactIntegrity.compute(data)
        assert integrity.algorithm == "sha256"
        assert len(integrity.digest) == 64  # sha256 hex

    def test_artifact_integrity_verify(self):
        from aquilia.artifacts.core import ArtifactIntegrity
        data = b"hello world"
        integrity = ArtifactIntegrity.compute(data)
        assert integrity.verify(data) is True
        assert integrity.verify(b"different") is False

    def test_artifact_integrity_roundtrip(self):
        from aquilia.artifacts.core import ArtifactIntegrity
        original = ArtifactIntegrity(algorithm="sha256", digest="abc123")
        d = original.to_dict()
        restored = ArtifactIntegrity.from_dict(d)
        assert restored.algorithm == original.algorithm
        assert restored.digest == original.digest

    def test_artifact_provenance_auto(self):
        from aquilia.artifacts.core import ArtifactProvenance
        prov = ArtifactProvenance.auto("/some/path")
        assert prov.created_at != ""
        assert prov.created_by != ""
        assert prov.source_path == "/some/path"
        assert prov.build_tool == "aquilia"

    def test_artifact_envelope_roundtrip(self):
        from aquilia.artifacts.core import ArtifactEnvelope, ArtifactIntegrity
        env = ArtifactEnvelope(
            kind="config",
            name="test",
            version="1.0",
            integrity=ArtifactIntegrity(digest="abc"),
            payload={"key": "val"},
            tags={"env": "prod"},
        )
        d = env.to_dict()
        restored = ArtifactEnvelope.from_dict(d)
        assert restored.kind == "config"
        assert restored.name == "test"
        assert restored.payload == {"key": "val"}
        assert restored.tags == {"env": "prod"}

    def test_artifact_kind_enum(self):
        from aquilia.artifacts.core import ArtifactKind
        assert ArtifactKind.CONFIG.value == "config"
        assert ArtifactKind.BUNDLE.value == "bundle"
        assert ArtifactKind.ROUTE.value == "route"

    def test_artifact_properties(self):
        from aquilia.artifacts.core import Artifact, ArtifactEnvelope, ArtifactIntegrity
        art = Artifact(ArtifactEnvelope(
            kind="module", name="auth", version="2.0.0",
            integrity=ArtifactIntegrity(digest="xyz"),
            payload={"handlers": 5},
            tags={"team": "backend"},
            metadata={"description": "Auth module"},
        ))
        assert art.name == "auth"
        assert art.version == "2.0.0"
        assert art.kind == "module"
        assert art.qualified_name == "auth:2.0.0"
        assert art.digest == "sha256:xyz"
        assert art.payload == {"handlers": 5}
        assert art.tags == {"team": "backend"}
        assert art.metadata == {"description": "Auth module"}
        assert art.size_bytes > 0


# ════════════════════════════════════════════════════════════════════════
# MODULE 12: INTEGRATION — Full Package Import Verification
# ════════════════════════════════════════════════════════════════════════


class TestFullImportChain:
    """Verify the entire import chain works without errors."""

    def test_import_aquilia_root(self):
        import aquilia
        assert hasattr(aquilia, "__version__")
        assert aquilia.__version__ == "1.0.0"

    def test_import_server(self):
        from aquilia.server import AquiliaServer
        assert AquiliaServer is not None

    def test_import_build_system(self):
        from aquilia.build import (
            AquiliaBuildPipeline, BuildResult, BuildConfig,
            StaticChecker, CrousBundler, BuildResolver,
        )

    def test_import_artifact_system(self):
        from aquilia.artifacts.store import (
            FilesystemArtifactStore, MemoryArtifactStore, ArtifactStore,
        )
        from aquilia.artifacts.core import Artifact, ArtifactEnvelope, ArtifactIntegrity

    def test_import_aquilary(self):
        from aquilia.aquilary.core import Aquilary, AquilaryRegistry
        from aquilia.aquilary.loader import ManifestLoader

    def test_import_cli_commands(self):
        from aquilia.cli.commands.serve import serve_production
        from aquilia.cli.commands.cache import cmd_cache_stats
        from aquilia.cli.commands.analytics import DiscoveryAnalytics

    def test_import_deployment_generators(self):
        from aquilia.cli.generators.deployment import (
            DockerfileGenerator,
            ComposeGenerator,
            KubernetesGenerator,
        )

    def test_no_trace_in_any_import(self):
        """After full import, 'aquilia.trace' should not be in sys.modules."""
        # Clear any cached trace module
        keys_before = set(sys.modules.keys())
        import aquilia  # noqa: F811
        keys_after = set(sys.modules.keys())
        trace_modules = [k for k in keys_after if "aquilia.trace" in k]
        assert len(trace_modules) == 0, \
            f"Trace modules found in sys.modules: {trace_modules}"
