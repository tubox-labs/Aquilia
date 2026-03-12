"""
Aquilia Artifacts -- Unified artifact system for the framework.

A first-class, content-addressed artifact layer that provides:

- **Envelope format** -- every artifact is a typed, versioned, hashed container
- **Pluggable storage** -- filesystem, memory, content-addressed (``ArtifactStore``)
- **Builder API** -- fluent ``ArtifactBuilder`` for constructing artifacts
- **Reader / inspector** -- ``ArtifactReader`` for loading and verifying
- **Typed kinds** -- ``CodeArtifact``, ``ModelArtifact``, ``ConfigArtifact``, etc.
- **Provenance** -- who built it, when, from what source, git sha
- **Integrity** -- SHA-256 content hashing, optional signing
- **GC** -- garbage-collect unreferenced artifacts

Quick start::

    from aquilia.artifacts import ArtifactBuilder, ArtifactStore, ArtifactReader

    # Build
    artifact = (
        ArtifactBuilder("my-config", kind="config", version="1.0.0")
        .set_payload({"database": {"url": "sqlite:///db.sqlite3"}})
        .tag("env", "production")
        .build()
    )

    # Store
    store = ArtifactStore("./artifacts")
    store.save(artifact)

    # Read
    reader = ArtifactReader(store)
    loaded = reader.load("my-config", version="1.0.0")

    # Inspect
    print(loaded.digest)      # sha256:abc123...
    print(loaded.metadata)    # {'env': 'production'}
"""

from aquilia._version import __version__  # noqa: F401 — re-exported

from .builder import ArtifactBuilder
from .core import (
    Artifact,
    ArtifactEnvelope,
    ArtifactIntegrity,
    ArtifactKind,
    ArtifactProvenance,
    register_artifact_kind,
)
from .kinds import (
    BundleArtifact,
    CodeArtifact,
    ConfigArtifact,
    DIGraphArtifact,
    MigrationArtifact,
    ModelArtifact,
    RegistryArtifact,
    RouteArtifact,
    TemplateArtifact,
)
from .reader import ArtifactReader
from .store import ArtifactStore, FilesystemArtifactStore, MemoryArtifactStore

__all__ = [
    # Core
    "Artifact",
    "ArtifactEnvelope",
    "ArtifactKind",
    "ArtifactProvenance",
    "ArtifactIntegrity",
    "register_artifact_kind",
    # Builder
    "ArtifactBuilder",
    # Store
    "ArtifactStore",
    "MemoryArtifactStore",
    "FilesystemArtifactStore",
    # Reader
    "ArtifactReader",
    # Typed Kinds
    "CodeArtifact",
    "ModelArtifact",
    "ConfigArtifact",
    "TemplateArtifact",
    "MigrationArtifact",
    "RegistryArtifact",
    "RouteArtifact",
    "DIGraphArtifact",
    "BundleArtifact",
]
