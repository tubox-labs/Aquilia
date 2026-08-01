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

from aquilia.artifacts.backends.json_file import JSONFileBackend
from aquilia.artifacts.backends.memory import MemoryBackend
from aquilia.artifacts.canonical import canonicalize
from aquilia.artifacts.di import ArtifactStoreProvider, provide_artifact_store
from aquilia.artifacts.envelope import ArtifactEnvelope
from aquilia.artifacts.faults import (
    ArtifactCorruptFault,
    ArtifactLockTimeoutFault,
    ArtifactStaleFault,
    ArtifactTransactionFault,
)
from aquilia.artifacts.integrity import sign_payload, verify_payload
from aquilia.artifacts.registry import ArtifactRegistry, ArtifactTypeDescriptor, register_artifact_type
from aquilia.artifacts.store import ArtifactStore, ArtifactTransaction

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
