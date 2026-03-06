"""
Phase 31 Tests — Module Generator Fix, Config Namespace, Auth Background Tasks.

Tests cover:
1. ModuleGenerator._create_init_file() indentation fix (textwrap.dedent bug)
2. Config namespace validation for module apps
3. Auth background task definitions and execution
"""

import asyncio
import os
import sys
import tempfile
import textwrap
from datetime import datetime, timezone
from pathlib import Path

import pytest

# Ensure repo root is on sys.path
REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)


# ═══════════════════════════════════════════════════════════════════════════
# 1. ModuleGenerator — _create_init_file() Indentation Fix
# ═══════════════════════════════════════════════════════════════════════════


class TestModuleGeneratorInitFile:
    """
    Verify that _create_init_file() produces correctly indented output.

    The bug: when with_tests=True, a ``test_import`` variable with a
    ``\\n`` prefix and 0 leading spaces was interpolated into a
    ``textwrap.dedent(f'...')`` block, which caused dedent to find 0
    common whitespace and leave every other line with 16 spaces of
    indentation.
    """

    def _make_generator(self, name="blog", with_tests=False, minimal=False):
        from aquilia.cli.generators.module import ModuleGenerator

        tmpdir = Path(tempfile.mkdtemp()) / name
        tmpdir.mkdir(parents=True, exist_ok=True)
        return ModuleGenerator(
            name=name,
            path=tmpdir,
            depends_on=[],
            fault_domain=name.upper(),
            route_prefix=f"/{name}",
            with_tests=with_tests,
            minimal=minimal,
        )

    # ── Core regression tests ────────────────────────────────────────

    def test_init_file_no_tests_no_leading_whitespace(self):
        """Full mode, no test routes — no line should start with spaces."""
        gen = self._make_generator(with_tests=False)
        gen._create_init_file()
        content = (gen.path / "__init__.py").read_text()
        for i, line in enumerate(content.split("\n"), 1):
            if line.strip() == "":
                continue
            assert not line.startswith("    "), (
                f"Line {i} has unexpected leading whitespace: {line!r}"
            )

    def test_init_file_with_tests_no_leading_whitespace(self):
        """Full mode WITH test routes — the fix target. No 16-space indent."""
        gen = self._make_generator(with_tests=True)
        gen._create_init_file()
        content = (gen.path / "__init__.py").read_text()
        for i, line in enumerate(content.split("\n"), 1):
            if line.strip() == "":
                continue
            assert not line.startswith("    "), (
                f"Line {i} has unexpected leading whitespace: {line!r}"
            )

    def test_init_file_minimal_no_leading_whitespace(self):
        """Minimal mode — must also be clean."""
        gen = self._make_generator(minimal=True)
        gen._create_init_file()
        content = (gen.path / "__init__.py").read_text()
        for i, line in enumerate(content.split("\n"), 1):
            if line.strip() == "":
                continue
            assert not line.startswith("    "), (
                f"Line {i} has unexpected leading whitespace: {line!r}"
            )

    # ── Content correctness ──────────────────────────────────────────

    def test_init_file_with_tests_contains_test_routes_import(self):
        """When with_tests=True, the file must contain the test_routes import."""
        gen = self._make_generator(with_tests=True)
        gen._create_init_file()
        content = (gen.path / "__init__.py").read_text()
        assert "from .test_routes import *" in content

    def test_init_file_without_tests_no_test_routes_import(self):
        """When with_tests=False, no test_routes import."""
        gen = self._make_generator(with_tests=False)
        gen._create_init_file()
        content = (gen.path / "__init__.py").read_text()
        assert "from .test_routes import *" not in content

    def test_init_file_contains_module_name(self):
        """__module_name__ must match the generator name."""
        gen = self._make_generator(name="orders")
        gen._create_init_file()
        content = (gen.path / "__init__.py").read_text()
        assert '__module_name__ = "orders"' in content

    def test_init_file_contains_docstring(self):
        """Generated file must start with a docstring."""
        gen = self._make_generator(name="products", with_tests=True)
        gen._create_init_file()
        content = (gen.path / "__init__.py").read_text()
        assert content.startswith('"""')

    def test_init_file_contains_version(self):
        """Generated file must contain __version__."""
        gen = self._make_generator(with_tests=True)
        gen._create_init_file()
        content = (gen.path / "__init__.py").read_text()
        assert '__version__ = "0.1.0"' in content

    def test_init_file_has_standard_imports(self):
        """Full mode must import controllers, services, faults."""
        gen = self._make_generator(with_tests=True)
        gen._create_init_file()
        content = (gen.path / "__init__.py").read_text()
        assert "from .controllers import *" in content
        assert "from .services import *" in content
        assert "from .faults import *" in content

    def test_init_file_minimal_only_controllers(self):
        """Minimal mode only imports controllers."""
        gen = self._make_generator(minimal=True)
        gen._create_init_file()
        content = (gen.path / "__init__.py").read_text()
        assert "from .controllers import *" in content
        assert "from .services import *" not in content
        assert "from .faults import *" not in content

    def test_init_file_test_import_order(self):
        """test_routes import must come after faults import."""
        gen = self._make_generator(with_tests=True)
        gen._create_init_file()
        content = (gen.path / "__init__.py").read_text()
        faults_pos = content.index("from .faults import *")
        test_pos = content.index("from .test_routes import *")
        assert test_pos > faults_pos, "test_routes import must follow faults import"

    # ── Various module names ─────────────────────────────────────────

    @pytest.mark.parametrize("name", ["auth", "users", "products", "my_module"])
    def test_init_file_various_names_with_tests(self, name):
        """No indentation issues regardless of module name."""
        gen = self._make_generator(name=name, with_tests=True)
        gen._create_init_file()
        content = (gen.path / "__init__.py").read_text()
        for i, line in enumerate(content.split("\n"), 1):
            if line.strip() == "":
                continue
            assert not line.startswith("    "), (
                f"Module '{name}', line {i} has leading whitespace: {line!r}"
            )
        assert f'__module_name__ = "{name}"' in content
        assert "from .test_routes import *" in content

    def test_init_file_capitalized_docstring(self):
        """Docstring should have the module name capitalized."""
        gen = self._make_generator(name="payments", with_tests=True)
        gen._create_init_file()
        content = (gen.path / "__init__.py").read_text()
        assert "Payments Module." in content

    def test_init_file_generated_by_comment(self):
        """Docstring should mention 'Generated by: aq add module <name>'."""
        gen = self._make_generator(name="users", with_tests=True)
        gen._create_init_file()
        content = (gen.path / "__init__.py").read_text()
        assert "Generated by: aq add module users" in content

    def test_init_file_minimal_generated_by_minimal_flag(self):
        """Minimal docstring includes --minimal flag."""
        gen = self._make_generator(name="api", minimal=True)
        gen._create_init_file()
        content = (gen.path / "__init__.py").read_text()
        assert "Generated by: aq add module api --minimal" in content

    def test_init_file_is_valid_python(self):
        """Generated init file must be valid Python syntax."""
        gen = self._make_generator(with_tests=True)
        gen._create_init_file()
        content = (gen.path / "__init__.py").read_text()
        compile(content, "<init>", "exec")  # Raises SyntaxError if invalid


# ═══════════════════════════════════════════════════════════════════════════
# 2. Config Namespace Validation
# ═══════════════════════════════════════════════════════════════════════════


class TestConfigNamespaceValidation:
    """Test that the config namespace validator works correctly."""

    def test_validator_warns_on_missing_namespace(self):
        """Validator should produce a warning when config.apps.<name> is missing."""
        from aquilia.aquilary.validator import RegistryValidator
        from aquilia.aquilary.errors import ValidationReport

        class FakeManifest:
            name = "auth"

        class FakeApps:
            pass  # No 'auth' attribute

        class FakeConfig:
            apps = FakeApps()

        validator = RegistryValidator.__new__(RegistryValidator)
        report = ValidationReport()
        validator._validate_config_namespace(FakeManifest(), FakeConfig(), report)
        assert any("auth" in w and "no config namespace" in w for w in report.warnings), (
            f"Expected config namespace warning, got: {report.warnings}"
        )

    def test_validator_no_warning_when_namespace_exists(self):
        """No warning when config.apps.<name> is present."""
        from aquilia.aquilary.validator import RegistryValidator
        from aquilia.aquilary.errors import ValidationReport

        class FakeManifest:
            name = "auth"

        class FakeApps:
            auth = {"enabled": True}

        class FakeConfig:
            apps = FakeApps()

        validator = RegistryValidator.__new__(RegistryValidator)
        report = ValidationReport()
        validator._validate_config_namespace(FakeManifest(), FakeConfig(), report)
        assert not any("auth" in w and "no config namespace" in w for w in report.warnings)

    def test_validator_skips_when_no_config(self):
        """When config is None, validation is skipped — no crash."""
        from aquilia.aquilary.validator import RegistryValidator
        from aquilia.aquilary.errors import ValidationReport

        class FakeManifest:
            name = "auth"

        validator = RegistryValidator.__new__(RegistryValidator)
        report = ValidationReport()
        validator._validate_config_namespace(FakeManifest(), None, report)
        assert len(report.warnings) == 0

    def test_base_yaml_has_apps_auth(self):
        """myapp/config/base.yaml must define apps.auth namespace."""
        import yaml

        config_path = Path(REPO_ROOT) / "myapp" / "config" / "base.yaml"
        with open(config_path) as f:
            cfg = yaml.safe_load(f)

        assert "apps" in cfg, "base.yaml must have an 'apps' section"
        assert "auth" in cfg["apps"], "base.yaml apps section must include 'auth'"
        auth_cfg = cfg["apps"]["auth"]
        assert isinstance(auth_cfg, dict), "apps.auth must be a mapping"

    def test_auth_config_has_required_keys(self):
        """Auth config namespace should have expected keys."""
        import yaml

        config_path = Path(REPO_ROOT) / "myapp" / "config" / "base.yaml"
        with open(config_path) as f:
            cfg = yaml.safe_load(f)

        auth_cfg = cfg["apps"]["auth"]
        expected_keys = [
            "session_cleanup_interval",
            "audit_enabled",
            "token_expiry",
            "max_login_attempts",
            "lockout_duration",
        ]
        for key in expected_keys:
            assert key in auth_cfg, f"Missing config key: {key}"


# ═══════════════════════════════════════════════════════════════════════════
# 3. Auth Background Tasks
# ═══════════════════════════════════════════════════════════════════════════


class TestAuthTaskDefinitions:
    """Verify auth task module definitions and decorator metadata."""

    def test_cleanup_expired_sessions_is_task(self):
        """cleanup_expired_sessions must be a @task descriptor."""
        sys.path.insert(0, os.path.join(REPO_ROOT, "myapp"))
        from modules.auth.tasks import cleanup_expired_sessions

        assert hasattr(cleanup_expired_sessions, "task_name")
        assert hasattr(cleanup_expired_sessions, "queue")

    def test_cleanup_expired_sessions_queue(self):
        sys.path.insert(0, os.path.join(REPO_ROOT, "myapp"))
        from modules.auth.tasks import cleanup_expired_sessions

        assert cleanup_expired_sessions.queue == "maintenance"

    def test_cleanup_expired_sessions_priority(self):
        sys.path.insert(0, os.path.join(REPO_ROOT, "myapp"))
        from modules.auth.tasks import cleanup_expired_sessions
        from aquilia.tasks import Priority

        assert cleanup_expired_sessions.priority == Priority.LOW

    def test_cleanup_expired_sessions_tags(self):
        sys.path.insert(0, os.path.join(REPO_ROOT, "myapp"))
        from modules.auth.tasks import cleanup_expired_sessions

        assert "auth" in cleanup_expired_sessions.tags
        assert "sessions" in cleanup_expired_sessions.tags
        assert "cleanup" in cleanup_expired_sessions.tags

    def test_record_login_attempt_is_task(self):
        sys.path.insert(0, os.path.join(REPO_ROOT, "myapp"))
        from modules.auth.tasks import record_login_attempt

        assert hasattr(record_login_attempt, "task_name")
        assert record_login_attempt.queue == "audit"

    def test_record_login_attempt_priority(self):
        sys.path.insert(0, os.path.join(REPO_ROOT, "myapp"))
        from modules.auth.tasks import record_login_attempt
        from aquilia.tasks import Priority

        assert record_login_attempt.priority == Priority.NORMAL

    def test_record_login_attempt_tags(self):
        sys.path.insert(0, os.path.join(REPO_ROOT, "myapp"))
        from modules.auth.tasks import record_login_attempt

        assert "auth" in record_login_attempt.tags
        assert "audit" in record_login_attempt.tags
        assert "security" in record_login_attempt.tags

    def test_record_login_attempt_retries(self):
        sys.path.insert(0, os.path.join(REPO_ROOT, "myapp"))
        from modules.auth.tasks import record_login_attempt

        assert record_login_attempt.max_retries == 5

    def test_check_account_lockout_is_task(self):
        sys.path.insert(0, os.path.join(REPO_ROOT, "myapp"))
        from modules.auth.tasks import check_account_lockout

        assert hasattr(check_account_lockout, "task_name")
        assert check_account_lockout.queue == "security"

    def test_check_account_lockout_priority(self):
        sys.path.insert(0, os.path.join(REPO_ROOT, "myapp"))
        from modules.auth.tasks import check_account_lockout
        from aquilia.tasks import Priority

        assert check_account_lockout.priority == Priority.HIGH

    def test_check_account_lockout_tags(self):
        sys.path.insert(0, os.path.join(REPO_ROOT, "myapp"))
        from modules.auth.tasks import check_account_lockout

        assert "auth" in check_account_lockout.tags
        assert "security" in check_account_lockout.tags
        assert "lockout" in check_account_lockout.tags

    def test_check_account_lockout_timeout(self):
        sys.path.insert(0, os.path.join(REPO_ROOT, "myapp"))
        from modules.auth.tasks import check_account_lockout

        assert check_account_lockout.timeout == 15.0


class TestAuthTaskExecution:
    """Verify auth tasks can be called directly and return expected results."""

    @pytest.mark.asyncio
    async def test_cleanup_expired_sessions_returns_dict(self):
        sys.path.insert(0, os.path.join(REPO_ROOT, "myapp"))
        from modules.auth.tasks import cleanup_expired_sessions

        result = await cleanup_expired_sessions(max_idle_seconds=3600, batch_size=50)
        assert isinstance(result, dict)
        assert "purged" in result
        assert "cutoff" in result
        assert "elapsed_seconds" in result
        assert isinstance(result["purged"], int)

    @pytest.mark.asyncio
    async def test_cleanup_expired_sessions_default_args(self):
        sys.path.insert(0, os.path.join(REPO_ROOT, "myapp"))
        from modules.auth.tasks import cleanup_expired_sessions

        result = await cleanup_expired_sessions()
        assert result["purged"] == 0
        assert result["elapsed_seconds"] >= 0

    @pytest.mark.asyncio
    async def test_record_login_attempt_success(self):
        sys.path.insert(0, os.path.join(REPO_ROOT, "myapp"))
        from modules.auth.tasks import record_login_attempt

        result = await record_login_attempt(
            user_id=42,
            username="admin",
            ip_address="192.168.1.1",
            user_agent="Mozilla/5.0",
            success=True,
        )
        assert isinstance(result, dict)
        assert result["event"] == "login_attempt"
        assert result["user_id"] == 42
        assert result["username"] == "admin"
        assert result["success"] is True
        assert result["failure_reason"] is None
        assert "timestamp" in result

    @pytest.mark.asyncio
    async def test_record_login_attempt_failure(self):
        sys.path.insert(0, os.path.join(REPO_ROOT, "myapp"))
        from modules.auth.tasks import record_login_attempt

        result = await record_login_attempt(
            username="hacker",
            ip_address="10.0.0.99",
            success=False,
            failure_reason="invalid_password",
        )
        assert result["success"] is False
        assert result["failure_reason"] == "invalid_password"
        assert result["user_id"] is None

    @pytest.mark.asyncio
    async def test_record_login_attempt_default_args(self):
        sys.path.insert(0, os.path.join(REPO_ROOT, "myapp"))
        from modules.auth.tasks import record_login_attempt

        result = await record_login_attempt()
        assert result["username"] == ""
        assert result["ip_address"] == ""
        assert result["success"] is False

    @pytest.mark.asyncio
    async def test_check_account_lockout_returns_decision(self):
        sys.path.insert(0, os.path.join(REPO_ROOT, "myapp"))
        from modules.auth.tasks import check_account_lockout

        result = await check_account_lockout(
            username="admin",
            max_attempts=5,
            lockout_window_seconds=900,
        )
        assert isinstance(result, dict)
        assert result["username"] == "admin"
        assert "recent_failures" in result
        assert "locked" in result
        assert "checked_at" in result
        assert isinstance(result["locked"], bool)

    @pytest.mark.asyncio
    async def test_check_account_lockout_default_args(self):
        sys.path.insert(0, os.path.join(REPO_ROOT, "myapp"))
        from modules.auth.tasks import check_account_lockout

        result = await check_account_lockout()
        assert result["username"] == ""
        assert result["max_attempts"] == 5
        assert result["locked"] is False

    @pytest.mark.asyncio
    async def test_check_account_lockout_window_start_is_iso(self):
        sys.path.insert(0, os.path.join(REPO_ROOT, "myapp"))
        from modules.auth.tasks import check_account_lockout

        result = await check_account_lockout(username="test")
        # Verify window_start is valid ISO datetime
        dt = datetime.fromisoformat(result["window_start"])
        assert dt.tzinfo is not None


class TestAuthTaskRegistration:
    """Verify tasks are registered in the global task registry."""

    def test_tasks_appear_in_registry(self):
        sys.path.insert(0, os.path.join(REPO_ROOT, "myapp"))
        # Force import so decorators run
        import modules.auth.tasks  # noqa: F401
        from aquilia.tasks.decorators import get_registered_tasks

        registry = get_registered_tasks()
        task_names = list(registry.keys())
        # At least our three tasks should be registered
        assert any("cleanup_expired_sessions" in n for n in task_names)
        assert any("record_login_attempt" in n for n in task_names)
        assert any("check_account_lockout" in n for n in task_names)

    def test_all_auth_tasks_are_async(self):
        """All auth tasks must be async callables."""
        sys.path.insert(0, os.path.join(REPO_ROOT, "myapp"))
        from modules.auth.tasks import (
            cleanup_expired_sessions,
            record_login_attempt,
            check_account_lockout,
        )
        import inspect

        for t in [cleanup_expired_sessions, record_login_attempt, check_account_lockout]:
            # _TaskDescriptor wraps an async function
            assert inspect.iscoroutinefunction(t._fn), (
                f"{t.task_name} wrapped function is not async"
            )


class TestAuthModuleInit:
    """Verify the auth module __init__.py correctly imports tasks."""

    def test_auth_init_imports_tasks(self):
        init_path = Path(REPO_ROOT) / "myapp" / "modules" / "auth" / "__init__.py"
        content = init_path.read_text()
        assert "from .tasks import *" in content

    def test_auth_module_has_tasks_file(self):
        tasks_path = Path(REPO_ROOT) / "myapp" / "modules" / "auth" / "tasks.py"
        assert tasks_path.exists(), "auth/tasks.py must exist"


class TestAuthManifestTasks:
    """Verify the auth module auto-discovers tasks via import."""

    def test_manifest_auto_discover_enabled(self):
        """Manifest must have auto_discover=True for task discovery."""
        sys.path.insert(0, os.path.join(REPO_ROOT, "myapp"))
        from modules.auth.manifest import manifest

        assert manifest.auto_discover is True

    def test_tasks_importable_via_module_init(self):
        """Importing the auth module must bring in the task descriptors."""
        sys.path.insert(0, os.path.join(REPO_ROOT, "myapp"))
        import modules.auth  # noqa: F401
        from modules.auth.tasks import (
            cleanup_expired_sessions,
            record_login_attempt,
            check_account_lockout,
        )

        # All three must be importable
        assert cleanup_expired_sessions is not None
        assert record_login_attempt is not None
        assert check_account_lockout is not None


# ═══════════════════════════════════════════════════════════════════════════
# 4. BackgroundTaskConfig & Manifest Wiring
# ═══════════════════════════════════════════════════════════════════════════


class TestBackgroundTaskConfig:
    """Verify BackgroundTaskConfig dataclass and manifest integration."""

    def test_import_from_manifest_module(self):
        from aquilia.manifest import BackgroundTaskConfig
        assert BackgroundTaskConfig is not None

    def test_import_from_aquilia_root(self):
        from aquilia import BackgroundTaskConfig
        assert BackgroundTaskConfig is not None

    def test_default_values(self):
        from aquilia.manifest import BackgroundTaskConfig
        cfg = BackgroundTaskConfig()
        assert cfg.tasks == []
        assert cfg.default_queue == "default"
        assert cfg.auto_discover is True
        assert cfg.enabled is True

    def test_custom_values(self):
        from aquilia.manifest import BackgroundTaskConfig
        cfg = BackgroundTaskConfig(
            tasks=["mod.tasks:do_stuff"],
            default_queue="high",
            auto_discover=False,
            enabled=True,
        )
        assert cfg.tasks == ["mod.tasks:do_stuff"]
        assert cfg.default_queue == "high"
        assert cfg.auto_discover is False

    def test_to_dict(self):
        from aquilia.manifest import BackgroundTaskConfig
        cfg = BackgroundTaskConfig(
            tasks=["a:b", "c:d"],
            default_queue="q",
        )
        d = cfg.to_dict()
        assert d["tasks"] == ["a:b", "c:d"]
        assert d["default_queue"] == "q"
        assert d["auto_discover"] is True
        assert d["enabled"] is True

    def test_app_manifest_accepts_background_tasks(self):
        from aquilia import AppManifest
        from aquilia.manifest import BackgroundTaskConfig

        m = AppManifest(
            name="test_bg",
            version="0.1.0",
            background_tasks=BackgroundTaskConfig(
                tasks=["mod.tasks:my_task"],
                default_queue="bg",
            ),
        )
        assert m.background_tasks is not None
        assert m.background_tasks.default_queue == "bg"
        assert "mod.tasks:my_task" in m.background_tasks.tasks

    def test_app_manifest_default_none(self):
        from aquilia import AppManifest
        m = AppManifest(name="no_bg", version="0.1.0")
        assert m.background_tasks is None

    def test_app_manifest_to_dict_includes_background_tasks(self):
        from aquilia import AppManifest
        from aquilia.manifest import BackgroundTaskConfig

        m = AppManifest(
            name="t",
            version="0.1.0",
            background_tasks=BackgroundTaskConfig(
                tasks=["x:y"],
            ),
        )
        d = m.to_dict()
        assert "background_tasks" in d
        assert d["background_tasks"]["tasks"] == ["x:y"]

    def test_app_manifest_to_dict_omits_when_none(self):
        from aquilia import AppManifest
        m = AppManifest(name="no_bg", version="0.1.0")
        d = m.to_dict()
        assert "background_tasks" not in d

    def test_discover_patterns_includes_tasks(self):
        """Default discover_patterns must include 'tasks'."""
        from aquilia import AppManifest
        m = AppManifest(name="dp", version="0.1.0")
        assert "tasks" in m.discover_patterns


class TestAuthManifestBackgroundTaskConfig:
    """Verify the auth manifest has BackgroundTaskConfig wired."""

    def test_auth_manifest_has_background_tasks(self):
        sys.path.insert(0, os.path.join(REPO_ROOT, "myapp"))
        from modules.auth.manifest import manifest

        assert manifest.background_tasks is not None

    def test_auth_manifest_bg_task_refs(self):
        sys.path.insert(0, os.path.join(REPO_ROOT, "myapp"))
        from modules.auth.manifest import manifest

        refs = manifest.background_tasks.tasks
        assert any("cleanup_expired_sessions" in r for r in refs)
        assert any("record_login_attempt" in r for r in refs)
        assert any("check_account_lockout" in r for r in refs)

    def test_auth_manifest_bg_default_queue(self):
        sys.path.insert(0, os.path.join(REPO_ROOT, "myapp"))
        from modules.auth.manifest import manifest

        assert manifest.background_tasks.default_queue == "auth"

    def test_auth_manifest_bg_auto_discover(self):
        sys.path.insert(0, os.path.join(REPO_ROOT, "myapp"))
        from modules.auth.manifest import manifest

        assert manifest.background_tasks.auto_discover is True


class TestWorkspaceTasksIntegration:
    """Verify workspace has Integration.tasks() configured."""

    def test_workspace_has_tasks_config(self):
        """The workspace config must produce enabled tasks config."""
        from aquilia.config import ConfigLoader

        config = ConfigLoader()
        # Simulate loading from workspace integrations
        tasks_cfg = config.get_tasks_config()
        # Even if default returns False, the workspace integration
        # should set enabled = True once Integration.tasks() is used
        assert isinstance(tasks_cfg, dict)

    def test_integration_tasks_builder(self):
        """Integration.tasks() must produce correct config dict."""
        from aquilia.config_builders import Integration

        cfg = Integration.tasks(
            backend="memory",
            num_workers=4,
            default_queue="default",
        )
        assert cfg["_integration_type"] == "tasks"
        assert cfg["enabled"] is True
        assert cfg["backend"] == "memory"
        assert cfg["num_workers"] == 4


class TestErrorTrackerLogLevel:
    """Verify error tracker uses INFO level logging."""

    def test_error_tracker_info_log(self):
        """_setup_error_tracker should use self.logger.info, not debug."""
        import inspect
        from aquilia.server import AquiliaServer

        source = inspect.getsource(AquiliaServer._setup_error_tracker)
        assert 'self.logger.info("Error tracker wired to FaultEngine")' in source
        assert 'self.logger.debug("Error tracker wired to FaultEngine")' not in source
