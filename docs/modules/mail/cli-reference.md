# Mail CLI Reference

This page is derived from the mounted Click command tree. If a source file has CLI helper functions but they are not mounted under `aq`, this page states that explicitly.

## Relationship To The `aq` CLI

The following mounted commands map to this subsystem.

| Command | Syntax | Purpose |
| --- | --- | --- |
| `aq mail check` | `aq mail check` | Validate mail configuration and report issues. |
| `aq mail send-test` | `aq mail send-test TO [--subject VALUE] [--body VALUE]` | Send a test email to verify mail provider configuration. |
| `aq mail inspect` | `aq mail inspect` | Display current mail configuration as JSON. |

## Detailed Commands

### `aq mail check`

Validate mail configuration and report issues.

```bash
aq mail check
```

### `aq mail send-test`

Send a test email to verify mail provider configuration.

```bash
aq mail send-test TO [--subject VALUE] [--body VALUE]
```

| Kind | Name | Flags | Required | Default | Help |
| --- | --- | --- | --- | --- | --- |
| Argument | `to` | `to` | True | `not set` |  |
| Option | `subject` | `--subject` | False | `` | Email subject |
| Option | `body` | `--body` | False | `` | Email body |

### `aq mail inspect`

Display current mail configuration as JSON.

```bash
aq mail inspect
```

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
