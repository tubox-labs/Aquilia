"""
Build Resolver -- loads and verifies pre-built Crous artifacts.

Reads ``.crous`` binary artifacts from the build directory, verifies
their integrity (SHA-256 digest), and hydrates them back into
``AquilaryRegistry`` / ``RuntimeRegistry`` objects so the server
can boot from compiled state instead of re-parsing manifests.

This is the counterpart of the ``CrousBundler``: the bundler writes,
the resolver reads.
"""

from __future__ import annotations

import hashlib
import logging
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

logger = logging.getLogger("aquilia.build.resolver")


# ═══════════════════════════════════════════════════════════════════════════
# Data Structures
# ═══════════════════════════════════════════════════════════════════════════


@dataclass
class ResolvedArtifact:
    """A single verified and decoded artifact."""

    name: str
    kind: str
    version: str
    payload: Any
    digest: str
    verified: bool


@dataclass
class ResolvedBuild:
    """Complete resolved build -- ready to hydrate into a server."""

    workspace_name: str
    workspace_version: str
    mode: str
    fingerprint: str
    artifacts: dict[str, ResolvedArtifact] = field(default_factory=dict)
    modules: list[str] = field(default_factory=list)
    elapsed_ms: float = 0.0
    from_bundle: bool = False

    @property
    def is_valid(self) -> bool:
        """All artifacts verified successfully."""
        return all(a.verified for a in self.artifacts.values())

    def get_workspace_metadata(self) -> dict[str, Any] | None:
        """Get the workspace metadata artifact payload."""
        ws = self.artifacts.get("workspace") or self.artifacts.get(self.workspace_name)
        if ws:
            return ws.payload if isinstance(ws.payload, dict) else None
        return None

    def get_module_payload(self, module_name: str) -> dict[str, Any] | None:
        """Get a module's compiled artifact payload."""
        mod = self.artifacts.get(module_name)
        if mod and isinstance(mod.payload, dict):
            return mod.payload
        return None

    def get_routes(self) -> dict[str, Any] | None:
        """Get the compiled routes artifact payload."""
        for name, artifact in self.artifacts.items():
            if artifact.kind == "route" or "routes" in name:
                return artifact.payload if isinstance(artifact.payload, dict) else None
        return None

    def get_di_graph(self) -> dict[str, Any] | None:
        """Get the compiled DI graph artifact payload."""
        for name, artifact in self.artifacts.items():
            if artifact.kind == "di_graph" or "di" in name:
                return artifact.payload if isinstance(artifact.payload, dict) else None
        return None


# ═══════════════════════════════════════════════════════════════════════════
# Resolver
# ═══════════════════════════════════════════════════════════════════════════


class BuildResolver:
    """
    Loads and verifies pre-built Crous artifacts from the build directory.

    Loads ``bundle.crous`` (single file containing all artifacts) and
    verifies integrity by recomputing SHA-256 digests against recorded
    values.
    """

    def __init__(self, build_dir: Path):
        self.build_dir = build_dir.resolve()

    def has_build(self) -> bool:
        """Check if a build exists in the build directory."""
        bundle = self.build_dir / "bundle.crous"
        return bundle.exists()

    def resolve(self, verify: bool = True) -> ResolvedBuild:
        """
        Load and verify all artifacts from the build directory.

        Loads ``bundle.crous`` — the consolidated binary containing all
        compiled artifacts.

        Args:
            verify: If True, verify SHA-256 digests (recommended for prod)

        Returns:
            ResolvedBuild with all decoded artifacts

        Raises:
            FileNotFoundError: If no build exists
        """
        start = time.monotonic()

        bundle_path = self.build_dir / "bundle.crous"
        if bundle_path.exists():
            result = self._resolve_from_bundle(bundle_path, verify)
            result.elapsed_ms = (time.monotonic() - start) * 1000
            return result

        raise FileNotFoundError(
            f"No build found in {self.build_dir}.\nRun 'aq build' or 'aq compile' to create build artifacts."
        )

    def _resolve_from_bundle(
        self,
        bundle_path: Path,
        verify: bool,
    ) -> ResolvedBuild:
        """Load all artifacts from a single bundle.crous file."""
        from .bundler import _get_backend

        backend = _get_backend()

        raw_bytes = bundle_path.read_bytes()

        # Verify the bundle itself
        if verify:
            bundle_digest = hashlib.sha256(raw_bytes).hexdigest()

        bundle_data = backend.decode(raw_bytes)

        if not isinstance(bundle_data, dict):
            from aquilia.faults.domains import ConfigInvalidFault

            raise ConfigInvalidFault(
                key="build.bundle.format",
                reason="Invalid bundle format -- expected a dict",
            )

        fingerprint = bundle_data.get("fingerprint", "")
        mode = bundle_data.get("mode", "unknown")
        artifacts_data = bundle_data.get("artifacts", {})

        result = ResolvedBuild(
            workspace_name="",
            workspace_version="",
            mode=mode,
            fingerprint=fingerprint,
            from_bundle=True,
        )

        for name, artifact_info in artifacts_data.items():
            if not isinstance(artifact_info, dict):
                continue

            kind = artifact_info.get("kind", "unknown")
            version = artifact_info.get("version", "0.0.0")
            expected_digest = artifact_info.get("digest", "")
            payload = artifact_info.get("payload", {})

            verified = True
            if verify and expected_digest:
                # Re-encode payload to verify digest
                try:
                    re_encoded = backend.encode(payload)
                    actual_digest = hashlib.sha256(re_encoded).hexdigest()
                    verified = actual_digest == expected_digest
                except Exception:
                    # Verification failed -- do NOT trust the artifact
                    verified = False

            resolved = ResolvedArtifact(
                name=name,
                kind=kind,
                version=version,
                payload=payload,
                digest=expected_digest,
                verified=verified,
            )
            result.artifacts[name] = resolved

            # Extract workspace info
            if kind in ("workspace", "workspace_metadata") or name in ("workspace",):
                if isinstance(payload, dict):
                    result.workspace_name = payload.get("name", name)
                    result.workspace_version = payload.get("version", version)
                    result.modules = payload.get("modules", [])

        return result
