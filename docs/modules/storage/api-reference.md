# Storage API Reference

This page is generated from the current Python source using the AST. It lists public classes, public methods, public module-level functions, constants, exports, and source files.

## Source Inventory

| File | Lines | Classes | Functions | Purpose |
| --- | ---: | ---: | ---: | --- |
| `aquilia/storage/__init__.py` | 155 | 0 | 0 | Aquilia Storage -- Production-grade, async-first file storage abstraction. |
| `aquilia/storage/backends/__init__.py` | 25 | 0 | 0 | Storage Backends -- concrete StorageBackend implementations. |
| `aquilia/storage/backends/azure.py` | 324 | 1 | 0 | Azure Blob Storage Backend. |
| `aquilia/storage/backends/composite.py` | 167 | 1 | 0 | Composite / Multi-Backend Storage. |
| `aquilia/storage/backends/gcs.py` | 279 | 1 | 0 | Google Cloud Storage Backend. |
| `aquilia/storage/backends/local.py` | 211 | 1 | 0 | Local Filesystem Storage Backend. |
| `aquilia/storage/backends/memory.py` | 158 | 1 | 0 | In-Memory Storage Backend. |
| `aquilia/storage/backends/s3.py` | 300 | 1 | 0 | Amazon S3 / S3-Compatible Storage Backend. |
| `aquilia/storage/backends/sftp.py` | 277 | 1 | 0 | SFTP / SSH Storage Backend. |
| `aquilia/storage/base.py` | 585 | 10 | 0 | Storage Base -- Abstract backend contract and core types. |
| `aquilia/storage/configs.py` | 209 | 8 | 1 | Storage Configs -- Typed configuration dataclasses for each backend. |
| `aquilia/storage/effects.py` | 81 | 1 | 0 | Storage Effect Provider -- Bridges storage into the Aquilia Effect system. |
| `aquilia/storage/registry.py` | 224 | 1 | 1 | Storage Registry -- Named backend registry. |
| `aquilia/storage/subsystem.py` | 171 | 1 | 0 | Storage Subsystem -- Aquilia boot lifecycle integration for storage. |

## Public Exports

`AzureBlobConfig`, `AzureBlobStorage`, `BackendUnavailableError`, `CompositeConfig`, `CompositeStorage`, `GCSConfig`, `GCSStorage`, `LocalConfig`, `LocalStorage`, `MemoryConfig`, `MemoryStorage`, `S3Config`, `S3Storage`, `SFTPConfig`, `SFTPStorage`, `STORAGE_DOMAIN`, `StorageBackend`, `StorageConfig`, `StorageConfigFault`, `StorageEffectProvider`, `StorageError`, `StorageFile`, `StorageFileNotFoundError`, `StorageFullError`, `StorageIOFault`, `StorageMetadata`, `StoragePermissionError`, `StorageRegistry`, `StorageSubsystem`

## Public Class Summary

| Class | Source | Bases | Summary |
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
| `StorageEffectProvider` | `aquilia/storage/effects.py` | EffectProvider | Effect provider that yields ``StorageBackend`` instances from the ``StorageRegistry``. |
| `StorageRegistry` | `aquilia/storage/registry.py` | object | Named registry of storage backends. |
| `StorageSubsystem` | `aquilia/storage/subsystem.py` | BaseSubsystem | Subsystem initializer for the Aquilia storage system. |

## Public Function Summary

| Function | Source | Signature | Summary |
| --- | --- | --- | --- |
| `config_from_dict` | `aquilia/storage/configs.py` | `def config_from_dict(data: dict[str, Any])` | Instantiate a typed StorageConfig from a raw dict. |
| `create_backend` | `aquilia/storage/registry.py` | `def create_backend(config: StorageConfig)` | Instantiate a ``StorageBackend`` from a ``StorageConfig``. |

## Constants And Module Flags

| Name | Source | Value or Type |
| --- | --- | --- |
| `STORAGE_DOMAIN` | `aquilia/storage/base.py` | `FaultDomain.custom('storage', 'File storage faults')` |
| `_BACKEND_CONFIGS` | `aquilia/storage/configs.py` | `{'local': LocalConfig, 'memory': MemoryConfig, 's3': S3Config, 'gcs': GCSConfig, 'azure': AzureBlobConfig, 'sftp': SFTPConfig, 'composite': CompositeConfig}` |
| `_BUILTIN_BACKENDS` | `aquilia/storage/registry.py` | `dict[str, str]` |

## Detailed Classes And Methods

### `AzureBlobStorage`

- Source: `aquilia/storage/backends/azure.py`
- Bases: `StorageBackend`
- Summary: Azure Blob Storage backend.

Methods:

| Method | Signature | Summary |
| --- | --- | --- |
| `backend_name` | `def backend_name(self)` |  |
| `initialize` | `async def initialize(self)` |  |
| `shutdown` | `async def shutdown(self)` |  |
| `ping` | `async def ping(self)` |  |
| `save` | `async def save(self, name: str, content: bytes \| BinaryIO \| AsyncIterator[bytes] \| StorageFile, *, content_type: str \| None=None, metadata: dict[str, str] \| None=None, overwrite: bool=False)` |  |
| `open` | `async def open(self, name: str, mode: str='rb')` |  |
| `delete` | `async def delete(self, name: str)` |  |
| `exists` | `async def exists(self, name: str)` |  |
| `stat` | `async def stat(self, name: str)` |  |
| `listdir` | `async def listdir(self, path: str='')` |  |
| `size` | `async def size(self, name: str)` |  |
| `url` | `async def url(self, name: str, expire: int \| None=None)` |  |

### `CompositeStorage`

- Source: `aquilia/storage/backends/composite.py`
- Bases: `StorageBackend`
- Summary: Composite storage that routes files to sub-backends by rules.

Methods:

| Method | Signature | Summary |
| --- | --- | --- |
| `backend_name` | `def backend_name(self)` |  |
| `initialize` | `async def initialize(self)` |  |
| `shutdown` | `async def shutdown(self)` |  |
| `ping` | `async def ping(self)` |  |
| `save` | `async def save(self, name: str, content: bytes \| BinaryIO \| AsyncIterator[bytes] \| StorageFile, *, content_type: str \| None=None, metadata: dict[str, str] \| None=None, overwrite: bool=False)` |  |
| `open` | `async def open(self, name: str, mode: str='rb')` |  |
| `delete` | `async def delete(self, name: str)` |  |
| `exists` | `async def exists(self, name: str)` |  |
| `stat` | `async def stat(self, name: str)` |  |
| `listdir` | `async def listdir(self, path: str='')` |  |
| `size` | `async def size(self, name: str)` |  |
| `url` | `async def url(self, name: str, expire: int \| None=None)` |  |

### `GCSStorage`

- Source: `aquilia/storage/backends/gcs.py`
- Bases: `StorageBackend`
- Summary: Google Cloud Storage backend.

Methods:

| Method | Signature | Summary |
| --- | --- | --- |
| `backend_name` | `def backend_name(self)` |  |
| `initialize` | `async def initialize(self)` |  |
| `shutdown` | `async def shutdown(self)` |  |
| `ping` | `async def ping(self)` |  |
| `save` | `async def save(self, name: str, content: bytes \| BinaryIO \| AsyncIterator[bytes] \| StorageFile, *, content_type: str \| None=None, metadata: dict[str, str] \| None=None, overwrite: bool=False)` |  |
| `open` | `async def open(self, name: str, mode: str='rb')` |  |
| `delete` | `async def delete(self, name: str)` |  |
| `exists` | `async def exists(self, name: str)` |  |
| `stat` | `async def stat(self, name: str)` |  |
| `listdir` | `async def listdir(self, path: str='')` |  |
| `size` | `async def size(self, name: str)` |  |
| `url` | `async def url(self, name: str, expire: int \| None=None)` |  |

### `LocalStorage`

- Source: `aquilia/storage/backends/local.py`
- Bases: `StorageBackend`
- Summary: Local filesystem storage backend.

Methods:

| Method | Signature | Summary |
| --- | --- | --- |
| `backend_name` | `def backend_name(self)` |  |
| `initialize` | `async def initialize(self)` |  |
| `ping` | `async def ping(self)` |  |
| `save` | `async def save(self, name: str, content: bytes \| BinaryIO \| AsyncIterator[bytes] \| StorageFile, *, content_type: str \| None=None, metadata: dict[str, str] \| None=None, overwrite: bool=False)` |  |
| `open` | `async def open(self, name: str, mode: str='rb')` |  |
| `delete` | `async def delete(self, name: str)` |  |
| `exists` | `async def exists(self, name: str)` |  |
| `stat` | `async def stat(self, name: str)` |  |
| `listdir` | `async def listdir(self, path: str='')` |  |
| `size` | `async def size(self, name: str)` |  |
| `url` | `async def url(self, name: str, expire: int \| None=None)` |  |
| `copy` | `async def copy(self, src: str, dst: str)` |  |

### `MemoryStorage`

- Source: `aquilia/storage/backends/memory.py`
- Bases: `StorageBackend`
- Summary: In-memory storage backend.

Methods:

| Method | Signature | Summary |
| --- | --- | --- |
| `backend_name` | `def backend_name(self)` |  |
| `initialize` | `async def initialize(self)` |  |
| `shutdown` | `async def shutdown(self)` |  |
| `ping` | `async def ping(self)` |  |
| `save` | `async def save(self, name: str, content: bytes \| BinaryIO \| AsyncIterator[bytes] \| StorageFile, *, content_type: str \| None=None, metadata: dict[str, str] \| None=None, overwrite: bool=False)` |  |
| `open` | `async def open(self, name: str, mode: str='rb')` |  |
| `delete` | `async def delete(self, name: str)` |  |
| `exists` | `async def exists(self, name: str)` |  |
| `stat` | `async def stat(self, name: str)` |  |
| `listdir` | `async def listdir(self, path: str='')` |  |
| `size` | `async def size(self, name: str)` |  |
| `url` | `async def url(self, name: str, expire: int \| None=None)` |  |

### `S3Storage`

- Source: `aquilia/storage/backends/s3.py`
- Bases: `StorageBackend`
- Summary: Amazon S3 / S3-compatible storage backend.

Methods:

| Method | Signature | Summary |
| --- | --- | --- |
| `backend_name` | `def backend_name(self)` |  |
| `initialize` | `async def initialize(self)` |  |
| `shutdown` | `async def shutdown(self)` |  |
| `ping` | `async def ping(self)` |  |
| `save` | `async def save(self, name: str, content: bytes \| BinaryIO \| AsyncIterator[bytes] \| StorageFile, *, content_type: str \| None=None, metadata: dict[str, str] \| None=None, overwrite: bool=False)` |  |
| `open` | `async def open(self, name: str, mode: str='rb')` |  |
| `delete` | `async def delete(self, name: str)` |  |
| `exists` | `async def exists(self, name: str)` |  |
| `stat` | `async def stat(self, name: str)` |  |
| `listdir` | `async def listdir(self, path: str='')` |  |
| `size` | `async def size(self, name: str)` |  |
| `url` | `async def url(self, name: str, expire: int \| None=None)` |  |

### `SFTPStorage`

- Source: `aquilia/storage/backends/sftp.py`
- Bases: `StorageBackend`
- Summary: SFTP storage backend.

Methods:

| Method | Signature | Summary |
| --- | --- | --- |
| `backend_name` | `def backend_name(self)` |  |
| `initialize` | `async def initialize(self)` |  |
| `shutdown` | `async def shutdown(self)` |  |
| `ping` | `async def ping(self)` |  |
| `save` | `async def save(self, name: str, content: bytes \| BinaryIO \| AsyncIterator[bytes] \| StorageFile, *, content_type: str \| None=None, metadata: dict[str, str] \| None=None, overwrite: bool=False)` |  |
| `open` | `async def open(self, name: str, mode: str='rb')` |  |
| `delete` | `async def delete(self, name: str)` |  |
| `exists` | `async def exists(self, name: str)` |  |
| `stat` | `async def stat(self, name: str)` |  |
| `listdir` | `async def listdir(self, path: str='')` |  |
| `size` | `async def size(self, name: str)` |  |
| `url` | `async def url(self, name: str, expire: int \| None=None)` |  |

### `StorageError`

- Source: `aquilia/storage/base.py`
- Bases: `Fault`
- Summary: Base fault for all storage operations.

### `FileNotFoundError`

- Source: `aquilia/storage/base.py`
- Bases: `StorageError`
- Summary: Raised when a file does not exist in the storage backend.

### `PermissionError`

- Source: `aquilia/storage/base.py`
- Bases: `StorageError`
- Summary: Raised when the caller lacks permission for the operation.

### `StorageFullError`

- Source: `aquilia/storage/base.py`
- Bases: `StorageError`
- Summary: Raised when the storage quota is exceeded.

### `BackendUnavailableError`

- Source: `aquilia/storage/base.py`
- Bases: `StorageError`
- Summary: Raised when the storage backend is unreachable or not configured.

### `StorageIOFault`

- Source: `aquilia/storage/base.py`
- Bases: `StorageError`
- Summary: Raised on I/O operation errors (closed file, wrong mode).

### `StorageConfigFault`

- Source: `aquilia/storage/base.py`
- Bases: `StorageError`
- Summary: Raised on storage configuration / registry errors.

### `StorageMetadata`

- Source: `aquilia/storage/base.py`
- Bases: `object`
- Summary: Immutable metadata for a stored file.
- Decorators: `dataclass(frozen=True, slots=True)`

Fields and class attributes:

| Name | Type | Default / Value |
| --- | --- | --- |
| `name` | `str` | `` |
| `size` | `int` | `0` |
| `content_type` | `str` | `'application/octet-stream'` |
| `etag` | `str` | `''` |
| `last_modified` | `datetime \| None` | `None` |
| `created_at` | `datetime \| None` | `None` |
| `metadata` | `dict[str, str]` | `field(default_factory=dict)` |
| `storage_class` | `str` | `''` |

Methods:

| Method | Signature | Summary |
| --- | --- | --- |
| `to_dict` | `def to_dict(self)` |  |

### `StorageFile`

- Source: `aquilia/storage/base.py`
- Bases: `object`
- Summary: Async file wrapper returned by ``StorageBackend.open()``.

Methods:

| Method | Signature | Summary |
| --- | --- | --- |
| `read` | `async def read(self, size: int=-1)` | Read bytes from the file. |
| `write` | `async def write(self, data: bytes)` | Write bytes (for writable files). |
| `seek` | `async def seek(self, pos: int)` | Seek to byte position (clamped to valid range). |
| `tell` | `async def tell(self)` | Return current byte position. |
| `content` | `def content(self)` | Return raw content bytes (or None if not materialised). |
| `close` | `async def close(self)` | Release resources. |
| `closed` | `def closed(self)` |  |
| `size` | `def size(self)` |  |

### `StorageBackend`

- Source: `aquilia/storage/base.py`
- Bases: `ABC`
- Summary: Abstract storage backend.

Methods:

| Method | Signature | Summary |
| --- | --- | --- |
| `backend_name` | `def backend_name(self)` | Human-readable backend identifier (e.g. 'local', 's3'). |
| `initialize` | `async def initialize(self)` | Async initialization (create dirs, connect to remote, etc.). Called by StorageSubsystem during server startup. |
| `shutdown` | `async def shutdown(self)` | Graceful shutdown (close connections, flush buffers). Called by StorageSubsystem during server shutdown. |
| `ping` | `async def ping(self)` | Health check — return True if the backend is reachable. Used by HealthRegistry for storage health monitoring. |
| `save` | `async def save(self, name: str, content: bytes \| BinaryIO \| AsyncIterator[bytes] \| StorageFile, *, content_type: str \| None=None, metadata: dict[str, str] \| None=None, overwrite: bool=False)` | Save content under ``name``. |
| `open` | `async def open(self, name: str, mode: str='rb')` | Open a file for reading. |
| `delete` | `async def delete(self, name: str)` | Delete a file.  Idempotent — does NOT raise if missing. |
| `exists` | `async def exists(self, name: str)` | Check if a file exists. |
| `stat` | `async def stat(self, name: str)` | Return metadata for a file. |
| `listdir` | `async def listdir(self, path: str='')` | List contents of a directory/prefix. |
| `size` | `async def size(self, name: str)` | Return file size in bytes. |
| `url` | `async def url(self, name: str, expire: int \| None=None)` | Return a URL for accessing the file. |
| `copy` | `async def copy(self, src: str, dst: str)` | Copy a file within the same backend. |
| `move` | `async def move(self, src: str, dst: str)` | Move a file within the same backend. |
| `generate_filename` | `def generate_filename(self, filename: str)` | Generate a safe, unique filename. |
| `get_valid_name` | `def get_valid_name(name: str)` | Return a filesystem-safe filename. |
| `guess_content_type` | `def guess_content_type(name: str)` | Guess MIME type from filename. |

### `StorageConfig`

- Source: `aquilia/storage/configs.py`
- Bases: `object`
- Summary: Base storage configuration.
- Decorators: `dataclass(frozen=True, slots=True)`

Fields and class attributes:

| Name | Type | Default / Value |
| --- | --- | --- |
| `alias` | `str` | `'default'` |
| `backend` | `str` | `''` |
| `default` | `bool` | `False` |

Methods:

| Method | Signature | Summary |
| --- | --- | --- |
| `to_dict` | `def to_dict(self)` |  |

### `LocalConfig`

- Source: `aquilia/storage/configs.py`
- Bases: `StorageConfig`
- Summary: Configuration for the local filesystem storage backend.
- Decorators: `dataclass(frozen=True, slots=True)`

Fields and class attributes:

| Name | Type | Default / Value |
| --- | --- | --- |
| `backend` | `str` | `'local'` |
| `root` | `str` | `'./storage'` |
| `base_url` | `str` | `'/storage/'` |
| `permissions` | `int` | `420` |
| `dir_permissions` | `int` | `493` |
| `create_dirs` | `bool` | `True` |

### `MemoryConfig`

- Source: `aquilia/storage/configs.py`
- Bases: `StorageConfig`
- Summary: Configuration for the in-memory storage backend (testing).
- Decorators: `dataclass(frozen=True, slots=True)`

Fields and class attributes:

| Name | Type | Default / Value |
| --- | --- | --- |
| `backend` | `str` | `'memory'` |
| `max_size` | `int` | `0` |

### `S3Config`

- Source: `aquilia/storage/configs.py`
- Bases: `StorageConfig`
- Summary: Configuration for Amazon S3 or S3-compatible storage.
- Decorators: `dataclass(frozen=True, slots=True)`

Fields and class attributes:

| Name | Type | Default / Value |
| --- | --- | --- |
| `backend` | `str` | `'s3'` |
| `bucket` | `str` | `''` |
| `region` | `str` | `'us-east-1'` |
| `access_key` | `str \| None` | `None` |
| `secret_key` | `str \| None` | `None` |
| `session_token` | `str \| None` | `None` |
| `endpoint_url` | `str \| None` | `None` |
| `prefix` | `str` | `''` |
| `signature_version` | `str` | `'s3v4'` |
| `use_ssl` | `bool` | `True` |
| `addressing_style` | `str` | `'auto'` |
| `default_acl` | `str \| None` | `None` |
| `storage_class` | `str` | `'STANDARD'` |
| `presigned_expiry` | `int` | `3600` |
| `transfer_config` | `dict[str, Any]` | `field(default_factory=dict)` |

### `GCSConfig`

- Source: `aquilia/storage/configs.py`
- Bases: `StorageConfig`
- Summary: Configuration for Google Cloud Storage.
- Decorators: `dataclass(frozen=True, slots=True)`

Fields and class attributes:

| Name | Type | Default / Value |
| --- | --- | --- |
| `backend` | `str` | `'gcs'` |
| `bucket` | `str` | `''` |
| `project` | `str \| None` | `None` |
| `credentials_path` | `str \| None` | `None` |
| `credentials_json` | `str \| None` | `None` |
| `prefix` | `str` | `''` |
| `default_acl` | `str \| None` | `None` |
| `location` | `str` | `''` |
| `presigned_expiry` | `int` | `3600` |

### `AzureBlobConfig`

- Source: `aquilia/storage/configs.py`
- Bases: `StorageConfig`
- Summary: Configuration for Azure Blob Storage.
- Decorators: `dataclass(frozen=True, slots=True)`

Fields and class attributes:

| Name | Type | Default / Value |
| --- | --- | --- |
| `backend` | `str` | `'azure'` |
| `container` | `str` | `''` |
| `connection_string` | `str \| None` | `None` |
| `account_name` | `str \| None` | `None` |
| `account_key` | `str \| None` | `None` |
| `sas_token` | `str \| None` | `None` |
| `prefix` | `str` | `''` |
| `custom_domain` | `str \| None` | `None` |
| `presigned_expiry` | `int` | `3600` |
| `overwrite` | `bool` | `False` |

### `SFTPConfig`

- Source: `aquilia/storage/configs.py`
- Bases: `StorageConfig`
- Summary: Configuration for SFTP/SSH storage.
- Decorators: `dataclass(frozen=True, slots=True)`

Fields and class attributes:

| Name | Type | Default / Value |
| --- | --- | --- |
| `backend` | `str` | `'sftp'` |
| `host` | `str` | `'localhost'` |
| `port` | `int` | `22` |
| `username` | `str` | `''` |
| `password` | `str \| None` | `None` |
| `key_path` | `str \| None` | `None` |
| `key_passphrase` | `str \| None` | `None` |
| `root` | `str` | `'/'` |
| `known_hosts` | `str \| None` | `None` |
| `base_url` | `str` | `''` |
| `timeout` | `int` | `30` |

### `CompositeConfig`

- Source: `aquilia/storage/configs.py`
- Bases: `StorageConfig`
- Summary: Configuration for the composite (multi-backend) storage.
- Decorators: `dataclass(frozen=True, slots=True)`

Fields and class attributes:

| Name | Type | Default / Value |
| --- | --- | --- |
| `backend` | `str` | `'composite'` |
| `backends` | `dict[str, dict[str, Any]]` | `field(default_factory=dict)` |
| `rules` | `dict[str, str]` | `field(default_factory=dict)` |
| `fallback` | `str` | `'default'` |

### `StorageEffectProvider`

- Source: `aquilia/storage/effects.py`
- Bases: `EffectProvider`
- Summary: Effect provider that yields ``StorageBackend`` instances from the ``StorageRegistry``.

Methods:

| Method | Signature | Summary |
| --- | --- | --- |
| `kind` | `def kind(self)` |  |
| `set_registry` | `def set_registry(self, registry: Any)` | Inject registry after construction (for deferred wiring). |
| `initialize` | `async def initialize(self)` | No-op -- backends are initialised by StorageSubsystem. |
| `acquire` | `async def acquire(self, mode: str \| None=None)` | Acquire a storage backend. |
| `release` | `async def release(self, resource: Any, success: bool=True)` | No-op -- storage backends are stateless per request. |
| `finalize` | `async def finalize(self)` | No-op -- shutdown handled by StorageSubsystem. |

### `StorageRegistry`

- Source: `aquilia/storage/registry.py`
- Bases: `object`
- Summary: Named registry of storage backends.

Methods:

| Method | Signature | Summary |
| --- | --- | --- |
| `register` | `def register(self, alias: str, backend: StorageBackend)` | Register a backend under an alias. |
| `unregister` | `def unregister(self, alias: str)` | Remove and return a backend by alias. |
| `set_default` | `def set_default(self, alias: str)` | Set which alias is the default backend. |
| `default` | `def default(self)` | Return the default backend. |
| `get` | `def get(self, alias: str)` | Return a backend by alias, or None. |
| `aliases` | `def aliases(self)` | Return all registered aliases. |
| `items` | `def items(self)` |  |
| `initialize_all` | `async def initialize_all(self)` | Initialize every registered backend. |
| `shutdown_all` | `async def shutdown_all(self)` | Shutdown every registered backend. |
| `health_check` | `async def health_check(self)` | Ping every backend and return alias → healthy map. |
| `from_config` | `def from_config(cls, configs: list[dict[str, Any]])` | Build a registry from a list of config dicts. |

### `StorageSubsystem`

- Source: `aquilia/storage/subsystem.py`
- Bases: `BaseSubsystem`
- Summary: Subsystem initializer for the Aquilia storage system.

Methods:

| Method | Signature | Summary |
| --- | --- | --- |
| `health_check` | `async def health_check(self)` | Check health of all storage backends. |
