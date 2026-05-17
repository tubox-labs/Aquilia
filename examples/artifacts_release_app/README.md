# Artifacts Release App

## Purpose

Demonstrates release artifact creation, integrity verification, in-memory artifact storage, signed release tokens, and promotion provenance.

## Architecture

- `ReleaseArtifactService` uses `ArtifactBuilder` and `MemoryArtifactStore`.
- Signed release tokens use `aquilia.signing.dumps()` and `loads()`.
- Promotion uses `artifact.evolve()` to preserve a `derived_from` digest tag.

## Setup

```bash
python -m pip install -e ".[dev]"
python -m pytest examples/artifacts_release_app -q
```

## Run

```bash
cd examples/artifacts_release_app
python -m uvicorn runtime:app --reload --port 8070
```

## Expected Behavior

Created releases verify their own digest and can be inspected only when the signed token matches the stored artifact.

## Common Pitfalls

- Signing secrets must be at least 32 bytes for Aquilia's signing engine.
- Artifact integrity covers serialized payload, not arbitrary external files unless they are included in payload metadata.

## Extension Ideas

Add filesystem artifact store, bundle export/import, garbage collection, CI metadata, and deployment approval workflows.

## Related APIs

`ArtifactBuilder`, `ArtifactKind`, `MemoryArtifactStore`, `Artifact.verify`, `dumps`, `loads`.
