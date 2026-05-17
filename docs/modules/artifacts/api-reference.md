# Artifacts API Reference

This page is extracted from the current Python source. It includes public classes, methods, functions, constants, dataclass-like fields, decorators, and notable attributes.

## Public Class Summary

| Name | Source | Bases | Purpose |
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

| Name | Source | Signature | Purpose |
| --- | --- | --- | --- |
| `register_artifact_kind` | `aquilia/artifacts/core.py` | `def register_artifact_kind(kind: str, cls: type[Artifact]) -> None` | Register a typed subclass so ``Artifact.from_dict`` auto-resolves. |
| `ArtifactStore` | `aquilia/artifacts/store.py` | `def ArtifactStore(root: str = 'artifacts') -> FilesystemArtifactStore` | Convenience constructor -- returns a :class:`FilesystemArtifactStore`. |

## Constants

| Name | Source | Value or type |
| --- | --- | --- |
| `_KIND_REGISTRY` | `aquilia/artifacts/core.py` | `dict[str, type[Artifact]]` |

## Detailed Classes And Methods

### Class: `ArtifactBuilder`

- Source: `aquilia/artifacts/builder.py`
- Bases: `object`
- Summary: Fluent builder for creating :class:`Artifact` instances.

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `from_artifact` | `def from_artifact(cls, artifact: Artifact, *, version: str = '') -> ArtifactBuilder` | classmethod | Pre-populate builder from an existing artifact. |
| `set_payload` | `def set_payload(self, payload: Any) -> ArtifactBuilder` |  | Set the artifact payload (dict, list, string, bytes, ...). |
| `merge_payload` | `def merge_payload(self, extra: dict[str, Any]) -> ArtifactBuilder` |  | Merge additional keys into an existing dict payload. |
| `set_metadata` | `def set_metadata(self, **kwargs: Any) -> ArtifactBuilder` |  | Set metadata key-value pairs. |
| `tag` | `def tag(self, key: str, value: str) -> ArtifactBuilder` |  | Add a tag (string->string). |
| `tags` | `def tags(self, **kwargs: str) -> ArtifactBuilder` |  | Add multiple tags at once. |
| `set_provenance` | `def set_provenance(self, *, git_sha: str = '', source_path: str = '', created_by: str = '', hostname: str = '') -> ArtifactBuilder` |  | Set provenance explicitly. |
| `auto_provenance` | `def auto_provenance(self, source_path: str = '') -> ArtifactBuilder` |  | Auto-detect provenance from the environment. |
| `add_file` | `def add_file(self, path: str, *, role: str = 'data', digest: str = '', size: int = 0) -> ArtifactBuilder` |  | Register a file reference inside the artifact. |
| `set_version` | `def set_version(self, version: str) -> ArtifactBuilder` |  | Method. |
| `build` | `def build(self) -> Artifact` |  | Freeze the artifact and compute its integrity digest. |

### Class: `ArtifactKind`

- Source: `aquilia/artifacts/core.py`
- Bases: `str, Enum`
- Summary: Standard artifact kinds recognised by the framework.

Attributes and fields:

| Name | Type | Default |
| --- | --- | --- |
| `CONFIG` |  | `'config'` |
| `CODE` |  | `'code'` |
| `MODEL` |  | `'model'` |
| `TEMPLATE` |  | `'template'` |
| `MIGRATION` |  | `'migration'` |
| `REGISTRY` |  | `'registry'` |
| `ROUTE` |  | `'route'` |
| `DI_GRAPH` |  | `'di_graph'` |
| `MODULE` |  | `'module'` |
| `WORKSPACE` |  | `'workspace'` |
| `BUNDLE` |  | `'bundle'` |
| `CUSTOM` |  | `'custom'` |

### Class: `ArtifactIntegrity`

- Source: `aquilia/artifacts/core.py`
- Bases: `object`
- Decorators: `dataclass`
- Summary: Content-addressed integrity proof.

Attributes and fields:

| Name | Type | Default |
| --- | --- | --- |
| `algorithm` | `str` | `'sha256'` |
| `digest` | `str` | `''` |

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `to_dict` | `def to_dict(self) -> dict[str, str]` |  | Method. |
| `from_dict` | `def from_dict(cls, d: dict[str, Any]) -> ArtifactIntegrity` | classmethod | Method. |
| `compute` | `def compute(cls, data: bytes, algorithm: str = 'sha256') -> ArtifactIntegrity` | classmethod | Compute integrity from raw bytes. |
| `verify` | `def verify(self, data: bytes) -> bool` |  | Verify that *data* matches this integrity proof. |

### Class: `ArtifactProvenance`

- Source: `aquilia/artifacts/core.py`
- Bases: `object`
- Decorators: `dataclass`
- Summary: Where and when the artifact was produced.

Attributes and fields:

| Name | Type | Default |
| --- | --- | --- |
| `created_at` | `str` | `''` |
| `created_by` | `str` | `''` |
| `git_sha` | `str` | `''` |
| `source_path` | `str` | `''` |
| `hostname` | `str` | `''` |
| `build_tool` | `str` | `'aquilia'` |

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `to_dict` | `def to_dict(self) -> dict[str, str]` |  | Method. |
| `from_dict` | `def from_dict(cls, d: dict[str, Any]) -> ArtifactProvenance` | classmethod | Method. |
| `auto` | `def auto(cls, source_path: str = '') -> ArtifactProvenance` | classmethod | Auto-populate with current env info. |

### Class: `ArtifactEnvelope`

- Source: `aquilia/artifacts/core.py`
- Bases: `object`
- Decorators: `dataclass`
- Summary: The outer envelope that wraps every artifact's serialised form.

Attributes and fields:

| Name | Type | Default |
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

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `to_dict` | `def to_dict(self) -> dict[str, Any]` |  | Method. |
| `is_known_kind` | `def is_known_kind(self) -> bool` | property | True when *kind* matches a standard :class:`ArtifactKind`. |
| `from_dict` | `def from_dict(cls, d: dict[str, Any]) -> ArtifactEnvelope` | classmethod | Method. |

### Class: `Artifact`

- Source: `aquilia/artifacts/core.py`
- Bases: `object`
- Summary: First-class Aquilia artifact.

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `name` | `def name(self) -> str` | property | Method. |
| `version` | `def version(self) -> str` | property | Method. |
| `kind` | `def kind(self) -> str` | property | Method. |
| `qualified_name` | `def qualified_name(self) -> str` | property | ``name:version`` identifier. |
| `digest` | `def digest(self) -> str` | property | Full digest string, e.g. ``sha256:abc123...``. |
| `integrity` | `def integrity(self) -> ArtifactIntegrity` | property | Method. |
| `verify` | `def verify(self) -> bool` |  | Re-compute digest from payload and compare. |
| `provenance` | `def provenance(self) -> ArtifactProvenance` | property | Method. |
| `created_at` | `def created_at(self) -> str` | property | Method. |
| `age_seconds` | `def age_seconds(self) -> float` | property | Seconds since the artifact was created (0.0 if unknown). |
| `metadata` | `def metadata(self) -> dict[str, Any]` | property | Method. |
| `tags` | `def tags(self) -> dict[str, str]` | property | Method. |
| `payload` | `def payload(self) -> Any` | property | Method. |
| `envelope` | `def envelope(self) -> ArtifactEnvelope` | property | Method. |
| `size_bytes` | `def size_bytes(self) -> int` | property | Approximate serialised size of the payload in bytes. |
| `evolve` | `def evolve(self, *, version: str = '', **payload_overrides: Any) -> Artifact` |  | Create a **new** artifact derived from this one. |
| `to_dict` | `def to_dict(self) -> dict[str, Any]` |  | Method. |
| `to_json` | `def to_json(self, indent: int = 2) -> str` |  | Method. |
| `to_bytes` | `def to_bytes(self) -> bytes` |  | Method. |
| `from_dict` | `def from_dict(cls, d: dict[str, Any]) -> Artifact` | classmethod | Deserialise and return the correct typed subclass when possible. |
| `from_json` | `def from_json(cls, raw: str) -> Artifact` | classmethod | Method. |
| `from_bytes` | `def from_bytes(cls, data: bytes) -> Artifact` | classmethod | Method. |

### Class: `ConfigArtifact`

- Source: `aquilia/artifacts/kinds.py`
- Bases: `Artifact`
- Summary: Frozen configuration snapshot.

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `build` | `def build(cls, name: str, version: str, config: dict[str, Any], **metadata: Any) -> ConfigArtifact` | classmethod | Method. |
| `config` | `def config(self) -> dict[str, Any]` | property | Method. |
| `get` | `def get(self, key: str, default: Any = None) -> Any` |  | Method. |

### Class: `CodeArtifact`

- Source: `aquilia/artifacts/kinds.py`
- Bases: `Artifact`
- Summary: Compiled module / controller / service artifact.

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `build` | `def build(cls, name: str, version: str, *, controllers: list[str] &#124; None = None, services: list[str] &#124; None = None, route_prefix: str = '/', fault_domain: str = 'GENERIC', depends_on: list[str] &#124; None = None, **metadata: Any) -> CodeArtifact` | classmethod | Method. |
| `controllers` | `def controllers(self) -> list[str]` | property | Method. |
| `services` | `def services(self) -> list[str]` | property | Method. |
| `route_prefix` | `def route_prefix(self) -> str` | property | Method. |
| `fault_domain` | `def fault_domain(self) -> str` | property | Method. |
| `depends_on` | `def depends_on(self) -> list[str]` | property | Method. |

### Class: `ModelArtifact`

- Source: `aquilia/artifacts/kinds.py`
- Bases: `Artifact`
- Summary: ML model artifact.

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `build` | `def build(cls, name: str, version: str, *, framework: str = 'custom', entrypoint: str = '', accuracy: float = 0.0, files: list[dict[str, Any]] &#124; None = None, **metadata: Any) -> ModelArtifact` | classmethod | Method. |
| `framework` | `def framework(self) -> str` | property | Method. |
| `entrypoint` | `def entrypoint(self) -> str` | property | Method. |
| `accuracy` | `def accuracy(self) -> float` | property | Method. |
| `files` | `def files(self) -> list[dict[str, Any]]` | property | Method. |

### Class: `TemplateArtifact`

- Source: `aquilia/artifacts/kinds.py`
- Bases: `Artifact`
- Summary: Compiled template artifact.

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `build` | `def build(cls, name: str, version: str, *, templates: dict[str, Any] &#124; None = None, **metadata: Any) -> TemplateArtifact` | classmethod | Method. |
| `templates` | `def templates(self) -> dict[str, Any]` | property | Method. |
| `template_count` | `def template_count(self) -> int` | property | Method. |

### Class: `MigrationArtifact`

- Source: `aquilia/artifacts/kinds.py`
- Bases: `Artifact`
- Summary: Database migration checkpoint artifact.

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `build` | `def build(cls, name: str, version: str, *, migrations_applied: list[str] &#124; None = None, head: str = '', schema_hash: str = '', **metadata: Any) -> MigrationArtifact` | classmethod | Method. |
| `head` | `def head(self) -> str` | property | Method. |
| `migrations_applied` | `def migrations_applied(self) -> list[str]` | property | Method. |
| `schema_hash` | `def schema_hash(self) -> str` | property | Method. |

### Class: `RegistryArtifact`

- Source: `aquilia/artifacts/kinds.py`
- Bases: `Artifact`
- Summary: Module registry catalog artifact.

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `build` | `def build(cls, name: str, version: str, *, modules: list[dict[str, Any]] &#124; None = None, **metadata: Any) -> RegistryArtifact` | classmethod | Method. |
| `modules` | `def modules(self) -> list[dict[str, Any]]` | property | Method. |

### Class: `RouteArtifact`

- Source: `aquilia/artifacts/kinds.py`
- Bases: `Artifact`
- Summary: Compiled routing table artifact.

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `build` | `def build(cls, name: str, version: str, *, routes: list[dict[str, Any]] &#124; None = None, **metadata: Any) -> RouteArtifact` | classmethod | Method. |
| `routes` | `def routes(self) -> list[dict[str, Any]]` | property | Method. |

### Class: `DIGraphArtifact`

- Source: `aquilia/artifacts/kinds.py`
- Bases: `Artifact`
- Summary: Compiled dependency injection graph artifact.

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `build` | `def build(cls, name: str, version: str, *, providers: list[dict[str, Any]] &#124; None = None, **metadata: Any) -> DIGraphArtifact` | classmethod | Method. |
| `providers` | `def providers(self) -> list[dict[str, Any]]` | property | Method. |

### Class: `BundleArtifact`

- Source: `aquilia/artifacts/kinds.py`
- Bases: `Artifact`
- Summary: Artifact bundle -- a container that holds multiple artifacts.

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `build` | `def build(cls, name: str, version: str, *, artifacts: list[dict[str, Any]] &#124; None = None, **metadata: Any) -> BundleArtifact` | classmethod | Method. |
| `artifacts` | `def artifacts(self) -> list[dict[str, Any]]` | property | Method. |
| `artifact_count` | `def artifact_count(self) -> int` | property | Method. |
| `unpack` | `def unpack(self) -> list[Artifact]` |  | Deserialise contained artifacts. |

### Class: `ArtifactReader`

- Source: `aquilia/artifacts/reader.py`
- Bases: `object`
- Summary: High-level artifact reader / inspector.

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `store` | `def store(self) -> ArtifactStoreProtocol` | property | Underlying store reference. |
| `load` | `def load(self, name: str, *, version: str = '') -> Artifact &#124; None` |  | Load an artifact by name and optional version. |
| `load_or_fail` | `def load_or_fail(self, name: str, *, version: str = '') -> Artifact` |  | Load or raise ``FileNotFoundError``. |
| `load_by_digest` | `def load_by_digest(self, digest: str) -> Artifact &#124; None` |  | Content-addressed lookup. |
| `list_all` | `def list_all(self, *, kind: str = '') -> list[Artifact]` |  | List all artifacts, optionally filtered by kind. |
| `history` | `def history(self, name: str) -> list[Artifact]` |  | All versions of a named artifact, oldest first. |
| `search` | `def search(self, *, kind: str = '', tag_key: str = '', tag_value: str = '', name_prefix: str = '') -> list[Artifact]` |  | Search artifacts by kind, tag, or name prefix. |
| `names` | `def names(self) -> list[str]` |  | Unique artifact names in the store (sorted). |
| `latest` | `def latest(self, name: str) -> Artifact &#124; None` |  | Latest version of a named artifact by creation time. |
| `verify` | `def verify(self, artifact: Artifact) -> bool` |  | Re-compute the payload digest and compare to stored integrity. |
| `verify_by_name` | `def verify_by_name(self, name: str, *, version: str = '') -> bool &#124; None` |  | Load + verify an artifact. |
| `batch_verify` | `def batch_verify(self) -> tuple[int, int, list[str]]` |  | Verify every artifact in the store. |
| `inspect` | `def inspect(artifact: Artifact) -> dict[str, Any]` | staticmethod | Return a human-readable inspection summary. |
| `diff` | `def diff(a: Artifact, b: Artifact) -> dict[str, Any]` | staticmethod | Compare two artifacts and return a diff summary. |
| `stats` | `def stats(self) -> dict[str, Any]` |  | Aggregate statistics about the store. |

### Class: `ArtifactStoreProtocol`

- Source: `aquilia/artifacts/store.py`
- Bases: `object`
- Summary: Minimal interface every store must implement.

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `save` | `def save(self, artifact: Artifact) -> str` |  | Method. |
| `load` | `def load(self, name: str, *, version: str = '') -> Artifact &#124; None` |  | Method. |
| `load_by_digest` | `def load_by_digest(self, digest: str) -> Artifact &#124; None` |  | Method. |
| `list_artifacts` | `def list_artifacts(self, *, kind: str = '', tag_key: str = '', tag_value: str = '') -> list[Artifact]` |  | Method. |
| `delete` | `def delete(self, name: str, *, version: str = '') -> int` |  | Method. |
| `exists` | `def exists(self, name: str, *, version: str = '') -> bool` |  | Method. |

### Class: `MemoryArtifactStore`

- Source: `aquilia/artifacts/store.py`
- Bases: `ArtifactStoreProtocol`
- Summary: Ephemeral in-memory artifact store.

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `save` | `def save(self, artifact: Artifact) -> str` |  | Method. |
| `load` | `def load(self, name: str, *, version: str = '') -> Artifact &#124; None` |  | Method. |
| `load_by_digest` | `def load_by_digest(self, digest: str) -> Artifact &#124; None` |  | Method. |
| `list_artifacts` | `def list_artifacts(self, *, kind: str = '', tag_key: str = '', tag_value: str = '') -> list[Artifact]` |  | Method. |
| `delete` | `def delete(self, name: str, *, version: str = '') -> int` |  | Method. |
| `exists` | `def exists(self, name: str, *, version: str = '') -> bool` |  | Method. |
| `gc` | `def gc(self, referenced: set[str]) -> int` |  | Remove artifacts whose digest is not in *referenced*. |
| `clear` | `def clear(self) -> None` |  | Method. |
| `count` | `def count(self, *, kind: str = '') -> int` |  | Count artifacts, optionally filtered by kind. |

### Class: `FilesystemArtifactStore`

- Source: `aquilia/artifacts/store.py`
- Bases: `ArtifactStoreProtocol`
- Summary: Persistent filesystem artifact store.

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `save` | `def save(self, artifact: Artifact) -> str` |  | Method. |
| `load` | `def load(self, name: str, *, version: str = '') -> Artifact &#124; None` |  | Method. |
| `load_by_digest` | `def load_by_digest(self, digest: str) -> Artifact &#124; None` |  | Method. |
| `list_artifacts` | `def list_artifacts(self, *, kind: str = '', tag_key: str = '', tag_value: str = '') -> list[Artifact]` |  | Method. |
| `delete` | `def delete(self, name: str, *, version: str = '') -> int` |  | Method. |
| `exists` | `def exists(self, name: str, *, version: str = '') -> bool` |  | Method. |
| `gc` | `def gc(self, referenced: set[str]) -> int` |  | Remove artifacts whose digest is not in *referenced*. |
| `export_bundle` | `def export_bundle(self, names: list[str], output_path: str) -> str` |  | Export a subset of artifacts as a Crous binary bundle. |
| `count` | `def count(self, *, kind: str = '') -> int` |  | Count artifacts, optionally filtered by kind. |
| `import_bundle` | `def import_bundle(self, bundle_path: str) -> int` |  | Import artifacts from a bundle file produced by ``export_bundle``. |

## Functions

| Name | Source | Signature | Purpose |
| --- | --- | --- | --- |
| `register_artifact_kind` | `aquilia/artifacts/core.py` | `def register_artifact_kind(kind: str, cls: type[Artifact]) -> None` | Register a typed subclass so ``Artifact.from_dict`` auto-resolves. |
| `ArtifactStore` | `aquilia/artifacts/store.py` | `def ArtifactStore(root: str = 'artifacts') -> FilesystemArtifactStore` | Convenience constructor -- returns a :class:`FilesystemArtifactStore`. |

## Constants

| Name | Source | Value or type |
| --- | --- | --- |
| `_KIND_REGISTRY` | `aquilia/artifacts/core.py` | `dict[str, type[Artifact]]` |
