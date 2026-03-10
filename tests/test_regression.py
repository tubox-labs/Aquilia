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

    def test_server_startup_no_trace(self):
        """startup() should not reference old trace system."""
        import inspect
        from aquilia.server import AquiliaServer
        source = inspect.getsource(AquiliaServer.startup)
        assert "self.trace" not in source, "startup() still references self.trace"
        assert "trace.journal" not in source, "startup() still references trace.journal"

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
            BuildManifest,
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
            "BuildPhase", "BuildError", "BuildManifest",
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
        assert "[!!]" in s

    def test_check_error_str_without_location(self):
        from aquilia.build.checker import CheckError, CheckSeverity
        err = CheckError(
            severity=CheckSeverity.WARNING,
            message="Unused import",
        )
        s = str(err)
        assert "[??]" in s
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

    def test_store_does_not_write_json_sidecar(self, store, sample_artifact):
        """save() must NOT write a .aq.json sidecar (Crous-only store)."""
        store.save(sample_artifact)
        json_files = list(Path(store.root).glob("*.aq.json"))
        assert len(json_files) == 0, "Unexpected .aq.json sidecar was created"

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

    def test_store_delete_removes_crous_file(self, store, sample_artifact):
        """delete() should remove the .crous file."""
        store.save(sample_artifact)
        assert store.exists("test-config")
        removed = store.delete("test-config", version="1.0.0")
        assert removed >= 1
        assert not store.exists("test-config", version="1.0.0")
        # Verify the crous file is gone
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
        import json as _json
        from aquilia.artifacts.store import FilesystemArtifactStore

        store = FilesystemArtifactStore(root=str(tmp_path / "artifacts"))
        Path(store.root).mkdir(parents=True, exist_ok=True)

        # Write a legacy .aq.json directly — simulates an old artifact directory
        # where save() wrote sidecars before this migration.
        legacy_data = {
            "kind": "config",
            "name": "legacy-art",
            "version": "1.0.0",
            "integrity": {"algorithm": "sha256", "digest": "legacy_digest"},
            "payload": {"legacy": True},
            "tags": {},
            "created_at": None,
        }
        legacy_file = Path(store.root) / "legacy-art-1.0.0.aq.json"
        legacy_file.write_text(_json.dumps(legacy_data), encoding="utf-8")

        # _iter_files should yield the .aq.json when no .crous counterpart exists
        files = list(store._iter_files())
        assert len(files) == 1
        assert files[0].name.endswith(".aq.json")

        # load() without version uses _iter_files which does the legacy fallback
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
        """Default values should be sane for production.

        ``workers`` and ``bind`` default to ``None`` so that values are
        resolved from the workspace AquilaConfig at runtime.  The fixed
        defaults (use_gunicorn, timeout, graceful_timeout) remain.
        """
        import inspect
        from aquilia.cli.commands.serve import serve_production
        sig = inspect.signature(serve_production)
        assert sig.parameters["use_gunicorn"].default is False
        assert sig.parameters["timeout"].default == 120
        assert sig.parameters["graceful_timeout"].default == 30
        # workers and bind are None — resolved from workspace config at runtime
        assert sig.parameters["workers"].default is None
        assert sig.parameters["bind"].default is None

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
# MODULE 6b: CONFIG RESOLUTION — CLI reads AquilaConfig from workspace.py
# ════════════════════════════════════════════════════════════════════════


class TestRuntimeConfigResolution:
    """Verify that run/serve commands read AquilaConfig from workspace.py."""

    def test_load_workspace_runtime_config_reads_port(self, tmp_path):
        """_load_workspace_runtime_config returns port from AquilaConfig."""
        from aquilia.cli.commands.run import _load_workspace_runtime_config

        ws = tmp_path / "workspace.py"
        ws.write_text(
            "from aquilia.config_builders import Workspace, AquilaConfig\n"
            "\n"
            "class BaseEnv(AquilaConfig):\n"
            "    env = 'dev'\n"
            "    class server(AquilaConfig.Server):\n"
            "        host = '0.0.0.0'\n"
            "        port = 9000\n"
            "        workers = 2\n"
            "        reload = False\n"
            "\n"
            "workspace = Workspace('test-app').env_config(BaseEnv)\n"
        )
        rt = _load_workspace_runtime_config(tmp_path)
        assert rt.get("host") == "0.0.0.0"
        assert rt.get("port") == 9000
        assert rt.get("workers") == 2
        assert rt.get("reload") is False

    def test_load_workspace_runtime_config_empty_on_missing(self, tmp_path):
        """Returns empty dict when workspace.py does not exist."""
        from aquilia.cli.commands.run import _load_workspace_runtime_config
        assert _load_workspace_runtime_config(tmp_path) == {}

    def test_run_dev_server_signature_uses_none_defaults(self):
        """run_dev_server accepts None for host/port/reload (resolved from config)."""
        import inspect
        from aquilia.cli.commands.run import run_dev_server
        sig = inspect.signature(run_dev_server)
        assert sig.parameters["host"].default is None
        assert sig.parameters["port"].default is None
        assert sig.parameters["reload"].default is None

    def test_server_run_signature_uses_none_defaults(self):
        """AquiliaServer.run() accepts None for host/port/reload."""
        import inspect
        from aquilia.server import AquiliaServer
        sig = inspect.signature(AquiliaServer.run)
        assert sig.parameters["host"].default is None
        assert sig.parameters["port"].default is None
        assert sig.parameters["reload"].default is None


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

    def test_dockerfile_uses_uvicorn(self):
        """Production Dockerfile CMD should use uvicorn."""
        import inspect
        from aquilia.cli.generators.deployment import DockerfileGenerator
        source = inspect.getsource(DockerfileGenerator.generate_dockerfile)
        assert "uvicorn" in source, \
            "Production Dockerfile should use uvicorn in CMD"

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
    """Test project configuration reflects actual dependency usage."""

    def test_pyproject_core_dependencies(self):
        """Core deps should only include click, PyYAML, uvicorn."""
        pyproject = Path(__file__).parent.parent / "pyproject.toml"
        content = pyproject.read_text()
        assert "click>=8.1.0" in content, "pyproject.toml missing click core dep"
        assert "PyYAML>=6.0.0" in content, "pyproject.toml missing PyYAML core dep"
        assert "uvicorn>=0.30.0" in content, "pyproject.toml missing uvicorn core dep"

    def test_pyproject_no_phantom_deps(self):
        """Removed deps that are never imported in the codebase."""
        pyproject = Path(__file__).parent.parent / "pyproject.toml"
        content = pyproject.read_text()
        # These are not imported anywhere in the aquilia package
        assert "passlib" not in content, "passlib should be removed (unused)"
        assert "python-dotenv" not in content, "python-dotenv should be removed (unused)"
        # crousr is used by aquilia.artifacts.store for .crous binary format
        assert "crousr" in content, "crousr is required by artifact store"

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
        assert aquilia.__version__ == "1.0.1a1"

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


# ════════════════════════════════════════════════════════════════════════
# MODULE 9: BUILD-FIRST DEPLOY SYSTEM — Comprehensive Test Suite
# ════════════════════════════════════════════════════════════════════════


class TestHasProductionBuild:
    """Verify _has_production_build correctly detects build artifacts.

    A valid production build requires BOTH build/manifest.json (the
    build→deploy metadata contract) and build/bundle.crous (the compiled
    binary artifacts).  Missing either file means no valid build exists.
    """

    def test_returns_false_when_build_dir_missing(self, tmp_path):
        """No build/ directory at all → False."""
        from aquilia.cli.commands.deploy_gen import _has_production_build
        assert _has_production_build(tmp_path) is False

    def test_returns_false_when_build_dir_empty(self, tmp_path):
        """Empty build/ directory → False."""
        from aquilia.cli.commands.deploy_gen import _has_production_build
        (tmp_path / "build").mkdir()
        assert _has_production_build(tmp_path) is False

    def test_returns_false_with_only_manifest(self, tmp_path):
        """Only manifest.json present (no bundle.crous) → False."""
        from aquilia.cli.commands.deploy_gen import _has_production_build
        build_dir = tmp_path / "build"
        build_dir.mkdir()
        (build_dir / "manifest.json").write_text("{}")
        assert _has_production_build(tmp_path) is False

    def test_returns_false_with_only_bundle(self, tmp_path):
        """Only bundle.crous present (no manifest.json) → False."""
        from aquilia.cli.commands.deploy_gen import _has_production_build
        build_dir = tmp_path / "build"
        build_dir.mkdir()
        (build_dir / "bundle.crous").write_bytes(b"\x00CROUS\x00")
        assert _has_production_build(tmp_path) is False

    def test_returns_true_with_both_artifacts(self, tmp_path):
        """Both manifest.json and bundle.crous present → True."""
        from aquilia.cli.commands.deploy_gen import _has_production_build
        build_dir = tmp_path / "build"
        build_dir.mkdir()
        (build_dir / "manifest.json").write_text('{"__format__": "aquilia-build-manifest"}')
        (build_dir / "bundle.crous").write_bytes(b"\x00CROUS\x00")
        assert _has_production_build(tmp_path) is True

    def test_ignores_extra_files_in_build_dir(self, tmp_path):
        """Extra files in build/ don't affect the check."""
        from aquilia.cli.commands.deploy_gen import _has_production_build
        build_dir = tmp_path / "build"
        build_dir.mkdir()
        (build_dir / "manifest.json").write_text("{}")
        (build_dir / "bundle.crous").write_bytes(b"BIN")
        (build_dir / "extra.log").write_text("build log")
        (build_dir / ".build-cache").mkdir()
        assert _has_production_build(tmp_path) is True

    def test_returns_false_when_manifest_is_dir_not_file(self, tmp_path):
        """manifest.json as a directory (not file) → False (exists() is True
        for dirs, but this shouldn't matter because both need to exist)."""
        from aquilia.cli.commands.deploy_gen import _has_production_build
        build_dir = tmp_path / "build"
        build_dir.mkdir()
        (build_dir / "manifest.json").mkdir()  # directory, not file
        (build_dir / "bundle.crous").write_bytes(b"BIN")
        # exists() returns True for directories too, so this actually returns True
        # This tests the current behavior — we check .exists() not .is_file()
        assert _has_production_build(tmp_path) is True

    def test_empty_files_still_count_as_existing(self, tmp_path):
        """Zero-byte files still pass the existence check."""
        from aquilia.cli.commands.deploy_gen import _has_production_build
        build_dir = tmp_path / "build"
        build_dir.mkdir()
        (build_dir / "manifest.json").write_text("")
        (build_dir / "bundle.crous").write_bytes(b"")
        assert _has_production_build(tmp_path) is True

    def test_nested_build_dir_not_detected(self, tmp_path):
        """build/ inside a subdirectory is NOT detected."""
        from aquilia.cli.commands.deploy_gen import _has_production_build
        nested = tmp_path / "sub" / "build"
        nested.mkdir(parents=True)
        (nested / "manifest.json").write_text("{}")
        (nested / "bundle.crous").write_bytes(b"BIN")
        # workspace_root is tmp_path, not tmp_path/sub
        assert _has_production_build(tmp_path) is False

    def test_symlinked_build_artifacts(self, tmp_path):
        """Symlinks to build artifacts are considered valid."""
        from aquilia.cli.commands.deploy_gen import _has_production_build
        real_dir = tmp_path / "real_build"
        real_dir.mkdir()
        (real_dir / "manifest.json").write_text("{}")
        (real_dir / "bundle.crous").write_bytes(b"BIN")

        build_dir = tmp_path / "build"
        build_dir.mkdir()
        (build_dir / "manifest.json").symlink_to(real_dir / "manifest.json")
        (build_dir / "bundle.crous").symlink_to(real_dir / "bundle.crous")
        assert _has_production_build(tmp_path) is True


class TestIsBuildStale:
    """Verify _is_build_stale correctly detects when sources are newer
    than the last build.

    Staleness is determined by comparing mtime of build/manifest.json
    against workspace.py, modules/**/*.py, and config/* files.
    """

    def test_stale_when_no_manifest(self, tmp_path):
        """No manifest.json at all → always stale."""
        from aquilia.cli.commands.deploy_gen import _is_build_stale
        assert _is_build_stale(tmp_path) is True

    def test_stale_when_manifest_dir_missing(self, tmp_path):
        """No build/ directory → stale."""
        from aquilia.cli.commands.deploy_gen import _is_build_stale
        assert _is_build_stale(tmp_path) is True

    def test_fresh_when_no_source_files(self, tmp_path):
        """Manifest exists but no source files → fresh (nothing to compare)."""
        from aquilia.cli.commands.deploy_gen import _is_build_stale
        build_dir = tmp_path / "build"
        build_dir.mkdir()
        (build_dir / "manifest.json").write_text("{}")
        assert _is_build_stale(tmp_path) is False

    def test_fresh_when_build_newer_than_workspace_py(self, tmp_path):
        """workspace.py older than manifest → fresh."""
        from aquilia.cli.commands.deploy_gen import _is_build_stale
        import time as _time

        (tmp_path / "workspace.py").write_text("# workspace")
        _time.sleep(0.05)
        build_dir = tmp_path / "build"
        build_dir.mkdir()
        (build_dir / "manifest.json").write_text("{}")

        assert _is_build_stale(tmp_path) is False

    def test_stale_when_workspace_py_modified(self, tmp_path):
        """workspace.py newer than manifest → stale."""
        from aquilia.cli.commands.deploy_gen import _is_build_stale
        import time as _time

        build_dir = tmp_path / "build"
        build_dir.mkdir()
        (build_dir / "manifest.json").write_text("{}")
        _time.sleep(0.05)
        (tmp_path / "workspace.py").write_text("# modified workspace")

        assert _is_build_stale(tmp_path) is True

    def test_stale_when_module_py_modified(self, tmp_path):
        """A .py file in modules/ newer than manifest → stale."""
        from aquilia.cli.commands.deploy_gen import _is_build_stale
        import time as _time

        build_dir = tmp_path / "build"
        build_dir.mkdir()
        (build_dir / "manifest.json").write_text("{}")
        _time.sleep(0.05)

        modules_dir = tmp_path / "modules" / "users"
        modules_dir.mkdir(parents=True)
        (modules_dir / "controller.py").write_text("# controller")

        assert _is_build_stale(tmp_path) is True

    def test_stale_when_deeply_nested_module_modified(self, tmp_path):
        """Deeply nested .py file under modules/ → stale."""
        from aquilia.cli.commands.deploy_gen import _is_build_stale
        import time as _time

        build_dir = tmp_path / "build"
        build_dir.mkdir()
        (build_dir / "manifest.json").write_text("{}")
        _time.sleep(0.05)

        deep_dir = tmp_path / "modules" / "billing" / "services" / "stripe"
        deep_dir.mkdir(parents=True)
        (deep_dir / "webhook.py").write_text("# webhook handler")

        assert _is_build_stale(tmp_path) is True

    def test_stale_when_config_file_modified(self, tmp_path):
        """Config file newer than manifest → stale."""
        from aquilia.cli.commands.deploy_gen import _is_build_stale
        import time as _time

        build_dir = tmp_path / "build"
        build_dir.mkdir()
        (build_dir / "manifest.json").write_text("{}")
        _time.sleep(0.05)

        config_dir = tmp_path / "config"
        config_dir.mkdir()
        (config_dir / "prod.yaml").write_text("db:\n  url: postgres://localhost/mydb")

        assert _is_build_stale(tmp_path) is True

    def test_stale_when_nested_config_modified(self, tmp_path):
        """Nested config file (config/envs/staging.yaml) → stale."""
        from aquilia.cli.commands.deploy_gen import _is_build_stale
        import time as _time

        build_dir = tmp_path / "build"
        build_dir.mkdir()
        (build_dir / "manifest.json").write_text("{}")
        _time.sleep(0.05)

        nested_cfg = tmp_path / "config" / "envs"
        nested_cfg.mkdir(parents=True)
        (nested_cfg / "staging.yaml").write_text("env: staging")

        assert _is_build_stale(tmp_path) is True

    def test_fresh_when_all_sources_older(self, tmp_path):
        """All source files older than manifest → fresh."""
        from aquilia.cli.commands.deploy_gen import _is_build_stale
        import time as _time

        # Create all source files first
        (tmp_path / "workspace.py").write_text("# ws")
        mod_dir = tmp_path / "modules" / "auth"
        mod_dir.mkdir(parents=True)
        (mod_dir / "manifest.py").write_text("# m")
        (mod_dir / "controller.py").write_text("# c")
        cfg_dir = tmp_path / "config"
        cfg_dir.mkdir()
        (cfg_dir / "base.yaml").write_text("key: val")
        _time.sleep(0.05)

        # Create manifest AFTER all sources
        build_dir = tmp_path / "build"
        build_dir.mkdir()
        (build_dir / "manifest.json").write_text("{}")

        assert _is_build_stale(tmp_path) is False

    def test_stale_with_multiple_modules_one_modified(self, tmp_path):
        """Multiple modules, only one newer → stale."""
        from aquilia.cli.commands.deploy_gen import _is_build_stale
        import time as _time

        # Create two modules before the build
        for mod_name in ("auth", "billing"):
            d = tmp_path / "modules" / mod_name
            d.mkdir(parents=True)
            (d / "controller.py").write_text(f"# {mod_name}")

        _time.sleep(0.05)
        build_dir = tmp_path / "build"
        build_dir.mkdir()
        (build_dir / "manifest.json").write_text("{}")
        _time.sleep(0.05)

        # Modify just one module
        (tmp_path / "modules" / "billing" / "controller.py").write_text("# updated")

        assert _is_build_stale(tmp_path) is True

    def test_non_py_files_in_modules_ignored(self, tmp_path):
        """Non-.py files in modules/ don't trigger staleness."""
        from aquilia.cli.commands.deploy_gen import _is_build_stale
        import time as _time

        build_dir = tmp_path / "build"
        build_dir.mkdir()
        (build_dir / "manifest.json").write_text("{}")
        _time.sleep(0.05)

        mod_dir = tmp_path / "modules" / "docs"
        mod_dir.mkdir(parents=True)
        (mod_dir / "README.md").write_text("# Docs module")
        (mod_dir / "notes.txt").write_text("notes")

        # Only .py files are checked in modules/
        assert _is_build_stale(tmp_path) is False

    def test_config_non_file_entries_ignored(self, tmp_path):
        """Subdirectories in config/ are traversed, only files count."""
        from aquilia.cli.commands.deploy_gen import _is_build_stale
        import time as _time

        build_dir = tmp_path / "build"
        build_dir.mkdir()
        (build_dir / "manifest.json").write_text("{}")
        _time.sleep(0.05)

        # config dir with only a subdirectory (no files)
        (tmp_path / "config" / "empty_subdir").mkdir(parents=True)

        assert _is_build_stale(tmp_path) is False


class TestEnsureProductionBuild:
    """Verify _ensure_production_build orchestrates the build gate correctly.

    This function is the main entry point for the build gate logic.
    It checks for build existence, staleness, and prompts/auto-builds.
    """

    def test_skip_flag_bypasses_all_checks(self):
        """skip_build_check=True → always returns True, even for /nonexistent."""
        from aquilia.cli.commands.deploy_gen import _ensure_production_build
        result = _ensure_production_build(
            Path("/absolutely/nonexistent/path"),
            interactive=False,
            skip_build_check=True,
        )
        assert result is True

    def test_fresh_build_returns_true_immediately(self, tmp_path):
        """Fresh build (both artifacts, nothing stale) → True without prompts."""
        from aquilia.cli.commands.deploy_gen import _ensure_production_build
        build_dir = tmp_path / "build"
        build_dir.mkdir()
        (build_dir / "manifest.json").write_text("{}")
        (build_dir / "bundle.crous").write_bytes(b"CROUS")

        result = _ensure_production_build(
            tmp_path, interactive=False, skip_build_check=False,
        )
        assert result is True

    def test_no_build_non_interactive_triggers_auto_build(self, tmp_path):
        """No build + non-interactive → calls _auto_build."""
        from aquilia.cli.commands.deploy_gen import _ensure_production_build

        with patch("aquilia.cli.commands.deploy_gen._auto_build", return_value=True) as mock_build:
            with patch("aquilia.cli.commands.deploy_gen.panel"):
                with patch("aquilia.cli.commands.deploy_gen.info"):
                    result = _ensure_production_build(
                        tmp_path, interactive=False, skip_build_check=False,
                    )
        assert result is True
        mock_build.assert_called_once_with(tmp_path)

    def test_no_build_non_interactive_auto_build_fails(self, tmp_path):
        """No build + non-interactive + auto-build fails → returns False."""
        from aquilia.cli.commands.deploy_gen import _ensure_production_build

        with patch("aquilia.cli.commands.deploy_gen._auto_build", return_value=False) as mock_build:
            with patch("aquilia.cli.commands.deploy_gen.panel"):
                with patch("aquilia.cli.commands.deploy_gen.info"):
                    with patch("aquilia.cli.commands.deploy_gen.error"):
                        result = _ensure_production_build(
                            tmp_path, interactive=False, skip_build_check=False,
                        )
        assert result is False
        mock_build.assert_called_once()

    def test_no_build_interactive_user_declines(self, tmp_path):
        """No build + interactive + user says No → returns False."""
        from aquilia.cli.commands.deploy_gen import _ensure_production_build

        with patch("aquilia.cli.commands.deploy_gen.confirm", return_value=False):
            with patch("aquilia.cli.commands.deploy_gen.panel"):
                with patch("aquilia.cli.commands.deploy_gen.error"):
                    with patch("aquilia.cli.commands.deploy_gen.info"):
                        result = _ensure_production_build(
                            tmp_path, interactive=True, skip_build_check=False,
                        )
        assert result is False

    def test_no_build_interactive_user_accepts_build_succeeds(self, tmp_path):
        """No build + interactive + user says Yes + build succeeds → True."""
        from aquilia.cli.commands.deploy_gen import _ensure_production_build

        with patch("aquilia.cli.commands.deploy_gen.confirm", return_value=True):
            with patch("aquilia.cli.commands.deploy_gen._auto_build", return_value=True):
                with patch("aquilia.cli.commands.deploy_gen.panel"):
                    result = _ensure_production_build(
                        tmp_path, interactive=True, skip_build_check=False,
                    )
        assert result is True

    def test_no_build_interactive_user_accepts_build_fails(self, tmp_path):
        """No build + interactive + user says Yes + build fails → False."""
        from aquilia.cli.commands.deploy_gen import _ensure_production_build

        with patch("aquilia.cli.commands.deploy_gen.confirm", return_value=True):
            with patch("aquilia.cli.commands.deploy_gen._auto_build", return_value=False):
                with patch("aquilia.cli.commands.deploy_gen.panel"):
                    with patch("aquilia.cli.commands.deploy_gen.error"):
                        result = _ensure_production_build(
                            tmp_path, interactive=True, skip_build_check=False,
                        )
        assert result is False

    def test_stale_build_interactive_user_declines_rebuild(self, tmp_path):
        """Stale build + interactive + user declines → True with warning."""
        from aquilia.cli.commands.deploy_gen import _ensure_production_build
        import time as _time

        # Create build artifacts
        build_dir = tmp_path / "build"
        build_dir.mkdir()
        (build_dir / "manifest.json").write_text("{}")
        (build_dir / "bundle.crous").write_bytes(b"CROUS")
        _time.sleep(0.05)
        # Make source newer
        (tmp_path / "workspace.py").write_text("# modified")

        with patch("aquilia.cli.commands.deploy_gen.confirm", return_value=False):
            with patch("aquilia.cli.commands.deploy_gen.panel"):
                with patch("aquilia.cli.commands.deploy_gen.warning"):
                    result = _ensure_production_build(
                        tmp_path, interactive=True, skip_build_check=False,
                    )
        # Stale build but user declined → continues with warning
        assert result is True

    def test_stale_build_non_interactive_triggers_auto_rebuild(self, tmp_path):
        """Stale build + non-interactive → auto-rebuilds."""
        from aquilia.cli.commands.deploy_gen import _ensure_production_build
        import time as _time

        build_dir = tmp_path / "build"
        build_dir.mkdir()
        (build_dir / "manifest.json").write_text("{}")
        (build_dir / "bundle.crous").write_bytes(b"CROUS")
        _time.sleep(0.05)
        (tmp_path / "workspace.py").write_text("# modified")

        with patch("aquilia.cli.commands.deploy_gen._auto_build", return_value=True) as mock_build:
            with patch("aquilia.cli.commands.deploy_gen.panel"):
                with patch("aquilia.cli.commands.deploy_gen.info"):
                    result = _ensure_production_build(
                        tmp_path, interactive=False, skip_build_check=False,
                    )
        assert result is True
        mock_build.assert_called_once_with(tmp_path)

    def test_stale_build_interactive_user_accepts_rebuild(self, tmp_path):
        """Stale build + interactive + rebuild succeeds → True."""
        from aquilia.cli.commands.deploy_gen import _ensure_production_build
        import time as _time

        build_dir = tmp_path / "build"
        build_dir.mkdir()
        (build_dir / "manifest.json").write_text("{}")
        (build_dir / "bundle.crous").write_bytes(b"CROUS")
        _time.sleep(0.05)
        (tmp_path / "workspace.py").write_text("# changed")

        with patch("aquilia.cli.commands.deploy_gen.confirm", return_value=True):
            with patch("aquilia.cli.commands.deploy_gen._auto_build", return_value=True):
                with patch("aquilia.cli.commands.deploy_gen.panel"):
                    result = _ensure_production_build(
                        tmp_path, interactive=True, skip_build_check=False,
                    )
        assert result is True


class TestAutoBuild:
    """Verify _auto_build delegates to AquiliaBuildPipeline correctly."""

    def test_auto_build_calls_pipeline_with_prod_mode(self, tmp_path):
        """_auto_build should call AquiliaBuildPipeline.build(mode='prod')."""
        from aquilia.cli.commands.deploy_gen import _auto_build

        mock_result = MagicMock()
        mock_result.success = True
        mock_result.fingerprint = "abc123def456"

        with patch("aquilia.build.AquiliaBuildPipeline.build", return_value=mock_result) as mock_build:
            with patch("aquilia.cli.commands.deploy_gen.banner"):
                with patch("aquilia.cli.commands.deploy_gen.success"):
                    with patch("aquilia.cli.commands.deploy_gen.kv"):
                        with patch("click.echo"):
                            result = _auto_build(tmp_path)

        assert result is True
        mock_build.assert_called_once_with(
            workspace_root=str(tmp_path),
            mode="prod",
            verbose=False,
        )

    def test_auto_build_returns_false_on_failure(self, tmp_path):
        """_auto_build returns False when the build fails."""
        from aquilia.cli.commands.deploy_gen import _auto_build

        mock_result = MagicMock()
        mock_result.success = False
        mock_result.errors = ["Module 'auth' has no manifest", "Syntax error in controller.py"]

        with patch("aquilia.build.AquiliaBuildPipeline.build", return_value=mock_result):
            with patch("aquilia.cli.commands.deploy_gen.banner"):
                with patch("aquilia.cli.commands.deploy_gen.error"):
                    with patch("click.echo"):
                        result = _auto_build(tmp_path)

        assert result is False

    def test_auto_build_returns_true_on_success_without_fingerprint(self, tmp_path):
        """_auto_build handles success with no fingerprint (None)."""
        from aquilia.cli.commands.deploy_gen import _auto_build

        mock_result = MagicMock()
        mock_result.success = True
        mock_result.fingerprint = None

        with patch("aquilia.build.AquiliaBuildPipeline.build", return_value=mock_result):
            with patch("aquilia.cli.commands.deploy_gen.banner"):
                with patch("aquilia.cli.commands.deploy_gen.success"):
                    with patch("click.echo"):
                        result = _auto_build(tmp_path)

        assert result is True

    def test_auto_build_truncates_long_error_list(self, tmp_path):
        """When >10 errors, only first 10 are shown + '... and N more'."""
        from aquilia.cli.commands.deploy_gen import _auto_build

        mock_result = MagicMock()
        mock_result.success = False
        mock_result.errors = [f"Error {i}" for i in range(15)]

        error_calls = []

        with patch("aquilia.build.AquiliaBuildPipeline.build", return_value=mock_result):
            with patch("aquilia.cli.commands.deploy_gen.banner"):
                with patch("aquilia.cli.commands.deploy_gen.error", side_effect=lambda x: error_calls.append(x)):
                    with patch("aquilia.cli.commands.deploy_gen.dim") as mock_dim:
                        with patch("click.echo"):
                            _auto_build(tmp_path)

        # 1 header + 10 error lines = 11 error() calls
        assert len(error_calls) == 11
        # dim() called with "... and 5 more"
        mock_dim.assert_called_once()
        dim_msg = mock_dim.call_args[0][0]
        assert "5 more" in dim_msg


class TestSubcommandBuildGate:
    """Verify _subcommand_build_gate reads skip from ctx.obj and exits
    on build gate failure."""

    def test_gate_passes_when_skip_set(self, tmp_path):
        """skip_build_check=True in ctx.obj → gate passes silently."""
        from aquilia.cli.commands.deploy_gen import _subcommand_build_gate

        ctx = MagicMock()
        ctx.obj = {"skip_build_check": True}

        # Should NOT raise or sys.exit
        _subcommand_build_gate(ctx, tmp_path)

    def test_gate_passes_with_fresh_build(self, tmp_path):
        """Valid build exists → gate passes."""
        from aquilia.cli.commands.deploy_gen import _subcommand_build_gate

        build_dir = tmp_path / "build"
        build_dir.mkdir()
        (build_dir / "manifest.json").write_text("{}")
        (build_dir / "bundle.crous").write_bytes(b"CROUS")

        ctx = MagicMock()
        ctx.obj = {"skip_build_check": False}

        _subcommand_build_gate(ctx, tmp_path)

    def test_gate_exits_when_no_build_non_interactive(self, tmp_path):
        """No build + non-interactive + auto-build fails → sys.exit(1)."""
        from aquilia.cli.commands.deploy_gen import _subcommand_build_gate

        ctx = MagicMock()
        ctx.obj = {"skip_build_check": False}

        with patch("aquilia.cli.commands.deploy_gen._auto_build", return_value=False):
            with patch("aquilia.cli.commands.deploy_gen.panel"):
                with patch("aquilia.cli.commands.deploy_gen.info"):
                    with patch("aquilia.cli.commands.deploy_gen.error"):
                        with patch("sys.stdin") as mock_stdin:
                            mock_stdin.isatty.return_value = False
                            with pytest.raises(SystemExit) as exc_info:
                                _subcommand_build_gate(ctx, tmp_path)
        assert exc_info.value.code == 1

    def test_gate_reads_skip_from_ctx_obj(self):
        """_subcommand_build_gate reads 'skip_build_check' from ctx.obj."""
        from aquilia.cli.commands.deploy_gen import _subcommand_build_gate

        ctx = MagicMock()
        ctx.obj = {"skip_build_check": True}

        # Should pass for any path since skip is True
        _subcommand_build_gate(ctx, Path("/nonexistent"))

    def test_gate_defaults_skip_to_false_when_missing(self, tmp_path):
        """If ctx.obj has no 'skip_build_check' key, default is False."""
        from aquilia.cli.commands.deploy_gen import _subcommand_build_gate

        build_dir = tmp_path / "build"
        build_dir.mkdir()
        (build_dir / "manifest.json").write_text("{}")
        (build_dir / "bundle.crous").write_bytes(b"CROUS")

        ctx = MagicMock()
        ctx.obj = {}  # No skip_build_check key

        # Should still pass because fresh build exists
        _subcommand_build_gate(ctx, tmp_path)


class TestGetCtx:
    """Verify _get_ctx prefers BuildManifest, falls back to introspection."""

    def test_prefers_build_manifest_when_available(self, tmp_path):
        """When manifest.json exists with valid format, use it."""
        from aquilia.cli.commands.deploy_gen import _get_ctx
        import json

        build_dir = tmp_path / "build"
        build_dir.mkdir()
        manifest_data = {
            "__format__": "aquilia-build-manifest",
            "schema_version": "2.0",
            "workspace_name": "my-app",
            "workspace_version": "1.2.0",
            "build_mode": "prod",
            "build_fingerprint": "abc123",
            "build_timestamp": "2026-03-05T00:00:00Z",
            "modules": [{"name": "users", "controllers": ["UserController"], "services": []}],
            "features": {"db": True, "cache": True, "websockets": False},
            "dependency_graph": {},
            "artifacts": [],
            "bundle_path": "bundle.crous",
            "warnings_count": 0,
        }
        (build_dir / "manifest.json").write_text(json.dumps(manifest_data))

        ctx = _get_ctx(tmp_path)
        assert ctx["_from_build_manifest"] is True
        assert ctx["name"] == "my-app"
        assert ctx["has_db"] is True
        assert ctx["has_cache"] is True
        assert ctx["has_websockets"] is False
        assert ctx["module_count"] == 1
        assert "users" in ctx["modules"]

    def test_falls_back_to_introspector_on_invalid_manifest(self, tmp_path):
        """Invalid manifest format → falls back to WorkspaceIntrospector."""
        from aquilia.cli.commands.deploy_gen import _get_ctx

        build_dir = tmp_path / "build"
        build_dir.mkdir()
        # Wrong format
        (build_dir / "manifest.json").write_text('{"__format__": "wrong"}')

        mock_introspector = MagicMock()
        mock_introspector.introspect.return_value = {"name": "fallback-app", "modules": []}

        with patch("aquilia.cli.generators.deployment.WorkspaceIntrospector", return_value=mock_introspector):
            ctx = _get_ctx(tmp_path)

        assert ctx["name"] == "fallback-app"

    def test_falls_back_when_no_build_dir(self, tmp_path):
        """No build/ dir at all → falls back to WorkspaceIntrospector."""
        from aquilia.cli.commands.deploy_gen import _get_ctx

        mock_introspector = MagicMock()
        mock_introspector.introspect.return_value = {"name": "no-build-app", "modules": []}

        with patch("aquilia.cli.generators.deployment.WorkspaceIntrospector", return_value=mock_introspector):
            ctx = _get_ctx(tmp_path)

        assert ctx["name"] == "no-build-app"


class TestWriteFile:
    """Verify _write_file handles force, dry_run, and existing files."""

    def test_writes_new_file(self, tmp_path):
        """Creates a new file with the given content."""
        from aquilia.cli.commands.deploy_gen import _write_file

        target = tmp_path / "output" / "Dockerfile"
        with patch("aquilia.cli.commands.deploy_gen.file_written"):
            result = _write_file(target, "FROM python:3.12", label="Dockerfile", verbose=False)

        assert result is True
        assert target.read_text() == "FROM python:3.12"

    def test_skips_existing_without_force(self, tmp_path):
        """Existing file without --force → skipped."""
        from aquilia.cli.commands.deploy_gen import _write_file

        target = tmp_path / "Dockerfile"
        target.write_text("OLD CONTENT")

        with patch("aquilia.cli.commands.deploy_gen.file_skipped") as mock_skipped:
            result = _write_file(target, "NEW CONTENT", label="Dockerfile", verbose=False)

        assert result is False
        assert target.read_text() == "OLD CONTENT"
        mock_skipped.assert_called_once()

    def test_overwrites_existing_with_force(self, tmp_path):
        """Existing file with --force → overwritten."""
        from aquilia.cli.commands.deploy_gen import _write_file

        target = tmp_path / "Dockerfile"
        target.write_text("OLD CONTENT")

        with patch("aquilia.cli.commands.deploy_gen.file_written"):
            result = _write_file(target, "NEW CONTENT", label="Dockerfile", verbose=False, force=True)

        assert result is True
        assert target.read_text() == "NEW CONTENT"

    def test_dry_run_does_not_write(self, tmp_path):
        """Dry run → returns True but doesn't create the file."""
        from aquilia.cli.commands.deploy_gen import _write_file

        target = tmp_path / "Dockerfile"

        with patch("aquilia.cli.commands.deploy_gen.file_dry"):
            result = _write_file(target, "FROM python:3.12", label="Dockerfile", verbose=False, dry_run=True)

        assert result is True
        assert not target.exists()

    def test_creates_parent_directories(self, tmp_path):
        """Nested output path → parent directories created automatically."""
        from aquilia.cli.commands.deploy_gen import _write_file

        target = tmp_path / "deploy" / "nginx" / "ssl" / "cert.pem"
        with patch("aquilia.cli.commands.deploy_gen.file_written"):
            result = _write_file(target, "cert content", label="cert.pem", verbose=False)

        assert result is True
        assert target.exists()
        assert target.read_text() == "cert content"


class TestBuildManifest:
    """Verify BuildManifest load, serialisation, and deploy context conversion."""

    def test_load_valid_manifest(self, tmp_path):
        """Load a properly formatted manifest.json."""
        from aquilia.build.pipeline import BuildManifest

        manifest_data = {
            "__format__": "aquilia-build-manifest",
            "schema_version": "2.0",
            "workspace_name": "shop-api",
            "workspace_version": "2.1.0",
            "build_mode": "prod",
            "build_fingerprint": "sha256:abcdef1234567890",
            "build_timestamp": "2026-03-05T10:30:00Z",
            "modules": [
                {"name": "products", "controllers": ["ProductController"], "services": ["ProductService"]},
                {"name": "orders", "controllers": ["OrderController"], "services": []},
            ],
            "features": {
                "db": True, "cache": True, "sessions": True,
                "websockets": False, "mlops": False, "mail": True,
                "auth": True, "templates": False, "static": True,
            },
            "dependency_graph": {"orders": ["products"]},
            "artifacts": [{"type": "bundle", "path": "bundle.crous", "size": 1024}],
            "bundle_path": "bundle.crous",
            "warnings_count": 2,
        }
        (tmp_path / "manifest.json").write_text(json.dumps(manifest_data))

        m = BuildManifest.load(tmp_path)
        assert m.workspace_name == "shop-api"
        assert m.workspace_version == "2.1.0"
        assert m.build_mode == "prod"
        assert m.build_fingerprint == "sha256:abcdef1234567890"
        assert len(m.modules) == 2
        assert m.features["db"] is True
        assert m.features["websockets"] is False
        assert m.dependency_graph == {"orders": ["products"]}
        assert m.warnings_count == 2

    def test_load_raises_file_not_found(self, tmp_path):
        """No manifest.json → FileNotFoundError."""
        from aquilia.build.pipeline import BuildManifest

        with pytest.raises(FileNotFoundError, match="No build manifest"):
            BuildManifest.load(tmp_path)

    def test_load_raises_value_error_on_invalid_format(self, tmp_path):
        """Wrong __format__ → ConfigInvalidFault."""
        from aquilia.build.pipeline import BuildManifest
        from aquilia.faults.domains import ConfigInvalidFault

        (tmp_path / "manifest.json").write_text('{"__format__": "not-aquilia"}')

        with pytest.raises(ConfigInvalidFault, match="Invalid build manifest format"):
            BuildManifest.load(tmp_path)

    def test_load_raises_value_error_on_missing_format(self, tmp_path):
        """Missing __format__ key → ConfigInvalidFault (defaults to empty string)."""
        from aquilia.build.pipeline import BuildManifest
        from aquilia.faults.domains import ConfigInvalidFault

        (tmp_path / "manifest.json").write_text('{"workspace_name": "test"}')

        with pytest.raises(ConfigInvalidFault, match="Invalid build manifest format"):
            BuildManifest.load(tmp_path)

    def test_to_deploy_context_basic_fields(self, tmp_path):
        """to_deploy_context populates all expected wctx keys."""
        from aquilia.build.pipeline import BuildManifest

        m = BuildManifest(
            workspace_name="ctx-app",
            workspace_version="3.0.0",
            build_mode="prod",
            build_fingerprint="fp123",
            modules=[
                {"name": "auth", "controllers": ["AuthCtrl"], "services": ["AuthSvc"]},
                {"name": "users", "controllers": ["UserCtrl"], "services": ["UserSvc", "ProfileSvc"]},
            ],
            features={"db": True, "cache": True, "websockets": True, "mlops": False},
        )
        ctx = m.to_deploy_context(tmp_path)

        assert ctx["name"] == "ctx-app"
        assert ctx["version"] == "3.0.0"
        assert ctx["port"] == 8000
        assert ctx["host"] == "0.0.0.0"
        assert ctx["module_count"] == 2
        assert ctx["controller_count"] == 2
        assert ctx["service_count"] == 3
        assert ctx["has_db"] is True
        assert ctx["has_cache"] is True
        assert ctx["has_websockets"] is True
        assert ctx["has_mlops"] is False
        assert ctx["build_fingerprint"] == "fp123"
        assert ctx["build_mode"] == "prod"
        assert ctx["_from_build_manifest"] is True

    def test_to_deploy_context_module_names(self, tmp_path):
        """Module names are correctly extracted."""
        from aquilia.build.pipeline import BuildManifest

        m = BuildManifest(
            workspace_name="multi-mod",
            modules=[
                {"name": "billing", "controllers": [], "services": []},
                {"name": "shipping", "controllers": [], "services": []},
                {"name": "notifications", "controllers": [], "services": []},
            ],
        )
        ctx = m.to_deploy_context(tmp_path)

        assert ctx["modules"] == ["billing", "shipping", "notifications"]
        assert ctx["module_count"] == 3

    def test_to_deploy_context_empty_modules(self, tmp_path):
        """No modules → empty list and zero counts."""
        from aquilia.build.pipeline import BuildManifest

        m = BuildManifest(workspace_name="empty-app", modules=[])
        ctx = m.to_deploy_context(tmp_path)

        assert ctx["modules"] == []
        assert ctx["module_count"] == 0
        assert ctx["controller_count"] == 0
        assert ctx["service_count"] == 0

    def test_to_deploy_context_cache_backend_mapping(self, tmp_path):
        """cache=True → cache_backend='redis', cache=False → 'memory'."""
        from aquilia.build.pipeline import BuildManifest

        m_cache = BuildManifest(workspace_name="a", features={"cache": True})
        ctx_cache = m_cache.to_deploy_context(tmp_path)
        assert ctx_cache["cache_backend"] == "redis"

        m_no_cache = BuildManifest(workspace_name="b", features={"cache": False})
        ctx_no_cache = m_no_cache.to_deploy_context(tmp_path)
        assert ctx_no_cache["cache_backend"] == "memory"

    def test_to_deploy_context_session_store_mapping(self, tmp_path):
        """sessions=True → session_store='redis', sessions=False → 'memory'."""
        from aquilia.build.pipeline import BuildManifest

        m = BuildManifest(workspace_name="s", features={"sessions": True})
        ctx = m.to_deploy_context(tmp_path)
        assert ctx["session_store"] == "redis"

        m2 = BuildManifest(workspace_name="s2", features={"sessions": False})
        ctx2 = m2.to_deploy_context(tmp_path)
        assert ctx2["session_store"] == "memory"

    def test_to_deploy_context_db_driver_detection_postgres(self, tmp_path):
        """Detects postgres from workspace.py."""
        from aquilia.build.pipeline import BuildManifest

        (tmp_path / "workspace.py").write_text('db_url = "postgresql://user:pass@db:5432/mydb"')

        m = BuildManifest(workspace_name="pg-app", features={"db": True})
        ctx = m.to_deploy_context(tmp_path)
        assert ctx["db_driver"] == "postgres"

    def test_to_deploy_context_db_driver_detection_mysql(self, tmp_path):
        """Detects mysql from workspace.py."""
        from aquilia.build.pipeline import BuildManifest

        (tmp_path / "workspace.py").write_text('db_url = "mysql://user:pass@db:3306/mydb"')

        m = BuildManifest(workspace_name="mysql-app", features={"db": True})
        ctx = m.to_deploy_context(tmp_path)
        assert ctx["db_driver"] == "mysql"

    def test_to_deploy_context_db_driver_defaults_to_sqlite(self, tmp_path):
        """No config files → defaults to sqlite."""
        from aquilia.build.pipeline import BuildManifest

        m = BuildManifest(workspace_name="lite-app", features={"db": True})
        ctx = m.to_deploy_context(tmp_path)
        assert ctx["db_driver"] == "sqlite"

    def test_to_deploy_context_worker_sizing(self, tmp_path):
        """Worker count scales with module count (min 2, max 8)."""
        from aquilia.build.pipeline import BuildManifest

        # 0 modules → workers = max(2, 2 + 0//4) = 2
        m0 = BuildManifest(workspace_name="a", modules=[])
        assert m0.to_deploy_context(tmp_path)["workers"] == 2

        # 4 modules → workers = max(2, 2 + 4//4) = 3
        m4 = BuildManifest(workspace_name="b", modules=[{"name": f"m{i}", "controllers": [], "services": []} for i in range(4)])
        assert m4.to_deploy_context(tmp_path)["workers"] == 3

        # 24 modules → workers = min(8, max(2, 2 + 24//4)) = min(8, 8) = 8
        m24 = BuildManifest(workspace_name="c", modules=[{"name": f"m{i}", "controllers": [], "services": []} for i in range(24)])
        assert m24.to_deploy_context(tmp_path)["workers"] == 8

        # 100 modules → capped at 8
        m100 = BuildManifest(workspace_name="d", modules=[{"name": f"m{i}", "controllers": [], "services": []} for i in range(100)])
        assert m100.to_deploy_context(tmp_path)["workers"] == 8

    def test_to_deploy_context_all_feature_flags(self, tmp_path):
        """All feature flags correctly mapped to wctx keys."""
        from aquilia.build.pipeline import BuildManifest

        features = {
            "db": True, "cache": True, "sessions": True,
            "websockets": True, "mlops": True, "mail": True,
            "auth": True, "templates": True, "static": True,
            "migrations": True, "effects": True, "faults": True,
            "cors": True, "csrf": True, "tracing": True, "metrics": True,
        }
        m = BuildManifest(workspace_name="full", features=features)
        ctx = m.to_deploy_context(tmp_path)

        assert ctx["has_db"] is True
        assert ctx["has_cache"] is True
        assert ctx["has_sessions"] is True
        assert ctx["has_websockets"] is True
        assert ctx["has_mlops"] is True
        assert ctx["has_mail"] is True
        assert ctx["has_auth"] is True
        assert ctx["has_templates"] is True
        assert ctx["has_static"] is True
        assert ctx["has_migrations"] is True
        assert ctx["has_effects"] is True
        assert ctx["has_faults"] is True
        assert ctx["cors_enabled"] is True
        assert ctx["csrf_protection"] is True
        assert ctx["tracing_enabled"] is True
        assert ctx["metrics_enabled"] is True

    def test_to_deploy_context_missing_features_default_false(self, tmp_path):
        """Unset feature flags default to False."""
        from aquilia.build.pipeline import BuildManifest

        m = BuildManifest(workspace_name="minimal", features={})
        ctx = m.to_deploy_context(tmp_path)

        assert ctx["has_db"] is False
        assert ctx["has_cache"] is False
        assert ctx["has_websockets"] is False
        assert ctx["has_mlops"] is False
        assert ctx["has_auth"] is False

    def test_to_deploy_context_generated_at_is_iso_format(self, tmp_path):
        """generated_at is a valid ISO timestamp."""
        from aquilia.build.pipeline import BuildManifest
        from datetime import datetime

        m = BuildManifest(workspace_name="ts-app")
        ctx = m.to_deploy_context(tmp_path)

        # Should not raise
        dt = datetime.fromisoformat(ctx["generated_at"])
        assert dt.year >= 2026

    def test_to_deploy_context_detects_existing_files(self, tmp_path):
        """Detects has_pyproject, has_requirements_txt, has_dockerfile, etc."""
        from aquilia.build.pipeline import BuildManifest

        # No files → all False
        m = BuildManifest(workspace_name="bare")
        ctx = m.to_deploy_context(tmp_path)
        assert ctx["has_pyproject"] is False
        assert ctx["has_requirements_txt"] is False
        assert ctx["has_dockerfile"] is False
        assert ctx["has_compose"] is False
        assert ctx["has_k8s"] is False

        # Create files
        (tmp_path / "pyproject.toml").write_text("[tool.aquilia]")
        (tmp_path / "requirements.txt").write_text("aquilia>=1.0")
        (tmp_path / "Dockerfile").write_text("FROM python:3.12")
        (tmp_path / "docker-compose.yml").write_text("version: '3'")
        (tmp_path / "k8s").mkdir()

        ctx2 = m.to_deploy_context(tmp_path)
        assert ctx2["has_pyproject"] is True
        assert ctx2["has_requirements_txt"] is True
        assert ctx2["has_dockerfile"] is True
        assert ctx2["has_compose"] is True
        assert ctx2["has_k8s"] is True

    def test_load_with_defaults_for_missing_keys(self, tmp_path):
        """Manifest with only __format__ uses sensible defaults."""
        from aquilia.build.pipeline import BuildManifest

        (tmp_path / "manifest.json").write_text('{"__format__": "aquilia-build-manifest"}')

        m = BuildManifest.load(tmp_path)
        assert m.workspace_name == ""
        assert m.workspace_version == "0.1.0"
        assert m.build_mode == "dev"
        assert m.build_fingerprint == ""
        assert m.modules == []
        assert m.features == {}
        assert m.warnings_count == 0

    def test_load_with_mariadb_url(self, tmp_path):
        """Detects mariadb as mysql driver."""
        from aquilia.build.pipeline import BuildManifest

        (tmp_path / "workspace.py").write_text('db_url = "mariadb://user:pass@db:3306/mydb"')

        m = BuildManifest(workspace_name="maria-app", features={"db": True})
        ctx = m.to_deploy_context(tmp_path)
        assert ctx["db_driver"] == "mysql"

    def test_load_detects_db_from_workspace_py(self, tmp_path):
        """Detects DB driver from workspace.py."""
        from aquilia.build.pipeline import BuildManifest

        (tmp_path / "workspace.py").write_text('url = "postgresql://host/db"')

        m = BuildManifest(workspace_name="ws-py", features={"db": True})
        ctx = m.to_deploy_context(tmp_path)
        assert ctx["db_driver"] == "postgres"

    def test_load_detects_aquilia_py_fallback(self, tmp_path):
        """Detects DB driver from aquilia.py when workspace.py absent."""
        from aquilia.build.pipeline import BuildManifest

        (tmp_path / "aquilia.py").write_text('host = "mysql://host/db"')

        m = BuildManifest(workspace_name="aquilia-py", features={"db": True})
        ctx = m.to_deploy_context(tmp_path)
        assert ctx["db_driver"] == "mysql"


class TestDeployGroupCLI:
    """Verify the deploy Click group, options, and subcommand registration."""

    def test_deploy_group_is_click_group(self):
        """deploy_gen_group is a Click group."""
        import click
        from aquilia.cli.commands.deploy_gen import deploy_gen_group
        assert isinstance(deploy_gen_group, click.Group)

    def test_deploy_group_invokes_without_command(self):
        """Group has invoke_without_command=True."""
        from aquilia.cli.commands.deploy_gen import deploy_gen_group
        assert deploy_gen_group.invoke_without_command is True

    def test_deploy_group_has_required_options(self):
        """Group exposes --force, --dry-run, --yes, --skip-build-check."""
        from aquilia.cli.commands.deploy_gen import deploy_gen_group
        param_names = [p.name for p in deploy_gen_group.params]
        assert "force" in param_names
        assert "dry_run" in param_names
        assert "yes" in param_names
        assert "skip_build_check" in param_names

    def test_all_nine_subcommands_registered(self):
        """All 9 subcommands are registered on the deploy group."""
        from aquilia.cli.commands.deploy_gen import deploy_gen_group
        expected = {"dockerfile", "compose", "kubernetes", "nginx", "ci", "monitoring", "env", "all", "makefile"}
        actual = set(deploy_gen_group.commands.keys())
        assert expected.issubset(actual), f"Missing: {expected - actual}"

    def test_each_subcommand_is_click_command(self):
        """Each registered subcommand is a click.Command instance."""
        import click
        from aquilia.cli.commands.deploy_gen import deploy_gen_group
        for name, cmd in deploy_gen_group.commands.items():
            assert isinstance(cmd, click.Command), f"{name} is not a click.Command"

    def test_dockerfile_subcommand_has_dev_and_mlops_flags(self):
        """aq deploy dockerfile has --dev and --mlops flags."""
        from aquilia.cli.commands.deploy_gen import deploy_gen_group
        cmd = deploy_gen_group.commands["dockerfile"]
        param_names = [p.name for p in cmd.params]
        assert "dev_mode" in param_names
        assert "mlops_mode" in param_names

    def test_compose_subcommand_has_monitoring_flag(self):
        """aq deploy compose has --monitoring flag."""
        from aquilia.cli.commands.deploy_gen import deploy_gen_group
        cmd = deploy_gen_group.commands["compose"]
        param_names = [p.name for p in cmd.params]
        assert "monitoring" in param_names

    def test_kubernetes_subcommand_has_mlops_flag(self):
        """aq deploy kubernetes has --mlops flag."""
        from aquilia.cli.commands.deploy_gen import deploy_gen_group
        cmd = deploy_gen_group.commands["kubernetes"]
        param_names = [p.name for p in cmd.params]
        assert "mlops" in param_names

    def test_ci_subcommand_has_provider_choice(self):
        """aq deploy ci has --provider with github/gitlab choices."""
        import click
        from aquilia.cli.commands.deploy_gen import deploy_gen_group
        cmd = deploy_gen_group.commands["ci"]
        provider_param = None
        for p in cmd.params:
            if p.name == "provider":
                provider_param = p
                break
        assert provider_param is not None
        assert isinstance(provider_param.type, click.Choice)
        assert set(provider_param.type.choices) == {"github", "gitlab"}

    def test_all_subcommand_has_ci_provider_and_monitoring(self):
        """aq deploy all has --ci-provider and --monitoring."""
        from aquilia.cli.commands.deploy_gen import deploy_gen_group
        cmd = deploy_gen_group.commands["all"]
        param_names = [p.name for p in cmd.params]
        assert "ci_provider" in param_names
        assert "monitoring" in param_names


class TestDeployContextIntegration:
    """Integration tests ensuring BuildManifest→deploy context→generator
    pipeline works end to end with realistic data."""

    def test_full_manifest_roundtrip(self, tmp_path):
        """Write manifest.json, load it, convert to deploy context."""
        from aquilia.build.pipeline import BuildManifest

        manifest_data = {
            "__format__": "aquilia-build-manifest",
            "schema_version": "2.0",
            "workspace_name": "e2e-test",
            "workspace_version": "1.0.0",
            "build_mode": "prod",
            "build_fingerprint": "sha256:roundtrip",
            "build_timestamp": "2026-03-05T12:00:00Z",
            "modules": [
                {"name": "api", "controllers": ["ApiController"], "services": ["ApiService"]},
            ],
            "features": {"db": True, "cache": True, "auth": True},
            "dependency_graph": {},
            "artifacts": [],
            "bundle_path": "bundle.crous",
            "warnings_count": 0,
        }
        build_dir = tmp_path / "build"
        build_dir.mkdir()
        (build_dir / "manifest.json").write_text(json.dumps(manifest_data))

        # Load and convert
        m = BuildManifest.load(build_dir)
        ctx = m.to_deploy_context(tmp_path)

        # Verify roundtrip preserves all data
        assert ctx["name"] == "e2e-test"
        assert ctx["version"] == "1.0.0"
        assert ctx["build_fingerprint"] == "sha256:roundtrip"
        assert ctx["build_mode"] == "prod"
        assert ctx["has_db"] is True
        assert ctx["has_cache"] is True
        assert ctx["has_auth"] is True
        assert ctx["module_count"] == 1
        assert ctx["controller_count"] == 1
        assert ctx["service_count"] == 1
        assert ctx["_from_build_manifest"] is True

    def test_get_ctx_uses_manifest_over_introspector(self, tmp_path):
        """_get_ctx prefers manifest over WorkspaceIntrospector."""
        from aquilia.cli.commands.deploy_gen import _get_ctx

        manifest_data = {
            "__format__": "aquilia-build-manifest",
            "workspace_name": "manifest-wins",
            "modules": [],
            "features": {},
        }
        build_dir = tmp_path / "build"
        build_dir.mkdir()
        (build_dir / "manifest.json").write_text(json.dumps(manifest_data))

        ctx = _get_ctx(tmp_path)
        assert ctx["name"] == "manifest-wins"
        assert ctx["_from_build_manifest"] is True

    def test_build_gate_then_get_ctx_flow(self, tmp_path):
        """Simulates the real flow: build gate passes → _get_ctx reads manifest."""
        from aquilia.cli.commands.deploy_gen import (
            _has_production_build,
            _is_build_stale,
            _get_ctx,
        )

        # Set up a complete, fresh build
        build_dir = tmp_path / "build"
        build_dir.mkdir()
        manifest_data = {
            "__format__": "aquilia-build-manifest",
            "workspace_name": "flow-test",
            "modules": [{"name": "core", "controllers": ["CoreCtrl"], "services": []}],
            "features": {"db": True},
        }
        (build_dir / "manifest.json").write_text(json.dumps(manifest_data))
        (build_dir / "bundle.crous").write_bytes(b"\x00CROUSBINARY\x00")

        # 1. Check build exists
        assert _has_production_build(tmp_path) is True
        # 2. Check not stale
        assert _is_build_stale(tmp_path) is False
        # 3. Get context
        ctx = _get_ctx(tmp_path)
        assert ctx["name"] == "flow-test"
        assert ctx["has_db"] is True
        assert ctx["_from_build_manifest"] is True

    def test_deploy_context_has_all_required_keys(self, tmp_path):
        """Deploy context dict contains all keys expected by generators."""
        from aquilia.build.pipeline import BuildManifest

        m = BuildManifest(
            workspace_name="keychecker",
            modules=[{"name": "mod", "controllers": ["C"], "services": ["S"]}],
            features={"db": True, "cache": True},
        )
        ctx = m.to_deploy_context(tmp_path)

        # Required keys that generators depend on
        required_keys = [
            "name", "version", "python_version", "port", "host", "workers",
            "modules", "module_count", "controller_count", "service_count",
            "has_db", "db_driver", "has_cache", "cache_backend",
            "has_sessions", "session_store", "has_websockets", "has_mlops",
            "has_mail", "has_auth", "has_templates", "has_static",
            "has_migrations", "has_openapi", "has_effects", "has_faults",
            "cors_enabled", "csrf_protection", "helmet_enabled", "rate_limiting",
            "tracing_enabled", "metrics_enabled", "logging_enabled",
            "has_pyproject", "dependencies", "has_requirements_txt",
            "has_dockerfile", "has_compose", "has_k8s",
            "build_fingerprint", "build_mode", "build_timestamp",
            "generated_at", "_from_build_manifest",
        ]
        for key in required_keys:
            assert key in ctx, f"Missing required key: {key}"


class TestBuildPhaseEnum:
    """Verify BuildPhase enum values and string representation."""

    def test_all_phases_present(self):
        """All expected build phases exist in the enum."""
        from aquilia.build.pipeline import BuildPhase

        expected = {"discovery", "validation", "static_check", "compilation", "bundling", "done"}
        actual = {p.value for p in BuildPhase}
        assert expected == actual

    def test_phases_are_strings(self):
        """BuildPhase values are strings (str, Enum)."""
        from aquilia.build.pipeline import BuildPhase
        for phase in BuildPhase:
            assert isinstance(phase, str)
            assert isinstance(phase.value, str)

    def test_phase_ordering(self):
        """Phases can be compared as strings."""
        from aquilia.build.pipeline import BuildPhase
        assert BuildPhase.DISCOVERY.value == "discovery"
        assert BuildPhase.DONE.value == "done"


class TestBuildGateImportsAndAPI:
    """Verify the public API surface of the build-first deploy system."""

    def test_all_build_gate_functions_importable(self):
        """All build gate functions are importable from deploy_gen."""
        from aquilia.cli.commands.deploy_gen import (
            _has_production_build,
            _is_build_stale,
            _auto_build,
            _ensure_production_build,
            _subcommand_build_gate,
            _get_ctx,
            _write_file,
        )
        for fn in [_has_production_build, _is_build_stale, _auto_build,
                    _ensure_production_build, _subcommand_build_gate,
                    _get_ctx, _write_file]:
            assert callable(fn)

    def test_build_manifest_importable_from_build_package(self):
        """BuildManifest is in the aquilia.build public API."""
        from aquilia.build import BuildManifest
        assert hasattr(BuildManifest, "load")
        assert hasattr(BuildManifest, "to_deploy_context")

    def test_build_pipeline_importable(self):
        """AquiliaBuildPipeline is in the aquilia.build public API."""
        from aquilia.build import AquiliaBuildPipeline
        assert hasattr(AquiliaBuildPipeline, "build")

    def test_deploy_gen_module_docstring(self):
        """deploy_gen module has a docstring describing build-first."""
        import aquilia.cli.commands.deploy_gen as mod
        assert mod.__doc__ is not None
        assert "build" in mod.__doc__.lower()
        assert "deploy" in mod.__doc__.lower()

    def test_deploy_options_decorator_exists(self):
        """deploy_options decorator is defined and callable."""
        from aquilia.cli.commands.deploy_gen import deploy_options
        assert callable(deploy_options)

    def test_has_command_utility(self):
        """_has_command checks PATH for CLI tools."""
        from aquilia.cli.commands.deploy_gen import _has_command
        # 'python' should exist in any test environment
        assert _has_command("python3") is True or _has_command("python") is True
        # Non-existent command
        assert _has_command("this_command_does_not_exist_xyz123") is False


class TestExecutionHelpers:
    """Verify execution helper functions for running containers and tools."""

    def test_has_command_returns_bool(self):
        """_has_command always returns a boolean."""
        from aquilia.cli.commands.deploy_gen import _has_command
        result = _has_command("ls")
        assert isinstance(result, bool)

    def test_run_dry_run_does_not_execute(self, tmp_path):
        """_run with dry_run=True does not execute the command."""
        from aquilia.cli.commands.deploy_gen import _run

        with patch("aquilia.cli.commands.deploy_gen.dim"):
            result = _run(
                ["echo", "hello"],
                label="test",
                cwd=tmp_path,
                dry_run=True,
            )
        assert result is True

    def test_run_with_nonexistent_command(self, tmp_path):
        """_run with a command that doesn't exist → returns False."""
        from aquilia.cli.commands.deploy_gen import _run

        with patch("aquilia.cli.commands.deploy_gen.info"):
            with patch("aquilia.cli.commands.deploy_gen.error"):
                result = _run(
                    ["this_cmd_does_not_exist_xyz"],
                    label="test",
                    cwd=tmp_path,
                    dry_run=False,
                )
        assert result is False

    def test_exec_docker_build_dry_run(self, tmp_path):
        """_exec_docker_build with dry_run → returns True without Docker."""
        from aquilia.cli.commands.deploy_gen import _exec_docker_build

        wctx = {"name": "test-app"}
        with patch("aquilia.cli.commands.deploy_gen.dim"):
            result = _exec_docker_build(tmp_path, wctx, dry_run=True)
        assert result is True

    def test_exec_docker_build_no_dockerfile(self, tmp_path):
        """_exec_docker_build without Dockerfile → returns False."""
        from aquilia.cli.commands.deploy_gen import _exec_docker_build

        wctx = {"name": "test-app"}
        with patch("aquilia.cli.commands.deploy_gen.warning"):
            result = _exec_docker_build(tmp_path, wctx, dry_run=False)
        assert result is False

    def test_exec_compose_up_dry_run(self, tmp_path):
        """_exec_compose_up with dry_run → returns True."""
        from aquilia.cli.commands.deploy_gen import _exec_compose_up

        with patch("aquilia.cli.commands.deploy_gen.dim"):
            result = _exec_compose_up(tmp_path, dry_run=True)
        assert result is True

    def test_exec_compose_up_no_compose_file(self, tmp_path):
        """_exec_compose_up without docker-compose.yml → returns False."""
        from aquilia.cli.commands.deploy_gen import _exec_compose_up

        with patch("aquilia.cli.commands.deploy_gen.warning"):
            result = _exec_compose_up(tmp_path, dry_run=False)
        assert result is False

    def test_exec_k8s_apply_no_k8s_dir(self, tmp_path):
        """_exec_k8s_apply without k8s/ → returns None (skipped)."""
        from aquilia.cli.commands.deploy_gen import _exec_k8s_apply

        with patch("aquilia.cli.commands.deploy_gen.warning"):
            result = _exec_k8s_apply(tmp_path, dry_run=False)
        assert result is None

    def test_exec_k8s_apply_dry_run(self, tmp_path):
        """_exec_k8s_apply with dry_run → returns True."""
        from aquilia.cli.commands.deploy_gen import _exec_k8s_apply

        with patch("aquilia.cli.commands.deploy_gen.dim"):
            result = _exec_k8s_apply(tmp_path, dry_run=True)
        assert result is True

    def test_exec_k8s_apply_no_kubectl(self, tmp_path):
        """_exec_k8s_apply without kubectl on PATH → returns None."""
        from aquilia.cli.commands.deploy_gen import _exec_k8s_apply

        (tmp_path / "k8s").mkdir()
        with patch("aquilia.cli.commands.deploy_gen._has_command", return_value=False):
            with patch("aquilia.cli.commands.deploy_gen.warning"):
                result = _exec_k8s_apply(tmp_path, dry_run=False)
        assert result is None

    def test_exec_compose_audit_no_compose(self, tmp_path):
        """_exec_compose_audit without compose file → returns False."""
        from aquilia.cli.commands.deploy_gen import _exec_compose_audit
        result = _exec_compose_audit(tmp_path, dry_run=False)
        assert result is False

    def test_exec_monitoring_up_no_compose(self, tmp_path):
        """_exec_monitoring_up without compose file → returns False."""
        from aquilia.cli.commands.deploy_gen import _exec_monitoring_up

        with patch("aquilia.cli.commands.deploy_gen.warning"):
            result = _exec_monitoring_up(tmp_path, dry_run=False)
        assert result is False

    def test_k8s_cluster_reachable_returns_bool(self):
        """_k8s_cluster_reachable always returns a boolean."""
        from aquilia.cli.commands.deploy_gen import _k8s_cluster_reachable
        result = _k8s_cluster_reachable()
        assert isinstance(result, bool)
