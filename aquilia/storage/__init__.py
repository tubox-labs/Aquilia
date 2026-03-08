"""
Aquilia Storage -- Production-grade, async-first file storage abstraction.

Provides a unified API for storing, retrieving, and managing files across
multiple storage backends. Deeply integrated with Aquilia's DI, Config,
Effects, Blueprints, and Subsystem lifecycle.

Supported Backends:
    - LocalStorage      : Local filesystem (default)
    - MemoryStorage     : In-memory (testing/ephemeral)
    - S3Storage         : Amazon S3 / S3-compatible (MinIO, DigitalOcean Spaces)
    - GCSStorage        : Google Cloud Storage
    - AzureBlobStorage  : Azure Blob Storage
    - SFTPStorage       : SFTP/SSH remote filesystem
    - CompositeStorage  : Fan-out writes to multiple backends

Architecture:
    - StorageBackend    : ABC defining the backend contract (async)
    - StorageRegistry   : Named backend registry (keyed by alias)
    - StorageFile       : Async file wrapper with streaming support
    - StorageConfig     : Typed config dataclasses per backend
    - StorageSubsystem  : Lifecycle-managed subsystem initializer
    - StorageEffect     : Effect system integration for handler-level DI
    - Integration.storage() : Workspace config builder

Wiring:
    - DI: StorageRegistry registered as app-scoped singleton
    - Config: Integration.storage() + Workspace.storage()
    - Effects: EffectKind.STORAGE with StorageEffectProvider
    - Blueprints: FileFacet auto-wires to default storage
    - Subsystems: StorageSubsystem (priority 25, before DB)
    - Health: StorageHealthCheck per backend

Quick Start::

    # workspace.py
    from aquilia import Workspace, Integration
    from aquilia.storage import LocalConfig, S3Config

    workspace = (
        Workspace("myapp")
        .storage(
            default="local",
            backends={
                "local": LocalConfig(root="./uploads"),
                "media": S3Config(
                    bucket="my-bucket",
                    region="us-east-1",
                ),
            },
        )
    )

    # In a controller:
    from aquilia.storage import StorageRegistry

    class UploadController(Controller):
        def __init__(self, storage: StorageRegistry):
            self.storage = storage

        @POST("/upload")
        async def upload(self, ctx: RequestCtx):
            file = await ctx.file("attachment")
            path = await self.storage.default.save(
                f"uploads/{file.filename}", file
            )
            return {"path": path, "url": self.storage.default.url(path)}
"""

from aquilia._version import __version__  # noqa: F401 — re-exported

# ── Core abstractions ────────────────────────────────────────────────────
from .base import (
    StorageBackend,
    StorageFile,
    StorageMetadata,
    StorageError,
    FileNotFoundError as StorageFileNotFoundError,
    PermissionError as StoragePermissionError,
    StorageFullError,
    BackendUnavailableError,
    StorageIOFault,
    StorageConfigFault,
    STORAGE_DOMAIN,
)

# ── Backend implementations ──────────────────────────────────────────────
from .backends.local import LocalStorage
from .backends.memory import MemoryStorage
from .backends.s3 import S3Storage
from .backends.gcs import GCSStorage
from .backends.azure import AzureBlobStorage
from .backends.sftp import SFTPStorage
from .backends.composite import CompositeStorage

# ── Configuration dataclasses ────────────────────────────────────────────
from .configs import (
    StorageConfig,
    LocalConfig,
    MemoryConfig,
    S3Config,
    GCSConfig,
    AzureBlobConfig,
    SFTPConfig,
    CompositeConfig,
)

# ── Registry & wiring ───────────────────────────────────────────────────
from .registry import StorageRegistry

# ── Subsystem & effects ─────────────────────────────────────────────────
from .subsystem import StorageSubsystem
from .effects import StorageEffectProvider

__all__ = [
    # Core
    "StorageBackend",
    "StorageFile",
    "StorageMetadata",
    "StorageRegistry",
    # Errors
    "StorageError",
    "StorageFileNotFoundError",
    "StoragePermissionError",
    "StorageFullError",
    "BackendUnavailableError",
    "StorageIOFault",
    "StorageConfigFault",
    "STORAGE_DOMAIN",
    # Backends
    "LocalStorage",
    "MemoryStorage",
    "S3Storage",
    "GCSStorage",
    "AzureBlobStorage",
    "SFTPStorage",
    "CompositeStorage",
    # Configs
    "StorageConfig",
    "LocalConfig",
    "MemoryConfig",
    "S3Config",
    "GCSConfig",
    "AzureBlobConfig",
    "SFTPConfig",
    "CompositeConfig",
    # Subsystem
    "StorageSubsystem",
    "StorageEffectProvider",
]
