from __future__ import annotations

from typing import Any

from aquilia.artifacts import ArtifactBuilder, ArtifactKind, MemoryArtifactStore
from aquilia.signing import dumps, loads


class ReleaseArtifactService:
    def __init__(self, secret: str = "release-secret-key-that-is-at-least-32-bytes") -> None:
        self.store = MemoryArtifactStore()
        self.secret = secret

    def create_release(self, name: str, version: str, payload: dict[str, Any]) -> dict[str, Any]:
        artifact = (
            ArtifactBuilder(name, kind=ArtifactKind.CONFIG.value, version=version)
            .set_payload(payload)
            .set_metadata(owner="platform", pipeline="examples")
            .tag("environment", payload.get("environment", "dev"))
            .tag("type", "release")
            .build()
        )
        digest = self.store.save(artifact)
        token = dumps({"name": artifact.name, "version": artifact.version, "digest": digest}, secret=self.secret)
        return {"name": artifact.name, "version": artifact.version, "digest": digest, "verified": artifact.verify(), "token": token}

    def inspect_release(self, name: str, token: str) -> dict[str, Any]:
        signed = loads(token, secret=self.secret)
        artifact = self.store.load(name, version=signed["version"])
        if artifact is None:
            raise KeyError(name)
        if artifact.digest != signed["digest"]:
            raise ValueError("artifact digest does not match signed token")
        return {"qualified_name": artifact.qualified_name, "payload": artifact.payload, "tags": artifact.tags}

    def promote(self, name: str, from_version: str, to_version: str, environment: str) -> dict[str, Any]:
        artifact = self.store.load(name, version=from_version)
        if artifact is None:
            raise KeyError(name)
        promoted = artifact.evolve(version=to_version, environment=environment)
        self.store.save(promoted)
        return {"digest": promoted.digest, "derived_from": promoted.tags["derived_from"], "environment": promoted.payload["environment"]}
