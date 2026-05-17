# Cli CLI Reference

This page is derived from the mounted Click command tree. If a source file has CLI helper functions but they are not mounted under `aq`, this page states that explicitly.

## Relationship To The `aq` CLI

The following mounted commands map to this subsystem.

| Command | Syntax | Purpose |
| --- | --- | --- |
| `aq init workspace` | `aq init workspace [NAME] [--minimal] [--template VALUE] [--yes]` | Create a new Aquilia workspace. |
| `aq add module` | `aq add module [NAME] [--depends-on VALUE] [--fault-domain VALUE] [--route-prefix VALUE] [--with-tests] [--minimal] [--no-docker] [--yes]` | Add a new module to the workspace. |
| `aq generate controller` | `aq generate controller NAME [--prefix VALUE] [--resource VALUE] [--simple] [--with-lifecycle] [--test] [--output VALUE]` | Generate a new controller. |
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
| `aq migrate` | `aq migrate SOURCE [--dry-run]` | Migrate from legacy layout. |
| `aq doctor` | `aq doctor [--json]` | Diagnose workspace issues. |
| `aq ws inspect` | `aq ws inspect [--artifacts-dir VALUE]` | Inspect compiled WebSocket namespaces. |
| `aq ws broadcast` | `aq ws broadcast [--namespace VALUE] [--room VALUE] [--event VALUE] [--payload VALUE]` | Broadcast message to namespace or room. |
| `aq ws gen-client` | `aq ws gen-client [--lang VALUE] [--out VALUE] [--artifacts-dir VALUE]` | Generate TypeScript client SDK from compiled WebSocket artifacts. |
| `aq ws purge-room` | `aq ws purge-room [--namespace VALUE] [--room VALUE] [--redis-url VALUE]` | Purge a room's state from the adapter. |
| `aq ws kick` | `aq ws kick [--conn VALUE] [--reason VALUE] [--redis-url VALUE]` | Kick (disconnect) a WebSocket connection. |
| `aq discover` | `aq discover [--path VALUE] [--sync] [--dry-run] [--json]` | Inspect auto-discovered modules in workspace. |
| `aq analytics` | `aq analytics [--path VALUE]` | Run discovery analytics and show health report. |
| `aq mail check` | `aq mail check` | Validate mail configuration and report issues. |
| `aq mail send-test` | `aq mail send-test TO [--subject VALUE] [--body VALUE]` | Send a test email to verify mail provider configuration. |
| `aq mail inspect` | `aq mail inspect` | Display current mail configuration as JSON. |
| `aq cache check` | `aq cache check` | Validate cache configuration and test backend connectivity. |
| `aq cache inspect` | `aq cache inspect` | Display current cache configuration as JSON. |
| `aq cache stats` | `aq cache stats` | Display cache statistics from trace diagnostics. |
| `aq cache clear` | `aq cache clear [--namespace VALUE]` | Clear all or namespace-scoped cache entries. |
| `aq i18n init` | `aq i18n init [--locales VALUE] [--directory VALUE] [--format VALUE]` | Initialize i18n in the current workspace. |
| `aq i18n check` | `aq i18n check` | Validate i18n configuration and catalog structure. |
| `aq i18n inspect` | `aq i18n inspect` | Display current i18n configuration as JSON. |
| `aq i18n extract` | `aq i18n extract [--source-dirs VALUE] [--output VALUE] [--no-merge]` | Extract translation keys from source files. |
| `aq i18n coverage` | `aq i18n coverage` | Show translation coverage per locale. |
| `aq i18n compile` | `aq i18n compile [--directory VALUE] [--output VALUE]` | Compile JSON locale files to SURP format. |
| `aq db makemigrations` | `aq db makemigrations [--app VALUE] [--migrations-dir VALUE] [--dsl VALUE] [--format VALUE]` | Generate migration files from Python Model definitions. |
| `aq db migrate` | `aq db migrate [--migrations-dir VALUE] [--database-url VALUE] [--database VALUE] [--target VALUE] [--fake] [--plan]` | Apply pending migrations to the database. |
| `aq db dump` | `aq db dump [--emit VALUE] [--output-dir VALUE]` | Dump model schema -- annotated Python overview or raw SQL DDL. |
| `aq db shell` | `aq db shell [--database-url VALUE]` | Open an async REPL with models pre-loaded. |
| `aq db inspectdb` | `aq db inspectdb [--database-url VALUE] [--table VALUE] [--output VALUE]` | Introspect database and generate Model definitions. |
| `aq db showmigrations` | `aq db showmigrations [--migrations-dir VALUE] [--database-url VALUE] [--database VALUE]` | Show all migrations and their applied/pending status. |
| `aq db sqlmigrate` | `aq db sqlmigrate MIGRATION_NAME [--migrations-dir VALUE] [--database VALUE]` | Display SQL statements for a specific migration. |
| `aq db status` | `aq db status [--database-url VALUE]` | Show database status -- tables, row counts, columns. |
| `aq pack save` | `aq pack save MODEL_PATH [--name VALUE] [--version VALUE] [--framework VALUE] [--env-lock VALUE] [--output VALUE] [--sign-key VALUE]` | Package a model into an .aquilia archive. |
| `aq pack inspect` | `aq pack inspect ARCHIVE_PATH` | Display manifest of an .aquilia archive. |
| `aq pack verify` | `aq pack verify ARCHIVE_PATH [--key VALUE]` | Verify the signature of an .aquilia archive. |
| `aq pack push` | `aq pack push ARCHIVE_PATH [--registry VALUE] [--tag VALUE]` | Push a pack to a remote registry. |
| `aq model serve` | `aq model serve MODEL_PATH [--runtime VALUE] [--host VALUE] [--port VALUE] [--batch-size VALUE] [--batch-latency-ms VALUE]` | Serve a model with the built-in inference server. |
| `aq model health` | `aq model health [--url VALUE]` | Check model server health. |
| `aq mlops-deploy rollout` | `aq mlops-deploy rollout MODEL_NAME [--from-version VALUE] [--to-version VALUE] [--strategy VALUE] [--steps VALUE] [--error-threshold VALUE]` | Start a progressive rollout. |
| `aq mlops-deploy ci-template` | `aq mlops-deploy ci-template [--registry VALUE] [--output VALUE]` | Generate CI/CD templates (GitHub Actions + Dockerfile). |
| `aq observe drift` | `aq observe drift REFERENCE_CSV CURRENT_CSV [--method VALUE] [--threshold VALUE]` | Detect data drift between reference and current datasets. |
| `aq observe metrics` | `aq observe metrics [--format VALUE]` | Export current metrics. |
| `aq export onnx` | `aq export onnx MODEL_PATH [--output VALUE] [--opset VALUE]` | Export a PyTorch model to ONNX. |
| `aq export edge` | `aq export edge MODEL_PATH [--target VALUE] [--output VALUE]` | Export model for edge deployment. |
| `aq plugin list` | `aq plugin list` | List discovered plugins. |
| `aq plugin install` | `aq plugin install PACKAGE_NAME` | Install a plugin from PyPI. |
| `aq plugin uninstall` | `aq plugin uninstall PACKAGE_NAME` | Uninstall a plugin. |
| `aq plugin search` | `aq plugin search QUERY [--verified-only]` | Search the plugin marketplace. |
| `aq lineage show` | `aq lineage show [--format VALUE]` | Show the full model lineage graph. |
| `aq lineage ancestors` | `aq lineage ancestors MODEL_ID` | Show all ancestors (transitive parents) of a model. |
| `aq lineage descendants` | `aq lineage descendants MODEL_ID` | Show all descendants (derived models) of a model. |
| `aq lineage path` | `aq lineage path FROM_MODEL TO_MODEL` | Find derivation path between two models. |
| `aq experiment create` | `aq experiment create EXPERIMENT_ID [--description VALUE] [--arm VALUE]` | Create a new A/B experiment. |
| `aq experiment list` | `aq experiment list` | List all experiments. |
| `aq experiment conclude` | `aq experiment conclude EXPERIMENT_ID [--winner VALUE]` | Conclude an experiment and optionally declare a winner. |
| `aq experiment summary` | `aq experiment summary EXPERIMENT_ID` | Show detailed experiment summary with per-arm metrics. |
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
| `aq deploy dockerfile` | `aq deploy dockerfile [--dev] [--mlops] [--output VALUE] [--force] [--dry-run]` | Generate production-ready Dockerfiles. |
| `aq deploy compose` | `aq deploy compose [--dev] [--monitoring] [--output VALUE] [--force] [--dry-run]` | Generate docker-compose.yml for the workspace. |
| `aq deploy kubernetes` | `aq deploy kubernetes [--output VALUE] [--mlops] [--force] [--dry-run]` | Generate production Kubernetes manifests. |
| `aq deploy nginx` | `aq deploy nginx [--output VALUE] [--force] [--dry-run]` | Generate Nginx reverse-proxy configuration. |
| `aq deploy ci` | `aq deploy ci [--provider VALUE] [--output VALUE] [--force] [--dry-run]` | Generate CI/CD pipeline configuration. |
| `aq deploy monitoring` | `aq deploy monitoring [--output VALUE] [--force] [--dry-run]` | Generate monitoring configuration (Prometheus + Grafana). |
| `aq deploy env` | `aq deploy env [--output VALUE] [--force] [--dry-run]` | Generate .env.example template with all Aquilia settings. |
| `aq deploy all` | `aq deploy all [--output VALUE] [--monitoring VALUE] [--ci-provider VALUE] [--force] [--dry-run]` | Generate ALL deployment files at once. |
| `aq deploy makefile` | `aq deploy makefile [--output VALUE] [--force] [--dry-run]` | Generate a self-documenting Makefile for dev & ops tasks. |
| `aq deploy render` | `aq deploy render [--image VALUE] [--region VALUE] [--plan VALUE] [--num-instances VALUE] [--service-name VALUE] [--destroy] [--status] [--force] [--dry-run]` | Deploy to Render PaaS with a single command. |
| `aq provider render env list` | `aq provider render env list [--service VALUE]` | List all environment variables for a Render service. |
| `aq provider render env set` | `aq provider render env set NAME [VALUE] [--service VALUE]` | Create or update an environment variable on a Render service. |
| `aq provider render env delete` | `aq provider render env delete NAME [--service VALUE]` | Delete an environment variable from a Render service. |
| `aq provider login` | `aq provider login PROVIDER_NAME [--token VALUE] [--region VALUE]` | Login to a cloud provider. |
| `aq provider logout` | `aq provider logout PROVIDER_NAME` | Logout from a cloud provider. |
| `aq provider status` | `aq provider status PROVIDER_NAME` | Show cloud provider authentication status. |
| `aq test` | `aq test [PATHS] [-k VALUE] [-m VALUE] [--coverage] [--coverage-html] [--failfast]` | Run the test suite with Aquilia-aware defaults. |
| `aq admin check` | `aq admin check [--fix] [--json]` | Pre-flight check for admin dashboard dependencies. |
| `aq admin createsuperuser` | `aq admin createsuperuser [--username VALUE] [--email VALUE] [--password VALUE] [--first-name VALUE] [--last-name VALUE] [--no-input]` | Create an admin superuser in the database. |
| `aq admin createstaff` | `aq admin createstaff [--username VALUE] [--email VALUE] [--password VALUE] [--first-name VALUE] [--last-name VALUE] [--no-input]` | Create an admin staff user in the database. |
| `aq admin listusers` | `aq admin listusers [--database-url VALUE] [--json] [--active-only]` | List all admin users. |
| `aq admin changepassword` | `aq admin changepassword USERNAME [--password VALUE] [--database-url VALUE]` | Change an admin user's password. |
| `aq admin setup` | `aq admin setup [--non-interactive] [--database-url VALUE]` | Auto-configure all admin dependencies in workspace.py. |
| `aq admin status` | `aq admin status [--database-url VALUE]` | Show admin dashboard status and registered models. |
| `aq admin audit` | `aq admin audit [--limit VALUE] [--action VALUE] [--user VALUE]` | View admin audit trail. |

## Detailed Commands

### `aq init workspace`

Create a new Aquilia workspace.

```bash
aq init workspace [NAME] [--minimal] [--template VALUE] [--yes]
```

| Kind | Name | Flags | Required | Default | Help |
| --- | --- | --- | --- | --- | --- |
| Argument | `name` | `name` | False | `` |  |
| Option | `minimal` | `--minimal` | False | `False` | Minimal setup (no examples) |
| Option | `template` | `--template` | False | `not set` | Use template (api, service, monolith) |
| Option | `yes` | `--yes, -y` | False | `False` | Skip interactive prompts and use defaults |

### `aq add module`

Add a new module to the workspace.

```bash
aq add module [NAME] [--depends-on VALUE] [--fault-domain VALUE] [--route-prefix VALUE] [--with-tests] [--minimal] [--no-docker] [--yes]
```

| Kind | Name | Flags | Required | Default | Help |
| --- | --- | --- | --- | --- | --- |
| Argument | `name` | `name` | False | `` |  |
| Option | `depends_on` | `--depends-on` | False | `not set` | Module dependencies |
| Option | `fault_domain` | `--fault-domain` | False | `not set` | Custom fault domain |
| Option | `route_prefix` | `--route-prefix` | False | `not set` | Route prefix (default: /name) |
| Option | `with_tests` | `--with-tests` | False | `False` | Generate test routes |
| Option | `minimal` | `--minimal` | False | `False` | Generate minimal module (controller + manifest only) |
| Option | `no_docker` | `--no-docker` | False | `False` | Skip auto-generating Docker files |
| Option | `yes` | `--yes, -y` | False | `False` | Skip interactive prompts and use defaults |

### `aq generate controller`

Generate a new controller.

```bash
aq generate controller NAME [--prefix VALUE] [--resource VALUE] [--simple] [--with-lifecycle] [--test] [--output VALUE]
```

| Kind | Name | Flags | Required | Default | Help |
| --- | --- | --- | --- | --- | --- |
| Argument | `name` | `name` | True | `not set` |  |
| Option | `prefix` | `--prefix` | False | `not set` | Route prefix (default: /name) |
| Option | `resource` | `--resource` | False | `not set` | Resource name (default: name) |
| Option | `simple` | `--simple` | False | `False` | Generate simple controller |
| Option | `with_lifecycle` | `--with-lifecycle` | False | `False` | Include lifecycle hooks |
| Option | `test` | `--test` | False | `False` | Generate test/demo controller |
| Option | `output` | `--output` | False | `not set` | Output directory |

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

### `aq migrate`

Migrate from legacy layout.

```bash
aq migrate SOURCE [--dry-run]
```

| Kind | Name | Flags | Required | Default | Help |
| --- | --- | --- | --- | --- | --- |
| Argument | `source` | `source` | True | `not set` |  |
| Option | `dry_run` | `--dry-run` | False | `False` | Preview migration |

### `aq doctor`

Diagnose workspace issues.

```bash
aq doctor [--json]
```

| Kind | Name | Flags | Required | Default | Help |
| --- | --- | --- | --- | --- | --- |
| Option | `as_json` | `--json` | False | `False` | Output results as JSON |

### `aq ws inspect`

Inspect compiled WebSocket namespaces.

```bash
aq ws inspect [--artifacts-dir VALUE]
```

| Kind | Name | Flags | Required | Default | Help |
| --- | --- | --- | --- | --- | --- |
| Option | `artifacts_dir` | `--artifacts-dir` | False | `artifacts` | Artifacts directory |

### `aq ws broadcast`

Broadcast message to namespace or room.

```bash
aq ws broadcast [--namespace VALUE] [--room VALUE] [--event VALUE] [--payload VALUE]
```

| Kind | Name | Flags | Required | Default | Help |
| --- | --- | --- | --- | --- | --- |
| Option | `namespace` | `--namespace` | True | `not set` | Namespace |
| Option | `room` | `--room` | False | `` | Room (optional) |
| Option | `event` | `--event` | True | `not set` | Event name |
| Option | `payload` | `--payload` | False | `{}` | JSON payload |

### `aq ws gen-client`

Generate TypeScript client SDK from compiled WebSocket artifacts.

```bash
aq ws gen-client [--lang VALUE] [--out VALUE] [--artifacts-dir VALUE]
```

| Kind | Name | Flags | Required | Default | Help |
| --- | --- | --- | --- | --- | --- |
| Option | `lang` | `--lang` | False | `ts` | Language (ts) |
| Option | `out` | `--out` | True | `not set` | Output file |
| Option | `artifacts_dir` | `--artifacts-dir` | False | `artifacts` | Artifacts directory |

### `aq ws purge-room`

Purge a room's state from the adapter.

```bash
aq ws purge-room [--namespace VALUE] [--room VALUE] [--redis-url VALUE]
```

| Kind | Name | Flags | Required | Default | Help |
| --- | --- | --- | --- | --- | --- |
| Option | `namespace` | `--namespace` | True | `not set` | Namespace |
| Option | `room` | `--room` | True | `not set` | Room to purge |
| Option | `redis_url` | `--redis-url` | False | `` | Redis URL (optional) |

### `aq ws kick`

Kick (disconnect) a WebSocket connection.

```bash
aq ws kick [--conn VALUE] [--reason VALUE] [--redis-url VALUE]
```

| Kind | Name | Flags | Required | Default | Help |
| --- | --- | --- | --- | --- | --- |
| Option | `conn` | `--conn` | True | `not set` | Connection ID to disconnect |
| Option | `reason` | `--reason` | False | `kicked by admin` | Reason for kick |
| Option | `redis_url` | `--redis-url` | False | `` | Redis URL (optional) |

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

### `aq analytics`

Run discovery analytics and show health report.

```bash
aq analytics [--path VALUE]
```

| Kind | Name | Flags | Required | Default | Help |
| --- | --- | --- | --- | --- | --- |
| Option | `path` | `--path` | False | `` | Workspace path |

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

### `aq db makemigrations`

Generate migration files from Python Model definitions.

```bash
aq db makemigrations [--app VALUE] [--migrations-dir VALUE] [--dsl VALUE] [--format VALUE]
```

| Kind | Name | Flags | Required | Default | Help |
| --- | --- | --- | --- | --- | --- |
| Option | `app` | `--app` | False | `` | Restrict to specific module/app |
| Option | `migrations_dir` | `--migrations-dir` | False | `migrations` | Migrations directory |
| Option | `dsl` | `--dsl, --no-dsl` | False | `True` | Use new DSL format (default: True) |
| Option | `fmt` | `--format` | False | `surp` | Migration file format -- surp (binary, default) or python |

### `aq db migrate`

Apply pending migrations to the database.

```bash
aq db migrate [--migrations-dir VALUE] [--database-url VALUE] [--database VALUE] [--target VALUE] [--fake] [--plan]
```

| Kind | Name | Flags | Required | Default | Help |
| --- | --- | --- | --- | --- | --- |
| Option | `migrations_dir` | `--migrations-dir` | False | `migrations` | Migrations directory |
| Option | `database_url` | `--database-url` | False | `` | Database URL (auto-detected from workspace.py) |
| Option | `database` | `--database` | False | `` | Database alias (for multi-db) |
| Option | `target` | `--target` | False | `` | Target revision (or "zero" to rollback all) |
| Option | `fake` | `--fake` | False | `False` | Mark migrations as applied without running SQL |
| Option | `plan` | `--plan` | False | `False` | Preview SQL without executing (dry-run) |

### `aq db dump`

Dump model schema -- annotated Python overview or raw SQL DDL.

```bash
aq db dump [--emit VALUE] [--output-dir VALUE]
```

| Kind | Name | Flags | Required | Default | Help |
| --- | --- | --- | --- | --- | --- |
| Option | `emit` | `--emit` | False | `python` | Output format |
| Option | `output_dir` | `--output-dir` | False | `` | Output directory |

### `aq db shell`

Open an async REPL with models pre-loaded.

```bash
aq db shell [--database-url VALUE]
```

| Kind | Name | Flags | Required | Default | Help |
| --- | --- | --- | --- | --- | --- |
| Option | `database_url` | `--database-url` | False | `` | Database URL (auto-detected from workspace.py) |

### `aq db inspectdb`

Introspect database and generate Model definitions.

```bash
aq db inspectdb [--database-url VALUE] [--table VALUE] [--output VALUE]
```

| Kind | Name | Flags | Required | Default | Help |
| --- | --- | --- | --- | --- | --- |
| Option | `database_url` | `--database-url` | False | `` | Database URL (auto-detected from workspace.py) |
| Option | `table` | `--table` | False | `not set` | Specific tables to inspect |
| Option | `output` | `--output` | False | `` | Output file path |

### `aq db showmigrations`

Show all migrations and their applied/pending status.

```bash
aq db showmigrations [--migrations-dir VALUE] [--database-url VALUE] [--database VALUE]
```

| Kind | Name | Flags | Required | Default | Help |
| --- | --- | --- | --- | --- | --- |
| Option | `migrations_dir` | `--migrations-dir` | False | `migrations` | Migrations directory |
| Option | `database_url` | `--database-url` | False | `` | Database URL (auto-detected from workspace.py) |
| Option | `database` | `--database` | False | `` | Database alias |

### `aq db sqlmigrate`

Display SQL statements for a specific migration.

```bash
aq db sqlmigrate MIGRATION_NAME [--migrations-dir VALUE] [--database VALUE]
```

| Kind | Name | Flags | Required | Default | Help |
| --- | --- | --- | --- | --- | --- |
| Argument | `migration_name` | `migration_name` | True | `not set` |  |
| Option | `migrations_dir` | `--migrations-dir` | False | `migrations` | Migrations directory |
| Option | `database` | `--database` | False | `` | Database alias |

### `aq db status`

Show database status -- tables, row counts, columns.

```bash
aq db status [--database-url VALUE]
```

| Kind | Name | Flags | Required | Default | Help |
| --- | --- | --- | --- | --- | --- |
| Option | `database_url` | `--database-url` | False | `` | Database URL (auto-detected from workspace.py) |

### `aq pack save`

Package a model into an .aquilia archive.

```bash
aq pack save MODEL_PATH [--name VALUE] [--version VALUE] [--framework VALUE] [--env-lock VALUE] [--output VALUE] [--sign-key VALUE]
```

| Kind | Name | Flags | Required | Default | Help |
| --- | --- | --- | --- | --- | --- |
| Argument | `model_path` | `model_path` | True | `not set` |  |
| Option | `name` | `--name, -n` | True | `not set` | Model name |
| Option | `version` | `--version, -V` | True | `not set` | Semantic version |
| Option | `framework` | `--framework, -f` | False | `custom` | Model framework |
| Option | `env_lock` | `--env-lock` | False | `not set` | Path to requirements.txt or conda lock |
| Option | `output` | `--output, -o` | False | `.` | Output directory |
| Option | `sign_key` | `--sign-key` | False | `not set` | HMAC key or path to RSA private key for signing |

### `aq pack inspect`

Display manifest of an .aquilia archive.

```bash
aq pack inspect ARCHIVE_PATH
```

| Kind | Name | Flags | Required | Default | Help |
| --- | --- | --- | --- | --- | --- |
| Argument | `archive_path` | `archive_path` | True | `not set` |  |

### `aq pack verify`

Verify the signature of an .aquilia archive.

```bash
aq pack verify ARCHIVE_PATH [--key VALUE]
```

| Kind | Name | Flags | Required | Default | Help |
| --- | --- | --- | --- | --- | --- |
| Argument | `archive_path` | `archive_path` | True | `not set` |  |
| Option | `key` | `--key` | True | `not set` | HMAC key or path to RSA public key |

### `aq pack push`

Push a pack to a remote registry.

```bash
aq pack push ARCHIVE_PATH [--registry VALUE] [--tag VALUE]
```

| Kind | Name | Flags | Required | Default | Help |
| --- | --- | --- | --- | --- | --- |
| Argument | `archive_path` | `archive_path` | True | `not set` |  |
| Option | `registry` | `--registry, -r` | False | `http://localhost:8080` | Registry URL |
| Option | `tag` | `--tag, -t` | False | `not set` | Additional tags |

### `aq model serve`

Serve a model with the built-in inference server.

```bash
aq model serve MODEL_PATH [--runtime VALUE] [--host VALUE] [--port VALUE] [--batch-size VALUE] [--batch-latency-ms VALUE]
```

| Kind | Name | Flags | Required | Default | Help |
| --- | --- | --- | --- | --- | --- |
| Argument | `model_path` | `model_path` | True | `not set` |  |
| Option | `runtime` | `--runtime, -r` | False | `python` |  |
| Option | `host` | `--host` | False | `0.0.0.0` | Bind host |
| Option | `port` | `--port, -p` | False | `9000` | Bind port |
| Option | `batch_size` | `--batch-size` | False | `1` | Max batch size |
| Option | `batch_latency_ms` | `--batch-latency-ms` | False | `50` | Max batch wait (ms) |

### `aq model health`

Check model server health.

```bash
aq model health [--url VALUE]
```

| Kind | Name | Flags | Required | Default | Help |
| --- | --- | --- | --- | --- | --- |
| Option | `url` | `--url` | False | `http://localhost:9000` | Server URL |

### `aq mlops-deploy rollout`

Start a progressive rollout.

```bash
aq mlops-deploy rollout MODEL_NAME [--from-version VALUE] [--to-version VALUE] [--strategy VALUE] [--steps VALUE] [--error-threshold VALUE]
```

| Kind | Name | Flags | Required | Default | Help |
| --- | --- | --- | --- | --- | --- |
| Argument | `model_name` | `model_name` | True | `not set` |  |
| Option | `from_version` | `--from-version` | True | `not set` | Current version |
| Option | `to_version` | `--to-version` | True | `not set` | Target version |
| Option | `strategy` | `--strategy` | False | `canary` |  |
| Option | `steps` | `--steps` | False | `5` | Number of rollout phases |
| Option | `error_threshold` | `--error-threshold` | False | `0.05` | Auto-rollback error rate |

### `aq mlops-deploy ci-template`

Generate CI/CD templates (GitHub Actions + Dockerfile).

```bash
aq mlops-deploy ci-template [--registry VALUE] [--output VALUE]
```

| Kind | Name | Flags | Required | Default | Help |
| --- | --- | --- | --- | --- | --- |
| Option | `registry` | `--registry` | False | `ghcr.io/my-org/models` | Container registry |
| Option | `output` | `--output, -o` | False | `.` | Output directory |

### `aq observe drift`

Detect data drift between reference and current datasets.

```bash
aq observe drift REFERENCE_CSV CURRENT_CSV [--method VALUE] [--threshold VALUE]
```

| Kind | Name | Flags | Required | Default | Help |
| --- | --- | --- | --- | --- | --- |
| Argument | `reference_csv` | `reference_csv` | True | `not set` |  |
| Argument | `current_csv` | `current_csv` | True | `not set` |  |
| Option | `method` | `--method` | False | `psi` |  |
| Option | `threshold` | `--threshold` | False | `0.2` | Drift alert threshold |

### `aq observe metrics`

Export current metrics.

```bash
aq observe metrics [--format VALUE]
```

| Kind | Name | Flags | Required | Default | Help |
| --- | --- | --- | --- | --- | --- |
| Option | `fmt` | `--format` | False | `json` |  |

### `aq export onnx`

Export a PyTorch model to ONNX.

```bash
aq export onnx MODEL_PATH [--output VALUE] [--opset VALUE]
```

| Kind | Name | Flags | Required | Default | Help |
| --- | --- | --- | --- | --- | --- |
| Argument | `model_path` | `model_path` | True | `not set` |  |
| Option | `output` | `--output, -o` | True | `not set` | Output .onnx path |
| Option | `opset` | `--opset` | False | `17` | ONNX opset version |

### `aq export edge`

Export model for edge deployment.

```bash
aq export edge MODEL_PATH [--target VALUE] [--output VALUE]
```

| Kind | Name | Flags | Required | Default | Help |
| --- | --- | --- | --- | --- | --- |
| Argument | `model_path` | `model_path` | True | `not set` |  |
| Option | `target` | `--target` | True | `not set` |  |
| Option | `output` | `--output, -o` | True | `not set` |  |

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

| Kind | Name | Flags | Required | Default | Help |
| --- | --- | --- | --- | --- | --- |
| Argument | `package_name` | `package_name` | True | `not set` |  |

### `aq plugin uninstall`

Uninstall a plugin.

```bash
aq plugin uninstall PACKAGE_NAME
```

| Kind | Name | Flags | Required | Default | Help |
| --- | --- | --- | --- | --- | --- |
| Argument | `package_name` | `package_name` | True | `not set` |  |

### `aq plugin search`

Search the plugin marketplace.

```bash
aq plugin search QUERY [--verified-only]
```

| Kind | Name | Flags | Required | Default | Help |
| --- | --- | --- | --- | --- | --- |
| Argument | `query` | `query` | True | `not set` |  |
| Option | `verified_only` | `--verified-only` | False | `False` | Only show verified plugins |

### `aq lineage show`

Show the full model lineage graph.

```bash
aq lineage show [--format VALUE]
```

| Kind | Name | Flags | Required | Default | Help |
| --- | --- | --- | --- | --- | --- |
| Option | `fmt` | `--format` | False | `tree` |  |

### `aq lineage ancestors`

Show all ancestors (transitive parents) of a model.

```bash
aq lineage ancestors MODEL_ID
```

| Kind | Name | Flags | Required | Default | Help |
| --- | --- | --- | --- | --- | --- |
| Argument | `model_id` | `model_id` | True | `not set` |  |

### `aq lineage descendants`

Show all descendants (derived models) of a model.

```bash
aq lineage descendants MODEL_ID
```

| Kind | Name | Flags | Required | Default | Help |
| --- | --- | --- | --- | --- | --- |
| Argument | `model_id` | `model_id` | True | `not set` |  |

### `aq lineage path`

Find derivation path between two models.

```bash
aq lineage path FROM_MODEL TO_MODEL
```

| Kind | Name | Flags | Required | Default | Help |
| --- | --- | --- | --- | --- | --- |
| Argument | `from_model` | `from_model` | True | `not set` |  |
| Argument | `to_model` | `to_model` | True | `not set` |  |

### `aq experiment create`

Create a new A/B experiment.

```bash
aq experiment create EXPERIMENT_ID [--description VALUE] [--arm VALUE]
```

| Kind | Name | Flags | Required | Default | Help |
| --- | --- | --- | --- | --- | --- |
| Argument | `experiment_id` | `experiment_id` | True | `not set` |  |
| Option | `description` | `--description, -d` | False | `` | Experiment description |
| Option | `arm` | `--arm, -a` | False | `not set` | Arm spec: name:version:weight (e.g. control:v1:0.5) |

### `aq experiment list`

List all experiments.

```bash
aq experiment list
```

### `aq experiment conclude`

Conclude an experiment and optionally declare a winner.

```bash
aq experiment conclude EXPERIMENT_ID [--winner VALUE]
```

| Kind | Name | Flags | Required | Default | Help |
| --- | --- | --- | --- | --- | --- |
| Argument | `experiment_id` | `experiment_id` | True | `not set` |  |
| Option | `winner` | `--winner, -w` | False | `` | Winning arm name |

### `aq experiment summary`

Show detailed experiment summary with per-arm metrics.

```bash
aq experiment summary EXPERIMENT_ID
```

| Kind | Name | Flags | Required | Default | Help |
| --- | --- | --- | --- | --- | --- |
| Argument | `experiment_id` | `experiment_id` | True | `not set` |  |

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

### `aq deploy dockerfile`

Generate production-ready Dockerfiles.

```bash
aq deploy dockerfile [--dev] [--mlops] [--output VALUE] [--force] [--dry-run]
```

| Kind | Name | Flags | Required | Default | Help |
| --- | --- | --- | --- | --- | --- |
| Option | `dev_mode` | `--dev` | False | `False` | Generate development Dockerfile (with hot-reload) |
| Option | `mlops_mode` | `--mlops` | False | `False` | Generate MLOps model-serving Dockerfile |
| Option | `output` | `--output, -o` | False | `.` | Output directory |
| Option | `force` | `--force, -f` | False | `False` | Overwrite existing files |
| Option | `dry_run` | `--dry-run` | False | `False` | Preview without writing files |

### `aq deploy compose`

Generate docker-compose.yml for the workspace.

```bash
aq deploy compose [--dev] [--monitoring] [--output VALUE] [--force] [--dry-run]
```

| Kind | Name | Flags | Required | Default | Help |
| --- | --- | --- | --- | --- | --- |
| Option | `dev_mode` | `--dev` | False | `False` | Also generate docker-compose.dev.yml |
| Option | `monitoring` | `--monitoring` | False | `False` | Include Prometheus + Grafana services |
| Option | `output` | `--output, -o` | False | `.` | Output directory |
| Option | `force` | `--force, -f` | False | `False` | Overwrite existing files |
| Option | `dry_run` | `--dry-run` | False | `False` | Preview without writing files |

### `aq deploy kubernetes`

Generate production Kubernetes manifests.

```bash
aq deploy kubernetes [--output VALUE] [--mlops] [--force] [--dry-run]
```

| Kind | Name | Flags | Required | Default | Help |
| --- | --- | --- | --- | --- | --- |
| Option | `output` | `--output, -o` | False | `k8s` | Output directory |
| Option | `mlops` | `--mlops` | False | `False` | Force include MLOps manifests |
| Option | `force` | `--force, -f` | False | `False` | Overwrite existing files |
| Option | `dry_run` | `--dry-run` | False | `False` | Preview without writing files |

### `aq deploy nginx`

Generate Nginx reverse-proxy configuration.

```bash
aq deploy nginx [--output VALUE] [--force] [--dry-run]
```

| Kind | Name | Flags | Required | Default | Help |
| --- | --- | --- | --- | --- | --- |
| Option | `output` | `--output, -o` | False | `deploy/nginx` | Output directory |
| Option | `force` | `--force, -f` | False | `False` | Overwrite existing files |
| Option | `dry_run` | `--dry-run` | False | `False` | Preview without writing files |

### `aq deploy ci`

Generate CI/CD pipeline configuration.

```bash
aq deploy ci [--provider VALUE] [--output VALUE] [--force] [--dry-run]
```

| Kind | Name | Flags | Required | Default | Help |
| --- | --- | --- | --- | --- | --- |
| Option | `provider` | `--provider` | False | `github` | CI provider |
| Option | `output` | `--output, -o` | False | `` | Output directory |
| Option | `force` | `--force, -f` | False | `False` | Overwrite existing files |
| Option | `dry_run` | `--dry-run` | False | `False` | Preview without writing files |

### `aq deploy monitoring`

Generate monitoring configuration (Prometheus + Grafana).

```bash
aq deploy monitoring [--output VALUE] [--force] [--dry-run]
```

| Kind | Name | Flags | Required | Default | Help |
| --- | --- | --- | --- | --- | --- |
| Option | `output` | `--output, -o` | False | `deploy` | Output base directory |
| Option | `force` | `--force, -f` | False | `False` | Overwrite existing files |
| Option | `dry_run` | `--dry-run` | False | `False` | Preview without writing files |

### `aq deploy env`

Generate .env.example template with all Aquilia settings.

```bash
aq deploy env [--output VALUE] [--force] [--dry-run]
```

| Kind | Name | Flags | Required | Default | Help |
| --- | --- | --- | --- | --- | --- |
| Option | `output` | `--output, -o` | False | `.` | Output directory |
| Option | `force` | `--force, -f` | False | `False` | Overwrite existing files |
| Option | `dry_run` | `--dry-run` | False | `False` | Preview without writing files |

### `aq deploy all`

Generate ALL deployment files at once.

```bash
aq deploy all [--output VALUE] [--monitoring VALUE] [--ci-provider VALUE] [--force] [--dry-run]
```

| Kind | Name | Flags | Required | Default | Help |
| --- | --- | --- | --- | --- | --- |
| Option | `output` | `--output, -o` | False | `.` | Output base directory |
| Option | `monitoring` | `--monitoring` | False | `True` | Include monitoring (default: yes) |
| Option | `ci_provider` | `--ci-provider` | False | `github` | CI/CD provider |
| Option | `force` | `--force, -f` | False | `False` | Overwrite existing files |
| Option | `dry_run` | `--dry-run` | False | `False` | Preview without writing files |

### `aq deploy makefile`

Generate a self-documenting Makefile for dev & ops tasks.

```bash
aq deploy makefile [--output VALUE] [--force] [--dry-run]
```

| Kind | Name | Flags | Required | Default | Help |
| --- | --- | --- | --- | --- | --- |
| Option | `output` | `--output, -o` | False | `.` | Output directory |
| Option | `force` | `--force, -f` | False | `False` | Overwrite existing files |
| Option | `dry_run` | `--dry-run` | False | `False` | Preview without writing files |

### `aq deploy render`

Deploy to Render PaaS with a single command.

```bash
aq deploy render [--image VALUE] [--region VALUE] [--plan VALUE] [--num-instances VALUE] [--service-name VALUE] [--destroy] [--status] [--force] [--dry-run]
```

| Kind | Name | Flags | Required | Default | Help |
| --- | --- | --- | --- | --- | --- |
| Option | `image` | `--image, -i` | False | `` | Docker image to deploy (e.g. registry/myapp:latest) |
| Option | `region` | `--region, -r` | False | `` | Deployment region (oregon, frankfurt, ohio, virginia, singapore) |
| Option | `plan` | `--plan` | False | `` | Render plan |
| Option | `num_instances` | `--num-instances` | False | `` | Number of instances |
| Option | `service_name` | `--service-name` | False | `` | Render service name (default: workspace name) |
| Option | `destroy` | `--destroy` | False | `False` | Destroy the deployed service |
| Option | `show_status` | `--status` | False | `False` | Show deployment status |
| Option | `force` | `--force, -f` | False | `False` | Overwrite existing files |
| Option | `dry_run` | `--dry-run` | False | `False` | Preview without writing files |

### `aq provider render env list`

List all environment variables for a Render service.

```bash
aq provider render env list [--service VALUE]
```

| Kind | Name | Flags | Required | Default | Help |
| --- | --- | --- | --- | --- | --- |
| Option | `service` | `--service, -s` | True | `not set` | Render service name |

### `aq provider render env set`

Create or update an environment variable on a Render service.

```bash
aq provider render env set NAME [VALUE] [--service VALUE]
```

| Kind | Name | Flags | Required | Default | Help |
| --- | --- | --- | --- | --- | --- |
| Argument | `name` | `name` | True | `not set` |  |
| Argument | `value` | `value` | False | `not set` |  |
| Option | `service` | `--service, -s` | True | `not set` | Render service name |

### `aq provider render env delete`

Delete an environment variable from a Render service.

```bash
aq provider render env delete NAME [--service VALUE]
```

| Kind | Name | Flags | Required | Default | Help |
| --- | --- | --- | --- | --- | --- |
| Argument | `name` | `name` | True | `not set` |  |
| Option | `service` | `--service, -s` | True | `not set` | Render service name |

### `aq provider login`

Login to a cloud provider.

```bash
aq provider login PROVIDER_NAME [--token VALUE] [--region VALUE]
```

| Kind | Name | Flags | Required | Default | Help |
| --- | --- | --- | --- | --- | --- |
| Argument | `provider_name` | `provider_name` | True | `not set` |  |
| Option | `token` | `--token, -t` | False | `` | API token (reads from stdin if omitted) |
| Option | `region` | `--region, -r` | False | `oregon` | Default deployment region |

### `aq provider logout`

Logout from a cloud provider.

```bash
aq provider logout PROVIDER_NAME
```

| Kind | Name | Flags | Required | Default | Help |
| --- | --- | --- | --- | --- | --- |
| Argument | `provider_name` | `provider_name` | True | `not set` |  |

### `aq provider status`

Show cloud provider authentication status.

```bash
aq provider status PROVIDER_NAME
```

| Kind | Name | Flags | Required | Default | Help |
| --- | --- | --- | --- | --- | --- |
| Argument | `provider_name` | `provider_name` | True | `not set` |  |

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

### `aq admin check`

Pre-flight check for admin dashboard dependencies.

```bash
aq admin check [--fix] [--json]
```

| Kind | Name | Flags | Required | Default | Help |
| --- | --- | --- | --- | --- | --- |
| Option | `fix` | `--fix` | False | `False` | Auto-fix missing configuration by uncommenting workspace.py sections |
| Option | `as_json` | `--json` | False | `False` | Output results as JSON |

### `aq admin createsuperuser`

Create an admin superuser in the database.

```bash
aq admin createsuperuser [--username VALUE] [--email VALUE] [--password VALUE] [--first-name VALUE] [--last-name VALUE] [--no-input]
```

| Kind | Name | Flags | Required | Default | Help |
| --- | --- | --- | --- | --- | --- |
| Option | `username` | `--username` | False | `not set` | Admin username |
| Option | `email` | `--email` | False | `not set` | Admin email (required) |
| Option | `password` | `--password` | False | `not set` | Admin password |
| Option | `first_name` | `--first-name` | False | `` | First name (optional) |
| Option | `last_name` | `--last-name` | False | `` | Last name (optional) |
| Option | `no_input` | `--no-input` | False | `False` | Non-interactive mode (requires all options) |

### `aq admin createstaff`

Create an admin staff user in the database.

```bash
aq admin createstaff [--username VALUE] [--email VALUE] [--password VALUE] [--first-name VALUE] [--last-name VALUE] [--no-input]
```

| Kind | Name | Flags | Required | Default | Help |
| --- | --- | --- | --- | --- | --- |
| Option | `username` | `--username` | False | `not set` | Staff username |
| Option | `email` | `--email` | False | `not set` | Staff email (required) |
| Option | `password` | `--password` | False | `not set` | Staff password |
| Option | `first_name` | `--first-name` | False | `` | First name (optional) |
| Option | `last_name` | `--last-name` | False | `` | Last name (optional) |
| Option | `no_input` | `--no-input` | False | `False` | Non-interactive mode (requires all options) |

### `aq admin listusers`

List all admin users.

```bash
aq admin listusers [--database-url VALUE] [--json] [--active-only]
```

| Kind | Name | Flags | Required | Default | Help |
| --- | --- | --- | --- | --- | --- |
| Option | `database_url` | `--database-url` | False | `` | Database URL |
| Option | `as_json` | `--json` | False | `False` | Output as JSON |
| Option | `active_only` | `--active-only` | False | `False` | Show only active users |

### `aq admin changepassword`

Change an admin user's password.

```bash
aq admin changepassword USERNAME [--password VALUE] [--database-url VALUE]
```

| Kind | Name | Flags | Required | Default | Help |
| --- | --- | --- | --- | --- | --- |
| Argument | `username` | `username` | True | `not set` |  |
| Option | `password` | `--password` | False | `not set` | New password |
| Option | `database_url` | `--database-url` | False | `` | Database URL |

### `aq admin setup`

Auto-configure all admin dependencies in workspace.py.

```bash
aq admin setup [--non-interactive] [--database-url VALUE]
```

| Kind | Name | Flags | Required | Default | Help |
| --- | --- | --- | --- | --- | --- |
| Option | `non_interactive` | `--non-interactive, -y` | False | `False` | Skip confirmation prompts |
| Option | `database_url` | `--database-url` | False | `` | Database URL to use (default: sqlite:///db.sqlite3) |

### `aq admin status`

Show admin dashboard status and registered models.

```bash
aq admin status [--database-url VALUE]
```

| Kind | Name | Flags | Required | Default | Help |
| --- | --- | --- | --- | --- | --- |
| Option | `database_url` | `--database-url` | False | `` | Database URL |

### `aq admin audit`

View admin audit trail.

```bash
aq admin audit [--limit VALUE] [--action VALUE] [--user VALUE]
```

| Kind | Name | Flags | Required | Default | Help |
| --- | --- | --- | --- | --- | --- |
| Option | `limit` | `--limit` | False | `50` | Number of entries to show |
| Option | `action` | `--action` | False | `` | Filter by action type |
| Option | `user` | `--user` | False | `` | Filter by username |

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
