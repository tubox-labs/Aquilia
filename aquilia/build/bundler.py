"""
Crous Bundler -- serializes artifacts to Crous binary format.

Pure Crous binary encoding using the ``crous`` pure Python API or the
``_crous_native`` Rust extension for ~20x performance.

Features:
- String deduplication (repeated keys, class paths, module names)
- Optional LZ4/ZSTD compression for production bundles
- XXH64 checksums per block (built into the Crous wire format)
- Content-addressed integrity (SHA-256 over the encoded bytes)
- Single bundle file (``build/bundle.crous``) + per-module files
- No JSON output -- Crous binary only
"""

from __future__ import annotations

import hashlib
import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

logger = logging.getLogger("aquilia.build.bundler")


# ═══════════════════════════════════════════════════════════════════════════
# Crous Backend Abstraction
# ═══════════════════════════════════════════════════════════════════════════


class _CrousBackend:
    """
    Thin wrapper that prefers ``_crous_native`` (Rust/PyO3, ~20x faster)
    and falls back to ``crous`` (pure Python).
    """

    def __init__(self):
        self._native = False
        self._mod = None
        self._encoder_cls = None

        try:
            import _crous_native as cn

            self._mod = cn
            self._native = True
            self._encoder_cls = cn.Encoder
        except ImportError:
            try:
                import crous

                self._mod = crous
                self._native = False
            except ImportError:
                raise ImportError(
                    "Crous is required for binary artifact bundling.\n"
                    "Install with: pip install crous\n"
                    "Or build the native extension: cd crous-python && maturin develop --release"
                )

    @property
    def is_native(self) -> bool:
        return self._native

    def encode(self, obj: Any) -> bytes:
        """Encode a Python object to Crous binary bytes."""
        return self._mod.encode(obj)

    def decode(self, data: bytes) -> Any:
        """Decode Crous binary bytes to Python object."""
        return self._mod.decode(data)

    def dump(self, obj: Any, path: str) -> int:
        """Encode and write to file. Returns bytes written."""
        if self._native:
            return self._mod.encode_to_file(obj, path)
        return self._mod.dump(obj, path)

    def load(self, path: str) -> Any:
        """Read and decode from file."""
        if self._native:
            return self._mod.decode_from_file(path)
        return self._mod.load(path)

    def encode_with_dedup(
        self,
        obj: Any,
        compression: str = "none",
    ) -> bytes:
        """
        Encode with string deduplication and optional compression.

        Args:
            obj: Python object to encode
            compression: "none", "lz4", "zstd", or "snappy"

        Returns:
            Encoded bytes
        """
        if self._native:
            enc = self._mod.Encoder()
            enc.enable_dedup()
            if compression != "none":
                enc.set_compression(compression)
            enc.encode(obj)
            return enc.finish()
        else:
            from crous.encoder import Encoder

            enc = Encoder()
            enc.enable_dedup()
            if compression != "none":
                from crous.wire import CompressionType

                comp_map = {
                    "zstd": CompressionType.ZSTD,
                    "lz4": CompressionType.LZ4,
                    "snappy": CompressionType.SNAPPY,
                }
                comp_type = comp_map.get(compression)
                if comp_type:
                    enc.set_compression(comp_type)

            from crous.value import Value

            enc.encode_value(Value.from_python(obj))
            return enc.finish()


# Singleton backend instance
_backend: _CrousBackend | None = None


def _get_backend() -> _CrousBackend:
    """Get or create the Crous backend singleton."""
    global _backend
    if _backend is None:
        _backend = _CrousBackend()
    return _backend


# ═══════════════════════════════════════════════════════════════════════════
# Data Structures
# ═══════════════════════════════════════════════════════════════════════════


@dataclass
class BundledArtifact:
    """A single artifact that has been serialized to Crous binary."""

    name: str
    kind: str  # "workspace", "module", "routes", "di", "registry"
    version: str
    crous_path: Path  # Path to .crous binary file
    size_bytes: int  # Size of the .crous file
    digest: str  # SHA-256 of the .crous content


@dataclass
class BundleManifest:
    """
    Manifest for a complete build bundle.

    Written as ``build/bundle.manifest.crous`` and also encoded inside
    ``build/bundle.crous`` for self-describing bundles.
    """

    workspace_name: str
    workspace_version: str
    mode: str  # "dev" or "prod"
    compression: str  # "none", "lz4", "zstd"
    artifacts: list[BundledArtifact] = field(default_factory=list)
    fingerprint: str = ""  # SHA-256 over all artifact digests
    build_time_ms: float = 0.0
    crous_backend: str = ""  # "native" or "pure-python"
    bundle_path: Path | None = None  # Path to bundle.crous

    def to_dict(self) -> dict[str, Any]:
        return {
            "__format__": "aquilia-bundle",
            "schema_version": "2.0",
            "workspace_name": self.workspace_name,
            "workspace_version": self.workspace_version,
            "mode": self.mode,
            "compression": self.compression,
            "fingerprint": self.fingerprint,
            "build_time_ms": round(self.build_time_ms, 2),
            "crous_backend": self.crous_backend,
            "artifacts": [
                {
                    "name": a.name,
                    "kind": a.kind,
                    "version": a.version,
                    "file": str(a.crous_path.name),
                    "size_bytes": a.size_bytes,
                    "digest": a.digest,
                }
                for a in self.artifacts
            ],
        }


# ═══════════════════════════════════════════════════════════════════════════
# Crous Bundler
# ═══════════════════════════════════════════════════════════════════════════


class CrousBundler:
    """
    Serializes compiled artifact dicts to Crous binary format.

    Replaces the legacy ``_write_artifact(path, data)`` which wrote JSON
    to ``.crous`` files. Now produces real Crous wire-format files with:
    - ``CROUSv1`` magic header
    - String deduplication (shared keys across repeated structures)
    - Optional block compression (LZ4 for dev, ZSTD for prod)
    - Per-block XXH64 checksums
    - Content-addressed SHA-256 digest per artifact

    Outputs (Crous binary only -- no JSON):
    - ``build/<name>.crous`` -- binary artifact (used by resolver)
    - ``build/bundle.crous`` -- single-file bundle of all artifacts
    - ``build/bundle.manifest.crous``-- bundle metadata
    """

    def __init__(
        self,
        output_dir: Path,
        compression: str = "none",
        verbose: bool = False,
    ):
        self.output_dir = output_dir.resolve()
        self.compression = compression
        self.verbose = verbose
        self._backend = _get_backend()
        self._artifacts: list[BundledArtifact] = []
        self._bundle_errors: list[str] = []

    def bundle_artifact(
        self,
        name: str,
        kind: str,
        version: str,
        payload: dict[str, Any],
    ) -> BundledArtifact:
        """
        Serialize a single artifact to Crous binary.

        Args:
            name: Artifact name (e.g., "blogs", "routes", "workspace")
            kind: Artifact kind (e.g., "module", "route", "workspace")
            version: Artifact version
            payload: The artifact payload dict

        Returns:
            BundledArtifact with paths and digest
        """
        self.output_dir.mkdir(parents=True, exist_ok=True)

        # Write Crous binary with dedup + compression
        crous_path = self.output_dir / f"{name}.crous"
        encoded = self._backend.encode_with_dedup(payload, self.compression)
        crous_path.write_bytes(encoded)

        # Compute SHA-256 digest
        digest = hashlib.sha256(encoded).hexdigest()

        artifact = BundledArtifact(
            name=name,
            kind=kind,
            version=version,
            crous_path=crous_path,
            size_bytes=len(encoded),
            digest=digest,
        )
        self._artifacts.append(artifact)

        if self.verbose:
            backend_label = "native" if self._backend.is_native else "python"

        return artifact

    def create_bundle(
        self,
        workspace_name: str,
        workspace_version: str,
        mode: str,
    ) -> BundleManifest:
        """
        Create a consolidated bundle file from all individual artifacts.

        Produces:
        - ``build/bundle.crous`` -- all artifacts in a single Crous file
        - ``build/bundle.manifest.crous`` -- bundle metadata

        Args:
            workspace_name: Workspace name
            workspace_version: Workspace version
            mode: Build mode ("dev" or "prod")

        Returns:
            BundleManifest with all artifact info and fingerprint
        """
        # Compute combined fingerprint
        hasher = hashlib.sha256()
        for artifact in sorted(self._artifacts, key=lambda a: a.name):
            hasher.update(artifact.digest.encode("utf-8"))
        fingerprint = hasher.hexdigest()

        manifest = BundleManifest(
            workspace_name=workspace_name,
            workspace_version=workspace_version,
            mode=mode,
            compression=self.compression,
            artifacts=list(self._artifacts),
            fingerprint=fingerprint,
            crous_backend="native" if self._backend.is_native else "pure-python",
        )

        # Write the combined bundle.crous
        bundle_payload = {
            "__format__": "aquilia-bundle",
            "schema_version": "2.0",
            "fingerprint": fingerprint,
            "mode": mode,
            "artifacts": {},
        }

        # Load each artifact's payload and include in bundle
        for artifact in self._artifacts:
            try:
                data = self._backend.decode(artifact.crous_path.read_bytes())
                bundle_payload["artifacts"][artifact.name] = {
                    "kind": artifact.kind,
                    "version": artifact.version,
                    "digest": artifact.digest,
                    "payload": data,
                }
            except Exception as e:
                error_msg = f"Could not include artifact '{artifact.name}' in bundle: {e}"
                logger.error(error_msg)
                self._bundle_errors.append(error_msg)

        bundle_path = self.output_dir / "bundle.crous"
        encoded_bundle = self._backend.encode_with_dedup(
            bundle_payload,
            self.compression,
        )
        bundle_path.write_bytes(encoded_bundle)
        manifest.bundle_path = bundle_path

        # Write manifest as Crous binary (bundle.manifest.crous)
        manifest_path = self.output_dir / "bundle.manifest.crous"
        manifest_path.write_bytes(self._backend.encode_with_dedup(manifest.to_dict(), self.compression))

        if self.verbose:
            pass

        return manifest

    @property
    def artifacts(self) -> list[BundledArtifact]:
        """All bundled artifacts so far."""
        return list(self._artifacts)

    @property
    def bundle_errors(self) -> list[str]:
        """Errors encountered during bundling (non-empty = degraded bundle)."""
        return list(self._bundle_errors)

    @staticmethod
    def encode_single(data: dict, compression: str = "none") -> bytes:
        """
        Encode a single dict to Crous binary (convenience method).

        Useful for callers that need a one-shot encode without setting
        up a full CrousBundler instance.

        Args:
            data: Dict to encode
            compression: Compression type ("none", "lz4", "zstd")

        Returns:
            Encoded Crous binary bytes
        """
        backend = _get_backend()
        return backend.encode_with_dedup(data, compression)
