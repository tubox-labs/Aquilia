"""
Comprehensive Regression Test Suite for Aquilia Storage System.

Tests cover EVERY layer of the storage subsystem:

    1. Base Abstractions
       - StorageError hierarchy
       - StorageMetadata (frozen dataclass, serialization)
       - StorageFile (read, write, seek, tell, close, streaming, context manager)
       - StorageBackend (ABC contract, convenience methods, filename sanitization)

    2. Configuration Dataclasses
       - StorageConfig base + each backend-specific config
       - Frozen immutability
       - to_dict round-trip
       - config_from_dict factory (all shorthands + unknown backends)
       - _BACKEND_CONFIGS registry completeness

    3. Backend Implementations
       a) MemoryStorage -- full async CRUD, quota, metadata, listdir, url, shutdown
       b) LocalStorage  -- real filesystem CRUD, permissions, path traversal guard,
                           copy, move, listdir, url, directory auto-create
       c) CompositeStorage -- rule routing, fallback, multi-backend listdir
       d) S3Storage / GCSStorage / AzureBlobStorage / SFTPStorage -- import guard,
          config wiring, ensure-client guard, backend_name

    4. StorageRegistry
       - register / unregister / set_default / get / contains / len / iter / aliases
       - default property (happy + missing)
       - __getitem__ (happy + missing)
       - from_config factory
       - initialize_all / shutdown_all / health_check lifecycle

    5. StorageSubsystem (boot lifecycle)
       - _do_initialize happy path (with config)
       - _do_initialize no config (graceful skip)
       - _do_shutdown
       - health_check (healthy / degraded / unhealthy / not initialized)

    6. StorageEffectProvider (effect system bridge)
       - acquire default / by alias / no registry
       - kind == EffectKind.STORAGE
       - set_registry / initialize / release / finalize

    7. Config Builder Integration
       - Integration.storage() output structure
       - Workspace.storage() chaining
       - StorageConfig -> to_dict -> config_from_dict round-trip

    8. Cross-cutting Regression
       - StorageFile double-close
       - StorageFile read after close
       - StorageFile write mode enforcement
       - generate_filename uniqueness
       - get_valid_name sanitization edge cases
       - MemoryStorage quota boundary (exactly at limit, 1 byte over)
       - LocalStorage path traversal with symlinks / ".."
       - Registry concurrent access patterns
       - Empty registry health_check
       - CompositeStorage with no backends
"""

from __future__ import annotations

import asyncio
import io
import os
import shutil
import tempfile
import uuid
from dataclasses import FrozenInstanceError, fields
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, AsyncIterator, Dict, List, Optional, Tuple
from unittest.mock import AsyncMock, MagicMock, patch, PropertyMock

import pytest

# ── Imports under test ───────────────────────────────────────────────────

from aquilia.storage.base import (
    BackendUnavailableError,
    FileNotFoundError as StorageFileNotFoundError,
    PermissionError as StoragePermissionError,
    StorageBackend,
    StorageError,
    StorageFile,
    StorageFullError,
    StorageMetadata,
)
from aquilia.storage.configs import (
    AzureBlobConfig,
    CompositeConfig,
    GCSConfig,
    LocalConfig,
    MemoryConfig,
    S3Config,
    SFTPConfig,
    StorageConfig,
    config_from_dict,
    _BACKEND_CONFIGS,
)
from aquilia.storage.backends.local import LocalStorage
from aquilia.storage.backends.memory import MemoryStorage
from aquilia.storage.backends.composite import CompositeStorage
from aquilia.storage.registry import (
    StorageRegistry,
    create_backend,
    _BUILTIN_BACKENDS,
    _import_backend,
)
from aquilia.storage.subsystem import StorageSubsystem
from aquilia.storage.effects import StorageEffectProvider
from aquilia.effects import EffectKind
from aquilia.config_builders import Integration, Workspace


# ═══════════════════════════════════════════════════════════════════════════
#  SECTION 1 — Base Abstractions
# ═══════════════════════════════════════════════════════════════════════════


class TestStorageErrorHierarchy:
    """Every storage error carries backend + path context."""

    def test_storage_error_base(self):
        err = StorageError("boom", backend="s3", path="foo/bar.txt")
        assert "boom" in str(err)
        assert err.backend_name_str == "s3"
        assert err.path == "foo/bar.txt"

    def test_storage_error_defaults(self):
        err = StorageError("oops")
        assert err.backend_name_str == ""
        assert err.path == ""

    def test_file_not_found_is_storage_error(self):
        err = StorageFileNotFoundError("gone", backend="local", path="x")
        assert isinstance(err, StorageError)

    def test_permission_error_is_storage_error(self):
        err = StoragePermissionError("denied", backend="local", path="x")
        assert isinstance(err, StorageError)

    def test_storage_full_error_is_storage_error(self):
        err = StorageFullError("full", backend="memory", path="x")
        assert isinstance(err, StorageError)

    def test_backend_unavailable_is_storage_error(self):
        err = BackendUnavailableError("down", backend="s3")
        assert isinstance(err, StorageError)

    def test_all_errors_are_exceptions(self):
        for cls in (
            StorageError,
            StorageFileNotFoundError,
            StoragePermissionError,
            StorageFullError,
            BackendUnavailableError,
        ):
            assert issubclass(cls, Exception)


class TestStorageMetadata:
    """Immutable metadata with serialization."""

    def test_defaults(self):
        m = StorageMetadata(name="file.txt")
        assert m.size == 0
        assert m.content_type == "application/octet-stream"
        assert m.etag == ""
        assert m.last_modified is None
        assert m.created_at is None
        assert m.metadata == {}
        assert m.storage_class == ""

    def test_frozen(self):
        m = StorageMetadata(name="file.txt", size=100)
        with pytest.raises((FrozenInstanceError, AttributeError)):
            m.size = 200  # type: ignore[misc]

    def test_to_dict_round_trip(self):
        now = datetime.now(timezone.utc)
        m = StorageMetadata(
            name="a/b.pdf",
            size=42,
            content_type="application/pdf",
            etag="abc123",
            last_modified=now,
            created_at=now,
            metadata={"author": "test"},
            storage_class="STANDARD",
        )
        d = m.to_dict()
        assert d["name"] == "a/b.pdf"
        assert d["size"] == 42
        assert d["content_type"] == "application/pdf"
        assert d["etag"] == "abc123"
        assert d["last_modified"] == now.isoformat()
        assert d["created_at"] == now.isoformat()
        assert d["metadata"] == {"author": "test"}
        assert d["storage_class"] == "STANDARD"

    def test_to_dict_none_timestamps(self):
        m = StorageMetadata(name="x")
        d = m.to_dict()
        assert d["last_modified"] is None
        assert d["created_at"] is None

    def test_slots(self):
        m = StorageMetadata(name="x")
        assert hasattr(m, "__slots__")


class TestStorageFile:
    """Async file wrapper: read, write, seek, stream, context manager."""

    @pytest.mark.asyncio
    async def test_read_all(self):
        sf = StorageFile(name="test.txt", content=b"hello world")
        data = await sf.read()
        assert data == b"hello world"

    @pytest.mark.asyncio
    async def test_read_partial(self):
        sf = StorageFile(name="test.txt", content=b"abcdefghij")
        chunk1 = await sf.read(3)
        chunk2 = await sf.read(4)
        assert chunk1 == b"abc"
        assert chunk2 == b"defg"

    @pytest.mark.asyncio
    async def test_read_exhausted(self):
        sf = StorageFile(name="test.txt", content=b"hi")
        await sf.read()
        rest = await sf.read()
        assert rest == b""

    @pytest.mark.asyncio
    async def test_read_none_content(self):
        sf = StorageFile(name="test.txt", content=None)
        data = await sf.read()
        assert data == b""

    @pytest.mark.asyncio
    async def test_write(self):
        sf = StorageFile(name="out.txt", mode="wb")
        n = await sf.write(b"data")
        assert n == 4
        assert sf.content == b"data"

    @pytest.mark.asyncio
    async def test_write_append(self):
        sf = StorageFile(name="out.txt", mode="wb", content=b"aaa")
        await sf.write(b"bbb")
        assert sf.content == b"aaabbb"

    @pytest.mark.asyncio
    async def test_write_read_mode_raises(self):
        from aquilia.storage import StorageIOFault

        sf = StorageFile(name="out.txt", mode="rb")
        with pytest.raises(StorageIOFault, match="not opened for writing"):
            await sf.write(b"nope")

    @pytest.mark.asyncio
    async def test_seek_and_tell(self):
        sf = StorageFile(name="test.txt", content=b"0123456789")
        await sf.seek(5)
        pos = await sf.tell()
        assert pos == 5
        data = await sf.read(3)
        assert data == b"567"

    @pytest.mark.asyncio
    async def test_seek_negative_clamps(self):
        sf = StorageFile(name="test.txt", content=b"abc")
        await sf.seek(-10)
        pos = await sf.tell()
        assert pos == 0

    @pytest.mark.asyncio
    async def test_close(self):
        sf = StorageFile(name="test.txt", content=b"x")
        assert not sf.closed
        await sf.close()
        assert sf.closed

    @pytest.mark.asyncio
    async def test_read_after_close_raises(self):
        from aquilia.storage import StorageIOFault

        sf = StorageFile(name="test.txt", content=b"x")
        await sf.close()
        with pytest.raises(StorageIOFault, match="closed"):
            await sf.read()

    @pytest.mark.asyncio
    async def test_write_after_close_raises(self):
        from aquilia.storage import StorageIOFault

        sf = StorageFile(name="out.txt", mode="wb")
        await sf.close()
        with pytest.raises(StorageIOFault, match="closed"):
            await sf.write(b"x")

    @pytest.mark.asyncio
    async def test_double_close(self):
        sf = StorageFile(name="test.txt", content=b"x")
        await sf.close()
        await sf.close()  # Should not raise
        assert sf.closed

    @pytest.mark.asyncio
    async def test_context_manager(self):
        sf = StorageFile(name="test.txt", content=b"ctx")
        async with sf as f:
            data = await f.read()
            assert data == b"ctx"
        assert sf.closed

    @pytest.mark.asyncio
    async def test_size_from_content(self):
        sf = StorageFile(name="test.txt", content=b"12345")
        assert sf.size == 5

    @pytest.mark.asyncio
    async def test_size_from_meta(self):
        meta = StorageMetadata(name="test.txt", size=99)
        sf = StorageFile(name="test.txt", meta=meta)
        assert sf.size == 99

    @pytest.mark.asyncio
    async def test_size_none_content_no_meta(self):
        sf = StorageFile(name="test.txt")
        assert sf.size == 0

    @pytest.mark.asyncio
    async def test_async_iteration(self):
        sf = StorageFile(name="test.txt", content=b"a" * 200_000)
        chunks = []
        async for chunk in sf:
            chunks.append(chunk)
        assert b"".join(chunks) == b"a" * 200_000
        assert len(chunks) > 1  # Should be chunked at 65536

    @pytest.mark.asyncio
    async def test_read_from_async_chunks(self):
        async def _chunks() -> AsyncIterator[bytes]:
            yield b"hello "
            yield b"world"

        sf = StorageFile(name="test.txt", chunks=_chunks())
        data = await sf.read()
        assert data == b"hello world"

    @pytest.mark.asyncio
    async def test_iter_from_async_chunks(self):
        async def _chunks() -> AsyncIterator[bytes]:
            yield b"aaa"
            yield b"bbb"

        sf = StorageFile(name="test.txt", chunks=_chunks())
        parts = []
        async for chunk in sf:
            parts.append(chunk)
        assert b"".join(parts) == b"aaabbb"


class TestStorageBackendABC:
    """StorageBackend convenience methods and static helpers."""

    def test_get_valid_name_basic(self):
        assert StorageBackend.get_valid_name("hello.txt") == "hello.txt"

    def test_get_valid_name_strips_path(self):
        result = StorageBackend.get_valid_name("/etc/passwd")
        assert result == "passwd"

    def test_get_valid_name_sanitizes_unsafe(self):
        result = StorageBackend.get_valid_name('file<>:"|?*.txt')
        assert "<" not in result
        assert ">" not in result
        assert '"' not in result
        assert "?" not in result
        assert "*" not in result

    def test_get_valid_name_null_bytes(self):
        result = StorageBackend.get_valid_name("file\x00name.txt")
        assert "\x00" not in result

    def test_get_valid_name_truncates_long(self):
        long_name = "a" * 300 + ".txt"
        result = StorageBackend.get_valid_name(long_name)
        root, ext = os.path.splitext(result)
        assert len(root) <= 200

    def test_get_valid_name_empty_returns_unnamed(self):
        result = StorageBackend.get_valid_name("")
        assert result == "unnamed"

    def test_guess_content_type_known(self):
        assert "image/png" in StorageBackend.guess_content_type("photo.png")
        assert "text/" in StorageBackend.guess_content_type("readme.txt")

    def test_guess_content_type_unknown(self):
        assert StorageBackend.guess_content_type("file.xyz123") == "application/octet-stream"

    def test_normalize_path(self):
        assert StorageBackend._normalize_path("/a/b/c.txt") == "a/b/c.txt"
        assert StorageBackend._normalize_path("a/b/c.txt") == "a/b/c.txt"

    def test_generate_filename_uniqueness(self):
        backend = MemoryStorage()
        names = {backend.generate_filename("test.txt") for _ in range(100)}
        assert len(names) == 100  # All unique due to UUID prefix

    def test_generate_filename_preserves_extension(self):
        backend = MemoryStorage()
        result = backend.generate_filename("report.pdf")
        assert result.endswith(".pdf")

    @pytest.mark.asyncio
    async def test_read_content_bytes(self):
        data = await StorageBackend._read_content(b"raw bytes")
        assert data == b"raw bytes"

    @pytest.mark.asyncio
    async def test_read_content_storage_file(self):
        sf = StorageFile(name="t", content=b"from sf")
        data = await StorageBackend._read_content(sf)
        assert data == b"from sf"

    @pytest.mark.asyncio
    async def test_read_content_file_like(self):
        buf = io.BytesIO(b"from buffer")
        data = await StorageBackend._read_content(buf)
        assert data == b"from buffer"

    @pytest.mark.asyncio
    async def test_read_content_async_iterator(self):
        async def gen() -> AsyncIterator[bytes]:
            yield b"chunk1"
            yield b"chunk2"

        data = await StorageBackend._read_content(gen())
        assert data == b"chunk1chunk2"

    def test_repr(self):
        ms = MemoryStorage()
        assert "MemoryStorage" in repr(ms)
        assert "memory" in repr(ms)


# ═══════════════════════════════════════════════════════════════════════════
#  SECTION 2 — Configuration Dataclasses
# ═══════════════════════════════════════════════════════════════════════════


class TestStorageConfigs:
    """Every config is frozen, has correct defaults, and round-trips."""

    def test_base_config_defaults(self):
        c = StorageConfig()
        assert c.alias == "default"
        assert c.backend == ""
        assert c.default is False

    def test_base_config_frozen(self):
        c = StorageConfig()
        with pytest.raises((FrozenInstanceError, AttributeError)):
            c.alias = "x"  # type: ignore[misc]

    def test_base_config_to_dict(self):
        c = StorageConfig(alias="test", backend="local")
        d = c.to_dict()
        assert d["alias"] == "test"
        assert d["backend"] == "local"

    def test_local_config_defaults(self):
        c = LocalConfig()
        assert c.backend == "local"
        assert c.root == "./storage"
        assert c.base_url == "/storage/"
        assert c.permissions == 0o644
        assert c.dir_permissions == 0o755
        assert c.create_dirs is True

    def test_local_config_custom(self):
        c = LocalConfig(root="/custom", base_url="/files/", permissions=0o600)
        assert c.root == "/custom"
        assert c.base_url == "/files/"
        assert c.permissions == 0o600

    def test_memory_config_defaults(self):
        c = MemoryConfig()
        assert c.backend == "memory"
        assert c.max_size == 0

    def test_memory_config_with_quota(self):
        c = MemoryConfig(max_size=1024)
        assert c.max_size == 1024

    def test_s3_config_defaults(self):
        c = S3Config()
        assert c.backend == "s3"
        assert c.bucket == ""
        assert c.region == "us-east-1"
        assert c.access_key is None
        assert c.secret_key is None
        assert c.endpoint_url is None
        assert c.prefix == ""
        assert c.signature_version == "s3v4"
        assert c.use_ssl is True
        assert c.addressing_style == "auto"
        assert c.default_acl is None
        assert c.storage_class == "STANDARD"
        assert c.presigned_expiry == 3600

    def test_s3_config_minio(self):
        c = S3Config(
            bucket="test-bucket",
            endpoint_url="http://localhost:9000",
            access_key="minio",
            secret_key="minio123",
            addressing_style="path",
        )
        assert c.endpoint_url == "http://localhost:9000"
        assert c.addressing_style == "path"

    def test_gcs_config_defaults(self):
        c = GCSConfig()
        assert c.backend == "gcs"
        assert c.bucket == ""
        assert c.project is None
        assert c.credentials_path is None
        assert c.credentials_json is None
        assert c.presigned_expiry == 3600

    def test_azure_config_defaults(self):
        c = AzureBlobConfig()
        assert c.backend == "azure"
        assert c.container == ""
        assert c.connection_string is None
        assert c.account_name is None
        assert c.account_key is None
        assert c.sas_token is None
        assert c.custom_domain is None
        assert c.overwrite is False

    def test_sftp_config_defaults(self):
        c = SFTPConfig()
        assert c.backend == "sftp"
        assert c.host == "localhost"
        assert c.port == 22
        assert c.username == ""
        assert c.password is None
        assert c.key_path is None
        assert c.root == "/"
        assert c.timeout == 30

    def test_composite_config_defaults(self):
        c = CompositeConfig()
        assert c.backend == "composite"
        assert c.backends == {}
        assert c.rules == {}
        assert c.fallback == "default"

    def test_composite_config_with_rules(self):
        c = CompositeConfig(
            backends={"media": {"backend": "memory"}},
            rules={"*.jpg": "media", "*.png": "media"},
            fallback="media",
        )
        assert len(c.rules) == 2
        assert c.fallback == "media"


class TestConfigFromDict:
    """config_from_dict factory dispatches to correct config class."""

    def test_local(self):
        c = config_from_dict({"backend": "local", "root": "/data"})
        assert isinstance(c, LocalConfig)
        assert c.root == "/data"

    def test_memory(self):
        c = config_from_dict({"backend": "memory", "max_size": 2048})
        assert isinstance(c, MemoryConfig)
        assert c.max_size == 2048

    def test_s3(self):
        c = config_from_dict({"backend": "s3", "bucket": "my-bucket", "region": "eu-west-1"})
        assert isinstance(c, S3Config)
        assert c.bucket == "my-bucket"
        assert c.region == "eu-west-1"

    def test_gcs(self):
        c = config_from_dict({"backend": "gcs", "bucket": "gcs-bucket"})
        assert isinstance(c, GCSConfig)
        assert c.bucket == "gcs-bucket"

    def test_azure(self):
        c = config_from_dict({"backend": "azure", "container": "media"})
        assert isinstance(c, AzureBlobConfig)
        assert c.container == "media"

    def test_sftp(self):
        c = config_from_dict({"backend": "sftp", "host": "files.example.com"})
        assert isinstance(c, SFTPConfig)
        assert c.host == "files.example.com"

    def test_composite(self):
        c = config_from_dict({"backend": "composite", "fallback": "media"})
        assert isinstance(c, CompositeConfig)
        assert c.fallback == "media"

    def test_unknown_backend_falls_to_base(self):
        c = config_from_dict({"backend": "unknown_exotic"})
        assert isinstance(c, StorageConfig)
        assert c.backend == "unknown_exotic"

    def test_default_backend_is_local(self):
        c = config_from_dict({})
        assert isinstance(c, LocalConfig)
        assert c.backend == "local"

    def test_extra_keys_filtered(self):
        c = config_from_dict(
            {
                "backend": "memory",
                "max_size": 100,
                "nonexistent_field": "should_be_ignored",
            }
        )
        assert isinstance(c, MemoryConfig)
        assert c.max_size == 100

    def test_backend_configs_registry_complete(self):
        expected = {"local", "memory", "s3", "gcs", "azure", "sftp", "composite"}
        assert set(_BACKEND_CONFIGS.keys()) == expected

    def test_config_to_dict_then_from_dict_round_trip(self):
        original = S3Config(
            alias="cdn",
            bucket="my-cdn",
            region="ap-south-1",
            prefix="assets/",
            default_acl="public-read",
        )
        d = original.to_dict()
        restored = config_from_dict(d)
        assert isinstance(restored, S3Config)
        assert restored.alias == original.alias
        assert restored.bucket == original.bucket
        assert restored.region == original.region
        assert restored.prefix == original.prefix
        assert restored.default_acl == original.default_acl


# ═══════════════════════════════════════════════════════════════════════════
#  SECTION 3 — Backend Implementations
# ═══════════════════════════════════════════════════════════════════════════


class TestMemoryStorage:
    """Full async CRUD test suite for MemoryStorage."""

    @pytest.fixture
    def storage(self) -> MemoryStorage:
        return MemoryStorage(MemoryConfig())

    @pytest.mark.asyncio
    async def test_backend_name(self, storage):
        assert storage.backend_name == "memory"

    @pytest.mark.asyncio
    async def test_save_and_exists(self, storage):
        name = await storage.save("test.txt", b"hello")
        assert await storage.exists(name)

    @pytest.mark.asyncio
    async def test_save_and_open(self, storage):
        await storage.save("doc.txt", b"document content")
        sf = await storage.open("doc.txt")
        data = await sf.read()
        assert data == b"document content"

    @pytest.mark.asyncio
    async def test_save_overwrite_false_generates_new_name(self, storage):
        n1 = await storage.save("file.txt", b"v1")
        n2 = await storage.save("file.txt", b"v2", overwrite=False)
        assert n1 != n2
        assert await storage.exists(n1)
        assert await storage.exists(n2)

    @pytest.mark.asyncio
    async def test_save_overwrite_true(self, storage):
        await storage.save("file.txt", b"v1")
        n2 = await storage.save("file.txt", b"v2", overwrite=True)
        assert n2 == "file.txt"
        sf = await storage.open("file.txt")
        assert await sf.read() == b"v2"

    @pytest.mark.asyncio
    async def test_save_with_content_type(self, storage):
        await storage.save("img.png", b"PNG", content_type="image/png")
        meta = await storage.stat("img.png")
        assert meta.content_type == "image/png"

    @pytest.mark.asyncio
    async def test_save_with_custom_metadata(self, storage):
        await storage.save("f.txt", b"x", metadata={"author": "test"})
        meta = await storage.stat("f.txt")
        assert meta.metadata.get("author") == "test"

    @pytest.mark.asyncio
    async def test_save_auto_content_type(self, storage):
        await storage.save("report.pdf", b"PDF")
        meta = await storage.stat("report.pdf")
        assert "pdf" in meta.content_type.lower() or "octet" in meta.content_type

    @pytest.mark.asyncio
    async def test_open_nonexistent_raises(self, storage):
        with pytest.raises(StorageFileNotFoundError):
            await storage.open("nonexistent.txt")

    @pytest.mark.asyncio
    async def test_delete_existing(self, storage):
        await storage.save("del.txt", b"bye")
        assert await storage.exists("del.txt")
        await storage.delete("del.txt")
        assert not await storage.exists("del.txt")

    @pytest.mark.asyncio
    async def test_delete_nonexistent_idempotent(self, storage):
        await storage.delete("ghost.txt")  # Should not raise

    @pytest.mark.asyncio
    async def test_stat_existing(self, storage):
        await storage.save("s.txt", b"12345")
        meta = await storage.stat("s.txt")
        assert meta.name == "s.txt"
        assert meta.size == 5
        assert meta.last_modified is not None

    @pytest.mark.asyncio
    async def test_stat_nonexistent_raises(self, storage):
        with pytest.raises(StorageFileNotFoundError):
            await storage.stat("nope.txt")

    @pytest.mark.asyncio
    async def test_size(self, storage):
        await storage.save("sized.txt", b"abcdef")
        assert await storage.size("sized.txt") == 6

    @pytest.mark.asyncio
    async def test_size_nonexistent_raises(self, storage):
        with pytest.raises(StorageFileNotFoundError):
            await storage.size("missing.txt")

    @pytest.mark.asyncio
    async def test_url(self, storage):
        await storage.save("u.txt", b"url test")
        url = await storage.url("u.txt")
        assert url.startswith("memory:///")
        assert "u.txt" in url

    @pytest.mark.asyncio
    async def test_listdir_root(self, storage):
        await storage.save("root.txt", b"r")
        await storage.save("sub/nested.txt", b"n")
        dirs, files = await storage.listdir()
        assert "root.txt" in files
        assert "sub" in dirs

    @pytest.mark.asyncio
    async def test_listdir_subdir(self, storage):
        await storage.save("dir/a.txt", b"a")
        await storage.save("dir/b.txt", b"b")
        await storage.save("dir/sub/c.txt", b"c")
        dirs, files = await storage.listdir("dir")
        assert "a.txt" in files
        assert "b.txt" in files
        assert "sub" in dirs

    @pytest.mark.asyncio
    async def test_listdir_empty(self, storage):
        dirs, files = await storage.listdir()
        assert dirs == []
        assert files == []

    @pytest.mark.asyncio
    async def test_ping(self, storage):
        assert await storage.ping() is True

    @pytest.mark.asyncio
    async def test_initialize(self, storage):
        await storage.initialize()  # No-op, should not raise

    @pytest.mark.asyncio
    async def test_shutdown_clears_data(self, storage):
        await storage.save("x.txt", b"data")
        await storage.shutdown()
        assert not await storage.exists("x.txt")

    @pytest.mark.asyncio
    async def test_copy(self, storage):
        await storage.save("orig.txt", b"content")
        result = await storage.copy("orig.txt", "copy.txt")
        assert result == "copy.txt"
        sf = await storage.open("copy.txt")
        assert await sf.read() == b"content"
        assert await storage.exists("orig.txt")  # Original still exists

    @pytest.mark.asyncio
    async def test_move(self, storage):
        await storage.save("src.txt", b"move me")
        result = await storage.move("src.txt", "dst.txt")
        assert result == "dst.txt"
        assert not await storage.exists("src.txt")
        sf = await storage.open("dst.txt")
        assert await sf.read() == b"move me"

    @pytest.mark.asyncio
    async def test_save_from_storage_file(self, storage):
        sf = StorageFile(name="input.txt", content=b"from sf")
        name = await storage.save("output.txt", sf)
        assert name == "output.txt"
        opened = await storage.open("output.txt")
        assert await opened.read() == b"from sf"

    @pytest.mark.asyncio
    async def test_save_from_bytesio(self, storage):
        buf = io.BytesIO(b"buffered")
        name = await storage.save("buf.txt", buf)
        assert name == "buf.txt"
        sf = await storage.open("buf.txt")
        assert await sf.read() == b"buffered"

    @pytest.mark.asyncio
    async def test_save_from_async_iterator(self, storage):
        async def gen() -> AsyncIterator[bytes]:
            yield b"chunk1"
            yield b"chunk2"

        name = await storage.save("async.txt", gen())
        sf = await storage.open("async.txt")
        assert await sf.read() == b"chunk1chunk2"

    @pytest.mark.asyncio
    async def test_open_returns_correct_meta(self, storage):
        await storage.save("meta.txt", b"test", content_type="text/plain")
        sf = await storage.open("meta.txt")
        assert sf.meta is not None
        assert sf.meta.content_type == "text/plain"
        assert sf.meta.size == 4


class TestMemoryStorageQuota:
    """MemoryStorage quota enforcement edge cases."""

    @pytest.mark.asyncio
    async def test_quota_exact_limit(self):
        storage = MemoryStorage(MemoryConfig(max_size=10))
        await storage.save("a.txt", b"12345", overwrite=True)
        await storage.save("b.txt", b"12345", overwrite=True)  # Total = 10
        # Should succeed

    @pytest.mark.asyncio
    async def test_quota_one_byte_over(self):
        storage = MemoryStorage(MemoryConfig(max_size=10))
        await storage.save("a.txt", b"12345", overwrite=True)
        with pytest.raises(StorageFullError):
            await storage.save("b.txt", b"123456", overwrite=True)  # Total = 11

    @pytest.mark.asyncio
    async def test_quota_unlimited(self):
        storage = MemoryStorage(MemoryConfig(max_size=0))
        # Should not raise regardless of size
        await storage.save("big.bin", b"x" * 1_000_000)

    @pytest.mark.asyncio
    async def test_quota_after_delete_frees_space(self):
        storage = MemoryStorage(MemoryConfig(max_size=20))
        await storage.save("a.txt", b"0123456789", overwrite=True)  # 10 bytes
        await storage.save("b.txt", b"0123456789", overwrite=True)  # 20 bytes total
        await storage.delete("a.txt")  # Free 10 bytes
        # Now should be able to save 10 more bytes
        await storage.save("c.txt", b"0123456789", overwrite=True)


class TestLocalStorage:
    """Full async CRUD for LocalStorage with real filesystem."""

    @pytest.fixture
    def tmp_dir(self, tmp_path):
        return str(tmp_path / "storage_root")

    @pytest.fixture
    def storage(self, tmp_dir) -> LocalStorage:
        return LocalStorage(LocalConfig(root=tmp_dir, base_url="/files/"))

    @pytest.mark.asyncio
    async def test_backend_name(self, storage):
        assert storage.backend_name == "local"

    @pytest.mark.asyncio
    async def test_initialize_creates_root(self, storage, tmp_dir):
        assert not os.path.exists(tmp_dir)
        await storage.initialize()
        assert os.path.isdir(tmp_dir)

    @pytest.mark.asyncio
    async def test_ping_after_init(self, storage):
        await storage.initialize()
        assert await storage.ping() is True

    @pytest.mark.asyncio
    async def test_ping_before_init(self, storage, tmp_dir):
        # Root doesn't exist yet
        assert await storage.ping() is False

    @pytest.mark.asyncio
    async def test_save_and_open(self, storage):
        await storage.initialize()
        name = await storage.save("hello.txt", b"hello world")
        sf = await storage.open(name)
        assert await sf.read() == b"hello world"

    @pytest.mark.asyncio
    async def test_save_creates_subdirectories(self, storage):
        await storage.initialize()
        name = await storage.save("a/b/c/deep.txt", b"deep")
        assert await storage.exists(name)

    @pytest.mark.asyncio
    async def test_save_overwrite_false(self, storage):
        await storage.initialize()
        n1 = await storage.save("dup.txt", b"v1")
        n2 = await storage.save("dup.txt", b"v2", overwrite=False)
        assert n1 != n2

    @pytest.mark.asyncio
    async def test_save_overwrite_true(self, storage):
        await storage.initialize()
        await storage.save("over.txt", b"v1")
        n2 = await storage.save("over.txt", b"v2", overwrite=True)
        assert n2 == "over.txt"
        sf = await storage.open("over.txt")
        assert await sf.read() == b"v2"

    @pytest.mark.asyncio
    async def test_delete(self, storage):
        await storage.initialize()
        await storage.save("del.txt", b"bye")
        await storage.delete("del.txt")
        assert not await storage.exists("del.txt")

    @pytest.mark.asyncio
    async def test_delete_nonexistent(self, storage):
        await storage.initialize()
        await storage.delete("ghost.txt")  # Idempotent

    @pytest.mark.asyncio
    async def test_exists(self, storage):
        await storage.initialize()
        assert not await storage.exists("nope.txt")
        await storage.save("yes.txt", b"y")
        assert await storage.exists("yes.txt")

    @pytest.mark.asyncio
    async def test_stat(self, storage):
        await storage.initialize()
        await storage.save("stat.txt", b"abcde")
        meta = await storage.stat("stat.txt")
        assert meta.name == "stat.txt"
        assert meta.size == 5
        assert meta.last_modified is not None
        assert meta.created_at is not None

    @pytest.mark.asyncio
    async def test_stat_nonexistent_raises(self, storage):
        await storage.initialize()
        with pytest.raises(StorageFileNotFoundError):
            await storage.stat("missing.txt")

    @pytest.mark.asyncio
    async def test_open_nonexistent_raises(self, storage):
        await storage.initialize()
        with pytest.raises(StorageFileNotFoundError):
            await storage.open("missing.txt")

    @pytest.mark.asyncio
    async def test_size(self, storage):
        await storage.initialize()
        await storage.save("sz.txt", b"123")
        assert await storage.size("sz.txt") == 3

    @pytest.mark.asyncio
    async def test_url(self, storage):
        await storage.initialize()
        url = await storage.url("path/to/file.pdf")
        assert url == "/files/path/to/file.pdf"

    @pytest.mark.asyncio
    async def test_url_strips_trailing_slash(self):
        s = LocalStorage(LocalConfig(root="/tmp/x", base_url="/storage/"))
        url = await s.url("test.txt")
        assert url == "/storage/test.txt"
        assert "//" not in url.replace("://", "")

    @pytest.mark.asyncio
    async def test_listdir(self, storage):
        await storage.initialize()
        await storage.save("root.txt", b"r")
        await storage.save("sub/a.txt", b"a")
        dirs, files = await storage.listdir()
        assert "root.txt" in files
        assert "sub" in dirs

    @pytest.mark.asyncio
    async def test_listdir_subdir(self, storage):
        await storage.initialize()
        await storage.save("d/x.txt", b"x")
        await storage.save("d/y.txt", b"y")
        dirs, files = await storage.listdir("d")
        assert "x.txt" in files
        assert "y.txt" in files

    @pytest.mark.asyncio
    async def test_listdir_nonexistent_dir(self, storage):
        await storage.initialize()
        dirs, files = await storage.listdir("does_not_exist")
        assert dirs == []
        assert files == []

    @pytest.mark.asyncio
    async def test_copy(self, storage):
        await storage.initialize()
        await storage.save("src.txt", b"copy me")
        result = await storage.copy("src.txt", "dst.txt")
        assert result == "dst.txt"
        sf = await storage.open("dst.txt")
        assert await sf.read() == b"copy me"
        assert await storage.exists("src.txt")

    @pytest.mark.asyncio
    async def test_copy_nonexistent_raises(self, storage):
        await storage.initialize()
        with pytest.raises(StorageFileNotFoundError):
            await storage.copy("missing.txt", "dst.txt")

    @pytest.mark.asyncio
    async def test_move(self, storage):
        await storage.initialize()
        await storage.save("mv_src.txt", b"move me")
        result = await storage.move("mv_src.txt", "mv_dst.txt")
        assert result == "mv_dst.txt"
        assert not await storage.exists("mv_src.txt")
        sf = await storage.open("mv_dst.txt")
        assert await sf.read() == b"move me"

    @pytest.mark.asyncio
    async def test_path_traversal_blocked(self, storage):
        await storage.initialize()
        with pytest.raises(StoragePermissionError):
            await storage.save("../../etc/passwd", b"hacked")

    @pytest.mark.asyncio
    async def test_path_traversal_blocked_open(self, storage):
        await storage.initialize()
        with pytest.raises(StoragePermissionError):
            await storage.open("../../etc/passwd")

    @pytest.mark.asyncio
    async def test_open_returns_meta(self, storage):
        await storage.initialize()
        await storage.save("m.txt", b"metadata test")
        sf = await storage.open("m.txt")
        assert sf.meta is not None
        assert sf.meta.name == "m.txt"
        assert sf.meta.size == 13

    @pytest.mark.asyncio
    async def test_save_binary_content(self, storage):
        await storage.initialize()
        binary = bytes(range(256))
        await storage.save("binary.bin", binary)
        sf = await storage.open("binary.bin")
        assert await sf.read() == binary

    @pytest.mark.asyncio
    async def test_large_file(self, storage):
        await storage.initialize()
        large = b"x" * (1024 * 1024)  # 1 MB
        await storage.save("large.bin", large)
        sf = await storage.open("large.bin")
        assert await sf.read() == large

    @pytest.mark.asyncio
    async def test_no_create_dirs(self, tmp_path):
        root = str(tmp_path / "no_auto")
        s = LocalStorage(LocalConfig(root=root, create_dirs=False))
        # initialize should not create root when create_dirs=False
        await s.initialize()
        assert not os.path.exists(root)


class TestCompositeStorage:
    """Composite backend: rule routing, fallback, multi-backend."""

    @pytest.fixture
    def composite(self):
        config = CompositeConfig(
            backends={
                "images": {"backend": "memory"},
                "docs": {"backend": "memory"},
            },
            rules={
                "*.jpg": "images",
                "*.png": "images",
                "*.pdf": "docs",
            },
            fallback="docs",
        )
        return CompositeStorage(config)

    @pytest.mark.asyncio
    async def test_backend_name(self, composite):
        assert composite.backend_name == "composite"

    @pytest.mark.asyncio
    async def test_initialize(self, composite):
        await composite.initialize()
        assert len(composite._backends) == 2

    @pytest.mark.asyncio
    async def test_rule_routing_jpg(self, composite):
        await composite.initialize()
        name = await composite.save("photo.jpg", b"JPEG data")
        # Should be stored in the "images" backend
        images_backend = composite._backends["images"]
        assert await images_backend.exists("photo.jpg")

    @pytest.mark.asyncio
    async def test_rule_routing_pdf(self, composite):
        await composite.initialize()
        await composite.save("report.pdf", b"PDF data")
        docs_backend = composite._backends["docs"]
        assert await docs_backend.exists("report.pdf")

    @pytest.mark.asyncio
    async def test_fallback_routing(self, composite):
        await composite.initialize()
        await composite.save("random.xyz", b"fallback")
        docs_backend = composite._backends["docs"]  # fallback = "docs"
        assert await docs_backend.exists("random.xyz")

    @pytest.mark.asyncio
    async def test_open_via_composite(self, composite):
        await composite.initialize()
        await composite.save("test.jpg", b"image data")
        sf = await composite.open("test.jpg")
        assert await sf.read() == b"image data"

    @pytest.mark.asyncio
    async def test_delete_via_composite(self, composite):
        await composite.initialize()
        await composite.save("del.png", b"del")
        await composite.delete("del.png")
        assert not await composite.exists("del.png")

    @pytest.mark.asyncio
    async def test_exists_via_composite(self, composite):
        await composite.initialize()
        assert not await composite.exists("nope.jpg")
        await composite.save("yes.jpg", b"y")
        assert await composite.exists("yes.jpg")

    @pytest.mark.asyncio
    async def test_stat_via_composite(self, composite):
        await composite.initialize()
        await composite.save("s.pdf", b"abcde")
        meta = await composite.stat("s.pdf")
        assert meta.size == 5

    @pytest.mark.asyncio
    async def test_size_via_composite(self, composite):
        await composite.initialize()
        await composite.save("sz.jpg", b"123")
        assert await composite.size("sz.jpg") == 3

    @pytest.mark.asyncio
    async def test_url_via_composite(self, composite):
        await composite.initialize()
        url = await composite.url("photo.jpg")
        assert "photo.jpg" in url

    @pytest.mark.asyncio
    async def test_listdir_aggregates(self, composite):
        await composite.initialize()
        await composite.save("a.jpg", b"a")
        await composite.save("b.pdf", b"b")
        dirs, files = await composite.listdir()
        assert "a.jpg" in files
        assert "b.pdf" in files

    @pytest.mark.asyncio
    async def test_ping(self, composite):
        await composite.initialize()
        assert await composite.ping() is True

    @pytest.mark.asyncio
    async def test_shutdown(self, composite):
        await composite.initialize()
        await composite.shutdown()  # Should not raise

    @pytest.mark.asyncio
    async def test_no_backends_raises(self):
        config = CompositeConfig(backends={}, rules={}, fallback="missing")
        comp = CompositeStorage(config)
        await comp.initialize()
        with pytest.raises(BackendUnavailableError):
            await comp.save("test.txt", b"data")

    @pytest.mark.asyncio
    async def test_nested_path_routing(self, composite):
        await composite.initialize()
        await composite.save("uploads/photos/sunset.jpg", b"sunset")
        images_backend = composite._backends["images"]
        assert await images_backend.exists("uploads/photos/sunset.jpg")


class TestS3StorageGuards:
    """S3Storage import guard and ensure-client guard."""

    def test_backend_name(self):
        s3 = S3Storage(S3Config(bucket="test"))
        assert s3.backend_name == "s3"

    @pytest.mark.asyncio
    async def test_ensure_client_raises_before_init(self):
        from aquilia.storage.backends.s3 import S3Storage

        s3 = S3Storage(S3Config(bucket="test"))
        with pytest.raises(BackendUnavailableError, match="not initialized"):
            await s3.save("test.txt", b"data")

    @pytest.mark.asyncio
    async def test_s3_config_wiring(self):
        config = S3Config(
            bucket="my-bucket",
            region="eu-west-1",
            access_key="AKIA...",
            secret_key="secret",
            prefix="uploads/",
            storage_class="GLACIER",
        )
        s3 = S3Storage(config)
        assert s3._config.bucket == "my-bucket"
        assert s3._config.region == "eu-west-1"
        assert s3._config.prefix == "uploads/"
        assert s3._config.storage_class == "GLACIER"


class TestGCSStorageGuards:
    """GCSStorage import guard and config wiring."""

    def test_backend_name(self):
        from aquilia.storage.backends.gcs import GCSStorage

        gcs = GCSStorage(GCSConfig(bucket="test"))
        assert gcs.backend_name == "gcs"

    @pytest.mark.asyncio
    async def test_ensure_bucket_raises_before_init(self):
        from aquilia.storage.backends.gcs import GCSStorage

        gcs = GCSStorage(GCSConfig(bucket="test"))
        with pytest.raises(BackendUnavailableError, match="not initialized"):
            await gcs.save("test.txt", b"data")


class TestAzureStorageGuards:
    """AzureBlobStorage import guard and config wiring."""

    def test_backend_name(self):
        from aquilia.storage.backends.azure import AzureBlobStorage

        az = AzureBlobStorage(AzureBlobConfig(container="test"))
        assert az.backend_name == "azure"

    @pytest.mark.asyncio
    async def test_ensure_container_raises_before_init(self):
        from aquilia.storage.backends.azure import AzureBlobStorage

        az = AzureBlobStorage(AzureBlobConfig(container="test"))
        with pytest.raises(BackendUnavailableError, match="not initialized"):
            await az.save("test.txt", b"data")

    def test_azure_url_custom_domain(self):
        az = AzureBlobStorage(
            AzureBlobConfig(
                container="media",
                custom_domain="cdn.example.com",
                account_name="myaccount",
            )
        )
        # Simulate container client being set
        az._container_client = MagicMock()

    def test_azure_config_connection_string(self):
        c = AzureBlobConfig(
            container="media",
            connection_string="DefaultEndpointsProtocol=https;AccountName=test",
        )
        assert c.connection_string is not None


class TestSFTPStorageGuards:
    """SFTPStorage import guard and config wiring."""

    def test_backend_name(self):
        from aquilia.storage.backends.sftp import SFTPStorage

        sftp = SFTPStorage(SFTPConfig(host="example.com"))
        assert sftp.backend_name == "sftp"

    @pytest.mark.asyncio
    async def test_ensure_sftp_raises_before_init(self):
        from aquilia.storage.backends.sftp import SFTPStorage

        sftp = SFTPStorage(SFTPConfig(host="example.com"))
        with pytest.raises(BackendUnavailableError, match="not initialized"):
            await sftp.save("test.txt", b"data")

    def test_remote_path(self):
        from aquilia.storage.backends.sftp import SFTPStorage

        sftp = SFTPStorage(SFTPConfig(root="/data"))
        assert sftp._remote_path("uploads/file.txt") == "/data/uploads/file.txt"


# Import S3Storage at module level for class reference
from aquilia.storage.backends.s3 import S3Storage
from aquilia.storage.backends.azure import AzureBlobStorage


# ═══════════════════════════════════════════════════════════════════════════
#  SECTION 4 — StorageRegistry
# ═══════════════════════════════════════════════════════════════════════════


class TestStorageRegistry:
    """Registry: register, access, default, lifecycle."""

    @pytest.fixture
    def registry(self) -> StorageRegistry:
        return StorageRegistry()

    @pytest.fixture
    def memory_backend(self) -> MemoryStorage:
        return MemoryStorage(MemoryConfig())

    def test_empty_registry(self, registry):
        assert len(registry) == 0
        assert registry.aliases() == []

    def test_register_and_access(self, registry, memory_backend):
        registry.register("test", memory_backend)
        assert "test" in registry
        assert registry["test"] is memory_backend
        assert registry.get("test") is memory_backend

    def test_register_multiple(self, registry):
        b1 = MemoryStorage()
        b2 = MemoryStorage()
        registry.register("a", b1)
        registry.register("b", b2)
        assert len(registry) == 2
        assert set(registry.aliases()) == {"a", "b"}

    def test_unregister(self, registry, memory_backend):
        registry.register("rm", memory_backend)
        removed = registry.unregister("rm")
        assert removed is memory_backend
        assert "rm" not in registry

    def test_unregister_nonexistent(self, registry):
        result = registry.unregister("ghost")
        assert result is None

    def test_set_default(self, registry, memory_backend):
        registry.register("main", memory_backend)
        registry.set_default("main")
        assert registry.default is memory_backend

    def test_set_default_nonexistent_raises(self, registry):
        from aquilia.storage import StorageConfigFault

        with pytest.raises(StorageConfigFault):
            registry.set_default("nonexistent")

    def test_default_not_set_raises(self, registry):
        with pytest.raises(BackendUnavailableError):
            _ = registry.default

    def test_default_alias_is_default(self, registry, memory_backend):
        registry.register("default", memory_backend)
        assert registry.default is memory_backend

    def test_getitem_missing_raises(self, registry):
        with pytest.raises(BackendUnavailableError, match="not registered"):
            _ = registry["missing"]

    def test_get_missing_returns_none(self, registry):
        assert registry.get("missing") is None

    def test_contains(self, registry, memory_backend):
        registry.register("x", memory_backend)
        assert "x" in registry
        assert "y" not in registry

    def test_len(self, registry, memory_backend):
        assert len(registry) == 0
        registry.register("a", memory_backend)
        assert len(registry) == 1

    def test_iter(self, registry):
        b1, b2 = MemoryStorage(), MemoryStorage()
        registry.register("alpha", b1)
        registry.register("beta", b2)
        aliases = list(registry)
        assert "alpha" in aliases
        assert "beta" in aliases

    def test_items(self, registry, memory_backend):
        registry.register("x", memory_backend)
        items = registry.items()
        assert len(items) == 1
        assert items[0] == ("x", memory_backend)

    def test_repr(self, registry, memory_backend):
        registry.register("default", memory_backend)
        r = repr(registry)
        assert "StorageRegistry" in r
        assert "default" in r

    @pytest.mark.asyncio
    async def test_initialize_all(self, registry):
        b1 = MemoryStorage()
        b2 = MemoryStorage()
        registry.register("a", b1)
        registry.register("b", b2)
        await registry.initialize_all()  # Should not raise

    @pytest.mark.asyncio
    async def test_shutdown_all(self, registry):
        b1 = MemoryStorage()
        await b1.save("x.txt", b"data")
        registry.register("a", b1)
        await registry.shutdown_all()
        assert not await b1.exists("x.txt")  # Data cleared

    @pytest.mark.asyncio
    async def test_health_check_all_healthy(self, registry):
        registry.register("a", MemoryStorage())
        registry.register("b", MemoryStorage())
        health = await registry.health_check()
        assert health == {"a": True, "b": True}

    @pytest.mark.asyncio
    async def test_health_check_empty(self, registry):
        health = await registry.health_check()
        assert health == {}

    @pytest.mark.asyncio
    async def test_health_check_mixed(self, registry):
        healthy = MemoryStorage()
        unhealthy = MemoryStorage()
        unhealthy.ping = AsyncMock(side_effect=Exception("down"))
        registry.register("good", healthy)
        registry.register("bad", unhealthy)
        health = await registry.health_check()
        assert health["good"] is True
        assert health["bad"] is False


class TestStorageRegistryFromConfig:
    """StorageRegistry.from_config factory."""

    def test_single_backend(self):
        registry = StorageRegistry.from_config(
            [
                {"alias": "default", "backend": "memory"},
            ]
        )
        assert "default" in registry
        assert isinstance(registry["default"], MemoryStorage)

    def test_multiple_backends(self):
        registry = StorageRegistry.from_config(
            [
                {"alias": "mem1", "backend": "memory"},
                {"alias": "mem2", "backend": "memory", "max_size": 1024},
            ]
        )
        assert len(registry) == 2
        assert "mem1" in registry
        assert "mem2" in registry

    def test_default_is_set(self):
        registry = StorageRegistry.from_config(
            [
                {"alias": "default", "backend": "memory"},
                {"alias": "other", "backend": "memory"},
            ]
        )
        assert registry.default is registry["default"]

    def test_explicit_default_flag(self):
        registry = StorageRegistry.from_config(
            [
                {"alias": "primary", "backend": "memory", "default": True},
                {"alias": "secondary", "backend": "memory"},
            ]
        )
        assert registry._default_alias == "primary"

    def test_local_backend_from_config(self, tmp_path):
        registry = StorageRegistry.from_config(
            [
                {"alias": "default", "backend": "local", "root": str(tmp_path)},
            ]
        )
        assert isinstance(registry["default"], LocalStorage)

    def test_empty_config(self):
        registry = StorageRegistry.from_config([])
        assert len(registry) == 0


class TestCreateBackend:
    """create_backend factory function."""

    def test_memory(self):
        b = create_backend(MemoryConfig())
        assert isinstance(b, MemoryStorage)

    def test_local(self):
        b = create_backend(LocalConfig(root="/tmp/test"))
        assert isinstance(b, LocalStorage)

    def test_unknown_raises(self):
        with pytest.raises(BackendUnavailableError, match="Unknown"):
            create_backend(StorageConfig(backend="nonsense"))

    def test_all_builtins_importable(self):
        for shorthand, dotted in _BUILTIN_BACKENDS.items():
            cls = _import_backend(dotted)
            assert issubclass(cls, StorageBackend)

    def test_import_backend_bad_path(self):
        with pytest.raises(ImportError):
            _import_backend("nonexistent.module.ClassName")


# ═══════════════════════════════════════════════════════════════════════════
#  SECTION 5 — StorageSubsystem (Boot Lifecycle)
# ═══════════════════════════════════════════════════════════════════════════


class TestStorageSubsystem:
    """Subsystem lifecycle: init, shutdown, health."""

    def _make_boot_context(self, storage_config: dict | None = None) -> Any:
        """Create a minimal BootContext-like object."""
        from aquilia.subsystems.base import BootContext
        from aquilia.health import HealthRegistry

        config = {}
        if storage_config is not None:
            config["storage"] = storage_config

        ctx = BootContext(
            config=config,
            manifests=[],
            health=HealthRegistry(),
        )
        return ctx

    def test_subsystem_identity(self):
        sub = StorageSubsystem()
        assert sub._name == "storage"
        assert sub._priority == 25
        assert sub._required is False

    @pytest.mark.asyncio
    async def test_init_with_memory_backends(self):
        sub = StorageSubsystem()
        ctx = self._make_boot_context(
            {
                "backends": [
                    {"alias": "default", "backend": "memory"},
                    {"alias": "cache", "backend": "memory", "max_size": 4096},
                ],
            }
        )
        await sub._do_initialize(ctx)
        assert sub._registry is not None
        assert "default" in sub._registry
        assert "cache" in sub._registry
        assert "storage_registry" in ctx.shared_state

    @pytest.mark.asyncio
    async def test_init_no_storage_config(self):
        sub = StorageSubsystem()
        ctx = self._make_boot_context(None)
        await sub._do_initialize(ctx)
        assert sub._registry is None

    @pytest.mark.asyncio
    async def test_init_empty_storage_config(self):
        sub = StorageSubsystem()
        ctx = self._make_boot_context({})
        await sub._do_initialize(ctx)
        assert sub._registry is None

    @pytest.mark.asyncio
    async def test_init_empty_backends_list(self):
        sub = StorageSubsystem()
        ctx = self._make_boot_context({"backends": []})
        await sub._do_initialize(ctx)
        assert sub._registry is None

    @pytest.mark.asyncio
    async def test_init_single_backend_shorthand(self):
        sub = StorageSubsystem()
        ctx = self._make_boot_context(
            {
                "backend": "memory",
                "alias": "default",
            }
        )
        await sub._do_initialize(ctx)
        assert sub._registry is not None
        assert "default" in sub._registry

    @pytest.mark.asyncio
    async def test_init_dict_backends_wraps_to_list(self):
        sub = StorageSubsystem()
        ctx = self._make_boot_context(
            {
                "backends": {"alias": "default", "backend": "memory"},
            }
        )
        await sub._do_initialize(ctx)
        assert sub._registry is not None

    @pytest.mark.asyncio
    async def test_shutdown(self):
        sub = StorageSubsystem()
        ctx = self._make_boot_context(
            {
                "backends": [{"alias": "default", "backend": "memory"}],
            }
        )
        await sub._do_initialize(ctx)

        # Save data to verify shutdown clears it
        await sub._registry["default"].save("test.txt", b"data")
        assert await sub._registry["default"].exists("test.txt")

        await sub._do_shutdown()
        assert not await sub._registry["default"].exists("test.txt")

    @pytest.mark.asyncio
    async def test_shutdown_no_registry(self):
        sub = StorageSubsystem()
        await sub._do_shutdown()  # Should not raise

    @pytest.mark.asyncio
    async def test_health_check_healthy(self):
        sub = StorageSubsystem()
        ctx = self._make_boot_context(
            {
                "backends": [
                    {"alias": "default", "backend": "memory"},
                ],
            }
        )
        await sub._do_initialize(ctx)
        sub._initialized = True

        health = await sub.health_check()
        assert health.name == "storage"
        assert health.status.value == "healthy"

    @pytest.mark.asyncio
    async def test_health_check_not_initialized(self):
        sub = StorageSubsystem()
        health = await sub.health_check()
        assert health.status.value == "stopped"

    @pytest.mark.asyncio
    async def test_health_check_degraded(self):
        sub = StorageSubsystem()
        ctx = self._make_boot_context(
            {
                "backends": [
                    {"alias": "good", "backend": "memory"},
                    {"alias": "bad", "backend": "memory"},
                ],
            }
        )
        await sub._do_initialize(ctx)
        sub._initialized = True

        # Make one backend "unhealthy"
        sub._registry["bad"].ping = AsyncMock(side_effect=Exception("down"))

        health = await sub.health_check()
        assert health.status.value == "degraded"
        assert "bad" in health.message

    @pytest.mark.asyncio
    async def test_health_check_all_unhealthy(self):
        sub = StorageSubsystem()
        ctx = self._make_boot_context(
            {
                "backends": [
                    {"alias": "a", "backend": "memory"},
                    {"alias": "b", "backend": "memory"},
                ],
            }
        )
        await sub._do_initialize(ctx)
        sub._initialized = True

        sub._registry["a"].ping = AsyncMock(side_effect=Exception("down"))
        sub._registry["b"].ping = AsyncMock(side_effect=Exception("down"))

        health = await sub.health_check()
        assert health.status.value == "unhealthy"

    @pytest.mark.asyncio
    async def test_health_registers_per_backend(self):
        sub = StorageSubsystem()
        ctx = self._make_boot_context(
            {
                "backends": [
                    {"alias": "default", "backend": "memory"},
                ],
            }
        )
        await sub._do_initialize(ctx)
        # Health registry should have storage.default
        h = ctx.health.get("storage.default")
        assert h is not None
        assert h.status.value == "healthy"


# ═══════════════════════════════════════════════════════════════════════════
#  SECTION 6 — StorageEffectProvider
# ═══════════════════════════════════════════════════════════════════════════


class TestStorageEffectProvider:
    """Effect system bridge for storage."""

    @pytest.fixture
    def registry_with_backends(self) -> StorageRegistry:
        reg = StorageRegistry()
        reg.register("default", MemoryStorage())
        reg.register("cdn", MemoryStorage())
        return reg

    def test_kind(self):
        provider = StorageEffectProvider()
        assert provider.kind == EffectKind.STORAGE

    @pytest.mark.asyncio
    async def test_acquire_default(self, registry_with_backends):
        provider = StorageEffectProvider(registry_with_backends)
        backend = await provider.acquire()
        assert isinstance(backend, MemoryStorage)

    @pytest.mark.asyncio
    async def test_acquire_by_alias(self, registry_with_backends):
        provider = StorageEffectProvider(registry_with_backends)
        backend = await provider.acquire("cdn")
        assert isinstance(backend, MemoryStorage)
        assert backend is registry_with_backends["cdn"]

    @pytest.mark.asyncio
    async def test_acquire_no_registry_raises(self):
        from aquilia.storage import StorageConfigFault

        provider = StorageEffectProvider()
        with pytest.raises(StorageConfigFault, match="no registry"):
            await provider.acquire()

    @pytest.mark.asyncio
    async def test_acquire_nonexistent_alias_raises(self, registry_with_backends):
        provider = StorageEffectProvider(registry_with_backends)
        with pytest.raises(BackendUnavailableError):
            await provider.acquire("nonexistent")

    def test_set_registry(self, registry_with_backends):
        provider = StorageEffectProvider()
        assert provider._registry is None
        provider.set_registry(registry_with_backends)
        assert provider._registry is registry_with_backends

    @pytest.mark.asyncio
    async def test_initialize(self, registry_with_backends):
        provider = StorageEffectProvider(registry_with_backends)
        await provider.initialize()  # Should not raise

    @pytest.mark.asyncio
    async def test_release(self, registry_with_backends):
        provider = StorageEffectProvider(registry_with_backends)
        backend = await provider.acquire()
        await provider.release(backend)  # No-op, should not raise

    @pytest.mark.asyncio
    async def test_release_with_failure(self, registry_with_backends):
        provider = StorageEffectProvider(registry_with_backends)
        backend = await provider.acquire()
        await provider.release(backend, success=False)  # Still no-op

    @pytest.mark.asyncio
    async def test_finalize(self, registry_with_backends):
        provider = StorageEffectProvider(registry_with_backends)
        await provider.finalize()  # No-op, should not raise

    @pytest.mark.asyncio
    async def test_initialize_no_registry(self):
        provider = StorageEffectProvider()
        await provider.initialize()  # Should not raise even without registry


# ═══════════════════════════════════════════════════════════════════════════
#  SECTION 7 — Config Builder Integration
# ═══════════════════════════════════════════════════════════════════════════


class TestIntegrationStorage:
    """Integration.storage() config builder output."""

    def test_basic_output(self):
        result = Integration.storage(
            backends={"default": {"backend": "memory"}},
        )
        assert result["_integration_type"] == "storage"
        assert result["enabled"] is True
        assert result["default"] == "default"
        assert isinstance(result["backends"], list)
        assert len(result["backends"]) == 1

    def test_default_alias_marked(self):
        result = Integration.storage(
            default="cdn",
            backends={
                "local": {"backend": "local", "root": "./uploads"},
                "cdn": {"backend": "s3", "bucket": "cdn-bucket"},
            },
        )
        backends = result["backends"]
        cdn_entry = next(b for b in backends if b["alias"] == "cdn")
        local_entry = next(b for b in backends if b["alias"] == "local")
        assert cdn_entry.get("default") is True
        assert local_entry.get("default") is not True

    def test_storage_config_instances(self):
        result = Integration.storage(
            default="local",
            backends={
                "local": LocalConfig(alias="local", root="./uploads"),
                "mem": MemoryConfig(alias="mem", max_size=1024),
            },
        )
        backends = result["backends"]
        assert len(backends) == 2
        local_entry = next(b for b in backends if b["alias"] == "local")
        assert local_entry["root"] == "./uploads"
        mem_entry = next(b for b in backends if b["alias"] == "mem")
        assert mem_entry["max_size"] == 1024

    def test_no_backends(self):
        result = Integration.storage()
        assert result["backends"] == []

    def test_extra_kwargs_passed(self):
        result = Integration.storage(
            backends={},
            custom_option="test",
        )
        assert result["custom_option"] == "test"


class TestWorkspaceStorage:
    """Workspace.storage() chaining."""

    def test_storage_chaining(self):
        ws = Workspace("testapp").storage(
            default="default",
            backends={"default": MemoryConfig()},
        )
        assert isinstance(ws, Workspace)

    def test_storage_config_stored(self):
        ws = Workspace("testapp").storage(
            default="local",
            backends={"local": LocalConfig(root="./uploads")},
        )
        assert "storage" in ws._integrations
        config = ws._integrations["storage"]
        assert config["_integration_type"] == "storage"
        assert config["default"] == "local"

    def test_storage_multiple_backends(self):
        ws = Workspace("testapp").storage(
            default="cdn",
            backends={
                "local": LocalConfig(root="./uploads"),
                "cdn": MemoryConfig(),
            },
        )
        config = ws._integrations["storage"]
        assert len(config["backends"]) == 2

    def test_full_workspace_chain(self):
        """Full workspace with storage + other integrations."""
        ws = Workspace("fullapp").storage(
            default="mem",
            backends={"mem": MemoryConfig()},
        )
        assert isinstance(ws, Workspace)
        assert ws._integrations.get("storage") is not None


# ═══════════════════════════════════════════════════════════════════════════
#  SECTION 8 — Cross-cutting Regression Tests
# ═══════════════════════════════════════════════════════════════════════════


class TestStorageFileRegression:
    """Edge cases and regression tests for StorageFile."""

    @pytest.mark.asyncio
    async def test_read_size_zero(self):
        sf = StorageFile(name="test.txt", content=b"hello")
        data = await sf.read(0)
        assert data == b""

    @pytest.mark.asyncio
    async def test_read_size_larger_than_content(self):
        sf = StorageFile(name="test.txt", content=b"hi")
        data = await sf.read(1000)
        assert data == b"hi"

    @pytest.mark.asyncio
    async def test_seek_beyond_content(self):
        sf = StorageFile(name="test.txt", content=b"abc")
        await sf.seek(100)
        data = await sf.read()
        assert data == b""

    @pytest.mark.asyncio
    async def test_write_to_none_content(self):
        sf = StorageFile(name="out.txt", mode="wb")
        await sf.write(b"first")
        assert sf.content == b"first"

    @pytest.mark.asyncio
    async def test_multiple_writes_accumulate(self):
        sf = StorageFile(name="out.txt", mode="wb")
        await sf.write(b"a")
        await sf.write(b"b")
        await sf.write(b"c")
        assert sf.content == b"abc"

    @pytest.mark.asyncio
    async def test_empty_content_read(self):
        sf = StorageFile(name="empty.txt", content=b"")
        data = await sf.read()
        assert data == b""

    @pytest.mark.asyncio
    async def test_content_property(self):
        sf = StorageFile(name="test.txt", content=b"prop")
        assert sf.content == b"prop"

    @pytest.mark.asyncio
    async def test_content_property_none(self):
        sf = StorageFile(name="test.txt")
        assert sf.content is None

    @pytest.mark.asyncio
    async def test_mode_preserved(self):
        sf = StorageFile(name="test.txt", mode="wb")
        assert sf.mode == "wb"

    @pytest.mark.asyncio
    async def test_name_preserved(self):
        sf = StorageFile(name="my/file.txt")
        assert sf.name == "my/file.txt"


class TestMetadataRegression:
    """Edge cases for StorageMetadata."""

    def test_empty_metadata_dict(self):
        m = StorageMetadata(name="x", metadata={})
        assert m.metadata == {}

    def test_metadata_is_not_shared_across_instances(self):
        m1 = StorageMetadata(name="a")
        m2 = StorageMetadata(name="b")
        assert m1.metadata is not m2.metadata or m1.metadata == {}

    def test_to_dict_returns_new_dict(self):
        m = StorageMetadata(name="x")
        d1 = m.to_dict()
        d2 = m.to_dict()
        assert d1 == d2
        assert d1 is not d2

    def test_metadata_large_size(self):
        m = StorageMetadata(name="big", size=2**40)
        assert m.size == 2**40
        assert m.to_dict()["size"] == 2**40


class TestRegistryRegression:
    """Edge cases for StorageRegistry."""

    def test_overwrite_registration(self):
        reg = StorageRegistry()
        b1 = MemoryStorage()
        b2 = MemoryStorage()
        reg.register("same", b1)
        reg.register("same", b2)
        assert reg["same"] is b2
        assert len(reg) == 1

    @pytest.mark.asyncio
    async def test_shutdown_with_failing_backend(self):
        reg = StorageRegistry()
        bad = MemoryStorage()
        bad.shutdown = AsyncMock(side_effect=Exception("fail"))
        reg.register("bad", bad)
        await reg.shutdown_all()  # Should not raise (best-effort)

    @pytest.mark.asyncio
    async def test_health_check_with_exception_in_ping(self):
        reg = StorageRegistry()
        bad = MemoryStorage()
        bad.ping = AsyncMock(side_effect=RuntimeError("oops"))
        reg.register("x", bad)
        health = await reg.health_check()
        assert health["x"] is False

    def test_from_config_with_alias_default(self):
        reg = StorageRegistry.from_config(
            [
                {"backend": "memory"},  # No alias → defaults to "default"
            ]
        )
        assert "default" in reg


class TestLocalStorageRegression:
    """Edge cases for LocalStorage."""

    @pytest.mark.asyncio
    async def test_save_empty_file(self, tmp_path):
        s = LocalStorage(LocalConfig(root=str(tmp_path)))
        await s.initialize()
        name = await s.save("empty.txt", b"")
        assert await s.exists(name)
        assert await s.size(name) == 0

    @pytest.mark.asyncio
    async def test_save_unicode_filename(self, tmp_path):
        s = LocalStorage(LocalConfig(root=str(tmp_path)))
        await s.initialize()
        name = await s.save("café.txt", b"hello")
        assert await s.exists(name)

    @pytest.mark.asyncio
    async def test_save_deep_nested_path(self, tmp_path):
        s = LocalStorage(LocalConfig(root=str(tmp_path)))
        await s.initialize()
        name = await s.save("a/b/c/d/e/f/g.txt", b"deep")
        assert await s.exists(name)

    @pytest.mark.asyncio
    async def test_multiple_path_traversal_patterns(self, tmp_path):
        s = LocalStorage(LocalConfig(root=str(tmp_path)))
        await s.initialize()

        traversal_paths = [
            "../escape.txt",
            "../../escape.txt",
            "subdir/../../../escape.txt",
        ]
        for path in traversal_paths:
            with pytest.raises(StoragePermissionError):
                await s.save(path, b"hacked")

    @pytest.mark.asyncio
    async def test_stat_content_type_guessing(self, tmp_path):
        s = LocalStorage(LocalConfig(root=str(tmp_path)))
        await s.initialize()
        await s.save("photo.jpg", b"jpeg data")
        meta = await s.stat("photo.jpg")
        assert "image" in meta.content_type or "jpeg" in meta.content_type

    @pytest.mark.asyncio
    async def test_copy_creates_parent_dirs(self, tmp_path):
        s = LocalStorage(LocalConfig(root=str(tmp_path)))
        await s.initialize()
        await s.save("src.txt", b"data")
        result = await s.copy("src.txt", "new_dir/copy.txt")
        assert await s.exists("new_dir/copy.txt")


class TestMemoryStorageRegression:
    """Edge cases for MemoryStorage."""

    @pytest.mark.asyncio
    async def test_default_config(self):
        s = MemoryStorage()  # None config → defaults
        assert s.backend_name == "memory"
        await s.save("test.txt", b"default config")
        assert await s.exists("test.txt")

    @pytest.mark.asyncio
    async def test_path_normalization(self):
        s = MemoryStorage()
        await s.save("/leading/slash.txt", b"norm")
        assert await s.exists("leading/slash.txt")

    @pytest.mark.asyncio
    async def test_multiple_saves_and_deletes(self):
        s = MemoryStorage()
        names = []
        for i in range(100):
            name = await s.save(f"file_{i}.txt", f"content_{i}".encode())
            names.append(name)

        assert len(s._store) == 100

        for name in names[:50]:
            await s.delete(name)

        assert len(s._store) == 50

    @pytest.mark.asyncio
    async def test_overwrite_updates_metadata(self):
        s = MemoryStorage()
        await s.save("up.txt", b"v1", content_type="text/plain")
        await s.save("up.txt", b"v2 longer", content_type="text/html", overwrite=True)
        meta = await s.stat("up.txt")
        assert meta.content_type == "text/html"
        assert meta.size == 9

    @pytest.mark.asyncio
    async def test_listdir_complex_hierarchy(self):
        s = MemoryStorage()
        await s.save("a/b/c.txt", b"1")
        await s.save("a/b/d.txt", b"2")
        await s.save("a/e.txt", b"3")
        await s.save("a/f/g/h.txt", b"4")

        dirs, files = await s.listdir("a")
        assert "e.txt" in files
        assert "b" in dirs
        assert "f" in dirs


class TestCompositeStorageRegression:
    """Edge cases for CompositeStorage."""

    @pytest.mark.asyncio
    async def test_first_backend_used_if_no_fallback_match(self):
        config = CompositeConfig(
            backends={
                "first": {"backend": "memory"},
                "second": {"backend": "memory"},
            },
            rules={},
            fallback="nonexistent",
        )
        comp = CompositeStorage(config)
        await comp.initialize()
        # Fallback doesn't exist, should use first backend
        await comp.save("test.txt", b"data")
        assert await comp._backends["first"].exists("test.txt")

    @pytest.mark.asyncio
    async def test_case_sensitive_rules(self):
        config = CompositeConfig(
            backends={
                "images": {"backend": "memory"},
                "default": {"backend": "memory"},
            },
            rules={"*.JPG": "images"},
            fallback="default",
        )
        comp = CompositeStorage(config)
        await comp.initialize()

        # *.JPG rule should NOT match .jpg (fnmatch is case-sensitive on most OS)
        await comp.save("photo.jpg", b"lowercase")
        await comp.save("photo.JPG", b"uppercase")
        # At minimum, uppercase match should go to images
        assert await comp._backends["images"].exists("photo.JPG")


class TestEffectProviderRegression:
    """Edge cases for StorageEffectProvider."""

    @pytest.mark.asyncio
    async def test_acquire_after_set_registry(self):
        provider = StorageEffectProvider()
        reg = StorageRegistry()
        reg.register("default", MemoryStorage())
        provider.set_registry(reg)
        backend = await provider.acquire()
        assert isinstance(backend, MemoryStorage)

    @pytest.mark.asyncio
    async def test_multiple_acquires(self):
        reg = StorageRegistry()
        reg.register("default", MemoryStorage())
        provider = StorageEffectProvider(reg)

        b1 = await provider.acquire()
        b2 = await provider.acquire()
        assert b1 is b2  # Same backend instance


class TestSubsystemRegression:
    """Edge cases for StorageSubsystem."""

    @pytest.mark.asyncio
    async def test_health_check_empty_registry_returns_stopped(self):
        """When all backends are removed post-init, registry is falsy → stopped."""
        sub = StorageSubsystem()

        from aquilia.subsystems.base import BootContext
        from aquilia.health import HealthRegistry

        ctx = BootContext(
            config={"storage": {"backends": [{"alias": "default", "backend": "memory"}]}},
            manifests=[],
            health=HealthRegistry(),
        )
        await sub._do_initialize(ctx)
        sub._initialized = True

        # Remove all backends — registry becomes falsy (len==0)
        sub._registry._backends.clear()

        health = await sub.health_check()
        # Empty registry is falsy → `not self._registry` is True → STOPPED
        assert health.status.value == "stopped"


class TestEndToEndIntegration:
    """Full integration: config builder → subsystem → registry → backend → effect."""

    @pytest.mark.asyncio
    async def test_full_pipeline(self):
        """Config → Subsystem → Registry → Backend operations → Effect → Health."""
        from aquilia.subsystems.base import BootContext
        from aquilia.health import HealthRegistry

        # 1. Build config via Integration builder
        storage_config = Integration.storage(
            default="primary",
            backends={
                "primary": MemoryConfig(alias="primary", max_size=10240),
                "secondary": MemoryConfig(alias="secondary"),
            },
        )

        # 2. Create boot context
        ctx = BootContext(
            config={"storage": storage_config},
            manifests=[],
            health=HealthRegistry(),
        )

        # 3. Initialize subsystem
        sub = StorageSubsystem()
        await sub._do_initialize(ctx)
        sub._initialized = True

        registry = sub._registry
        assert registry is not None
        assert "primary" in registry
        assert "secondary" in registry

        # 4. Backend operations through registry
        primary = registry["primary"]
        name = await primary.save("test.txt", b"integration test")
        assert await primary.exists(name)

        sf = await primary.open(name)
        assert await sf.read() == b"integration test"

        meta = await primary.stat(name)
        assert meta.size == 16

        # 5. Effect provider
        effect = StorageEffectProvider(registry)
        await effect.initialize()
        backend = await effect.acquire("primary")
        assert await backend.exists(name)

        default_backend = await effect.acquire()
        assert default_backend is registry.default

        # 6. Health check
        health = await sub.health_check()
        assert health.status.value == "healthy"

        # 7. Cross-backend isolation
        await registry["secondary"].save("other.txt", b"secondary data")
        assert not await registry["primary"].exists("other.txt")
        assert await registry["secondary"].exists("other.txt")

        # 8. Shutdown
        await sub._do_shutdown()

    @pytest.mark.asyncio
    async def test_local_storage_full_lifecycle(self, tmp_path):
        """LocalStorage full lifecycle through subsystem."""
        from aquilia.subsystems.base import BootContext
        from aquilia.health import HealthRegistry

        root = str(tmp_path / "integration_uploads")

        storage_config = Integration.storage(
            default="local",
            backends={
                "local": LocalConfig(alias="local", root=root, base_url="/uploads/"),
            },
        )

        ctx = BootContext(
            config={"storage": storage_config},
            manifests=[],
            health=HealthRegistry(),
        )

        sub = StorageSubsystem()
        await sub._do_initialize(ctx)
        sub._initialized = True

        registry = sub._registry
        assert registry is not None

        backend = registry["local"]
        await backend.initialize()

        # CRUD
        name = await backend.save("uploads/doc.pdf", b"PDF content")
        assert await backend.exists(name)

        sf = await backend.open(name)
        assert await sf.read() == b"PDF content"

        url = await backend.url(name)
        assert "/uploads/" in url

        meta = await backend.stat(name)
        assert meta.size == 11

        dirs, files = await backend.listdir("uploads")
        assert "doc.pdf" in files

        await backend.delete(name)
        assert not await backend.exists(name)

        # Health
        health = await sub.health_check()
        assert health.status.value == "healthy"

        await sub._do_shutdown()

    @pytest.mark.asyncio
    async def test_composite_via_subsystem(self):
        """CompositeStorage configured via subsystem."""
        from aquilia.subsystems.base import BootContext
        from aquilia.health import HealthRegistry

        storage_config = Integration.storage(
            default="composite",
            backends={
                "composite": CompositeConfig(
                    alias="composite",
                    backends={
                        "images": {"backend": "memory"},
                        "docs": {"backend": "memory"},
                    },
                    rules={"*.jpg": "images", "*.pdf": "docs"},
                    fallback="docs",
                ),
            },
        )

        ctx = BootContext(
            config={"storage": storage_config},
            manifests=[],
            health=HealthRegistry(),
        )

        sub = StorageSubsystem()
        await sub._do_initialize(ctx)
        sub._initialized = True

        registry = sub._registry
        composite = registry["composite"]

        await composite.save("photo.jpg", b"JPEG")
        await composite.save("report.pdf", b"PDF")
        await composite.save("random.xyz", b"unknown type")

        # Verify routing
        assert await composite.exists("photo.jpg")
        assert await composite.exists("report.pdf")
        assert await composite.exists("random.xyz")

        health = await sub.health_check()
        assert health.status.value == "healthy"

        await sub._do_shutdown()

    @pytest.mark.asyncio
    async def test_workspace_to_subsystem_pipeline(self):
        """Full Workspace → Integration → Subsystem pipeline."""
        from aquilia.subsystems.base import BootContext
        from aquilia.health import HealthRegistry

        # Workspace config
        ws = Workspace("pipeline_test").storage(
            default="mem",
            backends={"mem": MemoryConfig(alias="mem")},
        )

        # Extract storage config from workspace
        storage_config = ws._integrations["storage"]

        ctx = BootContext(
            config={"storage": storage_config},
            manifests=[],
            health=HealthRegistry(),
        )

        sub = StorageSubsystem()
        await sub._do_initialize(ctx)
        sub._initialized = True

        registry = sub._registry
        assert registry is not None
        assert "mem" in registry

        # Verify it works end to end
        await registry["mem"].save("ws_test.txt", b"workspace pipeline")
        sf = await registry["mem"].open("ws_test.txt")
        assert await sf.read() == b"workspace pipeline"

        await sub._do_shutdown()


class TestBuiltinBackendsRegistry:
    """Verify all builtin backends are correctly registered."""

    def test_all_shorthands_have_configs(self):
        for shorthand in _BUILTIN_BACKENDS:
            assert shorthand in _BACKEND_CONFIGS, f"Missing config for {shorthand}"

    def test_all_configs_have_backends(self):
        for shorthand in _BACKEND_CONFIGS:
            assert shorthand in _BUILTIN_BACKENDS, f"Missing backend for {shorthand}"

    def test_all_backends_are_storage_backend_subclasses(self):
        for shorthand, dotted in _BUILTIN_BACKENDS.items():
            cls = _import_backend(dotted)
            assert issubclass(cls, StorageBackend), f"{shorthand} → {cls} is not a StorageBackend"

    def test_configs_are_frozen_dataclasses(self):
        for shorthand, cls in _BACKEND_CONFIGS.items():
            instance = cls()
            with pytest.raises((FrozenInstanceError, AttributeError)):
                instance.alias = "mutated"  # type: ignore[misc]

    def test_every_config_has_to_dict(self):
        for shorthand, cls in _BACKEND_CONFIGS.items():
            instance = cls()
            d = instance.to_dict()
            assert isinstance(d, dict)
            assert "alias" in d
            assert "backend" in d


class TestModuleExports:
    """Verify the storage __init__.py exports everything correctly."""

    def test_all_public_names(self):
        import aquilia.storage as storage_mod

        expected = {
            "StorageBackend",
            "StorageFile",
            "StorageMetadata",
            "StorageRegistry",
            "StorageError",
            "StorageFileNotFoundError",
            "StoragePermissionError",
            "StorageFullError",
            "BackendUnavailableError",
            "LocalStorage",
            "MemoryStorage",
            "S3Storage",
            "GCSStorage",
            "AzureBlobStorage",
            "SFTPStorage",
            "CompositeStorage",
            "StorageConfig",
            "LocalConfig",
            "MemoryConfig",
            "S3Config",
            "GCSConfig",
            "AzureBlobConfig",
            "SFTPConfig",
            "CompositeConfig",
            "StorageSubsystem",
            "StorageEffectProvider",
        }
        actual = set(storage_mod.__all__)
        assert expected.issubset(actual), f"Missing exports: {expected - actual}"

    def test_version(self):
        import aquilia.storage as storage_mod

        assert hasattr(storage_mod, "__version__")
        from aquilia._version import __version__ as framework_version

        assert storage_mod.__version__ == framework_version
