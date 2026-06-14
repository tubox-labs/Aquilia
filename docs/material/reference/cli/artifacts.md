# aq artifacts

Manage Aquilia artifacts: list, inspect, verify integrity, export/import bundles, diff versions, garbage-collect unreferenced artifacts, and view statistics.

## Usage

```bash
aq artifact <SUBCOMMAND> [OPTIONS]
```

## Subcommands

### aq artifact list

List all artifacts in the store.

```bash
aq artifact list [OPTIONS]
```

| Option     | Alias | Description                          | Default     |
| ---------- | ----- | ------------------------------------ | ----------- |
| `--dir`    | `-d`  | Artifact store directory             | `artifacts` |
| `--kind`   | `-k`  | Filter by artifact kind              | `""`        |
| `--tag`    | `-t`  | Filter by tag (`key=value`)          | `""`        |
| `--json`   | `-j`  | Output as JSON                       | `False`     |

Table output columns: Name, Version, Kind, Digest, Created.

```bash
aq artifact list
aq artifact list --kind model
aq artifact list -d ./artifacts -t env=production
aq artifact list --json
```

### aq artifact inspect

Inspect an artifact by name.

```bash
aq artifact inspect <NAME> [OPTIONS]
```

| Option      | Alias | Description              | Default     |
| ----------- | ----- | ------------------------ | ----------- |
| `--version` | `-V`  | Artifact version         | latest      |
| `--dir`     | `-d`  | Artifact store directory | `artifacts` |
| `--json`    | `-j`  | Output as JSON           | `False`     |

```bash
aq artifact inspect my-config
aq artifact inspect my-model --version v1.0.0
aq artifact inspect my-model -j
```

### aq artifact verify

Verify the integrity of a single artifact.

```bash
aq artifact verify <NAME> [OPTIONS]
```

```bash
aq artifact verify my-config
aq artifact verify my-model --version v1.0.0
```

### aq artifact verify-all

Verify integrity of **all** artifacts in the store.

```bash
aq artifact verify-all [OPTIONS]
```

| Option     | Alias | Description              | Default     |
| ---------- | ----- | ------------------------ | ----------- |
| `--dir`    | `-d`  | Artifact store directory | `artifacts` |
| `--json`   | `-j`  | Output as JSON           | `False`     |

```bash
aq artifact verify-all
aq artifact verify-all -j
```

### aq artifact diff

Show differences between two versions of an artifact.

```bash
aq artifact diff <NAME> <VERSION_A> <VERSION_B> [OPTIONS]
```

```bash
aq artifact diff my-config 1.0.0 1.1.0
```

### aq artifact history

Show version history of an artifact.

```bash
aq artifact history <NAME> [OPTIONS]
```

```bash
aq artifact history my-config
```

### aq artifact export

Export artifacts as a bundle file.

```bash
aq artifact export [OPTIONS]
```

| Option     | Alias | Description                                    | Default          |
| ---------- | ----- | ---------------------------------------------- | ---------------- |
| `--dir`    | `-d`  | Artifact store directory                       | `artifacts`      |
| `--output` | `-o`  | Output bundle file                             | `bundle.aq.json` |
| `--name`   | `-n`  | Artifact names to export (repeatable)          | all              |

```bash
aq artifact export --name my-config --name my-model -o release.aq.json
aq artifact export
```

### aq artifact import

Import artifacts from a bundle file.

```bash
aq artifact import <BUNDLE_PATH> [OPTIONS]
```

```bash
aq artifact import release.aq.json
aq artifact import ./backup/bundle.aq.json -d ./artifacts
```

### aq artifact gc

Garbage-collect unreferenced artifacts.

```bash
aq artifact gc [OPTIONS]
```

| Option      | Description                               | Default     |
| ----------- | ----------------------------------------- | ----------- |
| `--dir`     | `-d` Artifact store directory              | `artifacts` |
| `--keep`    | `-k` Digests to keep (repeatable)          | `()`        |
| `--dry-run` | Show what would be removed                | `False`     |

```bash
aq artifact gc
aq artifact gc --keep sha256:abc123 --keep sha256:def456
aq artifact gc --dry-run
```

### aq artifact count

Count artifacts in the store.

```bash
aq artifact count [OPTIONS]
```

```bash
aq artifact count
aq artifact count --kind model
```

### aq artifact stats

Show aggregate statistics for the artifact store.

```bash
aq artifact stats [OPTIONS]
```

Reports: total count, unique names, total size, oldest/newest artifacts, breakdown by kind.

```bash
aq artifact stats
aq artifact stats -j
```

## Examples

```bash
# List all artifacts
aq artifact list

# Inspect and verify
aq artifact inspect my-config
aq artifact verify my-config

# Verify everything
aq artifact verify-all

# Compare versions
aq artifact diff my-config 1.0.0 1.1.0

# View history
aq artifact history my-config

# Export for deployment
aq artifact export -o release.aq.json

# Import on target
aq artifact import release.aq.json

# Clean up
aq artifact gc --dry-run
aq artifact gc
```

## See Also

- [`aq compile`](compile.md) — Generate artifacts
- [`aq freeze`](freeze.md) — Freeze artifacts for production