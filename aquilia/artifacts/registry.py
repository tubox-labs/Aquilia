"""
Artifact type registry — metadata descriptors and registration decorator.

Each artifact producer calls ``register_artifact_type`` once at module
load time (or in DI setup) to declare its artifact's:

- Type identifier string
- Which backend to use (JSON file, SQLite, memory)
- Schema version (payload format)
- Corruption policy (raise / warn_and_reset / reset)
- Whether to sign with HMAC (tamper-detection)
- Relative path within the artifact root

Registered types are used by :class:`ArtifactStore` to resolve paths,
select backends, enforce integrity policies, and produce status reports
(``aq artifacts status``).

Built-in registrations live here and are imported by
``aquilia/artifacts/__init__.py``.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import TYPE_CHECKING, Any, Literal

if TYPE_CHECKING:
    pass

logger = logging.getLogger("aquilia.artifacts.registry")

# On-corrupt policies: what to do when a loaded artifact is corrupt/tampered
OnCorruptPolicy = Literal["raise", "warn_and_reset", "reset"]


@dataclass
class ArtifactTypeDescriptor:
    """
    Metadata descriptor for a registered artifact type.

    Parameters
    ----------
    artifact_type
        Unique type identifier, e.g. ``"discovery_cache"``.
    schema_version
        Current payload schema version for this type.  When the on-disk
        schema_version differs from this, the artifact is treated as
        incompatible and rebuilt.
    relative_path
        Path relative to the artifact root where this type's files live.
        May include a ``{key}`` placeholder for keyed artifacts, e.g.
        ``"migrations/{key}.json"``.
    backend
        Backend class name: ``"json_file"`` (default), ``"memory"``, or
        ``"sqlite"`` (reserved, not yet implemented).
    on_corrupt
        What to do when an artifact is corrupt on load.
    sign
        Whether to sign artifacts with HMAC-SHA256.  Use for artifacts
        whose tampering has security implications (frozen manifest).
    description
        Human-readable description shown in ``aq artifacts status``.
    """

    artifact_type: str
    schema_version: str
    relative_path: str
    backend: str = "json_file"
    on_corrupt: OnCorruptPolicy = "warn_and_reset"
    sign: bool = False
    description: str = ""
    extra: dict[str, Any] = field(default_factory=dict)

    def resolve_path(self, root: Path, key: str) -> Path:
        """Resolve the absolute artifact file path for a given key."""
        rel = self.relative_path.replace("{key}", key).replace("{artifact_type}", self.artifact_type)
        return root / rel


# ─────────────────────────────────────────────────────────────────────────────
# Global registry
# ─────────────────────────────────────────────────────────────────────────────

_REGISTRY: dict[str, ArtifactTypeDescriptor] = {}


def register_artifact_type(
    artifact_type: str,
    *,
    schema_version: str,
    relative_path: str,
    backend: str = "json_file",
    on_corrupt: OnCorruptPolicy = "warn_and_reset",
    sign: bool = False,
    description: str = "",
    overwrite: bool = False,
    **extra: Any,
) -> ArtifactTypeDescriptor:
    """
    Register an artifact type.

    Can be used as a decorator or called directly::

        # Direct call (module-level setup)
        register_artifact_type(
            "discovery_cache",
            schema_version="1.0",
            relative_path="discovery_cache.json",
            on_corrupt="warn_and_reset",
            description="AST discovery cache for auto-discovery engine",
        )

        # Decorator on a producer class (optional style)
        @register_artifact_type("ws_metadata", schema_version="1.0", ...)
        class SocketCompiler: ...

    Parameters
    ----------
    artifact_type
        Unique type identifier.  Must not contain path separators.
    schema_version
        Payload schema version string.
    relative_path
        Path relative to artifact root.  Use ``{key}`` for keyed artifacts.
    backend
        Backend: ``"json_file"`` (default), ``"memory"``.
    on_corrupt
        Corruption policy.
    sign
        If ``True``, write HMAC signature header.
    description
        Human-readable description.
    overwrite
        If ``True``, re-registration of an existing type is allowed.
    **extra
        Passed through to :attr:`ArtifactTypeDescriptor.extra`.
    """
    if "/" in artifact_type or "\\" in artifact_type:
        raise ValueError(f"artifact_type must not contain path separators: {artifact_type!r}")

    if artifact_type in _REGISTRY and not overwrite:
        existing = _REGISTRY[artifact_type]
        if existing.schema_version != schema_version or existing.relative_path != relative_path:
            logger.warning(
                "Artifact type %r already registered with different parameters; ignoring re-registration. "
                "Pass overwrite=True to override.",
                artifact_type,
            )
        return _REGISTRY[artifact_type]

    descriptor = ArtifactTypeDescriptor(
        artifact_type=artifact_type,
        schema_version=schema_version,
        relative_path=relative_path,
        backend=backend,
        on_corrupt=on_corrupt,
        sign=sign,
        description=description,
        extra=extra,
    )
    _REGISTRY[artifact_type] = descriptor
    return descriptor


def get_descriptor(artifact_type: str) -> ArtifactTypeDescriptor | None:
    """Return the registered descriptor for ``artifact_type``, or ``None``."""
    return _REGISTRY.get(artifact_type)


def get_all_descriptors() -> dict[str, ArtifactTypeDescriptor]:
    """Return a copy of all registered descriptors."""
    return dict(_REGISTRY)


class ArtifactRegistry:
    """
    Runtime catalog of known artifact types and their on-disk status.

    This is an in-memory, rebuild-on-scan index.  It does not persist itself
    to disk — it is reconstructed cheaply each time by scanning the artifact
    root.

    Used by ``aq artifacts status`` to answer: "what artifacts are on disk,
    what are their fingerprints, and are they all current?"
    """

    def __init__(self, root: Path) -> None:
        self._root = root
        self._entries: dict[str, dict[str, Any]] = {}

    def scan(self) -> dict[str, dict[str, Any]]:
        """
        Scan the artifact root and build an in-memory status report.

        Returns a dict keyed by artifact type, each value being a dict
        of file path → status info.
        """
        from .backends.json_file import JSONFileBackend
        from .envelope import ArtifactEnvelope

        results: dict[str, dict[str, Any]] = {}

        if not self._root.exists():
            return results

        for descriptor in get_all_descriptors().values():
            entries: dict[str, Any] = {}

            # Find all matching files under root
            for json_file in self._root.rglob("*.json"):
                try:
                    backend = JSONFileBackend()
                    # Use sync read for scanning
                    raw = json_file.read_bytes()
                    import json as _json

                    # Try to parse as envelope
                    try:
                        data = _json.loads(raw)
                    except Exception:
                        continue

                    if not isinstance(data, dict):
                        continue

                    # Skip files with HMAC header — handled separately
                    artifact_type = data.get("artifact_type")
                    if artifact_type != descriptor.artifact_type:
                        continue

                    try:
                        envelope = ArtifactEnvelope.from_dict(data)
                        entries[str(json_file)] = {
                            "key": envelope.key,
                            "schema_version": envelope.schema_version,
                            "producer_version": envelope.producer_version,
                            "fingerprint": envelope.fingerprint,
                            "created_at": envelope.created_at,
                            "signed": envelope.is_signed(),
                            "size": json_file.stat().st_size,
                        }
                    except Exception as exc:
                        entries[str(json_file)] = {"error": str(exc)}

                except Exception:
                    continue

            if entries:
                results[descriptor.artifact_type] = entries

        self._entries = results
        return results

    def summary(self) -> list[dict[str, Any]]:
        """Return a flat list of artifact status records for CLI display."""
        records = []
        for artifact_type, files in self._entries.items():
            for path, info in files.items():
                record = {"type": artifact_type, "path": path}
                record.update(info)
                records.append(record)
        return records


# ─────────────────────────────────────────────────────────────────────────────
# Built-in artifact type registrations
# ─────────────────────────────────────────────────────────────────────────────

# Phase A — registered here so they're available immediately
register_artifact_type(
    "discovery_cache",
    schema_version="1.0",
    relative_path="discovery_cache.json",
    backend="json_file",
    on_corrupt="warn_and_reset",
    description="AST discovery cache for auto-discovery engine",
)

register_artifact_type(
    "frozen_registry",
    schema_version="1.0",
    relative_path="frozen_registry.json",
    backend="json_file",
    on_corrupt="raise",
    sign=True,
    description="Frozen registry manifest for reproducible deploys",
)

register_artifact_type(
    "schema_snapshot",
    schema_version="1.0",
    relative_path="schema_snapshot.json",
    backend="json_file",
    on_corrupt="raise",
    description="ORM schema snapshot for migration generation",
)

register_artifact_type(
    "ws_metadata",
    schema_version="1.0",
    relative_path="ws.json",
    backend="json_file",
    on_corrupt="warn_and_reset",
    description="WebSocket controller metadata artifact",
)

register_artifact_type(
    "template_manifest",
    schema_version="1.0",
    relative_path="templates.json",
    backend="json_file",
    on_corrupt="warn_and_reset",
    description="Template directory manifest",
)

register_artifact_type(
    "mcp_knowledge_index",
    schema_version="1.0",
    relative_path="mcp_knowledge_index.json",
    backend="json_file",
    on_corrupt="warn_and_reset",
    description="MCP context tool knowledge index",
)

register_artifact_type(
    "template_bytecode",
    schema_version="1.1",
    relative_path="templates.bytecode.json",
    backend="json_file",
    on_corrupt="warn_and_reset",
    sign=True,
    description="Compiled Jinja2 template bytecode cache",
)

register_artifact_type(
    "di_manifest",
    schema_version="1.0",
    relative_path="di_manifest.json",
    backend="json_file",
    on_corrupt="warn_and_reset",
    description="DI provider graph for LSP/IDE tooling",
)

register_artifact_type(
    "route_index",
    schema_version="1.0",
    relative_path="route_index.json",
    backend="json_file",
    on_corrupt="warn_and_reset",
    description="Compiled route index from Aquilary",
)

register_artifact_type(
    "migration_file",
    schema_version="1.0",
    relative_path="migrations/{key}.py",
    backend="json_file",
    on_corrupt="raise",
    description="Generated Python migration source file",
)
