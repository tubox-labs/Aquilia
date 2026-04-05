# I18n CLI Reference

This document covers i18n CLI behavior implemented in:

- `aquilia/cli/__main__.py`
- `aquilia/cli/commands/i18n.py`

## Command Group

Top-level group:

```bash
aq i18n
```

Currently registered subcommands in CLI entrypoint:

- `init`
- `check`
- `inspect`
- `extract`
- `coverage`
- `compile`

## `aq i18n init`

Purpose:

- bootstrap locale directory structure
- create starter translation files

CLI options (entrypoint):

- `--locales, -l` (comma-separated locales)
- `--directory, -d` (base directory)
- `--format, -f` (`json` or `yaml` in entrypoint validation)

Implementation details (`cmd_i18n_init`):

- supports `json`, `yaml`, and `crous` paths internally
- creates `<directory>/<locale>/messages.<ext>`
- skips existing files
- writes locale-specific starter keys when known (`en`, `fr`, `de`, `es`, `ja`)
- falls back to minimal starter strings for unknown locales

Examples:

```bash
aq i18n init --locales en,fr,de --directory locales --format json
aq i18n init --locales en --directory translations --format yaml
```

## `aq i18n check`

Purpose:

- validate effective i18n config and catalog directory presence

Behavior:

- loads config via workspace object (if available) or ConfigLoader
- prints enabled/default/fallback/resolver details
- enumerates locale subdirectories and files
- warns when catalog dirs are missing

## `aq i18n inspect`

Purpose:

- print effective i18n config as JSON

Behavior:

- emits `json.dumps(config, indent=2, ensure_ascii=False)`

## `aq i18n extract`

Purpose:

- scan source and templates for translation keys
- write dotted-key skeleton to output JSON

Options:

- `--source-dirs, -s` (default: `modules,controllers`)
- `--output, -o` (default: `locales/en/messages.json`)
- `--no-merge` (overwrite mode)

Detection patterns:

Python pattern includes:

- `_`, `gettext`
- `i18n.t`, `i18n.tn`, `i18n.tp`
- `lazy_t`, `lazy_tn`

Template pattern includes:

- `_`, `_n`, `_p`, `gettext`, `ngettext`

Output behavior:

- dotted keys are expanded to nested JSON objects
- new leaves are created with empty string values
- optional merge mode preserves existing values

## `aq i18n coverage`

Purpose:

- compute per-locale translation coverage against default locale key set

Behavior:

- collects default-locale keys from JSON files only
- compares key intersections for each configured locale
- prints percentage and key counts
- with verbose mode, prints up to first 10 missing keys per locale

## `aq i18n compile`

Purpose:

- compile JSON catalogs to CROUS format for faster startup and lookup

Options:

- `--directory, -d` source locales directory (default `locales`)
- `--output, -o` optional output directory for compiled artifacts

Behavior:

- invokes `cmd_i18n_compile`
- compiles discovered JSON catalogs to `.crous`
- preserves source layout per locale/namespace

Examples:

```bash
aq i18n compile
aq i18n compile --directory locales
aq i18n compile --directory locales --output artifacts/locales
```

## Config Load Source for CLI Commands

`_load_i18n_config()` uses:

1. `workspace.py` exported `workspace` object when present
2. fallback to `ConfigLoader().get_i18n_config()`

This means command output reflects workspace-level integration config when available.

## Workspace Generator Scaffolding

`aq init workspace` generation path (`aquilia/cli/generators/workspace.py`) also creates starter i18n content:

- `locales/en/messages.json`

This makes newly generated workspaces i18n-ready before explicit `aq i18n init` usage.

## Practical Workflows

Initialize and inspect:

```bash
aq i18n init --locales en,fr
aq i18n inspect
```

Extract and fill:

```bash
aq i18n extract --source-dirs modules,templates --output locales/en/messages.json
# then fill empty values and create sibling locale files
```

Coverage check:

```bash
aq i18n coverage
aq i18n coverage --verbose
```

Compile catalogs:

```bash
aq i18n compile --directory locales
```
