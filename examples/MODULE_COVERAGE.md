# Module Coverage Matrix

This matrix maps source modules to executable examples or workflow documentation.

| Module | Covered by | Notes |
| --- | --- | --- |
| `admin` | `admin_dashboard_app`, `multi_module_native_app`, `CLI_WORKFLOWS.md` | Admin integration config, model admin registration, role permission checks, CLI setup/check/user workflows. |
| `aquilary` | all app starters, `reference_suite/core_config_runtime.py` | Runtime discovery uses manifests through Aquilary. |
| `artifacts` | `artifacts_release_app`, `reference_suite/artifacts_signing_versioning.py`, `CLI_WORKFLOWS.md` | Builder, memory store, integrity verification, signed release tokens, artifact CLI. |
| `auth` | `auth_app`, `multi_module_native_app` | Memory identity/credential/token stores and protected routes. |
| `blueprints` | `rest_api_blueprint`, `crud_app`, `auth_app` | Request validation and field sealing. |
| `cache` | `cache_http_edge_app`, `multi_module_native_app`, `reference_suite/cache_storage_filesystem.py`, `CLI_WORKFLOWS.md` | Memory backend, service API, cache-aside gateway, stats, cache CLI. |
| `cli` | `CLI_WORKFLOWS.md` | Full command group coverage with flags from implementation. |
| `config`, `pyconfig`, `config_builders` | app `workspace.py`, `reference_suite/core_config_runtime.py` | Workspace builders, `AquilaConfig`, env-backed values, `ConfigLoader`. |
| `controller` | all app starters | HTTP decorators, `Controller`, `RequestCtx`, `Response`. |
| `db`, `models`, `sqlite` | `sqlite_inventory_app`, `crud_app`, `admin_dashboard_app`, `reference_suite/sqlite_models.py`, `CLI_WORKFLOWS.md` | Model fields, native sqlite service, pool transactions, database CLI workflows. |
| `debug`, `health` | runtime behavior, `multi_module_native_app/modules/operations` | Operational endpoints and debug pages are runtime-provided. |
| `di` | all manifests, `reference_suite/dependency_injection.py` | Providers, scopes, async resolution. |
| `discovery` | `CLI_WORKFLOWS.md` | `aq discover`, `aq analytics`, `aq manifest update`. |
| `dotenv`, `signing` | `reference_suite/core_config_runtime.py`, `reference_suite/artifacts_signing_versioning.py` | Env config and signed payloads. |
| `effects`, `flow`, `subsystems` | `MODULE_COVERAGE.md`, docs | Public APIs are documented; add a dedicated effect pipeline app when effect-backed integrations are expanded. |
| `faults` | app services, `reference_suite/http_patterns_faults.py` | Structured faults and `FaultEngine` processing. |
| `filesystem` | `reference_suite/cache_storage_filesystem.py` | Native async write/read/path APIs. |
| `http` | `cache_http_edge_app`, `reference_suite/http_patterns_faults.py` | `AsyncHTTPClient` with `MockTransport`, cache-aside HTTP integration. |
| `i18n` | `i18n_content_app`, `multi_module_native_app`, `reference_suite/i18n_templates_mail.py`, `CLI_WORKFLOWS.md` | Memory catalog, locale negotiation, pluralization, service formatting, i18n CLI. |
| `integrations` | app `workspace.py` files | Typed integration objects and fluent integration builder. |
| `mail` | `mail_notifications_app`, `multi_module_native_app`, `reference_suite/i18n_templates_mail.py`, `CLI_WORKFLOWS.md` | Message/envelope pipeline, file and console providers, mail CLI. |
| `middleware`, `middleware_ext` | `middleware_security_app`, workspace security/routing config, `multi_module_native_app` | Rate-limit rules, CSP policy, security integrations, middleware chain guidance. |
| `mlops` | `mlops_model_registry_app`, `CLI_WORKFLOWS.md` | Model metadata registry, local model inference, rollout engine, plugin host, command workflows. |
| `patterns` | `reference_suite/http_patterns_faults.py` | Pattern compiler and matcher. |
| `providers` | `provider_render_deploy_app`, `CLI_WORKFLOWS.md` | Render typed integration, deploy config payloads, dry-run planning, login/status/env/deploy workflows. |
| `request`, `response`, `_datastructures`, `_uploads` | app controllers | `RequestCtx` wraps request access; responses use `Response.json`. |
| `sessions` | `auth_app`, `multi_module_native_app` | Session policy config and auth integration. |
| `sockets` | `websocket_app`, `multi_module_native_app/modules/realtime` | Socket decorators, room join/leave, acknowledgements. |
| `storage` | `storage_filehub_app`, `multi_module_native_app`, `reference_suite/cache_storage_filesystem.py` | Storage registry, memory backend, metadata, health checks, local-style storage patterns. |
| `tasks` | `background_jobs`, `multi_module_native_app/modules/notifications`, `CLI_WORKFLOWS.md` | Task decorators, queues, schedules. |
| `templates` | `templates_portal_app`, `multi_module_native_app`, `reference_suite/i18n_templates_mail.py` | Template engine, loader, sandboxing, filters, globals, streaming, integration config. |
| `testing` | all tests under `examples/` | Pytest-style execution of example services and APIs. |
| `typing`, `utils` | indirectly through runtime/controllers | Support modules used by public APIs. |
| `versioning` | `versioned_public_api_app`, `multi_module_native_app`, `reference_suite/artifacts_signing_versioning.py` | Version integration config, route metadata decorators, strategy resolution, parsing, resolvers. |
