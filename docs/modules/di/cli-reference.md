# Di CLI Reference

This page is derived from the mounted Click command tree. If a source file has CLI helper functions but they are not mounted under `aq`, this page states that explicitly.

## Relationship To The `aq` CLI

No mounted `aq <module>` command maps directly to this subsystem. That is source evidence, not an omission: the root Click tree does not expose a dedicated group for it.

## Module-Local CLI Helper Files

These helper functions exist in source but are not necessarily mounted by the root `aq` command.

| File | Public helper functions |
| --- | --- |
| `aquilia/di/cli.py` | `load_manifests_from_settings`, `cmd_di_check`, `cmd_di_tree`, `cmd_di_graph`, `cmd_di_profile`, `cmd_di_manifest`, `setup_di_commands` |

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
