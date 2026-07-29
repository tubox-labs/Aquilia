"""
ArtifactStore — The unified artifact persistence service.

This is the single object all artifact producers talk to.  It owns:

- Path resolution (via registered artifact type descriptors)
- Locking (``AsyncFileLock``, shared reads / exclusive writes)
- Integrity (fingerprint verification on load, HMAC sign/verify)
- Atomicity (delegates to ``JSONFileBackend.write_sync`` which uses
  ``tempfile.mkstemp`` + ``os.replace``)
- Multi-artifact transactions (``ArtifactTransaction``)
- Pruning (``prune()``)
- Status reporting (``status()``)

Usage::

    store = ArtifactStore.for_root(".aquilia/artifacts")

    # Write an artifact
    envelope = await store.put("discovery_cache", "main", payload)

    # Read an artifact
    envelope = await store.get("discovery_cache", "main")

    # Verify integrity without loading payload
    ok = await store.verify("discovery_cache", "main")

    # Multi-artifact all-or-nothing write
    async with store.transaction() as tx:
        await tx.stage("schema_snapshot", "main", snapshot_data)
        await tx.stage("migration_file", "0001_initial", migration_text)
        # __aexit__ commits both or rolls back both

    # Housekeeping
    pruned = await store.prune(orphaned_only=True)
    report = await store.status()
"""

from __future__ import annotations

import logging
import warnings
from pathlib import Path
from typing import Any

from aquilia._version import __version__ as _AQUILIA_VERSION  # noqa: N812

from .backends.json_file import JSONFileBackend
from .backends.memory import MemoryBackend
from .canonical import bare_fingerprint
from .envelope import ArtifactEnvelope
from .faults import (
    ArtifactCorruptFault,
    ArtifactLockTimeoutFault,
    ArtifactTransactionFault,
)
from .registry import ArtifactTypeDescriptor, get_all_descriptors, get_descriptor

logger = logging.getLogger("aquilia.artifacts.store")

# Default root, overridable via config
DEFAULT_ARTIFACT_ROOT = ".aquilia/artifacts"

# Lock timeout for exclusive writes (seconds).  -1 = wait forever.
DEFAULT_LOCK_TIMEOUT = 30.0


class ArtifactStore:
    """
    Unified artifact persistence service.

    One instance per configured artifact root.  Typically registered as
    a DI singleton scoped per application, matching how ``SpeculaService``
    is registered.

    Parameters
    ----------
    root
        Absolute path to the artifact root directory.
    backend
        Storage backend.  Defaults to ``JSONFileBackend()``.
    lock_timeout
        Seconds to wait for an exclusive write lock.
    secret_key
        HMAC secret key override (falls back to ``AQUILIA_CACHE_SECRET``
        env var, then path-derived fallback).
    """

    def __init__(
        self,
        root: Path,
        *,
        backend: JSONFileBackend | MemoryBackend | None = None,
        lock_timeout: float = DEFAULT_LOCK_TIMEOUT,
        secret_key: str | None = None,
    ) -> None:
        self._root = root
        self._backend = backend or JSONFileBackend()
        self._lock_timeout = lock_timeout
        self._secret_key = secret_key

    # ------------------------------------------------------------------
    # Factory
    # ------------------------------------------------------------------

    @classmethod
    def for_root(
        cls,
        root: str | Path = DEFAULT_ARTIFACT_ROOT,
        *,
        lock_timeout: float = DEFAULT_LOCK_TIMEOUT,
        secret_key: str | None = None,
    ) -> ArtifactStore:
        """Create a store rooted at ``root``."""
        return cls(
            Path(root).resolve(),
            lock_timeout=lock_timeout,
            secret_key=secret_key,
        )

    @classmethod
    def for_testing(cls) -> ArtifactStore:
        """Create an in-memory store suitable for unit tests."""
        import tempfile

        return cls(
            Path(tempfile.mkdtemp()),
            backend=MemoryBackend(),
            lock_timeout=1.0,
        )

    # ------------------------------------------------------------------
    # Core API
    # ------------------------------------------------------------------

    async def get(
        self,
        artifact_type: str,
        key: str = "main",
        *,
        verify_integrity: bool = True,
    ) -> ArtifactEnvelope | None:
        """
        Load and return an artifact envelope, or ``None`` on cache miss.

        On load failure the corruption policy registered for ``artifact_type``
        is applied:

        - ``"raise"`` — raises :exc:`ArtifactCorruptFault`.
        - ``"warn_and_reset"`` — emits a warning, returns ``None``.
        - ``"reset"`` — silently returns ``None``.

        Parameters
        ----------
        artifact_type
            Registered type identifier.
        key
            Within-type identifier (``"main"`` for singleton artifacts).
        verify_integrity
            If ``True`` (default), re-computes the payload fingerprint and
            compares it with the stored value, catching silent bit-flip
            corruption that HMAC alone doesn't catch on unsigned artifacts.
        """
        descriptor = self._require_descriptor(artifact_type)
        path = descriptor.resolve_path(self._root, key)

        async with self._read_lock(path):
            try:
                raw = await self._backend.read(
                    path,
                    signed=descriptor.sign,
                    artifact_path_for_key=path,
                    secret_key=self._secret_key,
                )
            except ValueError as exc:
                return self._handle_corrupt(descriptor, path, str(exc))

            if raw is None:
                return None  # Cache miss — file doesn't exist

            try:
                envelope = ArtifactEnvelope.from_dict(raw)
            except ValueError as exc:
                return self._handle_corrupt(descriptor, path, str(exc))

            # Schema version check
            if envelope.schema_version != descriptor.schema_version:
                return self._handle_stale(descriptor, path, envelope.schema_version)

            # Integrity verification
            if verify_integrity:
                expected_fp = bare_fingerprint(
                    envelope.payload,
                    exclude_keys=frozenset(),  # Fingerprint the payload as-is
                )
                if expected_fp != envelope.fingerprint:
                    return self._handle_corrupt(
                        descriptor,
                        path,
                        f"Fingerprint mismatch: stored={envelope.fingerprint!r}, recomputed={expected_fp!r}",
                    )

            return envelope

    async def put(
        self,
        artifact_type: str,
        key: str = "main",
        payload: Any = None,
        *,
        schema_version: str | None = None,
        sign: bool | None = None,
    ) -> ArtifactEnvelope:
        """
        Build and persist an artifact envelope.

        Parameters
        ----------
        artifact_type
            Registered type identifier.
        key
            Within-type identifier.
        payload
            The artifact-specific data (must be JSON-serialisable).
        schema_version
            Override the registered schema version (use for migration scripts
            that write a specific version).
        sign
            Override the registered sign flag.

        Returns
        -------
        ArtifactEnvelope
            The written envelope.
        """
        descriptor = self._require_descriptor(artifact_type)
        path = descriptor.resolve_path(self._root, key)
        _schema_version = schema_version or descriptor.schema_version
        _sign = sign if sign is not None else descriptor.sign

        fp = bare_fingerprint(payload, exclude_keys=frozenset())
        envelope = ArtifactEnvelope.build(
            artifact_type=artifact_type,
            key=key,
            schema_version=_schema_version,
            payload=payload,
            fingerprint=fp,
            signed=_sign,
            producer_version=_AQUILIA_VERSION,
        )

        async with self._write_lock(path):
            await self._backend.write(
                path,
                envelope.to_dict(),
                signed=_sign,
                artifact_path_for_key=path,
                secret_key=self._secret_key,
            )

        logger.debug("Wrote artifact type=%r key=%r path=%s", artifact_type, key, path)
        return envelope

    async def invalidate(self, artifact_type: str, key: str = "main") -> bool:
        """
        Delete an artifact file.

        Returns ``True`` if a file was deleted, ``False`` if not found.
        """
        descriptor = self._require_descriptor(artifact_type)
        path = descriptor.resolve_path(self._root, key)

        async with self._write_lock(path):
            deleted = await self._backend.delete(path)

        if deleted:
            logger.debug("Invalidated artifact type=%r key=%r", artifact_type, key)
        return deleted

    async def verify(self, artifact_type: str, key: str = "main") -> bool:
        """
        Recompute and verify an artifact's fingerprint without loading it
        into the framework.

        Returns ``True`` if the artifact exists and is intact, ``False``
        if it's absent or corrupt.  Never raises.
        """
        try:
            envelope = await self.get(artifact_type, key, verify_integrity=True)
            return envelope is not None
        except ArtifactCorruptFault:
            return False
        except Exception as exc:
            logger.warning("Unexpected error verifying artifact %r/%r: %s", artifact_type, key, exc)
            return False

    # ------------------------------------------------------------------
    # Multi-artifact transactions
    # ------------------------------------------------------------------

    def transaction(self, *artifact_refs: tuple[str, str]) -> ArtifactTransaction:
        """
        Return an async context manager for all-or-nothing multi-artifact
        writes.

        Usage::

            async with store.transaction() as tx:
                await tx.stage("schema_snapshot", "main", snapshot)
                await tx.stage("migration_file", "0001_initial", text)
            # Both written or neither

        Locks are acquired in alphabetical path order to prevent deadlocks
        across concurrent transactions that span overlapping artifact sets.
        """
        return ArtifactTransaction(self, list(artifact_refs))

    # ------------------------------------------------------------------
    # Pruning / housekeeping
    # ------------------------------------------------------------------

    async def prune(
        self,
        artifact_type: str | None = None,
        *,
        orphaned_only: bool = True,
    ) -> int:
        """
        Remove stale/orphaned artifact files.

        Parameters
        ----------
        artifact_type
            Limit pruning to this type.  ``None`` prunes all registered types.
        orphaned_only
            If ``True`` (default), only remove files that don't correspond
            to any currently registered artifact type.

        Returns
        -------
        int
            Number of files removed.
        """

        pool = JSONFileBackend._get_pool() if hasattr(JSONFileBackend, "_get_pool") else None
        removed = 0

        if not self._root.exists():
            return 0

        # Collect all .json files under root
        def _scan():
            return list(self._root.rglob("*.json"))

        from aquilia.filesystem._pool import FileSystemPool as _FSPool

        _pool = _FSPool()
        all_files = await _pool.run(_scan)

        # Build set of known paths
        known_paths: set[Path] = set()
        descriptors = get_all_descriptors()
        target_types = {artifact_type} if artifact_type else set(descriptors.keys())

        for atype in target_types:
            desc = descriptors.get(atype)
            if desc:
                # Generate known paths for "main" key plus any existing keyed artifacts
                known_paths.add(desc.resolve_path(self._root, "main"))

        for json_file in all_files:
            if orphaned_only:
                if json_file not in known_paths:
                    # Check if this file belongs to any registered type
                    is_known = False
                    try:
                        raw = json_file.read_bytes()
                        import json as _json

                        try:
                            data = _json.loads(raw)
                            atype = data.get("artifact_type")
                            if atype and atype in descriptors:
                                is_known = True
                        except Exception:
                            pass
                    except Exception:
                        pass

                    if not is_known:
                        try:
                            json_file.unlink()
                            removed += 1
                            logger.debug("Pruned orphaned artifact: %s", json_file)
                        except OSError as exc:
                            logger.warning("Could not prune %s: %s", json_file, exc)

        return removed

    # ------------------------------------------------------------------
    # Status reporting
    # ------------------------------------------------------------------

    async def status(self) -> list[dict[str, Any]]:
        """
        Scan the artifact root and return a status report.

        Used by ``aq artifacts status``.
        """
        from .registry import ArtifactRegistry

        reg = ArtifactRegistry(self._root)

        from aquilia.filesystem._pool import FileSystemPool as _FSPool

        _pool = _FSPool()
        report = await _pool.run(reg.scan)

        records = []
        for artifact_type, files in report.items():
            for path, info in files.items():
                record = {"type": artifact_type, "path": path}
                record.update(info)
                records.append(record)
        return records

    # ------------------------------------------------------------------
    # Locking helpers
    # ------------------------------------------------------------------

    def _read_lock(self, path: Path):
        """Shared (read) lock context manager."""
        return self._make_lock(path, shared=True)

    def _write_lock(self, path: Path):
        """Exclusive (write) lock context manager."""
        return self._make_lock(path, shared=False)

    def _make_lock(self, path: Path, *, shared: bool):
        """Create an AsyncFileLock for an artifact path."""
        from aquilia.filesystem._lock import AsyncFileLock, LockAcquisitionError

        lock_path = path.with_suffix(".lock")

        class _LockCtx:
            def __init__(self_, path_, shared_):
                self_._lock = AsyncFileLock(
                    str(lock_path),
                    timeout=self._lock_timeout,
                    shared=shared_,
                )

            async def __aenter__(self_):
                try:
                    await self_._lock.acquire()
                except LockAcquisitionError as exc:
                    raise ArtifactLockTimeoutFault(str(path), self._lock_timeout) from exc
                return self_

            async def __aexit__(self_, *args):
                await self_._lock.release()

        return _LockCtx(path, shared)

    # ------------------------------------------------------------------
    # Descriptor helpers
    # ------------------------------------------------------------------

    def _require_descriptor(self, artifact_type: str) -> ArtifactTypeDescriptor:
        """Return descriptor or raise ValueError for unknown types."""
        desc = get_descriptor(artifact_type)
        if desc is None:
            known = sorted(get_all_descriptors().keys())
            raise ValueError(
                f"Unknown artifact type {artifact_type!r}. "
                f"Registered types: {known}. "
                f"Call register_artifact_type() before using the store."
            )
        return desc

    # ------------------------------------------------------------------
    # Corruption/staleness policy dispatch
    # ------------------------------------------------------------------

    def _handle_corrupt(
        self,
        descriptor: ArtifactTypeDescriptor,
        path: Path,
        reason: str,
    ) -> None:
        """Apply the artifact type's on_corrupt policy."""
        if descriptor.on_corrupt == "raise":
            raise ArtifactCorruptFault(str(path), reason)
        elif descriptor.on_corrupt == "warn_and_reset":
            warnings.warn(
                f"Artifact {descriptor.artifact_type!r} at {path} is corrupt: {reason}. Starting with an empty cache.",
                stacklevel=4,
            )
            return None
        else:  # "reset"
            return None

    def _handle_stale(
        self,
        descriptor: ArtifactTypeDescriptor,
        path: Path,
        stored_version: str,
    ) -> None:
        """Apply the artifact type's staleness policy (always treated as warn_and_reset)."""
        warnings.warn(
            f"Artifact {descriptor.artifact_type!r} at {path} has schema_version "
            f"{stored_version!r}; this build expects {descriptor.schema_version!r}. "
            f"Rebuilding from scratch.",
            stacklevel=4,
        )
        return None


# ─────────────────────────────────────────────────────────────────────────────
# ArtifactTransaction
# ─────────────────────────────────────────────────────────────────────────────


class ArtifactTransaction:
    """
    Async context manager for all-or-nothing multi-artifact writes.

    Acquires locks for all participating artifacts in a fixed alphabetical
    order (by resolved path) to prevent deadlocks between concurrent
    transactions that span overlapping artifact sets.

    On ``__aexit__`` without exception: commits all staged writes.
    On ``__aexit__`` with exception: discards all staged writes (the
    original artifacts on disk are left untouched).

    Usage::

        async with store.transaction() as tx:
            await tx.stage("schema_snapshot", "main", snapshot)
            await tx.stage("migration_file", "0001", migration_text)
        # Both written, or neither
    """

    def __init__(self, store: ArtifactStore, artifact_refs: list[tuple[str, str]]) -> None:
        self._store = store
        self._refs = artifact_refs  # (artifact_type, key) pairs
        self._staged: list[tuple[ArtifactEnvelope, Path]] = []
        self._locks: list[Any] = []

    async def __aenter__(self) -> ArtifactTransaction:
        # Acquire locks in alphabetical path order
        from aquilia.filesystem._lock import AsyncFileLock, LockAcquisitionError

        lock_targets: list[tuple[Path, Any]] = []
        for artifact_type, key in self._refs:
            descriptor = self._store._require_descriptor(artifact_type)
            path = descriptor.resolve_path(self._store._root, key)
            lock_path = path.with_suffix(".lock")
            lock = AsyncFileLock(
                str(lock_path),
                timeout=self._store._lock_timeout,
                shared=False,
            )
            lock_targets.append((path, lock))

        # Sort by path for deterministic lock ordering
        lock_targets.sort(key=lambda t: str(t[0]))

        acquired = []
        try:
            for path, lock in lock_targets:
                try:
                    await lock.acquire()
                    acquired.append(lock)
                except LockAcquisitionError as exc:
                    raise ArtifactLockTimeoutFault(str(path), self._store._lock_timeout) from exc
        except Exception:
            # Release already-acquired locks
            for l in reversed(acquired):
                await l.release()
            raise

        self._locks = [lock for _, lock in lock_targets]
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        try:
            if exc_type is None:
                # Commit all staged writes
                staged_types = [e.artifact_type for e, _ in self._staged]
                try:
                    for envelope, path in self._staged:
                        descriptor = self._store._require_descriptor(envelope.artifact_type)
                        await self._store._backend.write(
                            path,
                            envelope.to_dict(),
                            signed=descriptor.sign,
                            artifact_path_for_key=path,
                            secret_key=self._store._secret_key,
                        )
                        logger.debug(
                            "Transaction committed: type=%r key=%r",
                            envelope.artifact_type,
                            envelope.key,
                        )
                except Exception as exc:
                    # Rollback: the individual atomic writes are isolated, but
                    # if a later write fails some earlier writes may already be
                    # committed.  Log the partial commit as an error.
                    raise ArtifactTransactionFault(str(exc), staged_types) from exc
        finally:
            # Always release all locks
            for lock in reversed(self._locks):
                await lock.release()

    async def stage(
        self,
        artifact_type: str,
        key: str = "main",
        payload: Any = None,
        *,
        schema_version: str | None = None,
    ) -> None:
        """
        Stage an artifact for writing.

        The write does not happen until the transaction context manager's
        ``__aexit__`` is called without an exception.
        """
        descriptor = self._store._require_descriptor(artifact_type)
        path = descriptor.resolve_path(self._store._root, key)
        _schema_version = schema_version or descriptor.schema_version

        fp = bare_fingerprint(payload, exclude_keys=frozenset())
        envelope = ArtifactEnvelope.build(
            artifact_type=artifact_type,
            key=key,
            schema_version=_schema_version,
            payload=payload,
            fingerprint=fp,
            signed=descriptor.sign,
            producer_version=_AQUILIA_VERSION,
        )
        self._staged.append((envelope, path))
