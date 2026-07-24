# CLI Updates: Deprecation Validation

Aquilia 1.3.4 introduces a new CLI tool designed to help developers identify and migrate away from legacy configuration patterns before the major 2.0 release.

## `aq validate --deprecated`

This command scans your entire workspace, parses all `AppManifest` declarations, and reports any usage of fields that have been marked for deprecation.

### Detected Fields
The validator currently flags the following legacy manifest fields:
- `route_prefix`: Replaced by router-level mounting.
- `database`: Replaced by the new Data Layer plugin system.
- `middlewares`: Moved to app-level configuration.
- `depends_on`: Replaced by the `imports` field.

### Usage Examples

Run the validation in your terminal:

```bash
$ aq validate --deprecated

⚠️ Deprecation warnings found in 2 manifests:

billing/manifest.py:
  - 'depends_on' is deprecated. Use 'imports' instead.

auth/manifest.py:
  - 'route_prefix' is deprecated. Mount the router in your entrypoint instead.
  - 'database' is deprecated. Use the Data Layer plugin.
```

### JSON Output for CI/CD
For continuous integration environments, you can output the validation results as JSON to enforce compliance in pull requests.

```bash
$ aq validate --deprecated --json

{
  "deprecated_count": 3,
  "manifests": {
    "billing": ["depends_on"],
    "auth": ["route_prefix", "database"]
  }
}
```

## Migration Paths

| Deprecated Field | Migration Path |
|------------------|----------------|
| `depends_on` | Rename the kwarg to `imports`. |
| `route_prefix` | Remove from manifest. Mount explicitly: `app.mount("/prefix", router)` |
| `middlewares` | Define middlewares in `config.py` rather than the manifest. |
| `database` | Initialize databases via standard dependency injection. |
