# CLI API Reference

This page is extracted from the current Python source. It includes public classes, methods, functions, constants, dataclass-like fields, decorators, and notable attributes.

## Public Class Summary

| Name | Source | Bases | Purpose |
| --- | --- | --- | --- |
| `AquiliaGroup` | `aquilia/cli/__main__.py` | click.Group | Click group subclass with branded help output. |
| `DiscoveryAnalytics` | `aquilia/cli/commands/analytics.py` | object | Analyze discovered modules and provide insights. |
| `DiscoveryInspector` | `aquilia/cli/commands/discover.py` | object | Inspect, validate, and auto-sync discovered modules. |
| `DiagnosticResult` | `aquilia/cli/commands/doctor.py` | object | Structured diagnostic result. |
| `DiagnosticReport` | `aquilia/cli/commands/doctor.py` | object | Complete diagnostic report. |
| `MigrationResult` | `aquilia/cli/commands/migrate.py` | object | Result of migration operation. |
| `ValidationResult` | `aquilia/cli/commands/validate.py` | object | Result of manifest validation. |
| `WorkspaceCompiler` | `aquilia/cli/compilers/workspace.py` | object | Compile workspace manifests to artifacts via the unified artifact system. |
| `DiscoveryCLI` | `aquilia/cli/discovery_cli.py` | object | CLI interface for discovery operations. |
| `TypeClassifier` | `aquilia/cli/discovery_utils.py` | object | Classifies discovered classes as controllers, services, or other. |
| `EnhancedDiscovery` | `aquilia/cli/discovery_utils.py` | object | Enhanced discovery with intelligent classification and filtering. |
| `WorkspaceIntrospector` | `aquilia/cli/generators/deployment.py` | object | Introspects an Aquilia workspace to discover configuration needed |
| `DockerfileGenerator` | `aquilia/cli/generators/deployment.py` | object | Generates production-ready, multi-stage Dockerfile for Aquilia workspaces. |
| `ComposeGenerator` | `aquilia/cli/generators/deployment.py` | object | Generates production-ready docker-compose.yml for Aquilia workspaces. |
| `KubernetesGenerator` | `aquilia/cli/generators/deployment.py` | object | Generates production-ready Kubernetes manifests for Aquilia workspaces. |
| `NginxGenerator` | `aquilia/cli/generators/deployment.py` | object | Generate production-ready Nginx configuration for Aquilia. |
| `CIGenerator` | `aquilia/cli/generators/deployment.py` | object | Generate CI/CD pipelines (GitHub Actions, GitLab CI). |
| `PrometheusGenerator` | `aquilia/cli/generators/deployment.py` | object | Generate Prometheus configuration. |
| `GrafanaGenerator` | `aquilia/cli/generators/deployment.py` | object | Generate Grafana provisioning configuration. |
| `EnvGenerator` | `aquilia/cli/generators/deployment.py` | object | Generate .env templates for local and production. |
| `MakefileGenerator` | `aquilia/cli/generators/deployment.py` | object | Generate a production-ready Makefile for Aquilia workspaces. |
| `ModuleGenerator` | `aquilia/cli/generators/module.py` | object | Generate Aquilia module structure. |
| `WorkspaceGenerator` | `aquilia/cli/generators/workspace.py` | object | Generate Aquilia workspace structure. |
| `ModuleManifest` | `aquilia/cli/parsers/module.py` | object | Parsed module manifest (module.aq). |
| `WorkspaceManifest` | `aquilia/cli/parsers/workspace.py` | object | Parsed workspace manifest (aquilia.aq). |

## Public Function Summary

| Name | Source | Signature | Purpose |
| --- | --- | --- | --- |
| `main` | `aquilia/cli/__init__.py` | `def main()` | Wrapper to avoid eager import of __main__ which causes warnings with -m. |
| `cli` | `aquilia/cli/__main__.py` | `def cli(ctx, verbose: bool, quiet: bool, debug: bool, no_color: bool)` | Manifest-driven, artifact-first project orchestration. |
| `init` | `aquilia/cli/__main__.py` | `def init()` | Initialize new workspace or module. |
| `init_workspace` | `aquilia/cli/__main__.py` | `def init_workspace(ctx, name: str &#124; None, minimal: bool, template: str &#124; None, yes: bool)` | Create a new Aquilia workspace. |
| `add` | `aquilia/cli/__main__.py` | `def add()` | Add module to workspace. |
| `add_module` | `aquilia/cli/__main__.py` | `def add_module(ctx, name: str &#124; None, depends_on: tuple, fault_domain: str &#124; None, route_prefix: str &#124; None, with_tests: bool, minimal: bool, no_docker: bool, yes: bool)` | Add a new module to the workspace. |
| `generate` | `aquilia/cli/__main__.py` | `def generate()` | Generate code from templates. |
| `generate_controller` | `aquilia/cli/__main__.py` | `def generate_controller(ctx, name: str, prefix: str &#124; None, resource: str &#124; None, simple: bool, with_lifecycle: bool, test: bool, output: str &#124; None)` | Generate a new controller. |
| `validate` | `aquilia/cli/__main__.py` | `def validate(ctx, strict: bool, module: str &#124; None, as_json: bool)` | Validate workspace manifests. |
| `compile` | `aquilia/cli/__main__.py` | `def compile(ctx, watch: bool, output: str &#124; None)` | Compile manifests to artifacts. |
| `run` | `aquilia/cli/__main__.py` | `def run(ctx, mode: str, port, host, reload, skip_checks: bool)` | Start development server. |
| `serve` | `aquilia/cli/__main__.py` | `def serve(ctx, workers, bind, use_gunicorn: bool, timeout: int, graceful_timeout: int)` | Start production server. |
| `freeze` | `aquilia/cli/__main__.py` | `def freeze(ctx, output: str &#124; None, sign: bool)` | Freeze generated artifacts for production integrity checks. |
| `manifest` | `aquilia/cli/__main__.py` | `def manifest()` | Manage module manifests. |
| `manifest_update` | `aquilia/cli/__main__.py` | `def manifest_update(ctx, module: str, check: bool, freeze: bool)` | Update manifest with auto-discovered resources. |
| `inspect` | `aquilia/cli/__main__.py` | `def inspect()` | Inspect compiled artifacts. |
| `inspect_routes` | `aquilia/cli/__main__.py` | `def inspect_routes(ctx)` | Show compiled routes. |
| `inspect_di` | `aquilia/cli/__main__.py` | `def inspect_di(ctx)` | Show DI graph. |
| `inspect_modules` | `aquilia/cli/__main__.py` | `def inspect_modules(ctx)` | List all modules. |
| `inspect_faults` | `aquilia/cli/__main__.py` | `def inspect_faults(ctx)` | Show fault domains. |
| `inspect_config` | `aquilia/cli/__main__.py` | `def inspect_config(ctx)` | Show resolved configuration. |
| `migrate` | `aquilia/cli/__main__.py` | `def migrate(ctx, source: str, dry_run: bool)` | Migrate from legacy layout. |
| `doctor` | `aquilia/cli/__main__.py` | `def doctor(ctx, as_json: bool)` | Diagnose workspace issues. |
| `ws` | `aquilia/cli/__main__.py` | `def ws()` | WebSocket management commands. |
| `ws_inspect` | `aquilia/cli/__main__.py` | `def ws_inspect(ctx, artifacts_dir: str)` | Inspect compiled WebSocket namespaces. |
| `ws_broadcast` | `aquilia/cli/__main__.py` | `def ws_broadcast(ctx, namespace: str, room: str &#124; None, event: str, payload: str)` | Broadcast message to namespace or room. |
| `ws_gen_client` | `aquilia/cli/__main__.py` | `def ws_gen_client(ctx, lang: str, out: str, artifacts_dir: str)` | Generate TypeScript client SDK from compiled WebSocket artifacts. |
| `ws_purge_room` | `aquilia/cli/__main__.py` | `def ws_purge_room(ctx, namespace: str, room: str, redis_url: str &#124; None)` | Purge a room's state from the adapter. |
| `ws_kick` | `aquilia/cli/__main__.py` | `def ws_kick(ctx, conn: str, reason: str, redis_url: str &#124; None)` | Kick (disconnect) a WebSocket connection. |
| `discover` | `aquilia/cli/__main__.py` | `def discover(ctx, path: str &#124; None, sync: bool, dry_run: bool, as_json: bool)` | Inspect auto-discovered modules in workspace. |
| `analytics` | `aquilia/cli/__main__.py` | `def analytics(ctx, path: str &#124; None)` | Run discovery analytics and show health report. |
| `mail` | `aquilia/cli/__main__.py` | `def mail()` | AquilaMail -- test, inspect, and validate mail configuration. |
| `mail_check` | `aquilia/cli/__main__.py` | `def mail_check(ctx)` | Validate mail configuration and report issues. |
| `mail_send_test` | `aquilia/cli/__main__.py` | `def mail_send_test(ctx, to: str, subject: str &#124; None, body: str &#124; None)` | Send a test email to verify mail provider configuration. |
| `mail_inspect` | `aquilia/cli/__main__.py` | `def mail_inspect(ctx)` | Display current mail configuration as JSON. |
| `cache` | `aquilia/cli/__main__.py` | `def cache()` | AquilaCache -- check, inspect, clear, and view cache stats. |
| `cache_check` | `aquilia/cli/__main__.py` | `def cache_check(ctx)` | Validate cache configuration and test backend connectivity. |
| `cache_inspect` | `aquilia/cli/__main__.py` | `def cache_inspect(ctx)` | Display current cache configuration as JSON. |
| `cache_stats` | `aquilia/cli/__main__.py` | `def cache_stats(ctx)` | Display cache statistics from trace diagnostics. |
| `cache_clear` | `aquilia/cli/__main__.py` | `def cache_clear(ctx, namespace: str &#124; None)` | Clear all or namespace-scoped cache entries. |
| `i18n` | `aquilia/cli/__main__.py` | `def i18n()` | AquilaI18n -- init, check, inspect, extract, coverage, and compile. |
| `i18n_init` | `aquilia/cli/__main__.py` | `def i18n_init(ctx, locales: str, directory: str, format: str)` | Initialize i18n in the current workspace. |
| `i18n_check` | `aquilia/cli/__main__.py` | `def i18n_check(ctx)` | Validate i18n configuration and catalog structure. |
| `i18n_inspect` | `aquilia/cli/__main__.py` | `def i18n_inspect(ctx)` | Display current i18n configuration as JSON. |
| `i18n_extract` | `aquilia/cli/__main__.py` | `def i18n_extract(ctx, source_dirs: str, output: str, no_merge: bool)` | Extract translation keys from source files. |
| `i18n_coverage` | `aquilia/cli/__main__.py` | `def i18n_coverage(ctx)` | Show translation coverage per locale. |
| `i18n_compile` | `aquilia/cli/__main__.py` | `def i18n_compile(ctx, directory: str, output: str &#124; None)` | Compile JSON locale files to CROUS format. |
| `db` | `aquilia/cli/__main__.py` | `def db()` | Database and model ORM commands. |
| `db_makemigrations` | `aquilia/cli/__main__.py` | `def db_makemigrations(ctx, app: str &#124; None, migrations_dir: str, dsl: bool, fmt: str)` | Generate migration files from Python Model definitions. |
| `db_migrate` | `aquilia/cli/__main__.py` | `def db_migrate(ctx, migrations_dir: str, database_url: str &#124; None, database: str &#124; None, target: str &#124; None, fake: bool, plan: bool)` | Apply pending migrations to the database. |
| `db_dump` | `aquilia/cli/__main__.py` | `def db_dump(ctx, emit: str, output_dir: str &#124; None)` | Dump model schema -- annotated Python overview or raw SQL DDL. |
| `db_shell` | `aquilia/cli/__main__.py` | `def db_shell(ctx, database_url: str &#124; None)` | Open an async REPL with models pre-loaded. |
| `db_inspectdb` | `aquilia/cli/__main__.py` | `def db_inspectdb(ctx, database_url: str &#124; None, table: tuple, output: str &#124; None)` | Introspect database and generate Model definitions. |
| `db_showmigrations` | `aquilia/cli/__main__.py` | `def db_showmigrations(ctx, migrations_dir: str, database_url: str &#124; None, database: str &#124; None)` | Show all migrations and their applied/pending status. |
| `db_sqlmigrate` | `aquilia/cli/__main__.py` | `def db_sqlmigrate(ctx, migration_name: str, migrations_dir: str, database: str &#124; None)` | Display SQL statements for a specific migration. |
| `db_status` | `aquilia/cli/__main__.py` | `def db_status(ctx, database_url: str &#124; None)` | Show database status -- tables, row counts, columns. |
| `test` | `aquilia/cli/__main__.py` | `def test(ctx, paths: tuple, pattern: str &#124; None, markers: str &#124; None, coverage: bool, coverage_html: bool, failfast: bool)` | Run the test suite with Aquilia-aware defaults. |
| `admin` | `aquilia/cli/__main__.py` | `def admin()` | Admin dashboard management and diagnostics. |
| `admin_check` | `aquilia/cli/__main__.py` | `def admin_check(ctx, fix: bool, as_json: bool)` | Pre-flight check for admin dashboard dependencies. |
| `admin_createsuperuser` | `aquilia/cli/__main__.py` | `def admin_createsuperuser(ctx, username: str, email: str, password: str, first_name: str &#124; None, last_name: str &#124; None, no_input: bool)` | Create an admin superuser in the database. |
| `admin_createstaff` | `aquilia/cli/__main__.py` | `def admin_createstaff(ctx, username: str, email: str, password: str, first_name: str &#124; None, last_name: str &#124; None, no_input: bool)` | Create an admin staff user in the database. |
| `admin_listusers` | `aquilia/cli/__main__.py` | `def admin_listusers(ctx, database_url: str &#124; None, as_json: bool, active_only: bool)` | List all admin users. |
| `admin_changepassword` | `aquilia/cli/__main__.py` | `def admin_changepassword(ctx, username: str, password: str, database_url: str &#124; None)` | Change an admin user's password. |
| `admin_setup` | `aquilia/cli/__main__.py` | `def admin_setup(ctx, non_interactive: bool, database_url: str &#124; None)` | Auto-configure all admin dependencies in workspace.py. |
| `admin_status` | `aquilia/cli/__main__.py` | `def admin_status(ctx, database_url: str &#124; None)` | Show admin dashboard status and registered models. |
| `admin_audit` | `aquilia/cli/__main__.py` | `def admin_audit(ctx, limit: int, action: str &#124; None, user: str &#124; None)` | View admin audit trail. |
| `main` | `aquilia/cli/__main__.py` | `def main()` | Entry point for `aq` command. |
| `add_module` | `aquilia/cli/commands/add.py` | `def add_module(name: str, depends_on: list[str], fault_domain: str &#124; None = None, route_prefix: str &#124; None = None, with_tests: bool = False, minimal: bool = False, no_docker: bool = False, verbose: bool = False) -> Path` | Add a new module to the workspace. |
| `print_analysis_report` | `aquilia/cli/commands/analytics.py` | `def print_analysis_report(analysis: dict) -> None` | Pretty print analysis report. |
| `artifact_group` | `aquilia/cli/commands/artifacts.py` | `def artifact_group()` | Artifact management commands. |
| `artifact_list` | `aquilia/cli/commands/artifacts.py` | `def artifact_list(store_dir: str, kind: str, tag: str, json_output: bool)` | List all artifacts in the store. |
| `artifact_inspect` | `aquilia/cli/commands/artifacts.py` | `def artifact_inspect(name: str, version: str, store_dir: str, json_output: bool)` | Inspect an artifact by name. |
| `artifact_verify` | `aquilia/cli/commands/artifacts.py` | `def artifact_verify(name: str, version: str, store_dir: str)` | Verify the integrity of an artifact. |
| `artifact_verify_all` | `aquilia/cli/commands/artifacts.py` | `def artifact_verify_all(store_dir: str, json_output: bool)` | Verify integrity of ALL artifacts in the store. |
| `artifact_gc` | `aquilia/cli/commands/artifacts.py` | `def artifact_gc(store_dir: str, keep: tuple, dry_run: bool)` | Garbage-collect unreferenced artifacts. |
| `artifact_export` | `aquilia/cli/commands/artifacts.py` | `def artifact_export(store_dir: str, output: str, name: tuple)` | Export artifacts as a bundle. |
| `artifact_diff` | `aquilia/cli/commands/artifacts.py` | `def artifact_diff(name: str, version_a: str, version_b: str, store_dir: str)` | Show differences between two versions of an artifact. |
| `artifact_history` | `aquilia/cli/commands/artifacts.py` | `def artifact_history(name: str, store_dir: str)` | Show version history of an artifact. |
| `artifact_import` | `aquilia/cli/commands/artifacts.py` | `def artifact_import(bundle_path: str, store_dir: str)` | Import artifacts from a bundle file. |
| `artifact_count` | `aquilia/cli/commands/artifacts.py` | `def artifact_count(store_dir: str, kind: str)` | Count artifacts in the store. |
| `artifact_stats` | `aquilia/cli/commands/artifacts.py` | `def artifact_stats(store_dir: str, json_output: bool)` | Show aggregate statistics for the artifact store. |
| `cmd_cache_check` | `aquilia/cli/commands/cache.py` | `def cmd_cache_check(verbose: bool = False) -> None` | Validate cache configuration. |
| `cmd_cache_inspect` | `aquilia/cli/commands/cache.py` | `def cmd_cache_inspect(verbose: bool = False) -> None` | Display cache config as JSON. |
| `cmd_cache_stats` | `aquilia/cli/commands/cache.py` | `def cmd_cache_stats(verbose: bool = False) -> None` | Display cache statistics by connecting to the live cache backend. |
| `cmd_cache_clear` | `aquilia/cli/commands/cache.py` | `def cmd_cache_clear(namespace: str &#124; None = None, verbose: bool = False) -> None` | Clear cache entries. |
| `compile_workspace` | `aquilia/cli/commands/compile.py` | `def compile_workspace(output_dir: str &#124; None = None, watch: bool = False, verbose: bool = False, mode: str = 'dev', check_only: bool = False) -> list[str]` | Compile manifests to artifacts using the workspace compiler. |
| `deploy_options` | `aquilia/cli/commands/deploy_gen.py` | `def deploy_options(f)` | Decorator to add shared --force and --dry-run options to subcommands. |
| `deploy_gen_group` | `aquilia/cli/commands/deploy_gen.py` | `def deploy_gen_group(ctx, force: bool, dry_run: bool, yes: bool)` | Generate & execute production deployment files. |
| `deploy_dockerfile` | `aquilia/cli/commands/deploy_gen.py` | `def deploy_dockerfile(ctx, dev_mode: bool, mlops_mode: bool, output: str, force: bool, dry_run: bool)` | Generate production-ready Dockerfiles. |
| `deploy_compose` | `aquilia/cli/commands/deploy_gen.py` | `def deploy_compose(ctx, dev_mode: bool, monitoring: bool, output: str, force: bool, dry_run: bool)` | Generate docker-compose.yml for the workspace. |
| `deploy_kubernetes` | `aquilia/cli/commands/deploy_gen.py` | `def deploy_kubernetes(ctx, output: str, mlops: bool, force: bool, dry_run: bool)` | Generate production Kubernetes manifests. |
| `deploy_nginx` | `aquilia/cli/commands/deploy_gen.py` | `def deploy_nginx(ctx, output: str, force: bool, dry_run: bool)` | Generate Nginx reverse-proxy configuration. |
| `deploy_ci` | `aquilia/cli/commands/deploy_gen.py` | `def deploy_ci(ctx, provider: str, output: str &#124; None, force: bool, dry_run: bool)` | Generate CI/CD pipeline configuration. |
| `deploy_monitoring` | `aquilia/cli/commands/deploy_gen.py` | `def deploy_monitoring(ctx, output: str, force: bool, dry_run: bool)` | Generate monitoring configuration (Prometheus + Grafana). |
| `deploy_env` | `aquilia/cli/commands/deploy_gen.py` | `def deploy_env(ctx, output: str, force: bool, dry_run: bool)` | Generate .env.example template with all Aquilia settings. |
| `deploy_all` | `aquilia/cli/commands/deploy_gen.py` | `def deploy_all(ctx, output: str, monitoring: bool, ci_provider: str, force: bool, dry_run: bool)` | Generate ALL deployment files at once. |
| `deploy_makefile` | `aquilia/cli/commands/deploy_gen.py` | `def deploy_makefile(ctx, output: str, force: bool, dry_run: bool)` | Generate a self-documenting Makefile for dev & ops tasks. |
| `deploy_render` | `aquilia/cli/commands/deploy_gen.py` | `def deploy_render(ctx, image: str &#124; None, region: str &#124; None, plan: str &#124; None, num_instances: int &#124; None, service_name: str &#124; None, destroy: bool, show_status: bool, force: bool, dry_run: bool)` | Deploy to Render PaaS with a single command. |
| `main` | `aquilia/cli/commands/discover.py` | `def main()` | CLI entry point for discovery command. |
| `diagnose_workspace` | `aquilia/cli/commands/doctor.py` | `def diagnose_workspace(verbose: bool = False) -> list[str]` | Comprehensive workspace diagnostics. |
| `freeze_artifacts` | `aquilia/cli/commands/freeze.py` | `def freeze_artifacts(output_dir: str &#124; None = None, sign: bool = False, verbose: bool = False) -> str` | Generate immutable artifacts for production. |
| `cmd_i18n_init` | `aquilia/cli/commands/i18n.py` | `def cmd_i18n_init(locales: str &#124; None = None, directory: str = 'locales', format: str = 'json', verbose: bool = False) -> None` | Initialize i18n in the current workspace. |
| `cmd_i18n_check` | `aquilia/cli/commands/i18n.py` | `def cmd_i18n_check(verbose: bool = False) -> None` | Validate i18n configuration and catalogs. |
| `cmd_i18n_inspect` | `aquilia/cli/commands/i18n.py` | `def cmd_i18n_inspect() -> None` | Show current i18n configuration as JSON. |
| `cmd_i18n_extract` | `aquilia/cli/commands/i18n.py` | `def cmd_i18n_extract(source_dirs: str &#124; None = None, output: str = 'locales/en/messages.json', merge: bool = True, verbose: bool = False) -> None` | Extract translation keys from Python and template source files. |
| `cmd_i18n_coverage` | `aquilia/cli/commands/i18n.py` | `def cmd_i18n_coverage(verbose: bool = False) -> None` | Show translation coverage per locale. |
| `cmd_i18n_compile` | `aquilia/cli/commands/i18n.py` | `def cmd_i18n_compile(directory: str = 'locales', output: str &#124; None = None, verbose: bool = False) -> None` | Compile JSON translation files to CROUS binary format. |
| `create_workspace` | `aquilia/cli/commands/init.py` | `def create_workspace(name: str, minimal: bool = False, template: str &#124; None = None, verbose: bool = False, *, include_docker: bool = True, include_readme: bool = True, include_makefile: bool = True, include_tests: bool = True, include_gitignore: bool = True, include_license: str &#124; None = None) -> Path` | Create a new Aquilia workspace. |
| `inspect_routes` | `aquilia/cli/commands/inspect.py` | `def inspect_routes(verbose: bool = False) -> None` | Show all routes discovered from module manifests and controllers. |
| `inspect_di` | `aquilia/cli/commands/inspect.py` | `def inspect_di(verbose: bool = False) -> None` | Show the DI service graph from module manifests. |
| `inspect_modules` | `aquilia/cli/commands/inspect.py` | `def inspect_modules(verbose: bool = False) -> None` | List all modules with metadata. |
| `inspect_faults` | `aquilia/cli/commands/inspect.py` | `def inspect_faults(verbose: bool = False) -> None` | Show fault domains from module manifests. |
| `inspect_config` | `aquilia/cli/commands/inspect.py` | `def inspect_config(verbose: bool = False) -> None` | Show resolved configuration from workspace + config files. |
| `cmd_mail_check` | `aquilia/cli/commands/mail.py` | `def cmd_mail_check(verbose: bool = False) -> None` | Validate mail configuration. |
| `cmd_mail_send_test` | `aquilia/cli/commands/mail.py` | `def cmd_mail_send_test(to: str, subject: str &#124; None = None, body: str &#124; None = None, verbose: bool = False) -> None` | Send a test email. |
| `cmd_mail_inspect` | `aquilia/cli/commands/mail.py` | `def cmd_mail_inspect(verbose: bool = False) -> None` | Inspect mail configuration (JSON output). |
| `update_manifest` | `aquilia/cli/commands/manifest.py` | `def update_manifest(module_name: str, workspace_root: Path, check: bool = False, freeze: bool = False, verbose: bool = False)` | Update manifest.py with auto-discovered resources. |
| `migrate_legacy` | `aquilia/cli/commands/migrate.py` | `def migrate_legacy(dry_run: bool = False, verbose: bool = False) -> MigrationResult` | Migrate from legacy layout to Aquilia workspace. |
| `pack_group` | `aquilia/cli/commands/mlops_cmds.py` | `def pack_group()` | Model packaging commands. |
| `pack_save` | `aquilia/cli/commands/mlops_cmds.py` | `def pack_save(model_path, name, version, framework, env_lock, output, sign_key)` | Package a model into an .aquilia archive. |
| `pack_inspect` | `aquilia/cli/commands/mlops_cmds.py` | `def pack_inspect(archive_path)` | Display manifest of an .aquilia archive. |
| `pack_verify` | `aquilia/cli/commands/mlops_cmds.py` | `def pack_verify(archive_path, key)` | Verify the signature of an .aquilia archive. |
| `pack_push` | `aquilia/cli/commands/mlops_cmds.py` | `def pack_push(archive_path, registry, tag)` | Push a pack to a remote registry. |
| `model_group` | `aquilia/cli/commands/mlops_cmds.py` | `def model_group()` | Model serving commands. |
| `model_serve` | `aquilia/cli/commands/mlops_cmds.py` | `def model_serve(model_path, runtime, host, port, batch_size, batch_latency_ms)` | Serve a model with the built-in inference server. |
| `model_health` | `aquilia/cli/commands/mlops_cmds.py` | `def model_health(url)` | Check model server health. |
| `deploy_group` | `aquilia/cli/commands/mlops_cmds.py` | `def deploy_group()` | MLOps model deployment and rollout commands. |
| `deploy_rollout` | `aquilia/cli/commands/mlops_cmds.py` | `def deploy_rollout(model_name, from_version, to_version, strategy, steps, error_threshold)` | Start a progressive rollout. |
| `deploy_ci_template` | `aquilia/cli/commands/mlops_cmds.py` | `def deploy_ci_template(registry, output)` | Generate CI/CD templates (GitHub Actions + Dockerfile). |
| `observe_group` | `aquilia/cli/commands/mlops_cmds.py` | `def observe_group()` | Observability and monitoring commands. |
| `observe_drift` | `aquilia/cli/commands/mlops_cmds.py` | `def observe_drift(reference_csv, current_csv, method, threshold)` | Detect data drift between reference and current datasets. |
| `observe_metrics` | `aquilia/cli/commands/mlops_cmds.py` | `def observe_metrics(fmt)` | Export current metrics. |
| `export_group` | `aquilia/cli/commands/mlops_cmds.py` | `def export_group()` | Export and optimise models for edge / production. |
| `export_onnx` | `aquilia/cli/commands/mlops_cmds.py` | `def export_onnx(model_path, output, opset)` | Export a PyTorch model to ONNX. |
| `export_edge` | `aquilia/cli/commands/mlops_cmds.py` | `def export_edge(model_path, target, output)` | Export model for edge deployment. |
| `plugin_group` | `aquilia/cli/commands/mlops_cmds.py` | `def plugin_group()` | Plugin management commands. |
| `plugin_list` | `aquilia/cli/commands/mlops_cmds.py` | `def plugin_list()` | List discovered plugins. |
| `plugin_install` | `aquilia/cli/commands/mlops_cmds.py` | `def plugin_install(package_name)` | Install a plugin from PyPI. |
| `plugin_uninstall` | `aquilia/cli/commands/mlops_cmds.py` | `def plugin_uninstall(package_name)` | Uninstall a plugin. |
| `plugin_search` | `aquilia/cli/commands/mlops_cmds.py` | `def plugin_search(query, verified_only)` | Search the plugin marketplace. |
| `lineage_group` | `aquilia/cli/commands/mlops_cmds.py` | `def lineage_group()` | Model lineage and provenance tracking commands. |
| `lineage_show` | `aquilia/cli/commands/mlops_cmds.py` | `def lineage_show(fmt)` | Show the full model lineage graph. |
| `lineage_ancestors` | `aquilia/cli/commands/mlops_cmds.py` | `def lineage_ancestors(model_id)` | Show all ancestors (transitive parents) of a model. |
| `lineage_descendants` | `aquilia/cli/commands/mlops_cmds.py` | `def lineage_descendants(model_id)` | Show all descendants (derived models) of a model. |
| `lineage_path` | `aquilia/cli/commands/mlops_cmds.py` | `def lineage_path(from_model, to_model)` | Find derivation path between two models. |
| `experiment_group` | `aquilia/cli/commands/mlops_cmds.py` | `def experiment_group()` | A/B experiment management commands. |
| `experiment_create` | `aquilia/cli/commands/mlops_cmds.py` | `def experiment_create(experiment_id, description, arm)` | Create a new A/B experiment. |
| `experiment_list` | `aquilia/cli/commands/mlops_cmds.py` | `def experiment_list()` | List all experiments. |
| `experiment_conclude` | `aquilia/cli/commands/mlops_cmds.py` | `def experiment_conclude(experiment_id, winner)` | Conclude an experiment and optionally declare a winner. |
| `experiment_summary` | `aquilia/cli/commands/mlops_cmds.py` | `def experiment_summary(experiment_id)` | Show detailed experiment summary with per-arm metrics. |
| `cmd_makemigrations` | `aquilia/cli/commands/model_cmds.py` | `def cmd_makemigrations(app: str &#124; None = None, migrations_dir: str = 'migrations', verbose: bool = False, use_dsl: bool = True, migration_format: str = 'crous') -> list[Path]` | Generate migration files from Python Model definitions. |
| `cmd_migrate` | `aquilia/cli/commands/model_cmds.py` | `def cmd_migrate(migrations_dir: str = 'migrations', database_url: str = 'sqlite:///db.sqlite3', target: str &#124; None = None, verbose: bool = False, fake: bool = False, plan: bool = False, database: str &#124; None = None) -> list[str]` | Apply pending migrations to the database. |
| `cmd_model_dump` | `aquilia/cli/commands/model_cmds.py` | `def cmd_model_dump(emit: str = 'python', output_dir: str &#124; None = None, verbose: bool = False) -> str &#124; None` | Dump model schema information. |
| `cmd_shell` | `aquilia/cli/commands/model_cmds.py` | `def cmd_shell(database_url: str = 'sqlite:///db.sqlite3', verbose: bool = False) -> None` | Launch an async REPL with models and database pre-loaded. |
| `cmd_inspectdb` | `aquilia/cli/commands/model_cmds.py` | `def cmd_inspectdb(database_url: str = 'sqlite:///db.sqlite3', tables: list[str] &#124; None = None, verbose: bool = False) -> str` | Introspect an existing database and generate Model classes. |
| `cmd_showmigrations` | `aquilia/cli/commands/model_cmds.py` | `def cmd_showmigrations(migrations_dir: str = 'migrations', database_url: str = 'sqlite:///db.sqlite3', verbose: bool = False) -> list[dict]` | Show all migrations and their applied status against the database. |
| `cmd_sqlmigrate` | `aquilia/cli/commands/model_cmds.py` | `def cmd_sqlmigrate(migration_name: str, migrations_dir: str = 'migrations', verbose: bool = False, database: str &#124; None = None) -> str &#124; None` | Display the SQL statements for a specific migration. |
| `cmd_db_status` | `aquilia/cli/commands/model_cmds.py` | `def cmd_db_status(database_url: str = 'sqlite:///db.sqlite3', verbose: bool = False) -> dict` | Show database status -- tables, row counts, schema details. |
| `provider_group` | `aquilia/cli/commands/provider.py` | `def provider_group()` | Manage cloud provider authentication & configuration. |
| `render_group` | `aquilia/cli/commands/provider.py` | `def render_group()` | Render provider management. |
| `provider_login` | `aquilia/cli/commands/provider.py` | `def provider_login(provider_name: str, token: str &#124; None, region: str)` | Login to a cloud provider. |
| `provider_logout` | `aquilia/cli/commands/provider.py` | `def provider_logout(provider_name: str)` | Logout from a cloud provider. |
| `provider_status` | `aquilia/cli/commands/provider.py` | `def provider_status(provider_name: str)` | Show cloud provider authentication status. |
| `render_env_group` | `aquilia/cli/commands/provider.py` | `def render_env_group()` | Manage Render service environment variables. |
| `render_env_list` | `aquilia/cli/commands/provider.py` | `def render_env_list(service: str)` | List all environment variables for a Render service. |
| `render_env_set` | `aquilia/cli/commands/provider.py` | `def render_env_set(name: str, value: str &#124; None, service: str)` | Create or update an environment variable on a Render service. |
| `render_env_delete` | `aquilia/cli/commands/provider.py` | `def render_env_delete(name: str, service: str)` | Delete an environment variable from a Render service. |
| `run_dev_server` | `aquilia/cli/commands/run.py` | `def run_dev_server(mode: str = 'dev', host: str &#124; None = None, port: int &#124; None = None, reload: bool &#124; None = None, verbose: bool = False) -> None` | Start development server using uvicorn. |
| `serve_production` | `aquilia/cli/commands/serve.py` | `def serve_production(workers: int &#124; None = None, bind: str &#124; None = None, verbose: bool = False, use_gunicorn: bool = False, timeout: int = 120, graceful_timeout: int = 30) -> None` | Start production server. |
| `run_tests` | `aquilia/cli/commands/test.py` | `def run_tests(*, paths: list[str] &#124; None = None, pattern: str &#124; None = None, verbose: bool = False, coverage: bool = False, coverage_html: bool = False, failfast: bool = False, markers: str &#124; None = None, parallel: bool = False, last_failed: bool = False, no_header: bool = False, extra_args: list[str] &#124; None = None) -> int` | Execute the test suite via pytest. |
| `validate_workspace` | `aquilia/cli/commands/validate.py` | `def validate_workspace(strict: bool = False, module_filter: str &#124; None = None, verbose: bool = False) -> ValidationResult` | Validate workspace manifests using the Aquilary pipeline. |
| `cmd_ws_inspect` | `aquilia/cli/commands/ws.py` | `def cmd_ws_inspect(args: dict)` | Inspect compiled WebSocket namespaces. |
| `cmd_ws_broadcast` | `aquilia/cli/commands/ws.py` | `def cmd_ws_broadcast(args: dict)` | Broadcast message to namespace or room. |
| `cmd_ws_purge_room` | `aquilia/cli/commands/ws.py` | `def cmd_ws_purge_room(args: dict)` | Purge room state from adapter. |
| `cmd_ws_kick` | `aquilia/cli/commands/ws.py` | `def cmd_ws_kick(args: dict)` | Kick (disconnect) a connection. |
| `cmd_ws_gen_client` | `aquilia/cli/commands/ws.py` | `def cmd_ws_gen_client(args: dict)` | Generate TypeScript client SDK from artifacts. |
| `main` | `aquilia/cli/commands/ws.py` | `def main()` | Main CLI entry point. |
| `main` | `aquilia/cli/discovery_cli.py` | `def main()` | Main CLI entry point. |
| `generate_controller` | `aquilia/cli/generators/controller.py` | `def generate_controller(name: str, output_dir: str = 'controllers', prefix: str = None, resource: str = None, simple: bool = False, with_lifecycle: bool = False, test: bool = False) -> Path` | Generate a controller file. |
| `success` | `aquilia/cli/utils/colors.py` | `def success(message: str) -> None` | Print success message in green. |
| `error` | `aquilia/cli/utils/colors.py` | `def error(message: str) -> None` | Print error message in red. |
| `warning` | `aquilia/cli/utils/colors.py` | `def warning(message: str) -> None` | Print warning message in yellow. |
| `info` | `aquilia/cli/utils/colors.py` | `def info(message: str) -> None` | Print info message in cyan. |
| `dim` | `aquilia/cli/utils/colors.py` | `def dim(message: str) -> None` | Print dimmed message. |
| `bold` | `aquilia/cli/utils/colors.py` | `def bold(message: str) -> str` | Return bold-styled text (does not echo). |
| `accent` | `aquilia/cli/utils/colors.py` | `def accent(message: str) -> str` | Return magenta-accented text (does not echo). |
| `banner` | `aquilia/cli/utils/colors.py` | `def banner(title: str = 'Aquilia', subtitle: str = '', *, width: int &#124; None = None, fg: str = 'cyan', icon: str = '') -> None` | Print a bordered banner with centred title and optional icon. |
| `section` | `aquilia/cli/utils/colors.py` | `def section(title: str, *, width: int &#124; None = None, fg: str = 'cyan') -> None` | Print a section header with a ruled line. |
| `rule` | `aquilia/cli/utils/colors.py` | `def rule(*, char: str = _L_H, width: int &#124; None = None, fg: str = 'white') -> None` | Print a thin horizontal rule. |
| `kv` | `aquilia/cli/utils/colors.py` | `def kv(key: str, value: str, *, key_width: int = 20, indent: int = 2, key_fg: str = 'white', val_fg: str = 'cyan') -> None` | Print an aligned key-value pair. |
| `badge` | `aquilia/cli/utils/colors.py` | `def badge(label: str, *, style: str = 'ok') -> str` | Return an inline badge string (not echoed). |
| `tree_item` | `aquilia/cli/utils/colors.py` | `def tree_item(text: str, *, last: bool = False, depth: int = 0, fg: str = 'white') -> None` | Print an indented tree node. |
| `bullet` | `aquilia/cli/utils/colors.py` | `def bullet(text: str, *, indent: int = 2, fg: str = 'white') -> None` | Print a bulleted list item. |
| `step` | `aquilia/cli/utils/colors.py` | `def step(number: int, text: str, *, fg: str = 'cyan') -> None` | Print a numbered step. |
| `indent_echo` | `aquilia/cli/utils/colors.py` | `def indent_echo(text: str, *, level: int = 1) -> None` | Echo text with indentation (2 spaces per level). |
| `table` | `aquilia/cli/utils/colors.py` | `def table(headers: Sequence[str], rows: Sequence[Sequence[str]], *, col_widths: Sequence[int] &#124; None = None, header_fg: str = 'cyan', row_fg: str = 'white', indent: int = 2) -> None` | Print a minimal aligned table. |
| `panel` | `aquilia/cli/utils/colors.py` | `def panel(lines: Sequence[str], *, title: str = '', width: int &#124; None = None, fg: str = 'cyan', pad: int = 1) -> None` | Print a bordered panel. |
| `file_written` | `aquilia/cli/utils/colors.py` | `def file_written(label: str, *, verbose: bool = False, path: str = '') -> None` | Announce a generated file. |
| `file_skipped` | `aquilia/cli/utils/colors.py` | `def file_skipped(label: str, reason: str = 'exists') -> None` | Announce a skipped file. |
| `file_dry` | `aquilia/cli/utils/colors.py` | `def file_dry(label: str) -> None` | Announce a dry-run file. |
| `next_steps` | `aquilia/cli/utils/colors.py` | `def next_steps(steps_list: Sequence[str], *, title: str = 'Next steps') -> None` | Print a numbered next-steps panel. |
| `status_line` | `aquilia/cli/utils/colors.py` | `def status_line(icon: str, label: str, value: str, *, label_fg: str = 'white', value_fg: str = 'cyan', indent: int = 2) -> None` | Print a status indicator with icon, label and value. |
| `progress_bar` | `aquilia/cli/utils/colors.py` | `def progress_bar(label: str, current: int, total: int, *, width: int = 30, filled_fg: str = 'cyan', empty_fg: str = 'white') -> None` | Print a styled progress bar. |
| `detail_card` | `aquilia/cli/utils/colors.py` | `def detail_card(title: str, items: Sequence[tuple], *, icon: str = '', fg: str = 'cyan') -> None` | Print a compact detail card with key-value pairs. |
| `phase_header` | `aquilia/cli/utils/colors.py` | `def phase_header(phase_num: int, title: str, *, icon: str = '', fg: str = 'cyan') -> None` | Print a numbered phase header for multi-step flows. |
| `flow_header` | `aquilia/cli/utils/prompts.py` | `def flow_header(title: str, subtitle: str = '', *, fg: str = 'cyan') -> None` | Print a minimal flow header. |
| `flow_done` | `aquilia/cli/utils/prompts.py` | `def flow_done(message: str = 'Done.', *, fg: str = 'green') -> None` | Public function. |
| `ask` | `aquilia/cli/utils/prompts.py` | `def ask(label: str, *, default: str = '', required: bool = False, validator: Callable[[str], str &#124; None] &#124; None = None, hint: str = '') -> str` | Styled text input prompt with optional validation. |
| `ask_password` | `aquilia/cli/utils/prompts.py` | `def ask_password(label: str, *, confirm: bool = True, min_length: int = 4) -> str` | Styled hidden password input with optional confirmation. |
| `select` | `aquilia/cli/utils/prompts.py` | `def select(label: str, choices: Sequence[tuple[str, str]], *, default: int = 0) -> str` | Single-choice select menu with ↑↓ arrow-key navigation. |
| `multi_select` | `aquilia/cli/utils/prompts.py` | `def multi_select(label: str, choices: Sequence[tuple[str, str, bool]]) -> list[str]` | Multi-choice toggle menu with ↑↓ navigation and Space to toggle. |
| `confirm` | `aquilia/cli/utils/prompts.py` | `def confirm(label: str, *, default: bool = True) -> bool` | Styled yes/no prompt. |
| `recap` | `aquilia/cli/utils/prompts.py` | `def recap(items: Sequence[tuple[str, str]], *, title: str = 'Summary') -> None` | Print a labelled summary of selected options. |
| `find_workspace_root` | `aquilia/cli/utils/workspace.py` | `def find_workspace_root(start_path: Path &#124; None = None) -> Path &#124; None` | Find the Aquilia workspace root by looking for workspace.py or aquilia.py. |
| `get_workspace_file` | `aquilia/cli/utils/workspace.py` | `def get_workspace_file(workspace_root: Path) -> Path &#124; None` | Get the workspace configuration file path. |
| `is_python_workspace` | `aquilia/cli/utils/workspace.py` | `def is_python_workspace(workspace_root: Path) -> bool` | Check if workspace uses Python format (workspace.py or aquilia.py). |

## Constants

| Name | Source | Value or type |
| --- | --- | --- |
| `_DEFAULT_DB_URL` | `aquilia/cli/__main__.py` | `'sqlite:///db.sqlite3'` |
| `_NO_WORKSPACE_REQUIRED` | `aquilia/cli/__main__.py` | `frozenset({'init', 'version', '--version', '--help', 'help', 'doctor'})` |
| `_UVICORN_KNOWN_PARAMS` | `aquilia/cli/commands/run.py` | `frozenset({'host', 'port', 'uds', 'fd', 'loop', 'http', 'ws', 'ws_max_size', 'ws_max_queue', 'ws_ping_interval', 'ws_ping_timeout', 'ws_per_message_deflate', 'l` |
| `_TERM_WIDTH` | `aquilia/cli/utils/colors.py` | `int &#124; None` |
| `_H_TL` | `aquilia/cli/utils/colors.py` | `_G('┏', '+')` |
| `_H_TR` | `aquilia/cli/utils/colors.py` | `_G('┓', '+')` |
| `_H_BL` | `aquilia/cli/utils/colors.py` | `_G('┗', '+')` |
| `_H_BR` | `aquilia/cli/utils/colors.py` | `_G('┛', '+')` |
| `_H_H` | `aquilia/cli/utils/colors.py` | `_G('-', '-')` |
| `_H_V` | `aquilia/cli/utils/colors.py` | `_G('┃', ' &#124; ')` |
| `_L_TL` | `aquilia/cli/utils/colors.py` | `_G('┌', '+')` |
| `_L_TR` | `aquilia/cli/utils/colors.py` | `_G('┐', '+')` |
| `_L_BL` | `aquilia/cli/utils/colors.py` | `_G('└', '+')` |
| `_L_BR` | `aquilia/cli/utils/colors.py` | `_G('┘', '+')` |
| `_L_H` | `aquilia/cli/utils/colors.py` | `_G('-', '-')` |
| `_L_V` | `aquilia/cli/utils/colors.py` | `_G('│', ' &#124; ')` |
| `_L_LT` | `aquilia/cli/utils/colors.py` | `_G('├', '+')` |
| `_L_RT` | `aquilia/cli/utils/colors.py` | `_G('┤', '+')` |
| `_BULLET` | `aquilia/cli/utils/colors.py` | `_G('•', '*')` |
| `_ARROW` | `aquilia/cli/utils/colors.py` | `_G('->', '->')` |
| `_CHECK` | `aquilia/cli/utils/colors.py` | `_G('✔', '[ok]')` |
| `_CROSS` | `aquilia/cli/utils/colors.py` | `_G('✘', '[x]')` |
| `_CIRCLE` | `aquilia/cli/utils/colors.py` | `_G('○', 'o')` |
| `_DOT` | `aquilia/cli/utils/colors.py` | `_G('·', '.')` |
| `_DASH` | `aquilia/cli/utils/colors.py` | `_G('-', '-')` |
| `_ROCKET` | `aquilia/cli/utils/colors.py` | `_G('🚀', '>>')` |
| `_LOCK` | `aquilia/cli/utils/colors.py` | `_G('🔒', '[#]')` |
| `_GLOBE` | `aquilia/cli/utils/colors.py` | `_G('🌐', '(o)')` |
| `_PKG` | `aquilia/cli/utils/colors.py` | `_G('📦', '[p]')` |
| `_GEAR` | `aquilia/cli/utils/colors.py` | `_G('⚙', '[*]')` |
| `_BOLT` | `aquilia/cli/utils/colors.py` | `_G('⚡', '!')` |
| `_SHIELD` | `aquilia/cli/utils/colors.py` | `_G('🛡', '[S]')` |
| `_LINK` | `aquilia/cli/utils/colors.py` | `_G('🔗', '[@]')` |
| `_CLOCK` | `aquilia/cli/utils/colors.py` | `_G('🕑', '[t]')` |
| `_SPARK` | `aquilia/cli/utils/colors.py` | `_G('✨', '*')` |
| `_WARN` | `aquilia/cli/utils/colors.py` | `_G('⚠', '[!]')` |
| `_CLOUD` | `aquilia/cli/utils/colors.py` | `_G('☁', '(c)')` |
| `_KEY` | `aquilia/cli/utils/colors.py` | `_G('🔑', '[k]')` |
| `_EYE` | `aquilia/cli/utils/colors.py` | `_G('👁', '(e)')` |
| `_DIAMOND` | `aquilia/cli/utils/colors.py` | `_G('◆', '*')` |
| `_IS_WINDOWS` | `aquilia/cli/utils/prompts.py` | `bool` |
| `_RADIO_ON` | `aquilia/cli/utils/prompts.py` | `_G('●', '(*)')` |
| `_RADIO_OFF` | `aquilia/cli/utils/prompts.py` | `_G('○', '( )')` |
| `_CHECK_ON` | `aquilia/cli/utils/prompts.py` | `_G('◼', '[x]')` |
| `_CHECK_OFF` | `aquilia/cli/utils/prompts.py` | `_G('◻', '[ ]')` |
| `_CLEAR_LINE` | `aquilia/cli/utils/prompts.py` | `'\x1b[2K'` |
| `_HIDE_CURSOR` | `aquilia/cli/utils/prompts.py` | `'\x1b[?25l'` |
| `_SHOW_CURSOR` | `aquilia/cli/utils/prompts.py` | `'\x1b[?25h'` |
| `_STDIN_FD` | `aquilia/cli/utils/prompts.py` | `int` |

## Detailed Classes And Methods

### Class: `AquiliaGroup`

- Source: `aquilia/cli/__main__.py`
- Bases: `click.Group`
- Summary: Click group subclass with branded help output.

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `format_help` | `def format_help(self, ctx: click.Context, formatter: click.HelpFormatter) -> None` |  | Override to add Aquilia branding to the top-level help. |
| `format_commands` | `def format_commands(self, ctx: click.Context, formatter: click.HelpFormatter) -> None` |  | Format command listing with categorised groups. |

### Class: `DiscoveryAnalytics`

- Source: `aquilia/cli/commands/analytics.py`
- Bases: `object`
- Summary: Analyze discovered modules and provide insights.

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `analyze` | `def analyze(self) -> dict` |  | Run full discovery analysis. |
| `get_cached_analysis` | `def get_cached_analysis(self, max_age_seconds: int = 3600) -> dict &#124; None` |  | Get cached analysis if fresh. |

### Class: `DiscoveryInspector`

- Source: `aquilia/cli/commands/discover.py`
- Bases: `object`
- Summary: Inspect, validate, and auto-sync discovered modules.

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `inspect` | `def inspect(self, verbose: bool = False, sync: bool = False, dry_run: bool = False) -> None` |  | Run discovery inspection and optionally sync manifests. |

### Class: `DiagnosticResult`

- Source: `aquilia/cli/commands/doctor.py`
- Bases: `object`
- Decorators: `dataclass`
- Summary: Structured diagnostic result.

Attributes and fields:

| Name | Type | Default |
| --- | --- | --- |
| `category` | `str` |  |
| `label` | `str` |  |
| `passed` | `bool` |  |
| `detail` | `str` | `''` |

### Class: `DiagnosticReport`

- Source: `aquilia/cli/commands/doctor.py`
- Bases: `object`
- Decorators: `dataclass`
- Summary: Complete diagnostic report.

Attributes and fields:

| Name | Type | Default |
| --- | --- | --- |
| `results` | `list[DiagnosticResult]` | `field(default_factory=list)` |
| `issues` | `list[str]` | `field(default_factory=list)` |
| `warnings` | `list[str]` | `field(default_factory=list)` |

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `passed` | `def passed(self) -> bool` | property | Method. |
| `add` | `def add(self, category: str, label: str, passed: bool, detail: str = '') -> None` |  | Method. |
| `warn` | `def warn(self, message: str) -> None` |  | Method. |

### Class: `MigrationResult`

- Source: `aquilia/cli/commands/migrate.py`
- Bases: `object`
- Decorators: `dataclass`
- Summary: Result of migration operation.

Attributes and fields:

| Name | Type | Default |
| --- | --- | --- |
| `changes` | `list[str]` | `field(default_factory=list)` |

### Class: `ValidationResult`

- Source: `aquilia/cli/commands/validate.py`
- Bases: `object`
- Decorators: `dataclass`
- Summary: Result of manifest validation.

Attributes and fields:

| Name | Type | Default |
| --- | --- | --- |
| `is_valid` | `bool` |  |
| `module_count` | `int` |  |
| `route_count` | `int` |  |
| `provider_count` | `int` |  |
| `faults` | `list[str]` |  |
| `warnings` | `list[str]` | `field(default_factory=list)` |
| `fingerprint` | `str &#124; None` | `None` |

### Class: `WorkspaceCompiler`

- Source: `aquilia/cli/compilers/workspace.py`
- Bases: `object`
- Summary: Compile workspace manifests to artifacts via the unified artifact system.

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `compile` | `def compile(self) -> list[Path]` |  | Compile workspace to artifacts. |

### Class: `DiscoveryCLI`

- Source: `aquilia/cli/discovery_cli.py`
- Bases: `object`
- Summary: CLI interface for discovery operations.

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `discover` | `def discover(workspace: str, path: str &#124; None = None, verbose: bool = False, sync: bool = False, dry_run: bool = False) -> None` | staticmethod | Discover and list all modules. Optionally sync manifests. |
| `analyze` | `def analyze(workspace: str, path: str &#124; None = None) -> None` | staticmethod | Run analytics on discovered modules. |
| `validate` | `def validate(workspace: str, path: str &#124; None = None) -> None` | staticmethod | Validate all discovered modules. |
| `dependencies` | `def dependencies(workspace: str, path: str &#124; None = None) -> None` | staticmethod | Show module dependency graph. |

### Class: `TypeClassifier`

- Source: `aquilia/cli/discovery_utils.py`
- Bases: `object`
- Summary: Classifies discovered classes as controllers, services, or other.

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `is_controller_class` | `def is_controller_class(cls: type) -> bool` | staticmethod | Determine if a class is a controller. |
| `is_service_class` | `def is_service_class(cls: type) -> bool` | staticmethod | Determine if a class is a service/provider. |
| `classify` | `def classify(cls: type) -> str &#124; None` | staticmethod | Classify a discovered class. |

### Class: `EnhancedDiscovery`

- Source: `aquilia/cli/discovery_utils.py`
- Bases: `object`
- Summary: Enhanced discovery with intelligent classification and filtering.

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `discover_module_controllers_and_services` | `def discover_module_controllers_and_services(self, base_package: str, module_name: str) -> tuple[list[Any], list[Any], list[Any]]` |  | Discover controllers, services, and socket controllers using static analysis first, |
| `clean_manifest_lists` | `def clean_manifest_lists(self, manifest_content: str, discovered_controllers: list[dict[str, Any]], discovered_services: list[dict[str, Any]], module_dir: Path &#124; None = None, discovered_sockets: list[dict[str, Any]] &#124; None = None) -> tuple[str, int, int]` |  | Clean and update manifest.py with properly classified items. |

### Class: `WorkspaceIntrospector`

- Source: `aquilia/cli/generators/deployment.py`
- Bases: `object`
- Summary: Introspects an Aquilia workspace to discover configuration needed

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `introspect` | `def introspect(self) -> dict[str, Any]` |  | Return a full introspection dictionary. |

### Class: `DockerfileGenerator`

- Source: `aquilia/cli/generators/deployment.py`
- Bases: `object`
- Summary: Generates production-ready, multi-stage Dockerfile for Aquilia workspaces.

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `generate_dockerfile` | `def generate_dockerfile(self) -> str` |  | Generate production Dockerfile. |
| `generate_dockerfile_dev` | `def generate_dockerfile_dev(self) -> str` |  | Generate development Dockerfile with hot-reload. |
| `generate_dockerfile_mlops` | `def generate_dockerfile_mlops(self) -> str` |  | Generate MLOps model-serving Dockerfile with optional GPU support. |
| `generate_dockerignore` | `def generate_dockerignore(self) -> str` |  | Generate .dockerignore for efficient builds. |

### Class: `ComposeGenerator`

- Source: `aquilia/cli/generators/deployment.py`
- Bases: `object`
- Summary: Generates production-ready docker-compose.yml for Aquilia workspaces.

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `generate_compose` | `def generate_compose(self, *, include_monitoring: bool = False) -> str` |  | Generate docker-compose.yml. |
| `generate_compose_dev` | `def generate_compose_dev(self) -> str` |  | Generate docker-compose.dev.yml for development. |

### Class: `KubernetesGenerator`

- Source: `aquilia/cli/generators/deployment.py`
- Bases: `object`
- Summary: Generates production-ready Kubernetes manifests for Aquilia workspaces.

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `generate_namespace` | `def generate_namespace(self) -> str` |  | Generate Kubernetes namespace. |
| `generate_configmap` | `def generate_configmap(self) -> str` |  | Generate ConfigMap for non-secret configuration. |
| `generate_secret` | `def generate_secret(self) -> str` |  | Generate Secret template for credentials. |
| `generate_deployment` | `def generate_deployment(self) -> str` |  | Generate production Deployment manifest. |
| `generate_service` | `def generate_service(self) -> str` |  | Generate Service manifest. |
| `generate_ingress` | `def generate_ingress(self) -> str` |  | Generate Ingress manifest with TLS. |
| `generate_hpa` | `def generate_hpa(self) -> str` |  | Generate HPA for auto-scaling. |
| `generate_pdb` | `def generate_pdb(self) -> str` |  | Generate PodDisruptionBudget. |
| `generate_network_policy` | `def generate_network_policy(self) -> str` |  | Generate NetworkPolicy for pod-level firewall. |
| `generate_service_account` | `def generate_service_account(self) -> str` |  | Generate ServiceAccount with minimal RBAC. |
| `generate_mlops_manifests` | `def generate_mlops_manifests(self) -> str` |  | Generate MLOps-specific Kubernetes manifests. |
| `generate_cronjob` | `def generate_cronjob(self) -> str` |  | Generate CronJob for periodic maintenance tasks. |
| `generate_pvc` | `def generate_pvc(self) -> str` |  | Generate PersistentVolumeClaim for application data. |
| `generate_all` | `def generate_all(self) -> dict[str, str]` |  | Generate all Kubernetes manifests as a dict of filename -> content. |

### Class: `NginxGenerator`

- Source: `aquilia/cli/generators/deployment.py`
- Bases: `object`
- Summary: Generate production-ready Nginx configuration for Aquilia.

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `generate_nginx_conf` | `def generate_nginx_conf(self) -> str` |  | Generate main nginx.conf. |

### Class: `CIGenerator`

- Source: `aquilia/cli/generators/deployment.py`
- Bases: `object`
- Summary: Generate CI/CD pipelines (GitHub Actions, GitLab CI).

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `generate_github_actions` | `def generate_github_actions(self) -> str` |  | Generate GitHub Actions CI/CD pipeline. |
| `generate_gitlab_ci` | `def generate_gitlab_ci(self) -> str` |  | Generate GitLab CI/CD pipeline. |

### Class: `PrometheusGenerator`

- Source: `aquilia/cli/generators/deployment.py`
- Bases: `object`
- Summary: Generate Prometheus configuration.

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `generate_prometheus_yml` | `def generate_prometheus_yml(self) -> str` |  | Generate prometheus.yml config. |

### Class: `GrafanaGenerator`

- Source: `aquilia/cli/generators/deployment.py`
- Bases: `object`
- Summary: Generate Grafana provisioning configuration.

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `generate_datasource` | `def generate_datasource(self) -> str` |  | Generate Grafana datasource provisioning. |
| `generate_dashboard_provisioning` | `def generate_dashboard_provisioning(self) -> str` |  | Generate Grafana dashboard provisioning config. |

### Class: `EnvGenerator`

- Source: `aquilia/cli/generators/deployment.py`
- Bases: `object`
- Summary: Generate .env templates for local and production.

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `generate_env_example` | `def generate_env_example(self) -> str` |  | Generate .env.example template. |

### Class: `MakefileGenerator`

- Source: `aquilia/cli/generators/deployment.py`
- Bases: `object`
- Summary: Generate a production-ready Makefile for Aquilia workspaces.

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `generate_makefile` | `def generate_makefile(self) -> str` |  | Generate Makefile with comprehensive targets. |

### Class: `ModuleGenerator`

- Source: `aquilia/cli/generators/module.py`
- Bases: `object`
- Summary: Generate Aquilia module structure.

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `generate` | `def generate(self) -> None` |  | Generate module structure. |

### Class: `WorkspaceGenerator`

- Source: `aquilia/cli/generators/workspace.py`
- Bases: `object`
- Summary: Generate Aquilia workspace structure.

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `generate` | `def generate(self) -> None` |  | Generate workspace structure. |
| `generate_workspace_module_config` | `def generate_workspace_module_config(self, discovered_modules: dict) -> str` |  | Generate workspace module configuration as pointers to per-module manifests. |
| `update_workspace_config` | `def update_workspace_config(self, workspace_path: Path, discovered_modules: dict) -> None` |  | Update workspace.py with auto-discovered module configurations. |

### Class: `ModuleManifest`

- Source: `aquilia/cli/parsers/module.py`
- Bases: `object`
- Decorators: `dataclass`
- Summary: Parsed module manifest (module.aq).

Attributes and fields:

| Name | Type | Default |
| --- | --- | --- |
| `name` | `str` |  |
| `version` | `str` |  |
| `description` | `str` | `''` |
| `route_prefix` | `str` | `'/'` |
| `fault_domain` | `str` | `'GENERIC'` |
| `depends_on` | `list[str]` | `field(default_factory=list)` |
| `providers` | `list[dict[str, Any]]` | `field(default_factory=list)` |
| `routes` | `list[dict[str, Any]]` | `field(default_factory=list)` |

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `from_file` | `def from_file(cls, path: Path) -> 'ModuleManifest'` | classmethod | Load module manifest from file. |

### Class: `WorkspaceManifest`

- Source: `aquilia/cli/parsers/workspace.py`
- Bases: `object`
- Decorators: `dataclass`
- Summary: Parsed workspace manifest (aquilia.aq).

Attributes and fields:

| Name | Type | Default |
| --- | --- | --- |
| `name` | `str` |  |
| `version` | `str` |  |
| `description` | `str` | `''` |
| `modules` | `list[str]` | `field(default_factory=list)` |
| `runtime` | `dict[str, Any]` | `field(default_factory=dict)` |
| `integrations` | `dict[str, Any]` | `field(default_factory=dict)` |

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `from_file` | `def from_file(cls, path: Path) -> 'WorkspaceManifest'` | classmethod | Load workspace manifest from file. |
| `add_module` | `def add_module(self, name: str, config: dict[str, Any]) -> None` |  | Add module to manifest. |
| `save` | `def save(self, path: Path) -> None` |  | Save manifest to file. |

## Functions

| Name | Source | Signature | Purpose |
| --- | --- | --- | --- |
| `main` | `aquilia/cli/__init__.py` | `def main()` | Wrapper to avoid eager import of __main__ which causes warnings with -m. |
| `cli` | `aquilia/cli/__main__.py` | `def cli(ctx, verbose: bool, quiet: bool, debug: bool, no_color: bool)` | Manifest-driven, artifact-first project orchestration. |
| `init` | `aquilia/cli/__main__.py` | `def init()` | Initialize new workspace or module. |
| `init_workspace` | `aquilia/cli/__main__.py` | `def init_workspace(ctx, name: str &#124; None, minimal: bool, template: str &#124; None, yes: bool)` | Create a new Aquilia workspace. |
| `add` | `aquilia/cli/__main__.py` | `def add()` | Add module to workspace. |
| `add_module` | `aquilia/cli/__main__.py` | `def add_module(ctx, name: str &#124; None, depends_on: tuple, fault_domain: str &#124; None, route_prefix: str &#124; None, with_tests: bool, minimal: bool, no_docker: bool, yes: bool)` | Add a new module to the workspace. |
| `generate` | `aquilia/cli/__main__.py` | `def generate()` | Generate code from templates. |
| `generate_controller` | `aquilia/cli/__main__.py` | `def generate_controller(ctx, name: str, prefix: str &#124; None, resource: str &#124; None, simple: bool, with_lifecycle: bool, test: bool, output: str &#124; None)` | Generate a new controller. |
| `validate` | `aquilia/cli/__main__.py` | `def validate(ctx, strict: bool, module: str &#124; None, as_json: bool)` | Validate workspace manifests. |
| `compile` | `aquilia/cli/__main__.py` | `def compile(ctx, watch: bool, output: str &#124; None)` | Compile manifests to artifacts. |
| `run` | `aquilia/cli/__main__.py` | `def run(ctx, mode: str, port, host, reload, skip_checks: bool)` | Start development server. |
| `serve` | `aquilia/cli/__main__.py` | `def serve(ctx, workers, bind, use_gunicorn: bool, timeout: int, graceful_timeout: int)` | Start production server. |
| `freeze` | `aquilia/cli/__main__.py` | `def freeze(ctx, output: str &#124; None, sign: bool)` | Freeze generated artifacts for production integrity checks. |
| `manifest` | `aquilia/cli/__main__.py` | `def manifest()` | Manage module manifests. |
| `manifest_update` | `aquilia/cli/__main__.py` | `def manifest_update(ctx, module: str, check: bool, freeze: bool)` | Update manifest with auto-discovered resources. |
| `inspect` | `aquilia/cli/__main__.py` | `def inspect()` | Inspect compiled artifacts. |
| `inspect_routes` | `aquilia/cli/__main__.py` | `def inspect_routes(ctx)` | Show compiled routes. |
| `inspect_di` | `aquilia/cli/__main__.py` | `def inspect_di(ctx)` | Show DI graph. |
| `inspect_modules` | `aquilia/cli/__main__.py` | `def inspect_modules(ctx)` | List all modules. |
| `inspect_faults` | `aquilia/cli/__main__.py` | `def inspect_faults(ctx)` | Show fault domains. |
| `inspect_config` | `aquilia/cli/__main__.py` | `def inspect_config(ctx)` | Show resolved configuration. |
| `migrate` | `aquilia/cli/__main__.py` | `def migrate(ctx, source: str, dry_run: bool)` | Migrate from legacy layout. |
| `doctor` | `aquilia/cli/__main__.py` | `def doctor(ctx, as_json: bool)` | Diagnose workspace issues. |
| `ws` | `aquilia/cli/__main__.py` | `def ws()` | WebSocket management commands. |
| `ws_inspect` | `aquilia/cli/__main__.py` | `def ws_inspect(ctx, artifacts_dir: str)` | Inspect compiled WebSocket namespaces. |
| `ws_broadcast` | `aquilia/cli/__main__.py` | `def ws_broadcast(ctx, namespace: str, room: str &#124; None, event: str, payload: str)` | Broadcast message to namespace or room. |
| `ws_gen_client` | `aquilia/cli/__main__.py` | `def ws_gen_client(ctx, lang: str, out: str, artifacts_dir: str)` | Generate TypeScript client SDK from compiled WebSocket artifacts. |
| `ws_purge_room` | `aquilia/cli/__main__.py` | `def ws_purge_room(ctx, namespace: str, room: str, redis_url: str &#124; None)` | Purge a room's state from the adapter. |
| `ws_kick` | `aquilia/cli/__main__.py` | `def ws_kick(ctx, conn: str, reason: str, redis_url: str &#124; None)` | Kick (disconnect) a WebSocket connection. |
| `discover` | `aquilia/cli/__main__.py` | `def discover(ctx, path: str &#124; None, sync: bool, dry_run: bool, as_json: bool)` | Inspect auto-discovered modules in workspace. |
| `analytics` | `aquilia/cli/__main__.py` | `def analytics(ctx, path: str &#124; None)` | Run discovery analytics and show health report. |
| `mail` | `aquilia/cli/__main__.py` | `def mail()` | AquilaMail -- test, inspect, and validate mail configuration. |
| `mail_check` | `aquilia/cli/__main__.py` | `def mail_check(ctx)` | Validate mail configuration and report issues. |
| `mail_send_test` | `aquilia/cli/__main__.py` | `def mail_send_test(ctx, to: str, subject: str &#124; None, body: str &#124; None)` | Send a test email to verify mail provider configuration. |
| `mail_inspect` | `aquilia/cli/__main__.py` | `def mail_inspect(ctx)` | Display current mail configuration as JSON. |
| `cache` | `aquilia/cli/__main__.py` | `def cache()` | AquilaCache -- check, inspect, clear, and view cache stats. |
| `cache_check` | `aquilia/cli/__main__.py` | `def cache_check(ctx)` | Validate cache configuration and test backend connectivity. |
| `cache_inspect` | `aquilia/cli/__main__.py` | `def cache_inspect(ctx)` | Display current cache configuration as JSON. |
| `cache_stats` | `aquilia/cli/__main__.py` | `def cache_stats(ctx)` | Display cache statistics from trace diagnostics. |
| `cache_clear` | `aquilia/cli/__main__.py` | `def cache_clear(ctx, namespace: str &#124; None)` | Clear all or namespace-scoped cache entries. |
| `i18n` | `aquilia/cli/__main__.py` | `def i18n()` | AquilaI18n -- init, check, inspect, extract, coverage, and compile. |
| `i18n_init` | `aquilia/cli/__main__.py` | `def i18n_init(ctx, locales: str, directory: str, format: str)` | Initialize i18n in the current workspace. |
| `i18n_check` | `aquilia/cli/__main__.py` | `def i18n_check(ctx)` | Validate i18n configuration and catalog structure. |
| `i18n_inspect` | `aquilia/cli/__main__.py` | `def i18n_inspect(ctx)` | Display current i18n configuration as JSON. |
| `i18n_extract` | `aquilia/cli/__main__.py` | `def i18n_extract(ctx, source_dirs: str, output: str, no_merge: bool)` | Extract translation keys from source files. |
| `i18n_coverage` | `aquilia/cli/__main__.py` | `def i18n_coverage(ctx)` | Show translation coverage per locale. |
| `i18n_compile` | `aquilia/cli/__main__.py` | `def i18n_compile(ctx, directory: str, output: str &#124; None)` | Compile JSON locale files to CROUS format. |
| `db` | `aquilia/cli/__main__.py` | `def db()` | Database and model ORM commands. |
| `db_makemigrations` | `aquilia/cli/__main__.py` | `def db_makemigrations(ctx, app: str &#124; None, migrations_dir: str, dsl: bool, fmt: str)` | Generate migration files from Python Model definitions. |
| `db_migrate` | `aquilia/cli/__main__.py` | `def db_migrate(ctx, migrations_dir: str, database_url: str &#124; None, database: str &#124; None, target: str &#124; None, fake: bool, plan: bool)` | Apply pending migrations to the database. |
| `db_dump` | `aquilia/cli/__main__.py` | `def db_dump(ctx, emit: str, output_dir: str &#124; None)` | Dump model schema -- annotated Python overview or raw SQL DDL. |
| `db_shell` | `aquilia/cli/__main__.py` | `def db_shell(ctx, database_url: str &#124; None)` | Open an async REPL with models pre-loaded. |
| `db_inspectdb` | `aquilia/cli/__main__.py` | `def db_inspectdb(ctx, database_url: str &#124; None, table: tuple, output: str &#124; None)` | Introspect database and generate Model definitions. |
| `db_showmigrations` | `aquilia/cli/__main__.py` | `def db_showmigrations(ctx, migrations_dir: str, database_url: str &#124; None, database: str &#124; None)` | Show all migrations and their applied/pending status. |
| `db_sqlmigrate` | `aquilia/cli/__main__.py` | `def db_sqlmigrate(ctx, migration_name: str, migrations_dir: str, database: str &#124; None)` | Display SQL statements for a specific migration. |
| `db_status` | `aquilia/cli/__main__.py` | `def db_status(ctx, database_url: str &#124; None)` | Show database status -- tables, row counts, columns. |
| `test` | `aquilia/cli/__main__.py` | `def test(ctx, paths: tuple, pattern: str &#124; None, markers: str &#124; None, coverage: bool, coverage_html: bool, failfast: bool)` | Run the test suite with Aquilia-aware defaults. |
| `admin` | `aquilia/cli/__main__.py` | `def admin()` | Admin dashboard management and diagnostics. |
| `admin_check` | `aquilia/cli/__main__.py` | `def admin_check(ctx, fix: bool, as_json: bool)` | Pre-flight check for admin dashboard dependencies. |
| `admin_createsuperuser` | `aquilia/cli/__main__.py` | `def admin_createsuperuser(ctx, username: str, email: str, password: str, first_name: str &#124; None, last_name: str &#124; None, no_input: bool)` | Create an admin superuser in the database. |
| `admin_createstaff` | `aquilia/cli/__main__.py` | `def admin_createstaff(ctx, username: str, email: str, password: str, first_name: str &#124; None, last_name: str &#124; None, no_input: bool)` | Create an admin staff user in the database. |
| `admin_listusers` | `aquilia/cli/__main__.py` | `def admin_listusers(ctx, database_url: str &#124; None, as_json: bool, active_only: bool)` | List all admin users. |
| `admin_changepassword` | `aquilia/cli/__main__.py` | `def admin_changepassword(ctx, username: str, password: str, database_url: str &#124; None)` | Change an admin user's password. |
| `admin_setup` | `aquilia/cli/__main__.py` | `def admin_setup(ctx, non_interactive: bool, database_url: str &#124; None)` | Auto-configure all admin dependencies in workspace.py. |
| `admin_status` | `aquilia/cli/__main__.py` | `def admin_status(ctx, database_url: str &#124; None)` | Show admin dashboard status and registered models. |
| `admin_audit` | `aquilia/cli/__main__.py` | `def admin_audit(ctx, limit: int, action: str &#124; None, user: str &#124; None)` | View admin audit trail. |
| `main` | `aquilia/cli/__main__.py` | `def main()` | Entry point for `aq` command. |
| `add_module` | `aquilia/cli/commands/add.py` | `def add_module(name: str, depends_on: list[str], fault_domain: str &#124; None = None, route_prefix: str &#124; None = None, with_tests: bool = False, minimal: bool = False, no_docker: bool = False, verbose: bool = False) -> Path` | Add a new module to the workspace. |
| `print_analysis_report` | `aquilia/cli/commands/analytics.py` | `def print_analysis_report(analysis: dict) -> None` | Pretty print analysis report. |
| `artifact_group` | `aquilia/cli/commands/artifacts.py` | `def artifact_group()` | Artifact management commands. |
| `artifact_list` | `aquilia/cli/commands/artifacts.py` | `def artifact_list(store_dir: str, kind: str, tag: str, json_output: bool)` | List all artifacts in the store. |
| `artifact_inspect` | `aquilia/cli/commands/artifacts.py` | `def artifact_inspect(name: str, version: str, store_dir: str, json_output: bool)` | Inspect an artifact by name. |
| `artifact_verify` | `aquilia/cli/commands/artifacts.py` | `def artifact_verify(name: str, version: str, store_dir: str)` | Verify the integrity of an artifact. |
| `artifact_verify_all` | `aquilia/cli/commands/artifacts.py` | `def artifact_verify_all(store_dir: str, json_output: bool)` | Verify integrity of ALL artifacts in the store. |
| `artifact_gc` | `aquilia/cli/commands/artifacts.py` | `def artifact_gc(store_dir: str, keep: tuple, dry_run: bool)` | Garbage-collect unreferenced artifacts. |
| `artifact_export` | `aquilia/cli/commands/artifacts.py` | `def artifact_export(store_dir: str, output: str, name: tuple)` | Export artifacts as a bundle. |
| `artifact_diff` | `aquilia/cli/commands/artifacts.py` | `def artifact_diff(name: str, version_a: str, version_b: str, store_dir: str)` | Show differences between two versions of an artifact. |
| `artifact_history` | `aquilia/cli/commands/artifacts.py` | `def artifact_history(name: str, store_dir: str)` | Show version history of an artifact. |
| `artifact_import` | `aquilia/cli/commands/artifacts.py` | `def artifact_import(bundle_path: str, store_dir: str)` | Import artifacts from a bundle file. |
| `artifact_count` | `aquilia/cli/commands/artifacts.py` | `def artifact_count(store_dir: str, kind: str)` | Count artifacts in the store. |
| `artifact_stats` | `aquilia/cli/commands/artifacts.py` | `def artifact_stats(store_dir: str, json_output: bool)` | Show aggregate statistics for the artifact store. |
| `cmd_cache_check` | `aquilia/cli/commands/cache.py` | `def cmd_cache_check(verbose: bool = False) -> None` | Validate cache configuration. |
| `cmd_cache_inspect` | `aquilia/cli/commands/cache.py` | `def cmd_cache_inspect(verbose: bool = False) -> None` | Display cache config as JSON. |
| `cmd_cache_stats` | `aquilia/cli/commands/cache.py` | `def cmd_cache_stats(verbose: bool = False) -> None` | Display cache statistics by connecting to the live cache backend. |
| `cmd_cache_clear` | `aquilia/cli/commands/cache.py` | `def cmd_cache_clear(namespace: str &#124; None = None, verbose: bool = False) -> None` | Clear cache entries. |
| `compile_workspace` | `aquilia/cli/commands/compile.py` | `def compile_workspace(output_dir: str &#124; None = None, watch: bool = False, verbose: bool = False, mode: str = 'dev', check_only: bool = False) -> list[str]` | Compile manifests to artifacts using the workspace compiler. |
| `deploy_options` | `aquilia/cli/commands/deploy_gen.py` | `def deploy_options(f)` | Decorator to add shared --force and --dry-run options to subcommands. |
| `deploy_gen_group` | `aquilia/cli/commands/deploy_gen.py` | `def deploy_gen_group(ctx, force: bool, dry_run: bool, yes: bool)` | Generate & execute production deployment files. |
| `deploy_dockerfile` | `aquilia/cli/commands/deploy_gen.py` | `def deploy_dockerfile(ctx, dev_mode: bool, mlops_mode: bool, output: str, force: bool, dry_run: bool)` | Generate production-ready Dockerfiles. |
| `deploy_compose` | `aquilia/cli/commands/deploy_gen.py` | `def deploy_compose(ctx, dev_mode: bool, monitoring: bool, output: str, force: bool, dry_run: bool)` | Generate docker-compose.yml for the workspace. |
| `deploy_kubernetes` | `aquilia/cli/commands/deploy_gen.py` | `def deploy_kubernetes(ctx, output: str, mlops: bool, force: bool, dry_run: bool)` | Generate production Kubernetes manifests. |
| `deploy_nginx` | `aquilia/cli/commands/deploy_gen.py` | `def deploy_nginx(ctx, output: str, force: bool, dry_run: bool)` | Generate Nginx reverse-proxy configuration. |
| `deploy_ci` | `aquilia/cli/commands/deploy_gen.py` | `def deploy_ci(ctx, provider: str, output: str &#124; None, force: bool, dry_run: bool)` | Generate CI/CD pipeline configuration. |
| `deploy_monitoring` | `aquilia/cli/commands/deploy_gen.py` | `def deploy_monitoring(ctx, output: str, force: bool, dry_run: bool)` | Generate monitoring configuration (Prometheus + Grafana). |
| `deploy_env` | `aquilia/cli/commands/deploy_gen.py` | `def deploy_env(ctx, output: str, force: bool, dry_run: bool)` | Generate .env.example template with all Aquilia settings. |
| `deploy_all` | `aquilia/cli/commands/deploy_gen.py` | `def deploy_all(ctx, output: str, monitoring: bool, ci_provider: str, force: bool, dry_run: bool)` | Generate ALL deployment files at once. |
| `deploy_makefile` | `aquilia/cli/commands/deploy_gen.py` | `def deploy_makefile(ctx, output: str, force: bool, dry_run: bool)` | Generate a self-documenting Makefile for dev & ops tasks. |
| `deploy_render` | `aquilia/cli/commands/deploy_gen.py` | `def deploy_render(ctx, image: str &#124; None, region: str &#124; None, plan: str &#124; None, num_instances: int &#124; None, service_name: str &#124; None, destroy: bool, show_status: bool, force: bool, dry_run: bool)` | Deploy to Render PaaS with a single command. |
| `main` | `aquilia/cli/commands/discover.py` | `def main()` | CLI entry point for discovery command. |
| `diagnose_workspace` | `aquilia/cli/commands/doctor.py` | `def diagnose_workspace(verbose: bool = False) -> list[str]` | Comprehensive workspace diagnostics. |
| `freeze_artifacts` | `aquilia/cli/commands/freeze.py` | `def freeze_artifacts(output_dir: str &#124; None = None, sign: bool = False, verbose: bool = False) -> str` | Generate immutable artifacts for production. |
| `cmd_i18n_init` | `aquilia/cli/commands/i18n.py` | `def cmd_i18n_init(locales: str &#124; None = None, directory: str = 'locales', format: str = 'json', verbose: bool = False) -> None` | Initialize i18n in the current workspace. |
| `cmd_i18n_check` | `aquilia/cli/commands/i18n.py` | `def cmd_i18n_check(verbose: bool = False) -> None` | Validate i18n configuration and catalogs. |
| `cmd_i18n_inspect` | `aquilia/cli/commands/i18n.py` | `def cmd_i18n_inspect() -> None` | Show current i18n configuration as JSON. |
| `cmd_i18n_extract` | `aquilia/cli/commands/i18n.py` | `def cmd_i18n_extract(source_dirs: str &#124; None = None, output: str = 'locales/en/messages.json', merge: bool = True, verbose: bool = False) -> None` | Extract translation keys from Python and template source files. |
| `cmd_i18n_coverage` | `aquilia/cli/commands/i18n.py` | `def cmd_i18n_coverage(verbose: bool = False) -> None` | Show translation coverage per locale. |
| `cmd_i18n_compile` | `aquilia/cli/commands/i18n.py` | `def cmd_i18n_compile(directory: str = 'locales', output: str &#124; None = None, verbose: bool = False) -> None` | Compile JSON translation files to CROUS binary format. |
| `create_workspace` | `aquilia/cli/commands/init.py` | `def create_workspace(name: str, minimal: bool = False, template: str &#124; None = None, verbose: bool = False, *, include_docker: bool = True, include_readme: bool = True, include_makefile: bool = True, include_tests: bool = True, include_gitignore: bool = True, include_license: str &#124; None = None) -> Path` | Create a new Aquilia workspace. |
| `inspect_routes` | `aquilia/cli/commands/inspect.py` | `def inspect_routes(verbose: bool = False) -> None` | Show all routes discovered from module manifests and controllers. |
| `inspect_di` | `aquilia/cli/commands/inspect.py` | `def inspect_di(verbose: bool = False) -> None` | Show the DI service graph from module manifests. |
| `inspect_modules` | `aquilia/cli/commands/inspect.py` | `def inspect_modules(verbose: bool = False) -> None` | List all modules with metadata. |
| `inspect_faults` | `aquilia/cli/commands/inspect.py` | `def inspect_faults(verbose: bool = False) -> None` | Show fault domains from module manifests. |
| `inspect_config` | `aquilia/cli/commands/inspect.py` | `def inspect_config(verbose: bool = False) -> None` | Show resolved configuration from workspace + config files. |
| `cmd_mail_check` | `aquilia/cli/commands/mail.py` | `def cmd_mail_check(verbose: bool = False) -> None` | Validate mail configuration. |
| `cmd_mail_send_test` | `aquilia/cli/commands/mail.py` | `def cmd_mail_send_test(to: str, subject: str &#124; None = None, body: str &#124; None = None, verbose: bool = False) -> None` | Send a test email. |
| `cmd_mail_inspect` | `aquilia/cli/commands/mail.py` | `def cmd_mail_inspect(verbose: bool = False) -> None` | Inspect mail configuration (JSON output). |
| `update_manifest` | `aquilia/cli/commands/manifest.py` | `def update_manifest(module_name: str, workspace_root: Path, check: bool = False, freeze: bool = False, verbose: bool = False)` | Update manifest.py with auto-discovered resources. |
| `migrate_legacy` | `aquilia/cli/commands/migrate.py` | `def migrate_legacy(dry_run: bool = False, verbose: bool = False) -> MigrationResult` | Migrate from legacy layout to Aquilia workspace. |
| `pack_group` | `aquilia/cli/commands/mlops_cmds.py` | `def pack_group()` | Model packaging commands. |
| `pack_save` | `aquilia/cli/commands/mlops_cmds.py` | `def pack_save(model_path, name, version, framework, env_lock, output, sign_key)` | Package a model into an .aquilia archive. |
| `pack_inspect` | `aquilia/cli/commands/mlops_cmds.py` | `def pack_inspect(archive_path)` | Display manifest of an .aquilia archive. |
| `pack_verify` | `aquilia/cli/commands/mlops_cmds.py` | `def pack_verify(archive_path, key)` | Verify the signature of an .aquilia archive. |
| `pack_push` | `aquilia/cli/commands/mlops_cmds.py` | `def pack_push(archive_path, registry, tag)` | Push a pack to a remote registry. |
| `model_group` | `aquilia/cli/commands/mlops_cmds.py` | `def model_group()` | Model serving commands. |
| `model_serve` | `aquilia/cli/commands/mlops_cmds.py` | `def model_serve(model_path, runtime, host, port, batch_size, batch_latency_ms)` | Serve a model with the built-in inference server. |
| `model_health` | `aquilia/cli/commands/mlops_cmds.py` | `def model_health(url)` | Check model server health. |
| `deploy_group` | `aquilia/cli/commands/mlops_cmds.py` | `def deploy_group()` | MLOps model deployment and rollout commands. |
| `deploy_rollout` | `aquilia/cli/commands/mlops_cmds.py` | `def deploy_rollout(model_name, from_version, to_version, strategy, steps, error_threshold)` | Start a progressive rollout. |
| `deploy_ci_template` | `aquilia/cli/commands/mlops_cmds.py` | `def deploy_ci_template(registry, output)` | Generate CI/CD templates (GitHub Actions + Dockerfile). |
| `observe_group` | `aquilia/cli/commands/mlops_cmds.py` | `def observe_group()` | Observability and monitoring commands. |
| `observe_drift` | `aquilia/cli/commands/mlops_cmds.py` | `def observe_drift(reference_csv, current_csv, method, threshold)` | Detect data drift between reference and current datasets. |
| `observe_metrics` | `aquilia/cli/commands/mlops_cmds.py` | `def observe_metrics(fmt)` | Export current metrics. |
| `export_group` | `aquilia/cli/commands/mlops_cmds.py` | `def export_group()` | Export and optimise models for edge / production. |
| `export_onnx` | `aquilia/cli/commands/mlops_cmds.py` | `def export_onnx(model_path, output, opset)` | Export a PyTorch model to ONNX. |
| `export_edge` | `aquilia/cli/commands/mlops_cmds.py` | `def export_edge(model_path, target, output)` | Export model for edge deployment. |
| `plugin_group` | `aquilia/cli/commands/mlops_cmds.py` | `def plugin_group()` | Plugin management commands. |
| `plugin_list` | `aquilia/cli/commands/mlops_cmds.py` | `def plugin_list()` | List discovered plugins. |
| `plugin_install` | `aquilia/cli/commands/mlops_cmds.py` | `def plugin_install(package_name)` | Install a plugin from PyPI. |
| `plugin_uninstall` | `aquilia/cli/commands/mlops_cmds.py` | `def plugin_uninstall(package_name)` | Uninstall a plugin. |
| `plugin_search` | `aquilia/cli/commands/mlops_cmds.py` | `def plugin_search(query, verified_only)` | Search the plugin marketplace. |
| `lineage_group` | `aquilia/cli/commands/mlops_cmds.py` | `def lineage_group()` | Model lineage and provenance tracking commands. |
| `lineage_show` | `aquilia/cli/commands/mlops_cmds.py` | `def lineage_show(fmt)` | Show the full model lineage graph. |
| `lineage_ancestors` | `aquilia/cli/commands/mlops_cmds.py` | `def lineage_ancestors(model_id)` | Show all ancestors (transitive parents) of a model. |
| `lineage_descendants` | `aquilia/cli/commands/mlops_cmds.py` | `def lineage_descendants(model_id)` | Show all descendants (derived models) of a model. |
| `lineage_path` | `aquilia/cli/commands/mlops_cmds.py` | `def lineage_path(from_model, to_model)` | Find derivation path between two models. |
| `experiment_group` | `aquilia/cli/commands/mlops_cmds.py` | `def experiment_group()` | A/B experiment management commands. |
| `experiment_create` | `aquilia/cli/commands/mlops_cmds.py` | `def experiment_create(experiment_id, description, arm)` | Create a new A/B experiment. |
| `experiment_list` | `aquilia/cli/commands/mlops_cmds.py` | `def experiment_list()` | List all experiments. |
| `experiment_conclude` | `aquilia/cli/commands/mlops_cmds.py` | `def experiment_conclude(experiment_id, winner)` | Conclude an experiment and optionally declare a winner. |
| `experiment_summary` | `aquilia/cli/commands/mlops_cmds.py` | `def experiment_summary(experiment_id)` | Show detailed experiment summary with per-arm metrics. |
| `cmd_makemigrations` | `aquilia/cli/commands/model_cmds.py` | `def cmd_makemigrations(app: str &#124; None = None, migrations_dir: str = 'migrations', verbose: bool = False, use_dsl: bool = True, migration_format: str = 'crous') -> list[Path]` | Generate migration files from Python Model definitions. |
| `cmd_migrate` | `aquilia/cli/commands/model_cmds.py` | `def cmd_migrate(migrations_dir: str = 'migrations', database_url: str = 'sqlite:///db.sqlite3', target: str &#124; None = None, verbose: bool = False, fake: bool = False, plan: bool = False, database: str &#124; None = None) -> list[str]` | Apply pending migrations to the database. |
| `cmd_model_dump` | `aquilia/cli/commands/model_cmds.py` | `def cmd_model_dump(emit: str = 'python', output_dir: str &#124; None = None, verbose: bool = False) -> str &#124; None` | Dump model schema information. |
| `cmd_shell` | `aquilia/cli/commands/model_cmds.py` | `def cmd_shell(database_url: str = 'sqlite:///db.sqlite3', verbose: bool = False) -> None` | Launch an async REPL with models and database pre-loaded. |
| `cmd_inspectdb` | `aquilia/cli/commands/model_cmds.py` | `def cmd_inspectdb(database_url: str = 'sqlite:///db.sqlite3', tables: list[str] &#124; None = None, verbose: bool = False) -> str` | Introspect an existing database and generate Model classes. |
| `cmd_showmigrations` | `aquilia/cli/commands/model_cmds.py` | `def cmd_showmigrations(migrations_dir: str = 'migrations', database_url: str = 'sqlite:///db.sqlite3', verbose: bool = False) -> list[dict]` | Show all migrations and their applied status against the database. |
| `cmd_sqlmigrate` | `aquilia/cli/commands/model_cmds.py` | `def cmd_sqlmigrate(migration_name: str, migrations_dir: str = 'migrations', verbose: bool = False, database: str &#124; None = None) -> str &#124; None` | Display the SQL statements for a specific migration. |
| `cmd_db_status` | `aquilia/cli/commands/model_cmds.py` | `def cmd_db_status(database_url: str = 'sqlite:///db.sqlite3', verbose: bool = False) -> dict` | Show database status -- tables, row counts, schema details. |
| `provider_group` | `aquilia/cli/commands/provider.py` | `def provider_group()` | Manage cloud provider authentication & configuration. |
| `render_group` | `aquilia/cli/commands/provider.py` | `def render_group()` | Render provider management. |
| `provider_login` | `aquilia/cli/commands/provider.py` | `def provider_login(provider_name: str, token: str &#124; None, region: str)` | Login to a cloud provider. |
| `provider_logout` | `aquilia/cli/commands/provider.py` | `def provider_logout(provider_name: str)` | Logout from a cloud provider. |
| `provider_status` | `aquilia/cli/commands/provider.py` | `def provider_status(provider_name: str)` | Show cloud provider authentication status. |
| `render_env_group` | `aquilia/cli/commands/provider.py` | `def render_env_group()` | Manage Render service environment variables. |
| `render_env_list` | `aquilia/cli/commands/provider.py` | `def render_env_list(service: str)` | List all environment variables for a Render service. |
| `render_env_set` | `aquilia/cli/commands/provider.py` | `def render_env_set(name: str, value: str &#124; None, service: str)` | Create or update an environment variable on a Render service. |
| `render_env_delete` | `aquilia/cli/commands/provider.py` | `def render_env_delete(name: str, service: str)` | Delete an environment variable from a Render service. |
| `run_dev_server` | `aquilia/cli/commands/run.py` | `def run_dev_server(mode: str = 'dev', host: str &#124; None = None, port: int &#124; None = None, reload: bool &#124; None = None, verbose: bool = False) -> None` | Start development server using uvicorn. |
| `serve_production` | `aquilia/cli/commands/serve.py` | `def serve_production(workers: int &#124; None = None, bind: str &#124; None = None, verbose: bool = False, use_gunicorn: bool = False, timeout: int = 120, graceful_timeout: int = 30) -> None` | Start production server. |
| `run_tests` | `aquilia/cli/commands/test.py` | `def run_tests(*, paths: list[str] &#124; None = None, pattern: str &#124; None = None, verbose: bool = False, coverage: bool = False, coverage_html: bool = False, failfast: bool = False, markers: str &#124; None = None, parallel: bool = False, last_failed: bool = False, no_header: bool = False, extra_args: list[str] &#124; None = None) -> int` | Execute the test suite via pytest. |
| `validate_workspace` | `aquilia/cli/commands/validate.py` | `def validate_workspace(strict: bool = False, module_filter: str &#124; None = None, verbose: bool = False) -> ValidationResult` | Validate workspace manifests using the Aquilary pipeline. |
| `cmd_ws_inspect` | `aquilia/cli/commands/ws.py` | `def cmd_ws_inspect(args: dict)` | Inspect compiled WebSocket namespaces. |
| `cmd_ws_broadcast` | `aquilia/cli/commands/ws.py` | `def cmd_ws_broadcast(args: dict)` | Broadcast message to namespace or room. |
| `cmd_ws_purge_room` | `aquilia/cli/commands/ws.py` | `def cmd_ws_purge_room(args: dict)` | Purge room state from adapter. |
| `cmd_ws_kick` | `aquilia/cli/commands/ws.py` | `def cmd_ws_kick(args: dict)` | Kick (disconnect) a connection. |
| `cmd_ws_gen_client` | `aquilia/cli/commands/ws.py` | `def cmd_ws_gen_client(args: dict)` | Generate TypeScript client SDK from artifacts. |
| `main` | `aquilia/cli/commands/ws.py` | `def main()` | Main CLI entry point. |
| `main` | `aquilia/cli/discovery_cli.py` | `def main()` | Main CLI entry point. |
| `generate_controller` | `aquilia/cli/generators/controller.py` | `def generate_controller(name: str, output_dir: str = 'controllers', prefix: str = None, resource: str = None, simple: bool = False, with_lifecycle: bool = False, test: bool = False) -> Path` | Generate a controller file. |
| `success` | `aquilia/cli/utils/colors.py` | `def success(message: str) -> None` | Print success message in green. |
| `error` | `aquilia/cli/utils/colors.py` | `def error(message: str) -> None` | Print error message in red. |
| `warning` | `aquilia/cli/utils/colors.py` | `def warning(message: str) -> None` | Print warning message in yellow. |
| `info` | `aquilia/cli/utils/colors.py` | `def info(message: str) -> None` | Print info message in cyan. |
| `dim` | `aquilia/cli/utils/colors.py` | `def dim(message: str) -> None` | Print dimmed message. |
| `bold` | `aquilia/cli/utils/colors.py` | `def bold(message: str) -> str` | Return bold-styled text (does not echo). |
| `accent` | `aquilia/cli/utils/colors.py` | `def accent(message: str) -> str` | Return magenta-accented text (does not echo). |
| `banner` | `aquilia/cli/utils/colors.py` | `def banner(title: str = 'Aquilia', subtitle: str = '', *, width: int &#124; None = None, fg: str = 'cyan', icon: str = '') -> None` | Print a bordered banner with centred title and optional icon. |
| `section` | `aquilia/cli/utils/colors.py` | `def section(title: str, *, width: int &#124; None = None, fg: str = 'cyan') -> None` | Print a section header with a ruled line. |
| `rule` | `aquilia/cli/utils/colors.py` | `def rule(*, char: str = _L_H, width: int &#124; None = None, fg: str = 'white') -> None` | Print a thin horizontal rule. |
| `kv` | `aquilia/cli/utils/colors.py` | `def kv(key: str, value: str, *, key_width: int = 20, indent: int = 2, key_fg: str = 'white', val_fg: str = 'cyan') -> None` | Print an aligned key-value pair. |
| `badge` | `aquilia/cli/utils/colors.py` | `def badge(label: str, *, style: str = 'ok') -> str` | Return an inline badge string (not echoed). |
| `tree_item` | `aquilia/cli/utils/colors.py` | `def tree_item(text: str, *, last: bool = False, depth: int = 0, fg: str = 'white') -> None` | Print an indented tree node. |
| `bullet` | `aquilia/cli/utils/colors.py` | `def bullet(text: str, *, indent: int = 2, fg: str = 'white') -> None` | Print a bulleted list item. |
| `step` | `aquilia/cli/utils/colors.py` | `def step(number: int, text: str, *, fg: str = 'cyan') -> None` | Print a numbered step. |
| `indent_echo` | `aquilia/cli/utils/colors.py` | `def indent_echo(text: str, *, level: int = 1) -> None` | Echo text with indentation (2 spaces per level). |
| `table` | `aquilia/cli/utils/colors.py` | `def table(headers: Sequence[str], rows: Sequence[Sequence[str]], *, col_widths: Sequence[int] &#124; None = None, header_fg: str = 'cyan', row_fg: str = 'white', indent: int = 2) -> None` | Print a minimal aligned table. |
| `panel` | `aquilia/cli/utils/colors.py` | `def panel(lines: Sequence[str], *, title: str = '', width: int &#124; None = None, fg: str = 'cyan', pad: int = 1) -> None` | Print a bordered panel. |
| `file_written` | `aquilia/cli/utils/colors.py` | `def file_written(label: str, *, verbose: bool = False, path: str = '') -> None` | Announce a generated file. |
| `file_skipped` | `aquilia/cli/utils/colors.py` | `def file_skipped(label: str, reason: str = 'exists') -> None` | Announce a skipped file. |
| `file_dry` | `aquilia/cli/utils/colors.py` | `def file_dry(label: str) -> None` | Announce a dry-run file. |
| `next_steps` | `aquilia/cli/utils/colors.py` | `def next_steps(steps_list: Sequence[str], *, title: str = 'Next steps') -> None` | Print a numbered next-steps panel. |
| `status_line` | `aquilia/cli/utils/colors.py` | `def status_line(icon: str, label: str, value: str, *, label_fg: str = 'white', value_fg: str = 'cyan', indent: int = 2) -> None` | Print a status indicator with icon, label and value. |
| `progress_bar` | `aquilia/cli/utils/colors.py` | `def progress_bar(label: str, current: int, total: int, *, width: int = 30, filled_fg: str = 'cyan', empty_fg: str = 'white') -> None` | Print a styled progress bar. |
| `detail_card` | `aquilia/cli/utils/colors.py` | `def detail_card(title: str, items: Sequence[tuple], *, icon: str = '', fg: str = 'cyan') -> None` | Print a compact detail card with key-value pairs. |
| `phase_header` | `aquilia/cli/utils/colors.py` | `def phase_header(phase_num: int, title: str, *, icon: str = '', fg: str = 'cyan') -> None` | Print a numbered phase header for multi-step flows. |
| `flow_header` | `aquilia/cli/utils/prompts.py` | `def flow_header(title: str, subtitle: str = '', *, fg: str = 'cyan') -> None` | Print a minimal flow header. |
| `flow_done` | `aquilia/cli/utils/prompts.py` | `def flow_done(message: str = 'Done.', *, fg: str = 'green') -> None` | Public function. |
| `ask` | `aquilia/cli/utils/prompts.py` | `def ask(label: str, *, default: str = '', required: bool = False, validator: Callable[[str], str &#124; None] &#124; None = None, hint: str = '') -> str` | Styled text input prompt with optional validation. |
| `ask_password` | `aquilia/cli/utils/prompts.py` | `def ask_password(label: str, *, confirm: bool = True, min_length: int = 4) -> str` | Styled hidden password input with optional confirmation. |
| `select` | `aquilia/cli/utils/prompts.py` | `def select(label: str, choices: Sequence[tuple[str, str]], *, default: int = 0) -> str` | Single-choice select menu with ↑↓ arrow-key navigation. |
| `multi_select` | `aquilia/cli/utils/prompts.py` | `def multi_select(label: str, choices: Sequence[tuple[str, str, bool]]) -> list[str]` | Multi-choice toggle menu with ↑↓ navigation and Space to toggle. |
| `confirm` | `aquilia/cli/utils/prompts.py` | `def confirm(label: str, *, default: bool = True) -> bool` | Styled yes/no prompt. |
| `recap` | `aquilia/cli/utils/prompts.py` | `def recap(items: Sequence[tuple[str, str]], *, title: str = 'Summary') -> None` | Print a labelled summary of selected options. |
| `find_workspace_root` | `aquilia/cli/utils/workspace.py` | `def find_workspace_root(start_path: Path &#124; None = None) -> Path &#124; None` | Find the Aquilia workspace root by looking for workspace.py or aquilia.py. |
| `get_workspace_file` | `aquilia/cli/utils/workspace.py` | `def get_workspace_file(workspace_root: Path) -> Path &#124; None` | Get the workspace configuration file path. |
| `is_python_workspace` | `aquilia/cli/utils/workspace.py` | `def is_python_workspace(workspace_root: Path) -> bool` | Check if workspace uses Python format (workspace.py or aquilia.py). |

## Constants

| Name | Source | Value or type |
| --- | --- | --- |
| `_DEFAULT_DB_URL` | `aquilia/cli/__main__.py` | `'sqlite:///db.sqlite3'` |
| `_NO_WORKSPACE_REQUIRED` | `aquilia/cli/__main__.py` | `frozenset({'init', 'version', '--version', '--help', 'help', 'doctor'})` |
| `_UVICORN_KNOWN_PARAMS` | `aquilia/cli/commands/run.py` | `frozenset({'host', 'port', 'uds', 'fd', 'loop', 'http', 'ws', 'ws_max_size', 'ws_max_queue', 'ws_ping_interval', 'ws_ping_timeout', 'ws_per_message_deflate', 'l` |
| `_TERM_WIDTH` | `aquilia/cli/utils/colors.py` | `int &#124; None` |
| `_H_TL` | `aquilia/cli/utils/colors.py` | `_G('┏', '+')` |
| `_H_TR` | `aquilia/cli/utils/colors.py` | `_G('┓', '+')` |
| `_H_BL` | `aquilia/cli/utils/colors.py` | `_G('┗', '+')` |
| `_H_BR` | `aquilia/cli/utils/colors.py` | `_G('┛', '+')` |
| `_H_H` | `aquilia/cli/utils/colors.py` | `_G('-', '-')` |
| `_H_V` | `aquilia/cli/utils/colors.py` | `_G('┃', ' &#124; ')` |
| `_L_TL` | `aquilia/cli/utils/colors.py` | `_G('┌', '+')` |
| `_L_TR` | `aquilia/cli/utils/colors.py` | `_G('┐', '+')` |
| `_L_BL` | `aquilia/cli/utils/colors.py` | `_G('└', '+')` |
| `_L_BR` | `aquilia/cli/utils/colors.py` | `_G('┘', '+')` |
| `_L_H` | `aquilia/cli/utils/colors.py` | `_G('-', '-')` |
| `_L_V` | `aquilia/cli/utils/colors.py` | `_G('│', ' &#124; ')` |
| `_L_LT` | `aquilia/cli/utils/colors.py` | `_G('├', '+')` |
| `_L_RT` | `aquilia/cli/utils/colors.py` | `_G('┤', '+')` |
| `_BULLET` | `aquilia/cli/utils/colors.py` | `_G('•', '*')` |
| `_ARROW` | `aquilia/cli/utils/colors.py` | `_G('->', '->')` |
| `_CHECK` | `aquilia/cli/utils/colors.py` | `_G('✔', '[ok]')` |
| `_CROSS` | `aquilia/cli/utils/colors.py` | `_G('✘', '[x]')` |
| `_CIRCLE` | `aquilia/cli/utils/colors.py` | `_G('○', 'o')` |
| `_DOT` | `aquilia/cli/utils/colors.py` | `_G('·', '.')` |
| `_DASH` | `aquilia/cli/utils/colors.py` | `_G('-', '-')` |
| `_ROCKET` | `aquilia/cli/utils/colors.py` | `_G('🚀', '>>')` |
| `_LOCK` | `aquilia/cli/utils/colors.py` | `_G('🔒', '[#]')` |
| `_GLOBE` | `aquilia/cli/utils/colors.py` | `_G('🌐', '(o)')` |
| `_PKG` | `aquilia/cli/utils/colors.py` | `_G('📦', '[p]')` |
| `_GEAR` | `aquilia/cli/utils/colors.py` | `_G('⚙', '[*]')` |
| `_BOLT` | `aquilia/cli/utils/colors.py` | `_G('⚡', '!')` |
| `_SHIELD` | `aquilia/cli/utils/colors.py` | `_G('🛡', '[S]')` |
| `_LINK` | `aquilia/cli/utils/colors.py` | `_G('🔗', '[@]')` |
| `_CLOCK` | `aquilia/cli/utils/colors.py` | `_G('🕑', '[t]')` |
| `_SPARK` | `aquilia/cli/utils/colors.py` | `_G('✨', '*')` |
| `_WARN` | `aquilia/cli/utils/colors.py` | `_G('⚠', '[!]')` |
| `_CLOUD` | `aquilia/cli/utils/colors.py` | `_G('☁', '(c)')` |
| `_KEY` | `aquilia/cli/utils/colors.py` | `_G('🔑', '[k]')` |
| `_EYE` | `aquilia/cli/utils/colors.py` | `_G('👁', '(e)')` |
| `_DIAMOND` | `aquilia/cli/utils/colors.py` | `_G('◆', '*')` |
| `_IS_WINDOWS` | `aquilia/cli/utils/prompts.py` | `bool` |
| `_RADIO_ON` | `aquilia/cli/utils/prompts.py` | `_G('●', '(*)')` |
| `_RADIO_OFF` | `aquilia/cli/utils/prompts.py` | `_G('○', '( )')` |
| `_CHECK_ON` | `aquilia/cli/utils/prompts.py` | `_G('◼', '[x]')` |
| `_CHECK_OFF` | `aquilia/cli/utils/prompts.py` | `_G('◻', '[ ]')` |
| `_CLEAR_LINE` | `aquilia/cli/utils/prompts.py` | `'\x1b[2K'` |
| `_HIDE_CURSOR` | `aquilia/cli/utils/prompts.py` | `'\x1b[?25l'` |
| `_SHOW_CURSOR` | `aquilia/cli/utils/prompts.py` | `'\x1b[?25h'` |
| `_STDIN_FD` | `aquilia/cli/utils/prompts.py` | `int` |
