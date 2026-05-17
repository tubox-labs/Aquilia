# Artifacts API Reference

This page is generated from the current Python source using the AST. It lists public classes, public methods, public module-level functions, constants, exports, and source files.

## Source Inventory

| File | Lines | Classes | Functions | Purpose |
| --- | ---: | ---: | ---: | --- |
| `aquilia/artifacts/__init__.py` | 91 | 0 | 0 | Aquilia Artifacts -- Unified artifact system for the framework. |
| `aquilia/artifacts/builder.py` | 240 | 1 | 0 | Artifact Builder -- fluent API for constructing artifacts. |
| `aquilia/artifacts/core.py` | 416 | 5 | 1 | Artifact Core -- the foundational types for Aquilia's artifact system. |
| `aquilia/artifacts/kinds.py` | 413 | 9 | 0 | Typed Artifact Kinds -- convenience subclasses with kind-specific helpers. |
| `aquilia/artifacts/reader.py` | 250 | 1 | 0 | Artifact Reader -- load, inspect, verify, and query artifacts. |
| `aquilia/artifacts/store.py` | 449 | 3 | 1 | Artifact Store -- pluggable storage backends for artifacts. |

## Public Exports

`Artifact`, `ArtifactBuilder`, `ArtifactEnvelope`, `ArtifactIntegrity`, `ArtifactKind`, `ArtifactProvenance`, `ArtifactReader`, `ArtifactStore`, `BundleArtifact`, `CodeArtifact`, `ConfigArtifact`, `DIGraphArtifact`, `FilesystemArtifactStore`, `MemoryArtifactStore`, `MigrationArtifact`, `ModelArtifact`, `RegistryArtifact`, `RouteArtifact`, `TemplateArtifact`, `register_artifact_kind`

## Public Class Summary

| Class | Source | Bases | Summary |
| --- | --- | --- | --- |
| `ArtifactBuilder` | `aquilia/artifacts/builder.py` | object | Fluent builder for creating :class:`Artifact` instances. |
| `ArtifactKind` | `aquilia/artifacts/core.py` | str, Enum | Standard artifact kinds recognised by the framework. |
| `ArtifactIntegrity` | `aquilia/artifacts/core.py` | object | Content-addressed integrity proof. |
| `ArtifactProvenance` | `aquilia/artifacts/core.py` | object | Where and when the artifact was produced. |
| `ArtifactEnvelope` | `aquilia/artifacts/core.py` | object | The outer envelope that wraps every artifact's serialised form. |
| `Artifact` | `aquilia/artifacts/core.py` | object | First-class Aquilia artifact. |
| `ConfigArtifact` | `aquilia/artifacts/kinds.py` | Artifact | Frozen configuration snapshot. |
| `CodeArtifact` | `aquilia/artifacts/kinds.py` | Artifact | Compiled module / controller / service artifact. |
| `ModelArtifact` | `aquilia/artifacts/kinds.py` | Artifact | ML model artifact. |
| `TemplateArtifact` | `aquilia/artifacts/kinds.py` | Artifact | Compiled template artifact. |
| `MigrationArtifact` | `aquilia/artifacts/kinds.py` | Artifact | Database migration checkpoint artifact. |
| `RegistryArtifact` | `aquilia/artifacts/kinds.py` | Artifact | Module registry catalog artifact. |
| `RouteArtifact` | `aquilia/artifacts/kinds.py` | Artifact | Compiled routing table artifact. |
| `DIGraphArtifact` | `aquilia/artifacts/kinds.py` | Artifact | Compiled dependency injection graph artifact. |
| `BundleArtifact` | `aquilia/artifacts/kinds.py` | Artifact | Artifact bundle -- a container that holds multiple artifacts. |
| `ArtifactReader` | `aquilia/artifacts/reader.py` | object | High-level artifact reader / inspector. |
| `ArtifactStoreProtocol` | `aquilia/artifacts/store.py` | object | Minimal interface every store must implement. |
| `MemoryArtifactStore` | `aquilia/artifacts/store.py` | ArtifactStoreProtocol | Ephemeral in-memory artifact store. |
| `FilesystemArtifactStore` | `aquilia/artifacts/store.py` | ArtifactStoreProtocol | Persistent filesystem artifact store. |

## Public Function Summary

| Function | Source | Signature | Summary |
| --- | --- | --- | --- |
| `register_artifact_kind` | `aquilia/artifacts/core.py` | `def register_artifact_kind(kind: str, cls: type[Artifact])` | Register a typed subclass so ``Artifact.from_dict`` auto-resolves. |
| `ArtifactStore` | `aquilia/artifacts/store.py` | `def ArtifactStore(root: str='artifacts')` | Convenience constructor -- returns a :class:`FilesystemArtifactStore`. |

## Constants And Module Flags

| Name | Source | Value or Type |
| --- | --- | --- |
| `_KIND_REGISTRY` | `aquilia/artifacts/core.py` | `dict[str, type[Artifact]]` |

## Detailed Classes And Methods

### `ArtifactBuilder`

- Source: `aquilia/artifacts/builder.py`
- Bases: `object`
- Summary: Fluent builder for creating :class:`Artifact` instances.

Methods:

| Method | Signature | Summary |
| --- | --- | --- |
| `from_artifact` | `def from_artifact(cls, artifact: Artifact, *, version: str='')` | Pre-populate builder from an existing artifact. |
| `set_payload` | `def set_payload(self, payload: Any)` | Set the artifact payload (dict, list, string, bytes, …). |
| `merge_payload` | `def merge_payload(self, extra: dict[str, Any])` | Merge additional keys into an existing dict payload. |
| `set_metadata` | `def set_metadata(self, **kwargs: Any)` | Set metadata key-value pairs. |
| `tag` | `def tag(self, key: str, value: str)` | Add a tag (string→string). |
| `tags` | `def tags(self, **kwargs: str)` | Add multiple tags at once. |
| `set_provenance` | `def set_provenance(self, *, git_sha: str='', source_path: str='', created_by: str='', hostname: str='')` | Set provenance explicitly. |
| `auto_provenance` | `def auto_provenance(self, source_path: str='')` | Auto-detect provenance from the environment. |
| `add_file` | `def add_file(self, path: str, *, role: str='data', digest: str='', size: int=0)` | Register a file reference inside the artifact. |
| `set_version` | `def set_version(self, version: str)` |  |
| `build` | `def build(self)` | Freeze the artifact and compute its integrity digest. |

### `ArtifactKind`

- Source: `aquilia/artifacts/core.py`
- Bases: `str, Enum`
- Summary: Standard artifact kinds recognised by the framework.

Fields and class attributes:

| Name | Type | Default / Value |
| --- | --- | --- |
| `CONFIG` | `` | `'config'` |
| `CODE` | `` | `'code'` |
| `MODEL` | `` | `'model'` |
| `TEMPLATE` | `` | `'template'` |
| `MIGRATION` | `` | `'migration'` |
| `REGISTRY` | `` | `'registry'` |
| `ROUTE` | `` | `'route'` |
| `DI_GRAPH` | `` | `'di_graph'` |
| `MODULE` | `` | `'module'` |
| `WORKSPACE` | `` | `'workspace'` |
| `BUNDLE` | `` | `'bundle'` |
| `CUSTOM` | `` | `'custom'` |

### `ArtifactIntegrity`

- Source: `aquilia/artifacts/core.py`
- Bases: `object`
- Summary: Content-addressed integrity proof.
- Decorators: `dataclass(frozen=True)`

Fields and class attributes:

| Name | Type | Default / Value |
| --- | --- | --- |
| `algorithm` | `str` | `'sha256'` |
| `digest` | `str` | `''` |

Methods:

| Method | Signature | Summary |
| --- | --- | --- |
| `to_dict` | `def to_dict(self)` |  |
| `from_dict` | `def from_dict(cls, d: dict[str, Any])` |  |
| `compute` | `def compute(cls, data: bytes, algorithm: str='sha256')` | Compute integrity from raw bytes. |
| `verify` | `def verify(self, data: bytes)` | Verify that *data* matches this integrity proof. |

### `ArtifactProvenance`

- Source: `aquilia/artifacts/core.py`
- Bases: `object`
- Summary: Where and when the artifact was produced.
- Decorators: `dataclass(frozen=True)`

Fields and class attributes:

| Name | Type | Default / Value |
| --- | --- | --- |
| `created_at` | `str` | `''` |
| `created_by` | `str` | `''` |
| `git_sha` | `str` | `''` |
| `source_path` | `str` | `''` |
| `hostname` | `str` | `''` |
| `build_tool` | `str` | `'aquilia'` |

Methods:

| Method | Signature | Summary |
| --- | --- | --- |
| `to_dict` | `def to_dict(self)` |  |
| `from_dict` | `def from_dict(cls, d: dict[str, Any])` |  |
| `auto` | `def auto(cls, source_path: str='')` | Auto-populate with current env info. |

### `ArtifactEnvelope`

- Source: `aquilia/artifacts/core.py`
- Bases: `object`
- Summary: The outer envelope that wraps every artifact's serialised form.
- Decorators: `dataclass`

Fields and class attributes:

| Name | Type | Default / Value |
| --- | --- | --- |
| `format` | `str` | `'aquilia-artifact'` |
| `schema_version` | `str` | `'1.0'` |
| `kind` | `str` | `''` |
| `name` | `str` | `''` |
| `version` | `str` | `''` |
| `integrity` | `ArtifactIntegrity` | `field(default_factory=ArtifactIntegrity)` |
| `provenance` | `ArtifactProvenance` | `field(default_factory=ArtifactProvenance)` |
| `metadata` | `dict[str, Any]` | `field(default_factory=dict)` |
| `tags` | `dict[str, str]` | `field(default_factory=dict)` |
| `payload` | `Any` | `None` |

Methods:

| Method | Signature | Summary |
| --- | --- | --- |
| `to_dict` | `def to_dict(self)` |  |
| `is_known_kind` | `def is_known_kind(self)` | True when *kind* matches a standard :class:`ArtifactKind`. |
| `from_dict` | `def from_dict(cls, d: dict[str, Any])` |  |

### `Artifact`

- Source: `aquilia/artifacts/core.py`
- Bases: `object`
- Summary: First-class Aquilia artifact.

Methods:

| Method | Signature | Summary |
| --- | --- | --- |
| `name` | `def name(self)` |  |
| `version` | `def version(self)` |  |
| `kind` | `def kind(self)` |  |
| `qualified_name` | `def qualified_name(self)` | ``name:version`` identifier. |
| `digest` | `def digest(self)` | Full digest string, e.g. ``sha256:abc123…``. |
| `integrity` | `def integrity(self)` |  |
| `verify` | `def verify(self)` | Re-compute digest from payload and compare. |
| `provenance` | `def provenance(self)` |  |
| `created_at` | `def created_at(self)` |  |
| `age_seconds` | `def age_seconds(self)` | Seconds since the artifact was created (0.0 if unknown). |
| `metadata` | `def metadata(self)` |  |
| `tags` | `def tags(self)` |  |
| `payload` | `def payload(self)` |  |
| `envelope` | `def envelope(self)` |  |
| `size_bytes` | `def size_bytes(self)` | Approximate serialised size of the payload in bytes. |
| `evolve` | `def evolve(self, *, version: str='', **payload_overrides: Any)` | Create a **new** artifact derived from this one. |
| `to_dict` | `def to_dict(self)` |  |
| `to_json` | `def to_json(self, indent: int=2)` |  |
| `to_bytes` | `def to_bytes(self)` |  |
| `from_dict` | `def from_dict(cls, d: dict[str, Any])` | Deserialise and return the correct typed subclass when possible. |
| `from_json` | `def from_json(cls, raw: str)` |  |
| `from_bytes` | `def from_bytes(cls, data: bytes)` |  |

### `ConfigArtifact`

- Source: `aquilia/artifacts/kinds.py`
- Bases: `Artifact`
- Summary: Frozen configuration snapshot.

Methods:

| Method | Signature | Summary |
| --- | --- | --- |
| `build` | `def build(cls, name: str, version: str, config: dict[str, Any], **metadata: Any)` |  |
| `config` | `def config(self)` |  |
| `get` | `def get(self, key: str, default: Any=None)` |  |

### `CodeArtifact`

- Source: `aquilia/artifacts/kinds.py`
- Bases: `Artifact`
- Summary: Compiled module / controller / service artifact.

Methods:

| Method | Signature | Summary |
| --- | --- | --- |
| `build` | `def build(cls, name: str, version: str, *, controllers: list[str] \| None=None, services: list[str] \| None=None, route_prefix: str='/', fault_domain: str='GENERIC', depends_on: list[str] \| None=None, **metadata: Any)` |  |
| `controllers` | `def controllers(self)` |  |
| `services` | `def services(self)` |  |
| `route_prefix` | `def route_prefix(self)` |  |
| `fault_domain` | `def fault_domain(self)` |  |
| `depends_on` | `def depends_on(self)` |  |

### `ModelArtifact`

- Source: `aquilia/artifacts/kinds.py`
- Bases: `Artifact`
- Summary: ML model artifact.

Methods:

| Method | Signature | Summary |
| --- | --- | --- |
| `build` | `def build(cls, name: str, version: str, *, framework: str='custom', entrypoint: str='', accuracy: float=0.0, files: list[dict[str, Any]] \| None=None, **metadata: Any)` |  |
| `framework` | `def framework(self)` |  |
| `entrypoint` | `def entrypoint(self)` |  |
| `accuracy` | `def accuracy(self)` |  |
| `files` | `def files(self)` |  |

### `TemplateArtifact`

- Source: `aquilia/artifacts/kinds.py`
- Bases: `Artifact`
- Summary: Compiled template artifact.

Methods:

| Method | Signature | Summary |
| --- | --- | --- |
| `build` | `def build(cls, name: str, version: str, *, templates: dict[str, Any] \| None=None, **metadata: Any)` |  |
| `templates` | `def templates(self)` |  |
| `template_count` | `def template_count(self)` |  |

### `MigrationArtifact`

- Source: `aquilia/artifacts/kinds.py`
- Bases: `Artifact`
- Summary: Database migration checkpoint artifact.

Methods:

| Method | Signature | Summary |
| --- | --- | --- |
| `build` | `def build(cls, name: str, version: str, *, migrations_applied: list[str] \| None=None, head: str='', schema_hash: str='', **metadata: Any)` |  |
| `head` | `def head(self)` |  |
| `migrations_applied` | `def migrations_applied(self)` |  |
| `schema_hash` | `def schema_hash(self)` |  |

### `RegistryArtifact`

- Source: `aquilia/artifacts/kinds.py`
- Bases: `Artifact`
- Summary: Module registry catalog artifact.

Methods:

| Method | Signature | Summary |
| --- | --- | --- |
| `build` | `def build(cls, name: str, version: str, *, modules: list[dict[str, Any]] \| None=None, **metadata: Any)` |  |
| `modules` | `def modules(self)` |  |

### `RouteArtifact`

- Source: `aquilia/artifacts/kinds.py`
- Bases: `Artifact`
- Summary: Compiled routing table artifact.

Methods:

| Method | Signature | Summary |
| --- | --- | --- |
| `build` | `def build(cls, name: str, version: str, *, routes: list[dict[str, Any]] \| None=None, **metadata: Any)` |  |
| `routes` | `def routes(self)` |  |

### `DIGraphArtifact`

- Source: `aquilia/artifacts/kinds.py`
- Bases: `Artifact`
- Summary: Compiled dependency injection graph artifact.

Methods:

| Method | Signature | Summary |
| --- | --- | --- |
| `build` | `def build(cls, name: str, version: str, *, providers: list[dict[str, Any]] \| None=None, **metadata: Any)` |  |
| `providers` | `def providers(self)` |  |

### `BundleArtifact`

- Source: `aquilia/artifacts/kinds.py`
- Bases: `Artifact`
- Summary: Artifact bundle -- a container that holds multiple artifacts.

Methods:

| Method | Signature | Summary |
| --- | --- | --- |
| `build` | `def build(cls, name: str, version: str, *, artifacts: list[dict[str, Any]] \| None=None, **metadata: Any)` |  |
| `artifacts` | `def artifacts(self)` |  |
| `artifact_count` | `def artifact_count(self)` |  |
| `unpack` | `def unpack(self)` | Deserialise contained artifacts. |

### `ArtifactReader`

- Source: `aquilia/artifacts/reader.py`
- Bases: `object`
- Summary: High-level artifact reader / inspector.

Methods:

| Method | Signature | Summary |
| --- | --- | --- |
| `store` | `def store(self)` | Underlying store reference. |
| `load` | `def load(self, name: str, *, version: str='')` | Load an artifact by name and optional version. |
| `load_or_fail` | `def load_or_fail(self, name: str, *, version: str='')` | Load or raise ``FileNotFoundError``. |
| `load_by_digest` | `def load_by_digest(self, digest: str)` | Content-addressed lookup. |
| `list_all` | `def list_all(self, *, kind: str='')` | List all artifacts, optionally filtered by kind. |
| `history` | `def history(self, name: str)` | All versions of a named artifact, oldest first. |
| `search` | `def search(self, *, kind: str='', tag_key: str='', tag_value: str='', name_prefix: str='')` | Search artifacts by kind, tag, or name prefix. |
| `names` | `def names(self)` | Unique artifact names in the store (sorted). |
| `latest` | `def latest(self, name: str)` | Latest version of a named artifact by creation time. |
| `verify` | `def verify(self, artifact: Artifact)` | Re-compute the payload digest and compare to stored integrity. |
| `verify_by_name` | `def verify_by_name(self, name: str, *, version: str='')` | Load + verify an artifact. |
| `batch_verify` | `def batch_verify(self)` | Verify every artifact in the store. |
| `inspect` | `def inspect(artifact: Artifact)` | Return a human-readable inspection summary. |
| `diff` | `def diff(a: Artifact, b: Artifact)` | Compare two artifacts and return a diff summary. |
| `stats` | `def stats(self)` | Aggregate statistics about the store. |

### `ArtifactStoreProtocol`

- Source: `aquilia/artifacts/store.py`
- Bases: `object`
- Summary: Minimal interface every store must implement.

Methods:

| Method | Signature | Summary |
| --- | --- | --- |
| `save` | `def save(self, artifact: Artifact)` |  |
| `load` | `def load(self, name: str, *, version: str='')` |  |
| `load_by_digest` | `def load_by_digest(self, digest: str)` |  |
| `list_artifacts` | `def list_artifacts(self, *, kind: str='', tag_key: str='', tag_value: str='')` |  |
| `delete` | `def delete(self, name: str, *, version: str='')` |  |
| `exists` | `def exists(self, name: str, *, version: str='')` |  |

### `MemoryArtifactStore`

- Source: `aquilia/artifacts/store.py`
- Bases: `ArtifactStoreProtocol`
- Summary: Ephemeral in-memory artifact store.

Methods:

| Method | Signature | Summary |
| --- | --- | --- |
| `save` | `def save(self, artifact: Artifact)` |  |
| `load` | `def load(self, name: str, *, version: str='')` |  |
| `load_by_digest` | `def load_by_digest(self, digest: str)` |  |
| `list_artifacts` | `def list_artifacts(self, *, kind: str='', tag_key: str='', tag_value: str='')` |  |
| `delete` | `def delete(self, name: str, *, version: str='')` |  |
| `exists` | `def exists(self, name: str, *, version: str='')` |  |
| `gc` | `def gc(self, referenced: set[str])` | Remove artifacts whose digest is not in *referenced*. |
| `clear` | `def clear(self)` |  |
| `count` | `def count(self, *, kind: str='')` | Count artifacts, optionally filtered by kind. |

### `FilesystemArtifactStore`

- Source: `aquilia/artifacts/store.py`
- Bases: `ArtifactStoreProtocol`
- Summary: Persistent filesystem artifact store.

Methods:

| Method | Signature | Summary |
| --- | --- | --- |
| `save` | `def save(self, artifact: Artifact)` |  |
| `load` | `def load(self, name: str, *, version: str='')` |  |
| `load_by_digest` | `def load_by_digest(self, digest: str)` |  |
| `list_artifacts` | `def list_artifacts(self, *, kind: str='', tag_key: str='', tag_value: str='')` |  |
| `delete` | `def delete(self, name: str, *, version: str='')` |  |
| `exists` | `def exists(self, name: str, *, version: str='')` |  |
| `gc` | `def gc(self, referenced: set[str])` | Remove artifacts whose digest is not in *referenced*. |
| `export_bundle` | `def export_bundle(self, names: list[str], output_path: str)` | Export a subset of artifacts as a Surp binary bundle. |
| `count` | `def count(self, *, kind: str='')` | Count artifacts, optionally filtered by kind. |
| `import_bundle` | `def import_bundle(self, bundle_path: str)` | Import artifacts from a bundle file produced by ``export_bundle``. |
