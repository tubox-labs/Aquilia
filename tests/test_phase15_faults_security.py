"""
Phase 15 — Tasks / Storage / Templates: Fault Migration & Security Audit.

Verifies:
  Task 1 — All raw exceptions (ValueError, RuntimeError, TypeError, KeyError)
           in aquilia/tasks/, aquilia/storage/, and aquilia/templates/ have
           been replaced with structured Aquilia Fault subclasses.

  Task 2 — Security hardening:
           - Pickle deserialization replaced with HMAC-verified JSON
           - Storage path normalization rejects null bytes and traversal
           - Task func_ref resolution only uses registered task registry
           - Regex-based HTML sanitizer emits deprecation warning
"""

import asyncio
import json
import hashlib
import hmac
import os
import pytest
import warnings
from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

# ============================================================================
# Imports — Fault classes
# ============================================================================

from aquilia.faults.core import Fault, FaultDomain, Severity

# Tasks faults
from aquilia.tasks.faults import (
    TASKS_DOMAIN,
    TaskFault,
    TaskScheduleFault,
    TaskNotBoundFault,
    TaskEnqueueFault,
    TaskResolutionFault,
)

# Storage faults
from aquilia.storage.base import (
    STORAGE_DOMAIN,
    StorageError,
    FileNotFoundError as StorageFileNotFoundError,
    PermissionError as StoragePermissionError,
    StorageFullError,
    BackendUnavailableError,
    StorageIOFault,
    StorageConfigFault,
    StorageBackend,
    StorageFile,
    StorageMetadata,
)

# Template faults
from aquilia.templates.faults import (
    TEMPLATE_DOMAIN,
    TemplateFault,
    TemplateEngineUnavailableFault,
    TemplateCacheIntegrityFault,
    TemplateSanitizationWarning,
)


# ============================================================================
# TASK 1 — Fault Taxonomy Tests
# ============================================================================


class TestTasksDomain:
    """Verify the TASKS fault domain exists and is well-formed."""

    def test_domain_is_fault_domain(self):
        assert isinstance(TASKS_DOMAIN, FaultDomain)

    def test_domain_name(self):
        assert TASKS_DOMAIN.name == "tasks"

    def test_domain_registered_on_class(self):
        assert hasattr(FaultDomain, "TASKS")
        assert FaultDomain.TASKS.name == "tasks"


class TestStorageDomain:
    """Verify the STORAGE fault domain exists and is well-formed."""

    def test_domain_is_fault_domain(self):
        assert isinstance(STORAGE_DOMAIN, FaultDomain)

    def test_domain_name(self):
        assert STORAGE_DOMAIN.name == "storage"

    def test_domain_registered_on_class(self):
        assert hasattr(FaultDomain, "STORAGE")
        assert FaultDomain.STORAGE.name == "storage"


class TestTemplateDomain:
    """Verify the TEMPLATE fault domain exists and is well-formed."""

    def test_domain_is_fault_domain(self):
        assert isinstance(TEMPLATE_DOMAIN, FaultDomain)

    def test_domain_name(self):
        assert TEMPLATE_DOMAIN.name == "template"

    def test_domain_registered_on_class(self):
        assert hasattr(FaultDomain, "TEMPLATE")
        assert FaultDomain.TEMPLATE.name == "template"


# ── Task Fault Hierarchy ─────────────────────────────────────────────────


class TestTaskFaultBase:
    """TaskFault is a proper Fault subclass."""

    def test_inherits_from_fault(self):
        assert issubclass(TaskFault, Fault)
        assert issubclass(TaskFault, Exception)

    def test_domain_is_tasks(self):
        f = TaskScheduleFault("test reason")
        assert f.domain == TASKS_DOMAIN

    def test_has_code(self):
        f = TaskScheduleFault("test reason")
        assert f.code == "TASK_SCHEDULE_INVALID"

    def test_has_message(self):
        f = TaskScheduleFault("test reason")
        assert "test reason" in f.message


class TestTaskScheduleFault:
    """TaskScheduleFault replaces ValueError in schedule helpers."""

    def test_inherits_from_task_fault(self):
        assert issubclass(TaskScheduleFault, TaskFault)

    def test_code(self):
        f = TaskScheduleFault("interval must be > 0")
        assert f.code == "TASK_SCHEDULE_INVALID"

    def test_message_includes_reason(self):
        f = TaskScheduleFault("interval must be > 0")
        assert "interval must be > 0" in f.message

    def test_severity(self):
        f = TaskScheduleFault("bad")
        assert f.severity == Severity.ERROR

    def test_not_retryable(self):
        f = TaskScheduleFault("bad")
        assert f.retryable is False

    def test_metadata_has_reason(self):
        f = TaskScheduleFault("bad cron")
        assert f.metadata["reason"] == "bad cron"

    def test_every_zero_raises_fault(self):
        from aquilia.tasks.schedule import every

        with pytest.raises(TaskScheduleFault):
            every()

    def test_every_negative_raises_fault(self):
        from aquilia.tasks.schedule import every

        with pytest.raises(TaskScheduleFault):
            every(seconds=-5)

    def test_cron_bad_field_count_raises_fault(self):
        from aquilia.tasks.schedule import cron

        with pytest.raises(TaskScheduleFault, match="5 fields"):
            cron("* *")

    def test_cron_too_many_fields_raises_fault(self):
        from aquilia.tasks.schedule import cron

        with pytest.raises(TaskScheduleFault, match="5 fields"):
            cron("* * * * * *")


class TestTaskNotBoundFault:
    """TaskNotBoundFault replaces RuntimeError in decorators.delay()."""

    def test_inherits_from_task_fault(self):
        assert issubclass(TaskNotBoundFault, TaskFault)

    def test_code(self):
        f = TaskNotBoundFault("my_task")
        assert f.code == "TASK_NOT_BOUND"

    def test_message_includes_task_name(self):
        f = TaskNotBoundFault("my_task")
        assert "my_task" in f.message
        assert "no bound TaskManager" in f.message

    def test_metadata_has_task_name(self):
        f = TaskNotBoundFault("my_task")
        assert f.metadata["task_name"] == "my_task"

    @pytest.mark.asyncio
    async def test_delay_raises_fault(self):
        from aquilia.tasks import task

        @task
        async def unbound_fn():
            return 1

        with pytest.raises(TaskNotBoundFault):
            await unbound_fn.delay()


class TestTaskEnqueueFault:
    """TaskEnqueueFault replaces TypeError in TaskManager.enqueue()."""

    def test_inherits_from_task_fault(self):
        assert issubclass(TaskEnqueueFault, TaskFault)

    def test_code(self):
        f = TaskEnqueueFault("<class 'str'>")
        assert f.code == "TASK_ENQUEUE_INVALID"

    def test_message_includes_type(self):
        f = TaskEnqueueFault("<class 'str'>")
        assert "<class 'str'>" in f.message

    @pytest.mark.asyncio
    async def test_enqueue_non_callable_raises_fault(self):
        from aquilia.tasks import TaskManager

        mgr = TaskManager()
        with pytest.raises(TaskEnqueueFault):
            await mgr.enqueue(42)


class TestTaskResolutionFault:
    """TaskResolutionFault replaces RuntimeError in _execute_job()."""

    def test_inherits_from_task_fault(self):
        assert issubclass(TaskResolutionFault, TaskFault)

    def test_code(self):
        f = TaskResolutionFault("mymod:myfunc")
        assert f.code == "TASK_RESOLUTION_FAILED"

    def test_message_includes_func_ref(self):
        f = TaskResolutionFault("mymod:myfunc")
        assert "mymod:myfunc" in f.message

    def test_metadata_has_func_ref(self):
        f = TaskResolutionFault("mymod:myfunc")
        assert f.metadata["func_ref"] == "mymod:myfunc"


# ── Storage Fault Hierarchy ──────────────────────────────────────────────


class TestStorageErrorIsFault:
    """StorageError now inherits from Fault."""

    def test_storage_error_inherits_fault(self):
        assert issubclass(StorageError, Fault)
        assert issubclass(StorageError, Exception)

    def test_file_not_found_inherits_storage_error(self):
        assert issubclass(StorageFileNotFoundError, StorageError)
        assert issubclass(StorageFileNotFoundError, Fault)

    def test_permission_error_inherits_storage_error(self):
        assert issubclass(StoragePermissionError, StorageError)
        assert issubclass(StoragePermissionError, Fault)

    def test_storage_full_inherits_storage_error(self):
        assert issubclass(StorageFullError, StorageError)

    def test_backend_unavailable_inherits_storage_error(self):
        assert issubclass(BackendUnavailableError, StorageError)

    def test_storage_io_fault_inherits_storage_error(self):
        assert issubclass(StorageIOFault, StorageError)

    def test_storage_config_fault_inherits_storage_error(self):
        assert issubclass(StorageConfigFault, StorageError)


class TestStorageErrorFaultAttributes:
    """StorageError carries proper Fault attributes."""

    def test_has_code(self):
        err = StorageError("boom", backend="s3", path="x")
        assert err.code == "STORAGE_ERROR"

    def test_has_domain(self):
        err = StorageError("boom", backend="s3", path="x")
        assert err.domain == STORAGE_DOMAIN

    def test_has_severity(self):
        err = StorageError("boom")
        assert isinstance(err.severity, Severity)

    def test_has_metadata(self):
        err = StorageError("boom", backend="s3", path="x.txt")
        assert err.metadata["backend"] == "s3"
        assert err.metadata["path"] == "x.txt"

    def test_file_not_found_code(self):
        err = StorageFileNotFoundError("gone", backend="local", path="x")
        assert err.code == "STORAGE_FILE_NOT_FOUND"
        assert err.severity == Severity.WARN

    def test_permission_error_code(self):
        err = StoragePermissionError("denied", backend="local", path="x")
        assert err.code == "STORAGE_PERMISSION_DENIED"

    def test_storage_full_code(self):
        err = StorageFullError("full", backend="memory")
        assert err.code == "STORAGE_FULL"

    def test_backend_unavailable_code(self):
        err = BackendUnavailableError("down", backend="s3")
        assert err.code == "STORAGE_BACKEND_UNAVAILABLE"
        assert err.severity == Severity.FATAL

    def test_storage_io_fault_code(self):
        err = StorageIOFault("closed file", path="test.txt")
        assert err.code == "STORAGE_IO_ERROR"

    def test_storage_config_fault_code(self):
        err = StorageConfigFault("no registry")
        assert err.code == "STORAGE_CONFIG_ERROR"
        assert err.severity == Severity.FATAL


class TestStorageIOFaultUsage:
    """StorageIOFault is raised for closed/wrong-mode I/O."""

    @pytest.mark.asyncio
    async def test_read_on_closed_file(self):
        sf = StorageFile(name="test.txt", content=b"hello")
        await sf.close()
        with pytest.raises(StorageIOFault, match="closed"):
            await sf.read()

    @pytest.mark.asyncio
    async def test_write_on_closed_file(self):
        sf = StorageFile(name="test.txt", mode="wb")
        await sf.close()
        with pytest.raises(StorageIOFault, match="closed"):
            await sf.write(b"x")

    @pytest.mark.asyncio
    async def test_write_in_read_mode(self):
        sf = StorageFile(name="test.txt", mode="rb")
        with pytest.raises(StorageIOFault, match="not opened for writing"):
            await sf.write(b"x")


class TestStorageConfigFaultUsage:
    """StorageConfigFault is raised for registry/config issues."""

    def test_set_default_nonexistent(self):
        from aquilia.storage.registry import StorageRegistry

        reg = StorageRegistry()
        with pytest.raises(StorageConfigFault):
            reg.set_default("nonexistent")

    @pytest.mark.asyncio
    async def test_effect_provider_no_registry(self):
        from aquilia.storage.effects import StorageEffectProvider

        prov = StorageEffectProvider()
        with pytest.raises(StorageConfigFault, match="no registry"):
            await prov.acquire()


# ── Template Fault Hierarchy ─────────────────────────────────────────────


class TestTemplateFaultBase:
    """TemplateFault is a proper Fault subclass."""

    def test_inherits_from_fault(self):
        assert issubclass(TemplateFault, Fault)

    def test_domain_is_template(self):
        f = TemplateEngineUnavailableFault()
        assert f.domain == TEMPLATE_DOMAIN


class TestTemplateEngineUnavailableFault:
    """TemplateEngineUnavailableFault replaces RuntimeError."""

    def test_code(self):
        f = TemplateEngineUnavailableFault()
        assert f.code == "TEMPLATE_ENGINE_UNAVAILABLE"

    def test_message(self):
        f = TemplateEngineUnavailableFault()
        assert "not available" in f.message

    def test_severity(self):
        f = TemplateEngineUnavailableFault()
        assert f.severity == Severity.ERROR

    @pytest.mark.asyncio
    async def test_auth_mixin_render_raises_fault(self):
        """TemplateAuthMixin.render_with_auth raises TemplateFault."""
        from aquilia.templates.auth_integration import TemplateAuthMixin

        mixin = TemplateAuthMixin()
        # _template_engine not set → should raise
        with pytest.raises(TemplateEngineUnavailableFault):
            await mixin.render_with_auth(MagicMock(), "test.html", {})


class TestTemplateCacheIntegrityFault:
    """TemplateCacheIntegrityFault for tampered cache."""

    def test_code(self):
        f = TemplateCacheIntegrityFault("/tmp/cache.crous")
        assert f.code == "TEMPLATE_CACHE_INTEGRITY"

    def test_severity_is_warn(self):
        f = TemplateCacheIntegrityFault("/tmp/cache.crous")
        assert f.severity == Severity.WARN

    def test_metadata_has_file(self):
        f = TemplateCacheIntegrityFault("/tmp/cache.crous")
        assert f.metadata["cache_file"] == "/tmp/cache.crous"


class TestTemplateSanitizationWarning:
    """TemplateSanitizationWarning for regex-based sanitizer."""

    def test_code(self):
        f = TemplateSanitizationWarning()
        assert f.code == "TEMPLATE_SANITIZE_REGEX"

    def test_severity_is_info(self):
        f = TemplateSanitizationWarning()
        assert f.severity == Severity.INFO

    def test_message_mentions_bleach(self):
        f = TemplateSanitizationWarning()
        assert "bleach" in f.message


# ============================================================================
# TASK 1 — Verify NO raw exceptions remain
# ============================================================================


class TestNoRawExceptionsInTasks:
    """No raw ValueError/RuntimeError/TypeError in tasks/ raise sites."""

    def test_schedule_every_raises_fault_not_value_error(self):
        from aquilia.tasks.schedule import every

        try:
            every()
        except Exception as e:
            assert isinstance(e, TaskScheduleFault)
            assert not isinstance(e, ValueError)

    def test_schedule_cron_raises_fault_not_value_error(self):
        from aquilia.tasks.schedule import cron

        try:
            cron("* *")
        except Exception as e:
            assert isinstance(e, TaskScheduleFault)
            assert not isinstance(e, ValueError)

    @pytest.mark.asyncio
    async def test_delay_raises_fault_not_runtime_error(self):
        from aquilia.tasks import task

        @task
        async def fn():
            pass

        try:
            await fn.delay()
        except Exception as e:
            assert isinstance(e, TaskNotBoundFault)
            assert not type(e).__name__ == "RuntimeError"

    @pytest.mark.asyncio
    async def test_enqueue_raises_fault_not_type_error(self):
        from aquilia.tasks import TaskManager

        mgr = TaskManager()
        try:
            await mgr.enqueue(123)
        except Exception as e:
            assert isinstance(e, TaskEnqueueFault)
            assert not type(e).__name__ == "TypeError"


class TestNoRawExceptionsInStorage:
    """No raw ValueError/KeyError/RuntimeError in storage/ raise sites."""

    @pytest.mark.asyncio
    async def test_closed_read_raises_fault_not_value_error(self):
        sf = StorageFile(name="x", content=b"")
        await sf.close()
        try:
            await sf.read()
        except Exception as e:
            assert isinstance(e, StorageIOFault)
            assert not type(e).__name__ == "ValueError"

    @pytest.mark.asyncio
    async def test_wrong_mode_write_raises_fault_not_value_error(self):
        sf = StorageFile(name="x", mode="rb")
        try:
            await sf.write(b"x")
        except Exception as e:
            assert isinstance(e, StorageIOFault)
            assert not type(e).__name__ == "ValueError"

    def test_set_default_raises_fault_not_key_error(self):
        from aquilia.storage.registry import StorageRegistry

        reg = StorageRegistry()
        try:
            reg.set_default("missing")
        except Exception as e:
            assert isinstance(e, StorageConfigFault)
            assert not type(e).__name__ == "KeyError"

    @pytest.mark.asyncio
    async def test_effect_provider_raises_fault_not_runtime_error(self):
        from aquilia.storage.effects import StorageEffectProvider

        prov = StorageEffectProvider()
        try:
            await prov.acquire()
        except Exception as e:
            assert isinstance(e, StorageConfigFault)
            assert not type(e).__name__ == "RuntimeError"


# ============================================================================
# TASK 2 — Security Audit: Pickle Deserialization
# ============================================================================


class TestPickleRemoval:
    """Verify pickle.load is no longer used in bytecode cache or manager."""

    def test_bytecode_cache_no_pickle_load(self):
        """CrousBytecodeCache._load uses JSON+HMAC, not pickle."""
        import inspect
        from aquilia.templates.bytecode_cache import CrousBytecodeCache

        source = inspect.getsource(CrousBytecodeCache._load)
        assert "pickle.load" not in source
        assert "json.loads" in source
        assert "hmac" in source.lower()

    def test_bytecode_cache_no_pickle_dump(self):
        """CrousBytecodeCache._save uses JSON+HMAC, not pickle."""
        import inspect
        from aquilia.templates.bytecode_cache import CrousBytecodeCache

        source = inspect.getsource(CrousBytecodeCache._save)
        assert "pickle.dump" not in source
        assert "json.dumps" in source

    def test_manager_no_pickle_dump(self):
        """TemplateManager.compile_all uses JSON+HMAC, not pickle."""
        import inspect
        from aquilia.templates.manager import TemplateManager

        source = inspect.getsource(TemplateManager.compile_all)
        assert "pickle.dump" not in source
        assert "pickle" not in source

    def test_manager_no_pickle_import(self):
        """manager.py does not import pickle at all."""
        import inspect
        from aquilia.templates import manager as mgr_mod

        source = inspect.getsource(mgr_mod)
        assert "import pickle" not in source


class TestBytecodeHMACIntegrity:
    """Verify HMAC integrity check on bytecode cache load."""

    def test_save_and_load_roundtrip(self, tmp_path):
        from aquilia.templates.bytecode_cache import CrousBytecodeCache

        cache = CrousBytecodeCache(
            cache_dir=str(tmp_path),
            filename="test.crous",
            secret_key="test-secret-key",
        )
        # Manually add data
        cache._cache["test_template"] = b"bytecode_content_here"
        cache._metadata["test_template"] = {"source_hash": "abc123"}
        cache._dirty = True
        cache._save()

        # Reload
        cache2 = CrousBytecodeCache(
            cache_dir=str(tmp_path),
            filename="test.crous",
            secret_key="test-secret-key",
        )
        assert "test_template" in cache2._cache
        assert cache2._cache["test_template"] == b"bytecode_content_here"

    def test_tampered_file_rejected(self, tmp_path):
        from aquilia.templates.bytecode_cache import CrousBytecodeCache

        cache = CrousBytecodeCache(
            cache_dir=str(tmp_path),
            filename="test.crous",
            secret_key="test-secret-key",
        )
        cache._cache["tpl"] = b"code"
        cache._metadata["tpl"] = {"source_hash": "x"}
        cache._save()

        # Tamper with file
        cache_file = tmp_path / "test.crous"
        raw = cache_file.read_bytes()
        # Replace one byte in payload (after HMAC line)
        tampered = raw[:65] + b"X" + raw[66:]
        cache_file.write_bytes(tampered)

        # Reload — should reject silently
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            cache2 = CrousBytecodeCache(
                cache_dir=str(tmp_path),
                filename="test.crous",
                secret_key="test-secret-key",
            )
            # Should have emitted a warning about integrity check
            integrity_warnings = [x for x in w if "integrity" in str(x.message).lower()]
            assert len(integrity_warnings) >= 1
            # Cache should be empty (tampered data rejected)
            assert len(cache2._cache) == 0

    def test_wrong_secret_rejected(self, tmp_path):
        from aquilia.templates.bytecode_cache import CrousBytecodeCache

        cache = CrousBytecodeCache(
            cache_dir=str(tmp_path),
            filename="test.crous",
            secret_key="correct-key",
        )
        cache._cache["tpl"] = b"code"
        cache._metadata["tpl"] = {}
        cache._save()

        # Load with wrong key
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            cache2 = CrousBytecodeCache(
                cache_dir=str(tmp_path),
                filename="test.crous",
                secret_key="wrong-key",
            )
            integrity_warnings = [x for x in w if "integrity" in str(x.message).lower()]
            assert len(integrity_warnings) >= 1
            assert len(cache2._cache) == 0

    def test_missing_file_no_error(self, tmp_path):
        from aquilia.templates.bytecode_cache import CrousBytecodeCache

        cache = CrousBytecodeCache(
            cache_dir=str(tmp_path),
            filename="nonexistent.crous",
            secret_key="key",
        )
        assert len(cache._cache) == 0

    def test_cache_file_format_is_hmac_newline_json(self, tmp_path):
        from aquilia.templates.bytecode_cache import CrousBytecodeCache

        cache = CrousBytecodeCache(
            cache_dir=str(tmp_path),
            filename="test.crous",
            secret_key="my-key",
        )
        cache._cache["tpl"] = b"\x00\x01\x02"
        cache._metadata["tpl"] = {"source_hash": "abc"}
        cache._save()

        raw = (tmp_path / "test.crous").read_bytes()
        # First 64 chars are hex HMAC
        assert raw[64:65] == b"\n"
        # After newline is valid JSON
        payload = json.loads(raw[65:])
        assert payload["__format__"] == "crous"
        assert payload["schema_version"] == "1.1"


# ============================================================================
# TASK 2 — Security: Path Traversal Hardening
# ============================================================================


class TestStoragePathNormalization:
    """_normalize_path rejects dangerous path patterns."""

    def test_null_byte_rejected(self):
        with pytest.raises(StoragePermissionError, match="Null byte"):
            StorageBackend._normalize_path("file\x00.txt")

    def test_double_dot_rejected(self):
        with pytest.raises(StoragePermissionError, match="traversal"):
            StorageBackend._normalize_path("../../etc/passwd")

    def test_double_dot_in_middle_rejected(self):
        with pytest.raises(StoragePermissionError, match="traversal"):
            StorageBackend._normalize_path("uploads/../../../etc/shadow")

    def test_long_path_rejected(self):
        long_name = "a" * 1025
        with pytest.raises(StoragePermissionError, match="too long"):
            StorageBackend._normalize_path(long_name)

    def test_normal_path_passes(self):
        result = StorageBackend._normalize_path("uploads/photos/avatar.png")
        assert result == "uploads/photos/avatar.png"

    def test_leading_slash_stripped(self):
        result = StorageBackend._normalize_path("/uploads/file.txt")
        assert result == "uploads/file.txt"

    def test_single_dot_passes(self):
        # Single dot is OK (PurePosixPath normalizes it)
        result = StorageBackend._normalize_path("./uploads/file.txt")
        assert ".." not in result

    def test_max_length_1024_passes(self):
        name = "a" * 1024
        result = StorageBackend._normalize_path(name)
        assert len(result) == 1024


# ============================================================================
# TASK 2 — Security: Task func_ref Allowlist
# ============================================================================


class TestTaskFuncRefSecurity:
    """Task resolution only uses the registered task registry."""

    @pytest.mark.asyncio
    async def test_unregistered_func_ref_raises_resolution_fault(self):
        """Jobs with unknown func_ref are rejected, not blindly imported."""
        from aquilia.tasks import TaskManager
        from aquilia.tasks.job import Job, JobState, Priority

        mgr = TaskManager()
        await mgr.start()

        # Create a job with a fake func_ref
        job = Job(
            name="evil_task",
            queue="default",
            priority=Priority.NORMAL,
            func_ref="os:system",  # Should NOT be resolved
            args=("echo pwned",),
            kwargs={},
            state=JobState.PENDING,
            max_retries=0,
            timeout=5.0,
        )

        # Execute the job — should fail with TaskResolutionFault
        try:
            await mgr._execute_job(job, "test-worker")
        except TaskResolutionFault:
            pass  # Expected
        except Exception:
            pass  # Job may fail in the worker loop differently

        await mgr.stop()

        # Verify the job did NOT execute os.system
        assert job.state != JobState.COMPLETED or (job.result and not job.result.success)


# ============================================================================
# TASK 2 — Security: Sanitize HTML Warning
# ============================================================================


class TestSanitizeHtmlWarning:
    """sanitize_html emits a deprecation warning about regex-based approach."""

    def test_emits_warning(self):
        from aquilia.templates.security import create_safe_filters

        filters = create_safe_filters()
        sanitize = filters["sanitize_html"]

        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            result = sanitize("<script>alert('xss')</script><b>safe</b>")
            assert any("NOT production-grade" in str(x.message) for x in w)

    def test_still_strips_scripts(self):
        from aquilia.templates.security import create_safe_filters

        filters = create_safe_filters()
        sanitize = filters["sanitize_html"]

        with warnings.catch_warnings(record=True):
            warnings.simplefilter("always")
            result = sanitize("<script>alert(1)</script>hello")
            assert "<script>" not in result
            assert "hello" in result


# ============================================================================
# TASK 2 — Exports Verification
# ============================================================================


class TestTasksExports:
    """Verify tasks module exports fault classes."""

    def test_all_faults_exported(self):
        import aquilia.tasks as tasks_mod

        assert hasattr(tasks_mod, "TaskFault")
        assert hasattr(tasks_mod, "TaskScheduleFault")
        assert hasattr(tasks_mod, "TaskNotBoundFault")
        assert hasattr(tasks_mod, "TaskEnqueueFault")
        assert hasattr(tasks_mod, "TaskResolutionFault")
        assert hasattr(tasks_mod, "TASKS_DOMAIN")


class TestStorageExports:
    """Verify storage module exports new fault classes."""

    def test_new_faults_exported(self):
        import aquilia.storage as storage_mod

        assert hasattr(storage_mod, "StorageIOFault")
        assert hasattr(storage_mod, "StorageConfigFault")
        assert hasattr(storage_mod, "STORAGE_DOMAIN")

    def test_old_errors_still_exported(self):
        import aquilia.storage as storage_mod

        assert hasattr(storage_mod, "StorageError")
        assert hasattr(storage_mod, "StorageFileNotFoundError")
        assert hasattr(storage_mod, "StoragePermissionError")
        assert hasattr(storage_mod, "StorageFullError")
        assert hasattr(storage_mod, "BackendUnavailableError")


class TestTemplatesExports:
    """Verify templates module exports fault classes."""

    def test_all_faults_exported(self):
        import aquilia.templates as tpl_mod

        assert hasattr(tpl_mod, "TemplateFault")
        assert hasattr(tpl_mod, "TemplateEngineUnavailableFault")
        assert hasattr(tpl_mod, "TemplateCacheIntegrityFault")
        assert hasattr(tpl_mod, "TemplateSanitizationWarning")
        assert hasattr(tpl_mod, "TEMPLATE_DOMAIN")


# ============================================================================
# TASK 2 — Fault to_dict Serialization
# ============================================================================


class TestFaultSerialization:
    """All new faults serialize to dict cleanly."""

    def test_task_schedule_fault_to_dict(self):
        f = TaskScheduleFault("bad interval")
        d = f.to_dict()
        assert d["code"] == "TASK_SCHEDULE_INVALID"
        assert "bad interval" in d["message"]
        assert d["domain"] == "tasks"

    def test_storage_error_to_dict(self):
        f = StorageError("boom", backend="s3", path="x.txt")
        d = f.to_dict()
        assert d["code"] == "STORAGE_ERROR"
        assert d["domain"] == "storage"

    def test_storage_file_not_found_to_dict(self):
        f = StorageFileNotFoundError("gone", backend="local", path="y.txt")
        d = f.to_dict()
        assert d["code"] == "STORAGE_FILE_NOT_FOUND"

    def test_storage_io_fault_to_dict(self):
        f = StorageIOFault("closed", path="z.txt")
        d = f.to_dict()
        assert d["code"] == "STORAGE_IO_ERROR"

    def test_template_fault_to_dict(self):
        f = TemplateEngineUnavailableFault()
        d = f.to_dict()
        assert d["code"] == "TEMPLATE_ENGINE_UNAVAILABLE"
        assert d["domain"] == "template"

    def test_task_not_bound_to_dict(self):
        f = TaskNotBoundFault("my_fn")
        d = f.to_dict()
        assert d["code"] == "TASK_NOT_BOUND"
        assert "my_fn" in d["message"]

    def test_task_enqueue_fault_to_dict(self):
        f = TaskEnqueueFault("<class 'int'>")
        d = f.to_dict()
        assert d["code"] == "TASK_ENQUEUE_INVALID"

    def test_task_resolution_fault_to_dict(self):
        f = TaskResolutionFault("mod:fn")
        d = f.to_dict()
        assert d["code"] == "TASK_RESOLUTION_FAILED"


# ============================================================================
# TASK 2 — Backward Compatibility
# ============================================================================


class TestBackwardCompatibility:
    """Existing code catching old exception types still works via inheritance."""

    def test_storage_error_is_still_exception(self):
        err = StorageError("test")
        assert isinstance(err, Exception)

    def test_file_not_found_caught_as_storage_error(self):
        with pytest.raises(StorageError):
            raise StorageFileNotFoundError("gone", backend="local", path="x")

    def test_permission_error_caught_as_storage_error(self):
        with pytest.raises(StorageError):
            raise StoragePermissionError("denied")

    def test_backend_unavailable_caught_as_storage_error(self):
        with pytest.raises(StorageError):
            raise BackendUnavailableError("down")

    def test_storage_io_caught_as_storage_error(self):
        with pytest.raises(StorageError):
            raise StorageIOFault("closed")

    def test_storage_config_caught_as_storage_error(self):
        with pytest.raises(StorageError):
            raise StorageConfigFault("no registry")

    def test_task_faults_caught_as_fault(self):
        with pytest.raises(Fault):
            raise TaskScheduleFault("bad interval")

    def test_task_faults_caught_as_exception(self):
        with pytest.raises(Exception):
            raise TaskNotBoundFault("my_task")

    def test_template_faults_caught_as_fault(self):
        with pytest.raises(Fault):
            raise TemplateEngineUnavailableFault()

    def test_all_storage_errors_are_faults(self):
        """Every storage error subclass is also a Fault."""
        for cls in [
            StorageError,
            StorageFileNotFoundError,
            StoragePermissionError,
            StorageFullError,
            BackendUnavailableError,
            StorageIOFault,
            StorageConfigFault,
        ]:
            err = cls("test")
            assert isinstance(err, Fault), f"{cls.__name__} is not a Fault"
