# Migration Guide — Aquilia v1.3.6

Aquilia v1.3.6 brings the new **Artifact Subsystem**. For most standard web applications, this upgrade is entirely transparent. The framework handles the migration, recreation, and cleanup of generated artifacts automatically.

However, if you maintain CI/CD pipelines, Dockerfiles, or external tooling that interacts with Aquilia's artifact files, you will need to apply a few small changes.

---

## Upgrading

```bash
pip install aquilia==1.3.6
```

---

## Upgrade Checklist

1. `pip install aquilia==1.3.6`
2. **Update `.gitignore`**: Add `.aquilia/artifacts/` to your `.gitignore`.
3. **Delete old artifacts**: Run `rm -rf artifacts/` from your project root.
4. **Update CI/CD caches**: If your CI caches the `artifacts/` folder, update the path to `.aquilia/artifacts/`.
5. **Update Dockerfiles**: If you `COPY artifacts/ /app/artifacts/`, update it to `COPY .aquilia/artifacts/ /app/.aquilia/artifacts/`.
6. **Update external scripts**: If you have tools parsing `templates.json` or `ws.json`, update them to read from the new path and parse the `.payload` property of the new JSON envelope.

---

## Breaking Changes Summary

### 1. Default Artifact Path Changed
The default path for all artifacts is now `.aquilia/artifacts/`.
* `JSONBytecodeCache(cache_dir=None)` previously defaulted to `"artifacts"`.
* Template compilation commands output to `.aquilia/artifacts/templates.json`.
* WebSocket inspect commands read from `.aquilia/artifacts/ws.json`.

If your code explicitly provided `cache_dir="artifacts"`, that code will continue to work, but the files written inside it will use the new JSON format.

### 2. Artifact File Format Changed
All framework JSON artifacts are now wrapped in an `ArtifactEnvelope`.

**Old Format (e.g. `discovery_cache.json`):**
```json
{
  "modules": ["app.users", "app.billing"],
  "timestamp": 123456789
}
```

**New Format:**
```json
{
  "format": "aquilia-artifact",
  "artifact_type": "discovery_cache",
  "schema_version": "1.0",
  "key": "main",
  "fingerprint": "...",
  "created_at": "...",
  "payload": {
    "modules": ["app.users", "app.billing"]
  }
}
```

The framework automatically handles backward compatibility for reading legacy `discovery_cache.json`, `schema_snapshot.json`, and `mcp_knowledge_index.json`. Other caches (like bytecode) will be regenerated.

---

## Verification

After upgrading, boot your application or run your tests, then use the new CLI tool to verify the store:

```bash
aq artifacts status
```

You should see a table showing the newly generated artifacts in the `.aquilia/artifacts/` directory.

---

## Rollback Procedure

If you need to roll back to v1.3.5:
1. `pip install aquilia==1.3.5`
2. Delete the new directory: `rm -rf .aquilia/artifacts/`
3. Delete any legacy `artifacts/` directory just to be safe.
4. Reboot the application; v1.3.5 will regenerate the artifacts in the old format and old locations.
