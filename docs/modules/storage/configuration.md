# Storage Configuration

## Configuration Entry Points

The implementation exposes the following configuration-like classes, policies, integrations, or dataclasses.

| Type | Source | Fields | Purpose |
| --- | --- | --- | --- |
| `StorageMetadata` | `aquilia/storage/base.py` | name: str, size: int, content_type: str, etag: str, last_modified: datetime &#124; None, created_at: datetime &#124; None, metadata: dict[str, str], storage_class: str | Immutable metadata for a stored file. |
| `StorageConfig` | `aquilia/storage/configs.py` | alias: str, backend: str, default: bool | Base storage configuration. |
| `LocalConfig` | `aquilia/storage/configs.py` | backend: str, root: str, base_url: str, permissions: int, dir_permissions: int, create_dirs: bool | Configuration for the local filesystem storage backend. |
| `MemoryConfig` | `aquilia/storage/configs.py` | backend: str, max_size: int | Configuration for the in-memory storage backend (testing). |
| `S3Config` | `aquilia/storage/configs.py` | backend: str, bucket: str, region: str, access_key: str &#124; None, secret_key: str &#124; None, session_token: str &#124; None, endpoint_url: str &#124; None, prefix: str, signature_version: str, use_ssl: bool, addressing_style: str, default_acl: str &#124; None, ... | Configuration for Amazon S3 or S3-compatible storage. |
| `GCSConfig` | `aquilia/storage/configs.py` | backend: str, bucket: str, project: str &#124; None, credentials_path: str &#124; None, credentials_json: str &#124; None, prefix: str, default_acl: str &#124; None, location: str, presigned_expiry: int | Configuration for Google Cloud Storage. |
| `AzureBlobConfig` | `aquilia/storage/configs.py` | backend: str, container: str, connection_string: str &#124; None, account_name: str &#124; None, account_key: str &#124; None, sas_token: str &#124; None, prefix: str, custom_domain: str &#124; None, presigned_expiry: int, overwrite: bool | Configuration for Azure Blob Storage. |
| `SFTPConfig` | `aquilia/storage/configs.py` | backend: str, host: str, port: int, username: str, password: str &#124; None, key_path: str &#124; None, key_passphrase: str &#124; None, root: str, known_hosts: str &#124; None, base_url: str, timeout: int | Configuration for SFTP/SSH storage. |
| `CompositeConfig` | `aquilia/storage/configs.py` | backend: str, backends: dict[str, dict[str, Any]], rules: dict[str, str], fallback: str | Configuration for the composite (multi-backend) storage. |

## Common Entry Points

- `StorageIntegration`
- `StorageConfig`
- `LocalConfig`
- `S3Config`
- `GCSConfig`
- `AzureBlobConfig`
- `SFTPConfig`

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
