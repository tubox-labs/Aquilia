"""
ArtifactEnvelope — Versioned, typed wrapper for every artifact payload.

Every artifact persisted by the framework (discovery cache, frozen registry
manifest, schema snapshot, template bytecode cache, WebSocket metadata, MCP
knowledge index) is stored inside this common envelope.  The envelope
carries the metadata needed for:

- Format negotiation (schema_version)
- Producer-version–driven cache invalidation (producer_version)
- Integrity verification (fingerprint, hmac_signature when signed)
- Observability (created_at, artifact_type, key)

The payload field is opaque to the envelope itself; each artifact type
knows how to interpret its own payload.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from typing import Any

from aquilia._version import __version__ as _AQUILIA_VERSION  # noqa: N812

# Current envelope format identifier — bump when the envelope shape changes,
# not when an individual artifact's payload schema changes.
ENVELOPE_FORMAT = "aquilia-artifact"
ENVELOPE_VERSION = "1.0"


@dataclass
class ArtifactEnvelope:
    """
    Immutable, versioned wrapper around any artifact payload.

    Attributes
    ----------
    format
        Always ``"aquilia-artifact"``.  Used to detect non-Aquilia files
        that happen to be JSON.
    schema_version
        Payload schema version for this artifact type.  Consumers reject
        envelopes whose schema_version they don't recognise and treat them
        as a cold-cache miss (triggering a clean rebuild).
    producer_version
        Aquilia framework version that wrote this artifact.  A version
        mismatch is logged at INFO level; the artifact is still used
        unless the schema_version also changed.
    artifact_type
        Registered artifact-type identifier (e.g. ``"discovery_cache"``,
        ``"frozen_registry"``, ``"schema_snapshot"``).
    key
        Within-type identifier (e.g. ``"main"`` for a singleton artifact,
        or ``"0001_initial"`` for a named migration file).
    fingerprint
        SHA-256 hex digest of the canonical payload representation.
        Always present; used for corruption detection.
    hmac_signature
        Optional HMAC-SHA256 signature (``"<64-hex-char>"``) of the
        serialized payload bytes, keyed by ``AQUILIA_CACHE_SECRET`` or a
        path-derived fallback.  Present only when ``sign=True`` was passed
        to :meth:`ArtifactStore.put`.
    created_at
        ISO-8601 UTC timestamp of when this envelope was written.
    payload
        The artifact-specific data.  Opaque to the envelope.
    extra
        Reserved for future use; round-tripped transparently.
    """

    format: str
    schema_version: str
    producer_version: str
    artifact_type: str
    key: str
    fingerprint: str
    created_at: str
    payload: Any
    hmac_signature: str | None = None
    extra: dict[str, Any] = field(default_factory=dict)

    # ------------------------------------------------------------------
    # Construction helpers
    # ------------------------------------------------------------------

    @classmethod
    def build(
        cls,
        *,
        artifact_type: str,
        key: str,
        schema_version: str,
        payload: Any,
        fingerprint: str,
        signed: bool = False,
        hmac_signature: str | None = None,
        producer_version: str | None = None,
        extra: dict[str, Any] | None = None,
    ) -> ArtifactEnvelope:
        """Build a new envelope from components."""
        return cls(
            format=ENVELOPE_FORMAT,
            schema_version=schema_version,
            producer_version=producer_version or _AQUILIA_VERSION,
            artifact_type=artifact_type,
            key=key,
            fingerprint=fingerprint,
            created_at=datetime.now(timezone.utc).isoformat(),
            payload=payload,
            hmac_signature=hmac_signature if signed else None,
            extra=extra or {},
        )

    # ------------------------------------------------------------------
    # Serialization
    # ------------------------------------------------------------------

    def to_dict(self) -> dict[str, Any]:
        """Serialize envelope to a plain dict (JSON-safe)."""
        d = asdict(self)
        d["__format__"] = "json"  # Backward compatibility marker
        # Remove None values for cleaner JSON output
        if self.hmac_signature is None:
            d.pop("hmac_signature", None)
        if not self.extra:
            d.pop("extra", None)
        return d

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> ArtifactEnvelope:
        """
        Deserialize an envelope from a plain dict.

        Raises
        ------
        ValueError
            If the dict is missing required envelope fields or has an
            unrecognised ``format`` marker.
        """
        if not isinstance(data, dict):
            raise ValueError(f"Expected dict, got {type(data).__name__}")

        fmt = data.get("format")
        if fmt != ENVELOPE_FORMAT:
            raise ValueError(f"Unrecognised artifact format {fmt!r}; expected {ENVELOPE_FORMAT!r}")

        required = (
            "schema_version",
            "producer_version",
            "artifact_type",
            "key",
            "fingerprint",
            "created_at",
            "payload",
        )
        missing = [k for k in required if k not in data]
        if missing:
            raise ValueError(f"Envelope missing required fields: {missing!r}")

        return cls(
            format=data["format"],
            schema_version=data["schema_version"],
            producer_version=data["producer_version"],
            artifact_type=data["artifact_type"],
            key=data["key"],
            fingerprint=data["fingerprint"],
            created_at=data["created_at"],
            payload=data["payload"],
            hmac_signature=data.get("hmac_signature"),
            extra=data.get("extra") or {},
        )

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def is_signed(self) -> bool:
        """Whether this envelope carries an HMAC signature."""
        return self.hmac_signature is not None

    def created_at_dt(self) -> datetime:
        """Return created_at as a timezone-aware datetime."""
        return datetime.fromisoformat(self.created_at)

    def __repr__(self) -> str:  # pragma: no cover
        return (
            f"ArtifactEnvelope("
            f"type={self.artifact_type!r}, "
            f"key={self.key!r}, "
            f"schema={self.schema_version!r}, "
            f"fp={self.fingerprint[:16]}..., "
            f"signed={self.is_signed()})"
        )
