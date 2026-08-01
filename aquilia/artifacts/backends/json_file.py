"""
JSONFileBackend — Default artifact storage backend.

Generalises the production-grade pattern from ``JSONBytecodeCache``
(``aquilia/templates/bytecode_cache.py``) into a format-agnostic backend
usable by every artifact producer.

On-disk format
--------------
**Unsigned** artifacts::

    <JSON envelope>

**Signed** artifacts (HMAC tamper-detection enabled)::

    <64-char HMAC hex>\\n<JSON envelope>

The HMAC header format exactly matches what ``JSONBytecodeCache._save()``
produces, so migrating the template bytecode cache onto this backend
(Phase D of the roadmap) produces byte-identical files.

Write strategy
--------------
Uses ``aquilia.filesystem.write_file(atomic=True)`` under the hood:
a ``tempfile.mkstemp()``-created file is written, optionally fsynced,
then ``os.replace()``-renamed to the final path.  This is the same
strategy as ``filesystem/_ops.py:306`` — process-unique temp names,
not the ``with_suffix('.tmp')`` approach of the bytecode cache (which
risks a temp-file race when two processes save concurrently).

Locking
-------
The store layer acquires ``AsyncFileLock`` before calling backend
read/write methods.  The backend itself does not lock.
"""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any

from aquilia.filesystem._pool import FileSystemPool

logger = logging.getLogger("aquilia.artifacts.backends.json_file")


class JSONFileBackend:
    """
    JSON file backend for artifact storage.

    This backend is purposely thin: it handles serialisation/deserialisation
    and raw file I/O.  Locking, path resolution, and integrity policy
    enforcement are the responsibility of :class:`~aquilia.artifacts.store.ArtifactStore`.
    """

    # ------------------------------------------------------------------
    # Sync read/write (used by ArtifactStore via thread-pool offload)
    # ------------------------------------------------------------------

    def read_sync(
        self,
        path: Path,
        *,
        signed: bool = False,
        artifact_path_for_key: Path | None = None,
        secret_key: str | None = None,
    ) -> dict[str, Any] | None:
        """
        Read and deserialise an artifact file.

        Returns ``None`` if the file does not exist.

        Raises
        ------
        ValueError
            If the file content cannot be parsed as a valid artifact
            envelope (for ``"raise"`` on_corrupt policy; callers catch
            this and apply their policy).
        """
        if not path.exists():
            return None

        try:
            raw = path.read_bytes()
        except OSError as exc:
            raise ValueError(f"Cannot read artifact file: {exc}") from exc

        if signed:
            from aquilia.artifacts.integrity import file_format_verify

            try:
                raw = file_format_verify(
                    raw,
                    artifact_path=artifact_path_for_key or path,
                    secret_key=secret_key,
                )
            except ValueError as exc:
                raise ValueError(str(exc)) from exc

        try:
            data = json.loads(raw)
        except json.JSONDecodeError as exc:
            raise ValueError(f"Artifact JSON parse error: {exc}") from exc

        return data

    def write_sync(
        self,
        path: Path,
        data: dict[str, Any],
        *,
        signed: bool = False,
        artifact_path_for_key: Path | None = None,
        secret_key: str | None = None,
    ) -> None:
        """
        Serialise and atomically write an artifact file.

        Uses ``tempfile.mkstemp`` + ``os.replace`` for atomicity.
        This is process-unique naming (unlike ``with_suffix('.tmp')``),
        so concurrent writers don't race on the same temp path.
        """
        import os
        import tempfile

        payload_bytes = json.dumps(data, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")

        if signed:
            from aquilia.artifacts.integrity import file_format_sign

            payload_bytes = file_format_sign(
                payload_bytes,
                artifact_path=artifact_path_for_key or path,
                secret_key=secret_key,
            )

        path.parent.mkdir(parents=True, exist_ok=True)

        fd, tmp = tempfile.mkstemp(dir=str(path.parent), prefix=".aquilia-artifact-tmp-")
        try:
            os.write(fd, payload_bytes)
            try:
                os.fsync(fd)
            except OSError:
                pass  # Best effort; not all platforms/mounts support fsync
            os.close(fd)
            os.replace(tmp, str(path))
        except BaseException:
            # Best effort cleanup of the temp file
            try:
                os.close(fd)
            except OSError:
                pass
            try:
                os.unlink(tmp)
            except OSError:
                pass
            raise

    def delete_sync(self, path: Path) -> bool:
        """
        Delete an artifact file.

        Returns ``True`` if deleted, ``False`` if not found.
        """
        try:
            path.unlink()
            return True
        except FileNotFoundError:
            return False
        except OSError as exc:
            raise ValueError(f"Cannot delete artifact file: {exc}") from exc

    # ------------------------------------------------------------------
    # Async wrappers (offload sync I/O to the filesystem thread pool)
    # ------------------------------------------------------------------

    async def read(
        self,
        path: Path,
        *,
        signed: bool = False,
        artifact_path_for_key: Path | None = None,
        secret_key: str | None = None,
    ) -> dict[str, Any] | None:
        """Async version of :meth:`read_sync`."""

        pool = _get_pool()
        return await pool.run(
            lambda: self.read_sync(
                path,
                signed=signed,
                artifact_path_for_key=artifact_path_for_key,
                secret_key=secret_key,
            )
        )

    async def write(
        self,
        path: Path,
        data: dict[str, Any],
        *,
        signed: bool = False,
        artifact_path_for_key: Path | None = None,
        secret_key: str | None = None,
    ) -> None:
        """Async version of :meth:`write_sync`."""
        pool = _get_pool()
        await pool.run(
            lambda: self.write_sync(
                path,
                data,
                signed=signed,
                artifact_path_for_key=artifact_path_for_key,
                secret_key=secret_key,
            )
        )

    async def delete(self, path: Path) -> bool:
        """Async version of :meth:`delete_sync`."""
        pool = _get_pool()
        return await pool.run(lambda: self.delete_sync(path))


_pool_singleton: Any = None


def _get_pool():
    global _pool_singleton
    if _pool_singleton is None:
        _pool_singleton = FileSystemPool()
    return _pool_singleton
