<!-- Legacy mirror. Canonical page: ../modules/i18n/cli-reference.md -->

# I18N CLI Reference

This page is derived from the mounted Click command tree. If a source file has CLI helper functions but they are not mounted under `aq`, this page states that explicitly.

## Relationship To The `aq` CLI

The following mounted commands map to this subsystem.

| Command | Syntax | Purpose |
| --- | --- | --- |
| `aq i18n init` | `aq i18n init [--locales VALUE] [--directory VALUE] [--format VALUE]` | Initialize i18n in the current workspace. |
| `aq i18n check` | `aq i18n check` | Validate i18n configuration and catalog structure. |
| `aq i18n inspect` | `aq i18n inspect` | Display current i18n configuration as JSON. |
| `aq i18n extract` | `aq i18n extract [--source-dirs VALUE] [--output VALUE] [--no-merge]` | Extract translation keys from source files. |
| `aq i18n coverage` | `aq i18n coverage` | Show translation coverage per locale. |
| `aq i18n compile` | `aq i18n compile [--directory VALUE] [--output VALUE]` | Compile JSON locale files to SURP format. |

## Detailed Commands

### `aq i18n init`

Initialize i18n in the current workspace.

```bash
aq i18n init [--locales VALUE] [--directory VALUE] [--format VALUE]
```

| Kind | Name | Flags | Required | Default | Help |
| --- | --- | --- | --- | --- | --- |
| Option | `locales` | `--locales, -l` | False | `en` | Comma-separated locale list (e.g. en,fr,de) |
| Option | `directory` | `--directory, -d` | False | `locales` | Base directory for locale files |
| Option | `format` | `--format, -f` | False | `json` | Translation file format |

### `aq i18n check`

Validate i18n configuration and catalog structure.

```bash
aq i18n check
```

### `aq i18n inspect`

Display current i18n configuration as JSON.

```bash
aq i18n inspect
```

### `aq i18n extract`

Extract translation keys from source files.

```bash
aq i18n extract [--source-dirs VALUE] [--output VALUE] [--no-merge]
```

| Kind | Name | Flags | Required | Default | Help |
| --- | --- | --- | --- | --- | --- |
| Option | `source_dirs` | `--source-dirs, -s` | False | `modules,controllers` | Comma-separated source directories |
| Option | `output` | `--output, -o` | False | `locales/en/messages.json` | Output file path |
| Option | `no_merge` | `--no-merge` | False | `False` | Overwrite output instead of merging |

### `aq i18n coverage`

Show translation coverage per locale.

```bash
aq i18n coverage
```

### `aq i18n compile`

Compile JSON locale files to SURP format.

```bash
aq i18n compile [--directory VALUE] [--output VALUE]
```

| Kind | Name | Flags | Required | Default | Help |
| --- | --- | --- | --- | --- | --- |
| Option | `directory` | `--directory` | False | `locales` | Source locales directory |
| Option | `output` | `--output` | False | `` | Output directory for compiled catalogs |

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
