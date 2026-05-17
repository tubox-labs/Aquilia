# Core CLI Reference

This page is derived from the mounted Click command tree. If a source file has CLI helper functions but they are not mounted under `aq`, this page states that explicitly.

## Relationship To The `aq` CLI

The following mounted commands map to this subsystem.

| Command | Syntax | Purpose |
| --- | --- | --- |
| `aq validate` | `aq validate [--strict] [--module VALUE] [--json]` | Validate workspace manifests. |
| `aq compile` | `aq compile [--watch] [--output VALUE]` | Compile manifests to artifacts. |
| `aq run` | `aq run [--mode VALUE] [--port VALUE] [--host VALUE] [--reload VALUE] [--skip-checks]` | Start development server. |
| `aq serve` | `aq serve [--workers VALUE] [--bind VALUE] [--use-gunicorn] [--timeout VALUE] [--graceful-timeout VALUE]` | Start production server. |
| `aq freeze` | `aq freeze [--output VALUE] [--sign]` | Freeze generated artifacts for production integrity checks. |
| `aq manifest update` | `aq manifest update MODULE [--check] [--freeze]` | Update manifest with auto-discovered resources. |
| `aq inspect routes` | `aq inspect routes` | Show compiled routes. |
| `aq inspect di` | `aq inspect di` | Show DI graph. |
| `aq inspect modules` | `aq inspect modules` | List all modules. |
| `aq inspect faults` | `aq inspect faults` | Show fault domains. |
| `aq inspect config` | `aq inspect config` | Show resolved configuration. |
| `aq doctor` | `aq doctor [--json]` | Diagnose workspace issues. |

## Detailed Commands

### `aq validate`

Validate workspace manifests.

```bash
aq validate [--strict] [--module VALUE] [--json]
```

| Kind | Name | Flags | Required | Default | Help |
| --- | --- | --- | --- | --- | --- |
| Option | `strict` | `--strict` | False | `False` | Strict validation (prod-level) |
| Option | `module` | `--module` | False | `not set` | Validate single module |
| Option | `as_json` | `--json` | False | `False` | Output results as JSON |

### `aq compile`

Compile manifests to artifacts.

```bash
aq compile [--watch] [--output VALUE]
```

| Kind | Name | Flags | Required | Default | Help |
| --- | --- | --- | --- | --- | --- |
| Option | `watch` | `--watch` | False | `False` | Watch for changes |
| Option | `output` | `--output` | False | `not set` | Output directory |

### `aq run`

Start development server.

```bash
aq run [--mode VALUE] [--port VALUE] [--host VALUE] [--reload VALUE] [--skip-checks]
```

| Kind | Name | Flags | Required | Default | Help |
| --- | --- | --- | --- | --- | --- |
| Option | `mode` | `--mode` | False | `dev` | Runtime mode |
| Option | `port` | `--port` | False | `` | Server port (default: from workspace.py AquilaConfig, or 8000) |
| Option | `host` | `--host` | False | `` | Server host (default: from workspace.py AquilaConfig, or 127.0.0.1) |
| Option | `reload` | `--reload, --no-reload` | False | `` | Enable hot-reload (default: from workspace.py AquilaConfig, or True) |
| Option | `skip_checks` | `--skip-checks` | False | `False` | Skip pre-flight dependency checks |

### `aq serve`

Start production server.

```bash
aq serve [--workers VALUE] [--bind VALUE] [--use-gunicorn] [--timeout VALUE] [--graceful-timeout VALUE]
```

| Kind | Name | Flags | Required | Default | Help |
| --- | --- | --- | --- | --- | --- |
| Option | `workers` | `--workers` | False | `` | Number of workers (default: from workspace.py AquilaConfig, or 1) |
| Option | `bind` | `--bind` | False | `` | Bind address (default: from workspace.py AquilaConfig, or 0.0.0.0:8000) |
| Option | `use_gunicorn` | `--use-gunicorn` | False | `False` | Use gunicorn with UvicornWorker (recommended for production) |
| Option | `timeout` | `--timeout` | False | `120` | Worker timeout in seconds (gunicorn only) |
| Option | `graceful_timeout` | `--graceful-timeout` | False | `30` | Graceful shutdown timeout (gunicorn only) |

### `aq freeze`

Freeze generated artifacts for production integrity checks.

```bash
aq freeze [--output VALUE] [--sign]
```

| Kind | Name | Flags | Required | Default | Help |
| --- | --- | --- | --- | --- | --- |
| Option | `output` | `--output` | False | `not set` | Output directory |
| Option | `sign` | `--sign` | False | `False` | Sign artifacts |

### `aq manifest update`

Update manifest with auto-discovered resources.

```bash
aq manifest update MODULE [--check] [--freeze]
```

| Kind | Name | Flags | Required | Default | Help |
| --- | --- | --- | --- | --- | --- |
| Argument | `module` | `module` | True | `not set` |  |
| Option | `check` | `--check` | False | `False` | Fail if manifest is out of sync (CI mode) |
| Option | `freeze` | `--freeze` | False | `False` | Disable auto-discovery after Sync (Strict mode) |

### `aq inspect routes`

Show compiled routes.

```bash
aq inspect routes
```

### `aq inspect di`

Show DI graph.

```bash
aq inspect di
```

### `aq inspect modules`

List all modules.

```bash
aq inspect modules
```

### `aq inspect faults`

Show fault domains.

```bash
aq inspect faults
```

### `aq inspect config`

Show resolved configuration.

```bash
aq inspect config
```

### `aq doctor`

Diagnose workspace issues.

```bash
aq doctor [--json]
```

| Kind | Name | Flags | Required | Default | Help |
| --- | --- | --- | --- | --- | --- |
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
