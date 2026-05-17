# Artifacts Configuration

## Configuration Entry Points

The implementation exposes the following configuration-like classes, policies, integrations, or dataclasses.

| Type | Source | Fields | Purpose |
| --- | --- | --- | --- |
| `ArtifactIntegrity` | `aquilia/artifacts/core.py` | algorithm: str, digest: str | Content-addressed integrity proof. |
| `ArtifactProvenance` | `aquilia/artifacts/core.py` | created_at: str, created_by: str, git_sha: str, source_path: str, hostname: str, build_tool: str | Where and when the artifact was produced. |
| `ArtifactEnvelope` | `aquilia/artifacts/core.py` | format: str, schema_version: str, kind: str, name: str, version: str, integrity: ArtifactIntegrity, provenance: ArtifactProvenance, metadata: dict[str, Any], tags: dict[str, str], payload: Any | The outer envelope that wraps every artifact's serialised form. |

## Common Entry Points

- No dedicated workspace integration was detected from module naming. Configure this module through direct constructors, manifests, or the subsystem that owns it.

## Precedence Model

Aquilia generally resolves configuration in this order:

1. Explicit constructor arguments or typed integration dataclass values.
2. `Workspace` builder methods and `Workspace.integrate(...)` output.
3. `ConfigLoader` defaults and environment overlays.
4. Runtime defaults inside the subsystem service or provider constructor.

When this module is registered through an `AppManifest`, keep component declarations inside `modules/<name>/manifest.py` and keep cross-cutting integration settings in `workspace.py`.

## Datatype Guidance

- Prefer typed dataclasses, policy objects, and config objects listed above when they exist.
- Keep secret values in environment-backed config, not literal strings in committed workspace files.
- Keep runtime-only state in services, stores, providers, or request state rather than static configuration.
- Use `to_dict()` on integration dataclasses when you need to inspect exactly what enters `ConfigLoader`.
