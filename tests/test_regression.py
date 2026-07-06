"""
Comprehensive Regression Test Suite — Aquilia v1.0.0 Architecture Overhaul
==========================================================================

Tests every change made during the two-phase architecture redesign:

Phase 1 — Architecture Overhaul
  - Trace removal: no trace imports, no trace module, no trace CLI
  - JSON → Surp migration: artifact store, aquilary core, aquilary loader
  - Artifact store: .surp binary + .aq.json sidecar, fallback reads
  - Production deploy: gunicorn + UvicornWorker support
  - Deployment generator: no .aquilia/, gunicorn CMD, native introspection
  - Analytics: cache dir moved to workspace cache, Surp format
  - pyproject.toml: server optional dependency group
"""

from pathlib import Path
from unittest.mock import patch

import pytest

try:
    import surp as _surp_probe  # noqa: F401

    _HAS_SURP = True
except ImportError:
    _HAS_SURP = False

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
            "AquiliaTrace",
            "TraceManifest",
            "TraceRouteMap",
            "TraceDIGraph",
            "TraceSchemaLedger",
            "TraceLifecycleJournal",
            "TraceConfigSnapshot",
            "TraceDiagnostics",
        ]
        for sym in trace_symbols:
            assert sym not in all_symbols, f"'{sym}' still in aquilia.__all__"

    def test_trace_not_in_commands_init(self):
        """'trace' must not be in cli/commands/__init__.py imports."""
        from aquilia.cli import commands

        assert "trace" not in dir(commands) or not hasattr(commands, "trace"), (
            "'trace' still importable from aquilia.cli.commands"
        )

    def test_trace_not_in_cli_categories(self):
        """'trace' must not appear in any CLI category."""
        from aquilia.cli.__main__ import AquiliaGroup

        categories = AquiliaGroup._CATEGORIES
        for cat_name, commands in categories.items():
            assert "trace" not in commands, f"'trace' still in CLI category '{cat_name}'"

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


# MODULE 2: SURP BINARY MIGRATION — Artifact Store removed (artifact system deprecated)


# ════════════════════════════════════════════════════════════════════════
# MODULE 4: SURP BINARY MIGRATION — Aquilary Core & Loader
# ════════════════════════════════════════════════════════════════════════


class TestAquilarySurpMigration:
    """Test that aquilary core uses Surp for freeze/from_frozen."""

    def test_aquilary_core_importable(self):
        from aquilia.aquilary.core import Aquilary, AquilaryRegistry

        assert Aquilary is not None
        assert AquilaryRegistry is not None

    def test_freeze_writes_surp_format(self):
        """AquilaryRegistry.export_manifest() should write .surp binary when Surp is available."""
        import inspect

        from aquilia.aquilary.core import AquilaryRegistry

        # The freeze/export method is export_manifest on AquilaryRegistry
        assert hasattr(AquilaryRegistry, "export_manifest"), "AquilaryRegistry should have an export_manifest() method"
        source = inspect.getsource(AquilaryRegistry.export_manifest)
        assert "surp" in source.lower(), "export_manifest() should reference Surp encoding"

    def test_from_frozen_reads_surp_format(self):
        """Aquilary._from_frozen_manifest() should read .surp binary."""
        import inspect

        from aquilia.aquilary.core import Aquilary

        # _from_frozen_manifest is a classmethod on Aquilary, not AquilaryRegistry
        assert hasattr(Aquilary, "_from_frozen_manifest"), "Aquilary should have a _from_frozen_manifest() classmethod"
        source = inspect.getsource(Aquilary._from_frozen_manifest)
        assert "surp" in source.lower(), "_from_frozen_manifest() should reference Surp decoding"
        assert "json" in source.lower(), "_from_frozen_manifest() should have JSON fallback"


class TestAquilaryLoaderSurp:
    """Test that the manifest loader supports .surp files."""

    def test_loader_supports_surp_extension(self):
        """ManifestLoader should accept .surp files in its loading logic."""
        import inspect

        from aquilia.aquilary.loader import ManifestLoader

        # Check the full class source for .surp support
        source = inspect.getsource(ManifestLoader)
        assert ".surp" in source, "ManifestLoader should support .surp extension"

    def test_loader_load_dsl_supports_surp(self):
        """_load_from_dsl_file should decode .surp files."""
        import inspect

        from aquilia.aquilary.loader import ManifestLoader

        source = inspect.getsource(ManifestLoader._load_from_dsl_file)
        assert ".surp" in source, "_load_from_dsl_file should handle .surp format"

    def test_loader_directory_scan_includes_surp(self):
        """Directory scanning should look for manifest.surp."""
        import inspect

        from aquilia.aquilary.loader import ManifestLoader

        # Check the full class source for manifest.surp file discovery
        source = inspect.getsource(ManifestLoader)
        assert "manifest.surp" in source or ".surp" in source, "ManifestLoader should discover manifest.surp files"


# ════════════════════════════════════════════════════════════════════════
# MODULE 5: SURP BINARY ENCODING — Low-Level Backend Tests
# ════════════════════════════════════════════════════════════════════════


@pytest.mark.skipif(not _HAS_SURP, reason="surp is not installed (optional dependency)")
class TestSurpBackend:
    """Test the low-level Surp binary encoder/decoder."""

    def test_surp_available(self):
        """Surp must be installed."""
        try:
            import surp

            return
        except ImportError:
            pytest.fail("surp is not installed")

    def test_encode_decode_dict(self):
        import surp as backend

        data = {"a": 1, "b": "hello", "c": [1, 2, 3]}
        assert backend.decode(backend.encode(data)) == data

    def test_encode_decode_nested(self):
        import surp as backend

        data = {"level1": {"level2": {"level3": [{"value": i} for i in range(10)]}}}
        assert backend.decode(backend.encode(data)) == data

    def test_encode_decode_types(self):
        """Test encoding of all supported types."""
        import surp as backend

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
        import surp as backend

        assert backend.decode(backend.encode({})) == {}
        assert backend.decode(backend.encode([])) == []
        assert backend.decode(backend.encode("")) == ""

    def test_encode_large_payload(self):
        """Surp should handle reasonably large payloads."""
        import surp as backend

        data = {
            "routes": [{"path": f"/api/resource/{i}", "method": "GET", "handler": f"handler_{i}"} for i in range(500)]
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
            "from aquilia import Workspace, AquilaConfig\n"
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
        assert ".aquilia" not in source, "Production Dockerfile still references .aquilia directory"

    def test_dockerfile_uses_uvicorn(self):
        """Production Dockerfile CMD should use uvicorn."""
        import inspect

        from aquilia.cli.generators.deployment import DockerfileGenerator

        source = inspect.getsource(DockerfileGenerator.generate_dockerfile)
        assert "uvicorn" in source, "Production Dockerfile should use uvicorn in CMD"

    def test_dockerignore_no_aquilia_dir(self):
        """Dockerignore should not reference .aquilia/."""
        import inspect

        from aquilia.cli.generators.deployment import DockerfileGenerator

        source = inspect.getsource(DockerfileGenerator.generate_dockerignore)
        assert ".aquilia/" not in source, ".dockerignore still references .aquilia/"

    def test_compose_no_trace_volume(self):
        """Compose generator should not have app-trace volume."""
        import inspect

        from aquilia.cli.generators.deployment import ComposeGenerator

        source = inspect.getsource(ComposeGenerator.generate_compose)
        assert "app-trace" not in source, "Docker Compose still has app-trace volume"

    def test_kubernetes_no_trace_volume(self):
        """K8s deployment should not have trace volume mounts."""
        import inspect

        from aquilia.cli.generators.deployment import KubernetesGenerator

        source = inspect.getsource(KubernetesGenerator.generate_deployment)
        assert "trace" not in source.lower() or "torch" in source.lower() or source.lower().count("trace") == 0, (
            "K8s deployment still has trace volume mount"
        )

    def test_makefile_uses_compile_command(self):
        """Makefile compile target should use the native compile command."""
        import inspect

        from aquilia.cli.generators.deployment import MakefileGenerator

        source = inspect.getsource(MakefileGenerator.generate_makefile)
        assert "aquilia.cli compile" in source
        assert "aquilia.cli build" not in source

    def test_makefile_clean_no_aquilia(self):
        """Makefile clean target should not reference .aquilia/."""
        import inspect

        from aquilia.cli.generators.deployment import MakefileGenerator

        source = inspect.getsource(MakefileGenerator.generate_makefile)
        assert ".aquilia/" not in source, "Makefile clean target still references .aquilia/"


# ════════════════════════════════════════════════════════════════════════
# MODULE 8: ANALYTICS — Cache Dir & Surp Format
# ════════════════════════════════════════════════════════════════════════


class TestAnalyticsSurp:
    """Test analytics cache directory and format changes."""

    def test_analytics_cache_dir_is_build_cache(self):
        """DiscoveryAnalytics cache_dir should be build/.cache, not .aquilia/discovery."""
        import inspect

        from aquilia.cli.commands.analytics import DiscoveryAnalytics

        source = inspect.getsource(DiscoveryAnalytics.__init__)
        assert ".aquilia" not in source, "Analytics init still references .aquilia directory"
        assert "build" in source, "Analytics init should use build/.cache directory"

    def test_analytics_cache_writes_surp(self):
        """_cache_analysis should write Surp binary format."""
        import inspect

        from aquilia.cli.commands.analytics import DiscoveryAnalytics

        source = inspect.getsource(DiscoveryAnalytics._cache_analysis)
        assert "surp" in source.lower(), "_cache_analysis should write Surp format"

    def test_analytics_cache_reads_surp(self):
        """get_cached_analysis should read Surp binary format."""
        import inspect

        from aquilia.cli.commands.analytics import DiscoveryAnalytics

        source = inspect.getsource(DiscoveryAnalytics.get_cached_analysis)
        assert "surp" in source.lower(), "get_cached_analysis should read Surp format"
        assert "json" in source.lower(), "get_cached_analysis should have JSON fallback"


# ════════════════════════════════════════════════════════════════════════
# MODULE 9: DEPLOY GENERATION SYSTEM
# ════════════════════════════════════════════════════════════════════════


class TestDeployGenNativeIntrospection:
    """Verify deploy generation uses live workspace introspection."""

    def test_get_ctx_uses_workspace_introspector(self, tmp_path):
        from aquilia.cli.commands.deploy_gen import _get_ctx

        (tmp_path / "workspace.py").write_text('Workspace("demo", version="0.1.0")')
        ctx = _get_ctx(tmp_path)
        assert "name" in ctx
        assert "module_count" in ctx

    def test_deploy_gen_module_docstring_mentions_deploy(self):
        import aquilia.cli.commands.deploy_gen as mod

        assert mod.__doc__ is not None
        assert "deploy" in mod.__doc__.lower()
        assert "aq " + "build" not in mod.__doc__

    def test_deploy_options_decorator_exists(self):
        from aquilia.cli.commands.deploy_gen import deploy_options

        assert callable(deploy_options)


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

        with patch("aquilia.cli.commands.deploy_gen.info"), patch("aquilia.cli.commands.deploy_gen.error"):
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
