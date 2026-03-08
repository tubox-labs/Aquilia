"""
Storage Configs -- Typed configuration dataclasses for each backend.

Every config is a frozen dataclass that plugs into the Aquilia
``Workspace`` / ``Integration.storage()`` config builder chain.
The ``StorageSubsystem`` reads these at boot time to instantiate
the correct ``StorageBackend``.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


# ═══════════════════════════════════════════════════════════════════════════
# Base
# ═══════════════════════════════════════════════════════════════════════════

@dataclass(frozen=True, slots=True)
class StorageConfig:
    """
    Base storage configuration.

    Every backend-specific config extends this.
    ``alias`` is the registry key used to look up this backend.
    """
    alias: str = "default"
    backend: str = ""          # Dotted import path OR shorthand ('local', 's3', …)
    default: bool = False      # Mark this alias as the default backend

    def to_dict(self) -> Dict[str, Any]:
        from dataclasses import fields
        return {f.name: getattr(self, f.name) for f in fields(self)}


# ═══════════════════════════════════════════════════════════════════════════
# Local Filesystem
# ═══════════════════════════════════════════════════════════════════════════

@dataclass(frozen=True, slots=True)
class LocalConfig(StorageConfig):
    """Configuration for the local filesystem storage backend."""
    backend: str = "local"
    root: str = "./storage"             # Base directory
    base_url: str = "/storage/"         # URL prefix for serving files
    permissions: int = 0o644            # File permissions (Unix)
    dir_permissions: int = 0o755        # Directory permissions
    create_dirs: bool = True            # Auto-create directories on save


# ═══════════════════════════════════════════════════════════════════════════
# In-Memory
# ═══════════════════════════════════════════════════════════════════════════

@dataclass(frozen=True, slots=True)
class MemoryConfig(StorageConfig):
    """Configuration for the in-memory storage backend (testing)."""
    backend: str = "memory"
    max_size: int = 0                   # Max total bytes (0 = unlimited)


# ═══════════════════════════════════════════════════════════════════════════
# Amazon S3 / S3-compatible
# ═══════════════════════════════════════════════════════════════════════════

@dataclass(frozen=True, slots=True)
class S3Config(StorageConfig):
    """Configuration for Amazon S3 or S3-compatible storage."""
    backend: str = "s3"
    bucket: str = ""
    region: str = "us-east-1"
    access_key: Optional[str] = None
    secret_key: Optional[str] = None
    session_token: Optional[str] = None
    endpoint_url: Optional[str] = None      # For MinIO / DigitalOcean Spaces / etc.
    prefix: str = ""                        # Key prefix (virtual folder)
    signature_version: str = "s3v4"
    use_ssl: bool = True
    addressing_style: str = "auto"          # 'path' | 'virtual' | 'auto'
    default_acl: Optional[str] = None       # e.g. 'private', 'public-read'
    storage_class: str = "STANDARD"         # STANDARD, GLACIER, etc.
    presigned_expiry: int = 3600            # Default presigned URL expiry (seconds)
    transfer_config: Dict[str, Any] = field(default_factory=dict)  # boto3 TransferConfig


# ═══════════════════════════════════════════════════════════════════════════
# Google Cloud Storage
# ═══════════════════════════════════════════════════════════════════════════

@dataclass(frozen=True, slots=True)
class GCSConfig(StorageConfig):
    """Configuration for Google Cloud Storage."""
    backend: str = "gcs"
    bucket: str = ""
    project: Optional[str] = None
    credentials_path: Optional[str] = None      # Path to service account JSON
    credentials_json: Optional[str] = None      # Raw JSON string
    prefix: str = ""
    default_acl: Optional[str] = None
    location: str = ""                          # Bucket location
    presigned_expiry: int = 3600


# ═══════════════════════════════════════════════════════════════════════════
# Azure Blob Storage
# ═══════════════════════════════════════════════════════════════════════════

@dataclass(frozen=True, slots=True)
class AzureBlobConfig(StorageConfig):
    """Configuration for Azure Blob Storage."""
    backend: str = "azure"
    container: str = ""
    connection_string: Optional[str] = None
    account_name: Optional[str] = None
    account_key: Optional[str] = None
    sas_token: Optional[str] = None
    prefix: str = ""
    custom_domain: Optional[str] = None
    presigned_expiry: int = 3600
    overwrite: bool = False


# ═══════════════════════════════════════════════════════════════════════════
# SFTP / SSH
# ═══════════════════════════════════════════════════════════════════════════

@dataclass(frozen=True, slots=True)
class SFTPConfig(StorageConfig):
    """Configuration for SFTP/SSH storage."""
    backend: str = "sftp"
    host: str = "localhost"
    port: int = 22
    username: str = ""
    password: Optional[str] = None
    key_path: Optional[str] = None          # Path to SSH private key
    key_passphrase: Optional[str] = None
    root: str = "/"                         # Remote root directory
    known_hosts: Optional[str] = None
    base_url: str = ""                      # Public URL prefix
    timeout: int = 30


# ═══════════════════════════════════════════════════════════════════════════
# Composite / Multi-backend
# ═══════════════════════════════════════════════════════════════════════════

@dataclass(frozen=True, slots=True)
class CompositeConfig(StorageConfig):
    """
    Configuration for the composite (multi-backend) storage.

    Routes files to different backends based on rules.
    ``backends`` maps alias names to their StorageConfig instances.
    ``rules`` maps glob patterns to alias names.
    """
    backend: str = "composite"
    backends: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    rules: Dict[str, str] = field(default_factory=dict)     # glob → alias
    fallback: str = "default"                               # Alias to use if no rule matches


# ═══════════════════════════════════════════════════════════════════════════
# Factory
# ═══════════════════════════════════════════════════════════════════════════

_BACKEND_CONFIGS = {
    "local": LocalConfig,
    "memory": MemoryConfig,
    "s3": S3Config,
    "gcs": GCSConfig,
    "azure": AzureBlobConfig,
    "sftp": SFTPConfig,
    "composite": CompositeConfig,
}


def config_from_dict(data: Dict[str, Any]) -> StorageConfig:
    """
    Instantiate a typed StorageConfig from a raw dict.

    The ``backend`` key determines which config class to use.

    >>> config_from_dict({"backend": "s3", "bucket": "my-bucket"})
    S3Config(alias='default', backend='s3', bucket='my-bucket', ...)
    """
    backend = data.get("backend", "local")
    cls = _BACKEND_CONFIGS.get(backend, StorageConfig)

    # Filter out keys that don't belong to the dataclass
    valid_fields = {f.name for f in cls.__dataclass_fields__.values()}
    filtered = {k: v for k, v in data.items() if k in valid_fields}
    return cls(**filtered)
