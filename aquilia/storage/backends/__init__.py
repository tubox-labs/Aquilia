"""
Storage Backends -- concrete StorageBackend implementations.

Exports all built-in backends for convenient import:

    from aquilia.storage.backends import LocalStorage, S3Storage, ...
"""

from aquilia.storage.backends.azure import AzureBlobStorage
from aquilia.storage.backends.composite import CompositeStorage
from aquilia.storage.backends.gcs import GCSStorage
from aquilia.storage.backends.local import LocalStorage
from aquilia.storage.backends.memory import MemoryStorage
from aquilia.storage.backends.s3 import S3Storage
from aquilia.storage.backends.sftp import SFTPStorage

__all__ = [
    "LocalStorage",
    "MemoryStorage",
    "S3Storage",
    "GCSStorage",
    "AzureBlobStorage",
    "SFTPStorage",
    "CompositeStorage",
]
