# Unified Artifact Directory

A critical path fix in Aquilia v1.3.6 is the consolidation of all framework-generated files into a single, predictable location.

## Before

In previous versions, artifacts were scattered, usually landing in an `artifacts/` folder created at the current working directory, or sometimes in the project root directly:

- `artifacts/templates.bytecode.json`
- `artifacts/ws.json`
- `artifacts/templates.json`

This polluted the project root, often conflicted with user folders named "artifacts", and lacked a standardized structure.

## After

**ALL** framework artifacts now live under a unified hidden directory: `.aquilia/artifacts/`.

This change is driven by `resolve_artifact_root()`, which locates the project root and appends `.aquilia/artifacts`.

### Directory Layout

```text
<project_root>/
└── .aquilia/
    └── artifacts/
        ├── discovery_cache.json          # auto-discovery engine cache
        ├── schema_snapshot.json          # ORM schema snapshot for migrations
        ├── templates.bytecode.json       # compiled Jinja2 bytecode (HMAC-signed)
        ├── templates.json                # template manifest / inventory
        ├── ws.json                       # WebSocket controller metadata
        ├── mcp_knowledge_index.json      # MCP context knowledge index
        ├── di_manifest.json              # DI provider graph
        └── route_index.json              # compiled route index
```

## Breaking Changes & Path Adjustments

Because the default path changed, any tooling or manual scripts that expected files in `artifacts/` will need to be updated.

- `JSONBytecodeCache.__init__(cache_dir: str | None = None)`: Default changed from `"artifacts"` to `None` (which dynamically resolves to `.aquilia/artifacts`).
- `create_template_engine_from_config(cache_dir: str | None = None)`: Default changed to `None`.
- `TemplateManager.compile_all(output_path=None)`: Default changed from `"artifacts/templates.json"` to `.aquilia/artifacts/templates.json`.
- `cmd_compile(output=None)`: Resolves via `resolve_artifact_root() / "templates.json"`.
- `cmd_clear_cache(cache_dir=None)`: Resolves via `resolve_artifact_root()`.
- `aq ws inspect --artifacts-dir`: Default changed from `"artifacts"` to `None`.
- `aq ws gen-client --artifacts-dir`: Default changed from `"artifacts"` to `None`.

**Backward Compatibility:** If your code explicitly passes `cache_dir="artifacts"`, the framework will respect it and continue to use the old directory. 

## Migration Steps

1. **Update `.gitignore`**: You should ignore the new directory.
   ```bash
   echo '.aquilia/artifacts/' >> .gitignore
   ```

2. **Clean up old artifacts**: You can safely delete the old scattered files.
   ```bash
   rm -rf artifacts/
   ```
   The framework will automatically regenerate everything inside `.aquilia/artifacts/` on the next run.

3. **Verify**: Run the new CLI command to ensure things are working:
   ```bash
   aq artifacts status
   ```

## Custom Configuration

If you deploy to a read-only filesystem and need to direct artifacts to a writable volume (like `/tmp` or `/var/lib/`), you can override the root path globally:

```toml
# pyproject.toml or aquilia.toml
[aquilia.artifacts]
root = "/var/lib/myapp/artifacts"
```

Or via environment variable (useful for Docker containers):
```bash
export AQUILIA_ARTIFACT_ROOT=/var/lib/myapp/artifacts
```
