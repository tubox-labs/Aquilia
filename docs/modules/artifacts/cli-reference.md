# Artifacts CLI Reference

This page is derived from the mounted Click command tree. If a source file has CLI helper functions but they are not mounted under `aq`, this page states that explicitly.

## Relationship To The `aq` CLI

The following mounted commands map to this subsystem.

| Command | Syntax | Purpose |
| --- | --- | --- |
| `aq artifact list` | `aq artifact list [--dir VALUE] [--kind VALUE] [--tag VALUE] [--json-output]` | List all artifacts in the store. |
| `aq artifact inspect` | `aq artifact inspect NAME [--version VALUE] [--dir VALUE] [--json-output]` | Inspect an artifact by name. |
| `aq artifact verify` | `aq artifact verify NAME [--version VALUE] [--dir VALUE]` | Verify the integrity of an artifact. |
| `aq artifact verify-all` | `aq artifact verify-all [--dir VALUE] [--json-output]` | Verify integrity of ALL artifacts in the store. |
| `aq artifact gc` | `aq artifact gc [--dir VALUE] [--keep VALUE] [--dry-run]` | Garbage-collect unreferenced artifacts. |
| `aq artifact export` | `aq artifact export [--dir VALUE] [--output VALUE] [--name VALUE]` | Export artifacts as a bundle. |
| `aq artifact diff` | `aq artifact diff NAME VERSION_A VERSION_B [--dir VALUE]` | Show differences between two versions of an artifact. |
| `aq artifact history` | `aq artifact history NAME [--dir VALUE]` | Show version history of an artifact. |
| `aq artifact import` | `aq artifact import BUNDLE_PATH [--dir VALUE]` | Import artifacts from a bundle file. |
| `aq artifact count` | `aq artifact count [--dir VALUE] [--kind VALUE]` | Count artifacts in the store. |
| `aq artifact stats` | `aq artifact stats [--dir VALUE] [--json-output]` | Show aggregate statistics for the artifact store. |

## Detailed Commands

### `aq artifact list`

List all artifacts in the store.

```bash
aq artifact list [--dir VALUE] [--kind VALUE] [--tag VALUE] [--json-output]
```

| Kind | Name | Flags | Required | Default | Help |
| --- | --- | --- | --- | --- | --- |
| Option | `store_dir` | `--dir, -d` | False | `artifacts` | Artifact store directory |
| Option | `kind` | `--kind, -k` | False | `` | Filter by artifact kind |
| Option | `tag` | `--tag, -t` | False | `` | Filter by tag (key=value) |
| Option | `json_output` | `--json-output, -j` | False | `False` | Output as JSON |

### `aq artifact inspect`

Inspect an artifact by name.

```bash
aq artifact inspect NAME [--version VALUE] [--dir VALUE] [--json-output]
```

| Kind | Name | Flags | Required | Default | Help |
| --- | --- | --- | --- | --- | --- |
| Argument | `name` | `name` | True | `not set` |  |
| Option | `version` | `--version, -V` | False | `` | Artifact version |
| Option | `store_dir` | `--dir, -d` | False | `artifacts` | Artifact store directory |
| Option | `json_output` | `--json-output, -j` | False | `False` | Output as JSON |

### `aq artifact verify`

Verify the integrity of an artifact.

```bash
aq artifact verify NAME [--version VALUE] [--dir VALUE]
```

| Kind | Name | Flags | Required | Default | Help |
| --- | --- | --- | --- | --- | --- |
| Argument | `name` | `name` | True | `not set` |  |
| Option | `version` | `--version, -V` | False | `` | Artifact version |
| Option | `store_dir` | `--dir, -d` | False | `artifacts` | Artifact store directory |

### `aq artifact verify-all`

Verify integrity of ALL artifacts in the store.

```bash
aq artifact verify-all [--dir VALUE] [--json-output]
```

| Kind | Name | Flags | Required | Default | Help |
| --- | --- | --- | --- | --- | --- |
| Option | `store_dir` | `--dir, -d` | False | `artifacts` | Artifact store directory |
| Option | `json_output` | `--json-output, -j` | False | `False` | Output as JSON |

### `aq artifact gc`

Garbage-collect unreferenced artifacts.

```bash
aq artifact gc [--dir VALUE] [--keep VALUE] [--dry-run]
```

| Kind | Name | Flags | Required | Default | Help |
| --- | --- | --- | --- | --- | --- |
| Option | `store_dir` | `--dir, -d` | False | `artifacts` | Artifact store directory |
| Option | `keep` | `--keep, -k` | False | `not set` | Digests to keep (repeatable) |
| Option | `dry_run` | `--dry-run` | False | `False` | Show what would be removed |

### `aq artifact export`

Export artifacts as a bundle.

```bash
aq artifact export [--dir VALUE] [--output VALUE] [--name VALUE]
```

| Kind | Name | Flags | Required | Default | Help |
| --- | --- | --- | --- | --- | --- |
| Option | `store_dir` | `--dir, -d` | False | `artifacts` | Artifact store directory |
| Option | `output` | `--output, -o` | False | `bundle.aq.json` | Output bundle file |
| Option | `name` | `--name, -n` | False | `not set` | Artifact names to export (repeatable) |

### `aq artifact diff`

Show differences between two versions of an artifact.

```bash
aq artifact diff NAME VERSION_A VERSION_B [--dir VALUE]
```

| Kind | Name | Flags | Required | Default | Help |
| --- | --- | --- | --- | --- | --- |
| Argument | `name` | `name` | True | `not set` |  |
| Argument | `version_a` | `version_a` | True | `not set` |  |
| Argument | `version_b` | `version_b` | True | `not set` |  |
| Option | `store_dir` | `--dir, -d` | False | `artifacts` | Artifact store directory |

### `aq artifact history`

Show version history of an artifact.

```bash
aq artifact history NAME [--dir VALUE]
```

| Kind | Name | Flags | Required | Default | Help |
| --- | --- | --- | --- | --- | --- |
| Argument | `name` | `name` | True | `not set` |  |
| Option | `store_dir` | `--dir, -d` | False | `artifacts` | Artifact store directory |

### `aq artifact import`

Import artifacts from a bundle file.

```bash
aq artifact import BUNDLE_PATH [--dir VALUE]
```

| Kind | Name | Flags | Required | Default | Help |
| --- | --- | --- | --- | --- | --- |
| Argument | `bundle_path` | `bundle_path` | True | `not set` |  |
| Option | `store_dir` | `--dir, -d` | False | `artifacts` | Artifact store directory |

### `aq artifact count`

Count artifacts in the store.

```bash
aq artifact count [--dir VALUE] [--kind VALUE]
```

| Kind | Name | Flags | Required | Default | Help |
| --- | --- | --- | --- | --- | --- |
| Option | `store_dir` | `--dir, -d` | False | `artifacts` | Artifact store directory |
| Option | `kind` | `--kind, -k` | False | `` | Filter by artifact kind |

### `aq artifact stats`

Show aggregate statistics for the artifact store.

```bash
aq artifact stats [--dir VALUE] [--json-output]
```

| Kind | Name | Flags | Required | Default | Help |
| --- | --- | --- | --- | --- | --- |
| Option | `store_dir` | `--dir, -d` | False | `artifacts` | Artifact store directory |
| Option | `json_output` | `--json-output, -j` | False | `False` | Output as JSON |

## General Commands Useful For This Module

| Command | Why it matters |
| --- | --- |
| `aq validate` | Validates workspace manifests and catches invalid component paths. |
| `aq doctor` | Runs environment, workspace, manifest, registry, integration, and deployment diagnostics. |
| `aq inspect config` | Shows resolved config after workspace/env merging. |
| `aq inspect modules` | Lists discovered modules. |
| `aq inspect routes` | Shows compiled routes when the module contributes controllers. |
| `aq run` | Starts the dev server and executes startup wiring. |

## Error Behavior

- Click handles missing required arguments and invalid options before command callbacks run.
- Most operational commands require `workspace.py`; the root CLI guard allows help/version/init/doctor without it.
- Commands that touch external providers, databases, or files can fail with subsystem-specific faults or provider errors.
