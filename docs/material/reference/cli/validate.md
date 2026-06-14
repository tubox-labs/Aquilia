# aq validate

Validate workspace manifests against the Aquilary pipeline. Performs static validation of module declarations, controller references, service references, dependency graphs, and optional strict-mode production checks.

## Usage

```bash
aq validate [OPTIONS]
```

## Options

| Option      | Description                                   | Default |
| ----------- | --------------------------------------------- | ------- |
| `--strict`  | Enable strict (production-level) validation   | `False` |
| `--module`  | Validate only a specific module               | `None`  |
| `--json`    | Output results as JSON                        | `False` |

## Validation Phases

### Phase 1 — Structure

- `workspace.py` existence
- Module directories present in `modules/`

### Phase 2 — Manifest

For each registered module:

- `manifest.py` exists and is loadable
- AppManifest instance found
- Required fields present (`name`, `version`)
- `__init__.py` present (warns if missing)
- Dependency names reference registered modules
- Controller and service file paths resolve to actual files

### Phase 3 — Aquilary Pipeline

- RegistryValidator validates manifest consistency
- DependencyGraph detects circular dependencies
- Topological sort verifies load order

### Phase 4 — Strict Mode (`--strict`)

Additional production checks:

- Recommended files present (`controllers.py`, `services.py`, `faults.py`)
- `route_prefix` configured
- Fault handling configured
- Registry fingerprint generated

## JSON Output

```json
{
  "valid": true,
  "modules": 3,
  "routes": 12,
  "providers": 5,
  "fingerprint": "sha256:a1b2c3d4e5f6...",
  "faults": [],
  "warnings": []
}
```

When `valid` is `false`, the CLI exits with code 1.

## Exit Codes

| Code | Meaning                 |
| ---- | ----------------------- |
| `0`  | Validation passed       |
| `1`  | Validation failed       |

## Examples

```bash
# Basic validation
aq validate

# Production-level strict validation
aq validate --strict

# Validate a single module
aq validate --module=users

# JSON output for CI/CD pipelines
aq validate --json

# Verbose with strict
aq validate --strict -v
```

## See Also

- [`aq doctor`](index.md) — Comprehensive workspace diagnostics
- [`aq inspect`](inspect.md) — Inspect routes, DI graph, modules
- [`aq compile`](compile.md) — Compile manifests to artifacts