# Discovery CLI Reference

This page is derived from the mounted Click command tree. If a source file has CLI helper functions but they are not mounted under `aq`, this page states that explicitly.

## Relationship To The `aq` CLI

The following mounted commands map to this subsystem.

| Command | Syntax | Purpose |
| --- | --- | --- |
| `aq discover` | `aq discover [--path VALUE] [--sync] [--dry-run] [--json]` | Inspect auto-discovered modules in workspace. |

## Detailed Commands

### `aq discover`

Inspect auto-discovered modules in workspace.

```bash
aq discover [--path VALUE] [--sync] [--dry-run] [--json]
```

| Kind | Name | Flags | Required | Default | Help |
| --- | --- | --- | --- | --- | --- |
| Option | `path` | `--path` | False | `` | Workspace path |
| Option | `sync` | `--sync` | False | `False` | Auto-sync discovered components into manifest.py files |
| Option | `dry_run` | `--dry-run` | False | `False` | Preview sync changes without writing (use with --sync) |
| Option | `as_json` | `--json` | False | `False` | Output results as JSON |

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
