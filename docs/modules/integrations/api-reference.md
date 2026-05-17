# Integrations API Reference

This page is generated from the current Python source using the AST. It lists public classes, public methods, public module-level functions, constants, exports, and source files.

## Source Inventory

| File | Lines | Classes | Functions | Purpose |
| --- | ---: | ---: | ---: | --- |
| `aquilia/integrations/__init__.py` | 191 | 0 | 0 | Aquilia Integrations — Typed, validated configuration objects. |
| `aquilia/integrations/_protocol.py` | 25 | 1 | 0 | IntegrationConfig protocol — the contract every integration type satisfies. |
| `aquilia/integrations/admin.py` | 924 | 8 | 0 | Admin integration — typed admin dashboard configuration. |
| `aquilia/integrations/auth.py` | 54 | 1 | 0 | AuthIntegration — typed auth configuration. |
| `aquilia/integrations/cache.py` | 65 | 1 | 0 | CacheIntegration — typed cache configuration. |
| `aquilia/integrations/database.py` | 75 | 1 | 0 | DatabaseIntegration — typed database configuration. |
| `aquilia/integrations/i18n.py` | 56 | 1 | 0 | I18nIntegration — typed internationalization configuration. |
| `aquilia/integrations/logging_cfg.py` | 52 | 1 | 0 | LoggingIntegration — typed request/response logging configuration. |
| `aquilia/integrations/mail.py` | 519 | 7 | 0 | Mail integration — typed, flat-namespace mail configuration. |
| `aquilia/integrations/mlops.py` | 99 | 1 | 0 | MLOpsIntegration — typed MLOps platform configuration. |
| `aquilia/integrations/mw.py` | 100 | 2 | 0 | Middleware chain integration — typed middleware configuration. |
| `aquilia/integrations/openapi.py` | 77 | 1 | 0 | OpenAPIIntegration — typed OpenAPI documentation configuration. |
| `aquilia/integrations/render.py` | 50 | 1 | 0 | RenderIntegration — typed Render PaaS deployment configuration. |
| `aquilia/integrations/security.py` | 180 | 4 | 0 | Security integrations — CORS, CSP, Rate-Limit, CSRF. |
| `aquilia/integrations/sessions.py` | 60 | 1 | 0 | SessionIntegration — typed session configuration. |
| `aquilia/integrations/simple.py` | 112 | 6 | 0 | Simple integrations — small typed configs for DI, routing, faults, etc. |
| `aquilia/integrations/static.py` | 48 | 1 | 0 | StaticFilesIntegration — typed static file serving configuration. |
| `aquilia/integrations/storage.py` | 49 | 1 | 0 | StorageIntegration — typed file storage configuration. |
| `aquilia/integrations/tasks.py` | 55 | 1 | 0 | TasksIntegration — typed background task configuration. |
| `aquilia/integrations/templates.py` | 102 | 1 | 0 | TemplatesIntegration — typed template configuration. |
| `aquilia/integrations/versioning_cfg.py` | 85 | 1 | 0 | VersioningIntegration — typed API versioning configuration. |

## Public Exports

`AdminAudit`, `AdminContainers`, `AdminIntegration`, `AdminModules`, `AdminMonitoring`, `AdminPods`, `AdminSecurity`, `AdminSidebar`, `AuthIntegration`, `CacheIntegration`, `ConsoleProvider`, `CorsIntegration`, `CspIntegration`, `CsrfIntegration`, `DatabaseIntegration`, `DiIntegration`, `FaultHandlingIntegration`, `FileProvider`, `I18nIntegration`, `IntegrationConfig`, `LoggingIntegration`, `MLOpsIntegration`, `MailAuth`, `MailIntegration`, `MiddlewareChain`, `MiddlewareEntry`, `OpenAPIIntegration`, `PatternsIntegration`, `RateLimitIntegration`, `RegistryIntegration`, `RenderIntegration`, `RoutingIntegration`, `SendGridProvider`, `SerializersIntegration`, `SesProvider`, `SessionIntegration`, `SmtpProvider`, `StaticFilesIntegration`, `StorageIntegration`, `TasksIntegration`, `TemplatesIntegration`, `VersioningIntegration`

## Public Class Summary

| Class | Source | Bases | Summary |
| --- | --- | --- | --- |
| `IntegrationConfig` | `aquilia/integrations/_protocol.py` | Protocol | Protocol that all typed integration configs implement. |
| `AdminModules` | `aquilia/integrations/admin.py` | object | Controls which admin pages are visible. |
| `AdminAudit` | `aquilia/integrations/admin.py` | object | Audit log configuration. |
| `AdminMonitoring` | `aquilia/integrations/admin.py` | object | Monitoring dashboard configuration. |
| `AdminSidebar` | `aquilia/integrations/admin.py` | object | Admin sidebar section visibility. |
| `AdminContainers` | `aquilia/integrations/admin.py` | object | Docker containers admin page configuration. |
| `AdminPods` | `aquilia/integrations/admin.py` | object | Kubernetes pods admin page configuration. |
| `AdminSecurity` | `aquilia/integrations/admin.py` | object | Admin dashboard security configuration (CSRF, rate-limit, passwords, headers). |
| `AdminIntegration` | `aquilia/integrations/admin.py` | object | Typed admin dashboard integration config. |
| `AuthIntegration` | `aquilia/integrations/auth.py` | object | Typed authentication integration config. |
| `CacheIntegration` | `aquilia/integrations/cache.py` | object | Typed cache subsystem configuration. |
| `DatabaseIntegration` | `aquilia/integrations/database.py` | object | Typed database integration config. |
| `I18nIntegration` | `aquilia/integrations/i18n.py` | object | Typed i18n (internationalization) configuration. |
| `LoggingIntegration` | `aquilia/integrations/logging_cfg.py` | object | Typed request logging configuration. |
| `MailAuth` | `aquilia/integrations/mail.py` | object | Mail authentication credentials. |
| `SmtpProvider` | `aquilia/integrations/mail.py` | _ProviderBase | SMTP / STARTTLS mail provider. |
| `SesProvider` | `aquilia/integrations/mail.py` | _ProviderBase | AWS Simple Email Service provider. |
| `SendGridProvider` | `aquilia/integrations/mail.py` | _ProviderBase | SendGrid Web API v3 provider. |
| `ConsoleProvider` | `aquilia/integrations/mail.py` | _ProviderBase | Console / stdout provider (development only). |
| `FileProvider` | `aquilia/integrations/mail.py` | _ProviderBase | File / .eml provider (testing & audit). |
| `MailIntegration` | `aquilia/integrations/mail.py` | object | Typed mail subsystem configuration. |
| `MLOpsIntegration` | `aquilia/integrations/mlops.py` | object | Typed MLOps platform configuration. |
| `MiddlewareEntry` | `aquilia/integrations/mw.py` | object | A single middleware entry in the chain. |
| `MiddlewareChain` | `aquilia/integrations/mw.py` | list | Fluent middleware chain builder. |
| `OpenAPIIntegration` | `aquilia/integrations/openapi.py` | object | Typed OpenAPI spec / Swagger UI configuration. |
| `RenderIntegration` | `aquilia/integrations/render.py` | object | Typed Render deployment configuration. |
| `CorsIntegration` | `aquilia/integrations/security.py` | object | Typed CORS middleware configuration. |
| `CspIntegration` | `aquilia/integrations/security.py` | object | Typed Content-Security-Policy configuration. |
| `RateLimitIntegration` | `aquilia/integrations/security.py` | object | Typed rate limiting configuration. |
| `CsrfIntegration` | `aquilia/integrations/security.py` | object | Typed CSRF protection configuration. |
| `SessionIntegration` | `aquilia/integrations/sessions.py` | object | Typed session integration config. |
| `DiIntegration` | `aquilia/integrations/simple.py` | object | Dependency injection configuration. |
| `RoutingIntegration` | `aquilia/integrations/simple.py` | object | Routing configuration. |
| `FaultHandlingIntegration` | `aquilia/integrations/simple.py` | object | Fault handling configuration. |
| `PatternsIntegration` | `aquilia/integrations/simple.py` | object | Patterns configuration. |
| `RegistryIntegration` | `aquilia/integrations/simple.py` | object | Registry configuration. |
| `SerializersIntegration` | `aquilia/integrations/simple.py` | object | Global serializer settings. |
| `StaticFilesIntegration` | `aquilia/integrations/static.py` | object | Typed static file serving configuration. |
| `StorageIntegration` | `aquilia/integrations/storage.py` | object | Typed file storage configuration. |
| `TasksIntegration` | `aquilia/integrations/tasks.py` | object | Typed background tasks configuration. |
| `TemplatesIntegration` | `aquilia/integrations/templates.py` | object | Typed template engine configuration. |
| `VersioningIntegration` | `aquilia/integrations/versioning_cfg.py` | object | Typed API versioning configuration. |

## Constants And Module Flags

| Name | Source | Value or Type |
| --- | --- | --- |
| `_ALL_METRICS` | `aquilia/integrations/admin.py` | `['cpu', 'memory', 'disk', 'network', 'process', 'python', 'system', 'health_checks']` |
| `_ALL_CONTAINER_ACTIONS` | `aquilia/integrations/admin.py` | `['start', 'stop', 'restart', 'pause', 'unpause', 'kill', 'rm', 'logs', 'inspect', 'exec', 'export']` |
| `_ALL_K8S_RESOURCES` | `aquilia/integrations/admin.py` | `['pods', 'deployments', 'services', 'ingresses', 'configmaps', 'secrets', 'namespaces', 'events', 'daemonsets', 'statefulsets', 'jobs', 'cronjobs', 'persistentvolumeclaims', 'nodes']` |

## Detailed Classes And Methods

### `IntegrationConfig`

- Source: `aquilia/integrations/_protocol.py`
- Bases: `Protocol`
- Summary: Protocol that all typed integration configs implement.
- Decorators: `runtime_checkable`

Methods:

| Method | Signature | Summary |
| --- | --- | --- |
| `to_dict` | `def to_dict(self)` | Serialize to the flat dict consumed by ``ConfigLoader``. |

### `AdminModules`

- Source: `aquilia/integrations/admin.py`
- Bases: `object`
- Summary: Controls which admin pages are visible.
- Decorators: `dataclass`

Fields and class attributes:

| Name | Type | Default / Value |
| --- | --- | --- |
| `dashboard` | `bool` | `True` |
| `orm` | `bool` | `True` |
| `migrations` | `bool` | `True` |
| `config` | `bool` | `True` |
| `workspace` | `bool` | `True` |
| `permissions` | `bool` | `True` |
| `monitoring` | `bool` | `False` |
| `admin_users` | `bool` | `True` |
| `profile` | `bool` | `True` |
| `audit` | `bool` | `False` |
| `containers` | `bool` | `False` |
| `pods` | `bool` | `False` |
| `query_inspector` | `bool` | `False` |
| `tasks` | `bool` | `False` |
| `errors` | `bool` | `False` |
| `testing` | `bool` | `False` |
| `mlops` | `bool` | `False` |
| `storage` | `bool` | `False` |
| `mailer` | `bool` | `False` |
| `api_keys` | `bool` | `True` |
| `preferences` | `bool` | `True` |
| `provider` | `bool` | `False` |

Methods:

| Method | Signature | Summary |
| --- | --- | --- |
| `default` | `def default(cls)` | Create with default visibility. |
| `all_enabled` | `def all_enabled(cls)` | Every module enabled. |
| `all_disabled` | `def all_disabled(cls)` | Every module disabled. |
| `with_` | `def with_(self, **overrides: bool)` | Return a copy with specific modules overridden. |
| `enable_dashboard` | `def enable_dashboard(self)` |  |
| `disable_dashboard` | `def disable_dashboard(self)` |  |
| `enable_orm` | `def enable_orm(self)` |  |
| `disable_orm` | `def disable_orm(self)` |  |
| `enable_migrations` | `def enable_migrations(self)` |  |
| `disable_migrations` | `def disable_migrations(self)` |  |
| `enable_config` | `def enable_config(self)` |  |
| `disable_config` | `def disable_config(self)` |  |
| `enable_workspace` | `def enable_workspace(self)` |  |
| `disable_workspace` | `def disable_workspace(self)` |  |
| `enable_permissions` | `def enable_permissions(self)` |  |
| `disable_permissions` | `def disable_permissions(self)` |  |
| `enable_monitoring` | `def enable_monitoring(self)` |  |
| `disable_monitoring` | `def disable_monitoring(self)` |  |
| `enable_admin_users` | `def enable_admin_users(self)` |  |
| `disable_admin_users` | `def disable_admin_users(self)` |  |
| `enable_profile` | `def enable_profile(self)` |  |
| `disable_profile` | `def disable_profile(self)` |  |
| `enable_containers` | `def enable_containers(self)` |  |
| `disable_containers` | `def disable_containers(self)` |  |
| `enable_pods` | `def enable_pods(self)` |  |
| `disable_pods` | `def disable_pods(self)` |  |
| `enable_audit` | `def enable_audit(self)` |  |
| `disable_audit` | `def disable_audit(self)` |  |
| `enable_query_inspector` | `def enable_query_inspector(self)` |  |
| `disable_query_inspector` | `def disable_query_inspector(self)` |  |
| `enable_tasks` | `def enable_tasks(self)` |  |
| `disable_tasks` | `def disable_tasks(self)` |  |
| `enable_errors` | `def enable_errors(self)` |  |
| `disable_errors` | `def disable_errors(self)` |  |
| `enable_testing` | `def enable_testing(self)` |  |
| `disable_testing` | `def disable_testing(self)` |  |
| `enable_mlops` | `def enable_mlops(self)` |  |
| `disable_mlops` | `def disable_mlops(self)` |  |
| `enable_storage` | `def enable_storage(self)` |  |
| `disable_storage` | `def disable_storage(self)` |  |
| `enable_mailer` | `def enable_mailer(self)` |  |
| `disable_mailer` | `def disable_mailer(self)` |  |
| `enable_provider` | `def enable_provider(self)` |  |
| `disable_provider` | `def disable_provider(self)` |  |
| `enable_api_keys` | `def enable_api_keys(self)` |  |
| `disable_api_keys` | `def disable_api_keys(self)` |  |
| `enable_preferences` | `def enable_preferences(self)` |  |
| `disable_preferences` | `def disable_preferences(self)` |  |
| `enable_all` | `def enable_all(self)` |  |
| `disable_all` | `def disable_all(self)` |  |
| `to_dict` | `def to_dict(self)` |  |

### `AdminAudit`

- Source: `aquilia/integrations/admin.py`
- Bases: `object`
- Summary: Audit log configuration.
- Decorators: `dataclass`

Fields and class attributes:

| Name | Type | Default / Value |
| --- | --- | --- |
| `enabled` | `bool` | `False` |
| `max_entries` | `int` | `10000` |
| `log_logins` | `bool` | `True` |
| `log_views` | `bool` | `True` |
| `log_searches` | `bool` | `True` |
| `excluded_actions` | `list[str]` | `field(default_factory=list)` |

Methods:

| Method | Signature | Summary |
| --- | --- | --- |
| `enable` | `def enable(self)` |  |
| `disable` | `def disable(self)` |  |
| `max_entries_set` | `def max_entries_set(self, n: int)` |  |
| `set_max_entries` | `def set_max_entries(self, n: int)` | Set the maximum number of audit entries (FIFO eviction). |
| `log_logins_set` | `def log_logins_set(self, enabled: bool=True)` |  |
| `no_log_logins` | `def no_log_logins(self)` |  |
| `log_views_set` | `def log_views_set(self, enabled: bool=True)` |  |
| `no_log_views` | `def no_log_views(self)` |  |
| `log_searches_set` | `def log_searches_set(self, enabled: bool=True)` |  |
| `no_log_searches` | `def no_log_searches(self)` |  |
| `exclude_actions` | `def exclude_actions(self, *actions: str)` |  |
| `to_dict` | `def to_dict(self)` |  |

### `AdminMonitoring`

- Source: `aquilia/integrations/admin.py`
- Bases: `object`
- Summary: Monitoring dashboard configuration.
- Decorators: `dataclass`

Fields and class attributes:

| Name | Type | Default / Value |
| --- | --- | --- |
| `enabled` | `bool` | `False` |
| `metrics` | `list[str]` | `field(default_factory=lambda: list(_ALL_METRICS))` |
| `refresh_interval` | `int` | `30` |

Methods:

| Method | Signature | Summary |
| --- | --- | --- |
| `enable` | `def enable(self)` |  |
| `disable` | `def disable(self)` |  |
| `metrics_set` | `def metrics_set(self, *names: str)` |  |
| `all_metrics` | `def all_metrics(self)` |  |
| `refresh_interval_set` | `def refresh_interval_set(self, seconds: int)` |  |
| `to_dict` | `def to_dict(self)` |  |

### `AdminSidebar`

- Source: `aquilia/integrations/admin.py`
- Bases: `object`
- Summary: Admin sidebar section visibility.
- Decorators: `dataclass`

Fields and class attributes:

| Name | Type | Default / Value |
| --- | --- | --- |
| `overview` | `bool` | `True` |
| `data` | `bool` | `True` |
| `system` | `bool` | `True` |
| `infrastructure` | `bool` | `True` |
| `security` | `bool` | `True` |
| `models` | `bool` | `True` |
| `devtools` | `bool` | `True` |

Methods:

| Method | Signature | Summary |
| --- | --- | --- |
| `show_overview` | `def show_overview(self)` |  |
| `hide_overview` | `def hide_overview(self)` |  |
| `show_data` | `def show_data(self)` |  |
| `hide_data` | `def hide_data(self)` |  |
| `show_system` | `def show_system(self)` |  |
| `hide_system` | `def hide_system(self)` |  |
| `show_infrastructure` | `def show_infrastructure(self)` |  |
| `hide_infrastructure` | `def hide_infrastructure(self)` |  |
| `show_security` | `def show_security(self)` |  |
| `hide_security` | `def hide_security(self)` |  |
| `show_models` | `def show_models(self)` |  |
| `hide_models` | `def hide_models(self)` |  |
| `show_devtools` | `def show_devtools(self)` |  |
| `hide_devtools` | `def hide_devtools(self)` |  |
| `show_all` | `def show_all(self)` |  |
| `hide_all` | `def hide_all(self)` |  |
| `to_dict` | `def to_dict(self)` |  |

### `AdminContainers`

- Source: `aquilia/integrations/admin.py`
- Bases: `object`
- Summary: Docker containers admin page configuration.
- Decorators: `dataclass`

Fields and class attributes:

| Name | Type | Default / Value |
| --- | --- | --- |
| `docker_host` | `str \| None` | `None` |
| `allowed_actions` | `list[str]` | `field(default_factory=lambda: list(_ALL_CONTAINER_ACTIONS))` |
| `denied_actions` | `list[str]` | `field(default_factory=list)` |
| `log_tail` | `int` | `200` |
| `log_since` | `str` | `''` |
| `refresh_interval` | `int` | `15` |
| `compose_files` | `list[str]` | `field(default_factory=list)` |
| `compose_project_dir` | `str \| None` | `None` |
| `show_system_containers` | `bool` | `False` |
| `enable_exec` | `bool` | `True` |
| `enable_prune` | `bool` | `True` |
| `enable_build` | `bool` | `True` |
| `enable_export` | `bool` | `True` |
| `enable_image_actions` | `bool` | `True` |
| `enable_volume_actions` | `bool` | `True` |
| `enable_network_actions` | `bool` | `True` |

Methods:

| Method | Signature | Summary |
| --- | --- | --- |
| `docker_socket` | `def docker_socket(self, path: str)` |  |
| `read_only` | `def read_only(self)` |  |
| `to_dict` | `def to_dict(self)` |  |

### `AdminPods`

- Source: `aquilia/integrations/admin.py`
- Bases: `object`
- Summary: Kubernetes pods admin page configuration.
- Decorators: `dataclass`

Fields and class attributes:

| Name | Type | Default / Value |
| --- | --- | --- |
| `kubeconfig` | `str \| None` | `None` |
| `namespace` | `str` | `'default'` |
| `contexts` | `list[str]` | `field(default_factory=list)` |
| `resources` | `list[str]` | `field(default_factory=lambda: list(_ALL_K8S_RESOURCES))` |
| `manifest_dirs` | `list[str]` | `field(default_factory=lambda: ['k8s'])` |
| `manifest_patterns` | `list[str]` | `field(default_factory=lambda: ['*.yaml', '*.yml'])` |
| `refresh_interval` | `int` | `15` |
| `log_tail` | `int` | `200` |
| `enable_logs` | `bool` | `True` |
| `enable_exec` | `bool` | `True` |
| `enable_delete` | `bool` | `True` |
| `enable_scale` | `bool` | `True` |
| `enable_restart` | `bool` | `True` |
| `enable_apply` | `bool` | `True` |

Methods:

| Method | Signature | Summary |
| --- | --- | --- |
| `all_namespaces` | `def all_namespaces(self)` |  |
| `read_only` | `def read_only(self)` |  |
| `to_dict` | `def to_dict(self)` |  |

### `AdminSecurity`

- Source: `aquilia/integrations/admin.py`
- Bases: `object`
- Summary: Admin dashboard security configuration (CSRF, rate-limit, passwords, headers).
- Decorators: `dataclass`

Fields and class attributes:

| Name | Type | Default / Value |
| --- | --- | --- |
| `csrf_enabled` | `bool` | `True` |
| `csrf_max_age` | `int` | `7200` |
| `csrf_token_length` | `int` | `32` |
| `rate_limit_enabled` | `bool` | `True` |
| `rate_limit_max_attempts` | `int` | `5` |
| `rate_limit_window` | `int` | `900` |
| `sensitive_op_limit` | `int` | `30` |
| `sensitive_op_window` | `int` | `300` |
| `progressive_lockout` | `bool` | `True` |
| `lockout_tiers` | `list[list[int]] \| None` | `None` |
| `password_min_length` | `int` | `10` |
| `password_max_length` | `int` | `128` |
| `password_require_upper` | `bool` | `True` |
| `password_require_lower` | `bool` | `True` |
| `password_require_digit` | `bool` | `True` |
| `password_require_special` | `bool` | `True` |
| `security_headers_enabled` | `bool` | `True` |
| `csp_template` | `str \| None` | `None` |
| `frame_options` | `str` | `'DENY'` |
| `permissions_policy` | `str \| None` | `None` |
| `session_fixation_protection` | `bool` | `True` |
| `event_tracker_max_events` | `int` | `1000` |

Methods:

| Method | Signature | Summary |
| --- | --- | --- |
| `csrf_enabled_set` | `def csrf_enabled_set(self, enabled: bool=True)` |  |
| `no_csrf` | `def no_csrf(self)` |  |
| `no_rate_limit` | `def no_rate_limit(self)` |  |
| `relaxed_password_policy` | `def relaxed_password_policy(self)` |  |
| `strict_password_policy` | `def strict_password_policy(self)` |  |
| `no_security_headers` | `def no_security_headers(self)` |  |
| `to_dict` | `def to_dict(self)` |  |

### `AdminIntegration`

- Source: `aquilia/integrations/admin.py`
- Bases: `object`
- Summary: Typed admin dashboard integration config.
- Decorators: `dataclass`

Fields and class attributes:

| Name | Type | Default / Value |
| --- | --- | --- |
| `url_prefix` | `str` | `'/admin'` |
| `site_title` | `str` | `'Aquilia Admin'` |
| `site_header` | `str` | `'Aquilia Administration'` |
| `auto_discover` | `bool` | `True` |
| `login_url` | `str \| None` | `None` |
| `list_per_page` | `int` | `25` |
| `theme` | `str` | `'auto'` |
| `modules` | `AdminModules \| None` | `None` |
| `audit` | `AdminAudit \| None` | `None` |
| `monitoring` | `AdminMonitoring \| None` | `None` |
| `sidebar` | `AdminSidebar \| None` | `None` |
| `containers` | `AdminContainers \| None` | `None` |
| `pods` | `AdminPods \| None` | `None` |
| `security` | `AdminSecurity \| None` | `None` |

Methods:

| Method | Signature | Summary |
| --- | --- | --- |
| `to_dict` | `def to_dict(self)` |  |

### `AuthIntegration`

- Source: `aquilia/integrations/auth.py`
- Bases: `object`
- Summary: Typed authentication integration config.
- Decorators: `dataclass`

Fields and class attributes:

| Name | Type | Default / Value |
| --- | --- | --- |
| `enabled` | `bool` | `True` |
| `store_type` | `str` | `'memory'` |
| `secret_key` | `str \| None` | `None` |
| `algorithm` | `str` | `'HS256'` |
| `issuer` | `str` | `'aquilia'` |
| `audience` | `str` | `'aquilia-app'` |
| `access_token_ttl_minutes` | `int` | `60` |
| `refresh_token_ttl_days` | `int` | `30` |
| `require_auth_by_default` | `bool` | `False` |

Methods:

| Method | Signature | Summary |
| --- | --- | --- |
| `to_dict` | `def to_dict(self)` |  |

### `CacheIntegration`

- Source: `aquilia/integrations/cache.py`
- Bases: `object`
- Summary: Typed cache subsystem configuration.
- Decorators: `dataclass`

Fields and class attributes:

| Name | Type | Default / Value |
| --- | --- | --- |
| `backend` | `str` | `'memory'` |
| `default_ttl` | `int` | `300` |
| `max_size` | `int` | `10000` |
| `eviction_policy` | `str` | `'lru'` |
| `namespace` | `str` | `'default'` |
| `key_prefix` | `str` | `'aq:'` |
| `serializer` | `str` | `'json'` |
| `redis_url` | `str` | `'redis://localhost:6379/0'` |
| `redis_max_connections` | `int` | `10` |
| `l1_max_size` | `int` | `1000` |
| `l1_ttl` | `int` | `60` |
| `l2_backend` | `str` | `'redis'` |
| `middleware_enabled` | `bool` | `False` |
| `middleware_default_ttl` | `int` | `60` |
| `enabled` | `bool` | `True` |

Methods:

| Method | Signature | Summary |
| --- | --- | --- |
| `to_dict` | `def to_dict(self)` |  |

### `DatabaseIntegration`

- Source: `aquilia/integrations/database.py`
- Bases: `object`
- Summary: Typed database integration config.
- Decorators: `dataclass`

Fields and class attributes:

| Name | Type | Default / Value |
| --- | --- | --- |
| `url` | `str \| None` | `None` |
| `config` | `Any \| None` | `field(default=None, repr=False)` |
| `auto_connect` | `bool` | `True` |
| `auto_create` | `bool` | `True` |
| `auto_migrate` | `bool` | `False` |
| `migrations_dir` | `str` | `'migrations'` |
| `pool_size` | `int` | `5` |
| `echo` | `bool` | `False` |
| `model_paths` | `list[str]` | `field(default_factory=list)` |
| `scan_dirs` | `list[str]` | `field(default_factory=lambda: ['models'])` |

Methods:

| Method | Signature | Summary |
| --- | --- | --- |
| `to_dict` | `def to_dict(self)` |  |

### `I18nIntegration`

- Source: `aquilia/integrations/i18n.py`
- Bases: `object`
- Summary: Typed i18n (internationalization) configuration.
- Decorators: `dataclass`

Fields and class attributes:

| Name | Type | Default / Value |
| --- | --- | --- |
| `default_locale` | `str` | `'en'` |
| `available_locales` | `list[str]` | `field(default_factory=lambda: ['en'])` |
| `fallback_locale` | `str` | `'en'` |
| `catalog_dirs` | `list[str]` | `field(default_factory=lambda: ['locales'])` |
| `catalog_format` | `str` | `'json'` |
| `missing_key_strategy` | `str` | `'log_and_key'` |
| `auto_reload` | `bool` | `False` |
| `auto_detect` | `bool` | `True` |
| `cookie_name` | `str` | `'aq_locale'` |
| `query_param` | `str` | `'lang'` |
| `path_prefix` | `bool` | `False` |
| `resolver_order` | `list[str]` | `field(default_factory=lambda: ['query', 'cookie', 'header'])` |
| `enabled` | `bool` | `True` |

Methods:

| Method | Signature | Summary |
| --- | --- | --- |
| `to_dict` | `def to_dict(self)` |  |

### `LoggingIntegration`

- Source: `aquilia/integrations/logging_cfg.py`
- Bases: `object`
- Summary: Typed request logging configuration.
- Decorators: `dataclass`

Fields and class attributes:

| Name | Type | Default / Value |
| --- | --- | --- |
| `format` | `str` | `'%(method)s %(path)s %(status)s %(duration_ms).1fms'` |
| `level` | `str` | `'INFO'` |
| `slow_threshold_ms` | `float` | `1000.0` |
| `skip_paths` | `list[str]` | `field(default_factory=lambda: ['/health', '/healthz', '/ready', '/metrics'])` |
| `include_headers` | `bool` | `False` |
| `include_query` | `bool` | `True` |
| `include_user_agent` | `bool` | `False` |
| `log_request_body` | `bool` | `False` |
| `log_response_body` | `bool` | `False` |
| `colorize` | `bool` | `True` |
| `enabled` | `bool` | `True` |

Methods:

| Method | Signature | Summary |
| --- | --- | --- |
| `to_dict` | `def to_dict(self)` |  |

### `MailAuth`

- Source: `aquilia/integrations/mail.py`
- Bases: `object`
- Summary: Mail authentication credentials.
- Decorators: `dataclass`

Fields and class attributes:

| Name | Type | Default / Value |
| --- | --- | --- |
| `method` | `str` | `'none'` |
| `username` | `str \| None` | `None` |
| `password` | `str \| None` | `None` |
| `password_env` | `str \| None` | `None` |
| `domain` | `str \| None` | `None` |
| `api_key` | `str \| None` | `None` |
| `api_key_env` | `str \| None` | `None` |
| `aws_access_key_id` | `str \| None` | `None` |
| `aws_access_key_id_env` | `str \| None` | `None` |
| `aws_secret_access_key` | `str \| None` | `None` |
| `aws_secret_access_key_env` | `str \| None` | `None` |
| `aws_region` | `str \| None` | `None` |
| `aws_session_token` | `str \| None` | `None` |
| `access_token` | `str \| None` | `None` |
| `refresh_token` | `str \| None` | `None` |
| `token_url` | `str \| None` | `None` |
| `client_id` | `str \| None` | `None` |
| `client_secret` | `str \| None` | `None` |
| `client_secret_env` | `str \| None` | `None` |
| `scope` | `str \| None` | `None` |

Methods:

| Method | Signature | Summary |
| --- | --- | --- |
| `plain` | `def plain(cls, username: str, password: str \| None=None, *, password_env: str \| None=None)` | SMTP AUTH PLAIN / LOGIN. |
| `api_key` | `def api_key(cls, key: str \| None=None, *, env: str \| None=None)` | API-key auth for SendGrid, Mailgun, Postmark, etc. |
| `aws_ses` | `def aws_ses(cls, access_key_id: str \| None=None, secret_access_key: str \| None=None, region: str='us-east-1', session_token: str \| None=None, *, access_key_id_env: str \| None=None, secret_access_key_env: str \| None=None)` | AWS SES credentials. |
| `oauth2` | `def oauth2(cls, client_id: str, client_secret: str \| None=None, *, client_secret_env: str \| None=None, token_url: str, scope: str \| None=None, access_token: str \| None=None, refresh_token: str \| None=None)` | OAuth2 bearer-token auth (Gmail, Microsoft 365, etc.). |
| `ntlm` | `def ntlm(cls, username: str, password: str \| None=None, domain: str \| None=None, *, password_env: str \| None=None)` | Windows NTLM authentication. |
| `anonymous` | `def anonymous(cls)` | No authentication — open relay. |
| `to_dict` | `def to_dict(self)` |  |

### `SmtpProvider`

- Source: `aquilia/integrations/mail.py`
- Bases: `_ProviderBase`
- Summary: SMTP / STARTTLS mail provider.
- Decorators: `dataclass`

Fields and class attributes:

| Name | Type | Default / Value |
| --- | --- | --- |
| `host` | `str` | `'localhost'` |
| `port` | `int` | `587` |
| `use_tls` | `bool` | `True` |
| `use_ssl` | `bool` | `False` |
| `timeout` | `float` | `30.0` |
| `pool_size` | `int` | `3` |
| `pool_recycle` | `float` | `300.0` |
| `validate_certs` | `bool` | `True` |
| `client_cert` | `str \| None` | `None` |
| `client_key` | `str \| None` | `None` |
| `source_address` | `str \| None` | `None` |
| `local_hostname` | `str \| None` | `None` |

Methods:

| Method | Signature | Summary |
| --- | --- | --- |
| `to_dict` | `def to_dict(self)` |  |

### `SesProvider`

- Source: `aquilia/integrations/mail.py`
- Bases: `_ProviderBase`
- Summary: AWS Simple Email Service provider.
- Decorators: `dataclass`

Fields and class attributes:

| Name | Type | Default / Value |
| --- | --- | --- |
| `region` | `str` | `'us-east-1'` |
| `configuration_set` | `str \| None` | `None` |
| `source_arn` | `str \| None` | `None` |
| `return_path` | `str \| None` | `None` |
| `tags` | `dict[str, str]` | `field(default_factory=dict)` |
| `use_raw` | `bool` | `True` |
| `endpoint_url` | `str \| None` | `None` |

Methods:

| Method | Signature | Summary |
| --- | --- | --- |
| `to_dict` | `def to_dict(self)` |  |

### `SendGridProvider`

- Source: `aquilia/integrations/mail.py`
- Bases: `_ProviderBase`
- Summary: SendGrid Web API v3 provider.
- Decorators: `dataclass`

Fields and class attributes:

| Name | Type | Default / Value |
| --- | --- | --- |
| `sandbox_mode` | `bool` | `False` |
| `click_tracking` | `bool` | `True` |
| `open_tracking` | `bool` | `True` |
| `categories` | `list[str]` | `field(default_factory=list)` |
| `asm_group_id` | `int \| None` | `None` |
| `ip_pool_name` | `str \| None` | `None` |
| `template_id` | `str \| None` | `None` |
| `api_base_url` | `str` | `'https://api.sendgrid.com'` |
| `timeout` | `float` | `30.0` |

Methods:

| Method | Signature | Summary |
| --- | --- | --- |
| `to_dict` | `def to_dict(self)` |  |

### `ConsoleProvider`

- Source: `aquilia/integrations/mail.py`
- Bases: `_ProviderBase`
- Summary: Console / stdout provider (development only).
- Decorators: `dataclass`

Methods:

| Method | Signature | Summary |
| --- | --- | --- |
| `to_dict` | `def to_dict(self)` |  |

### `FileProvider`

- Source: `aquilia/integrations/mail.py`
- Bases: `_ProviderBase`
- Summary: File / .eml provider (testing & audit).
- Decorators: `dataclass`

Fields and class attributes:

| Name | Type | Default / Value |
| --- | --- | --- |
| `output_dir` | `str` | `'/tmp/aquilia_mail'` |
| `max_files` | `int` | `10000` |
| `write_index` | `bool` | `True` |
| `include_metadata` | `bool` | `True` |
| `file_extension` | `str` | `'.eml'` |

Methods:

| Method | Signature | Summary |
| --- | --- | --- |
| `to_dict` | `def to_dict(self)` |  |

### `MailIntegration`

- Source: `aquilia/integrations/mail.py`
- Bases: `object`
- Summary: Typed mail subsystem configuration.
- Decorators: `dataclass`

Fields and class attributes:

| Name | Type | Default / Value |
| --- | --- | --- |
| `default_from` | `str` | `'noreply@localhost'` |
| `default_reply_to` | `str \| None` | `None` |
| `subject_prefix` | `str` | `''` |
| `providers` | `list[Any]` | `field(default_factory=list)` |
| `auth` | `MailAuth \| None` | `None` |
| `console_backend` | `bool` | `False` |
| `preview_mode` | `bool` | `False` |
| `template_dirs` | `list[str]` | `field(default_factory=lambda: ['mail_templates'])` |
| `retry_max_attempts` | `int` | `5` |
| `retry_base_delay` | `float` | `1.0` |
| `rate_limit_global` | `int` | `1000` |
| `rate_limit_per_domain` | `int` | `100` |
| `dkim_enabled` | `bool` | `False` |
| `dkim_domain` | `str \| None` | `None` |
| `dkim_selector` | `str` | `'aquilia'` |
| `require_tls` | `bool` | `True` |
| `pii_redaction` | `bool` | `False` |
| `metrics_enabled` | `bool` | `True` |
| `tracing_enabled` | `bool` | `False` |
| `enabled` | `bool` | `True` |

Methods:

| Method | Signature | Summary |
| --- | --- | --- |
| `to_dict` | `def to_dict(self)` |  |

### `MLOpsIntegration`

- Source: `aquilia/integrations/mlops.py`
- Bases: `object`
- Summary: Typed MLOps platform configuration.
- Decorators: `dataclass`

Fields and class attributes:

| Name | Type | Default / Value |
| --- | --- | --- |
| `enabled` | `bool` | `True` |
| `registry_db` | `str` | `'registry.db'` |
| `blob_root` | `str` | `'.aquilia-store'` |
| `storage_backend` | `str` | `'filesystem'` |
| `drift_method` | `str` | `'psi'` |
| `drift_threshold` | `float` | `0.2` |
| `drift_num_bins` | `int` | `10` |
| `max_batch_size` | `int` | `16` |
| `max_latency_ms` | `float` | `50.0` |
| `batching_strategy` | `str` | `'hybrid'` |
| `sample_rate` | `float` | `0.01` |
| `log_dir` | `str` | `'prediction_logs'` |
| `hmac_secret` | `str \| None` | `None` |
| `signing_private_key` | `str \| None` | `None` |
| `signing_public_key` | `str \| None` | `None` |
| `encryption_key` | `Any \| None` | `None` |
| `plugin_auto_discover` | `bool` | `True` |
| `scaling_policy` | `dict[str, Any] \| None` | `None` |
| `rollout_default_strategy` | `str` | `'canary'` |
| `auto_rollback` | `bool` | `True` |
| `metrics_model_name` | `str` | `''` |
| `metrics_model_version` | `str` | `''` |
| `cache_enabled` | `bool` | `True` |
| `cache_ttl` | `int` | `60` |
| `cache_namespace` | `str` | `'mlops'` |
| `artifact_store_dir` | `str` | `'artifacts'` |
| `fault_engine_debug` | `bool` | `False` |

Methods:

| Method | Signature | Summary |
| --- | --- | --- |
| `to_dict` | `def to_dict(self)` |  |

### `MiddlewareEntry`

- Source: `aquilia/integrations/mw.py`
- Bases: `object`
- Summary: A single middleware entry in the chain.
- Decorators: `dataclass`

Fields and class attributes:

| Name | Type | Default / Value |
| --- | --- | --- |
| `path` | `str` | `` |
| `priority` | `int` | `50` |
| `scope` | `str` | `'global'` |
| `name` | `str \| None` | `None` |
| `kwargs` | `dict[str, Any]` | `field(default_factory=dict)` |

Methods:

| Method | Signature | Summary |
| --- | --- | --- |
| `to_dict` | `def to_dict(self)` |  |

### `MiddlewareChain`

- Source: `aquilia/integrations/mw.py`
- Bases: `list`
- Summary: Fluent middleware chain builder.

Methods:

| Method | Signature | Summary |
| --- | --- | --- |
| `use` | `def use(self, path: str, *, priority: int=50, scope: str='global', name: str \| None=None, **kwargs: Any)` |  |
| `to_list` | `def to_list(self)` |  |
| `chain` | `def chain(cls)` | Create an empty chain. |
| `defaults` | `def defaults(cls)` | Standard development middleware chain. |
| `production` | `def production(cls)` | Production-grade middleware chain. |
| `minimal` | `def minimal(cls)` | Minimal middleware chain. |

### `OpenAPIIntegration`

- Source: `aquilia/integrations/openapi.py`
- Bases: `object`
- Summary: Typed OpenAPI spec / Swagger UI configuration.
- Decorators: `dataclass`

Fields and class attributes:

| Name | Type | Default / Value |
| --- | --- | --- |
| `title` | `str` | `'Aquilia API'` |
| `version` | `str` | `'1.0.0'` |
| `description` | `str` | `''` |
| `terms_of_service` | `str` | `''` |
| `contact_name` | `str` | `''` |
| `contact_email` | `str` | `''` |
| `contact_url` | `str` | `''` |
| `license_name` | `str` | `''` |
| `license_url` | `str` | `''` |
| `servers` | `list[dict[str, str]]` | `field(default_factory=list)` |
| `docs_path` | `str` | `'/docs'` |
| `openapi_json_path` | `str` | `'/openapi.json'` |
| `redoc_path` | `str` | `'/redoc'` |
| `include_internal` | `bool` | `False` |
| `group_by_module` | `bool` | `True` |
| `infer_request_body` | `bool` | `True` |
| `infer_responses` | `bool` | `True` |
| `detect_security` | `bool` | `True` |
| `external_docs_url` | `str` | `''` |
| `external_docs_description` | `str` | `''` |
| `swagger_ui_theme` | `str` | `''` |
| `swagger_ui_config` | `dict[str, Any]` | `field(default_factory=dict)` |
| `enabled` | `bool` | `True` |

Methods:

| Method | Signature | Summary |
| --- | --- | --- |
| `to_dict` | `def to_dict(self)` |  |

### `RenderIntegration`

- Source: `aquilia/integrations/render.py`
- Bases: `object`
- Summary: Typed Render deployment configuration.
- Decorators: `dataclass`

Fields and class attributes:

| Name | Type | Default / Value |
| --- | --- | --- |
| `service_name` | `str \| None` | `None` |
| `region` | `str` | `'oregon'` |
| `plan` | `str` | `'starter'` |
| `num_instances` | `int` | `1` |
| `image` | `str \| None` | `None` |
| `health_path` | `str` | `'/_health'` |
| `auto_deploy` | `str` | `'no'` |
| `enabled` | `bool` | `True` |

Methods:

| Method | Signature | Summary |
| --- | --- | --- |
| `to_dict` | `def to_dict(self)` |  |

### `CorsIntegration`

- Source: `aquilia/integrations/security.py`
- Bases: `object`
- Summary: Typed CORS middleware configuration.
- Decorators: `dataclass`

Fields and class attributes:

| Name | Type | Default / Value |
| --- | --- | --- |
| `allow_origins` | `list[str]` | `field(default_factory=lambda: ['*'])` |
| `allow_methods` | `list[str]` | `field(default_factory=lambda: ['GET', 'POST', 'PUT', 'PATCH', 'DELETE', 'HEAD', 'OPTIONS'])` |
| `allow_headers` | `list[str]` | `field(default_factory=lambda: ['accept', 'accept-language', 'content-language', 'content-type', 'authorization', 'x-requested-with'])` |
| `expose_headers` | `list[str]` | `field(default_factory=list)` |
| `allow_credentials` | `bool` | `False` |
| `max_age` | `int` | `600` |
| `allow_origin_regex` | `str \| None` | `None` |
| `enabled` | `bool` | `True` |

Methods:

| Method | Signature | Summary |
| --- | --- | --- |
| `to_dict` | `def to_dict(self)` |  |

### `CspIntegration`

- Source: `aquilia/integrations/security.py`
- Bases: `object`
- Summary: Typed Content-Security-Policy configuration.
- Decorators: `dataclass`

Fields and class attributes:

| Name | Type | Default / Value |
| --- | --- | --- |
| `policy` | `dict[str, list[str]] \| None` | `None` |
| `report_only` | `bool` | `False` |
| `nonce` | `bool` | `True` |
| `preset` | `str` | `'strict'` |
| `enabled` | `bool` | `True` |

Methods:

| Method | Signature | Summary |
| --- | --- | --- |
| `to_dict` | `def to_dict(self)` |  |

### `RateLimitIntegration`

- Source: `aquilia/integrations/security.py`
- Bases: `object`
- Summary: Typed rate limiting configuration.
- Decorators: `dataclass`

Fields and class attributes:

| Name | Type | Default / Value |
| --- | --- | --- |
| `limit` | `int` | `100` |
| `window` | `int` | `60` |
| `algorithm` | `str` | `'sliding_window'` |
| `per_user` | `bool` | `False` |
| `burst` | `int \| None` | `None` |
| `exempt_paths` | `list[str]` | `field(default_factory=lambda: ['/health', '/healthz', '/ready'])` |
| `enabled` | `bool` | `True` |

Methods:

| Method | Signature | Summary |
| --- | --- | --- |
| `to_dict` | `def to_dict(self)` |  |

### `CsrfIntegration`

- Source: `aquilia/integrations/security.py`
- Bases: `object`
- Summary: Typed CSRF protection configuration.
- Decorators: `dataclass`

Fields and class attributes:

| Name | Type | Default / Value |
| --- | --- | --- |
| `secret_key` | `str` | `''` |
| `token_length` | `int` | `32` |
| `header_name` | `str` | `'X-CSRF-Token'` |
| `field_name` | `str` | `'_csrf_token'` |
| `cookie_name` | `str` | `'_csrf_cookie'` |
| `cookie_path` | `str` | `'/'` |
| `cookie_domain` | `str \| None` | `None` |
| `cookie_secure` | `bool` | `True` |
| `cookie_samesite` | `str` | `'Lax'` |
| `cookie_httponly` | `bool` | `False` |
| `cookie_max_age` | `int` | `3600` |
| `safe_methods` | `list[str]` | `field(default_factory=lambda: ['GET', 'HEAD', 'OPTIONS', 'TRACE'])` |
| `exempt_paths` | `list[str]` | `field(default_factory=list)` |
| `exempt_content_types` | `list[str]` | `field(default_factory=list)` |
| `trust_ajax` | `bool` | `True` |
| `rotate_token` | `bool` | `False` |
| `failure_status` | `int` | `403` |
| `enabled` | `bool` | `True` |

Methods:

| Method | Signature | Summary |
| --- | --- | --- |
| `to_dict` | `def to_dict(self)` |  |

### `SessionIntegration`

- Source: `aquilia/integrations/sessions.py`
- Bases: `object`
- Summary: Typed session integration config.
- Decorators: `dataclass`

Fields and class attributes:

| Name | Type | Default / Value |
| --- | --- | --- |
| `enabled` | `bool` | `True` |
| `policy` | `Any \| None` | `None` |
| `store` | `Any \| None` | `None` |
| `transport` | `Any \| None` | `None` |

Methods:

| Method | Signature | Summary |
| --- | --- | --- |
| `to_dict` | `def to_dict(self)` |  |

### `DiIntegration`

- Source: `aquilia/integrations/simple.py`
- Bases: `object`
- Summary: Dependency injection configuration.
- Decorators: `dataclass`

Fields and class attributes:

| Name | Type | Default / Value |
| --- | --- | --- |
| `auto_wire` | `bool` | `True` |
| `enabled` | `bool` | `True` |

Methods:

| Method | Signature | Summary |
| --- | --- | --- |
| `to_dict` | `def to_dict(self)` |  |

### `RoutingIntegration`

- Source: `aquilia/integrations/simple.py`
- Bases: `object`
- Summary: Routing configuration.
- Decorators: `dataclass`

Fields and class attributes:

| Name | Type | Default / Value |
| --- | --- | --- |
| `strict_matching` | `bool` | `True` |
| `enabled` | `bool` | `True` |

Methods:

| Method | Signature | Summary |
| --- | --- | --- |
| `to_dict` | `def to_dict(self)` |  |

### `FaultHandlingIntegration`

- Source: `aquilia/integrations/simple.py`
- Bases: `object`
- Summary: Fault handling configuration.
- Decorators: `dataclass`

Fields and class attributes:

| Name | Type | Default / Value |
| --- | --- | --- |
| `default_strategy` | `str` | `'propagate'` |
| `enabled` | `bool` | `True` |

Methods:

| Method | Signature | Summary |
| --- | --- | --- |
| `to_dict` | `def to_dict(self)` |  |

### `PatternsIntegration`

- Source: `aquilia/integrations/simple.py`
- Bases: `object`
- Summary: Patterns configuration.
- Decorators: `dataclass`

Fields and class attributes:

| Name | Type | Default / Value |
| --- | --- | --- |
| `enabled` | `bool` | `True` |

Methods:

| Method | Signature | Summary |
| --- | --- | --- |
| `to_dict` | `def to_dict(self)` |  |

### `RegistryIntegration`

- Source: `aquilia/integrations/simple.py`
- Bases: `object`
- Summary: Registry configuration.
- Decorators: `dataclass`

Fields and class attributes:

| Name | Type | Default / Value |
| --- | --- | --- |
| `enabled` | `bool` | `True` |

Methods:

| Method | Signature | Summary |
| --- | --- | --- |
| `to_dict` | `def to_dict(self)` |  |

### `SerializersIntegration`

- Source: `aquilia/integrations/simple.py`
- Bases: `object`
- Summary: Global serializer settings.
- Decorators: `dataclass`

Fields and class attributes:

| Name | Type | Default / Value |
| --- | --- | --- |
| `auto_discover` | `bool` | `True` |
| `strict_validation` | `bool` | `True` |
| `raise_on_error` | `bool` | `False` |
| `date_format` | `str` | `'iso-8601'` |
| `datetime_format` | `str` | `'iso-8601'` |
| `coerce_decimal_to_string` | `bool` | `True` |
| `compact_json` | `bool` | `True` |
| `enabled` | `bool` | `True` |

Methods:

| Method | Signature | Summary |
| --- | --- | --- |
| `to_dict` | `def to_dict(self)` |  |

### `StaticFilesIntegration`

- Source: `aquilia/integrations/static.py`
- Bases: `object`
- Summary: Typed static file serving configuration.
- Decorators: `dataclass`

Fields and class attributes:

| Name | Type | Default / Value |
| --- | --- | --- |
| `directories` | `dict[str, str]` | `field(default_factory=lambda: {'/static': 'static'})` |
| `cache_max_age` | `int` | `86400` |
| `immutable` | `bool` | `False` |
| `etag` | `bool` | `True` |
| `gzip` | `bool` | `True` |
| `brotli` | `bool` | `True` |
| `memory_cache` | `bool` | `True` |
| `html5_history` | `bool` | `False` |
| `enabled` | `bool` | `True` |

Methods:

| Method | Signature | Summary |
| --- | --- | --- |
| `to_dict` | `def to_dict(self)` |  |

### `StorageIntegration`

- Source: `aquilia/integrations/storage.py`
- Bases: `object`
- Summary: Typed file storage configuration.
- Decorators: `dataclass`

Fields and class attributes:

| Name | Type | Default / Value |
| --- | --- | --- |
| `default` | `str` | `'default'` |
| `backends` | `dict[str, Any] \| None` | `None` |
| `enabled` | `bool` | `True` |

Methods:

| Method | Signature | Summary |
| --- | --- | --- |
| `to_dict` | `def to_dict(self)` |  |

### `TasksIntegration`

- Source: `aquilia/integrations/tasks.py`
- Bases: `object`
- Summary: Typed background tasks configuration.
- Decorators: `dataclass`

Fields and class attributes:

| Name | Type | Default / Value |
| --- | --- | --- |
| `backend` | `str` | `'memory'` |
| `num_workers` | `int` | `4` |
| `default_queue` | `str` | `'default'` |
| `cleanup_interval` | `float` | `300.0` |
| `cleanup_max_age` | `float` | `3600.0` |
| `max_retries` | `int` | `3` |
| `retry_delay` | `float` | `1.0` |
| `retry_backoff` | `float` | `2.0` |
| `retry_max_delay` | `float` | `300.0` |
| `default_timeout` | `float` | `300.0` |
| `auto_start` | `bool` | `True` |
| `dead_letter_max` | `int` | `1000` |
| `scheduler_tick` | `float` | `15.0` |
| `enabled` | `bool` | `True` |

Methods:

| Method | Signature | Summary |
| --- | --- | --- |
| `to_dict` | `def to_dict(self)` |  |

### `TemplatesIntegration`

- Source: `aquilia/integrations/templates.py`
- Bases: `object`
- Summary: Typed template engine configuration.
- Decorators: `dataclass`

Fields and class attributes:

| Name | Type | Default / Value |
| --- | --- | --- |
| `enabled` | `bool` | `True` |
| `search_paths` | `list[str]` | `field(default_factory=lambda: ['templates'])` |
| `cache` | `str` | `'memory'` |
| `sandbox` | `bool` | `True` |
| `sandbox_policy` | `str` | `'strict'` |
| `precompile` | `bool` | `False` |

Methods:

| Method | Signature | Summary |
| --- | --- | --- |
| `to_dict` | `def to_dict(self)` |  |
| `builder` | `def builder(cls)` | Start a fluent builder. |
| `source` | `def source(cls, *paths: str)` | Start builder with source paths. |
| `defaults` | `def defaults(cls)` | Start with default configuration. |

### `VersioningIntegration`

- Source: `aquilia/integrations/versioning_cfg.py`
- Bases: `object`
- Summary: Typed API versioning configuration.
- Decorators: `dataclass`

Fields and class attributes:

| Name | Type | Default / Value |
| --- | --- | --- |
| `strategy` | `str` | `'header'` |
| `versions` | `list[str]` | `field(default_factory=list)` |
| `default_version` | `str \| None` | `None` |
| `require_version` | `bool` | `False` |
| `header_name` | `str` | `'X-API-Version'` |
| `query_param` | `str` | `'api_version'` |
| `url_prefix` | `str` | `'v'` |
| `url_segment_index` | `int` | `0` |
| `strip_version_from_path` | `bool` | `True` |
| `media_type_param` | `str` | `'version'` |
| `channels` | `dict[str, str]` | `field(default_factory=dict)` |
| `channel_header` | `str` | `'X-API-Channel'` |
| `channel_query_param` | `str` | `'api_channel'` |
| `negotiation_mode` | `str` | `'exact'` |
| `sunset_policy` | `Any \| None` | `None` |
| `sunset_schedules` | `dict[str, dict[str, Any]] \| None` | `None` |
| `include_version_header` | `bool` | `True` |
| `response_header_name` | `str` | `'X-API-Version'` |
| `include_supported_versions_header` | `bool` | `True` |
| `neutral_paths` | `list[str]` | `field(default_factory=lambda: ['/_health', '/openapi.json', '/docs', '/redoc'])` |
| `enabled` | `bool` | `True` |

Methods:

| Method | Signature | Summary |
| --- | --- | --- |
| `to_dict` | `def to_dict(self)` |  |
