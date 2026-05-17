# Integrations Configuration

## Configuration Entry Points

The implementation exposes the following configuration-like classes, policies, integrations, or dataclasses.

| Type | Source | Fields | Purpose |
| --- | --- | --- | --- |
| `IntegrationConfig` | `aquilia/integrations/_protocol.py` | See class attributes and constructor methods. | Protocol that all typed integration configs implement. |
| `AdminModules` | `aquilia/integrations/admin.py` | dashboard: bool, orm: bool, migrations: bool, config: bool, workspace: bool, permissions: bool, monitoring: bool, admin_users: bool, profile: bool, audit: bool, containers: bool, pods: bool, ... | Controls which admin pages are visible. |
| `AdminAudit` | `aquilia/integrations/admin.py` | enabled: bool, max_entries: int, log_logins: bool, log_views: bool, log_searches: bool, excluded_actions: list[str] | Audit log configuration. |
| `AdminMonitoring` | `aquilia/integrations/admin.py` | enabled: bool, metrics: list[str], refresh_interval: int | Monitoring dashboard configuration. |
| `AdminSidebar` | `aquilia/integrations/admin.py` | overview: bool, data: bool, system: bool, infrastructure: bool, security: bool, models: bool, devtools: bool | Admin sidebar section visibility. |
| `AdminContainers` | `aquilia/integrations/admin.py` | docker_host: str &#124; None, allowed_actions: list[str], denied_actions: list[str], log_tail: int, log_since: str, refresh_interval: int, compose_files: list[str], compose_project_dir: str &#124; None, show_system_containers: bool, enable_exec: bool, enable_prune: bool, enable_build: bool, ... | Docker containers admin page configuration. |
| `AdminPods` | `aquilia/integrations/admin.py` | kubeconfig: str &#124; None, namespace: str, contexts: list[str], resources: list[str], manifest_dirs: list[str], manifest_patterns: list[str], refresh_interval: int, log_tail: int, enable_logs: bool, enable_exec: bool, enable_delete: bool, enable_scale: bool, ... | Kubernetes pods admin page configuration. |
| `AdminSecurity` | `aquilia/integrations/admin.py` | csrf_enabled: bool, csrf_max_age: int, csrf_token_length: int, rate_limit_enabled: bool, rate_limit_max_attempts: int, rate_limit_window: int, sensitive_op_limit: int, sensitive_op_window: int, progressive_lockout: bool, lockout_tiers: list[list[int]] &#124; None, password_min_length: int, password_max_length: int, ... | Admin dashboard security configuration (CSRF, rate-limit, passwords, headers). |
| `AdminIntegration` | `aquilia/integrations/admin.py` | url_prefix: str, site_title: str, site_header: str, auto_discover: bool, login_url: str &#124; None, list_per_page: int, theme: str, modules: AdminModules &#124; None, audit: AdminAudit &#124; None, monitoring: AdminMonitoring &#124; None, sidebar: AdminSidebar &#124; None, containers: AdminContainers &#124; None, ... | Typed admin dashboard integration config. |
| `AuthIntegration` | `aquilia/integrations/auth.py` | enabled: bool, store_type: str, secret_key: str &#124; None, algorithm: str, issuer: str, audience: str, access_token_ttl_minutes: int, refresh_token_ttl_days: int, require_auth_by_default: bool | Typed authentication integration config. |
| `CacheIntegration` | `aquilia/integrations/cache.py` | backend: str, default_ttl: int, max_size: int, eviction_policy: str, namespace: str, key_prefix: str, serializer: str, redis_url: str, redis_max_connections: int, l1_max_size: int, l1_ttl: int, l2_backend: str, ... | Typed cache subsystem configuration. |
| `DatabaseIntegration` | `aquilia/integrations/database.py` | url: str &#124; None, config: Any &#124; None, auto_connect: bool, auto_create: bool, auto_migrate: bool, migrations_dir: str, pool_size: int, echo: bool, model_paths: list[str], scan_dirs: list[str] | Typed database integration config. |
| `I18nIntegration` | `aquilia/integrations/i18n.py` | default_locale: str, available_locales: list[str], fallback_locale: str, catalog_dirs: list[str], catalog_format: str, missing_key_strategy: str, auto_reload: bool, auto_detect: bool, cookie_name: str, query_param: str, path_prefix: bool, resolver_order: list[str], ... | Typed i18n (internationalization) configuration. |
| `LoggingIntegration` | `aquilia/integrations/logging_cfg.py` | format: str, level: str, slow_threshold_ms: float, skip_paths: list[str], include_headers: bool, include_query: bool, include_user_agent: bool, log_request_body: bool, log_response_body: bool, colorize: bool, enabled: bool | Typed request logging configuration. |
| `MailAuth` | `aquilia/integrations/mail.py` | method: str, username: str &#124; None, password: str &#124; None, password_env: str &#124; None, domain: str &#124; None, api_key: str &#124; None, api_key_env: str &#124; None, aws_access_key_id: str &#124; None, aws_access_key_id_env: str &#124; None, aws_secret_access_key: str &#124; None, aws_secret_access_key_env: str &#124; None, aws_region: str &#124; None, ... | Mail authentication credentials. |
| `SmtpProvider` | `aquilia/integrations/mail.py` | host: str, port: int, use_tls: bool, use_ssl: bool, timeout: float, pool_size: int, pool_recycle: float, validate_certs: bool, client_cert: str &#124; None, client_key: str &#124; None, source_address: str &#124; None, local_hostname: str &#124; None | SMTP / STARTTLS mail provider. |
| `SesProvider` | `aquilia/integrations/mail.py` | region: str, configuration_set: str &#124; None, source_arn: str &#124; None, return_path: str &#124; None, tags: dict[str, str], use_raw: bool, endpoint_url: str &#124; None | AWS Simple Email Service provider. |
| `SendGridProvider` | `aquilia/integrations/mail.py` | sandbox_mode: bool, click_tracking: bool, open_tracking: bool, categories: list[str], asm_group_id: int &#124; None, ip_pool_name: str &#124; None, template_id: str &#124; None, api_base_url: str, timeout: float | SendGrid Web API v3 provider. |
| `ConsoleProvider` | `aquilia/integrations/mail.py` | See class attributes and constructor methods. | Console / stdout provider (development only). |
| `FileProvider` | `aquilia/integrations/mail.py` | output_dir: str, max_files: int, write_index: bool, include_metadata: bool, file_extension: str | File / .eml provider (testing & audit). |
| `MailIntegration` | `aquilia/integrations/mail.py` | default_from: str, default_reply_to: str &#124; None, subject_prefix: str, providers: list[Any], auth: MailAuth &#124; None, console_backend: bool, preview_mode: bool, template_dirs: list[str], retry_max_attempts: int, retry_base_delay: float, rate_limit_global: int, rate_limit_per_domain: int, ... | Typed mail subsystem configuration. |
| `MLOpsIntegration` | `aquilia/integrations/mlops.py` | enabled: bool, registry_db: str, blob_root: str, storage_backend: str, drift_method: str, drift_threshold: float, drift_num_bins: int, max_batch_size: int, max_latency_ms: float, batching_strategy: str, sample_rate: float, log_dir: str, ... | Typed MLOps platform configuration. |
| `MiddlewareEntry` | `aquilia/integrations/mw.py` | path: str, priority: int, scope: str, name: str &#124; None, kwargs: dict[str, Any] | A single middleware entry in the chain. |
| `OpenAPIIntegration` | `aquilia/integrations/openapi.py` | title: str, version: str, description: str, terms_of_service: str, contact_name: str, contact_email: str, contact_url: str, license_name: str, license_url: str, servers: list[dict[str, str]], docs_path: str, openapi_json_path: str, ... | Typed OpenAPI spec / Swagger UI configuration. |
| `RenderIntegration` | `aquilia/integrations/render.py` | service_name: str &#124; None, region: str, plan: str, num_instances: int, image: str &#124; None, health_path: str, auto_deploy: str, enabled: bool | Typed Render deployment configuration. |
| `CorsIntegration` | `aquilia/integrations/security.py` | allow_origins: list[str], allow_methods: list[str], allow_headers: list[str], expose_headers: list[str], allow_credentials: bool, max_age: int, allow_origin_regex: str &#124; None, enabled: bool | Typed CORS middleware configuration. |
| `CspIntegration` | `aquilia/integrations/security.py` | policy: dict[str, list[str]] &#124; None, report_only: bool, nonce: bool, preset: str, enabled: bool | Typed Content-Security-Policy configuration. |
| `RateLimitIntegration` | `aquilia/integrations/security.py` | limit: int, window: int, algorithm: str, per_user: bool, burst: int &#124; None, exempt_paths: list[str], enabled: bool | Typed rate limiting configuration. |
| `CsrfIntegration` | `aquilia/integrations/security.py` | secret_key: str, token_length: int, header_name: str, field_name: str, cookie_name: str, cookie_path: str, cookie_domain: str &#124; None, cookie_secure: bool, cookie_samesite: str, cookie_httponly: bool, cookie_max_age: int, safe_methods: list[str], ... | Typed CSRF protection configuration. |
| `SessionIntegration` | `aquilia/integrations/sessions.py` | enabled: bool, policy: Any &#124; None, store: Any &#124; None, transport: Any &#124; None | Typed session integration config. |
| `DiIntegration` | `aquilia/integrations/simple.py` | auto_wire: bool, enabled: bool | Dependency injection configuration. |
| `RoutingIntegration` | `aquilia/integrations/simple.py` | strict_matching: bool, enabled: bool | Routing configuration. |
| `FaultHandlingIntegration` | `aquilia/integrations/simple.py` | default_strategy: str, enabled: bool | Fault handling configuration. |
| `PatternsIntegration` | `aquilia/integrations/simple.py` | enabled: bool | Patterns configuration. |
| `RegistryIntegration` | `aquilia/integrations/simple.py` | enabled: bool | Registry configuration. |
| `SerializersIntegration` | `aquilia/integrations/simple.py` | auto_discover: bool, strict_validation: bool, raise_on_error: bool, date_format: str, datetime_format: str, coerce_decimal_to_string: bool, compact_json: bool, enabled: bool | Global serializer settings. |
| `StaticFilesIntegration` | `aquilia/integrations/static.py` | directories: dict[str, str], cache_max_age: int, immutable: bool, etag: bool, gzip: bool, brotli: bool, memory_cache: bool, html5_history: bool, enabled: bool | Typed static file serving configuration. |
| `StorageIntegration` | `aquilia/integrations/storage.py` | default: str, backends: dict[str, Any] &#124; None, enabled: bool | Typed file storage configuration. |
| `TasksIntegration` | `aquilia/integrations/tasks.py` | backend: str, num_workers: int, default_queue: str, cleanup_interval: float, cleanup_max_age: float, max_retries: int, retry_delay: float, retry_backoff: float, retry_max_delay: float, default_timeout: float, auto_start: bool, dead_letter_max: int, ... | Typed background tasks configuration. |
| `TemplatesIntegration` | `aquilia/integrations/templates.py` | enabled: bool, search_paths: list[str], cache: str, sandbox: bool, sandbox_policy: str, precompile: bool | Typed template engine configuration. |
| `VersioningIntegration` | `aquilia/integrations/versioning_cfg.py` | strategy: str, versions: list[str], default_version: str &#124; None, require_version: bool, header_name: str, query_param: str, url_prefix: str, url_segment_index: int, strip_version_from_path: bool, media_type_param: str, channels: dict[str, str], channel_header: str, ... | Typed API versioning configuration. |

## Common Entry Points

- `IntegrationConfig protocol`
- `typed dataclasses in aquilia.integrations`

## Precedence Model

Aquilia generally resolves configuration in this order:

1. Explicit constructor arguments or typed integration dataclass values.
2. `Workspace` builder methods and `Workspace.integrate(...)` output.
3. `ConfigLoader` defaults and environment overlays.
4. Runtime defaults inside the subsystem service or provider constructor.

When this module is registered through an `AppManifest`, keep component declarations inside `modules/<name>/manifest.py` and keep cross-cutting integration settings in `workspace.py`.

## Datatype Guidance

- Prefer typed dataclasses, policy objects, and config objects listed above when they exist.
- Keep secret values in environment-backed config, not literal strings in committed workspace files.
- Keep runtime-only state in services, stores, providers, or request state rather than static configuration.
- Use `to_dict()` on integration dataclasses when you need to inspect exactly what enters `ConfigLoader`.
