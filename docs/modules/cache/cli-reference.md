# Cache CLI Reference

This page is derived from the mounted Click command tree. If a source file has CLI helper functions but they are not mounted under `aq`, this page states that explicitly.

## Relationship To The `aq` CLI

The following mounted commands map to this subsystem.

| Command | Syntax | Purpose |
| --- | --- | --- |
| `aq cache check` | `aq cache check` | Validate cache configuration and test backend connectivity. |
| `aq cache inspect` | `aq cache inspect` | Display current cache configuration as JSON. |
| `aq cache stats` | `aq cache stats` | Display cache statistics from trace diagnostics. |
| `aq cache clear` | `aq cache clear [--namespace VALUE]` | Clear all or namespace-scoped cache entries. |

## Detailed Commands

### `aq cache check`

Validate cache configuration and test backend connectivity.

```bash
aq cache check
```

### `aq cache inspect`

Display current cache configuration as JSON.

```bash
aq cache inspect
```

### `aq cache stats`

Display cache statistics from trace diagnostics.

```bash
aq cache stats
```

### `aq cache clear`

Clear all or namespace-scoped cache entries.

```bash
aq cache clear [--namespace VALUE]
```

| Kind | Name | Flags | Required | Default | Help |
| --- | --- | --- | --- | --- | --- |
| Option | `namespace` | `--namespace, -n` | False | `` | Clear only this namespace |

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
