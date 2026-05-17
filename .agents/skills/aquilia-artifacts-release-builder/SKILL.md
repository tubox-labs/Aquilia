---
name: aquilia-artifacts-release-builder
description: "Build and manage Aquilia artifacts and release bundles. Use for Artifact, ArtifactBuilder, ArtifactReader, ArtifactStore, integrity/provenance, config/code/model/template/migration/registry/route/DI graph artifacts, signing, freeze, and aq artifact commands."
---

# Aquilia Artifacts Release Builder

## Purpose
Create, inspect, verify, diff, bundle, and release Aquilia artifacts using the implemented artifact system.

## Trigger Conditions
Use for artifact store operations, release bundles, provenance, integrity verification, frozen manifests, route/registry/DI graph artifacts, and `aq artifact` / `aq freeze` workflows.

## Inputs
- Artifact kind, name, version, payload, tags, provenance, store directory, bundle path, signing requirement.
- Whether operation should be read-only, destructive, or dry-run.

## Execution Flow
1. Use `ArtifactBuilder` to construct typed artifacts and include provenance/integrity metadata.
2. Persist through `FilesystemArtifactStore` or `MemoryArtifactStore`.
3. Inspect and verify with `ArtifactReader` and store APIs.
4. Use CLI `aq artifact list/inspect/verify/verify-all/gc/export/diff/history/import/count/stats` for operations.
5. Use `aq freeze` when generating reproducible release artifacts.

## Constraints
- Do not bypass integrity checks when importing or deploying artifacts.
- Garbage collection must respect keep lists and dry-run where available.
- Unknown artifact kinds should be registered with `register_artifact_kind` before use.

## Implementation Anchors
`aquilia/artifacts/`, `aquilia/cli/commands/artifacts.py`, `aquilia/cli/commands/freeze.py`, `aquilia/signing.py`, `examples/artifacts_release_app/`.

## Examples
- Export a release bundle with selected artifact names.
- Verify all artifacts in `artifacts/` before publishing.
- Diff two versions of a config or migration artifact.

## Failure Handling
Integrity mismatch should block import/deploy. Missing artifacts should produce clear name/version guidance. If Crous/frozen formats fail, fall back only where code supports JSON behavior.
