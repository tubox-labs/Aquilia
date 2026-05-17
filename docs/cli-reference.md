# Aquilia CLI Reference

This is the complete mounted `aq` command tree generated from `aquilia.cli.__main__.cli`.

## Root Options

| Option | Purpose |
| --- | --- |
| `--version` | Show the version and exit. |
| `--verbose, -v` | Verbose output (show debug details, full tracebacks) |
| `--quiet, -q` | Minimal output (suppress banners & decorations) |
| `--debug` | Enable debug mode (full stack traces on errors) |
| `--no-color` | Disable coloured output |

## Commands

### `aq init workspace`

Create a new Aquilia workspace.

```bash
aq init workspace [--minimal] [--template VALUE] [--yes] [NAME]
```

| Kind | Name | Flags | Required | Default |
| --- | --- | --- | --- | --- |
| Argument | `name` | `name` | False | `` |
| Option | `minimal` | `--minimal` | False | `False` |
| Option | `template` | `--template` | False | `not set` |
| Option | `yes` | `--yes, -y` | False | `False` |

### `aq add module`

Add a new module to the workspace.

```bash
aq add module [--depends-on VALUE] [--fault-domain VALUE] [--route-prefix VALUE] [--with-tests] [--minimal] [--no-docker] [--yes] [NAME]
```

| Kind | Name | Flags | Required | Default |
| --- | --- | --- | --- | --- |
| Argument | `name` | `name` | False | `` |
| Option | `depends_on` | `--depends-on` | False | `not set` |
| Option | `fault_domain` | `--fault-domain` | False | `not set` |
| Option | `route_prefix` | `--route-prefix` | False | `not set` |
| Option | `with_tests` | `--with-tests` | False | `False` |
| Option | `minimal` | `--minimal` | False | `False` |
| Option | `no_docker` | `--no-docker` | False | `False` |
| Option | `yes` | `--yes, -y` | False | `False` |

### `aq generate controller`

Generate a new controller.

```bash
aq generate controller [--prefix VALUE] [--resource VALUE] [--simple] [--with-lifecycle] [--test] [--output VALUE] NAME
```

| Kind | Name | Flags | Required | Default |
| --- | --- | --- | --- | --- |
| Argument | `name` | `name` | True | `not set` |
| Option | `prefix` | `--prefix` | False | `not set` |
| Option | `resource` | `--resource` | False | `not set` |
| Option | `simple` | `--simple` | False | `False` |
| Option | `with_lifecycle` | `--with-lifecycle` | False | `False` |
| Option | `test` | `--test` | False | `False` |
| Option | `output` | `--output` | False | `not set` |

### `aq validate`

Validate workspace manifests.

```bash
aq validate [--strict] [--module VALUE] [--json]
```

| Kind | Name | Flags | Required | Default |
| --- | --- | --- | --- | --- |
| Option | `strict` | `--strict` | False | `False` |
| Option | `module` | `--module` | False | `not set` |
| Option | `as_json` | `--json` | False | `False` |

### `aq compile`

Compile manifests to artifacts.

```bash
aq compile [--watch] [--output VALUE]
```

| Kind | Name | Flags | Required | Default |
| --- | --- | --- | --- | --- |
| Option | `watch` | `--watch` | False | `False` |
| Option | `output` | `--output` | False | `not set` |

### `aq run`

Start development server.

```bash
aq run [--mode VALUE] [--port VALUE] [--host VALUE] [--reload VALUE] [--skip-checks]
```

| Kind | Name | Flags | Required | Default |
| --- | --- | --- | --- | --- |
| Option | `mode` | `--mode` | False | `dev` |
| Option | `port` | `--port` | False | `` |
| Option | `host` | `--host` | False | `` |
| Option | `reload` | `--reload, --no-reload` | False | `` |
| Option | `skip_checks` | `--skip-checks` | False | `False` |

### `aq serve`

Start production server.

```bash
aq serve [--workers VALUE] [--bind VALUE] [--use-gunicorn] [--timeout VALUE] [--graceful-timeout VALUE]
```

| Kind | Name | Flags | Required | Default |
| --- | --- | --- | --- | --- |
| Option | `workers` | `--workers` | False | `` |
| Option | `bind` | `--bind` | False | `` |
| Option | `use_gunicorn` | `--use-gunicorn` | False | `False` |
| Option | `timeout` | `--timeout` | False | `120` |
| Option | `graceful_timeout` | `--graceful-timeout` | False | `30` |

### `aq freeze`

Freeze generated artifacts for production integrity checks.

```bash
aq freeze [--output VALUE] [--sign]
```

| Kind | Name | Flags | Required | Default |
| --- | --- | --- | --- | --- |
| Option | `output` | `--output` | False | `not set` |
| Option | `sign` | `--sign` | False | `False` |

### `aq manifest update`

Update manifest with auto-discovered resources.

```bash
aq manifest update [--check] [--freeze] MODULE
```

| Kind | Name | Flags | Required | Default |
| --- | --- | --- | --- | --- |
| Argument | `module` | `module` | True | `not set` |
| Option | `check` | `--check` | False | `False` |
| Option | `freeze` | `--freeze` | False | `False` |

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

### `aq migrate`

Migrate from legacy layout.

```bash
aq migrate [--dry-run] SOURCE
```

| Kind | Name | Flags | Required | Default |
| --- | --- | --- | --- | --- |
| Argument | `source` | `source` | True | `not set` |
| Option | `dry_run` | `--dry-run` | False | `False` |

### `aq doctor`

Diagnose workspace issues.

```bash
aq doctor [--json]
```

| Kind | Name | Flags | Required | Default |
| --- | --- | --- | --- | --- |
| Option | `as_json` | `--json` | False | `False` |

### `aq ws inspect`

Inspect compiled WebSocket namespaces.

```bash
aq ws inspect [--artifacts-dir VALUE]
```

| Kind | Name | Flags | Required | Default |
| --- | --- | --- | --- | --- |
| Option | `artifacts_dir` | `--artifacts-dir` | False | `artifacts` |

### `aq ws broadcast`

Broadcast message to namespace or room.

```bash
aq ws broadcast [--namespace VALUE] [--room VALUE] [--event VALUE] [--payload VALUE]
```

| Kind | Name | Flags | Required | Default |
| --- | --- | --- | --- | --- |
| Option | `namespace` | `--namespace` | True | `not set` |
| Option | `room` | `--room` | False | `` |
| Option | `event` | `--event` | True | `not set` |
| Option | `payload` | `--payload` | False | `{}` |

### `aq ws gen-client`

Generate TypeScript client SDK from compiled WebSocket artifacts.

```bash
aq ws gen-client [--lang VALUE] [--out VALUE] [--artifacts-dir VALUE]
```

| Kind | Name | Flags | Required | Default |
| --- | --- | --- | --- | --- |
| Option | `lang` | `--lang` | False | `ts` |
| Option | `out` | `--out` | True | `not set` |
| Option | `artifacts_dir` | `--artifacts-dir` | False | `artifacts` |

### `aq ws purge-room`

Purge a room's state from the adapter.

```bash
aq ws purge-room [--namespace VALUE] [--room VALUE] [--redis-url VALUE]
```

| Kind | Name | Flags | Required | Default |
| --- | --- | --- | --- | --- |
| Option | `namespace` | `--namespace` | True | `not set` |
| Option | `room` | `--room` | True | `not set` |
| Option | `redis_url` | `--redis-url` | False | `` |

### `aq ws kick`

Kick (disconnect) a WebSocket connection.

```bash
aq ws kick [--conn VALUE] [--reason VALUE] [--redis-url VALUE]
```

| Kind | Name | Flags | Required | Default |
| --- | --- | --- | --- | --- |
| Option | `conn` | `--conn` | True | `not set` |
| Option | `reason` | `--reason` | False | `kicked by admin` |
| Option | `redis_url` | `--redis-url` | False | `` |

### `aq discover`

Inspect auto-discovered modules in workspace.

```bash
aq discover [--path VALUE] [--sync] [--dry-run] [--json]
```

| Kind | Name | Flags | Required | Default |
| --- | --- | --- | --- | --- |
| Option | `path` | `--path` | False | `` |
| Option | `sync` | `--sync` | False | `False` |
| Option | `dry_run` | `--dry-run` | False | `False` |
| Option | `as_json` | `--json` | False | `False` |

### `aq analytics`

Run discovery analytics and show health report.

```bash
aq analytics [--path VALUE]
```

| Kind | Name | Flags | Required | Default |
| --- | --- | --- | --- | --- |
| Option | `path` | `--path` | False | `` |

### `aq mail check`

Validate mail configuration and report issues.

```bash
aq mail check
```

### `aq mail send-test`

Send a test email to verify mail provider configuration.

```bash
aq mail send-test [--subject VALUE] [--body VALUE] TO
```

| Kind | Name | Flags | Required | Default |
| --- | --- | --- | --- | --- |
| Argument | `to` | `to` | True | `not set` |
| Option | `subject` | `--subject` | False | `` |
| Option | `body` | `--body` | False | `` |

### `aq mail inspect`

Display current mail configuration as JSON.

```bash
aq mail inspect
```

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

| Kind | Name | Flags | Required | Default |
| --- | --- | --- | --- | --- |
| Option | `namespace` | `--namespace, -n` | False | `` |

### `aq i18n init`

Initialize i18n in the current workspace.

```bash
aq i18n init [--locales VALUE] [--directory VALUE] [--format VALUE]
```

| Kind | Name | Flags | Required | Default |
| --- | --- | --- | --- | --- |
| Option | `locales` | `--locales, -l` | False | `en` |
| Option | `directory` | `--directory, -d` | False | `locales` |
| Option | `format` | `--format, -f` | False | `json` |

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

| Kind | Name | Flags | Required | Default |
| --- | --- | --- | --- | --- |
| Option | `source_dirs` | `--source-dirs, -s` | False | `modules,controllers` |
| Option | `output` | `--output, -o` | False | `locales/en/messages.json` |
| Option | `no_merge` | `--no-merge` | False | `False` |

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

| Kind | Name | Flags | Required | Default |
| --- | --- | --- | --- | --- |
| Option | `directory` | `--directory` | False | `locales` |
| Option | `output` | `--output` | False | `` |

### `aq db makemigrations`

Generate migration files from Python Model definitions.

```bash
aq db makemigrations [--app VALUE] [--migrations-dir VALUE] [--dsl VALUE] [--format VALUE]
```

| Kind | Name | Flags | Required | Default |
| --- | --- | --- | --- | --- |
| Option | `app` | `--app` | False | `` |
| Option | `migrations_dir` | `--migrations-dir` | False | `migrations` |
| Option | `dsl` | `--dsl, --no-dsl` | False | `True` |
| Option | `fmt` | `--format` | False | `surp` |

### `aq db migrate`

Apply pending migrations to the database.

```bash
aq db migrate [--migrations-dir VALUE] [--database-url VALUE] [--database VALUE] [--target VALUE] [--fake] [--plan]
```

| Kind | Name | Flags | Required | Default |
| --- | --- | --- | --- | --- |
| Option | `migrations_dir` | `--migrations-dir` | False | `migrations` |
| Option | `database_url` | `--database-url` | False | `` |
| Option | `database` | `--database` | False | `` |
| Option | `target` | `--target` | False | `` |
| Option | `fake` | `--fake` | False | `False` |
| Option | `plan` | `--plan` | False | `False` |

### `aq db dump`

Dump model schema -- annotated Python overview or raw SQL DDL.

```bash
aq db dump [--emit VALUE] [--output-dir VALUE]
```

| Kind | Name | Flags | Required | Default |
| --- | --- | --- | --- | --- |
| Option | `emit` | `--emit` | False | `python` |
| Option | `output_dir` | `--output-dir` | False | `` |

### `aq db shell`

Open an async REPL with models pre-loaded.

```bash
aq db shell [--database-url VALUE]
```

| Kind | Name | Flags | Required | Default |
| --- | --- | --- | --- | --- |
| Option | `database_url` | `--database-url` | False | `` |

### `aq db inspectdb`

Introspect database and generate Model definitions.

```bash
aq db inspectdb [--database-url VALUE] [--table VALUE] [--output VALUE]
```

| Kind | Name | Flags | Required | Default |
| --- | --- | --- | --- | --- |
| Option | `database_url` | `--database-url` | False | `` |
| Option | `table` | `--table` | False | `not set` |
| Option | `output` | `--output` | False | `` |

### `aq db showmigrations`

Show all migrations and their applied/pending status.

```bash
aq db showmigrations [--migrations-dir VALUE] [--database-url VALUE] [--database VALUE]
```

| Kind | Name | Flags | Required | Default |
| --- | --- | --- | --- | --- |
| Option | `migrations_dir` | `--migrations-dir` | False | `migrations` |
| Option | `database_url` | `--database-url` | False | `` |
| Option | `database` | `--database` | False | `` |

### `aq db sqlmigrate`

Display SQL statements for a specific migration.

```bash
aq db sqlmigrate [--migrations-dir VALUE] [--database VALUE] MIGRATION_NAME
```

| Kind | Name | Flags | Required | Default |
| --- | --- | --- | --- | --- |
| Argument | `migration_name` | `migration_name` | True | `not set` |
| Option | `migrations_dir` | `--migrations-dir` | False | `migrations` |
| Option | `database` | `--database` | False | `` |

### `aq db status`

Show database status -- tables, row counts, columns.

```bash
aq db status [--database-url VALUE]
```

| Kind | Name | Flags | Required | Default |
| --- | --- | --- | --- | --- |
| Option | `database_url` | `--database-url` | False | `` |

### `aq pack save`

Package a model into an .aquilia archive.

```bash
aq pack save [--name VALUE] [--version VALUE] [--framework VALUE] [--env-lock VALUE] [--output VALUE] [--sign-key VALUE] MODEL_PATH
```

| Kind | Name | Flags | Required | Default |
| --- | --- | --- | --- | --- |
| Argument | `model_path` | `model_path` | True | `not set` |
| Option | `name` | `--name, -n` | True | `not set` |
| Option | `version` | `--version, -V` | True | `not set` |
| Option | `framework` | `--framework, -f` | False | `custom` |
| Option | `env_lock` | `--env-lock` | False | `not set` |
| Option | `output` | `--output, -o` | False | `.` |
| Option | `sign_key` | `--sign-key` | False | `not set` |

### `aq pack inspect`

Display manifest of an .aquilia archive.

```bash
aq pack inspect ARCHIVE_PATH
```

| Kind | Name | Flags | Required | Default |
| --- | --- | --- | --- | --- |
| Argument | `archive_path` | `archive_path` | True | `not set` |

### `aq pack verify`

Verify the signature of an .aquilia archive.

```bash
aq pack verify [--key VALUE] ARCHIVE_PATH
```

| Kind | Name | Flags | Required | Default |
| --- | --- | --- | --- | --- |
| Argument | `archive_path` | `archive_path` | True | `not set` |
| Option | `key` | `--key` | True | `not set` |

### `aq pack push`

Push a pack to a remote registry.

```bash
aq pack push [--registry VALUE] [--tag VALUE] ARCHIVE_PATH
```

| Kind | Name | Flags | Required | Default |
| --- | --- | --- | --- | --- |
| Argument | `archive_path` | `archive_path` | True | `not set` |
| Option | `registry` | `--registry, -r` | False | `http://localhost:8080` |
| Option | `tag` | `--tag, -t` | False | `not set` |

### `aq model serve`

Serve a model with the built-in inference server.

```bash
aq model serve [--runtime VALUE] [--host VALUE] [--port VALUE] [--batch-size VALUE] [--batch-latency-ms VALUE] MODEL_PATH
```

| Kind | Name | Flags | Required | Default |
| --- | --- | --- | --- | --- |
| Argument | `model_path` | `model_path` | True | `not set` |
| Option | `runtime` | `--runtime, -r` | False | `python` |
| Option | `host` | `--host` | False | `0.0.0.0` |
| Option | `port` | `--port, -p` | False | `9000` |
| Option | `batch_size` | `--batch-size` | False | `1` |
| Option | `batch_latency_ms` | `--batch-latency-ms` | False | `50` |

### `aq model health`

Check model server health.

```bash
aq model health [--url VALUE]
```

| Kind | Name | Flags | Required | Default |
| --- | --- | --- | --- | --- |
| Option | `url` | `--url` | False | `http://localhost:9000` |

### `aq mlops-deploy rollout`

Start a progressive rollout.

```bash
aq mlops-deploy rollout [--from-version VALUE] [--to-version VALUE] [--strategy VALUE] [--steps VALUE] [--error-threshold VALUE] MODEL_NAME
```

| Kind | Name | Flags | Required | Default |
| --- | --- | --- | --- | --- |
| Argument | `model_name` | `model_name` | True | `not set` |
| Option | `from_version` | `--from-version` | True | `not set` |
| Option | `to_version` | `--to-version` | True | `not set` |
| Option | `strategy` | `--strategy` | False | `canary` |
| Option | `steps` | `--steps` | False | `5` |
| Option | `error_threshold` | `--error-threshold` | False | `0.05` |

### `aq mlops-deploy ci-template`

Generate CI/CD templates (GitHub Actions + Dockerfile).

```bash
aq mlops-deploy ci-template [--registry VALUE] [--output VALUE]
```

| Kind | Name | Flags | Required | Default |
| --- | --- | --- | --- | --- |
| Option | `registry` | `--registry` | False | `ghcr.io/my-org/models` |
| Option | `output` | `--output, -o` | False | `.` |

### `aq observe drift`

Detect data drift between reference and current datasets.

```bash
aq observe drift [--method VALUE] [--threshold VALUE] REFERENCE_CSV CURRENT_CSV
```

| Kind | Name | Flags | Required | Default |
| --- | --- | --- | --- | --- |
| Argument | `reference_csv` | `reference_csv` | True | `not set` |
| Argument | `current_csv` | `current_csv` | True | `not set` |
| Option | `method` | `--method` | False | `psi` |
| Option | `threshold` | `--threshold` | False | `0.2` |

### `aq observe metrics`

Export current metrics.

```bash
aq observe metrics [--format VALUE]
```

| Kind | Name | Flags | Required | Default |
| --- | --- | --- | --- | --- |
| Option | `fmt` | `--format` | False | `json` |

### `aq export onnx`

Export a PyTorch model to ONNX.

```bash
aq export onnx [--output VALUE] [--opset VALUE] MODEL_PATH
```

| Kind | Name | Flags | Required | Default |
| --- | --- | --- | --- | --- |
| Argument | `model_path` | `model_path` | True | `not set` |
| Option | `output` | `--output, -o` | True | `not set` |
| Option | `opset` | `--opset` | False | `17` |

### `aq export edge`

Export model for edge deployment.

```bash
aq export edge [--target VALUE] [--output VALUE] MODEL_PATH
```

| Kind | Name | Flags | Required | Default |
| --- | --- | --- | --- | --- |
| Argument | `model_path` | `model_path` | True | `not set` |
| Option | `target` | `--target` | True | `not set` |
| Option | `output` | `--output, -o` | True | `not set` |

### `aq plugin list`

List discovered plugins.

```bash
aq plugin list
```

### `aq plugin install`

Install a plugin from PyPI.

```bash
aq plugin install PACKAGE_NAME
```

| Kind | Name | Flags | Required | Default |
| --- | --- | --- | --- | --- |
| Argument | `package_name` | `package_name` | True | `not set` |

### `aq plugin uninstall`

Uninstall a plugin.

```bash
aq plugin uninstall PACKAGE_NAME
```

| Kind | Name | Flags | Required | Default |
| --- | --- | --- | --- | --- |
| Argument | `package_name` | `package_name` | True | `not set` |

### `aq plugin search`

Search the plugin marketplace.

```bash
aq plugin search [--verified-only] QUERY
```

| Kind | Name | Flags | Required | Default |
| --- | --- | --- | --- | --- |
| Argument | `query` | `query` | True | `not set` |
| Option | `verified_only` | `--verified-only` | False | `False` |

### `aq lineage show`

Show the full model lineage graph.

```bash
aq lineage show [--format VALUE]
```

| Kind | Name | Flags | Required | Default |
| --- | --- | --- | --- | --- |
| Option | `fmt` | `--format` | False | `tree` |

### `aq lineage ancestors`

Show all ancestors (transitive parents) of a model.

```bash
aq lineage ancestors MODEL_ID
```

| Kind | Name | Flags | Required | Default |
| --- | --- | --- | --- | --- |
| Argument | `model_id` | `model_id` | True | `not set` |

### `aq lineage descendants`

Show all descendants (derived models) of a model.

```bash
aq lineage descendants MODEL_ID
```

| Kind | Name | Flags | Required | Default |
| --- | --- | --- | --- | --- |
| Argument | `model_id` | `model_id` | True | `not set` |

### `aq lineage path`

Find derivation path between two models.

```bash
aq lineage path FROM_MODEL TO_MODEL
```

| Kind | Name | Flags | Required | Default |
| --- | --- | --- | --- | --- |
| Argument | `from_model` | `from_model` | True | `not set` |
| Argument | `to_model` | `to_model` | True | `not set` |

### `aq experiment create`

Create a new A/B experiment.

```bash
aq experiment create [--description VALUE] [--arm VALUE] EXPERIMENT_ID
```

| Kind | Name | Flags | Required | Default |
| --- | --- | --- | --- | --- |
| Argument | `experiment_id` | `experiment_id` | True | `not set` |
| Option | `description` | `--description, -d` | False | `` |
| Option | `arm` | `--arm, -a` | False | `not set` |

### `aq experiment list`

List all experiments.

```bash
aq experiment list
```

### `aq experiment conclude`

Conclude an experiment and optionally declare a winner.

```bash
aq experiment conclude [--winner VALUE] EXPERIMENT_ID
```

| Kind | Name | Flags | Required | Default |
| --- | --- | --- | --- | --- |
| Argument | `experiment_id` | `experiment_id` | True | `not set` |
| Option | `winner` | `--winner, -w` | False | `` |

### `aq experiment summary`

Show detailed experiment summary with per-arm metrics.

```bash
aq experiment summary EXPERIMENT_ID
```

| Kind | Name | Flags | Required | Default |
| --- | --- | --- | --- | --- |
| Argument | `experiment_id` | `experiment_id` | True | `not set` |

### `aq artifact list`

List all artifacts in the store.

```bash
aq artifact list [--dir VALUE] [--kind VALUE] [--tag VALUE] [--json-output]
```

| Kind | Name | Flags | Required | Default |
| --- | --- | --- | --- | --- |
| Option | `store_dir` | `--dir, -d` | False | `artifacts` |
| Option | `kind` | `--kind, -k` | False | `` |
| Option | `tag` | `--tag, -t` | False | `` |
| Option | `json_output` | `--json-output, -j` | False | `False` |

### `aq artifact inspect`

Inspect an artifact by name.

```bash
aq artifact inspect [--version VALUE] [--dir VALUE] [--json-output] NAME
```

| Kind | Name | Flags | Required | Default |
| --- | --- | --- | --- | --- |
| Argument | `name` | `name` | True | `not set` |
| Option | `version` | `--version, -V` | False | `` |
| Option | `store_dir` | `--dir, -d` | False | `artifacts` |
| Option | `json_output` | `--json-output, -j` | False | `False` |

### `aq artifact verify`

Verify the integrity of an artifact.

```bash
aq artifact verify [--version VALUE] [--dir VALUE] NAME
```

| Kind | Name | Flags | Required | Default |
| --- | --- | --- | --- | --- |
| Argument | `name` | `name` | True | `not set` |
| Option | `version` | `--version, -V` | False | `` |
| Option | `store_dir` | `--dir, -d` | False | `artifacts` |

### `aq artifact verify-all`

Verify integrity of ALL artifacts in the store.

```bash
aq artifact verify-all [--dir VALUE] [--json-output]
```

| Kind | Name | Flags | Required | Default |
| --- | --- | --- | --- | --- |
| Option | `store_dir` | `--dir, -d` | False | `artifacts` |
| Option | `json_output` | `--json-output, -j` | False | `False` |

### `aq artifact gc`

Garbage-collect unreferenced artifacts.

```bash
aq artifact gc [--dir VALUE] [--keep VALUE] [--dry-run]
```

| Kind | Name | Flags | Required | Default |
| --- | --- | --- | --- | --- |
| Option | `store_dir` | `--dir, -d` | False | `artifacts` |
| Option | `keep` | `--keep, -k` | False | `not set` |
| Option | `dry_run` | `--dry-run` | False | `False` |

### `aq artifact export`

Export artifacts as a bundle.

```bash
aq artifact export [--dir VALUE] [--output VALUE] [--name VALUE]
```

| Kind | Name | Flags | Required | Default |
| --- | --- | --- | --- | --- |
| Option | `store_dir` | `--dir, -d` | False | `artifacts` |
| Option | `output` | `--output, -o` | False | `bundle.aq.json` |
| Option | `name` | `--name, -n` | False | `not set` |

### `aq artifact diff`

Show differences between two versions of an artifact.

```bash
aq artifact diff [--dir VALUE] NAME VERSION_A VERSION_B
```

| Kind | Name | Flags | Required | Default |
| --- | --- | --- | --- | --- |
| Argument | `name` | `name` | True | `not set` |
| Argument | `version_a` | `version_a` | True | `not set` |
| Argument | `version_b` | `version_b` | True | `not set` |
| Option | `store_dir` | `--dir, -d` | False | `artifacts` |

### `aq artifact history`

Show version history of an artifact.

```bash
aq artifact history [--dir VALUE] NAME
```

| Kind | Name | Flags | Required | Default |
| --- | --- | --- | --- | --- |
| Argument | `name` | `name` | True | `not set` |
| Option | `store_dir` | `--dir, -d` | False | `artifacts` |

### `aq artifact import`

Import artifacts from a bundle file.

```bash
aq artifact import [--dir VALUE] BUNDLE_PATH
```

| Kind | Name | Flags | Required | Default |
| --- | --- | --- | --- | --- |
| Argument | `bundle_path` | `bundle_path` | True | `not set` |
| Option | `store_dir` | `--dir, -d` | False | `artifacts` |

### `aq artifact count`

Count artifacts in the store.

```bash
aq artifact count [--dir VALUE] [--kind VALUE]
```

| Kind | Name | Flags | Required | Default |
| --- | --- | --- | --- | --- |
| Option | `store_dir` | `--dir, -d` | False | `artifacts` |
| Option | `kind` | `--kind, -k` | False | `` |

### `aq artifact stats`

Show aggregate statistics for the artifact store.

```bash
aq artifact stats [--dir VALUE] [--json-output]
```

| Kind | Name | Flags | Required | Default |
| --- | --- | --- | --- | --- |
| Option | `store_dir` | `--dir, -d` | False | `artifacts` |
| Option | `json_output` | `--json-output, -j` | False | `False` |

### `aq deploy dockerfile`

Generate production-ready Dockerfiles.

```bash
aq deploy dockerfile [--dev] [--mlops] [--output VALUE] [--force] [--dry-run]
```

| Kind | Name | Flags | Required | Default |
| --- | --- | --- | --- | --- |
| Option | `dev_mode` | `--dev` | False | `False` |
| Option | `mlops_mode` | `--mlops` | False | `False` |
| Option | `output` | `--output, -o` | False | `.` |
| Option | `force` | `--force, -f` | False | `False` |
| Option | `dry_run` | `--dry-run` | False | `False` |

### `aq deploy compose`

Generate docker-compose.yml for the workspace.

```bash
aq deploy compose [--dev] [--monitoring] [--output VALUE] [--force] [--dry-run]
```

| Kind | Name | Flags | Required | Default |
| --- | --- | --- | --- | --- |
| Option | `dev_mode` | `--dev` | False | `False` |
| Option | `monitoring` | `--monitoring` | False | `False` |
| Option | `output` | `--output, -o` | False | `.` |
| Option | `force` | `--force, -f` | False | `False` |
| Option | `dry_run` | `--dry-run` | False | `False` |

### `aq deploy kubernetes`

Generate production Kubernetes manifests.

```bash
aq deploy kubernetes [--output VALUE] [--mlops] [--force] [--dry-run]
```

| Kind | Name | Flags | Required | Default |
| --- | --- | --- | --- | --- |
| Option | `output` | `--output, -o` | False | `k8s` |
| Option | `mlops` | `--mlops` | False | `False` |
| Option | `force` | `--force, -f` | False | `False` |
| Option | `dry_run` | `--dry-run` | False | `False` |

### `aq deploy nginx`

Generate Nginx reverse-proxy configuration.

```bash
aq deploy nginx [--output VALUE] [--force] [--dry-run]
```

| Kind | Name | Flags | Required | Default |
| --- | --- | --- | --- | --- |
| Option | `output` | `--output, -o` | False | `deploy/nginx` |
| Option | `force` | `--force, -f` | False | `False` |
| Option | `dry_run` | `--dry-run` | False | `False` |

### `aq deploy ci`

Generate CI/CD pipeline configuration.

```bash
aq deploy ci [--provider VALUE] [--output VALUE] [--force] [--dry-run]
```

| Kind | Name | Flags | Required | Default |
| --- | --- | --- | --- | --- |
| Option | `provider` | `--provider` | False | `github` |
| Option | `output` | `--output, -o` | False | `` |
| Option | `force` | `--force, -f` | False | `False` |
| Option | `dry_run` | `--dry-run` | False | `False` |

### `aq deploy monitoring`

Generate monitoring configuration (Prometheus + Grafana).

```bash
aq deploy monitoring [--output VALUE] [--force] [--dry-run]
```

| Kind | Name | Flags | Required | Default |
| --- | --- | --- | --- | --- |
| Option | `output` | `--output, -o` | False | `deploy` |
| Option | `force` | `--force, -f` | False | `False` |
| Option | `dry_run` | `--dry-run` | False | `False` |

### `aq deploy env`

Generate .env.example template with all Aquilia settings.

```bash
aq deploy env [--output VALUE] [--force] [--dry-run]
```

| Kind | Name | Flags | Required | Default |
| --- | --- | --- | --- | --- |
| Option | `output` | `--output, -o` | False | `.` |
| Option | `force` | `--force, -f` | False | `False` |
| Option | `dry_run` | `--dry-run` | False | `False` |

### `aq deploy all`

Generate ALL deployment files at once.

```bash
aq deploy all [--output VALUE] [--monitoring VALUE] [--ci-provider VALUE] [--force] [--dry-run]
```

| Kind | Name | Flags | Required | Default |
| --- | --- | --- | --- | --- |
| Option | `output` | `--output, -o` | False | `.` |
| Option | `monitoring` | `--monitoring` | False | `True` |
| Option | `ci_provider` | `--ci-provider` | False | `github` |
| Option | `force` | `--force, -f` | False | `False` |
| Option | `dry_run` | `--dry-run` | False | `False` |

### `aq deploy makefile`

Generate a self-documenting Makefile for dev & ops tasks.

```bash
aq deploy makefile [--output VALUE] [--force] [--dry-run]
```

| Kind | Name | Flags | Required | Default |
| --- | --- | --- | --- | --- |
| Option | `output` | `--output, -o` | False | `.` |
| Option | `force` | `--force, -f` | False | `False` |
| Option | `dry_run` | `--dry-run` | False | `False` |

### `aq deploy render`

Deploy to Render PaaS with a single command.

```bash
aq deploy render [--image VALUE] [--region VALUE] [--plan VALUE] [--num-instances VALUE] [--service-name VALUE] [--destroy] [--status] [--force] [--dry-run]
```

| Kind | Name | Flags | Required | Default |
| --- | --- | --- | --- | --- |
| Option | `image` | `--image, -i` | False | `` |
| Option | `region` | `--region, -r` | False | `` |
| Option | `plan` | `--plan` | False | `` |
| Option | `num_instances` | `--num-instances` | False | `` |
| Option | `service_name` | `--service-name` | False | `` |
| Option | `destroy` | `--destroy` | False | `False` |
| Option | `show_status` | `--status` | False | `False` |
| Option | `force` | `--force, -f` | False | `False` |
| Option | `dry_run` | `--dry-run` | False | `False` |

### `aq provider render env list`

List all environment variables for a Render service.

```bash
aq provider render env list [--service VALUE]
```

| Kind | Name | Flags | Required | Default |
| --- | --- | --- | --- | --- |
| Option | `service` | `--service, -s` | True | `not set` |

### `aq provider render env set`

Create or update an environment variable on a Render service.

```bash
aq provider render env set [--service VALUE] NAME [VALUE]
```

| Kind | Name | Flags | Required | Default |
| --- | --- | --- | --- | --- |
| Argument | `name` | `name` | True | `not set` |
| Argument | `value` | `value` | False | `not set` |
| Option | `service` | `--service, -s` | True | `not set` |

### `aq provider render env delete`

Delete an environment variable from a Render service.

```bash
aq provider render env delete [--service VALUE] NAME
```

| Kind | Name | Flags | Required | Default |
| --- | --- | --- | --- | --- |
| Argument | `name` | `name` | True | `not set` |
| Option | `service` | `--service, -s` | True | `not set` |

### `aq provider login`

Login to a cloud provider.

```bash
aq provider login [--token VALUE] [--region VALUE] PROVIDER_NAME
```

| Kind | Name | Flags | Required | Default |
| --- | --- | --- | --- | --- |
| Argument | `provider_name` | `provider_name` | True | `not set` |
| Option | `token` | `--token, -t` | False | `` |
| Option | `region` | `--region, -r` | False | `oregon` |

### `aq provider logout`

Logout from a cloud provider.

```bash
aq provider logout PROVIDER_NAME
```

| Kind | Name | Flags | Required | Default |
| --- | --- | --- | --- | --- |
| Argument | `provider_name` | `provider_name` | True | `not set` |

### `aq provider status`

Show cloud provider authentication status.

```bash
aq provider status PROVIDER_NAME
```

| Kind | Name | Flags | Required | Default |
| --- | --- | --- | --- | --- |
| Argument | `provider_name` | `provider_name` | True | `not set` |

### `aq test`

Run the test suite with Aquilia-aware defaults.

```bash
aq test [-k VALUE] [-m VALUE] [--coverage] [--coverage-html] [--failfast] [PATHS...]
```

| Kind | Name | Flags | Required | Default |
| --- | --- | --- | --- | --- |
| Argument | `paths` | `paths` | False | `not set` |
| Option | `pattern` | `-k, --pattern` | False | `` |
| Option | `markers` | `-m, --markers` | False | `` |
| Option | `coverage` | `--coverage` | False | `False` |
| Option | `coverage_html` | `--coverage-html` | False | `False` |
| Option | `failfast` | `--failfast, -x` | False | `False` |

### `aq admin check`

Pre-flight check for admin dashboard dependencies.

```bash
aq admin check [--fix] [--json]
```

| Kind | Name | Flags | Required | Default |
| --- | --- | --- | --- | --- |
| Option | `fix` | `--fix` | False | `False` |
| Option | `as_json` | `--json` | False | `False` |

### `aq admin createsuperuser`

Create an admin superuser in the database.

```bash
aq admin createsuperuser [--username VALUE] [--email VALUE] [--password VALUE] [--first-name VALUE] [--last-name VALUE] [--no-input]
```

| Kind | Name | Flags | Required | Default |
| --- | --- | --- | --- | --- |
| Option | `username` | `--username` | False | `not set` |
| Option | `email` | `--email` | False | `not set` |
| Option | `password` | `--password` | False | `not set` |
| Option | `first_name` | `--first-name` | False | `` |
| Option | `last_name` | `--last-name` | False | `` |
| Option | `no_input` | `--no-input` | False | `False` |

### `aq admin createstaff`

Create an admin staff user in the database.

```bash
aq admin createstaff [--username VALUE] [--email VALUE] [--password VALUE] [--first-name VALUE] [--last-name VALUE] [--no-input]
```

| Kind | Name | Flags | Required | Default |
| --- | --- | --- | --- | --- |
| Option | `username` | `--username` | False | `not set` |
| Option | `email` | `--email` | False | `not set` |
| Option | `password` | `--password` | False | `not set` |
| Option | `first_name` | `--first-name` | False | `` |
| Option | `last_name` | `--last-name` | False | `` |
| Option | `no_input` | `--no-input` | False | `False` |

### `aq admin listusers`

List all admin users.

```bash
aq admin listusers [--database-url VALUE] [--json] [--active-only]
```

| Kind | Name | Flags | Required | Default |
| --- | --- | --- | --- | --- |
| Option | `database_url` | `--database-url` | False | `` |
| Option | `as_json` | `--json` | False | `False` |
| Option | `active_only` | `--active-only` | False | `False` |

### `aq admin changepassword`

Change an admin user's password.

```bash
aq admin changepassword [--password VALUE] [--database-url VALUE] USERNAME
```

| Kind | Name | Flags | Required | Default |
| --- | --- | --- | --- | --- |
| Argument | `username` | `username` | True | `not set` |
| Option | `password` | `--password` | False | `not set` |
| Option | `database_url` | `--database-url` | False | `` |

### `aq admin setup`

Auto-configure all admin dependencies in workspace.py.

```bash
aq admin setup [--non-interactive] [--database-url VALUE]
```

| Kind | Name | Flags | Required | Default |
| --- | --- | --- | --- | --- |
| Option | `non_interactive` | `--non-interactive, -y` | False | `False` |
| Option | `database_url` | `--database-url` | False | `` |

### `aq admin status`

Show admin dashboard status and registered models.

```bash
aq admin status [--database-url VALUE]
```

| Kind | Name | Flags | Required | Default |
| --- | --- | --- | --- | --- |
| Option | `database_url` | `--database-url` | False | `` |

### `aq admin audit`

View admin audit trail.

```bash
aq admin audit [--limit VALUE] [--action VALUE] [--user VALUE]
```

| Kind | Name | Flags | Required | Default |
| --- | --- | --- | --- | --- |
| Option | `limit` | `--limit` | False | `50` |
| Option | `action` | `--action` | False | `` |
| Option | `user` | `--user` | False | `` |
