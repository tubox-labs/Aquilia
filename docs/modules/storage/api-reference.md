# Storage API Reference

This page is extracted from the current Python source. It includes public classes, methods, functions, constants, dataclass-like fields, decorators, and notable attributes.

## Public Class Summary

| Name | Source | Bases | Purpose |
| --- | --- | --- | --- |
| `AzureBlobStorage` | `aquilia/storage/backends/azure.py` | StorageBackend | Azure Blob Storage backend. |
| `CompositeStorage` | `aquilia/storage/backends/composite.py` | StorageBackend | Composite storage that routes files to sub-backends by rules. |
| `GCSStorage` | `aquilia/storage/backends/gcs.py` | StorageBackend | Google Cloud Storage backend. |
| `LocalStorage` | `aquilia/storage/backends/local.py` | StorageBackend | Local filesystem storage backend. |
| `MemoryStorage` | `aquilia/storage/backends/memory.py` | StorageBackend | In-memory storage backend. |
| `S3Storage` | `aquilia/storage/backends/s3.py` | StorageBackend | Amazon S3 / S3-compatible storage backend. |
| `SFTPStorage` | `aquilia/storage/backends/sftp.py` | StorageBackend | SFTP storage backend. |
| `StorageError` | `aquilia/storage/base.py` | Fault | Base fault for all storage operations. |
| `FileNotFoundError` | `aquilia/storage/base.py` | StorageError | Raised when a file does not exist in the storage backend. |
| `PermissionError` | `aquilia/storage/base.py` | StorageError | Raised when the caller lacks permission for the operation. |
| `StorageFullError` | `aquilia/storage/base.py` | StorageError | Raised when the storage quota is exceeded. |
| `BackendUnavailableError` | `aquilia/storage/base.py` | StorageError | Raised when the storage backend is unreachable or not configured. |
| `StorageIOFault` | `aquilia/storage/base.py` | StorageError | Raised on I/O operation errors (closed file, wrong mode). |
| `StorageConfigFault` | `aquilia/storage/base.py` | StorageError | Raised on storage configuration / registry errors. |
| `StorageMetadata` | `aquilia/storage/base.py` | object | Immutable metadata for a stored file. |
| `StorageFile` | `aquilia/storage/base.py` | object | Async file wrapper returned by ``StorageBackend.open()``. |
| `StorageBackend` | `aquilia/storage/base.py` | ABC | Abstract storage backend. |
| `StorageConfig` | `aquilia/storage/configs.py` | object | Base storage configuration. |
| `LocalConfig` | `aquilia/storage/configs.py` | StorageConfig | Configuration for the local filesystem storage backend. |
| `MemoryConfig` | `aquilia/storage/configs.py` | StorageConfig | Configuration for the in-memory storage backend (testing). |
| `S3Config` | `aquilia/storage/configs.py` | StorageConfig | Configuration for Amazon S3 or S3-compatible storage. |
| `GCSConfig` | `aquilia/storage/configs.py` | StorageConfig | Configuration for Google Cloud Storage. |
| `AzureBlobConfig` | `aquilia/storage/configs.py` | StorageConfig | Configuration for Azure Blob Storage. |
| `SFTPConfig` | `aquilia/storage/configs.py` | StorageConfig | Configuration for SFTP/SSH storage. |
| `CompositeConfig` | `aquilia/storage/configs.py` | StorageConfig | Configuration for the composite (multi-backend) storage. |
| `StorageEffectProvider` | `aquilia/storage/effects.py` | EffectProvider | Effect provider that yields ``StorageBackend`` instances |
| `StorageRegistry` | `aquilia/storage/registry.py` | object | Named registry of storage backends. |
| `StorageSubsystem` | `aquilia/storage/subsystem.py` | BaseSubsystem | Subsystem initializer for the Aquilia storage system. |

## Public Function Summary

| Name | Source | Signature | Purpose |
| --- | --- | --- | --- |
| `config_from_dict` | `aquilia/storage/configs.py` | `def config_from_dict(data: dict[str, Any]) -> StorageConfig` | Instantiate a typed StorageConfig from a raw dict. |
| `create_backend` | `aquilia/storage/registry.py` | `def create_backend(config: StorageConfig) -> StorageBackend` | Instantiate a ``StorageBackend`` from a ``StorageConfig``. |

## Constants

| Name | Source | Value or type |
| --- | --- | --- |
| `STORAGE_DOMAIN` | `aquilia/storage/base.py` | `FaultDomain.custom('storage', 'File storage faults')` |
| `_BACKEND_CONFIGS` | `aquilia/storage/configs.py` | `{'local': LocalConfig, 'memory': MemoryConfig, 's3': S3Config, 'gcs': GCSConfig, 'azure': AzureBlobConfig, 'sftp': SFTPConfig, 'composite': CompositeConfig}` |
| `_BUILTIN_BACKENDS` | `aquilia/storage/registry.py` | `dict[str, str]` |

## Detailed Classes And Methods

### Class: `AzureBlobStorage`

- Source: `aquilia/storage/backends/azure.py`
- Bases: `StorageBackend`
- Summary: Azure Blob Storage backend.

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `backend_name` | `def backend_name(self) -> str` | property | Method. |
| `initialize` | `async def initialize(self) -> None` |  | Method. |
| `shutdown` | `async def shutdown(self) -> None` |  | Method. |
| `ping` | `async def ping(self) -> bool` |  | Method. |
| `save` | `async def save(self, name: str, content: bytes &#124; BinaryIO &#124; AsyncIterator[bytes] &#124; StorageFile, *, content_type: str &#124; None = None, metadata: dict[str, str] &#124; None = None, overwrite: bool = False) -> str` |  | Method. |
| `open` | `async def open(self, name: str, mode: str = 'rb') -> StorageFile` |  | Method. |
| `delete` | `async def delete(self, name: str) -> None` |  | Method. |
| `exists` | `async def exists(self, name: str) -> bool` |  | Method. |
| `stat` | `async def stat(self, name: str) -> StorageMetadata` |  | Method. |
| `listdir` | `async def listdir(self, path: str = '') -> tuple[list[str], list[str]]` |  | Method. |
| `size` | `async def size(self, name: str) -> int` |  | Method. |
| `url` | `async def url(self, name: str, expire: int &#124; None = None) -> str` |  | Method. |

### Class: `CompositeStorage`

- Source: `aquilia/storage/backends/composite.py`
- Bases: `StorageBackend`
- Summary: Composite storage that routes files to sub-backends by rules.

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `backend_name` | `def backend_name(self) -> str` | property | Method. |
| `initialize` | `async def initialize(self) -> None` |  | Method. |
| `shutdown` | `async def shutdown(self) -> None` |  | Method. |
| `ping` | `async def ping(self) -> bool` |  | Method. |
| `save` | `async def save(self, name: str, content: bytes &#124; BinaryIO &#124; AsyncIterator[bytes] &#124; StorageFile, *, content_type: str &#124; None = None, metadata: dict[str, str] &#124; None = None, overwrite: bool = False) -> str` |  | Method. |
| `open` | `async def open(self, name: str, mode: str = 'rb') -> StorageFile` |  | Method. |
| `delete` | `async def delete(self, name: str) -> None` |  | Method. |
| `exists` | `async def exists(self, name: str) -> bool` |  | Method. |
| `stat` | `async def stat(self, name: str) -> StorageMetadata` |  | Method. |
| `listdir` | `async def listdir(self, path: str = '') -> tuple[list[str], list[str]]` |  | Method. |
| `size` | `async def size(self, name: str) -> int` |  | Method. |
| `url` | `async def url(self, name: str, expire: int &#124; None = None) -> str` |  | Method. |

### Class: `GCSStorage`

- Source: `aquilia/storage/backends/gcs.py`
- Bases: `StorageBackend`
- Summary: Google Cloud Storage backend.

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `backend_name` | `def backend_name(self) -> str` | property | Method. |
| `initialize` | `async def initialize(self) -> None` |  | Method. |
| `shutdown` | `async def shutdown(self) -> None` |  | Method. |
| `ping` | `async def ping(self) -> bool` |  | Method. |
| `save` | `async def save(self, name: str, content: bytes &#124; BinaryIO &#124; AsyncIterator[bytes] &#124; StorageFile, *, content_type: str &#124; None = None, metadata: dict[str, str] &#124; None = None, overwrite: bool = False) -> str` |  | Method. |
| `open` | `async def open(self, name: str, mode: str = 'rb') -> StorageFile` |  | Method. |
| `delete` | `async def delete(self, name: str) -> None` |  | Method. |
| `exists` | `async def exists(self, name: str) -> bool` |  | Method. |
| `stat` | `async def stat(self, name: str) -> StorageMetadata` |  | Method. |
| `listdir` | `async def listdir(self, path: str = '') -> tuple[list[str], list[str]]` |  | Method. |
| `size` | `async def size(self, name: str) -> int` |  | Method. |
| `url` | `async def url(self, name: str, expire: int &#124; None = None) -> str` |  | Method. |

### Class: `LocalStorage`

- Source: `aquilia/storage/backends/local.py`
- Bases: `StorageBackend`
- Summary: Local filesystem storage backend.

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `backend_name` | `def backend_name(self) -> str` | property | Method. |
| `initialize` | `async def initialize(self) -> None` |  | Method. |
| `ping` | `async def ping(self) -> bool` |  | Method. |
| `save` | `async def save(self, name: str, content: bytes &#124; BinaryIO &#124; AsyncIterator[bytes] &#124; StorageFile, *, content_type: str &#124; None = None, metadata: dict[str, str] &#124; None = None, overwrite: bool = False) -> str` |  | Method. |
| `open` | `async def open(self, name: str, mode: str = 'rb') -> StorageFile` |  | Method. |
| `delete` | `async def delete(self, name: str) -> None` |  | Method. |
| `exists` | `async def exists(self, name: str) -> bool` |  | Method. |
| `stat` | `async def stat(self, name: str) -> StorageMetadata` |  | Method. |
| `listdir` | `async def listdir(self, path: str = '') -> tuple[list[str], list[str]]` |  | Method. |
| `size` | `async def size(self, name: str) -> int` |  | Method. |
| `url` | `async def url(self, name: str, expire: int &#124; None = None) -> str` |  | Method. |
| `copy` | `async def copy(self, src: str, dst: str) -> str` |  | Method. |

### Class: `MemoryStorage`

- Source: `aquilia/storage/backends/memory.py`
- Bases: `StorageBackend`
- Summary: In-memory storage backend.

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `backend_name` | `def backend_name(self) -> str` | property | Method. |
| `initialize` | `async def initialize(self) -> None` |  | Method. |
| `shutdown` | `async def shutdown(self) -> None` |  | Method. |
| `ping` | `async def ping(self) -> bool` |  | Method. |
| `save` | `async def save(self, name: str, content: bytes &#124; BinaryIO &#124; AsyncIterator[bytes] &#124; StorageFile, *, content_type: str &#124; None = None, metadata: dict[str, str] &#124; None = None, overwrite: bool = False) -> str` |  | Method. |
| `open` | `async def open(self, name: str, mode: str = 'rb') -> StorageFile` |  | Method. |
| `delete` | `async def delete(self, name: str) -> None` |  | Method. |
| `exists` | `async def exists(self, name: str) -> bool` |  | Method. |
| `stat` | `async def stat(self, name: str) -> StorageMetadata` |  | Method. |
| `listdir` | `async def listdir(self, path: str = '') -> tuple[list[str], list[str]]` |  | Method. |
| `size` | `async def size(self, name: str) -> int` |  | Method. |
| `url` | `async def url(self, name: str, expire: int &#124; None = None) -> str` |  | Method. |

### Class: `S3Storage`

- Source: `aquilia/storage/backends/s3.py`
- Bases: `StorageBackend`
- Summary: Amazon S3 / S3-compatible storage backend.

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `backend_name` | `def backend_name(self) -> str` | property | Method. |
| `initialize` | `async def initialize(self) -> None` |  | Method. |
| `shutdown` | `async def shutdown(self) -> None` |  | Method. |
| `ping` | `async def ping(self) -> bool` |  | Method. |
| `save` | `async def save(self, name: str, content: bytes &#124; BinaryIO &#124; AsyncIterator[bytes] &#124; StorageFile, *, content_type: str &#124; None = None, metadata: dict[str, str] &#124; None = None, overwrite: bool = False) -> str` |  | Method. |
| `open` | `async def open(self, name: str, mode: str = 'rb') -> StorageFile` |  | Method. |
| `delete` | `async def delete(self, name: str) -> None` |  | Method. |
| `exists` | `async def exists(self, name: str) -> bool` |  | Method. |
| `stat` | `async def stat(self, name: str) -> StorageMetadata` |  | Method. |
| `listdir` | `async def listdir(self, path: str = '') -> tuple[list[str], list[str]]` |  | Method. |
| `size` | `async def size(self, name: str) -> int` |  | Method. |
| `url` | `async def url(self, name: str, expire: int &#124; None = None) -> str` |  | Method. |

### Class: `SFTPStorage`

- Source: `aquilia/storage/backends/sftp.py`
- Bases: `StorageBackend`
- Summary: SFTP storage backend.

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `backend_name` | `def backend_name(self) -> str` | property | Method. |
| `initialize` | `async def initialize(self) -> None` |  | Method. |
| `shutdown` | `async def shutdown(self) -> None` |  | Method. |
| `ping` | `async def ping(self) -> bool` |  | Method. |
| `save` | `async def save(self, name: str, content: bytes &#124; BinaryIO &#124; AsyncIterator[bytes] &#124; StorageFile, *, content_type: str &#124; None = None, metadata: dict[str, str] &#124; None = None, overwrite: bool = False) -> str` |  | Method. |
| `open` | `async def open(self, name: str, mode: str = 'rb') -> StorageFile` |  | Method. |
| `delete` | `async def delete(self, name: str) -> None` |  | Method. |
| `exists` | `async def exists(self, name: str) -> bool` |  | Method. |
| `stat` | `async def stat(self, name: str) -> StorageMetadata` |  | Method. |
| `listdir` | `async def listdir(self, path: str = '') -> tuple[list[str], list[str]]` |  | Method. |
| `size` | `async def size(self, name: str) -> int` |  | Method. |
| `url` | `async def url(self, name: str, expire: int &#124; None = None) -> str` |  | Method. |

### Class: `StorageError`

- Source: `aquilia/storage/base.py`
- Bases: `Fault`
- Summary: Base fault for all storage operations.

### Class: `FileNotFoundError`

- Source: `aquilia/storage/base.py`
- Bases: `StorageError`
- Summary: Raised when a file does not exist in the storage backend.

### Class: `PermissionError`

- Source: `aquilia/storage/base.py`
- Bases: `StorageError`
- Summary: Raised when the caller lacks permission for the operation.

### Class: `StorageFullError`

- Source: `aquilia/storage/base.py`
- Bases: `StorageError`
- Summary: Raised when the storage quota is exceeded.

### Class: `BackendUnavailableError`

- Source: `aquilia/storage/base.py`
- Bases: `StorageError`
- Summary: Raised when the storage backend is unreachable or not configured.

### Class: `StorageIOFault`

- Source: `aquilia/storage/base.py`
- Bases: `StorageError`
- Summary: Raised on I/O operation errors (closed file, wrong mode).

### Class: `StorageConfigFault`

- Source: `aquilia/storage/base.py`
- Bases: `StorageError`
- Summary: Raised on storage configuration / registry errors.

### Class: `StorageMetadata`

- Source: `aquilia/storage/base.py`
- Bases: `object`
- Decorators: `dataclass`
- Summary: Immutable metadata for a stored file.

Attributes and fields:

| Name | Type | Default |
| --- | --- | --- |
| `name` | `str` |  |
| `size` | `int` | `0` |
| `content_type` | `str` | `'application/octet-stream'` |
| `etag` | `str` | `''` |
| `last_modified` | `datetime &#124; None` | `None` |
| `created_at` | `datetime &#124; None` | `None` |
| `metadata` | `dict[str, str]` | `field(default_factory=dict)` |
| `storage_class` | `str` | `''` |

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `to_dict` | `def to_dict(self) -> dict[str, Any]` |  | Method. |

### Class: `StorageFile`

- Source: `aquilia/storage/base.py`
- Bases: `object`
- Summary: Async file wrapper returned by ``StorageBackend.open()``.

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `read` | `async def read(self, size: int = -1) -> bytes` |  | Read bytes from the file. |
| `write` | `async def write(self, data: bytes) -> int` |  | Write bytes (for writable files). |
| `seek` | `async def seek(self, pos: int) -> None` |  | Seek to byte position (clamped to valid range). |
| `tell` | `async def tell(self) -> int` |  | Return current byte position. |
| `content` | `def content(self) -> bytes &#124; None` | property | Return raw content bytes (or None if not materialised). |
| `close` | `async def close(self) -> None` |  | Release resources. |
| `closed` | `def closed(self) -> bool` | property | Method. |
| `size` | `def size(self) -> int` | property | Method. |

### Class: `StorageBackend`

- Source: `aquilia/storage/base.py`
- Bases: `ABC`
- Summary: Abstract storage backend.

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `backend_name` | `def backend_name(self) -> str` | property, abstractmethod | Human-readable backend identifier (e.g. 'local', 's3'). |
| `initialize` | `async def initialize(self) -> None` |  | Async initialization (create dirs, connect to remote, etc.). |
| `shutdown` | `async def shutdown(self) -> None` |  | Graceful shutdown (close connections, flush buffers). |
| `ping` | `async def ping(self) -> bool` |  | Health check - return True if the backend is reachable. |
| `save` | `async def save(self, name: str, content: bytes &#124; BinaryIO &#124; AsyncIterator[bytes] &#124; StorageFile, *, content_type: str &#124; None = None, metadata: dict[str, str] &#124; None = None, overwrite: bool = False) -> str` | abstractmethod | Save content under ``name``. |
| `open` | `async def open(self, name: str, mode: str = 'rb') -> StorageFile` | abstractmethod | Open a file for reading. |
| `delete` | `async def delete(self, name: str) -> None` | abstractmethod | Delete a file.  Idempotent - does NOT raise if missing. |
| `exists` | `async def exists(self, name: str) -> bool` | abstractmethod | Check if a file exists. |
| `stat` | `async def stat(self, name: str) -> StorageMetadata` | abstractmethod | Return metadata for a file. |
| `listdir` | `async def listdir(self, path: str = '') -> tuple[list[str], list[str]]` | abstractmethod | List contents of a directory/prefix. |
| `size` | `async def size(self, name: str) -> int` | abstractmethod | Return file size in bytes. |
| `url` | `async def url(self, name: str, expire: int &#124; None = None) -> str` | abstractmethod | Return a URL for accessing the file. |
| `copy` | `async def copy(self, src: str, dst: str) -> str` |  | Copy a file within the same backend. |
| `move` | `async def move(self, src: str, dst: str) -> str` |  | Move a file within the same backend. |
| `generate_filename` | `def generate_filename(self, filename: str) -> str` |  | Generate a safe, unique filename. |
| `get_valid_name` | `def get_valid_name(name: str) -> str` | staticmethod | Return a filesystem-safe filename. |
| `guess_content_type` | `def guess_content_type(name: str) -> str` | staticmethod | Guess MIME type from filename. |

### Class: `StorageConfig`

- Source: `aquilia/storage/configs.py`
- Bases: `object`
- Decorators: `dataclass`
- Summary: Base storage configuration.

Attributes and fields:

| Name | Type | Default |
| --- | --- | --- |
| `alias` | `str` | `'default'` |
| `backend` | `str` | `''` |
| `default` | `bool` | `False` |

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `to_dict` | `def to_dict(self) -> dict[str, Any]` |  | Method. |

### Class: `LocalConfig`

- Source: `aquilia/storage/configs.py`
- Bases: `StorageConfig`
- Decorators: `dataclass`
- Summary: Configuration for the local filesystem storage backend.

Attributes and fields:

| Name | Type | Default |
| --- | --- | --- |
| `backend` | `str` | `'local'` |
| `root` | `str` | `'./storage'` |
| `base_url` | `str` | `'/storage/'` |
| `permissions` | `int` | `420` |
| `dir_permissions` | `int` | `493` |
| `create_dirs` | `bool` | `True` |

### Class: `MemoryConfig`

- Source: `aquilia/storage/configs.py`
- Bases: `StorageConfig`
- Decorators: `dataclass`
- Summary: Configuration for the in-memory storage backend (testing).

Attributes and fields:

| Name | Type | Default |
| --- | --- | --- |
| `backend` | `str` | `'memory'` |
| `max_size` | `int` | `0` |

### Class: `S3Config`

- Source: `aquilia/storage/configs.py`
- Bases: `StorageConfig`
- Decorators: `dataclass`
- Summary: Configuration for Amazon S3 or S3-compatible storage.

Attributes and fields:

| Name | Type | Default |
| --- | --- | --- |
| `backend` | `str` | `'s3'` |
| `bucket` | `str` | `''` |
| `region` | `str` | `'us-east-1'` |
| `access_key` | `str &#124; None` | `None` |
| `secret_key` | `str &#124; None` | `None` |
| `session_token` | `str &#124; None` | `None` |
| `endpoint_url` | `str &#124; None` | `None` |
| `prefix` | `str` | `''` |
| `signature_version` | `str` | `'s3v4'` |
| `use_ssl` | `bool` | `True` |
| `addressing_style` | `str` | `'auto'` |
| `default_acl` | `str &#124; None` | `None` |
| `storage_class` | `str` | `'STANDARD'` |
| `presigned_expiry` | `int` | `3600` |
| `transfer_config` | `dict[str, Any]` | `field(default_factory=dict)` |

### Class: `GCSConfig`

- Source: `aquilia/storage/configs.py`
- Bases: `StorageConfig`
- Decorators: `dataclass`
- Summary: Configuration for Google Cloud Storage.

Attributes and fields:

| Name | Type | Default |
| --- | --- | --- |
| `backend` | `str` | `'gcs'` |
| `bucket` | `str` | `''` |
| `project` | `str &#124; None` | `None` |
| `credentials_path` | `str &#124; None` | `None` |
| `credentials_json` | `str &#124; None` | `None` |
| `prefix` | `str` | `''` |
| `default_acl` | `str &#124; None` | `None` |
| `location` | `str` | `''` |
| `presigned_expiry` | `int` | `3600` |

### Class: `AzureBlobConfig`

- Source: `aquilia/storage/configs.py`
- Bases: `StorageConfig`
- Decorators: `dataclass`
- Summary: Configuration for Azure Blob Storage.

Attributes and fields:

| Name | Type | Default |
| --- | --- | --- |
| `backend` | `str` | `'azure'` |
| `container` | `str` | `''` |
| `connection_string` | `str &#124; None` | `None` |
| `account_name` | `str &#124; None` | `None` |
| `account_key` | `str &#124; None` | `None` |
| `sas_token` | `str &#124; None` | `None` |
| `prefix` | `str` | `''` |
| `custom_domain` | `str &#124; None` | `None` |
| `presigned_expiry` | `int` | `3600` |
| `overwrite` | `bool` | `False` |

### Class: `SFTPConfig`

- Source: `aquilia/storage/configs.py`
- Bases: `StorageConfig`
- Decorators: `dataclass`
- Summary: Configuration for SFTP/SSH storage.

Attributes and fields:

| Name | Type | Default |
| --- | --- | --- |
| `backend` | `str` | `'sftp'` |
| `host` | `str` | `'localhost'` |
| `port` | `int` | `22` |
| `username` | `str` | `''` |
| `password` | `str &#124; None` | `None` |
| `key_path` | `str &#124; None` | `None` |
| `key_passphrase` | `str &#124; None` | `None` |
| `root` | `str` | `'/'` |
| `known_hosts` | `str &#124; None` | `None` |
| `base_url` | `str` | `''` |
| `timeout` | `int` | `30` |

### Class: `CompositeConfig`

- Source: `aquilia/storage/configs.py`
- Bases: `StorageConfig`
- Decorators: `dataclass`
- Summary: Configuration for the composite (multi-backend) storage.

Attributes and fields:

| Name | Type | Default |
| --- | --- | --- |
| `backend` | `str` | `'composite'` |
| `backends` | `dict[str, dict[str, Any]]` | `field(default_factory=dict)` |
| `rules` | `dict[str, str]` | `field(default_factory=dict)` |
| `fallback` | `str` | `'default'` |

### Class: `StorageEffectProvider`

- Source: `aquilia/storage/effects.py`
- Bases: `EffectProvider`
- Summary: Effect provider that yields ``StorageBackend`` instances

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `kind` | `def kind(self) -> EffectKind` | property | Method. |
| `set_registry` | `def set_registry(self, registry: Any) -> None` |  | Inject registry after construction (for deferred wiring). |
| `initialize` | `async def initialize(self) -> None` |  | No-op -- backends are initialised by StorageSubsystem. |
| `acquire` | `async def acquire(self, mode: str &#124; None = None) -> Any` |  | Acquire a storage backend. |
| `release` | `async def release(self, resource: Any, success: bool = True) -> None` |  | No-op -- storage backends are stateless per request. |
| `finalize` | `async def finalize(self) -> None` |  | No-op -- shutdown handled by StorageSubsystem. |

### Class: `StorageRegistry`

- Source: `aquilia/storage/registry.py`
- Bases: `object`
- Summary: Named registry of storage backends.

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `register` | `def register(self, alias: str, backend: StorageBackend) -> None` |  | Register a backend under an alias. |
| `unregister` | `def unregister(self, alias: str) -> StorageBackend &#124; None` |  | Remove and return a backend by alias. |
| `set_default` | `def set_default(self, alias: str) -> None` |  | Set which alias is the default backend. |
| `default` | `def default(self) -> StorageBackend` | property | Return the default backend. |
| `get` | `def get(self, alias: str) -> StorageBackend &#124; None` |  | Return a backend by alias, or None. |
| `aliases` | `def aliases(self) -> list[str]` |  | Return all registered aliases. |
| `items` | `def items(self) -> list[tuple[str, StorageBackend]]` |  | Method. |
| `initialize_all` | `async def initialize_all(self) -> None` |  | Initialize every registered backend. |
| `shutdown_all` | `async def shutdown_all(self) -> None` |  | Shutdown every registered backend. |
| `health_check` | `async def health_check(self) -> dict[str, bool]` |  | Ping every backend and return alias -> healthy map. |
| `from_config` | `def from_config(cls, configs: list[dict[str, Any]]) -> StorageRegistry` | classmethod | Build a registry from a list of config dicts. |

### Class: `StorageSubsystem`

- Source: `aquilia/storage/subsystem.py`
- Bases: `BaseSubsystem`
- Summary: Subsystem initializer for the Aquilia storage system.

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `health_check` | `async def health_check(self) -> HealthStatus` |  | Check health of all storage backends. |

## Functions

| Name | Source | Signature | Purpose |
| --- | --- | --- | --- |
| `config_from_dict` | `aquilia/storage/configs.py` | `def config_from_dict(data: dict[str, Any]) -> StorageConfig` | Instantiate a typed StorageConfig from a raw dict. |
| `create_backend` | `aquilia/storage/registry.py` | `def create_backend(config: StorageConfig) -> StorageBackend` | Instantiate a ``StorageBackend`` from a ``StorageConfig``. |

## Constants

| Name | Source | Value or type |
| --- | --- | --- |
| `STORAGE_DOMAIN` | `aquilia/storage/base.py` | `FaultDomain.custom('storage', 'File storage faults')` |
| `_BACKEND_CONFIGS` | `aquilia/storage/configs.py` | `{'local': LocalConfig, 'memory': MemoryConfig, 's3': S3Config, 'gcs': GCSConfig, 'azure': AzureBlobConfig, 'sftp': SFTPConfig, 'composite': CompositeConfig}` |
| `_BUILTIN_BACKENDS` | `aquilia/storage/registry.py` | `dict[str, str]` |
