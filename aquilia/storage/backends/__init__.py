"""
Storage Backends -- concrete StorageBackend implementations.

Exports all built-in backends for convenient import:

    from aquilia.storage.backends import LocalStorage, S3Storage, ...
"""

from .local import LocalStorage
from .memory import MemoryStorage
from .s3 import S3Storage
from .gcs import GCSStorage
from .azure import AzureBlobStorage
from .sftp import SFTPStorage
from .composite import CompositeStorage

__all__ = [
    "LocalStorage",
    "MemoryStorage",
    "S3Storage",
    "GCSStorage",
    "AzureBlobStorage",
    "SFTPStorage",
    "CompositeStorage",
]
