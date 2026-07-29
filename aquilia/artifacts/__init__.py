"""
Aquilia Artifacts — Unified artifact persistence subsystem.

Provides a single, production-grade store for every file the framework
itself reads and writes as structured metadata.  All producers share:

- Versioned envelopes (schema_version + producer_version)
- Deterministic canonical fingerprinting (SHA-256)
- Optional HMAC tamper-detection
- Atomic writes (temp-file + os.replace via aquilia.filesystem)
- Cross-platform file locking (AsyncFileLock)
- Typed fault domain (ArtifactCorruptFault, etc.)
- Multi-artifact transactions (all-or-nothing)

Quick Start::

    from aquilia.artifacts import ArtifactStore

    store = ArtifactStore.for_root(".aquilia/artifacts")

    # Write
    envelope = await store.put("discovery_cache", "main", payload)

    # Read
    envelope = await store.get("discovery_cache", "main")
    if envelope:
        data = envelope.payload

    # Verify integrity
    ok = await store.verify("discovery_cache", "main")

    # Multi-artifact transaction (all-or-nothing)
    async with store.transaction() as tx:
        await tx.stage("schema_snapshot", "main", snapshot)
        await tx.stage("migration", "0001_initial", migration_text)

    # Status / housekeeping
    report = await store.status()
    pruned = await store.prune(orphaned_only=True)

CLI surface::

    aq artifacts status
    aq artifacts verify <path>
    aq artifacts clean
"""

from __future__ import annotations

from .backends.json_file import JSONFileBackend
from .backends.memory import MemoryBackend
from .canonical import canonicalize
from .di import ArtifactStoreProvider, provide_artifact_store
from .envelope import ArtifactEnvelope
from .faults import (
    ArtifactCorruptFault,
    ArtifactLockTimeoutFault,
    ArtifactStaleFault,
    ArtifactTransactionFault,
)
from .integrity import sign_payload, verify_payload
from .registry import ArtifactRegistry, ArtifactTypeDescriptor, register_artifact_type
from .store import ArtifactStore, ArtifactTransaction

__all__ = [
    # Envelope
    "ArtifactEnvelope",
    # Store
    "ArtifactStore",
    "ArtifactTransaction",
    # Backends
    "JSONFileBackend",
    "MemoryBackend",
    # Canonical hashing
    "canonicalize",
    # Integrity
    "sign_payload",
    "verify_payload",
    # Registry
    "ArtifactRegistry",
    "ArtifactTypeDescriptor",
    "register_artifact_type",
    # Faults
    "ArtifactCorruptFault",
    "ArtifactStaleFault",
    "ArtifactLockTimeoutFault",
    "ArtifactTransactionFault",
    # DI
    "ArtifactStoreProvider",
    "provide_artifact_store",
]
