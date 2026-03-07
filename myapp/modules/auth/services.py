"""
Auth module services (business logic).

Services contain the core business logic and are auto-wired
via dependency injection.
"""

import os
import uuid
import mimetypes
from datetime import datetime, timezone
from typing import Optional, List, Dict, Any, Set

from aquilia.di import service
from aquilia.storage import StorageRegistry, StorageFileNotFoundError, StorageFullError


# ── Constants ────────────────────────────────────────────────────────────

ALLOWED_IMAGE_TYPES: Set[str] = {
    "image/jpeg", "image/png", "image/gif", "image/webp", "image/svg+xml",
}
ALLOWED_DOCUMENT_TYPES: Set[str] = {
    "application/pdf",
    "application/msword",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    "text/plain", "text/csv", "text/markdown",
    "application/json", "application/xml",
}
ALL_ALLOWED_TYPES: Set[str] = ALLOWED_IMAGE_TYPES | ALLOWED_DOCUMENT_TYPES

MAX_AVATAR_SIZE: int = 2 * 1024 * 1024       # 2 MB
MAX_DOCUMENT_SIZE: int = 25 * 1024 * 1024     # 25 MB
MAX_UPLOAD_SIZE: int = 50 * 1024 * 1024       # 50 MB


@service(scope="app")
class AuthService:
    """
    Service for auth business logic.

    This service is automatically registered with the DI container
    and can be injected into controllers.
    """

    def __init__(self):
        self._storage: List[dict] = []
        self._next_id = 1

    async def get_all(self) -> List[dict]:
        """Get all items."""
        return self._storage

    async def get_by_id(self, item_id: int) -> Optional[dict]:
        """Get item by ID."""
        for item in self._storage:
            if item["id"] == item_id:
                return item
        return None

    async def create(self, data: dict) -> dict:
        """Create new item."""
        item = {
            "id": self._next_id,
            **data
        }
        self._storage.append(item)
        self._next_id += 1
        return item

    async def update(self, item_id: int, data: dict) -> Optional[dict]:
        """Update existing item."""
        item = await self.get_by_id(item_id)
        if item:
            item.update(data)
        return item

    async def delete(self, item_id: int) -> bool:
        """Delete item."""
        for i, item in enumerate(self._storage):
            if item["id"] == item_id:
                self._storage.pop(i)
                return True
        return False


@service(scope="app")
class FileStorageService:
    """
    Service for file storage operations in the auth module.

    Uses Aquilia's StorageRegistry to interact with configured backends
    (uploads, avatars, documents, temp).

    Injected via DI::

        class MyController(Controller):
            def __init__(self, file_service: FileStorageService):
                self.file_service = file_service
    """

    def __init__(self, storage: StorageRegistry):
        self.storage = storage

    # ── Backend helpers ──────────────────────────────────────────────────

    def _backend(self, backend_name: Optional[str] = None):
        """Resolve a named backend or the default."""
        if backend_name:
            return self.storage[backend_name]
        return self.storage.default

    @staticmethod
    def _safe_filename(original: str) -> str:
        """Generate a collision-safe filename preserving the extension."""
        _, ext = os.path.splitext(original)
        ext = ext.lower()
        uid = uuid.uuid4().hex[:12]
        ts = datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S")
        return f"{ts}_{uid}{ext}"

    @staticmethod
    def _guess_content_type(filename: str) -> str:
        ct, _ = mimetypes.guess_type(filename)
        return ct or "application/octet-stream"

    @staticmethod
    def _human_size(size_bytes: int) -> str:
        for unit in ("B", "KB", "MB", "GB"):
            if size_bytes < 1024:
                return f"{size_bytes:.1f} {unit}"
            size_bytes /= 1024
        return f"{size_bytes:.1f} TB"

    # ── Upload ───────────────────────────────────────────────────────────

    async def upload_file(
        self,
        filename: str,
        content: bytes,
        *,
        backend_name: str = "uploads",
        directory: str = "",
        content_type: Optional[str] = None,
        allowed_types: Optional[Set[str]] = None,
        max_size: int = MAX_UPLOAD_SIZE,
        overwrite: bool = False,
    ) -> Dict[str, Any]:
        """
        Upload a file to the specified storage backend.

        Args:
            filename: Original filename from the client.
            content: Raw file bytes.
            backend_name: Storage backend alias ('uploads', 'avatars', 'documents', 'temp').
            directory: Sub-directory within the backend (e.g. 'profiles/123').
            content_type: Explicit MIME type. Guessed from extension if omitted.
            allowed_types: Set of allowed MIME types. None = allow all.
            max_size: Maximum file size in bytes.
            overwrite: Whether to overwrite an existing file with the same name.

        Returns:
            Dict with file metadata: name, path, size, content_type, backend, url, uploaded_at.

        Raises:
            FileUploadFault: If validation fails.
            StorageQuotaFault: If quota is exceeded.
        """
        from .faults import FileUploadFault, StorageQuotaFault

        # ── Validation ───────────────────────────────────────────────
        if not content:
            raise FileUploadFault("Empty file", filename)

        if len(content) > max_size:
            raise FileUploadFault(
                f"File too large ({self._human_size(len(content))}). "
                f"Maximum allowed: {self._human_size(max_size)}",
                filename,
            )

        ct = content_type or self._guess_content_type(filename)
        if allowed_types and ct not in allowed_types:
            raise FileUploadFault(
                f"File type '{ct}' is not allowed. "
                f"Accepted: {', '.join(sorted(allowed_types))}",
                filename,
            )

        # ── Safe name & path ─────────────────────────────────────────
        safe_name = self._safe_filename(filename)
        storage_path = f"{directory.strip('/')}/{safe_name}" if directory else safe_name

        # ── Save ─────────────────────────────────────────────────────
        backend = self._backend(backend_name)
        try:
            saved_name = await backend.save(
                storage_path,
                content,
                content_type=ct,
                overwrite=overwrite,
            )
        except StorageFullError:
            raise StorageQuotaFault(
                backend_name,
                self._human_size(max_size),
            )

        url = await backend.url(saved_name)

        return {
            "name": os.path.basename(saved_name),
            "path": saved_name,
            "size": len(content),
            "size_human": self._human_size(len(content)),
            "content_type": ct,
            "backend": backend_name,
            "url": url,
            "uploaded_at": datetime.now(timezone.utc).isoformat(),
        }

    # ── Avatar shorthand ─────────────────────────────────────────────

    async def upload_avatar(
        self,
        user_id: int,
        filename: str,
        content: bytes,
    ) -> Dict[str, Any]:
        """Upload a user avatar image (max 2 MB, images only)."""
        return await self.upload_file(
            filename,
            content,
            backend_name="avatars",
            directory=f"user_{user_id}",
            allowed_types=ALLOWED_IMAGE_TYPES,
            max_size=MAX_AVATAR_SIZE,
            overwrite=True,
        )

    # ── Document shorthand ───────────────────────────────────────────

    async def upload_document(
        self,
        filename: str,
        content: bytes,
        *,
        directory: str = "",
    ) -> Dict[str, Any]:
        """Upload a document (max 25 MB, documents only)."""
        return await self.upload_file(
            filename,
            content,
            backend_name="documents",
            directory=directory,
            allowed_types=ALLOWED_DOCUMENT_TYPES,
            max_size=MAX_DOCUMENT_SIZE,
        )

    # ── Download ─────────────────────────────────────────────────────

    async def download_file(
        self,
        path: str,
        *,
        backend_name: str = "uploads",
    ) -> Dict[str, Any]:
        """
        Download / read a file from storage.

        Returns:
            Dict with keys: content (bytes), name, size, content_type.

        Raises:
            FileNotFoundFault: If the file does not exist.
        """
        from .faults import FileNotFoundFault

        backend = self._backend(backend_name)

        if not await backend.exists(path):
            raise FileNotFoundFault(path, backend_name)

        sf = await backend.open(path)
        data = await sf.read()
        meta = await backend.stat(path)

        return {
            "content": data,
            "name": os.path.basename(path),
            "path": path,
            "size": meta.size,
            "size_human": self._human_size(meta.size),
            "content_type": meta.content_type,
            "backend": backend_name,
        }

    # ── Delete ───────────────────────────────────────────────────────

    async def delete_file(
        self,
        path: str,
        *,
        backend_name: str = "uploads",
    ) -> Dict[str, Any]:
        """
        Delete a file from storage.

        Returns:
            Dict confirming deletion.

        Raises:
            FileNotFoundFault: If the file does not exist.
        """
        from .faults import FileNotFoundFault

        backend = self._backend(backend_name)

        if not await backend.exists(path):
            raise FileNotFoundFault(path, backend_name)

        await backend.delete(path)

        return {
            "deleted": True,
            "path": path,
            "backend": backend_name,
            "deleted_at": datetime.now(timezone.utc).isoformat(),
        }

    # ── List ─────────────────────────────────────────────────────────

    async def list_files(
        self,
        directory: str = "",
        *,
        backend_name: str = "uploads",
    ) -> Dict[str, Any]:
        """
        List files and directories in storage.

        Returns:
            Dict with 'directories', 'files', and metadata about each file.
        """
        backend = self._backend(backend_name)
        dirs, file_names = await backend.listdir(directory)

        files = []
        for fname in file_names:
            full_path = f"{directory.rstrip('/')}/{fname}" if directory else fname
            try:
                meta = await backend.stat(full_path)
                url = await backend.url(full_path)
                files.append({
                    "name": fname,
                    "path": full_path,
                    "size": meta.size,
                    "size_human": self._human_size(meta.size),
                    "content_type": meta.content_type,
                    "last_modified": meta.last_modified.isoformat() if meta.last_modified else None,
                    "url": url,
                })
            except Exception:
                files.append({"name": fname, "path": full_path, "error": "stat_failed"})

        return {
            "backend": backend_name,
            "directory": directory or "/",
            "directories": sorted(dirs),
            "files": files,
            "total_files": len(files),
            "total_dirs": len(dirs),
        }

    # ── Stat ─────────────────────────────────────────────────────────

    async def file_info(
        self,
        path: str,
        *,
        backend_name: str = "uploads",
    ) -> Dict[str, Any]:
        """
        Get detailed metadata for a single file.

        Raises:
            FileNotFoundFault: If the file does not exist.
        """
        from .faults import FileNotFoundFault

        backend = self._backend(backend_name)

        if not await backend.exists(path):
            raise FileNotFoundFault(path, backend_name)

        meta = await backend.stat(path)
        url = await backend.url(path)

        return {
            "name": os.path.basename(path),
            "path": path,
            "size": meta.size,
            "size_human": self._human_size(meta.size),
            "content_type": meta.content_type,
            "last_modified": meta.last_modified.isoformat() if meta.last_modified else None,
            "created_at": meta.created_at.isoformat() if meta.created_at else None,
            "etag": meta.etag,
            "metadata": meta.metadata,
            "storage_class": meta.storage_class,
            "backend": backend_name,
            "url": url,
        }

    # ── Health ───────────────────────────────────────────────────────

    async def storage_health(self) -> Dict[str, Any]:
        """
        Check health of all configured storage backends.

        Returns:
            Dict mapping backend aliases to their health status.
        """
        health = await self.storage.health_check()
        backends_info = {}

        for alias, is_healthy in health.items():
            backend = self.storage.get(alias)
            backends_info[alias] = {
                "healthy": is_healthy,
                "backend_type": backend.backend_name if backend else "unknown",
            }

        return {
            "status": "healthy" if all(health.values()) else "degraded",
            "backends": backends_info,
            "total_backends": len(health),
            "healthy_count": sum(1 for v in health.values() if v),
        }