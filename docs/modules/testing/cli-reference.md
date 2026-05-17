# Testing CLI Reference

This page is derived from the mounted Click command tree. If a source file has CLI helper functions but they are not mounted under `aq`, this page states that explicitly.

## Relationship To The `aq` CLI

The following mounted commands map to this subsystem.

| Command | Syntax | Purpose |
| --- | --- | --- |
| `aq test` | `aq test [PATHS] [-k VALUE] [-m VALUE] [--coverage] [--coverage-html] [--failfast]` | Run the test suite with Aquilia-aware defaults. |

## Detailed Commands

### `aq test`

Run the test suite with Aquilia-aware defaults.

```bash
aq test [PATHS] [-k VALUE] [-m VALUE] [--coverage] [--coverage-html] [--failfast]
```

| Kind | Name | Flags | Required | Default | Help |
| --- | --- | --- | --- | --- | --- |
| Argument | `paths` | `paths` | False | `not set` |  |
| Option | `pattern` | `-k, --pattern` | False | `` | Only run tests matching pattern |
| Option | `markers` | `-m, --markers` | False | `` | Only run tests matching markers |
| Option | `coverage` | `--coverage` | False | `False` | Collect coverage |
| Option | `coverage_html` | `--coverage-html` | False | `False` | Generate HTML coverage report |
| Option | `failfast` | `--failfast, -x` | False | `False` | Stop on first failure |

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
